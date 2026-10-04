"""The settle status of closed sessions, read for a whole list at once. It is derived, never stored."""

import uuid

from django.test import TestCase
from django.urls import reverse

from games import services as games
from games.models import GameNight
from groups.tests.helpers import add_player
from ledger import services as ledger
from ledger.money import format_amount
from ledger.tests.helpers import Night
from settlement import queries, services
from settlement.models import Transfer

from .test_archive import closed_example


def close(night, figures):
    """Play one set to the end with ``{name: (buy_in, cash_out)}`` and close the session."""
    for name, (buy_in, _) in figures.items():
        night.buy(name, buy_in)
    games.transition(night.session.pk, night.host, "end")
    for name, (_, cash_out) in figures.items():
        night.cash(name, cash_out)
    services.finalize(night.session.pk, night.host)
    services.close_night(night.session.night_id, night.host)
    return night.session.night_id


class SettleStatesTests(TestCase):
    def setUp(self):
        self.night = closed_example()  # B and C each owe A
        self.host, self.night_id = self.night.host, self.night.session.night_id
        self.first, self.second = Transfer.objects.order_by("position")

    def state(self):
        return queries.settle_states([self.night_id])[self.night_id]

    def agrees(self):
        outcome = queries.night_outcome(GameNight.objects.get(pk=self.night_id))
        state = self.state()
        self.assertEqual((state.status, state.label, state.still_to_pay), (outcome.status, outcome.status_label, outcome.still_to_pay))
        return state

    def test_moves_from_unsettled_to_partly_to_settled(self):
        state = self.agrees()
        self.assertEqual((state.status, state.label, state.transfers, state.paid), ("unsettled", "Unsettled", 2, 0))
        self.assertEqual(state.still_to_pay, self.first.amount + self.second.amount)
        services.mark_paid(self.night_id, self.host, self.first.pk, uuid.uuid4())
        state = self.agrees()
        self.assertEqual((state.status, state.label, state.still_to_pay), ("partly", "Partly settled", self.second.amount))
        services.mark_paid(self.night_id, self.host, self.second.pk, uuid.uuid4())
        state = self.agrees()
        self.assertEqual((state.status, state.label, state.still_to_pay), ("settled", "Settled", 0))

    def test_an_undone_payment_does_not_count_and_a_repaid_one_counts_once(self):
        services.mark_paid(self.night_id, self.host, self.first.pk, uuid.uuid4())
        services.mark_unpaid(self.night_id, self.host, self.first.pk, "wrong tap")
        self.assertEqual(self.agrees().status, "unsettled")
        services.mark_paid(self.night_id, self.host, self.first.pk, uuid.uuid4())
        services.mark_unpaid(self.night_id, self.host, self.first.pk, "again")
        services.mark_paid(self.night_id, self.host, self.first.pk, uuid.uuid4())
        state = self.agrees()  # three payment rows for one transfer
        self.assertEqual((state.paid, state.transfers, state.still_to_pay), (1, 2, self.second.amount))

    def test_a_closed_session_with_no_transfer_is_settled(self):
        even = Night("A", "B")
        night_id = close(even, {"A": (1000, 1000), "B": (500, 500)})
        state = queries.settle_states([night_id])[night_id]
        self.assertEqual((state.status, state.transfers, state.still_to_pay), ("settled", 0, 0))
        self.assertEqual(queries.night_outcome(GameNight.objects.get(pk=night_id)).status, "settled")

    def test_chips_and_several_sessions_in_two_queries(self):
        chips = Night("A", "B", unit="chips")
        chips_id = close(chips, {"A": (1000, 1500), "B": (1000, 500)})
        even = Night("A", "B")
        even_id = close(even, {"A": (1000, 1000), "B": (500, 500)})
        with self.assertNumQueries(2):
            states = queries.settle_states([self.night_id, chips_id, even_id])
        self.assertEqual({k: v.status for k, v in states.items()}, {self.night_id: "unsettled", chips_id: "unsettled", even_id: "settled"})
        self.assertEqual(states[chips_id].still_to_pay, 500)  # whole chips
        with self.assertNumQueries(0):
            self.assertEqual(queries.settle_states([]), {})


class SettledIndicatorPagesTests(TestCase):
    def setUp(self):
        self.night = closed_example()
        self.host, self.group, self.night_id = self.night.host, self.night.group, self.night.session.night_id
        self.first, self.second = Transfer.objects.order_by("position")
        self.group_url = reverse("group", args=[self.group.pk])
        self.night_url = reverse("night", args=[self.night_id])
        self.client.force_login(self.host.user)

    def test_past_sessions_row_and_heading_follow_the_paid_marks(self):
        page = self.client.get(self.group_url)
        self.assertContains(page, '<span class="badge badge-warn">Unsettled</span>')
        self.assertContains(page, f"1 set · {format_amount(self.first.amount + self.second.amount, 'php')} still to pay")
        self.assertContains(page, "1 not settled")
        services.mark_paid(self.night_id, self.host, self.first.pk, uuid.uuid4())
        page = self.client.get(self.group_url)
        self.assertContains(page, '<span class="badge badge-warn">Partly settled</span>')
        self.assertContains(page, f"1 set · {format_amount(self.second.amount, 'php')} still to pay")
        services.mark_paid(self.night_id, self.host, self.second.pk, uuid.uuid4())
        page = self.client.get(self.group_url)
        self.assertContains(page, 'class="badge badge-good"')
        self.assertContains(page, "Settled</span>")
        self.assertNotContains(page, "still to pay")
        self.assertNotContains(page, "not settled")
        services.mark_unpaid(self.night_id, self.host, self.second.pk, "wrong tap")
        self.assertContains(self.client.get(self.group_url), "Partly settled")

    def test_player_sees_the_same_status(self):
        self.client.force_login(add_player(self.group, "reader").user)
        page = self.client.get(self.group_url)
        self.assertContains(page, "Unsettled")
        self.assertContains(page, "still to pay")

    def test_session_page_top_bar_names_the_status(self):
        bar = lambda: self.client.get(self.night_url).content.decode().split("</nav>")[0]
        self.assertIn("Unsettled", bar())
        self.assertNotIn("Session closed", bar())
        services.mark_paid(self.night_id, self.host, self.first.pk, uuid.uuid4())
        self.assertIn("Partly settled", bar())
        services.mark_paid(self.night_id, self.host, self.second.pk, uuid.uuid4())
        self.assertIn("badge-good", bar())
        self.assertIn("Settled", bar())
        games.archive_night(self.night_id, self.host)
        self.assertIn("Archived", bar())
        self.assertNotIn("Settled", bar())

    def test_open_session_keeps_its_badge_and_has_no_status(self):
        live = Night("A", state="running")
        self.client.force_login(live.host.user)
        page = self.client.get(reverse("night", args=[live.session.night_id]))
        self.assertIn("Session open", page.content.decode().split("</nav>")[0])
        self.assertNotContains(self.client.get(reverse("group", args=[live.group.pk])), "settled")

    def test_query_count_does_not_grow_with_past_sessions(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        from games.tests.helpers import make_session

        def count():
            with CaptureQueriesContext(connection) as captured:
                self.client.get(self.group_url)
            return len(captured)

        one = count()
        for _ in range(3):
            session = make_session(self.host, table=self.night.session.table, state="running")
            player = games.add_participant(session.pk, self.host, self.host.pk)
            ledger.record_buy_in(session.pk, self.host, player.pk, 100000, uuid.uuid4())
            games.transition(session.pk, self.host, "end")
            ledger.record_cash_out(session.pk, self.host, player.pk, 100000, uuid.uuid4())
            services.finalize(session.pk, self.host)
            services.close_night(session.night_id, self.host)
        self.assertEqual(count(), one)
