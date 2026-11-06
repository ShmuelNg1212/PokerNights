import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from settlement import services
from settlement.tests.test_carried import Club


@override_settings(DEBTS_VIEW=True)
class DebtPagesTests(TestCase):
    def setUp(self):
        self.club = Club('Ana', 'Ben')
        self.ana, self.ben = self.club.members.values()
        for member in (self.ana, self.ben):
            member.user = get_user_model().objects.create_user(username=member.display_name)
            member.save(update_fields=['user'])
        self.nights = [self.club.closed({'Ana': -500, 'Ben': 500}), self.club.closed({'Ana': 300, 'Ben': -300})]

    def settle(self):
        return services.settle_pair(self.club.group.pk, self.ben, 'php', self.ana.pk, self.ben.pk,
            [self.club.unpaid(n)[0].pk for n in self.nights], 20000, uuid.uuid4())

    def test_cleared_session_names_counterpart_and_only_host_or_recorder_sees_undo(self):
        clearance = self.settle()
        url = reverse('night', args=[self.nights[0]])
        self.client.force_login(self.ben.user)
        response = self.client.get(url)
        self.assertContains(response, 'Settled with Ana on')
        self.assertContains(response, f'/g/{self.club.group.pk}/debts/{clearance.pk}/undo/')
        self.assertNotContains(response, f'/transfers/{self.club.unpaid(self.nights[0])[0].pk}/paid/')
        self.client.force_login(self.ana.user)
        self.assertNotContains(self.client.get(url), f'/g/{self.club.group.pk}/debts/{clearance.pk}/undo/')

    def test_receiver_can_mark_paid_and_undo_only_their_mark_from_session(self):
        url = reverse('night', args=[self.nights[0]])
        self.client.force_login(self.ben.user)
        transfer = self.club.unpaid(self.nights[0])[0]
        self.assertContains(self.client.get(url), reverse('transfer_paid', args=[self.nights[0], transfer.pk]))
        services.mark_paid(self.nights[0], self.ben, transfer.pk, uuid.uuid4())
        self.assertContains(self.client.get(url), reverse('transfer_unpaid', args=[self.nights[0], transfer.pk]))

    def test_home_nets_by_other_person_and_clearance_removes_due(self):
        self.client.force_login(self.ben.user)
        response = self.client.get(reverse('home'))
        card = response.context['cards'][0]
        self.assertEqual([(d.amount, d.owes) for d in card.dues], [(20000, False)])
        self.assertContains(response, 'See all debts')
        self.assertContains(response, f'/g/{self.club.group.pk}/#debts')
        self.settle()
        self.assertEqual(self.client.get(reverse('home')).context['cards'][0].dues, [])

    def test_sessions_not_settled_filter_excludes_cleared_sessions(self):
        self.settle()
        self.client.force_login(self.ben.user)
        response = self.client.get(reverse('group', args=[self.club.group.pk]) + '?past=unsettled')
        self.assertEqual(response.context['not_settled'], 0)
        self.assertEqual(response.context['past_years'], [])

    @override_settings(DEBTS_VIEW=False)
    def test_flag_off_keeps_individual_home_transfers_and_host_only_actions(self):
        self.client.force_login(self.ben.user)
        response = self.client.get(reverse('home'))
        self.assertEqual(len(response.context['cards'][0].dues), 2)
        self.assertNotContains(response, 'See all debts')
        transfer = self.club.unpaid(self.nights[0])[0]
        self.assertNotContains(self.client.get(reverse('night', args=[self.nights[0]])),
                               reverse('transfer_paid', args=[self.nights[0], transfer.pk]))
