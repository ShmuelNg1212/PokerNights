import uuid
from unittest import mock

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from audit.models import AuditEvent
from games import services
from games.models import Participant, ParticipantBatch
from groups import services as groups
from groups.errors import NotAllowed, RuleError
from groups.models import Member
from groups.tests.helpers import make_group, make_user

from .helpers import make_session

NAMES = ["Ana", "Ben", "Carlo", "Dani"]


class Roster:
    """A group with a host, four roster players and a game. Two of the four have logins."""

    def __init__(self, state="open", seat_count=9):
        self.group, self.host = make_group()
        # Login names are unique site-wide; display names are per group.
        tag = self.group.pk
        self.members = {
            "Ana": Member.objects.create(group=self.group, user=make_user(f"ana{tag}"), display_name="Ana"),
            "Ben": Member.objects.create(group=self.group, user=make_user(f"ben{tag}"), display_name="Ben"),
            "Carlo": groups.add_roster_player(self.host, "Carlo"),
            "Dani": groups.add_roster_player(self.host, "Dani"),
        }
        self.session = make_session(self.host, state=state, seat_count=seat_count)

    def ids(self, *names):
        return [self.members[name].pk for name in names or NAMES]

    def add(self, *names, actor=None, request_id=None):
        return services.add_participants(self.session.pk, actor or self.host, self.ids(*names), request_id or uuid.uuid4())

    def at_table(self):
        return sorted(
            Participant.objects.filter(session=self.session, status="joined").values_list("member__display_name", flat=True)
        )

    def version(self):
        self.session.refresh_from_db()
        return self.session.version


class AddParticipantsTests(TestCase):
    def test_four_players_join_with_one_action(self):
        roster = Roster()
        before = roster.version()
        added = roster.add()
        self.assertEqual([p.member.display_name for p in added], NAMES)
        self.assertEqual([p.join_order for p in added], [1, 2, 3, 4])
        self.assertEqual(roster.at_table(), NAMES)
        self.assertEqual(roster.version(), before + 1)  # one update for the live view
        summaries = list(AuditEvent.objects.filter(action="participant.joined").values_list("summary", flat=True))
        self.assertEqual(summaries, [f"Added {name}" for name in NAMES])
        self.assertEqual(ParticipantBatch.objects.get().participants.count(), 4)

    def test_join_order_continues_after_players_already_there(self):
        roster = Roster()
        services.add_participant(roster.session.pk, roster.host, roster.host.pk)
        added = roster.add("Dani", "Ana")
        self.assertEqual([(p.member.display_name, p.join_order) for p in added], [("Dani", 2), ("Ana", 3)])

    def test_more_players_than_free_seats_adds_nobody(self):
        roster = Roster(seat_count=4)
        services.add_participant(roster.session.pk, roster.host, roster.host.pk)  # three seats stay free
        with self.assertRaisesMessage(RuleError, "Only 3 seats are free and you selected 4 players. Remove 1 player."):
            roster.add()
        self.assertEqual(roster.at_table(), ["hana"])
        self.assertEqual(ParticipantBatch.objects.count(), 0)
        roster.add("Ana", "Ben", "Carlo")  # a selection that fits is accepted
        self.assertEqual(len(roster.at_table()), 4)
        with self.assertRaisesMessage(RuleError, "No seat is free"):
            roster.add("Dani")

    def test_a_player_already_at_the_table_refuses_the_whole_selection(self):
        roster = Roster()
        services.add_participant(roster.session.pk, roster.host, roster.members["Ben"].pk)
        with self.assertRaisesMessage(RuleError, "Ben is already at the table. Nothing was added."):
            roster.add()
        self.assertEqual(roster.at_table(), ["Ben"])
        services.add_participant(roster.session.pk, roster.host, roster.members["Dani"].pk)
        with self.assertRaisesMessage(RuleError, "Ben and Dani are already at the table"):
            roster.add()

    def test_only_active_members_of_this_group_are_eligible(self):
        roster = Roster()
        other_group, other_host = make_group("omar", "Other")
        outsider = groups.add_roster_player(other_host, "Outsider")
        groups.remove_member(roster.host, roster.members["Carlo"].pk)
        for bad in (outsider.pk, roster.members["Carlo"].pk, 999999):
            with self.assertRaisesMessage(RuleError, "no longer in this group"):
                services.add_participants(roster.session.pk, roster.host, [roster.members["Ana"].pk, bad], uuid.uuid4())
        with self.assertRaises(RuleError):
            services.add_participants(roster.session.pk, roster.host, ["abc"], uuid.uuid4())
        self.assertEqual(roster.at_table(), [])

    def test_empty_selection_is_refused_and_a_repeated_id_counts_once(self):
        roster = Roster()
        with self.assertRaisesMessage(RuleError, "Select at least one player"):
            services.add_participants(roster.session.pk, roster.host, [], uuid.uuid4())
        ana = roster.members["Ana"].pk
        added = services.add_participants(roster.session.pk, roster.host, [ana, str(ana), ana], uuid.uuid4())
        self.assertEqual(len(added), 1)
        self.assertEqual(roster.at_table(), ["Ana"])

    def test_players_who_left_or_withdrew_return_on_the_same_row(self):
        roster = Roster(state="running")
        first = {p.member.display_name: p for p in roster.add("Ana", "Ben", "Carlo")}
        services.set_left(roster.session.pk, roster.host, first["Ana"].pk)
        services.withdraw_participant(roster.session.pk, roster.host, first["Ben"].pk)
        again = roster.add("Ana", "Ben", "Dani")
        self.assertEqual([p.pk for p in again[:2]], [first["Ana"].pk, first["Ben"].pk])
        self.assertEqual([(p.status, p.left_at) for p in again[:2]], [("joined", None), ("joined", None)])
        self.assertEqual(again[2].join_order, 4)
        self.assertEqual(Participant.objects.filter(session=roster.session).count(), 4)

    def test_only_a_host_of_this_group(self):
        roster = Roster()
        with self.assertRaises(NotAllowed):
            roster.add(actor=roster.members["Ana"])
        _, other_host = make_group("omar", "Other")
        with self.assertRaises(RuleError):
            roster.add(actor=other_host)
        self.assertEqual(roster.at_table(), [])

    def test_allowed_in_setup_open_and_running_only(self):
        for state in ("setup", "open", "running"):
            roster = Roster(state=state)
            roster.add("Ana")
            self.assertEqual(roster.at_table(), ["Ana"], state)
        roster = Roster(state="reconciliation")
        with self.assertRaisesMessage(RuleError, "cannot be added at this stage"):
            roster.add("Ana")
        roster = Roster(state="open")
        services.transition(roster.session.pk, roster.host, "cancel", "rain")
        with self.assertRaises(RuleError):
            roster.add("Ana")

    def test_retry_of_a_successful_request_adds_nobody_twice(self):
        roster = Roster()
        request_id = uuid.uuid4()
        first = roster.add(request_id=request_id)
        version, events = roster.version(), AuditEvent.objects.count()
        again = roster.add(request_id=request_id)
        self.assertEqual([p.pk for p in again], [p.pk for p in first])
        self.assertEqual((roster.version(), AuditEvent.objects.count()), (version, events))
        self.assertEqual((ParticipantBatch.objects.count(), Participant.objects.count()), (1, 4))
        with self.assertRaises(IntegrityError), transaction.atomic():
            ParticipantBatch.objects.create(session=roster.session, request_id=request_id, added_by=roster.host.user)

    def test_a_failure_in_the_middle_leaves_nothing_behind(self):
        roster = Roster()
        version, events = roster.version(), AuditEvent.objects.count()
        calls = {"n": 0}
        real = services.audit.record

        def fail_on_third(*args, **kwargs):
            calls["n"] += 1
            if calls["n"] == 3:
                raise RuntimeError("boom")
            return real(*args, **kwargs)

        with mock.patch("games.services.audit.record", side_effect=fail_on_third):
            with self.assertRaises(RuntimeError):
                roster.add()
        self.assertEqual(roster.at_table(), [])
        self.assertEqual((Participant.objects.count(), ParticipantBatch.objects.count()), (0, 0))
        self.assertEqual((roster.version(), AuditEvent.objects.count()), (version, events))

    def test_single_add_still_works_next_to_the_batch(self):
        roster = Roster()
        roster.add("Ana", "Ben")
        single = services.add_participant(roster.session.pk, roster.host, roster.members["Carlo"].pk)
        self.assertEqual(single.join_order, 3)
        self.assertEqual(roster.at_table(), ["Ana", "Ben", "Carlo"])


class AddPlayersPageTests(TestCase):
    def setUp(self):
        self.roster = Roster()
        self.url = reverse("participants_add", args=[self.roster.session.pk])
        self.client.force_login(self.roster.host.user)

    def post(self, *names, **extra):
        return self.client.post(self.url, {"member_id": self.roster.ids(*names), **extra})

    def test_game_page_offers_add_players_to_a_host_and_keeps_the_single_flow(self):
        page = self.client.get(reverse("session", args=[self.roster.session.pk]))
        self.assertContains(page, self.url)
        self.assertContains(page, "Add players")
        self.assertContains(page, 'name="member_id"')  # the one-player dropdown is still there

    def test_picker_lists_members_with_labels_seats_and_disabled_rows(self):
        services.add_participant(self.roster.session.pk, self.roster.host, self.roster.members["Ben"].pk)
        page = self.client.get(self.url)
        self.assertContains(page, "<strong>8</strong> of 9 seats are free.")
        ben, ana = self.roster.members["Ben"].pk, self.roster.members["Ana"].pk
        self.assertContains(page, f'value="{ben}" data-label="Ben"\n                 disabled')
        self.assertContains(page, "At the table")
        self.assertNotContains(page, f'value="{ana}" data-label="Ana"\n                 disabled')
        self.assertContains(page, "No login")  # roster players without logins are listed too
        self.assertContains(page, '<label for="pick-search">Search players</label>', html=True)
        self.assertContains(page, "js/pick.js")
        self.assertEqual(page.content.decode().count("<label class=\"check"), 5)  # host + four players

    def test_one_confirmation_adds_four_and_reports_it(self):
        page = self.client.post(self.url, {"member_id": self.roster.ids()}, follow=True)
        self.assertRedirects(page, reverse("session", args=[self.roster.session.pk]))
        self.assertContains(page, "Added 4 players: Ana, Ben, Carlo, Dani.")
        self.assertEqual(self.roster.at_table(), NAMES)

    def test_resending_the_same_form_adds_nobody_twice_and_shows_success(self):
        request_id = str(uuid.uuid4())
        self.post(request_id=request_id)
        response = self.post(request_id=request_id)
        self.assertRedirects(response, reverse("session", args=[self.roster.session.pk]))
        self.assertEqual((Participant.objects.count(), ParticipantBatch.objects.count()), (4, 1))

    def test_over_capacity_explains_and_keeps_the_selection(self):
        roster = Roster(seat_count=3)
        self.client.force_login(roster.host.user)
        url = reverse("participants_add", args=[roster.session.pk])
        page = self.client.post(url, {"member_id": roster.ids()})
        self.assertContains(page, "Only 3 seats are free and you selected 4 players. Remove 1 player.")
        self.assertEqual(page.content.decode().count(" checked"), 4)
        self.assertEqual(roster.at_table(), [])

    def test_roster_changed_by_another_host_shows_the_conflict_and_keeps_the_rest(self):
        self.client.get(self.url)  # the host opens the picker
        services.add_participant(self.roster.session.pk, self.roster.host, self.roster.members["Ben"].pk)  # meanwhile
        page = self.post()
        self.assertContains(page, "Ben is already at the table. Nothing was added.")
        self.assertContains(page, "<strong>8</strong> of 9 seats are free.")
        html = page.content.decode()
        self.assertEqual(html.count(" checked"), 3)  # Ana, Carlo and Dani stay ticked
        ben = self.roster.members["Ben"].pk
        self.assertIn(f'value="{ben}" data-label="Ben"\n                 disabled', html)
        self.assertEqual(self.roster.at_table(), ["Ben"])
        self.assertRedirects(self.post("Ana", "Carlo", "Dani"), reverse("session", args=[self.roster.session.pk]))
        self.assertEqual(self.roster.at_table(), NAMES)

    def test_empty_selection_shows_a_message(self):
        page = self.client.post(self.url, {})
        self.assertContains(page, "Select at least one player")

    def test_player_stranger_and_signed_out_are_refused(self):
        self.client.force_login(self.roster.members["Ana"].user)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.post().status_code, 403)
        page = self.client.get(reverse("session", args=[self.roster.session.pk]))
        self.assertNotContains(page, self.url)
        self.client.force_login(make_user("stranger"))
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.post().status_code, 404)
        self.client.logout()
        self.assertEqual(self.post().status_code, 302)
        self.assertEqual(self.roster.at_table(), [])

    def test_picker_is_closed_once_play_has_ended(self):
        for action in ("start", "end"):
            services.transition(self.roster.session.pk, self.roster.host, action)
        response = self.client.get(self.url, follow=True)
        self.assertContains(response, "cannot be added at this stage")
        self.post()
        self.assertEqual(self.roster.at_table(), [])

    def test_everyone_at_the_table_shows_no_form(self):
        self.post()
        services.add_participant(self.roster.session.pk, self.roster.host, self.roster.host.pk)
        self.assertContains(self.client.get(self.url), "Every player of this group is already at the table.")
