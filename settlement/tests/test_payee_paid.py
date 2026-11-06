import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from groups.errors import NotAllowed
from settlement import services
from settlement.models import Payment
from settlement.tests.test_carried import Club


@override_settings(DEBTS_VIEW=True)
class PayeePaidTests(TestCase):
    def setUp(self):
        self.club = Club('Ana', 'Ben', 'Carlo')
        self.ana, self.ben, self.carlo = self.club.members.values()
        for member in (self.ana, self.ben, self.carlo):
            member.user = get_user_model().objects.create_user(username=member.display_name)
            member.save(update_fields=['user'])
        self.night = self.club.closed({'Ana': -500, 'Ben': 500})
        self.transfer = self.club.unpaid(self.night)[0]

    def pay(self, actor):
        return services.mark_paid(self.night, actor, self.transfer.pk, uuid.uuid4())

    def test_payee_can_confirm_and_recorder_can_undo(self):
        payment = self.pay(self.ben)
        self.assertEqual(payment.recorded_by_id, self.ben.user_id)
        services.mark_unpaid(self.night, self.ben, self.transfer.pk)
        self.assertFalse(Payment.objects.get(pk=payment.pk).active)

    def test_payer_and_third_player_cannot_confirm_or_undo(self):
        for actor in (self.ana, self.carlo):
            with self.assertRaises(NotAllowed):
                self.pay(actor)
        self.pay(self.ben)
        for actor in (self.ana, self.carlo):
            with self.assertRaises(NotAllowed):
                services.mark_unpaid(self.night, actor, self.transfer.pk)

    def test_receiver_cannot_undo_host_record(self):
        self.pay(self.club.host)
        with self.assertRaises(NotAllowed):
            services.mark_unpaid(self.night, self.ben, self.transfer.pk)

    def test_switch_off_keeps_host_only_permissions(self):
        with override_settings(DEBTS_VIEW=False):
            with self.assertRaises(NotAllowed):
                self.pay(self.ben)
        self.pay(self.ben)
        with override_settings(DEBTS_VIEW=False), self.assertRaises(NotAllowed):
            services.mark_unpaid(self.night, self.ben, self.transfer.pk)

    def test_rake_fund_stays_host_only(self):
        from settlement.tests.test_rake_fund import raked, to_fund, finish
        n = raked('A', 'B')
        to_fund(n)
        n.buy('A', 1000); n.buy('B', 1000)
        finish(n, A=1400, B=500)
        plan = services.close_night(n.session.night_id, n.host)
        transfer = plan.transfers.get(to_rake_fund=True)
        payer = transfer.payer
        payer.user = get_user_model().objects.create_user(username='fund-payer')
        payer.save(update_fields=['user'])
        with self.assertRaises(NotAllowed):
            services.mark_paid(n.session.night_id, payer, transfer.pk, uuid.uuid4())
