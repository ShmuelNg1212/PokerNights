"""Carried transfers on the pages: the list before closing, both sessions afterwards, and Your groups."""

from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from games.models import GameNight
from groups.tests.helpers import add_player
from settlement import queries, services
from settlement.models import CarriedTransfer
from settlement.tests.test_carried import Club


class CarriedPagesTests(TestCase):
    def setUp(self):
        self.club = Club("Ana", "Ben", "Carlo")
        self.first = self.club.closed({"Ana": -500, "Ben": 500})
        self.old = self.club.unpaid(self.first)[0]
        self.second = self.club.play({"Ana": 0, "Ben": -500, "Carlo": 500})
        self.client.force_login(self.club.host.user)

    def page(self, night_id):
        return self.client.get(reverse("night", args=[night_id]))

    def close(self, *carry):
        return self.client.post(reverse("night_close", args=[self.second]), {"carry": [t.pk for t in carry]}, follow=True)

    def test_the_host_is_shown_what_can_be_carried_ticked(self):
        page = self.page(self.second)
        self.assertContains(page, "Carry unpaid transfers from earlier sessions")
        self.assertContains(page, f'name="carry" value="{self.old.pk}" checked')
        self.assertContains(page, "<strong>Ana</strong> pays <strong>Ben</strong>")
        self.assertContains(page, "₱500")

    def test_nothing_to_carry_shows_the_close_as_before(self):
        services.mark_paid(self.first, self.club.host, self.old.pk, __import__("uuid").uuid4())
        page = self.page(self.second)
        self.assertNotContains(page, "data-carry-pick")
        self.assertContains(page, "Close session and settle up")

    def test_closing_with_the_tick_gives_one_list_and_says_what_it_includes(self):
        page = self.close(self.old)
        self.assertEqual(self.club.transfers(self.second), {("Ana", "Carlo"): 500})
        self.assertContains(page, "Includes <strong>1</strong> unpaid transfer from earlier session")
        self.assertContains(page, "<strong>Ana</strong> owed <strong>Ben</strong>")
        self.assertContains(page, reverse("night", args=[self.first]))
        self.assertContains(page, "and the earlier transfers carried in")

    def test_closing_without_the_tick_carries_nothing(self):
        page = self.close()
        self.assertEqual(self.club.transfers(self.second), {("Ben", "Carlo"): 500})
        self.assertEqual(CarriedTransfer.objects.count(), 0)
        self.assertNotContains(page, "night-carried")

    def test_the_earlier_session_says_carried_with_a_link_and_no_paid_button(self):
        self.close(self.old)
        page = self.page(self.first)
        self.assertContains(page, 'data-paid="c"')
        self.assertContains(page, '<span class="carried-word">Carried</span> to <a href="%s">' % reverse("night", args=[self.second]))
        self.assertNotContains(page, reverse("transfer_paid", args=[self.first, self.old.pk]))
        self.assertContains(page, "1 carried to a later session")
        self.assertContains(page, "Settled")
        self.assertContains(page, "Reopen that session first.")

    def test_a_person_sees_how_their_figure_is_made_up(self):
        club = Club("Ana", "Carlo")
        club.members["Ben"] = ben = add_player(club.group, "Ben")
        first = club.closed({"Ana": -500, "Ben": 500})
        second = club.play({"Ana": 0, "Ben": -200, "Carlo": 200})
        self.client.force_login(ben.user)
        home = self.client.get(reverse("home"))
        self.assertContains(home, "₱500")
        club.close(second, club.unpaid(first))
        page = self.client.get(reverse("night", args=[second]))
        self.assertContains(page, 'class="makeup"')
        self.assertContains(page, "Ana owed you")
        self.assertContains(page, "−₱200")
        self.assertContains(page, "+₱500")
        self.assertContains(page, "+₱300")
        self.assertEqual(club.transfers(second), {("Ana", "Ben"): 300, ("Ana", "Carlo"): 200})
        # Your groups: the earlier ₱500 is inside tonight's ₱300; it is not counted beside it.
        home = self.client.get(reverse("home"))
        self.assertContains(home, "₱300")
        self.assertNotContains(home, "₱500")
        self.assertNotContains(home, "₱800")
        earlier = self.client.get(reverse("night", args=[first]))
        self.assertContains(earlier, "Carried to")

    def test_a_changed_transfer_closes_nothing_and_says_so(self):
        import uuid

        services.mark_paid(self.first, self.club.host, self.old.pk, uuid.uuid4())
        page = self.close(self.old)
        self.assertContains(page, "Nothing was closed.")
        self.assertFalse(GameNight.objects.get(pk=self.second).is_closed)

    def test_the_group_page_counts_a_carried_transfer_as_settled_there(self):
        self.close(self.old)
        states = queries.settle_states([self.first, self.second])
        self.assertEqual((states[self.first].status, states[self.first].carried, states[self.first].still_to_pay), ("settled", 1, 0))
        self.assertEqual((states[self.second].status, states[self.second].still_to_pay), ("unsettled", 50000))
        page = self.client.get(reverse("group", args=[self.club.group.pk]))
        self.assertContains(page, "₱500 still to pay", count=1)

    def test_the_earlier_sessions_stamp_changes_when_carried_and_when_released(self):
        night = GameNight.objects.get(pk=self.first)
        before = queries.night_stamp(night)
        self.close(self.old)
        carried = queries.night_stamp(night)
        self.assertNotEqual(carried, before)
        self.assertContains(self.page(self.first), f'data-stamp="{carried}"')
        services.reopen_night(self.second, self.club.host, "undo")
        self.assertEqual(queries.night_stamp(night), before)

    def test_a_session_nobody_carried_from_costs_no_query_more(self):
        url = reverse("night", args=[self.first])

        def cost():
            self.client.get(url)
            with CaptureQueriesContext(connection) as made:
                self.assertEqual(self.client.get(url).status_code, 200)
            return len(made)

        plain = cost()
        self.close(self.old)
        self.assertEqual(cost(), plain + 1)

    def test_the_share_text_says_it(self):
        page = self.close(self.old)
        self.assertContains(page, "Includes unpaid transfers from earlier sessions.")

    @override_settings(CARRY_DEBTS=False)
    def test_the_switch_offers_nothing_and_carries_nothing(self):
        self.assertNotContains(self.page(self.second), "data-carry-pick")
        self.close(self.old)
        self.assertEqual(CarriedTransfer.objects.count(), 0)
        self.assertEqual(self.club.transfers(self.second), {("Ben", "Carlo"): 500})

    def test_a_player_is_not_shown_the_list_to_tick(self):
        member = add_player(self.club.group, "Dee")
        self.client.force_login(member.user)
        self.assertNotContains(self.page(self.second), "data-carry-pick")
