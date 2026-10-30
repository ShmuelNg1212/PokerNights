"""Add players in one send: roster players ticked and new names typed one per line."""

import re
import uuid

from django.test import TestCase, override_settings
from django.urls import reverse

from audit.models import AuditEvent
from games import services
from games.models import ParticipantBatch, PlayInterval
from groups import services as groups
from groups.errors import RuleError
from groups.models import Member

from .helpers import make_session
from .test_add_players import Roster


class AddPlayersServiceTests(TestCase):
    def setUp(self):
        self.r = Roster(state="running")

    def add(self, ticked=(), lines=(), request_id=None):
        return services.add_players(self.r.session.pk, self.r.host, [m.pk for m in ticked], lines, request_id or uuid.uuid4())

    def test_ticks_and_new_names_join_in_one_send(self):
        audits = AuditEvent.objects.count()
        added = self.add([self.r.members["Ana"], self.r.members["Ben"]], ["Lia", "  Mo   Reyes ", "", "Ned"])
        self.assertEqual([p.member.display_name for p in added], ["Ana", "Ben", "Lia", "Mo Reyes", "Ned"])
        new = Member.objects.filter(group=self.r.group, display_name__in=["Lia", "Mo Reyes", "Ned"])
        self.assertEqual(new.count(), 3)
        self.assertFalse(new.filter(user__isnull=False).exists())
        self.assertEqual(ParticipantBatch.objects.count(), 1)
        made = AuditEvent.objects.order_by("pk")[audits:]
        self.assertEqual([e.action for e in made].count("member.added"), 3)
        self.assertEqual([e.action for e in made].count("participant.joined"), 5)
        # In play, each new player's clock starts.
        self.assertEqual(PlayInterval.objects.filter(participant__in=added).count(), 5)

    def test_every_problem_is_named_at_once_and_nobody_is_added(self):
        self.r.add("Ben")
        groups.remove_member(self.r.host, groups.add_roster_player(self.r.host, "Gone").pk)
        before = Member.objects.count()
        with self.assertRaises(services.NamesRefused) as refused:
            self.add([self.r.members["Carlo"]], ["ana", "BEN", "Lia", "lia", "Gone", "x" * 61])
        message = str(refused.exception)
        for part in ("Already in this group: ana. Tick them in the list instead.", "Already at the table: BEN.",
                     "Typed twice: lia.", "Removed from this group: Gone.", "Too long (60 characters at most)", "Nothing was added."):
            self.assertIn(part, message)
        self.assertEqual(Member.objects.count(), before)
        self.assertFalse(self.r.session.participants.filter(member=self.r.members["Carlo"]).exists())

    def test_seats_are_counted_for_ticks_and_names_together(self):
        self.r.session.seat_count = 3
        self.r.session.save(update_fields=["seat_count"])  # fixture only
        with self.assertRaises(RuleError) as refused:
            self.add([self.r.members["Ana"], self.r.members["Ben"]], ["Lia", "Mo"])
        self.assertEqual(str(refused.exception), "Only 3 seats are free and you are adding 4 players. Remove 1 player. Nothing was added.")
        self.assertFalse(Member.objects.filter(display_name="Lia").exists())

    def test_a_bad_tick_takes_the_new_names_back(self):
        with self.assertRaises(RuleError):
            services.add_players(self.r.session.pk, self.r.host, ["nope"], ["Lia"], uuid.uuid4())
        self.assertFalse(Member.objects.filter(display_name="Lia").exists())

    def test_the_same_request_adds_nobody_twice(self):
        request_id = uuid.uuid4()
        first = self.add([self.r.members["Ana"]], ["Lia"], request_id)
        again = self.add([self.r.members["Ana"]], ["Lia"], request_id)
        self.assertEqual([p.pk for p in first], [p.pk for p in again])
        self.assertEqual(Member.objects.filter(display_name="Lia").count(), 1)

    def test_names_only_ticks_only_and_nothing(self):
        self.assertEqual([p.member.display_name for p in self.add(lines=["Lia"])], ["Lia"])
        self.assertEqual([p.member.display_name for p in self.add([self.r.members["Ana"]])], ["Ana"])
        with self.assertRaisesMessage(RuleError, "Select at least one player."):
            self.add(lines=["", "  "])

    def test_every_state_that_takes_players(self):
        for state in ("setup", "open", "running"):
            with self.subTest(state=state):
                session = make_session(self.r.host, state=state, table_name=f"T {state}")
                added = services.add_players(session.pk, self.r.host, [], [f"New {state}"], uuid.uuid4())
                self.assertEqual(len(added), 1)
        session = make_session(self.r.host, state="reconciliation", table_name="T end")
        with self.assertRaisesMessage(RuleError, "Players cannot be added at this stage of the set."):
            services.add_players(session.pk, self.r.host, [], ["Late"], uuid.uuid4())

    @override_settings(ROSTER_TOOLS=False)
    def test_with_the_roster_tools_off_one_name_at_a_time(self):
        with self.assertRaisesMessage(services.NamesRefused, "Type one new name at a time."):
            self.add(lines=["Lia", "Mo"])
        self.assertEqual(len(self.add(lines=["Lia"])), 1)

    def test_a_player_cannot_add(self):
        with self.assertRaises(Exception):
            services.add_players(self.r.session.pk, self.r.members["Ana"], [], ["Lia"], uuid.uuid4())
        self.assertFalse(Member.objects.filter(display_name="Lia").exists())


class AddPlayersPageTests(TestCase):
    def setUp(self):
        self.r = Roster(state="running")
        self.url = reverse("participants_add", args=[self.r.session.pk])
        self.set_url = reverse("session", args=[self.r.session.pk])
        self.client.force_login(self.r.host.user)

    def test_a_mixed_send_and_the_arrivals_marked_once(self):
        ana, ben = self.r.members["Ana"], self.r.members["Ben"]
        page = self.client.post(self.url, {"member_id": [ana.pk, ben.pk], "names": "Lia\r\nMo\r\nNed", "request_id": str(uuid.uuid4())}, follow=True)
        self.assertContains(page, "Added 5 players: Ana, Ben, Lia, Mo, Ned.")
        html = page.content.decode()
        marked = re.findall(r'data-watch="player-(\d+)" data-arrived', html)
        self.assertEqual(sorted(map(int, marked)), sorted(self.r.session.participants.values_list("pk", flat=True)))
        # Once: the next view, and every live update, has no mark.
        self.assertNotIn("data-arrived", self.client.get(self.set_url).content.decode())

    def test_the_page_carries_what_the_preview_checks_against(self):
        self.r.add("Ben")
        groups.remove_member(self.r.host, groups.add_roster_player(self.r.host, "Gone").pk)
        html = self.client.get(self.url).content.decode()
        self.assertIn("data-known=", html)
        self.assertIn("&quot;seated&quot;: [&quot;ben&quot;]", html)
        self.assertIn("&quot;removed&quot;: [&quot;gone&quot;]", html)
        self.assertIn("&quot;ana&quot;: %d" % self.r.members["Ana"].pk, html)

    def test_a_refused_tick_list_keeps_the_names(self):
        page = self.client.post(self.url, {"member_id": ["999999"], "names": "Lia", "request_id": str(uuid.uuid4())})
        self.assertContains(page, "A selected player is no longer in this group.")
        self.assertContains(page, ">\nLia</textarea>")
        self.assertFalse(Member.objects.filter(display_name="Lia").exists())
