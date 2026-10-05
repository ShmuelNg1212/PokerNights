"""Count-up as the host works through it: players first, one total, and a main button that follows the state."""
import uuid

from django.test import TestCase
from django.urls import reverse

from groups.tests.helpers import add_player
from ledger import services
from ledger.tests.helpers import Night
from ledger.tests.test_counts import count, counting


class CountUpStructureTests(TestCase):
    def setUp(self):
        self.night = counting("A", "B")
        self.url = reverse("session", args=[self.night.session.pk])
        self.client.force_login(self.night.host.user)

    def page(self):
        return self.client.get(self.url).content.decode()

    def test_the_players_come_before_the_action_and_the_reference_figures(self):
        html = self.page()
        order = [html.index(mark) for mark in ('class="felt hero"', 'class="count-workspace"', 'class="host-controls', 'class="count-facts"', 'class="end-balance"')]
        self.assertEqual(order, sorted(order))
        self.assertNotIn("table-left", html)

    def test_headings_go_down_one_level_at_a_time(self):
        import re
        levels = [int(n) for n in re.findall(r"<h([1-6])[\s>]", self.page()[self.page().index('id="live"'):])]
        self.assertEqual(levels[0], 1)
        for before, after in zip(levels, levels[1:]):
            self.assertLessEqual(after, before + 1, levels)

    def test_a_row_has_a_field_and_no_button_of_its_own(self):
        count(self.night, "A", 800)
        html = self.page()
        row = html[html.index('class="count-row"'):html.index("</li>", html.index('class="count-row"'))]
        self.assertIn('data-count-input', row)
        self.assertIn('data-numpad="pesos"', row)
        self.assertIn('inputmode="decimal"', row)
        self.assertIn('placeholder="800"', row)  # the confirmed count shows in its field
        self.assertIn('data-saved="80000"', row)
        self.assertNotIn('type="submit" form="counts-form"', row)
        self.assertIn("1 buy-in", row)  # moved into Details
        self.assertLess(row.index("<details"), row.index("1 buy-in"))

    def test_rake_rows_show_only_when_rake_was_collected(self):
        self.assertNotIn("Collected rake", self.page())

    def test_one_action_per_state(self):
        html = self.page()
        self.assertIn("data-confirm-typed hidden", html)
        self.assertEqual(html.count("data-next-server"), 0)  # nothing counted yet: type first
        count(self.night, "A", 800)
        html = self.page()
        self.assertEqual(html.count("data-next-server"), 1)
        self.assertIn("Cash out counted players (1)", html)
        dock = html[html.index('class="host-controls'):html.index('class="host-more"')]
        self.assertEqual(dock.count("btn-primary"), 1 + 1)  # that link, and the hidden confirm button that replaces it
        self.assertNotIn("btn-primary", html[html.index('count-help"'):html.index('class="host-controls')])  # "Confirm all counts" is the fallback

    def test_books_off_leads_to_the_difference(self):
        self.night.cash("A", 900)
        self.night.cash("B", 1000)
        html = self.page()
        self.assertIn('href="#balance"', html)
        self.assertIn("See the ₱100 difference", html)
        self.assertIn('id="balance"', html)
        self.assertIn("books-known", html)
        self.assertIn('data-tone="warn">₱100 missing.', html)
        self.assertNotIn("Finalize results", html)
        self.assertNotIn("disabled", html[html.index('class="host-controls'):html.index('class="host-more"')])

    def test_an_override_reads_as_covered(self):
        self.night.cash("A", 900)
        self.night.cash("B", 1000)
        services.record_override(self.night.session.pk, self.night.host, "Synthetic recount", "player", self.night.players["A"].pk, uuid.uuid4())
        html = self.page()
        self.assertIn("Off by ₱100, covered by an override.", html)
        self.assertNotIn("₱100 missing.", html)
        self.assertIn("Finalize results", html)

    def test_a_player_keeps_a_read_only_total_and_no_host_instructions(self):
        member = add_player(self.night.group, "viewer")
        self.client.force_login(member.user)
        html = self.page()
        self.assertEqual(html.count("Confirmed counts"), 1)
        self.assertNotIn("data-count-input", html)
        self.assertNotIn("Confirm each player", html)
        self.assertIn("Not cashed out yet: A, B.", html)
        self.assertNotIn("Type what each player has left", html)


class ChipsCountTests(TestCase):
    def test_a_chips_count_field_takes_no_decimal_point(self):
        night = Night("A", unit="chips")
        night.buy("A", 1000)
        night.go("reconciliation")
        self.client.force_login(night.host.user)
        page = self.client.get(reverse("session", args=[night.session.pk]))
        self.assertContains(page, 'data-count-input data-numpad="chips"')


class ReviewVerdictTests(TestCase):
    """The review says, above its button, what the books will be once the batch is recorded."""

    def setUp(self):
        self.night = counting("A", "B")
        self.url = reverse("cash_out_counted", args=[self.night.session.pk])
        self.client.force_login(self.night.host.user)

    def verdict(self):
        html = self.client.get(self.url).content.decode()
        start = html.index('class="review-verdict')
        self.assertLess(start, html.index('class="btn btn-primary btn-block">Cash out'))  # above the action
        return html[start:html.index("</p>", start)]

    def test_a_batch_that_balances_says_so(self):
        count(self.night, "A", 1200)
        count(self.night, "B", 800)
        verdict = self.verdict()
        self.assertIn('data-tone="good">After this batch the books balance.', verdict)
        self.assertIn("notice-good", verdict)

    def test_a_batch_that_leaves_the_books_short_warns(self):
        count(self.night, "A", 1200)
        count(self.night, "B", 750)
        verdict = self.verdict()
        self.assertIn('data-tone="warn">After this batch the books are ₱50 short.', verdict)
        self.assertIn("Recount before recording, or record and fix it after.", verdict)

    def test_a_batch_that_puts_the_books_over_warns(self):
        count(self.night, "A", 1200)
        count(self.night, "B", 900)
        self.assertIn("After this batch the books are ₱100 over.", self.verdict())

    def test_players_still_to_count_are_named_as_the_reason(self):
        count(self.night, "A", 1200)
        verdict = self.verdict()
        self.assertIn('data-tone="">After this batch 1 player is still to count.', verdict)
        self.assertNotIn("notice", verdict)

    def test_the_grey_sentence_and_rake_rows_are_gone(self):
        count(self.night, "A", 1200)
        page = self.client.get(self.url)
        self.assertNotContains(page, "After this batch:")
        self.assertNotContains(page, "Collected rake")
        self.assertContains(page, '<th scope="col" class="num">Cash-out</th>')


class FinalizeAsksOnceTests(TestCase):
    def setUp(self):
        self.night = counting("A", "B")
        self.night.cash("A", 1200)
        self.night.cash("B", 800)
        self.url = reverse("session", args=[self.night.session.pk])
        self.client.force_login(self.night.host.user)

    def test_the_button_opens_a_confirmation_that_restates_the_books(self):
        html = self.client.get(self.url).content.decode()
        self.assertIn('data-sheet-open="finalize"', html)
        sheet = html[html.index('data-sheet-source="finalize"'):html.index('class="host-more"')]
        self.assertIn('data-title="Finalize set 1?"', sheet)
        for text in ("<dt>Players</dt><dd>2</dd>", "<dt>Total bought in</dt><dd>₱2,000</dd>", "<dt>Total cashed out</dt><dd>₱2,000</dd>",
                     'data-tone="good">The books balance.', "It cannot be undone here.", ">Finalize set 1</button>", "data-sheet-close data-sheet-focus"):
            self.assertIn(text, sheet)
        self.assertEqual(html.count(reverse("session_finalize", args=[self.night.session.pk])), 1)
        # The form that finalizes is inside the confirmation, never the first button.
        self.assertLess(html.index('data-sheet-source="finalize"'), html.index(reverse("session_finalize", args=[self.night.session.pk])))

    def test_finalizing_still_works_with_one_post(self):
        page = self.client.post(reverse("session_finalize", args=[self.night.session.pk]), follow=True)
        self.assertContains(page, "Results of set 1")


class FinalPageTests(TestCase):
    def finalized(self, a=1200, b=800):
        night = counting("A", "B")
        night.cash("A", a)
        night.cash("B", b)
        self.client.force_login(night.host.user)
        self.client.post(reverse("session_finalize", args=[night.session.pk]))
        return night, self.client.get(reverse("session", args=[night.session.pk])).content.decode()

    def test_the_proof_leads_the_overview(self):
        night, html = self.finalized()
        hero = html[html.index('aria-label="Final set overview"'):html.index("</section>", html.index('aria-label="Final set overview"'))]
        self.assertIn("2 players · ₱2,000 in · ₱2,000 out", hero)
        self.assertIn('data-tone="good">The books balance.', hero)
        self.assertLess(hero.index("The books balance."), hero.index("The set is finalized."))
        self.assertIn("<dt>Total cashed out</dt><dd>₱2,000</dd>", hero)
        self.assertNotIn("Available to play", hero)
        self.assertNotIn("Collected rake", hero)
        self.assertEqual(html.count("The books balance."), 1)

    def test_an_even_result_reads_even(self):
        night = counting("A", "B")
        night.cash("A", 1000)
        night.cash("B", 1000)
        self.client.force_login(night.host.user)
        self.client.post(reverse("session_finalize", args=[night.session.pk]))
        html = self.client.get(reverse("session", args=[night.session.pk])).content.decode()
        self.assertEqual(html.count("Even</span>"), 2)
        self.assertNotIn("₱0</span>", html)
