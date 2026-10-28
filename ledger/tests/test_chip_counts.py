"""Chip quantities use saved session denominations, with server arithmetic and evidence."""
import uuid

from django.test import TestCase, override_settings

from games import services as games
from groups.errors import RuleError
from ledger import services
from ledger.models import CountEntry, FinalCount
from ledger.tests.test_player_entries import night_with_logins


@override_settings(PLAYER_ENTRIES=True)
class ChipCountTests(TestCase):
    def setUp(self):
        self.night = night_with_logins('reconciliation')
        self.sid = self.night.session.pk
        self.pid = self.night.players['maria'].pk
        games.set_chip_values(self.night.session.night_id, self.night.host, [
            {'colour': 'white', 'value': 550}, {'colour': 'red', 'value': 2500, 'label': 'Twenty five'},
        ], uuid.uuid4(), revision=0)

    def enter(self, quantities=None, **kwargs):
        return services.enter_count(
            self.sid, self.night.maria, kwargs.pop('amount', None), kwargs.pop('request_id', uuid.uuid4()),
            chips=quantities if quantities is not None else [('white', '12'), ('red', '20')],
            chip_revision=kwargs.pop('chip_revision', 1), **kwargs,
        )

    def test_player_count_uses_server_total_and_keeps_breakdown_on_confirmation(self):
        entered = self.enter(amount=1)
        self.assertEqual(entered.amount, 56600)
        self.assertEqual(entered.chip_breakdown, [
            {'id': 'white', 'colour': 'white', 'label': '', 'value': 550, 'quantity': 12, 'subtotal': 6600},
            {'id': 'red', 'colour': 'red', 'label': 'Twenty five', 'value': 2500, 'quantity': 20, 'subtotal': 50000},
        ])
        confirmed, = services.confirm_counts(self.sid, self.night.host, {}, uuid.uuid4(), entries={self.pid: entered.pk})
        self.assertEqual(confirmed.chip_breakdown, entered.chip_breakdown)
        self.assertEqual(confirmed.amount, 56600)
        self.night.session.night.refresh_from_db()
        self.assertIsNotNone(self.night.session.night.chip_values_locked_at)

    def test_host_count_locks_values_and_manual_correction_has_no_old_breakdown(self):
        saved = services.confirm_count(self.sid, self.night.host, self.pid, None, uuid.uuid4(),
                                       chips=[('red', '4')], chip_revision=1)
        self.assertEqual(saved.amount, 10000)
        with self.assertRaisesRegex(RuleError, 'locked'):
            games.set_chip_values(self.night.session.night_id, self.night.host,
                                  [{'colour': 'red', 'value': 100}], uuid.uuid4(), revision=1)
        manual = services.confirm_count(self.sid, self.night.host, self.pid, 20000, uuid.uuid4())
        self.assertEqual(manual.chip_breakdown, [])
        saved.refresh_from_db()
        self.assertEqual(saved.chip_breakdown[1]['quantity'], 4)
        services.clear_count(self.sid, self.night.host, self.pid)
        self.night.session.night.refresh_from_db()
        self.assertIsNotNone(self.night.session.night.chip_values_locked_at)

    def test_retries_return_original_before_checking_revision_and_do_not_touch_twice(self):
        rid = uuid.uuid4()
        entered = self.enter(request_id=rid)
        before = self.night.refresh().version
        self.assertEqual(self.enter(request_id=rid, chip_revision=0).pk, entered.pk)
        self.assertEqual(self.night.refresh().version, before)
        count = services.confirm_count(self.sid, self.night.host, self.pid, None, rid,
                                       chips=[('red', '1')], chip_revision=1)
        again = services.confirm_count(self.sid, self.night.host, self.pid, None, rid,
                                       chips=[], chip_revision=0)
        self.assertEqual(again.pk, count.pk)

    def test_bad_quantities_or_stale_values_never_lock_or_write(self):
        for quantities in [[('red', '-1')], [('red', '1.5')], [('red', '1e3')], [('red', True)],
                           [('red', '1'), ('red', '2')], [('nope', '1')], [('red', '')], [],
                           [('red', '9999999999999999999999999999999999999999999')],
                           [('red', '40000001')]]:
            with self.subTest(quantities=quantities), self.assertRaises(RuleError):
                self.enter(quantities)
        with self.assertRaisesRegex(RuleError, 'changed'):
            self.enter(chip_revision=0)
        self.night.session.night.refresh_from_db()
        self.assertIsNone(self.night.session.night.chip_values_locked_at)
        self.assertFalse(CountEntry.objects.exists())
        self.assertFalse(FinalCount.objects.exists())

    def test_explicit_zero_and_empty_stack_are_real_counts(self):
        zero = self.enter([('red', '0')])
        self.assertEqual(zero.amount, 0)
        empty = self.enter([], empty_stack=True)
        self.assertEqual(empty.amount, 0)
        self.assertTrue(empty.chip_breakdown)
        with self.assertRaisesRegex(RuleError, 'empty stack'):
            self.enter([('red', '1')], empty_stack=True)

    def test_refused_player_count_does_not_lock_values(self):
        services.confirm_count(self.sid, self.night.host, self.pid, 10000, uuid.uuid4())
        with self.assertRaisesRegex(RuleError, 'confirmed'):
            self.enter()
        self.night.session.night.refresh_from_db()
        self.assertIsNone(self.night.session.night.chip_values_locked_at)

    def test_whole_chip_unit_uses_no_peso_scale(self):
        from ledger.tests.helpers import Night
        other = Night('A', unit='chips')
        other.buy('A', 1000)
        other.go('reconciliation')
        games.set_chip_values(other.session.night_id, other.host,
                              [{'colour': 'red', 'value': 25}], uuid.uuid4(), revision=0)
        entered = services.confirm_count(other.session.pk, other.host, other.players['A'].pk, None, uuid.uuid4(),
                                         chips=[('red', '7')], chip_revision=1)
        self.assertEqual(entered.amount, 175)


@override_settings(PLAYER_ENTRIES=True)
class BatchChipCountTests(TestCase):
    """"Confirm all counts" carries chip counts with the typed ones: all of them, or none."""

    def setUp(self):
        self.night = night_with_logins('reconciliation')
        self.sid = self.night.session.pk
        self.maria = self.night.players['maria'].pk
        self.ben = self.night.players['ben'].pk
        self.lolo = self.night.players['Lolo'].pk
        games.set_chip_values(self.night.session.night_id, self.night.host, [
            {'colour': 'white', 'value': 550}, {'colour': 'red', 'value': 2500, 'label': 'Twenty five'},
        ], uuid.uuid4(), revision=0)

    def chips(self, quantities, revision=1, empty_stack=False):
        return {'quantities': quantities, 'revision': revision, 'empty_stack': empty_stack}

    def batch(self, amounts=None, chips=None, request_id=None, **kwargs):
        return services.confirm_counts(self.sid, self.night.host, amounts or {}, request_id or uuid.uuid4(),
                                       chips=chips, **kwargs)

    def current(self, pid):
        return FinalCount.objects.filter(participant_id=pid, is_current=True).first()

    def test_typed_and_chip_counts_are_written_together_with_the_breakdown(self):
        before = self.night.refresh().version
        written = self.batch({self.lolo: 80000}, {self.maria: self.chips([('white', '12'), ('red', '20')])})
        self.assertEqual(len(written), 2)
        self.assertEqual(self.current(self.lolo).amount, 80000)
        self.assertEqual(self.current(self.lolo).chip_breakdown, [])
        maria = self.current(self.maria)
        self.assertEqual(maria.amount, 56600)
        self.assertEqual([row['quantity'] for row in maria.chip_breakdown], [12, 20])
        self.assertEqual(self.night.refresh().version, before + 1)
        self.night.session.night.refresh_from_db()
        self.assertIsNotNone(self.night.session.night.chip_values_locked_at)

    def test_a_refused_chip_count_saves_nothing_and_does_not_lock(self):
        for chips in [{self.maria: self.chips([('red', '-1')])}, {self.maria: self.chips([('red', '1')], revision=0)},
                      {self.maria: self.chips([])}]:
            with self.subTest(chips=chips), self.assertRaises(RuleError):
                self.batch({self.lolo: 80000}, chips)
        self.assertIsNone(self.current(self.lolo))
        self.assertIsNone(self.current(self.maria))
        self.night.session.night.refresh_from_db()
        self.assertIsNone(self.night.session.night.chip_values_locked_at)

    def test_a_typed_amount_that_differs_from_the_chip_total_is_refused_by_name(self):
        with self.assertRaisesRegex(RuleError, 'maria'):
            self.batch({self.maria: 1000}, {self.maria: self.chips([('red', '4')])})
        self.assertIsNone(self.current(self.maria))
        written, = self.batch({self.maria: 10000}, {self.maria: self.chips([('red', '4')])})
        self.assertEqual(written.amount, 10000)
        self.assertEqual(written.chip_breakdown[1]['quantity'], 4)

    def test_empty_stack_is_a_zero_count_with_no_chips(self):
        written, = self.batch(chips={self.ben: self.chips([], empty_stack=True)})
        self.assertEqual(written.amount, 0)

    def test_a_chip_recount_with_the_same_total_writes_the_next_version(self):
        self.batch(chips={self.maria: self.chips([('red', '4')])})
        written, = self.batch(chips={self.maria: self.chips([('white', '0'), ('red', '4')])})
        self.assertEqual(written.version, 2)
        self.assertEqual(self.batch({self.maria: 10000}), [])  # a typed amount equal to the count is still skipped

    def test_a_chip_count_replaces_the_players_entry_in_the_same_batch(self):
        entry = services.enter_count(self.sid, self.night.maria, 30000, uuid.uuid4())
        written, = self.batch(chips={self.maria: self.chips([('red', '4')])}, entries={self.maria: entry.pk})
        self.assertEqual(written.amount, 10000)
        self.assertIsNone(written.entry)

    def test_a_repeated_batch_returns_the_first_write(self):
        rid = uuid.uuid4()
        first = self.batch(chips={self.maria: self.chips([('red', '4')])}, request_id=rid)
        again = self.batch(chips={self.maria: self.chips([('red', '9')], revision=0)}, request_id=rid)
        self.assertEqual([c.pk for c in again], [c.pk for c in first])

    def test_chip_counts_alone_satisfy_the_need_for_one_count(self):
        with self.assertRaisesRegex(RuleError, 'at least one'):
            self.batch()
        self.assertEqual(len(self.batch(chips={self.maria: self.chips([('red', '1')])})), 1)


class ChipFaceTests(TestCase):
    def test_the_face_is_short_and_exact(self):
        from ledger.chip_views import face
        cases = [(500, "pesos", "5"), (2550, "pesos", "25.5"), (2505, "pesos", "25.05"), (100000, "pesos", "1K"),
                 (150000, "pesos", "1500"), (25, "chips", "25"), (5000, "chips", "5K")]
        for value, unit, text in cases:
            with self.subTest(value=value, unit=unit):
                self.assertEqual(face(value, unit), text)
