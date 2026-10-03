from django.test import TestCase
from django.urls import reverse

from audit.models import AuditEvent
from games import services
from games.models import GameNight, GameSession, Participant
from groups import services as groups
from groups.errors import NotAllowed, RuleError
from groups.tests.helpers import add_player, make_group, make_user

from .helpers import STAKES, make_session


class NextSetTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.first = make_session(self.host, state="open", seat_count=6)
        self.people = {}
        for name in ("Ana", "Ben", "Carlo", "Dani"):
            member = groups.add_roster_player(self.host, name)
            self.people[name] = services.add_participant(self.first.pk, self.host, member.pk)
        services.transition(self.first.pk, self.host, "start")

    def end(self):
        return services.transition(self.first.pk, self.host, "end")

    def names(self, game):
        return [p.member.display_name for p in game.participants.filter(status="joined").order_by("join_order")]

    def test_next_set_copies_table_settings_and_players_but_no_money(self):
        services.update_settings(self.first.pk, self.host, {**STAKES, "big_blind": 4000, "small_blind": 2000})
        services.set_left(self.first.pk, self.host, self.people["Ben"].pk)  # Ben went home
        self.end()
        second = services.start_next_set(self.first.night_id, self.host)
        self.assertEqual((second.set_number, second.state, second.night_id), (2, "open", self.first.night_id))
        self.assertEqual((second.table_id, second.seat_count, second.unit), (self.first.table_id, 6, "php"))
        settings = services.current_settings(second)
        self.assertEqual((settings.number, settings.big_blind), (1, 4000))  # the latest settings of set 1
        self.assertEqual(self.names(second), ["Ana", "Carlo", "Dani"])  # players still at the table
        self.assertEqual([p.join_order for p in second.participants.order_by("join_order")], [1, 2, 3])
        self.assertFalse(services.has_money(second))
        self.assertEqual(self.names(self.first), ["Ana", "Carlo", "Dani"])  # set 1 is untouched
        self.assertIn("Started set 2 with 3 players from set 1", AuditEvent.objects.filter(session_id=second.pk).first().summary)

    def test_refused_while_a_set_is_in_play(self):
        with self.assertRaisesMessage(RuleError, "Set 1 is still running"):
            services.start_next_set(self.first.night_id, self.host)
        self.end()
        second = services.start_next_set(self.first.night_id, self.host)
        with self.assertRaisesMessage(RuleError, "Set 2 is still open"):
            services.start_next_set(self.first.night_id, self.host)  # a second tap
        self.assertEqual(GameSession.objects.filter(night=self.first.night).count(), 2)
        services.transition(second.pk, self.host, "start")
        with self.assertRaisesMessage(RuleError, "Set 2 is still running"):
            services.start_next_set(self.first.night_id, self.host)

    def test_refused_for_a_closed_session_a_player_and_another_group(self):
        self.end()
        with self.assertRaises(NotAllowed):
            services.start_next_set(self.first.night_id, add_player(self.group, "player"))
        _, other_host = make_group("omar", "Other")
        with self.assertRaises(RuleError):
            services.start_next_set(self.first.night_id, other_host)
        GameNight.objects.filter(pk=self.first.night_id).update(status="closed")
        with self.assertRaisesMessage(RuleError, "closed"):
            services.start_next_set(self.first.night_id, self.host)

    def test_a_set_cannot_resume_after_the_next_set_started(self):
        self.end()
        second = services.start_next_set(self.first.night_id, self.host)
        with self.assertRaisesMessage(RuleError, "later set"):
            services.transition(self.first.pk, self.host, "resume")
        services.transition(second.pk, self.host, "cancel", "nobody stayed")
        with self.assertRaisesMessage(RuleError, "later set"):
            services.transition(self.first.pk, self.host, "resume")

    def test_third_set_follows_a_canceled_set_and_takes_players_from_the_last_played_one(self):
        self.end()
        second = services.start_next_set(self.first.night_id, self.host)
        services.withdraw_participant(second.pk, self.host, second.participants.first().pk)
        services.transition(second.pk, self.host, "cancel", "break for dinner")
        third = services.start_next_set(self.first.night_id, self.host)
        self.assertEqual(third.set_number, 3)
        self.assertEqual(self.names(third), ["Ana", "Ben", "Carlo", "Dani"])

    def test_host_can_change_the_roster_of_the_new_set_before_it_starts(self):
        self.end()
        second = services.start_next_set(self.first.night_id, self.host)
        late = groups.add_roster_player(self.host, "Elena")
        services.add_participant(second.pk, self.host, late.pk)
        services.withdraw_participant(second.pk, self.host, Participant.objects.get(session=second, member__display_name="Ana").pk)
        services.transition(second.pk, self.host, "start")
        self.assertEqual(self.names(second), ["Ben", "Carlo", "Dani", "Elena"])


class NextSetPageTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.ben = add_player(self.group, "ben")
        self.first = make_session(self.host, state="running")
        self.night_url = reverse("night", args=[self.first.night_id])
        self.url = reverse("next_set", args=[self.first.night_id])

    def test_button_appears_only_after_play_has_ended(self):
        self.client.force_login(self.host.user)
        self.assertNotContains(self.client.get(self.night_url), "Start next set")
        services.transition(self.first.pk, self.host, "end")
        self.assertContains(self.client.get(self.night_url), "Start next set")
        page = self.client.post(self.url, follow=True)
        second = GameSession.objects.get(set_number=2)
        self.assertRedirects(page, reverse("session", args=[second.pk]))
        self.assertContains(page, "Set 2 is open")
        self.assertNotContains(self.client.get(self.night_url), "Start next set")
        page = self.client.post(self.url, follow=True)  # a repeated tap
        self.assertContains(page, "Set 2 is still open")
        self.assertEqual(GameSession.objects.count(), 2)

    def test_player_and_stranger_are_refused(self):
        services.transition(self.first.pk, self.host, "end")
        self.client.force_login(self.ben.user)
        self.assertNotContains(self.client.get(self.night_url), "Start next set")
        self.assertEqual(self.client.post(self.url).status_code, 403)
        self.client.force_login(make_user("stranger"))
        self.assertEqual(self.client.post(self.url).status_code, 404)
        self.assertEqual(GameSession.objects.count(), 1)
