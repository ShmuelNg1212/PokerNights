"""What next? A host chooses the next set or settle-up from the final set page, as equals."""
from django.test import TestCase
from django.urls import reverse

from games import services as games
from games.models import GameNight, GameSession
from groups.tests.helpers import add_player
from ledger.tests.test_counts import counting
from settlement import services as settlement


class NextStepTests(TestCase):
    def setUp(self):
        self.night = counting("A", "B")
        self.night.cash("A", 1200)
        self.night.cash("B", 800)
        settlement.finalize(self.night.session.pk, self.night.host)
        self.url = reverse("session", args=[self.night.session.pk])
        self.night_id = self.night.session.night_id
        self.client.force_login(self.night.host.user)

    def page(self):
        return self.client.get(self.url).content.decode()

    def test_a_host_sees_both_choices_and_no_old_words(self):
        html = self.page()
        choice = html[html.index('class="next-step'):html.index("</section>", html.index('class="next-step'))]
        self.assertIn("Play set 2", choice)
        self.assertIn("Same players, new buy-ins.", choice)
        self.assertIn('data-sheet-open="settle"', choice)
        self.assertIn('data-title="Close the session?"', choice)
        self.assertIn(reverse("next_set", args=[self.night_id]), choice)
        self.assertIn(reverse("night_close", args=[self.night_id]), choice)
        for gone in ("Next set or settle up", "Payment:", "Results are frozen"):
            self.assertNotIn(gone, html)

    def test_the_close_form_is_inside_the_confirmation(self):
        html = self.page()
        self.assertLess(html.index('data-sheet-source="settle"'), html.index(reverse("night_close", args=[self.night_id])))
        sheet = html[html.index('data-sheet-source="settle"'):html.index("</details>", html.index('data-sheet-source="settle"'))]
        self.assertIn("Adds up the results of 1 set.", sheet)
        self.assertIn("data-sheet-close data-sheet-focus>Not yet", sheet)

    def test_a_player_reads_one_line_and_no_choice(self):
        self.client.force_login(add_player(self.night.group, "ben").user)
        html = self.page()
        self.assertIn("Who pays whom comes when the host settles up.", html)
        self.assertNotIn("What next?", html)
        self.assertNotIn(reverse("night_close", args=[self.night_id]), html)

    def test_play_set_starts_it_from_the_final_page(self):
        page = self.client.post(reverse("next_set", args=[self.night_id]), follow=True)
        second = GameSession.objects.get(night_id=self.night_id, set_number=2)
        self.assertRedirects(page, reverse("session", args=[second.pk]))

    def test_settle_up_closes_from_the_final_page(self):
        self.client.post(reverse("night_close", args=[self.night_id]))
        self.assertEqual(GameNight.objects.get(pk=self.night_id).status, GameNight.Status.CLOSED)
        html = self.page()
        self.assertIn("See who pays whom", html)
        self.assertNotIn("What next?", html)

    def test_a_later_set_replaces_the_choice(self):
        second = games.start_next_set(self.night_id, self.night.host)
        html = self.page()
        self.assertNotIn("What next?", html)
        self.assertIn(f"Go to set {second.set_number}", html)

    def test_settle_up_waits_for_an_unfinished_set(self):
        second = games.start_next_set(self.night_id, self.night.host)
        games.transition(second.pk, self.night.host, "start")
        games.transition(second.pk, self.night.host, "end")  # set 2 is counting up
        html = self.page()
        self.assertIn("Play set 3", html)
        self.assertIn("Finish set 2 first.", html)
        self.assertNotIn(reverse("night_close", args=[self.night_id]), html)
