"""A member at the table of an unfinished set stays on the roster."""

import uuid

from django.test import TestCase

from games import services
from games.tests.test_add_players import Roster
from groups import services as groups
from groups.errors import RuleError
from groups.models import Member


class RemovalGuardTests(TestCase):
    def test_a_seated_player_is_refused_in_every_unfinished_state(self):
        for state in ("setup", "open", "running", "reconciliation"):
            with self.subTest(state=state):
                roster = Roster(state="open" if state == "reconciliation" else state)
                roster.add("Carlo")
                if state == "reconciliation":
                    services.transition(roster.session.pk, roster.host, "start", opening_buy_ins=False)
                    services.transition(roster.session.pk, roster.host, "end")
                carlo = roster.members["Carlo"]
                reason = groups.removal_refusal(roster.host, carlo.pk)
                self.assertEqual(reason, "Carlo is at the table in Friday table set 1. Take them off that set or finish it first.")
                with self.assertRaisesMessage(RuleError, "at the table"):
                    groups.remove_member(roster.host, carlo.pk)
                self.assertEqual(Member.objects.get(pk=carlo.pk).status, "active")
                self.assertIsNone(groups.removal_refusal(roster.host, roster.members["Dani"].pk))

    def test_withdrawn_left_and_finished_do_not_block(self):
        roster = Roster()
        seats = {p.member.display_name: p for p in roster.add("Carlo", "Dani", "Ana")}
        services.withdraw_participant(roster.session.pk, roster.host, seats["Carlo"].pk)
        groups.remove_member(roster.host, roster.members["Carlo"].pk)
        services.transition(roster.session.pk, roster.host, "start", opening_buy_ins=False)
        services.set_left(roster.session.pk, roster.host, seats["Dani"].pk)
        groups.remove_member(roster.host, roster.members["Dani"].pk)
        services.transition(roster.session.pk, roster.host, "cancel", "Rain")
        groups.remove_member(roster.host, roster.members["Ana"].pk)
        self.assertEqual(Member.objects.filter(group=roster.group, status="removed").count(), 3)

    def test_the_guard_names_the_set_for_the_page(self):
        roster = Roster()
        roster.add("Carlo")
        blocking = services.sets_seating(roster.members["Carlo"])
        self.assertEqual([s.pk for s in blocking], [roster.session.pk])

    def test_a_removed_name_at_the_table_says_where_to_bring_them_back(self):
        roster = Roster(state="running")
        groups.remove_member(roster.host, roster.members["Carlo"].pk)
        with self.assertRaisesMessage(RuleError, "Carlo was removed from this group. Bring them back in Group settings, then add them here."):
            services.add_new_player(roster.session.pk, roster.host, "carlo", uuid.uuid4())
        self.assertEqual(Member.objects.filter(group=roster.group, display_name__iexact="carlo").count(), 1)

    def test_a_removed_player_who_left_is_not_brought_back_to_the_table(self):
        roster = Roster(state="running")
        seat = roster.add("Dani")[0]
        services.set_left(roster.session.pk, roster.host, seat.pk)
        groups.remove_member(roster.host, roster.members["Dani"].pk)
        with self.assertRaisesMessage(RuleError, "Dani was removed from this group. Bring them back in Group settings first."):
            services.set_left(roster.session.pk, roster.host, seat.pk, left=False)
        groups.restore_member(roster.host, roster.members["Dani"].pk)
        self.assertEqual(services.set_left(roster.session.pk, roster.host, seat.pk, left=False).status, "joined")
