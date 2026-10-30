"""The seat draw: one dealer, an order around the table, and the seat the dealer takes."""

import uuid

from django.test import TestCase, override_settings

from audit.models import AuditEvent
from games import seats, services
from games.models import SeatDraw, SeatPlace
from groups.errors import NotAllowed, RuleError
from ledger.tests.helpers import Night


def table(count, state="open"):
    return Night(*[f"P{number}" for number in range(1, count + 1)], state=state)


class PositionTests(TestCase):
    def test_names_by_number_of_players(self):
        short = lambda count: [name for _, name in seats.positions(count)]
        self.assertEqual(short(2), ["D", "BB"])
        self.assertEqual(seats.positions(2)[0][0], "Dealer and small blind")
        self.assertEqual(short(3), ["D", "SB", "BB"])
        self.assertEqual(short(4), ["D", "SB", "BB", "UTG"])
        self.assertEqual(short(6), ["D", "SB", "BB", "UTG", "HJ", "CO"])
        self.assertEqual(short(9), ["D", "SB", "BB", "UTG", "MP1", "MP2", "MP3", "HJ", "CO"])
        self.assertEqual(len(seats.positions(12)), 12)
        self.assertEqual(short(12)[-2:], ["HJ", "CO"])

    def test_the_top_seat_is_first_and_seats_run_clockwise(self):
        x, y, turn = seats.spot(0, 4)
        self.assertEqual((x, turn), (50.0, 0.0))
        self.assertLess(y, 10)
        right, bottom, left = seats.spot(1, 4), seats.spot(2, 4), seats.spot(3, 4)
        self.assertGreater(right[0], 90)  # to the right of the top seat: clockwise on a screen
        self.assertEqual((right[1], right[2]), (50.0, 90.0))
        self.assertEqual((bottom[0], bottom[2]), (50.0, 180.0))
        self.assertGreater(bottom[1], 90)
        self.assertEqual((left[1], left[2]), (50.0, 270.0))

    def test_seats_are_equally_far_apart_along_the_edge_of_a_racetrack(self):
        import math

        for width, height in ((1.25, 1.0), (0.75, 1.0), (1.0, 1.0)):
            for count in range(2, 13):
                # Walk the edge finely and add up the distance between neighbouring seats.
                steps = 600
                points = [seats.edge(step, count * steps, width, height)[:2] for step in range(count * steps + 1)]
                lengths = []
                for seat in range(count):
                    run = points[seat * steps:(seat + 1) * steps + 1]
                    lengths.append(sum(math.dist(run[k], run[k + 1]) for k in range(steps)))
                self.assertAlmostEqual(max(lengths), min(lengths), delta=max(lengths) * 0.002, msg=(width, count))

    def test_every_seat_is_inside_the_box_and_faces_away_from_the_middle(self):
        import math

        for width, height in ((1.25, 1.0), (0.75, 1.0)):
            for count in (2, 6, 9, 12):
                for index in range(count):
                    x, y, turn = seats.edge(index, count, width, height)
                    self.assertLess(abs(x), width / 2)
                    self.assertLess(abs(y), height / 2)
                    outward = (math.sin(math.radians(turn)), -math.cos(math.radians(turn)))
                    self.assertGreater(x * outward[0] + y * outward[1], 0, (width, count, index))

    def test_a_wide_table_has_straight_sides_on_top_and_an_upright_one_at_the_sides(self):
        self.assertEqual([seats.edge(i, 12, 1.25, 1.0)[2] for i in (0, 6)], [0.0, 180.0])
        tall = [round(seats.edge(i, 12, 0.75, 1.0)[2]) for i in (3, 9)]
        self.assertEqual(tall, [90, 270])


class DrawTests(TestCase):
    def test_every_player_once_and_one_dealer(self):
        night = table(6)
        draw = services.draw_seats(night.session.pk, night.host, uuid.uuid4())
        places = list(draw.places.order_by("rank"))
        self.assertEqual({place.participant_id for place in places}, {p.pk for p in night.players.values()})
        self.assertEqual([place.rank for place in places], [index * SeatPlace.STEP for index in range(6)])
        seating = seats.seating(night.session)
        self.assertEqual(seating.state, "choosing")
        self.assertEqual(sum(seat.is_dealer for seat in seating.seats), 1)
        self.assertEqual([seat.position[1] for seat in seating.seats], ["D", "SB", "BB", "UTG", "HJ", "CO"])
        self.assertTrue(all(seat.index is None for seat in seating.seats))
        self.assertTrue(seating.poll_fast)

    def test_the_order_is_not_the_order_of_joining_every_time(self):
        night = table(6)
        orders = set()
        for _ in range(12):
            draw = services.draw_seats(night.session.pk, night.host, uuid.uuid4())
            orders.add(tuple(draw.places.order_by("rank").values_list("participant_id", flat=True)))
        self.assertGreater(len(orders), 1)

    def test_a_repeated_request_draws_nothing_twice(self):
        night = table(3)
        key = uuid.uuid4()
        first = services.draw_seats(night.session.pk, night.host, key)
        version = night.refresh().version
        self.assertEqual(services.draw_seats(night.session.pk, night.host, key).pk, first.pk)
        self.assertEqual(SeatDraw.objects.count(), 1)
        self.assertEqual(night.refresh().version, version)

    def test_only_a_host_draws(self):
        night = table(3)
        player = night.add_login_player("Ben")
        with self.assertRaises(NotAllowed):
            services.draw_seats(night.session.pk, player, uuid.uuid4())

    def test_refused_outside_an_open_set_and_with_one_player(self):
        with self.assertRaisesMessage(RuleError, "while the set is open"):
            night = table(3, state="running")
            services.draw_seats(night.session.pk, night.host, uuid.uuid4())
        with self.assertRaisesMessage(RuleError, "at least two players"):
            night = table(1)
            services.draw_seats(night.session.pk, night.host, uuid.uuid4())

    def test_drawing_again_keeps_the_earlier_draw(self):
        night = table(4)
        first = services.draw_seats(night.session.pk, night.host, uuid.uuid4())
        second = services.draw_seats(night.session.pk, night.host, uuid.uuid4())
        first.refresh_from_db()
        self.assertFalse(first.is_current)
        self.assertEqual(first.places.count(), 4)
        self.assertEqual((second.number, second.is_current), (2, True))
        self.assertEqual(seats.seating(night.session).draw.pk, second.pk)

    def test_the_draw_is_in_the_log_and_raises_the_version(self):
        night = table(3)
        before = night.refresh().version
        services.draw_seats(night.session.pk, night.host, uuid.uuid4())
        self.assertEqual(night.refresh().version, before + 1)
        event = AuditEvent.objects.filter(session_id=night.session.pk, action="seats.drawn").get()
        self.assertIn("has the dealer seat", event.summary)

    @override_settings(SEAT_DRAW=False)
    def test_the_switch_refuses(self):
        night = table(3)
        with self.assertRaisesMessage(RuleError, "switched off"):
            services.draw_seats(night.session.pk, night.host, uuid.uuid4())


class ChooseTests(TestCase):
    def setUp(self):
        self.night = table(5)
        self.ben = self.night.add_login_player("Ben")
        self.cara = self.night.add_login_player("Cara")
        self.draw = services.draw_seats(self.night.session.pk, self.night.host, uuid.uuid4())
        self.order = [place.participant for place in self.draw.places.select_related("participant__member").order_by("rank")]

    def test_a_host_chooses_and_everyone_follows_clockwise(self):
        services.choose_seat(self.night.session.pk, self.night.host, 4, uuid.uuid4())
        seating = seats.seating(self.night.session)
        self.assertEqual(seating.state, "seated")
        self.assertEqual([seat.index for seat in seating.seats], [4, 5, 6, 0, 1, 2, 3])
        self.assertEqual([seat.participant.pk for seat in seating.seats], [p.pk for p in self.order])
        self.assertEqual([seat.index for seat in seating.by_seat], list(range(7)))
        self.assertFalse(seating.poll_fast)

    def test_the_dealer_chooses_their_own_seat_and_nobody_else_does(self):
        dealer = self.order[0]
        logins = {self.night.players["Ben"].pk: self.ben, self.night.players["Cara"].pk: self.cara}
        if dealer.pk in logins:
            services.choose_seat(self.night.session.pk, logins[dealer.pk], 2, uuid.uuid4())
            self.assertEqual(seats.seating(self.night.session).seats[0].index, 2)
        else:
            someone = self.ben
            with self.assertRaisesMessage(RuleError, "has the dealer seat and chooses"):
                services.choose_seat(self.night.session.pk, someone, 2, uuid.uuid4())

    def test_a_player_who_is_not_the_dealer_is_refused(self):
        dealer = self.order[0]
        outsider = self.ben if self.night.players["Ben"].pk != dealer.pk else self.cara
        with self.assertRaisesMessage(RuleError, "has the dealer seat and chooses"):
            services.choose_seat(self.night.session.pk, outsider, 1, uuid.uuid4())

    def test_a_second_choice_is_refused_and_a_repeat_is_not_a_second_choice(self):
        key = uuid.uuid4()
        services.choose_seat(self.night.session.pk, self.night.host, 1, key)
        self.assertEqual(services.choose_seat(self.night.session.pk, self.night.host, 1, key).dealer_seat, 1)
        with self.assertRaisesMessage(RuleError, "already chosen"):
            services.choose_seat(self.night.session.pk, self.night.host, 3, uuid.uuid4())

    def test_a_seat_off_the_table_is_refused(self):
        for seat in (7, -1, "x", None):
            with self.assertRaisesMessage(RuleError, "Choose a seat on the table"):
                services.choose_seat(self.night.session.pk, self.night.host, seat, uuid.uuid4())

    def test_joining_and_taking_off_make_the_draw_out_of_date(self):
        self.night.add_login_player("Dita")
        seating = seats.seating(self.night.session)
        self.assertEqual(seating.state, "stale")
        with self.assertRaisesMessage(RuleError, "no seat draw"):
            services.choose_seat(self.night.session.pk, self.night.host, 0, uuid.uuid4())
        fresh = services.draw_seats(self.night.session.pk, self.night.host, uuid.uuid4())
        self.assertEqual(fresh.places.count(), 8)
        services.withdraw_participant(self.night.session.pk, self.night.host, self.night.players["P1"].pk)
        self.assertEqual(seats.seating(self.night.session).state, "stale")

    def test_start_seats_the_dealer_at_the_top_when_nobody_chose(self):
        self.night.go("running")
        seating = seats.seating(self.night.session)
        self.assertEqual(seating.state, "seated")
        self.assertEqual(seating.seats[0].index, 0)
        self.assertIsNone(seating.draw.chosen_by)

    def test_start_keeps_a_chosen_seat(self):
        services.choose_seat(self.night.session.pk, self.night.host, 3, uuid.uuid4())
        self.night.go("running")
        self.assertEqual(seats.seating(self.night.session).seats[0].index, 3)

    def test_a_late_player_is_seated_after_another_and_no_place_is_rewritten(self):
        services.choose_seat(self.night.session.pk, self.night.host, 0, uuid.uuid4())
        self.night.go("running")
        before = list(SeatPlace.objects.order_by("pk").values_list("pk", "rank"))
        late = self.night.add_login_player("Late")
        seating = seats.seating(self.night.session)
        self.assertEqual(seating.state, "seated")
        self.assertEqual([p.pk for p in seating.unseated], [self.night.players["Late"].pk])
        key = uuid.uuid4()
        services.seat_late_player(self.night.session.pk, self.night.host, self.night.players["Late"].pk, self.order[2].pk, key)
        services.seat_late_player(self.night.session.pk, self.night.host, self.night.players["Late"].pk, self.order[2].pk, key)
        seating = seats.seating(self.night.session)
        self.assertEqual([seat.participant.pk for seat in seating.seats][:4], [self.order[0].pk, self.order[1].pk, self.order[2].pk, self.night.players["Late"].pk])
        self.assertEqual([seat.index for seat in seating.seats], list(range(8)))
        self.assertIsNone(seating.seats[3].position)
        self.assertEqual(seating.seats[4].position[1], "UTG")
        self.assertEqual(seating.unseated, [])
        self.assertEqual(list(SeatPlace.objects.order_by("pk").values_list("pk", "rank"))[:len(before)], before)
        with self.assertRaisesMessage(RuleError, "already has a seat"):
            services.seat_late_player(self.night.session.pk, self.night.host, self.night.players["Late"].pk, self.order[0].pk, uuid.uuid4())
        self.assertIsNotNone(late)

    def test_a_late_player_after_the_last_seat(self):
        self.night.go("running")
        self.night.add_login_player("Late")
        services.seat_late_player(self.night.session.pk, self.night.host, self.night.players["Late"].pk, self.order[-1].pk, uuid.uuid4())
        self.assertEqual(seats.seating(self.night.session).seats[-1].participant.pk, self.night.players["Late"].pk)

    def test_a_player_who_left_keeps_their_seat_as_away(self):
        self.night.go("running")
        services.set_left(self.night.session.pk, self.night.host, self.order[1].pk)
        seating = seats.seating(self.night.session)
        self.assertEqual(seating.count, 7)
        self.assertTrue(seating.seats[1].away)

    def test_reading_the_seating_costs_one_query_with_the_players_in_hand(self):
        players = list(self.night.session.participants.select_related("member"))
        with self.assertNumQueries(1):
            seating = seats.seating(self.night.session, players)
            [seat.participant.member.display_name for seat in seating.seats]
