from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from games import services
from games.models import Participant
from groups import services as groups
from groups.errors import NotAllowed, RuleError
from groups.tests.helpers import add_player, make_group, make_user

from .helpers import make_session


class JoinTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.ben = add_player(self.group, "ben")
        self.cy = add_player(self.group, "cy")

    def test_player_joins_once(self):
        session = make_session(self.host, state="open")
        first = services.add_participant(session.pk, self.ben, self.ben.pk)
        again = services.add_participant(session.pk, self.ben, self.ben.pk)
        self.assertEqual(first.pk, again.pk)
        self.assertEqual(Participant.objects.filter(session=session).count(), 1)

    def test_database_refuses_a_second_row(self):
        session = make_session(self.host, state="open")
        services.add_participant(session.pk, self.ben, self.ben.pk)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Participant.objects.create(session=session, member=self.ben, join_order=9, added_by=self.ben.user)

    def test_join_order_follows_arrival(self):
        session = make_session(self.host, state="open")
        for member in (self.cy, self.host, self.ben):
            services.add_participant(session.pk, member, member.pk)
        names = [p.member.display_name for p in session.participants.order_by("join_order")]
        self.assertEqual(names, ["cy", "hana", "ben"])

    def test_full_table_refuses_the_next_join(self):
        session = make_session(self.host, state="open", seat_count=2)
        services.add_participant(session.pk, self.host, self.host.pk)
        services.add_participant(session.pk, self.ben, self.ben.pk)
        with self.assertRaisesMessage(RuleError, "full"):
            services.add_participant(session.pk, self.cy, self.cy.pk)

    def test_player_joins_late_but_not_in_other_states(self):
        session = make_session(self.host, state="running")
        services.add_participant(session.pk, self.ben, self.ben.pk)  # late join
        for state in ("setup", "reconciliation"):
            other = make_session(self.host, state=state, table_name=f"T-{state}")
            with self.assertRaises(RuleError):
                services.add_participant(other.pk, self.cy, self.cy.pk)

    def test_host_adds_roster_players_and_a_player_cannot_add_others(self):
        session = make_session(self.host)  # still in setup
        guest = groups.add_roster_player(self.host, "Tito Boy")
        services.add_participant(session.pk, self.host, guest.pk)
        services.transition(session.pk, self.host, "open")
        with self.assertRaises(NotAllowed):
            services.add_participant(session.pk, self.ben, self.cy.pk)

    def test_member_of_another_group_cannot_be_added_or_join(self):
        other_group, other_host = make_group("omar", "Other")
        session = make_session(self.host, state="open")
        with self.assertRaises(RuleError):
            services.add_participant(session.pk, self.host, other_host.pk)
        with self.assertRaises(RuleError):
            services.add_participant(session.pk, other_host, other_host.pk)

    def test_withdraw_frees_the_seat_and_rejoin_reuses_the_row(self):
        session = make_session(self.host, state="open", seat_count=2)
        services.add_participant(session.pk, self.host, self.host.pk)
        ben = services.add_participant(session.pk, self.ben, self.ben.pk)
        services.withdraw_participant(session.pk, self.ben, ben.pk)
        services.add_participant(session.pk, self.cy, self.cy.pk)
        services.withdraw_participant(session.pk, self.host, Participant.objects.get(member=self.cy).pk)
        back = services.add_participant(session.pk, self.ben, self.ben.pk)
        self.assertEqual((back.pk, back.status, back.join_order), (ben.pk, "joined", 2))

    def test_player_cannot_withdraw_someone_else(self):
        session = make_session(self.host, state="open")
        cy = services.add_participant(session.pk, self.cy, self.cy.pk)
        with self.assertRaises(NotAllowed):
            services.withdraw_participant(session.pk, self.ben, cy.pk)

    def test_exit_guards_can_refuse_a_withdrawal(self):
        session = make_session(self.host, state="open")
        ben = services.add_participant(session.pk, self.ben, self.ben.pk)

        def guard(participant):
            raise RuleError("has money")

        services.PARTICIPANT_EXIT_GUARDS.append(guard)
        self.addCleanup(services.PARTICIPANT_EXIT_GUARDS.remove, guard)
        with self.assertRaisesMessage(RuleError, "has money"):
            services.withdraw_participant(session.pk, self.ben, ben.pk)

    def test_left_frees_a_seat_and_only_a_host_brings_the_player_back(self):
        session = make_session(self.host, state="open", seat_count=2)
        services.add_participant(session.pk, self.host, self.host.pk)
        ben = services.add_participant(session.pk, self.ben, self.ben.pk)
        services.transition(session.pk, self.host, "start")
        with self.assertRaises(NotAllowed):
            services.set_left(session.pk, self.ben, ben.pk)
        ben = services.set_left(session.pk, self.host, ben.pk)
        self.assertEqual(ben.status, "left")
        self.assertIsNotNone(ben.left_at)
        with self.assertRaises(RuleError):
            services.add_participant(session.pk, self.ben, self.ben.pk)
        self.assertEqual(services.set_left(session.pk, self.host, ben.pk, False).status, "joined")


class JoinViewTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.ben = add_player(self.group, "ben")
        self.session = make_session(self.host, state="open", seat_count=2)

    def test_join_button_and_double_tap(self):
        self.client.force_login(self.ben.user)
        self.assertContains(self.client.get(reverse("session", args=[self.session.pk])), "Join this game")
        for _ in range(2):
            self.client.post(reverse("participant_add", args=[self.session.pk]))
        self.assertEqual(Participant.objects.filter(session=self.session).count(), 1)
        page = self.client.get(reverse("session", args=[self.session.pk]))
        self.assertNotContains(page, "Join this game")
        self.assertContains(page, "1 seat free")

    def test_full_table_message(self):
        services.add_participant(self.session.pk, self.host, self.host.pk)
        services.add_participant(self.session.pk, self.host, groups.add_roster_player(self.host, "Guest").pk)
        self.client.force_login(self.ben.user)
        self.assertContains(self.client.get(reverse("session", args=[self.session.pk])), "The table is full")
        response = self.client.post(reverse("participant_add", args=[self.session.pk]), follow=True)
        self.assertContains(response, "The table is full (2 seats).")

    def test_player_cannot_add_another_member_by_hand(self):
        cy = add_player(self.group, "cy")
        self.client.force_login(self.ben.user)
        response = self.client.post(reverse("participant_add", args=[self.session.pk]), {"member_id": cy.pk})
        self.assertEqual(response.status_code, 403)

    def test_stranger_gets_404(self):
        self.client.force_login(make_user("stranger"))
        self.assertEqual(self.client.post(reverse("participant_add", args=[self.session.pk])).status_code, 404)
