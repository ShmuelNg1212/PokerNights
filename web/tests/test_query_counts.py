"""How many database queries the busiest pages make. Each one is a network trip in production."""

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from games import services as games
from ledger.tests.helpers import Night
from settlement import services as settlement
from settlement.tests.test_archive import closed_example
from settlement.tests.test_finalize import worked_example


class QueryCountTests(TestCase):
    def queries(self, url):
        self.client.get(url)  # the first view of a page may take a kept form out of the login session
        with CaptureQueriesContext(connection) as made:
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return [query["sql"] for query in made]

    def test_a_closed_session_page(self):
        night = closed_example()
        self.client.force_login(night.host.user)
        self.assertLessEqual(len(self.queries(reverse("night", args=[night.session.night_id]))), 14)

    def test_a_session_page_costs_the_same_with_three_sets_as_with_one(self):
        night = worked_example()
        settlement.finalize(night.session.pk, night.host)
        self.client.force_login(night.host.user)
        url = reverse("night", args=[night.session.night_id])
        one = len(self.queries(url))
        for _ in range(2):
            later = games.start_next_set(night.session.night_id, night.host)
            games.transition(later.pk, night.host, "start", opening_buy_ins=False)
            games.transition(later.pk, night.host, "end")
        self.assertContains(self.client.get(url), "Set 3")
        self.assertEqual(len(self.queries(url)), one)

    def test_a_set_in_play(self):
        night = Night("A", "B", "C")
        night.buy("A", 1000)
        self.client.force_login(night.host.user)
        self.assertLessEqual(len(self.queries(reverse("session", args=[night.session.pk]))), 13)

    def test_a_changed_poll_costs_no_more_than_the_page(self):
        night = Night("A", "B", "C")
        night.buy("A", 1000)
        self.client.force_login(night.host.user)
        self.assertLessEqual(len(self.queries(reverse("session_state", args=[night.session.pk]) + "?v=0")), 13)

    def test_viewing_a_page_does_not_write_the_login_session(self):
        night = Night("A")
        self.client.force_login(night.host.user)
        for url in (reverse("home"), reverse("group", args=[night.group.pk]) + "?view=settings"):
            writes = [sql for sql in self.queries(url) if not sql.lstrip().upper().startswith(("SELECT", "BEGIN", "COMMIT", "SAVEPOINT", "RELEASE"))]
            self.assertEqual(writes, [], url)
