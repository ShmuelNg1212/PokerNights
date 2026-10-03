"""Cash out all counted players in one reviewed, all-or-nothing action."""

import uuid
from unittest import mock

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from audit.models import AuditEvent
from games import services as games
from groups.errors import NotAllowed, RuleError
from groups.tests.helpers import add_player, make_group, make_user
from ledger import queries, services
from ledger.models import CashOut, CashOutBatch, FinalCount, Finalization
from settlement.models import Payment

from .helpers import Night
from .test_counts import count, counting, statuses

SIX = ("A", "B", "C", "D", "E", "F")


def six_players():
    """Six players bought in ₱1,000 each; play has ended; four are counted, one of them at zero."""
    night = counting(*SIX)
    for name, pesos in (("A", 2500), ("B", 1500), ("C", 0), ("D", 800)):
        count(night, name, pesos)
    return night


def ready_ids(night):
    return [line.count.pk for line in queries.summary(night.session).ready_lines]


def run_batch(night, ids=None, request_id=None, actor=None):
    return services.cash_out_counted(
        night.session.pk, actor or night.host, ready_ids(night) if ids is None else ids, request_id or uuid.uuid4()
    )


class BatchTests(TestCase):
    def test_four_counted_players_are_cashed_out_and_two_stay_pending(self):
        night = six_players()
        before = night.refresh().version
        batch = run_batch(night)
        cash_outs = list(batch.cash_outs.order_by("participant__join_order"))
        self.assertEqual([(c.participant.member.display_name, c.amount, c.kind) for c in cash_outs], [
            ("A", 250000, "final"), ("B", 150000, "final"), ("C", 0, "final"), ("D", 80000, "final"),
        ])
        self.assertTrue(all(c.final_count_id and c.batch_id == batch.pk for c in cash_outs))
        self.assertEqual(statuses(night), {
            "A": "cashed_out", "B": "cashed_out", "C": "cashed_out", "D": "cashed_out", "E": "awaiting", "F": "awaiting",
        })
        self.assertEqual(night.refresh().version, before + 1)
        event = AuditEvent.objects.get(action="cash_out.batch")
        self.assertEqual((event.actor, event.summary), (night.host.user, "Cashed out 4 counted players: A, B, C, D (₱4,800 in all)"))
        self.assertEqual(AuditEvent.objects.filter(action="cash_out.recorded").count(), 4)

    def test_batch_does_not_finalize_the_set_or_mark_payments(self):
        night = six_players()
        run_batch(night)
        session = night.refresh()
        self.assertEqual(session.state, "reconciliation")
        self.assertEqual((Finalization.objects.count(), Payment.objects.count()), (0, 0))
        self.assertEqual(session.night.status, "open")
        balance = queries.balance(session)
        self.assertFalse(balance.ok)
        self.assertIn("Not cashed out yet: E, F", balance.explanation)

    def test_the_rest_is_cashed_out_by_running_the_action_again(self):
        night = six_players()
        run_batch(night)
        count(night, "E", 700)
        count(night, "F", 500)
        second = run_batch(night)
        self.assertEqual(second.cash_outs.count(), 2)
        self.assertEqual((CashOutBatch.objects.count(), CashOut.objects.count()), (2, 6))
        self.assertTrue(queries.balance(night.session).ok)  # 2,500 + 1,500 + 0 + 800 + 700 + 500 = 6,000

    def test_players_without_a_count_are_never_included(self):
        night = six_players()
        run_batch(night)
        self.assertFalse(CashOut.objects.filter(participant__in=[night.players["E"], night.players["F"]]).exists())
        with self.assertRaisesMessage(RuleError, "No player has a confirmed count yet"):
            run_batch(night)  # nobody is ready now

    def test_a_count_changed_after_the_review_rejects_the_whole_batch(self):
        night = six_players()
        reviewed = ready_ids(night)
        count(night, "B", 1400)  # another host corrects B while the review is open
        with self.assertRaisesMessage(RuleError, "B's count was changed or cleared. Nothing was recorded."):
            run_batch(night, reviewed)
        self.assertEqual((CashOut.objects.count(), CashOutBatch.objects.count()), (0, 0))
        self.assertEqual(len(ready_ids(night)), 4)  # the counts are kept
        self.assertEqual(run_batch(night).cash_outs.get(participant=night.players["B"]).amount, 140000)

    def test_a_cleared_count_or_a_player_cashed_out_elsewhere_rejects_the_batch(self):
        night = six_players()
        reviewed = ready_ids(night)
        services.clear_count(night.session.pk, night.host, night.players["D"].pk)
        with self.assertRaisesMessage(RuleError, "D's count was changed or cleared"):
            run_batch(night, reviewed)
        count(night, "D", 800)
        reviewed = ready_ids(night)
        night.cash("A", 2500)  # the individual action, in another tab
        with self.assertRaisesMessage(RuleError, "A was cashed out in the meantime"):
            run_batch(night, reviewed)
        self.assertEqual(CashOut.objects.count(), 1)

    def test_a_player_who_became_ready_after_the_review_is_left_for_the_next_run(self):
        night = six_players()
        reviewed = ready_ids(night)
        count(night, "E", 700)
        batch = run_batch(night, reviewed)
        self.assertEqual(batch.cash_outs.count(), 4)
        self.assertEqual(statuses(night)["E"], "ready")

    def test_a_failure_in_the_middle_records_nothing(self):
        night = six_players()
        version, events = night.refresh().version, AuditEvent.objects.count()
        calls = {"n": 0}
        real = services.audit.record

        def fail_on_third(*args, **kwargs):
            calls["n"] += 1
            if calls["n"] == 3:
                raise RuntimeError("boom")
            return real(*args, **kwargs)

        with mock.patch("ledger.services.audit.record", side_effect=fail_on_third):
            with self.assertRaises(RuntimeError):
                run_batch(night)
        self.assertEqual((CashOut.objects.count(), CashOutBatch.objects.count()), (0, 0))
        self.assertEqual((night.refresh().version, AuditEvent.objects.count()), (version, events))
        self.assertEqual(len(ready_ids(night)), 4)  # confirmed counts survive the failed request

    def test_repeated_request_records_each_cash_out_once(self):
        night = six_players()
        reviewed, request_id = ready_ids(night), uuid.uuid4()
        first = run_batch(night, reviewed, request_id)
        again = run_batch(night, reviewed, request_id)
        self.assertEqual(first.pk, again.pk)
        self.assertEqual((CashOutBatch.objects.count(), CashOut.objects.count()), (1, 4))
        with self.assertRaises(RuleError):
            run_batch(night, reviewed)  # the same review under a new request: the players are cashed out
        with self.assertRaises(IntegrityError), transaction.atomic():
            CashOutBatch.objects.create(session=night.session, request_id=request_id, recorded_by=night.host.user)

    def test_only_a_host_while_counting_up_and_only_this_sets_counts(self):
        night = six_players()
        with self.assertRaises(NotAllowed):
            run_batch(night, actor=add_player(night.group, "ben"))
        _, other_host = make_group("omar", "Other")
        with self.assertRaises(RuleError):
            run_batch(night, actor=other_host)
        other = counting("X")
        foreign = count(other, "X", 1000)
        with self.assertRaisesMessage(RuleError, "does not belong to this set"):
            run_batch(night, [foreign.pk])
        with self.assertRaises(RuleError):
            run_batch(night, ["abc"])
        reviewed = ready_ids(night)
        games.transition(night.session.pk, night.host, "resume")
        with self.assertRaisesMessage(RuleError, "after play has ended"):
            run_batch(night, reviewed)
        self.assertEqual(CashOut.objects.count(), 0)

    def test_batch_works_with_a_discrepancy_and_finalization_stays_blocked(self):
        night = counting("A", "B")
        count(night, "A", 1500)
        count(night, "B", 700)  # ₱200 more than was bought in
        run_batch(night)
        balance = queries.balance(night.session)
        self.assertEqual((balance.counted, balance.ok, balance.difference), (True, False, 20000))
        self.assertIn("₱200 too much", balance.explanation)

    def test_reversing_a_batch_cash_out_returns_the_player_to_awaiting_count(self):
        night = six_players()
        batch = run_batch(night)
        wrong = batch.cash_outs.get(participant=night.players["B"])
        services.reverse_cash_out(night.session.pk, night.host, wrong.pk, "counted the wrong stack")
        self.assertEqual(statuses(night)["B"], "awaiting")
        self.assertFalse(FinalCount.objects.get(pk=wrong.final_count_id).is_current)
        count(night, "B", 1450)
        self.assertEqual(run_batch(night).cash_outs.get().amount, 145000)

    def test_chips_game_batch_is_in_chips(self):
        night = Night("A", "B", unit="chips")
        night.buy("A", 1000)
        night.buy("B", 1000)
        night.go("reconciliation")
        count(night, "A", 1300)
        count(night, "B", 700)
        run_batch(night)
        self.assertEqual(sorted(CashOut.objects.values_list("amount", flat=True)), [700, 1300])
        self.assertNotIn("₱", AuditEvent.objects.get(action="cash_out.batch").summary)


class BatchPageTests(TestCase):
    def setUp(self):
        self.night = six_players()
        self.url = reverse("cash_out_counted", args=[self.night.session.pk])
        self.page_url = reverse("session", args=[self.night.session.pk])
        self.client.force_login(self.night.host.user)

    def confirm(self, ids=None, **extra):
        return self.client.post(self.url, {"count_id": ready_ids(self.night) if ids is None else ids, **extra}, follow=True)

    def test_button_shows_the_number_of_ready_players(self):
        page = self.client.get(self.page_url)
        self.assertContains(page, "Cash out counted players (4)")
        self.assertContains(page, self.url)
        self.assertContains(page, "Still to count: E, F.")
        self.assertContains(page, "2 awaiting count")
        self.assertNotContains(page, "notice-bad")  # players still to count are not an error

    def test_button_is_disabled_with_a_reason_when_nobody_is_ready(self):
        night = counting("A", "B")
        self.client.force_login(night.host.user)
        page = self.client.get(reverse("session", args=[night.session.pk]))
        self.assertContains(page, "Cash out counted players (0)")
        self.assertContains(page, "disabled aria-describedby")
        self.assertContains(page, "No player has a confirmed count yet.")
        self.assertNotContains(page, reverse("cash_out_counted", args=[night.session.pk]))

    def test_review_lists_players_counts_cash_outs_total_and_who_is_pending(self):
        page = self.client.get(self.url)
        for text in ("Confirmed count", "Cash-out", "₱2,500", "₱1,500", "₱0", "₱800", "Total of this batch", "₱4,800",
                     "Still to count", "Awaiting count", "Cash out 4 players", "It does not finalize the set"):
            self.assertContains(page, text)
        html = page.content.decode()
        self.assertEqual(html.count('name="count_id"'), 4)
        self.assertEqual(html.count("Awaiting count"), 2)  # E and F

    def test_confirm_reports_the_result_and_leaves_the_set_counting(self):
        page = self.confirm()
        self.assertRedirects(page, self.page_url)
        self.assertContains(page, "4 players cashed out; 2 awaiting final counts.")
        self.assertContains(page, "Counting up")
        self.assertContains(page, "Cash out counted players (0)")
        count(self.night, "E", 700)
        count(self.night, "F", 500)
        page = self.confirm()
        self.assertContains(page, "2 players cashed out; everyone is cashed out.")
        self.assertContains(page, "Every player is cashed out.")
        self.assertContains(page, "The books balance")

    def test_stale_review_explains_and_shows_a_fresh_one(self):
        reviewed = ready_ids(self.night)
        count(self.night, "B", 1400)
        page = self.confirm(reviewed)
        self.assertContains(page, "The review is out of date: B&#x27;s count was changed or cleared. Nothing was recorded.")
        self.assertContains(page, "₱1,400")  # the fresh review shows the new count
        self.assertContains(page, "Cash out 4 players")
        self.assertEqual(CashOut.objects.count(), 0)

    def test_resending_the_same_confirmation_records_once(self):
        ids, request_id = ready_ids(self.night), str(uuid.uuid4())
        self.confirm(ids, request_id=request_id)
        page = self.confirm(ids, request_id=request_id)
        self.assertContains(page, "4 players cashed out")
        self.assertEqual((CashOut.objects.count(), CashOutBatch.objects.count()), (4, 1))

    def test_player_and_stranger_are_refused(self):
        ben = add_player(self.night.group, "ben")
        self.client.force_login(ben.user)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.client.post(self.url, {"count_id": ready_ids(self.night)}).status_code, 403)
        page = self.client.get(self.page_url)
        self.assertNotContains(page, "Cash out counted players")
        self.assertContains(page, "4 ready to cash out")  # players still see the statuses
        self.client.force_login(make_user("stranger"))
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.post(self.url, {"count_id": ready_ids(self.night)}).status_code, 404)
        self.assertEqual(CashOut.objects.count(), 0)

    def test_review_is_closed_while_the_set_runs(self):
        games.transition(self.night.session.pk, self.night.host, "resume")
        page = self.client.get(self.url, follow=True)
        self.assertContains(page, "after play has ended")
