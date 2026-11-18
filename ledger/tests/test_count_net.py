"""The net beside a count row comes from accepted figures only, and equals the result it becomes (parlor revamp)."""

import uuid

from django.test import TestCase

from ledger import queries, services
from ledger.models import PlayerResult
from settlement import services as settlement

from .helpers import Night
from .test_rake import configure


def count(night, name, pesos):
    return services.confirm_count(night.session.pk, night.host, night.players[name].pk, pesos * night.scale, uuid.uuid4())


class CountNetTests(TestCase):
    def test_no_net_until_a_count_is_confirmed(self):
        n = Night("A", "B")
        n.buy("A", 1000)
        n.buy("B", 1000)
        n.go("reconciliation")
        self.assertIsNone(n.line("A").count_net)
        count(n, "A", 1500)
        self.assertEqual(n.line("A").count_net, 50000)
        self.assertIsNone(n.line("B").count_net)

    def test_a_player_without_a_buy_in_has_no_net(self):
        n = Night("A", "B")
        n.buy("A", 1000)
        n.go("reconciliation")
        self.assertIsNone(n.line("B").count_net)

    def test_rebuys_and_an_earlier_cash_out_are_in_the_net(self):
        n = Night("A")
        n.buy("A", 1000)
        n.buy("A", 500)
        n.go("reconciliation")
        count(n, "A", 400)
        self.assertEqual(n.line("A").count_net, -110000)

    def test_a_cashed_out_player_shows_the_cash_out_net(self):
        n = Night("A", "B")
        n.buy("A", 1000)
        n.go("reconciliation")
        n.cash("A", 0)
        self.assertEqual(n.line("A").count_net, -100000)

    def test_rake_is_a_loss_as_in_the_results(self):
        n = Night("A", "B")
        configure(n, rake_mode="percent", rake_basis_points=1000)
        n.buy("A", 1000)
        n.buy("B", 1000)
        n.go("reconciliation")
        # Each paid 100 rake; 1,800 is left on the table.
        count(n, "A", 1100)
        count(n, "B", 700)
        self.assertEqual((n.line("A").count_net, n.line("B").count_net), (10000, -30000))

    def test_chips_are_whole_chips(self):
        n = Night("A", "B", unit="chips")
        n.buy("A", 1000)
        n.go("reconciliation")
        count(n, "A", 1200)
        self.assertEqual(n.line("A").count_net, 200)

    def test_the_net_equals_the_final_result(self):
        n = Night("A", "B")
        n.buy("A", 1000)
        n.buy("B", 1000)
        n.buy("B", 500)
        n.go("reconciliation")
        count(n, "A", 1800)
        count(n, "B", 700)
        shown = {name: n.line(name).count_net for name in ("A", "B")}
        summary = queries.summary(n.session)
        counts = [line.count.pk for line in summary.ready_lines]
        services.cash_out_counted(n.session.pk, n.host, counts, uuid.uuid4())
        settlement.finalize(n.session.pk, n.host)
        results = {r.participant.member.display_name: r.net for r in PlayerResult.objects.filter(finalization__session=n.session)}
        self.assertEqual(results, shown)
