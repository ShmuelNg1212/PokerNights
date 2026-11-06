import uuid

from django.db import IntegrityError, transaction
from django.test import TestCase

from settlement.models import Clearance, ClearedTransfer
from settlement.tests.test_carried import Club


class ClearanceConstraintsTests(TestCase):
    def setUp(self):
        self.club = Club('Ana', 'Ben')
        self.night = self.club.closed({'Ana': -500, 'Ben': 500})
        self.transfer = self.club.unpaid(self.night)[0]

    def clearance(self, **changes):
        values = dict(group=self.club.group, unit='php', payer=self.club.members['Ana'],
                      payee=self.club.members['Ben'], amount=50000, request_id=uuid.uuid4(),
                      recorded_by=self.club.host.user)
        return Clearance.objects.create(**(values | changes))

    def test_database_refuses_negative_amount_same_party_and_repeated_request(self):
        first = self.clearance()
        for values in ({'amount': -1}, {'payee': self.club.members['Ana']}, {'request_id': first.request_id}):
            with self.assertRaises(IntegrityError), transaction.atomic():
                self.clearance(**values)
        self.clearance(amount=0)

    def test_only_one_active_clearance_per_transfer_but_reversal_keeps_history(self):
        first, second = self.clearance(), self.clearance()
        link = ClearedTransfer.objects.create(clearance=first, transfer=self.transfer)
        with self.assertRaises(IntegrityError), transaction.atomic():
            ClearedTransfer.objects.create(clearance=second, transfer=self.transfer)
        link.active = False
        link.save(update_fields=['active'])
        ClearedTransfer.objects.create(clearance=second, transfer=self.transfer)
        self.assertEqual(ClearedTransfer.objects.count(), 2)
        with self.assertRaises(IntegrityError), transaction.atomic():
            ClearedTransfer.objects.create(clearance=first, transfer=self.transfer, active=False)
