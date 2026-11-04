"""The seat draw on the set page: who is offered what, and what each address answers."""

import uuid

from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from games import seats, services as games
from games.tests.helpers import make_session
from groups.tests.helpers import add_player, make_group
from ledger.tests.helpers import Night


class SeatDrawPageTests(TestCase):
    def setUp(self):
        self.night = Night("Ana", "Bo", "Cy", state="open")
        self.ben = self.night.add_login_player("Ben")
        self.url = reverse("session", args=[self.night.session.pk])
        self.draw_url = reverse("seat_draw", args=[self.night.session.pk])
        self.seat_url = reverse("seat_choose", args=[self.night.session.pk])

    def draw(self):
        return games.draw_seats(self.night.session.pk, self.night.host, uuid.uuid4())

    def test_the_host_is_offered_the_draw_and_a_player_is_not(self):
        self.client.force_login(self.night.host.user)
        page = self.client.get(self.url)
        self.assertContains(page, 'data-step="seats" data-state="optional"')
        self.assertContains(page, "Draw seats")
        self.assertNotContains(page, "data-seats")
        self.client.force_login(self.ben.user)
        page = self.client.get(self.url)
        self.assertNotContains(page, self.draw_url)
        self.assertNotContains(page, "data-seats")

    def test_one_player_is_not_enough_to_offer_it(self):
        night = Night("Solo", state="open")
        self.client.force_login(night.host.user)
        self.assertNotContains(self.client.get(reverse("session", args=[night.session.pk])), "Draw seats")

    def test_the_host_draws_and_everyone_sees_who_chooses(self):
        self.client.force_login(self.night.host.user)
        self.assertRedirects(self.client.post(self.draw_url, {"request_id": str(uuid.uuid4())}), self.url)
        seating = seats.seating(self.night.session)
        dealer = seating.dealer.member.display_name
        page = self.client.get(self.url)
        self.assertContains(page, 'data-state="choosing"')
        self.assertContains(page, "data-poll-fast")
        self.assertContains(page, "data-can-choose")
        self.assertContains(page, f"<strong>{dealer}</strong> has the dealer seat")
        self.assertContains(page, 'name="seat"', count=4)
        self.assertContains(page, "Draw again")
        self.client.force_login(self.ben.user)
        page = self.client.get(self.url)
        self.assertContains(page, 'data-state="choosing"')
        if seating.dealer.member_id == self.ben.pk:
            self.assertContains(page, "Choose your seat.")
        else:
            self.assertNotContains(page, 'name="seat"')
            self.assertContains(page, "is choosing a seat")
        self.assertNotContains(page, "Draw again")

    def test_a_player_cannot_post_a_draw(self):
        self.client.force_login(self.ben.user)
        self.assertEqual(self.client.post(self.draw_url, {"request_id": str(uuid.uuid4())}).status_code, 403)
        self.assertIsNone(seats.seating(self.night.session))

    def test_a_seat_sent_from_the_stage_is_answered_as_data(self):
        self.draw()
        self.client.force_login(self.night.host.user)
        answer = self.client.post(self.seat_url, {"seat": "2", "request_id": str(uuid.uuid4())}, headers={"X-Requested-With": "fetch"})
        self.assertEqual(answer.status_code, 200)
        self.assertEqual(answer.json()["seat"], 2)
        again = self.client.post(self.seat_url, {"seat": "1", "request_id": str(uuid.uuid4())}, headers={"X-Requested-With": "fetch"})
        self.assertEqual(again.status_code, 409)
        self.assertIn("already chosen", again.json()["error"])
        page = self.client.get(self.url)
        self.assertContains(page, 'data-state="seated"')
        self.assertContains(page, 'data-dealer-seat="2"')
        self.assertContains(page, "seat-spot is-taken", count=4)
        self.assertContains(page, '<span class="seat-chair', count=4)
        self.assertContains(page, "--turn:0.0deg")
        self.assertContains(page, 'class="seat-rail"')
        self.assertContains(page, "branding/logo-mark.svg")
        self.assertContains(page, 'data-step="seats" data-state="done"')
        self.assertNotContains(page, "data-poll-fast")

    def test_a_seat_sent_by_a_form_returns_to_the_set(self):
        self.draw()
        self.client.force_login(self.night.host.user)
        self.assertRedirects(self.client.post(self.seat_url, {"seat": "0", "request_id": str(uuid.uuid4())}), self.url)
        self.assertEqual(seats.seating(self.night.session).state, "seated")

    def test_a_player_who_is_not_the_dealer_is_refused(self):
        self.draw()
        while seats.seating(self.night.session).dealer.member_id == self.ben.pk:
            self.draw()
        self.client.force_login(self.ben.user)
        answer = self.client.post(self.seat_url, {"seat": "1", "request_id": str(uuid.uuid4())}, headers={"X-Requested-With": "fetch"})
        self.assertEqual(answer.status_code, 409)
        self.assertEqual(seats.seating(self.night.session).state, "choosing")

    def test_a_changed_table_says_so(self):
        self.draw()
        self.night.add_login_player("Dee")
        self.client.force_login(self.night.host.user)
        page = self.client.get(self.url)
        self.assertContains(page, 'data-state="stale"')
        self.assertContains(page, "The table changed.")
        self.assertContains(page, "Draw seats again")
        self.assertNotContains(page, "seat-table")

    def test_in_play_the_table_stays_and_a_late_player_can_be_seated(self):
        self.draw()
        self.night.go("running")
        late = self.night.add_login_player("Late")
        self.client.force_login(self.night.host.user)
        page = self.client.get(self.url)
        self.assertContains(page, "dealt first")
        self.assertContains(page, "Seat Late after")
        after = seats.seating(self.night.session).seats[0].participant.pk
        self.client.post(reverse("seat_late", args=[self.night.session.pk]), {
            "participant_id": self.night.players["Late"].pk, "after": after, "request_id": str(uuid.uuid4()),
        })
        seating = seats.seating(self.night.session)
        self.assertEqual(seating.seats[1].participant.member_id, late.pk)
        self.assertNotContains(self.client.get(self.url), "Seat Late after")
        self.client.force_login(self.ben.user)
        self.assertNotContains(self.client.get(self.url), 'action="%s"' % reverse("seat_late", args=[self.night.session.pk]))

    def test_someone_outside_the_group_gets_404(self):
        self.draw()
        _, stranger = make_group("stranger", "Other club")
        self.client.force_login(stranger.user)
        for url in (self.draw_url, self.seat_url, reverse("seat_late", args=[self.night.session.pk])):
            self.assertEqual(self.client.post(url, {"seat": "0"}).status_code, 404, url)

    def test_the_poll_carries_the_draw(self):
        self.draw()
        self.client.force_login(self.ben.user)
        answer = self.client.get(reverse("session_state", args=[self.night.session.pk]) + "?v=0")
        self.assertIn('data-state="choosing"', answer.json()["html"])

    def test_a_set_with_a_draw_costs_one_query_more_and_one_without_costs_none(self):
        self.client.force_login(self.night.host.user)

        def cost():
            self.client.get(self.url)
            with CaptureQueriesContext(connection) as made:
                self.assertEqual(self.client.get(self.url).status_code, 200)
            return len(made)

        without = cost()
        self.draw()
        self.assertEqual(cost(), without + 1)

    @override_settings(SEAT_DRAW=False)
    def test_the_switch_hides_it(self):
        self.client.force_login(self.night.host.user)
        page = self.client.get(self.url)
        self.assertNotContains(page, "Draw seats")
        self.assertNotContains(page, 'data-step="seats"')
        self.client.post(self.draw_url, {"request_id": str(uuid.uuid4())})
        self.assertIsNone(seats.seating(self.night.session))


class DraftSeatDrawPageTests(TestCase):
    """A host draws from a draft. The draw opens the set first."""

    def setUp(self):
        self.group, self.host = make_group()
        self.ben = add_player(self.group, "ben")
        self.cara = add_player(self.group, "cara")
        self.session = make_session(self.host)
        self.url = reverse("session", args=[self.session.pk])
        self.draw_url = reverse("seat_draw", args=[self.session.pk])

    def seat(self, *members):
        for member in members:
            games.add_participant(self.session.pk, self.host, member.pk)

    def state(self):
        self.session.refresh_from_db()
        return self.session.state

    def test_a_draft_with_two_players_offers_the_draw_and_says_players_see_the_set(self):
        self.seat(self.ben, self.cara)
        self.client.force_login(self.host.user)
        page = self.client.get(self.url)
        self.assertContains(page, 'data-step="seats" data-state="optional"')
        self.assertContains(page, 'aria-label="Draw seats"')
        self.assertContains(page, "Players see the set when you draw.")

    def test_a_draft_with_one_player_does_not_offer_it(self):
        self.seat(self.ben)
        self.client.force_login(self.host.user)
        page = self.client.get(self.url)
        self.assertNotContains(page, 'aria-label="Draw seats"')
        self.assertNotContains(page, 'data-step="seats"')

    def test_the_open_set_keeps_its_own_line(self):
        self.seat(self.ben, self.cara)
        games.transition(self.session.pk, self.host, "open")
        self.client.force_login(self.host.user)
        page = self.client.get(self.url)
        self.assertContains(page, 'aria-label="Draw seats"')
        self.assertNotContains(page, "Players see the set when you draw.")

    def test_the_host_draws_from_the_draft_and_the_set_opens(self):
        self.seat(self.ben, self.cara)
        self.client.force_login(self.host.user)
        self.assertRedirects(self.client.post(self.draw_url, {"request_id": str(uuid.uuid4())}), self.url)
        self.assertEqual(self.state(), "open")
        page = self.client.get(self.url)
        self.assertContains(page, 'data-state="choosing"')
        self.client.force_login(self.ben.user)
        self.assertContains(self.client.get(self.url), 'data-state="choosing"')

    def test_a_player_gets_404_on_a_draft_and_it_stays_a_draft(self):
        self.seat(self.ben, self.cara)
        self.client.force_login(self.ben.user)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.post(self.draw_url, {"request_id": str(uuid.uuid4())}).status_code, 404)
        self.assertEqual(self.state(), "setup")
        self.assertIsNone(seats.seating(self.session))

    def test_a_draft_does_not_show_an_earlier_draw(self):
        # An open set held a draw, lost its players and went back to draft.
        self.seat(self.ben, self.cara)
        games.transition(self.session.pk, self.host, "open")
        games.draw_seats(self.session.pk, self.host, uuid.uuid4())
        for participant in self.session.participants.all():
            games.withdraw_participant(self.session.pk, self.host, participant.pk)
        games.transition(self.session.pk, self.host, "close")
        self.seat(add_player(self.group, "dee"), add_player(self.group, "eve"))
        self.client.force_login(self.host.user)
        page = self.client.get(self.url)
        self.assertNotContains(page, "data-seats")
        self.assertNotContains(page, "The table changed.")
        self.assertContains(page, 'aria-label="Draw seats"')

    def test_the_join_first_note_no_longer_promises_the_draw(self):
        self.client.force_login(self.host.user)
        page = self.client.get(self.url)
        self.assertContains(page, "Let players join first")
        self.assertNotContains(page, "You can draw seats then.")
