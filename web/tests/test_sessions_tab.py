import datetime
import uuid

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from games import services as games
from games.tests.helpers import CHIP_STAKES, make_session, make_table
from groups import services as groups
from groups.tests.helpers import add_player, make_group
from ledger import services as ledger
from settlement import services as settlement
from settlement.models import Transfer
from web.sessions_tab import sessions_context


class CardOrderTests(TestCase):
    """Current sessions lead with the tables in play where the viewer sits."""

    def setUp(self):
        self.group, self.host = make_group()
        self.ben = add_player(self.group, "Ben")
        self.table = make_table(self.host, name="Garage")
        day = datetime.date(2026, 10, 2)
        self.draft = make_session(self.host, table=self.table, state="setup", game_date=day)
        self.open_other = make_session(self.host, table=self.table, state="open", game_date=day)
        self.live_other = make_session(self.host, table=self.table, state="running", game_date=day)
        self.open_mine = self.seat(make_session(self.host, table=self.table, state="open", game_date=day))
        self.live_mine = self.seat(make_session(self.host, table=self.table, state="running", game_date=day))

    def seat(self, session):
        games.add_participant(session.pk, self.host, self.ben.pk)
        return session

    def order(self, me):
        return [card.latest_set.pk for card in sessions_context(me)["cards"]]

    def test_a_seated_player_gets_their_tables_first_and_no_draft(self):
        expected = [self.live_mine, self.live_other, self.open_mine, self.open_other]
        self.assertEqual(self.order(self.ben), [s.pk for s in expected])
        cards = sessions_context(self.ben)["cards"]
        self.assertEqual([card.mine for card in cards], [True, False, True, False])

    def test_a_card_lists_who_sits_in_join_order_and_times_only_play(self):
        later = add_player(self.group, "Ada")
        games.add_participant(self.live_mine.pk, self.host, later.pk)
        games.add_participant(self.live_mine.pk, self.host, self.host.pk)
        cards = {card.latest_set.pk: card for card in sessions_context(self.ben)["cards"]}
        live, waiting = cards[self.live_mine.pk], cards[self.open_mine.pk]
        self.assertEqual([p.member.display_name for p in live.seated], ["Ben", "Ada", self.host.display_name])
        self.assertEqual((live.at_table, waiting.at_table), (3, 1))
        self.assertIsInstance(live.seconds, int)
        self.assertIsNone(waiting.seconds)

    def test_today_is_named_by_the_manila_date(self):
        from django.utils import timezone

        today = make_session(self.host, table=self.table, state="open", game_date=timezone.localdate())
        cards = {card.latest_set.pk: card for card in sessions_context(self.host)["cards"]}
        self.assertTrue(cards[today.pk].is_today)
        self.assertFalse(cards[self.open_other.pk].is_today)

    def test_only_the_first_table_that_is_yours_carries_the_main_action(self):
        cards = sessions_context(self.ben)["cards"]
        self.assertEqual([(c.mine, c.primary) for c in cards], [(True, True), (False, False), (True, False), (False, False)])

    def test_a_host_who_does_not_sit_gets_the_draft_last_and_nothing_marked_theirs(self):
        # Nothing is the host's, so each band is oldest first.
        expected = [self.live_other, self.live_mine, self.open_other, self.open_mine, self.draft]
        self.assertEqual(self.order(self.host), [s.pk for s in expected])
        self.assertFalse(any(card.mine for card in sessions_context(self.host)["cards"]))


class Played:
    """A group with Ben (a login), Carlo and Dina, and closed sessions made to order."""

    def setUp(self):
        self.group, self.host = make_group()
        self.ben = add_player(self.group, "Ben")
        self.carlo = groups.add_roster_player(self.host, "Carlo")
        self.dina = groups.add_roster_player(self.host, "Dina")
        self.table = make_table(self.host, name="Garage")

    def played(self, day, nets, unit="php", close=True):
        """A closed session on ``day`` where each member in ``nets`` ends with that net, in whole pesos or chips."""
        scale, stakes = (1, {**CHIP_STAKES, "unit": "chips"}) if unit == "chips" else (100, {})
        s = make_session(self.host, table=self.table, state="open", game_date=day, **stakes)
        seats = games.add_participants(s.pk, self.host, [m.pk for m in nets], uuid.uuid4())
        bought = 1000 * scale
        for seat in seats:
            ledger.record_buy_in(s.pk, self.host, seat.pk, bought, uuid.uuid4())
        games.transition(s.pk, self.host, "start")
        games.transition(s.pk, self.host, "end")
        for seat, net in zip(seats, nets.values()):
            ledger.record_cash_out(s.pk, self.host, seat.pk, bought + net * scale, uuid.uuid4())
        settlement.finalize(s.pk, self.host)
        if close:
            settlement.close_night(s.night_id, self.host)
        return s.night


class CardLinkTests(Played, TestCase):
    """A card opens its set while the set is unfinished, and the session once the set is done."""

    def test_links_labels_and_chips_beyond_six(self):
        finished = self.played(datetime.date(2026, 10, 3), {self.ben: 100, self.carlo: -100}, close=False)
        live = make_session(self.host, table=self.table, state="running", game_date=datetime.date(2026, 10, 3))
        crowd = [self.ben, self.carlo, self.dina] + [groups.add_roster_player(self.host, n) for n in "EFGHI"]
        games.add_participants(live.pk, self.host, [m.pk for m in crowd], uuid.uuid4())
        cards = {card.pk: card for card in sessions_context(self.ben)["cards"]}
        mine = cards[live.night_id]
        self.assertEqual((mine.url, mine.action_label), (reverse("session", args=[live.pk]), "Open the table"))
        self.assertEqual((len(mine.chips), mine.more_seated), (6, 2))
        self.assertEqual(cards[finished.pk].url, reverse("night", args=[finished.pk]))
        self.assertEqual(cards[finished.pk].action_label, "Go to the session")


class PastRowsTests(Played, TestCase):
    """Each past session tells the viewer their own result and what they still pay or receive."""

    def rows(self, me):
        return {
            night.pk: night
            for year in sessions_context(me)["past_years"] for month in year.months for night in month.nights
        }

    def test_the_viewer_reads_their_net_or_that_they_did_not_play(self):
        won = self.played(datetime.date(2026, 10, 3), {self.ben: 500, self.carlo: -500})
        away = self.played(datetime.date(2026, 10, 10), {self.carlo: 200, self.dina: -200})
        rows = self.rows(self.ben)
        self.assertEqual(rows[won.pk].my_net, 50000)
        self.assertIsNone(rows[away.pk].my_net)

    def test_debts_name_the_other_player_in_both_directions(self):
        lost = self.played(datetime.date(2026, 10, 3), {self.ben: -300, self.carlo: 100, self.dina: 200})
        won = self.played(datetime.date(2026, 10, 10), {self.ben: 400, self.carlo: -400})
        rows = self.rows(self.ben)
        self.assertEqual(
            sorted((d.other.display_name, d.i_pay, d.amount) for d in rows[lost.pk].debts),
            [("Carlo", True, 10000), ("Dina", True, 20000)],
        )
        self.assertEqual([(d.other.display_name, d.i_pay, d.amount) for d in rows[won.pk].debts], [("Carlo", False, 40000)])
        # Nobody else's debt reaches the viewer.
        self.assertEqual(self.rows(self.host)[lost.pk].debts, [])

    def test_a_paid_transfer_is_no_longer_a_debt(self):
        won = self.played(datetime.date(2026, 10, 3), {self.ben: 400, self.carlo: -400})
        transfer = Transfer.objects.get(plan__night=won)
        settlement.mark_paid(won.pk, self.host, transfer.pk, uuid.uuid4())
        self.assertEqual(self.rows(self.ben)[won.pk].debts, [])

    def test_months_newest_first_this_year_open_and_earlier_years_closed(self):
        from django.utils import timezone

        year = timezone.localdate().year
        for day in (datetime.date(year, 1, 3), datetime.date(year, 1, 10), datetime.date(year, 2, 7), datetime.date(year - 1, 12, 5)):
            self.played(day, {self.ben: 100, self.carlo: -100})
        years = sessions_context(self.ben)["past_years"]
        self.assertEqual([(y.year, y.open, y.count) for y in years], [(year, True, 3), (year - 1, False, 1)])
        self.assertEqual(
            [(m.first_day, [n.game_date.day for n in m.nights]) for m in years[0].months],
            [(datetime.date(year, 2, 1), [7]), (datetime.date(year, 1, 1), [10, 3])],
        )

    def test_with_nothing_this_year_the_newest_year_is_open(self):
        from django.utils import timezone

        year = timezone.localdate().year
        self.played(datetime.date(year - 1, 6, 5), {self.ben: 100, self.carlo: -100})
        self.played(datetime.date(year - 2, 6, 5), {self.ben: 100, self.carlo: -100})
        self.assertEqual([(y.year, y.open) for y in sessions_context(self.ben)["past_years"]], [(year - 1, True), (year - 2, False)])


class SessionsPageTests(Played, TestCase):
    """The tab through the group page: what each role sees, and a fixed number of queries."""

    def setUp(self):
        super().setUp()
        self.url = reverse("group", args=[self.group.pk])

    def build(self, day):
        self.played(day, {self.ben: 300, self.carlo: -100, self.dina: -200})
        live = make_session(self.host, table=self.table, state="running", game_date=day)
        games.add_participants(live.pk, self.host, [self.ben.pk, self.carlo.pk], uuid.uuid4())
        make_session(self.host, table=self.table, state="open", game_date=day)
        make_session(self.host, table=self.table, state="setup", game_date=day)

    def queries(self):
        with CaptureQueriesContext(connection) as seen:
            self.assertEqual(self.client.get(self.url).status_code, 200)
        return len(seen)

    def test_the_query_count_does_not_grow_with_sessions(self):
        self.client.force_login(self.ben.user)
        self.build(datetime.date(2026, 9, 4))
        few = self.queries()
        for day in (11, 18, 25):
            self.build(datetime.date(2026, 9, day))
        self.build(datetime.date(2025, 9, 4))
        self.assertEqual(self.queries(), few)

    def test_a_player_never_sees_a_draft(self):
        make_session(self.host, table=make_table(self.host, name="Kitchen"), state="setup")
        self.client.force_login(self.ben.user)
        self.assertNotContains(self.client.get(self.url), "Kitchen")
        self.client.force_login(self.host.user)
        self.assertContains(self.client.get(self.url), "Kitchen")

    def test_a_chips_session_shows_chips_and_never_pesos(self):
        self.played(datetime.date(2026, 9, 4), {self.ben: 6, self.carlo: -6}, unit="chips")
        self.client.force_login(self.ben.user)
        page = self.client.get(self.url).content.decode()
        row = page.split('class="ledger-month"')[1]
        self.assertIn("+6 chips", row)
        self.assertIn("Carlo pays you <b>6 chips</b>", row)
        self.assertNotIn("₱", row)
