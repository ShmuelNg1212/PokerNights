import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from audit.models import AuditEvent
from games.models import GameNight, GameSession
from groups.errors import NotAllowed, RuleError
from settlement import queries, services
from settlement.models import Clearance, ClearedTransfer, ClearanceReversal
from settlement.tests.test_carried import Club


@override_settings(DEBTS_VIEW=True)
class SettlePairTests(TestCase):
    def setUp(self):
        self.club = Club('Ana', 'Ben', 'Carlo')
        self.ana, self.ben, self.carlo = self.club.members.values()
        for member in (self.ana, self.ben, self.carlo):
            member.user = get_user_model().objects.create_user(username=member.display_name)
            member.save(update_fields=['user'])
        self.nights = [self.club.closed({'Ana': -500, 'Ben': 500}),
                      self.club.closed({'Ana': -100, 'Ben': 100}),
                      self.club.closed({'Ana': 400, 'Ben': -400})]
        self.ids = [self.club.unpaid(n)[0].pk for n in self.nights]
        self.request = uuid.uuid4()

    def settle(self, actor=None, **changes):
        values = dict(group_id=self.club.group.pk, actor=actor or self.club.host, unit='php',
            member_a_id=self.ana.pk, member_b_id=self.ben.pk, transfer_ids=self.ids, net=20000,
            request_id=self.request)
        return services.settle_pair(**(values | changes))

    def test_host_clears_three_transfers_with_one_net_and_no_payment_rows(self):
        before = list(GameSession.objects.filter(night_id__in=self.nights).values_list('version', flat=True))
        clearance = self.settle()
        self.assertEqual((clearance.payer_id, clearance.payee_id, clearance.amount), (self.ana.pk, self.ben.pk, 20000))
        self.assertEqual(queries.debts(self.club.group, self.ana), [])
        self.assertEqual(ClearedTransfer.objects.filter(active=True).count(), 3)
        self.assertEqual(AuditEvent.objects.filter(action='debts.cleared').count(), 1)
        event = AuditEvent.objects.get(action='debts.cleared')
        self.assertEqual(set(event.data['transfer_ids']), set(self.ids))
        after = list(GameSession.objects.filter(night_id__in=self.nights).values_list('version', flat=True))
        self.assertEqual(after, [v + 1 for v in before])
        self.assertTrue(all(s.status == 'settled' for s in queries.settle_states(self.nights).values()))

    def test_receiver_can_settle_but_payer_and_third_member_cannot(self):
        for actor in (self.ana, self.carlo):
            with self.assertRaises(NotAllowed):
                self.settle(actor)
        self.settle(self.ben)

    def test_repeated_request_returns_first_even_after_undo_and_writes_nothing(self):
        first = self.settle(self.ben)
        self.assertEqual(self.settle(self.ben).pk, first.pk)
        self.assertEqual(Clearance.objects.count(), 1)
        self.assertEqual(AuditEvent.objects.filter(action='debts.cleared').count(), 1)
        services.undo_clearance(self.club.group.pk, self.ben, first.pk, 'Mistake')
        self.assertEqual(self.settle(self.ben).pk, first.pk)
        self.assertEqual(len(queries.debts(self.club.group, self.ana)[0].transfers), 3)

    def test_changed_ids_or_net_refuse_everything(self):
        for changes in ({'transfer_ids': self.ids[:-1]}, {'net': 20001}, {'transfer_ids': self.ids + self.ids[:1]}):
            with self.assertRaisesMessage(RuleError, 'These debts changed. Look again.'):
                self.settle(**changes)
        services.mark_paid(self.nights[0], self.club.host, self.ids[0], uuid.uuid4())
        with self.assertRaisesMessage(RuleError, 'These debts changed. Look again.'):
            self.settle()
        self.assertEqual(Clearance.objects.count(), 0)

    def test_zero_net_either_person_can_clear(self):
        self.club.closed({'Ana': 200, 'Ben': -200})
        row = queries.debts(self.club.group, self.ana)[0]
        clearance = self.settle(self.ana, transfer_ids=[t.pk for t in row.transfers], net=0)
        self.assertEqual(clearance.amount, 0)

    def test_negative_net_names_the_actual_receiver(self):
        self.club.closed({'Ana': 300, 'Ben': -300})
        row = queries.debts(self.club.group, self.ana)[0]
        clearance = self.settle(self.ana, transfer_ids=[t.pk for t in row.transfers], net=-10000)
        self.assertEqual((clearance.payer_id, clearance.payee_id, clearance.amount), (self.ben.pk, self.ana.pk, 10000))

    def test_only_host_or_recorder_can_undo_and_then_settle_again(self):
        clearance = self.settle(self.ben)
        with self.assertRaises(NotAllowed):
            services.undo_clearance(self.club.group.pk, self.ana, clearance.pk, 'Mistake')
        services.undo_clearance(self.club.group.pk, self.ben, clearance.pk, 'Mistake')
        services.undo_clearance(self.club.group.pk, self.ben, clearance.pk, 'Repeated')
        self.assertEqual(ClearanceReversal.objects.count(), 1)
        self.assertEqual(ClearedTransfer.objects.filter(active=True).count(), 0)
        self.assertEqual(queries.debts(self.club.group, self.ana)[0].net, 20000)
        self.settle(request_id=uuid.uuid4())
        self.assertEqual(Clearance.objects.count(), 2)

    def test_mark_paid_and_reopen_refuse_until_clearance_is_undone(self):
        clearance = self.settle()
        with self.assertRaisesMessage(RuleError, 'Undo that first.'):
            services.mark_paid(self.nights[0], self.club.host, self.ids[0], uuid.uuid4())
        with self.assertRaisesMessage(RuleError, 'settled across sessions'):
            services.reopen_night(self.nights[0], self.club.host, 'Wrong count')
        services.undo_clearance(self.club.group.pk, self.club.host, clearance.pk, 'Wrong count')
        services.reopen_night(self.nights[0], self.club.host, 'Wrong count')
        self.assertEqual(GameNight.objects.get(pk=self.nights[0]).status, 'open')

    def test_cleared_transfers_are_not_carried_into_another_session(self):
        self.settle()
        later = self.club.play({'Ana': 0, 'Ben': 0})
        self.assertEqual(queries.carryable(GameNight.objects.get(pk=later)), [])

    def test_switch_off_refuses_both_writes(self):
        with override_settings(DEBTS_VIEW=False), self.assertRaises(RuleError):
            self.settle()
        clearance = self.settle()
        with override_settings(DEBTS_VIEW=False), self.assertRaises(RuleError):
            services.undo_clearance(self.club.group.pk, self.club.host, clearance.pk, 'Mistake')

    def test_other_group_or_removed_actor_is_refused(self):
        other = Club('Elsewhere')
        with self.assertRaises(NotAllowed):
            self.settle(other.host)
        self.ben.status = 'removed'
        self.ben.save(update_fields=['status'])
        with self.assertRaises(NotAllowed):
            self.settle(self.ben)
