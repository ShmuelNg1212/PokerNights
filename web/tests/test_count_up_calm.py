"""The calm count-up: a labelled dock figure, the remaining sentence once, and the override in More host controls."""
import re
import uuid

from django.test import TestCase
from django.urls import reverse

from ledger import services
from ledger.tests.helpers import Night
from web.tests.test_books_off_panel import off_by_100


def section(html, start_marker, end_marker):
    start = html.index(start_marker)
    return html[start:html.index(end_marker, start)]


def books(html):
    return section(html, '<section class="balance-panel books', "</section>")


def host_more(html):
    return section(html, '<details class="host-more"', '<div class="end-balance"')


def counting(login=None):
    """Three players, one count confirmed, two still to count; a login player too when named."""
    night = Night("A", "B", "C")
    if login:
        night.add_login_player(login)
    for name in ["A", "B", "C"] + ([login] if login else []):
        night.buy(name, 1000)
    night.go("reconciliation")
    services.confirm_count(night.session.pk, night.host, night.players["A"].pk, 50000, uuid.uuid4())
    return night


class PageMixin:
    def page(self, night, user=None):
        self.client.force_login(user or night.host.user)
        return self.client.get(reverse("session", args=[night.session.pk])).content.decode()


class DockFigureLabelTests(PageMixin, TestCase):
    def test_the_folded_figure_says_what_it_adds_up(self):
        html = self.page(counting())
        bar = section(html, '<button type="button" class="dock-toggle', "</button>")
        self.assertRegex(bar, r'<span data-dock-prefix></span><span class="dock-label">Accounted for</span> <strong data-dock-accounted>₱500</strong> <span class="dock-of">of ₱3,000</span>')
        self.assertNotIn("bought in", bar)

    def test_the_label_matches_the_verdict_with_rake_too(self):
        night, _ = off_by_100(rake=True)
        bar = section(self.page(night), '<button type="button" class="dock-toggle', "</button>")
        self.assertIn('<span class="dock-label">Accounted for</span>', bar)  # "still to account for" under it; rake is in the open sum


class RemainingSentenceOnceTests(PageMixin, TestCase):
    def test_the_host_reads_what_remains_in_the_dock_only(self):
        html = self.page(counting())
        self.assertNotIn("still to account for", books(html))
        self.assertNotIn("data-books-status", html)
        # The folded bar and the dock's count total; the books keep the table and the names.
        self.assertEqual(html.count("₱2,500 still to account for."), 2)
        self.assertIn("Counted", books(html))
        self.assertIn("Still to count: B, C.", books(html))

    def test_a_players_books_keep_their_count_total(self):
        night = counting(login="Carlo")
        carlo = night.players["Carlo"].member
        self.assertIn("data-count-status", books(self.page(night, carlo.user)))


class OverrideInHostMoreTests(PageMixin, TestCase):
    def setUp(self):
        self.night, self.carlo = off_by_100()

    def test_the_override_waits_in_more_host_controls_unchanged(self):
        html = self.page(self.night)
        self.assertNotIn("Finalize with an override", books(html))
        menu = host_more(html)
        self.assertIn('<details data-key="override">', menu)
        self.assertIn('<summary class="btn btn-quiet btn-block">Finalize with an override</summary>', menu)
        form = re.search(r'<form method="post"[^>]*action="([^"]+)"[^>]*>(.*?)</form>', menu[menu.index('data-key="override"'):], re.S)
        self.assertEqual(form.group(1), reverse("override_add", args=[self.night.session.pk]))
        body = form.group(2)
        self.assertIn('name="request_id"', body)
        self.assertIn('<select id="absorber" name="absorber">', body)
        self.assertIn('<option value="equal">All players, in equal shares</option>', body)
        self.assertRegex(body, r'<input id="override-note" type="text" name="note" data-keep="override-note" maxlength="255" required>')
        self.assertIn("Record override", body)

    def test_the_words_point_to_more_host_controls(self):
        html = self.page(self.night)
        self.assertIn("Find the wrong record, or record an override in More host controls.", html)
        self.assertIn("or record an override in More host controls if the error cannot be found.", books(html))

    def test_a_player_never_gets_it(self):
        html = self.page(self.night, self.carlo.user)
        self.assertNotIn("Finalize with an override", html)
        self.client.force_login(self.carlo.user)
        response = self.client.post(reverse("override_add", args=[self.night.session.pk]), {"absorber": "equal", "note": "x"})
        self.assertEqual(response.status_code, 403)

    def test_not_offered_while_players_are_still_to_count(self):
        self.assertNotIn("Finalize with an override", self.page(counting()))

    def test_remove_stays_in_the_books(self):
        services.record_override(self.night.session.pk, self.night.host, "Recount", "equal", None, uuid.uuid4())
        html = self.page(self.night)
        self.assertIn("Remove the override", books(html))
        self.assertNotIn("Finalize with an override", html)


class CalmMismatchButtonTests(PageMixin, TestCase):
    def test_the_main_button_is_a_search_not_an_alarm(self):
        night, _ = off_by_100()
        html = self.page(night)
        self.assertIn('<a class="btn btn-primary btn-block next-action" href="#balance" data-turbo="false" data-next-server data-books-gap>Find the ₱100 difference</a>', html)
        self.assertNotIn("btn-danger btn-block next-action", html)


class MismatchOrderTests(PageMixin, TestCase):
    def test_the_host_searches_from_the_counts_and_a_player_reads_the_verdict_first(self):
        night, carlo = off_by_100()
        self.assertNotIn("books-known", self.page(night))
        self.assertIn("count-v2 books-known", self.page(night, carlo.user))
