"""Finish set: one action records the reviewed cash-outs and freezes the results, both or neither."""

import re
import uuid

from django.test import TestCase
from django.urls import reverse

from audit.models import AuditEvent
from groups.errors import NotAllowed, RuleError
from groups.tests.helpers import add_player
from ledger import queries
from ledger.models import CashOut, CashOutBatch, Finalization, PlayerResult
from ledger.tests.helpers import Night
from ledger.tests.test_batch import ready_ids
from ledger.tests.test_counts import count, counting
from ledger.tests.test_rake import configure
from settlement import services


def balanced(*names):
    """Everyone bought in ₱1,000 and is counted; the counts add up to what went in."""
    night = counting(*names or ("A", "B"))
    amounts = [1000] * len(night.players)
    amounts[0], amounts[-1] = 1200, 800
    for name, pesos in zip(night.players, amounts):
        count(night, name, pesos)
    return night


def finish(night, ids=None, request_id=None, actor=None):
    return services.finish_set(
        night.session.pk, actor or night.host, ready_ids(night) if ids is None else ids, request_id or uuid.uuid4()
    )


class FinishSetTests(TestCase):
    def nothing_recorded(self, night):
        self.assertEqual(night.refresh().state, "reconciliation")
        self.assertEqual((CashOut.objects.count(), CashOutBatch.objects.count(), Finalization.objects.count()), (0, 0, 0))
        self.assertFalse(AuditEvent.objects.filter(action__in=("cash_out.recorded", "cash_out.batch", "session.finalized")).exists())

    def test_a_balanced_set_goes_to_final_in_one_action(self):
        night = balanced("A", "B", "C")
        before = night.refresh().version
        finalization = finish(night)
        self.assertEqual(night.refresh().state, "finalized")
        self.assertGreater(night.session.version, before)
        self.assertEqual(finalization.total_cash_out, 300000)
        self.assertEqual(
            {r.participant.member.display_name: r.net for r in finalization.results.all()},
            {"A": 20000, "B": 0, "C": -20000},
        )
        self.assertEqual(CashOut.objects.filter(kind="final", batch__isnull=False).count(), 3)
        self.assertEqual(AuditEvent.objects.filter(action="cash_out.recorded").count(), 3)
        self.assertEqual(AuditEvent.objects.filter(action="cash_out.batch").count(), 1)
        self.assertEqual(AuditEvent.objects.filter(action="session.finalized").count(), 1)

    def test_it_marks_no_payment_and_leaves_the_session_open(self):
        night = balanced()
        finish(night)
        self.assertEqual(night.refresh().night.status, "open")

    def test_a_retry_records_nothing_more(self):
        night = balanced()
        reviewed, request_id = ready_ids(night), uuid.uuid4()
        first = finish(night, reviewed, request_id)
        version = night.refresh().version
        second = finish(night, reviewed, request_id)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(night.refresh().version, version)
        self.assertEqual((CashOutBatch.objects.count(), CashOut.objects.count(), Finalization.objects.count()), (1, 2, 1))

    def test_a_retry_after_a_reopen_does_not_finish_the_set_again(self):
        night = balanced()
        reviewed, request_id = ready_ids(night), uuid.uuid4()
        finish(night, reviewed, request_id)
        services.reopen_set(night.session.pk, night.host, "wrong count")
        finish(night, reviewed, request_id)
        self.assertEqual(night.refresh().state, "reconciliation")
        self.assertEqual(Finalization.objects.filter(is_current=True).count(), 0)

    def test_a_count_changed_by_another_host_refuses_and_records_nothing(self):
        night = balanced()
        reviewed = ready_ids(night)
        count(night, "A", 1100)
        with self.assertRaisesMessage(RuleError, "A's count was changed or cleared"):
            finish(night, reviewed)
        self.nothing_recorded(night)

    def test_books_that_do_not_balance_refuse_and_record_nothing(self):
        night = counting("A", "B")
        count(night, "A", 1200)
        count(night, "B", 750)
        with self.assertRaisesMessage(RuleError, "Nothing was recorded"):
            finish(night)
        self.nothing_recorded(night)

    def test_a_player_still_to_count_refuses_and_records_nothing(self):
        night = counting("A", "B")
        count(night, "A", 1000)
        with self.assertRaisesMessage(RuleError, "Not cashed out yet: B"):
            finish(night)
        self.nothing_recorded(night)

    def test_a_set_another_host_finished_refuses_and_keeps_one_result(self):
        night = balanced()
        reviewed = ready_ids(night)
        finish(night, reviewed)
        with self.assertRaisesMessage(RuleError, "already final"):
            finish(night, reviewed)
        self.assertEqual((CashOutBatch.objects.count(), Finalization.objects.count()), (1, 1))

    def test_a_player_is_refused_and_nothing_is_recorded(self):
        night = balanced()
        player = add_player(night.group, "ben")
        with self.assertRaises(NotAllowed):
            finish(night, actor=player)
        self.nothing_recorded(night)

    def test_a_partial_cash_out_counts_towards_the_result(self):
        night = Night("A", "B")
        night.buy("A", 1000)
        night.buy("B", 1000)
        self.assertEqual(night.cash("A", 300).kind, "partial")
        night.go("reconciliation")
        count(night, "A", 900)
        count(night, "B", 800)
        finalization = finish(night)
        self.assertEqual(
            {r.participant.member.display_name: (r.cashed_out, r.net) for r in finalization.results.all()},
            {"A": (120000, 20000), "B": (80000, -20000)},
        )

    def test_rake_is_part_of_the_balance(self):
        night = Night("A", "B")
        configure(night, rake_mode="percent", rake_basis_points=500)
        night.buy("A", 1000)
        night.buy("B", 1000)
        night.go("reconciliation")
        count(night, "A", 1100)
        count(night, "B", 800)  # ₱1,900 counted and ₱100 of rake make the ₱2,000 bought in
        finalization = finish(night)
        self.assertEqual((finalization.total_rake, finalization.total_cash_out), (10000, 190000))
        self.assertEqual(sum(r.net for r in PlayerResult.objects.all()), -10000)

    def test_a_chips_game_finishes_in_chips(self):
        night = Night("A", "B", unit="chips")
        night.buy("A", 1000)
        night.buy("B", 1000)
        night.go("reconciliation")
        count(night, "A", 1500)
        count(night, "B", 500)
        finalization = finish(night)
        self.assertEqual((finalization.unit, finalization.total_cash_out), ("chips", 2000))


class FinishesTheSetTests(TestCase):
    def finishes(self, night):
        return queries.finishes_the_set(queries.summary(night.session))

    def test_only_when_the_counts_balance_and_nobody_is_left(self):
        night = counting("A", "B")
        self.assertFalse(self.finishes(night))
        count(night, "A", 1200)
        self.assertFalse(self.finishes(night))  # B is still to count
        count(night, "B", 750)
        self.assertFalse(self.finishes(night))  # ₱50 short
        count(night, "B", 800)
        self.assertTrue(self.finishes(night))

    def test_not_when_every_player_is_already_cashed_out(self):
        night = counting("A", "B")
        night.cash("A", 1000)
        night.cash("B", 1000)
        self.assertFalse(self.finishes(night))  # nothing to review: Finalize results is the way


class FinishPageTests(TestCase):
    def setUp(self):
        self.night = balanced()
        self.session = self.night.session
        self.review = reverse("cash_out_counted", args=[self.session.pk])
        self.client.force_login(self.night.host.user)

    def post(self, html, follow=True):
        return self.client.post(reverse("session_finish", args=[self.session.pk]), {
            "count_id": re.findall(r'name="count_id" value="(\d+)"', html),
            "request_id": re.search(r'name="request_id" value="([^"]+)"', html).group(1),
        }, follow=follow)

    def test_a_balanced_review_offers_one_button_that_finishes(self):
        html = self.client.get(self.review).content.decode()
        self.assertIn(f'action="{reverse("session_finish", args=[self.session.pk])}"', html)
        self.assertIn(">Finish set 1</button>", html)
        self.assertIn('data-tone="good">The books balance.', html)
        self.assertNotIn(">Cash out 2 players</button>", html)
        self.assertEqual(html.count('class="btn btn-primary btn-block">'), 1)  # the install sheet's button has more attributes

    def test_the_set_page_leads_to_the_review_by_name(self):
        page = self.client.get(reverse("session", args=[self.session.pk]))
        self.assertContains(page, ">Review and finish</a>")
        self.assertNotContains(page, "Cash out counted players")

    def test_finishing_lands_on_the_final_set(self):
        page = self.post(self.client.get(self.review).content.decode())
        self.assertRedirects(page, reverse("session", args=[self.session.pk]))
        self.assertContains(page, "Set 1 is final.")
        self.assertContains(page, 'class="final-results"')

    def test_a_refusal_returns_to_a_fresh_review(self):
        html = self.client.get(self.review).content.decode()
        count(self.night, "A", 1100)
        count(self.night, "B", 900)
        page = self.post(html)
        self.assertRedirects(page, self.review)
        self.assertContains(page, "Nothing was recorded")
        self.assertContains(page, "₱1,100")
        self.assertEqual(CashOut.objects.count(), 0)

    def test_a_set_finished_meanwhile_leads_to_the_final_set(self):
        html = self.client.get(self.review).content.decode()
        finish(self.night)
        page = self.post(html)
        self.assertRedirects(page, reverse("session", args=[self.session.pk]))
        self.assertContains(page, "already final")
        self.assertNotContains(page, "Counted players are cashed out")

    def test_a_balance_that_needs_more_keeps_the_batch_button(self):
        count(self.night, "B", 750)
        html = self.client.get(self.review).content.decode()
        self.assertIn(">Cash out 2 players</button>", html)
        self.assertNotIn("Finish set", html)
        self.assertNotIn(reverse("session_finish", args=[self.session.pk]), html)

    def test_a_player_gets_no_way_to_finish(self):
        player = add_player(self.night.group, "ben")
        self.client.force_login(player.user)
        response = self.client.post(reverse("session_finish", args=[self.session.pk]), {"count_id": ready_ids(self.night)})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(CashOut.objects.count(), 0)

    def test_a_get_changes_nothing(self):
        response = self.client.get(reverse("session_finish", args=[self.session.pk]))
        self.assertEqual(response.status_code, 405)


class ResultsAtAGlanceTests(TestCase):
    def setUp(self):
        self.night = counting("A", "B", "C")
        count(self.night, "A", 800)
        count(self.night, "B", 1500)
        count(self.night, "C", 700)
        finish(self.night)
        self.client.force_login(self.night.host.user)
        self.url = reverse("session", args=[self.night.session.pk])

    def test_set_results_run_best_to_worst(self):
        html = self.client.get(self.url).content.decode()
        rows = html[html.index('class="final-results"'):]
        self.assertEqual(re.findall(r'class="player-name grow">(\w+)', rows), ["B", "A", "C"])

    def test_the_row_is_the_disclosure_and_holds_the_facts(self):
        html = self.client.get(self.url).content.decode()
        row = html[html.index('class="result-details"'):]
        row = row[:row.index("</details>")]
        self.assertLess(row.index("<summary"), row.index("</summary>"))
        summary = row[row.index("<summary"):row.index("</summary>")]
        self.assertIn("result-amount", summary)
        self.assertNotIn("₱1,000 in", summary)
        self.assertIn("₱1,000 in", row[row.index("</summary>"):])
        self.assertIn("Final cash-out", row)

    def test_session_results_run_best_to_worst_and_tokens_keep_their_colours(self):
        night = self.night.refresh().night
        url = reverse("night", args=[night.pk])
        html = self.client.get(url).content.decode()
        rows = html[html.index('class="list night-results"'):]
        rows = rows[:rows.index("</ul>")]
        names = [name for name in re.findall(r'<span class="grow">(\w+)<br>', rows)]
        self.assertEqual(names, ["B", "A", "C"])
