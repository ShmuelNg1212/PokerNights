"""A closed session's results read as a ledger: Player, In, Out, Net, with a footer that balances (parlor revamp)."""

import re
import uuid

from django.test import TestCase
from django.urls import reverse

from groups.tests.helpers import make_user
from groups.models import Member
from ledger import services as ledger_services
from ledger.tests.helpers import Night
from ledger.tests.test_rake import configure
from settlement import services as settle


def finish(n, **cash):
    n.go("reconciliation")
    for name, amount in cash.items():
        n.cash(name, amount)
    settle.finalize(n.session.pk, n.host)
    settle.close_night(n.session.night_id, n.host)


def ledger(html):
    start = html.index('<table class="ledger-table')
    return html[start:html.index("</table>", start)]


def cells(row_html):
    return [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row_html, re.S)]


class LedgerTableTests(TestCase):
    def page(self, n):
        self.client.force_login(n.host.user)
        return self.client.get(reverse("night", args=[n.session.night_id])).content.decode()

    def test_rows_and_footer_without_rake(self):
        n = Night("A", "B", "C")
        n.buy("A", 1000); n.buy("B", 1000); n.buy("B", 500); n.buy("C", 1000)
        finish(n, A=2100, B=400, C=1000)
        table = ledger(self.page(n))
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table, re.S)
        body = [cells(r) for r in rows[1:-1]]
        names = re.findall(r'class="ledger-name">([^<]+)<', table)
        self.assertEqual(names, ["A", "C", "B"])  # best first, as the results are
        self.assertEqual(body[0][1:], ["₱1,000", "₱2,100", "+₱1,100"])
        self.assertEqual(body[2][1:], ["₱1,500", "₱400", "−₱1,100"])
        self.assertIn("2 buy-ins", body[2][0])
        self.assertEqual(cells(rows[-1]), ["Total", "₱3,500", "₱3,500", "₱0"])
        self.assertNotIn("Rake", table)

    def test_recap_totals_match_the_session(self):
        n = Night("A", "B")
        n.buy("A", 1000); n.buy("B", 1000)
        finish(n, A=1300, B=700)
        self.client.force_login(n.host.user)
        recap = self.client.get(reverse("night", args=[n.session.night_id])).context["recap"]
        self.assertEqual((recap.total_buy_in, recap.total_cash_out, recap.total_net), (200000, 200000, 0))
        self.assertEqual(recap.total_cash_out, sum(line.cash_out for line in recap.ranking))

    def test_with_rake_the_footer_still_balances(self):
        n = Night("A", "B")
        configure(n, rake_mode="percent", rake_basis_points=1000)
        n.buy("A", 1000); n.buy("B", 1000)
        finish(n, A=1300, B=500)
        table = ledger(self.page(n))
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table, re.S)
        # Results are after rake: the nets sum to minus the rake, and the rake row says where it went.
        self.assertEqual(cells(rows[-2]), ["Rake already collected", "", "₱200", "+₱200"])
        self.assertEqual(cells(rows[-1]), ["Total", "₱2,000", "₱2,000", "₱0"])

    def test_a_chips_game_uses_chips(self):
        n = Night("A", "B", unit="chips")
        n.buy("A", 1000); n.buy("B", 1000)
        finish(n, A=1500, B=500)
        table = ledger(self.page(n))
        self.assertIn("+500 chips", table)
        self.assertNotIn("₱", table)

    def test_a_player_sees_the_same_table(self):
        n = Night("A", "B")
        user = make_user("viewer")
        Member.objects.filter(pk=n.players["A"].member_id).update(user=user)
        n.buy("A", 1000); n.buy("B", 1000)
        finish(n, A=1200, B=800)
        self.client.force_login(user)
        html = self.client.get(reverse("night", args=[n.session.night_id])).content.decode()
        self.assertIn("<caption", ledger(html))

    def test_an_open_session_keeps_its_results_list(self):
        n = Night("A", "B")
        n.buy("A", 1000); n.buy("B", 1000)
        n.go("reconciliation"); n.cash("A", 1200); n.cash("B", 800)
        settle.finalize(n.session.pk, n.host)
        self.assertNotIn('class="ledger-table', self.page(n))

    def test_long_figures_take_two_lines_on_a_phone(self):
        short = Night("A", "B")
        short.buy("A", 1000); short.buy("B", 1000)
        finish(short, A=1200, B=800)
        self.assertNotIn("ledger-stacked", ledger(self.page(short)))
        cents = Night("A", "B")
        for name in ("A", "B"):
            ledger_services.record_buy_in(cents.session.pk, cents.host, cents.players[name].pk, 100050, uuid.uuid4())
        cents.go("reconciliation")
        ledger_services.record_cash_out(cents.session.pk, cents.host, cents.players["A"].pk, 120050, uuid.uuid4())
        ledger_services.record_cash_out(cents.session.pk, cents.host, cents.players["B"].pk, 80050, uuid.uuid4())
        settle.finalize(cents.session.pk, cents.host)
        settle.close_night(cents.session.night_id, cents.host)
        table = ledger(self.page(cents))
        self.assertIn("ledger-stacked", table)  # "₱1,000.50" is longer than four columns allow on a phone
        self.assertIn('data-label="Net"', table)
        self.assertIn('role="rowheader"', table)  # the table keeps its meaning when its rows are restyled
