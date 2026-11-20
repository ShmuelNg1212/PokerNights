"""Finish set: one action records the reviewed cash-outs and freezes the results, both or neither."""

import re
import uuid
from types import SimpleNamespace

from django.test import TestCase
from django.urls import reverse

from audit.models import AuditEvent
from groups.errors import NotAllowed, RuleError
from groups.tests.helpers import add_player
from ledger import queries
from ledger import services as ledger
from ledger.models import CashOut, CashOutBatch, Finalization, PlayerResult
from ledger.tests.helpers import Night
from ledger.tests.test_batch import ready_ids
from ledger.tests.test_counts import count, counting
from ledger.tests.test_rake import configure
from settlement import queries as settlement_queries
from settlement import services
from web.templatetags.table_tags import group_token


def balanced(*names):
    """Everyone bought in ₱1,000 and is counted; the counts add up to what went in."""
    night = counting(*names or ("A", "B"))
    amounts = [1000] * len(night.players)
    amounts[0], amounts[-1] = 1200, 800
    for name, pesos in zip(night.players, amounts):
        count(night, name, pesos)
    return night


def covered_by_an_override():
    """₱100 short with an override on B; then A's cash-out is reversed and the same count is confirmed again."""
    night = counting("A", "B")
    first = night.cash("A", 1100)
    night.cash("B", 800)
    ledger.record_override(night.session.pk, night.host, "lost chip", "player", night.players["B"].pk, uuid.uuid4())
    ledger.reverse_cash_out(night.session.pk, night.host, first.pk, "recount")
    count(night, "A", 1100)
    return night


def finish(night, ids=None, request_id=None, actor=None, override=None):
    return services.finish_set(
        night.session.pk, actor or night.host, ready_ids(night) if ids is None else ids, request_id or uuid.uuid4(),
        override=override,
    )


def short(night):
    """A ₱50 short: every count is in and they do not add up."""
    count(night, "A", 1200)
    count(night, "B", 750)
    return night


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
        with self.assertRaisesMessage(RuleError, "already used"):
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
        with self.assertRaisesMessage(RuleError, "Still to count: B"):
            finish(night)
        self.nothing_recorded(night)

    def test_a_batch_recorded_without_finishing_is_not_taken_for_a_finish(self):
        night = balanced()
        reviewed, request_id = ready_ids(night), uuid.uuid4()
        ledger.cash_out_counted(night.session.pk, night.host, reviewed, request_id)
        with self.assertRaisesMessage(RuleError, "already used"):
            finish(night, reviewed, request_id)
        self.assertEqual((night.refresh().state, Finalization.objects.count()), ("reconciliation", 0))

    def test_an_override_in_place_lets_the_set_finish(self):
        night = covered_by_an_override()
        self.assertTrue(queries.finishes_the_set(queries.summary(night.session)))
        finalization = finish(night)
        self.assertEqual(night.refresh().state, "finalized")
        self.assertEqual({r.participant.member.display_name: r.net for r in finalization.results.all()}, {"A": 10000, "B": -10000})

    def test_counts_that_do_not_balance_finish_with_an_override_in_one_action(self):
        night = short(counting("A", "B"))
        finalization = finish(night, override={"note": "lost chip", "mode": "player", "participant_id": night.players["B"].pk})
        self.assertEqual(night.refresh().state, "finalized")
        self.assertEqual(CashOut.objects.filter(kind="final", batch__isnull=False).count(), 2)
        self.assertEqual(AuditEvent.objects.filter(action="balance.overridden").count(), 1)
        self.assertEqual({r.participant.member.display_name: r.net for r in finalization.results.all()}, {"A": 20000, "B": -20000})

    def test_an_equal_override_splits_the_gap(self):
        night = short(counting("A", "B"))
        finalization = finish(night, override={"note": "lost chip", "mode": "equal", "participant_id": ""})
        self.assertEqual({r.participant.member.display_name: r.net for r in finalization.results.all()}, {"A": 22500, "B": -22500})

    def test_an_override_without_a_note_records_nothing(self):
        night = short(counting("A", "B"))
        with self.assertRaisesMessage(RuleError, "Write a note"):
            finish(night, override={"note": " ", "mode": "player", "participant_id": night.players["B"].pk})
        self.nothing_recorded(night)

    def test_an_override_on_balanced_counts_records_nothing(self):
        night = balanced()
        with self.assertRaisesMessage(RuleError, "No override is needed"):
            finish(night, override={"note": "x", "mode": "player", "participant_id": night.players["B"].pk})
        self.nothing_recorded(night)

    def test_an_override_finish_replaces_an_older_override(self):
        night = covered_by_an_override()  # ₱100 short, covered on B; A recounted at 1,100
        count(night, "A", 1050)  # now ₱150 short
        finalization = finish(night, override={"note": "recount", "mode": "player", "participant_id": night.players["A"].pk})
        from ledger.models import BalanceAdjustment
        active = BalanceAdjustment.objects.filter(session=night.session, voided_at__isnull=True)
        self.assertEqual([(a.participant.member.display_name, a.amount, a.note) for a in active], [("A", 15000, "recount")])
        self.assertEqual({r.participant.member.display_name: r.net for r in finalization.results.all()}, {"A": 20000, "B": -20000})

    def test_a_retried_override_finish_records_nothing_more(self):
        night = short(counting("A", "B"))
        request_id = uuid.uuid4()
        wanted = {"note": "lost chip", "mode": "player", "participant_id": night.players["B"].pk}
        reviewed = ready_ids(night)
        first = finish(night, reviewed, request_id, override=wanted)
        self.assertEqual(finish(night, reviewed, request_id, override=wanted), first)
        self.assertEqual((CashOut.objects.count(), AuditEvent.objects.filter(action="balance.overridden").count()), (2, 1))

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

    def test_counts_that_are_off_do_not_finish_without_an_override(self):
        self.assertFalse(self.finishes(short(counting("A", "B"))))


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

    def test_a_review_with_nothing_left_after_a_refusal_leads_to_the_set(self):
        html = self.client.get(self.review).content.decode()
        self.night.cash("A", 1200)
        self.night.cash("B", 800)
        page = self.post(html)
        self.assertRedirects(page, reverse("session", args=[self.session.pk]))
        self.assertContains(page, "cashed out in the meantime")
        self.assertContains(page, "Finalize results")

    def test_a_used_review_says_so_after_a_reopen(self):
        html = self.client.get(self.review).content.decode()
        self.post(html)
        services.reopen_set(self.session.pk, self.night.host, "wrong count")
        page = self.post(html)
        self.assertContains(page, "That review was already used. Nothing changed.")
        self.assertNotContains(page, "Set 1 is final.")

    def test_an_overridden_review_discloses_the_override_and_finishes(self):
        night = covered_by_an_override()
        self.client.force_login(night.host.user)
        html = self.client.get(reverse("cash_out_counted", args=[night.session.pk])).content.decode()
        self.assertIn('data-tone="warn">An override covers the difference.', html)
        self.assertIn(">Finish set 1</button>", html)
        self.assertNotIn("Cash out", html)

    def test_a_review_that_cannot_finish_leads_to_the_set(self):
        count(self.night, "B", 750)
        page = self.client.get(self.review, follow=True)
        self.assertRedirects(page, reverse("session", args=[self.session.pk]))
        self.assertNotContains(page, ">Cash out")
        self.assertContains(page, "The set finishes when every count is in and the counts add up.")

    def test_a_post_to_the_review_is_refused_and_records_nothing(self):
        html = self.client.get(self.review).content.decode()
        response = self.client.post(self.review, {"count_id": re.findall(r'name="count_id" value="(\d+)"', html), "request_id": uuid.uuid4()})
        self.assertEqual(response.status_code, 405)
        self.assertEqual(CashOut.objects.count(), 0)

    def test_the_review_says_nothing_about_cashing_out(self):
        html = self.client.get(self.review).content.decode()
        html = html[html.index('<main'):html.index('</main>')]
        self.assertNotIn("Cash-out", html)
        self.assertNotIn("cash-out", html)
        self.assertNotIn("After this batch", html)
        self.assertIn("Total counted", html)

    def test_a_player_gets_no_way_to_finish(self):
        player = add_player(self.night.group, "ben")
        self.client.force_login(player.user)
        response = self.client.post(reverse("session_finish", args=[self.session.pk]), {"count_id": ready_ids(self.night)})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(CashOut.objects.count(), 0)

    def test_a_get_changes_nothing(self):
        response = self.client.get(reverse("session_finish", args=[self.session.pk]))
        self.assertEqual(response.status_code, 405)


class CountUpDockTests(TestCase):
    """Count-up asks for counts and a confirmation. Cash-outs are recorded by the finishing action."""

    def setUp(self):
        self.night = counting("A", "B")
        self.client.force_login(self.night.host.user)
        self.url = reverse("session", args=[self.night.session.pk])

    def page(self):
        return self.client.get(self.url).content.decode()

    def test_a_confirmed_count_reads_counted(self):
        count(self.night, "A", 1000)
        html = self.page()
        self.assertIn("1 <span>of 2</span></strong> players counted<", html)
        self.assertNotIn("Ready to cash out", html)
        self.assertNotIn("Cash out counted players", html)
        self.assertNotIn(reverse("cash_out_counted", args=[self.night.session.pk]), html)

    def test_counts_that_are_off_lead_to_the_difference_and_an_override_finish(self):
        short(self.night)
        html = self.page()
        self.assertIn("Find the ₱50 difference", html)
        self.assertNotIn("Cash out counted players", html)
        form = html[html.index('data-key="override"'):]
        form = form[:form.index("</form>")]
        self.assertIn(f'action="{reverse("session_finish", args=[self.night.session.pk])}"', form)
        self.assertEqual(len(re.findall(r'name="count_id" value="\d+"', form)), 2)
        self.assertIn("Finish with the override", form)
        books = html[html.index('id="balance"'):]
        self.assertIn('id="books-gap"', books)
        self.assertIn("The counts are ₱50 short. Correct a count, or finish with an override.", books)
        self.assertNotIn("Finish the set to record", books)

    def test_a_player_reads_that_the_counts_are_off(self):
        night = Night("A", "B")
        carlo = night.add_login_player("Carlo")  # at the table with no buy-in: a viewer of the books
        night.buy("A", 1000)
        night.buy("B", 1000)
        night.go("reconciliation")
        short(night)
        self.client.force_login(carlo.user)
        html = self.client.get(reverse("session", args=[night.session.pk])).content.decode()
        self.assertIn("The counts are ₱50 short. The host is checking them.", html)
        self.assertNotIn("Finish the set to record", html)

    def test_the_override_form_finishes_the_set(self):
        short(self.night)
        html = self.page()
        form = html[html.index('data-key="override"'):]
        form = form[:form.index("</form>")]
        page = self.client.post(reverse("session_finish", args=[self.night.session.pk]), {
            "count_id": re.findall(r'name="count_id" value="(\d+)"', form),
            "request_id": re.search(r'name="request_id" value="([^"]+)"', form).group(1),
            "absorber": str(self.night.players["B"].pk), "note": "lost chip",
        }, follow=True)
        self.assertContains(page, "Set 1 is final.")
        self.assertEqual(self.night.refresh().state, "finalized")

    def test_an_override_finish_without_a_note_stays_on_the_set(self):
        short(self.night)
        page = self.client.post(reverse("session_finish", args=[self.night.session.pk]), {
            "count_id": ready_ids(self.night), "request_id": uuid.uuid4(),
            "absorber": str(self.night.players["B"].pk), "note": "",
        }, follow=True)
        self.assertRedirects(page, self.url)
        self.assertContains(page, "Write a note")
        self.assertEqual(CashOut.objects.count(), 0)


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
        shown = re.findall(r'<span class="chip k(\d+)".*?<span class="grow">(\w+)<br>', rows)
        self.assertEqual([name for _, name in shown], ["B", "A", "C"])
        standings = settlement_queries.night_outcome(night).standings
        self.assertEqual(
            {name: int(colour) for colour, name in shown},
            {s.member.display_name: group_token(s.member)[1] for s in standings},
        )

    def test_a_tie_goes_by_name_and_the_set_log_keeps_join_order(self):
        outcome = settlement_queries.outcome(self.night.refresh())
        self.assertEqual([r.participant.member.display_name for r in outcome.results], ["A", "B", "C"])
        self.assertEqual([r.participant.member.display_name for r in outcome.ranked], ["B", "A", "C"])
        rows = [SimpleNamespace(net=0, member=SimpleNamespace(display_name=name, pk=pk)) for pk, name in ((1, "zoe"), (2, "Abe"))]
        self.assertEqual([r.member.display_name for r in settlement_queries.best_first(rows, lambda r: r.member)], ["Abe", "zoe"])

    def test_closing_a_session_sends_no_success_message(self):
        night = self.night.refresh().night
        page = self.client.post(reverse("night_close", args=[night.pk]), follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertEqual([str(message) for message in page.context["messages"]], [])
        # Nothing covers the money: the recap opens only from its card under the lead.
        self.assertContains(page, 'data-recap-card')
        self.assertNotContains(page, 'data-recap-lands')
