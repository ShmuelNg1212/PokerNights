"""The session page asks whether anything it shows has changed. The answer is derived, never stored."""

import uuid

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from games import services as games
from games.models import GameNight
from groups.tests.helpers import add_player, make_user
from ledger.tests.helpers import Night
from settlement import queries, services
from settlement.tests.test_night import TwoSets


def stamp(night_id):
    return queries.night_stamp(GameNight.objects.get(pk=night_id))


class NightStampTests(TestCase):
    def test_it_is_the_same_until_something_the_page_shows_changes(self):
        two = TwoSets(finalize_second=False)
        seen = [stamp(two.night_id)]
        self.assertEqual(stamp(two.night_id), seen[0])  # a second read

        self.client.force_login(two.host.user)

        def changed(what):
            now = stamp(two.night_id)
            self.assertNotIn(now, seen, what)
            seen.append(now)
            # The page works its mark out from its own rows; it must be this one, or it would redraw for ever.
            self.assertContains(self.client.get(reverse("night", args=[two.night_id])), f'data-stamp="{now}"', msg_prefix=what)

        # A buy-in in a set in play changes nothing this page shows.
        two.night.session = two.second
        before = stamp(two.night_id)
        from ledger import services as ledger
        ledger.record_buy_in(two.second.pk, two.host, two.players2["A"].pk, 100000, uuid.uuid4())
        self.assertEqual(stamp(two.night_id), before)
        ledger.reverse_buy_in(two.second.pk, two.host, ledger.BuyIn.objects.filter(session=two.second).get().pk, "test")

        two.finish_second()
        changed("a set ended and was finalized")
        plan = services.close_night(two.night_id, two.host)
        changed("the session closed")
        transfer = plan.transfers.first()
        services.mark_paid(two.night_id, two.host, transfer.pk, uuid.uuid4())
        changed("a transfer marked paid")
        services.mark_unpaid(two.night_id, two.host, transfer.pk)
        changed("the mark undone")
        services.mark_paid(two.night_id, two.host, transfer.pk, uuid.uuid4())
        changed("marked paid again")
        services.mark_unpaid(two.night_id, two.host, transfer.pk)
        services.reopen_night(two.night_id, two.host, "why")
        changed("the session reopened")
        services.reopen_set(two.first.pk, two.host, "why")
        changed("a set reopened")
        services.finalize(two.first.pk, two.host)
        changed("the set finalized again, as a new revision")
        third = games.start_next_set(two.night_id, two.host)
        changed("the next set started")
        games.transition(third.pk, two.host, "start", opening_buy_ins=False)
        changed("a set moved on")

    def test_archiving_changes_it(self):
        night = Night("A", "B")
        games.transition(night.session.pk, night.host, "cancel", "rain")
        before = stamp(night.session.night_id)
        games.archive_night(night.session.night_id, night.host)
        self.assertNotEqual(stamp(night.session.night_id), before)


class NightStateViewTests(TestCase):
    def setUp(self):
        self.two = TwoSets()
        self.plan = services.close_night(self.two.night_id, self.two.host)
        self.url = reverse("night_state", args=[self.two.night_id])
        self.player = add_player(self.two.night.group, "Player")
        self.client.force_login(self.player.user)

    def test_the_page_carries_its_stamp_and_where_to_ask(self):
        page = self.client.get(reverse("night", args=[self.two.night_id]))
        self.assertContains(page, f'data-state-url="{self.url}"')
        self.assertContains(page, f'data-stamp="{stamp(self.two.night_id)}"')

    def test_nothing_new_then_something_new(self):
        current = stamp(self.two.night_id)
        self.assertEqual(self.client.get(self.url, {"v": current}).status_code, 204)
        services.mark_paid(self.two.night_id, self.two.host, self.plan.transfers.first().pk, uuid.uuid4())
        answer = self.client.get(self.url, {"v": current})
        self.assertEqual(answer.status_code, 200)
        self.assertEqual(answer.json(), {"stamp": stamp(self.two.night_id)})
        self.assertNotEqual(answer.json()["stamp"], current)
        self.assertIn("no-store", answer["Cache-Control"])

    def test_only_for_members(self):
        self.client.force_login(make_user("stranger"))
        self.assertEqual(self.client.get(self.url, {"v": "x"}).status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.get(self.url, {"v": "x"}).status_code, 302)

    def test_asking_is_cheap(self):
        current = stamp(self.two.night_id)
        with CaptureQueriesContext(connection) as made:
            self.client.get(self.url, {"v": current})
        self.assertLessEqual(len(made), 8, [q["sql"][:90] for q in made])

    def test_an_archived_session_is_not_asked_about(self):
        games.archive_night(self.two.night_id, self.two.host)
        self.client.force_login(self.two.host.user)
        self.assertNotContains(self.client.get(reverse("night", args=[self.two.night_id])), "data-state-url")
