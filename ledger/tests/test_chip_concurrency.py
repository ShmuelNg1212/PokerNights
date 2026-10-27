"""PostgreSQL proves assignment edits and first chip counts cannot interleave."""
import uuid

from django.test import TransactionTestCase, skipUnlessDBFeature

from games import services as games
from games.models import GameNight
from ledger import services
from ledger.models import FinalCount
from ledger.tests.helpers import Night
from web.tests.test_concurrency import race


@skipUnlessDBFeature('has_select_for_update')
class ChipCountRaceTests(TransactionTestCase):
    def test_assignment_edit_races_with_first_count(self):
        night = Night('A')
        night.buy('A', 1000)
        night.go('reconciliation')
        games.set_chip_values(night.session.night_id, night.host,
                              [{'colour': 'red', 'value': 2500}], uuid.uuid4(), revision=0)
        outcomes = race(
            lambda: games.set_chip_values(night.session.night_id, night.host,
                                           [{'colour': 'red', 'value': 5000}], uuid.uuid4(), revision=1),
            lambda: services.confirm_count(night.session.pk, night.host, night.players['A'].pk, None,
                                             uuid.uuid4(), chips=[('red', '4')], chip_revision=1),
        )
        self.assertEqual(sorted(kind for kind, _ in outcomes), ['ok', 'refused'], outcomes)
        stored = GameNight.objects.get(pk=night.session.night_id)
        if outcomes[1][0] == 'ok':
            self.assertEqual(FinalCount.objects.get().amount, 10000)
            self.assertEqual(stored.chip_values[0]['value'], 2500)
            self.assertIsNotNone(stored.chip_values_locked_at)
        else:
            self.assertFalse(FinalCount.objects.exists())
            self.assertEqual(stored.chip_values_revision, 2)
            self.assertIsNone(stored.chip_values_locked_at)

    def test_two_first_counts_with_one_request_id_write_once(self):
        night = Night('A')
        night.buy('A', 1000)
        night.go('reconciliation')
        games.set_chip_values(night.session.night_id, night.host,
                              [{'colour': 'red', 'value': 2500}], uuid.uuid4(), revision=0)
        rid = uuid.uuid4()
        outcomes = race(*[
            lambda: services.confirm_count(night.session.pk, night.host, night.players['A'].pk, None,
                                             rid, chips=[('red', '4')], chip_revision=1)
        ] * 3)
        self.assertEqual([kind for kind, _ in outcomes], ['ok'] * 3, outcomes)
        self.assertEqual(FinalCount.objects.count(), 1)
