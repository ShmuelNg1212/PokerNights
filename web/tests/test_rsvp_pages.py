"""RSVP screens: the Announce card, "Coming up" on the Sessions tab, "Who's coming", and set 1's add-players."""

import uuid

from django.test import TestCase, override_settings
from django.urls import reverse

from games import services
from games.models import Rsvp
from games.tests.helpers import make_session
from groups.models import Member
from groups.tests.helpers import add_player, make_group


@override_settings(TABLE_NOTICES=True)
class RsvpPageTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.first = make_session(self.host, seat_count=2)
        self.night = self.first.night
        self.ana, self.ben, self.carlo = (add_player(self.group, n) for n in ("ana", "ben", "carlo"))

    def as_(self, member):
        self.client.force_login(member.user)

    def post(self, name, data=None):
        return self.client.post(reverse(name, args=[self.night.pk]), data or {})

    def tab(self):
        return self.client.get(reverse("group", args=[self.group.pk])).content.decode()

    # --- Announce --------------------------------------------------------------

    def test_a_host_sees_the_announce_card_and_announces(self):
        self.as_(self.host)
        page = self.client.get(reverse("night", args=[self.night.pk])).content.decode()
        self.assertIn("Announce to the group", page)
        self.assertIn("3 players with a login get a notice", page)
        response = self.post("night_announce", {"start_time": "20:00", "seat_limit": "2"})
        self.assertEqual(response.status_code, 302)
        self.night.refresh_from_db()
        self.assertEqual((str(self.night.start_time), self.night.seat_limit), ("20:00:00", 2))

    def test_a_refused_announce_keeps_what_was_typed(self):
        self.as_(self.host)
        self.post("night_announce", {"start_time": "20:30", "seat_limit": "20"})
        page = self.client.get(reverse("night", args=[self.night.pk])).content.decode()
        self.assertIn("Seats must be between 2 and 12", page)
        self.assertIn('value="20:30"', page)
        self.assertIn('value="20"', page)

    def test_a_player_cannot_announce(self):
        services.announce_night(self.night.pk, self.host)  # so the player can reach the session at all
        self.as_(self.ana)
        self.assertEqual(self.post("night_announce").status_code, 403)

    # --- Visibility ------------------------------------------------------------

    def test_a_player_sees_an_announced_draft_but_not_its_set(self):
        self.as_(self.ana)
        self.assertEqual(self.client.get(reverse("night", args=[self.night.pk])).status_code, 404)
        self.assertNotIn("Coming up", self.tab())
        services.announce_night(self.night.pk, self.host)
        self.assertEqual(self.client.get(reverse("night", args=[self.night.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("session", args=[self.first.pk])).status_code, 404)
        self.assertIn("Coming up", self.tab())

    def test_another_group_gets_404(self):
        services.announce_night(self.night.pk, self.host)
        _, stranger = make_group("zed", "Other")
        self.as_(stranger)
        self.assertEqual(self.client.get(reverse("night", args=[self.night.pk])).status_code, 404)
        self.assertEqual(self.post("night_rsvp", {"going": "in"}).status_code, 404)

    # --- Answers ---------------------------------------------------------------

    def test_a_player_answers_from_the_tab_and_sees_each_state(self):
        services.announce_night(self.night.pk, self.host)
        services.answer_rsvp(self.night.pk, self.ben, self.ben.pk, True, uuid.uuid4())
        services.answer_rsvp(self.night.pk, self.carlo, self.carlo.pk, True, uuid.uuid4())
        self.as_(self.ana)
        self.assertIn("Join the waitlist", self.tab())
        response = self.post("night_rsvp", {"going": "in", "back": "tab", "request_id": str(uuid.uuid4())})
        self.assertRedirects(response, reverse("group", args=[self.group.pk]) + f"#coming-{self.night.pk}",
                             fetch_redirect_response=False)
        self.assertIn("Waitlist · 1st in line", self.tab())
        self.as_(self.ben)
        self.assertIn("You're in", self.tab())
        self.post("night_rsvp", {"going": "out", "back": "tab"})
        self.assertIn("You said you can't make it", self.tab())
        self.as_(self.ana)
        self.assertIn("You're in", self.tab())

    def test_a_player_cannot_answer_for_another(self):
        services.announce_night(self.night.pk, self.host)
        self.as_(self.ana)
        self.assertEqual(self.post("night_rsvp", {"going": "in", "member": self.ben.pk}).status_code, 403)
        self.assertFalse(Rsvp.objects.exists())

    def test_a_host_answers_seats_and_marks_out_from_the_session_page(self):
        services.announce_night(self.night.pk, self.host)
        fe = Member.objects.create(group=self.group, display_name="Fe")
        self.as_(self.host)
        page = self.client.get(reverse("night", args=[self.night.pk])).content.decode()
        self.assertIn("Not answered", page)
        for member in (fe, self.ana, self.ben):
            self.post("night_rsvp", {"going": "in", "member": member.pk})
        page = self.client.get(reverse("night", args=[self.night.pk])).content.decode()
        self.assertIn("Seat now", page)
        self.assertIn("answered by", page)
        self.post("night_seat_now", {"member": self.ben.pk})
        self.night.refresh_from_db()
        self.assertEqual(self.night.seat_limit, 3)
        response = self.post("night_seats", {"seat_limit": "2"})
        page = self.client.get(response.url).content.decode()
        self.assertIn("3 players are coming. Mark someone out first.", page)

    def test_answers_close_once_play_starts(self):

        services.announce_night(self.night.pk, self.host)
        services.transition(self.first.pk, self.host, "open")
        services.transition(self.first.pk, self.host, "start")
        self.as_(self.ana)
        self.post("night_rsvp", {"going": "in"})
        self.assertFalse(Rsvp.objects.exists())
        self.assertNotIn("Coming up", self.tab())

    def test_opening_the_session_page_clears_the_rsvp_notice(self):
        from notify.models import Notice

        services.announce_night(self.night.pk, self.host)
        self.as_(self.ana)
        self.client.get(reverse("night", args=[self.night.pk]))
        self.assertIsNotNone(Notice.objects.get(user=self.ana.user, night_id=self.night.pk).seen_at)

    def test_an_answer_changes_the_page_stamp(self):
        services.announce_night(self.night.pk, self.host)
        self.as_(self.ana)
        url = reverse("night_state", args=[self.night.pk])
        page = self.client.get(reverse("night", args=[self.night.pk])).content.decode()
        stamp = page.split('data-stamp="')[1].split('"')[0]
        self.assertEqual(self.client.get(url, {"v": stamp}).status_code, 204)
        services.answer_rsvp(self.night.pk, self.ben, self.ben.pk, True, uuid.uuid4())
        self.assertEqual(self.client.get(url, {"v": stamp}).status_code, 200)

    # --- Set 1 -----------------------------------------------------------------

    def test_set_one_add_players_ticks_the_confirmed(self):
        services.announce_night(self.night.pk, self.host)
        for member in (self.ana, self.ben, self.carlo):
            services.answer_rsvp(self.night.pk, member, member.pk, True, uuid.uuid4())
        self.as_(self.host)
        response = self.client.get(reverse("participants_add", args=[self.first.pk]))
        rows = {row["member"].pk: row for row in response.context["rows"]}
        self.assertTrue(rows[self.ana.pk]["checked"] and rows[self.ben.pk]["checked"])
        self.assertFalse(rows[self.carlo.pk]["checked"])
        self.assertEqual(rows[self.carlo.pk]["rsvp"], ("waitlisted", 1))
        self.assertEqual([r["member"] for r in response.context["rows"]][:3], [self.ana, self.ben, self.carlo])

    def test_an_unannounced_set_ticks_nobody(self):
        self.as_(self.host)
        response = self.client.get(reverse("participants_add", args=[self.first.pk]))
        self.assertFalse(any(row["checked"] for row in response.context["rows"]))


class RsvpQueryCountTests(TestCase):
    def test_the_sessions_tab_reads_rsvps_in_constant_queries(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        group, host = make_group()
        players = [add_player(group, f"q{i}") for i in range(30)]
        self.client.force_login(host.user)
        url = reverse("group", args=[group.pk])

        def announce_one(name):
            night = make_session(host, table_name=name).night
            services.announce_night(night.pk, host)
            for member in players[:12]:
                services.answer_rsvp(night.pk, member, member.pk, True, uuid.uuid4())

        announce_one("A")
        self.client.get(url)
        with CaptureQueriesContext(connection) as one:
            self.client.get(url)
        announce_one("B")
        announce_one("C")
        with CaptureQueriesContext(connection) as three:
            self.client.get(url)
        self.assertEqual(len(three), len(one), [q["sql"] for q in three.captured_queries])


class RsvpHomeTests(TestCase):
    def test_your_groups_asks_until_the_player_answers(self):
        group, host = make_group()
        night = make_session(host).night
        ana = add_player(group, "ana")
        self.client.force_login(ana.user)
        self.assertNotIn("Are you in?", self.client.get(reverse("home")).content.decode())
        services.announce_night(night.pk, host, start_time=__import__("datetime").time(20, 0))
        page = self.client.get(reverse("home")).content.decode()
        self.assertIn("Are you in?", page)
        self.assertIn("8:00 PM", page)
        services.answer_rsvp(night.pk, ana, ana.pk, False, uuid.uuid4())
        self.assertNotIn("Are you in?", self.client.get(reverse("home")).content.decode())


class RsvpBadInputTests(TestCase):
    def test_a_member_that_is_not_a_number_is_a_404(self):
        group, host = make_group()
        night = make_session(host).night
        services.announce_night(night.pk, host)
        self.client.force_login(host.user)
        for name in ("night_rsvp", "night_seat_now"):
            self.assertEqual(self.client.post(reverse(name, args=[night.pk]), {"member": "x'", "going": "in"}).status_code, 404)


@override_settings(TABLE_NOTICES=True)
class RsvpPageReviewFixTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.first = make_session(self.host, seat_count=2)
        self.night = self.first.night
        self.ana, self.ben, self.carlo = (add_player(self.group, n) for n in ("ana", "ben", "carlo"))
        services.announce_night(self.night.pk, self.host)

    def test_coming_up_stays_while_set_one_is_open(self):
        services.transition(self.first.pk, self.host, "open")
        self.client.force_login(self.ana.user)
        page = self.client.get(reverse("group", args=[self.group.pk])).content.decode()
        self.assertIn("Coming up", page)
        self.assertIn("Set 1 · Open", page)  # and the set is on Now playing
        self.assertIn("Are you in?", self.client.get(reverse("home")).content.decode())

    def test_answered_by_names_the_host_as_the_group_knows_them(self):
        self.host.display_name = "Hana T."
        self.host.save()
        fe = Member.objects.create(group=self.group, display_name="Fe")
        services.answer_rsvp(self.night.pk, self.host, fe.pk, True, uuid.uuid4())
        self.client.force_login(self.ana.user)
        page = self.client.get(reverse("night", args=[self.night.pk])).content.decode()
        self.assertIn("answered by Hana T.", page)
        self.assertNotIn(f"answered by {self.host.user.username}", page)

    def test_add_players_ticks_no_more_than_the_free_seats(self):
        from games.models import GameSession

        for member in (self.ana, self.ben, self.carlo):
            services.answer_rsvp(self.night.pk, member, member.pk, True, uuid.uuid4())
        services.seat_from_waitlist(self.night.pk, self.host, self.carlo.pk)
        GameSession.objects.filter(pk=self.first.pk).update(seat_count=2)  # as if set 1 had fewer seats
        self.client.force_login(self.host.user)
        rows = self.client.get(reverse("participants_add", args=[self.first.pk])).context["rows"]
        self.assertEqual([r["member"] for r in rows if r["checked"]], [self.ana, self.ben])
