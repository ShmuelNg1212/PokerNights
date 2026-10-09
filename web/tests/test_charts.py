"""The running-profit chart is geometry worked out on the server. These check the numbers, not the look."""

import datetime
from types import SimpleNamespace

from django.test import SimpleTestCase

from settlement.stats import PlayerRecord, SessionResult
from web import charts


def record(*nets):
    days = [datetime.date(2026, 1, 1) + datetime.timedelta(days=7 * n) for n in range(len(nets))]
    rows = [SessionResult(1, n, day, "Main table", net, 100000, 0, 0, None) for n, (day, net) in enumerate(zip(days, nets))]
    return PlayerRecord(SimpleNamespace(pk=1, display_name="Ana"), rows)


class RunningChartTests(SimpleTestCase):
    def inside(self, chart):
        for p in chart.points:
            self.assertTrue(0 <= p.x <= 100 and 0 <= p.y <= 100, p)
            self.assertTrue(p.bar_height >= 0 and 0 <= p.bar_top <= 100 and p.bar_top + p.bar_height <= 100.01, p)
        self.assertTrue(0 <= chart.zero <= 100 and 0 <= chart.bar_zero <= 100)
        self.assertNotIn("nan", chart.path.lower())

    def test_mixed_results(self):
        chart = charts.running_chart(record(50000, -20000, 30000, -90000), "php")
        self.inside(chart)
        self.assertEqual([p.total for p in chart.points], [50000, 30000, 60000, -30000])
        self.assertEqual([p.x for p in chart.points], [12.5, 37.5, 62.5, 87.5])
        ys = [p.y for p in chart.points]
        self.assertLess(ys[2], ys[0])                 # a higher total is drawn higher
        self.assertLess(chart.zero, ys[3])            # a negative total is under the zero line
        self.assertEqual([p.up for p in chart.points], [True, False, True, False])
        self.assertEqual(chart.points[0].bar_top + chart.points[0].bar_height, chart.bar_zero)   # up bars stand on the baseline
        self.assertEqual(chart.points[1].bar_top, chart.bar_zero)                                 # down bars hang from it
        self.assertEqual([text for _, text in chart.labels], ["+₱600", "₱0", "−₱300"])
        self.assertEqual((chart.first_label, chart.last_label, chart.end_label), ("Jan 1", "Jan 22", "−₱300"))
        self.assertTrue(chart.path.startswith("M12.5 "))

    def test_all_up_all_down_and_flat(self):
        up, down, flat = (charts.running_chart(record(*nets), "php") for nets in ((100, 100, 100), (-100, -100, -100), (0, 0, 0)))
        for chart in (up, down, flat):
            self.inside(chart)
        self.assertEqual(up.bar_zero, 100)
        self.assertEqual(down.bar_zero, 0)
        self.assertEqual([text for _, text in up.labels], ["+₱3", "₱0"])
        self.assertEqual([text for _, text in down.labels], ["₱0", "−₱3"])
        self.assertEqual([p.bar_height for p in flat.points], [0, 0, 0])

    def test_a_long_record_shows_its_last_sixty_with_true_totals(self):
        chart = charts.running_chart(record(*[100] * 200), "chips")
        self.inside(chart)
        self.assertEqual((len(chart.points), chart.clipped), (60, True))
        self.assertEqual((chart.points[0].total, chart.points[-1].total), (14100, 20000))
        self.assertEqual(chart.end_label, "+20,000 chips")

    def test_no_chart_under_three_sessions(self):
        self.assertIsNone(charts.running_chart(record(100, 200), "php"))
