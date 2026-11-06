import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from settlement import services
from settlement.models import Clearance
from settlement.tests.test_carried import Club


@override_settings(DEBTS_VIEW=True)
class DebtViewTests(TestCase):
    def setUp(self):
        self.club = Club('Ana', 'Ben', 'Carlo', 'Dee')
        self.ana, self.ben, self.carlo, self.dee = self.club.members.values()
        for member in self.club.members.values():
            member.user = get_user_model().objects.create_user(username=member.display_name, password='tablestakes-91')
            member.save(update_fields=['user'])
        self.nights = [self.club.closed({'Ana': -500, 'Ben': 500}), self.club.closed({'Ana': 300, 'Ben': -300})]
        self.other = self.club.closed({'Carlo': -100, 'Dee': 100})
        self.url = reverse('group', args=[self.club.group.pk])
        self.post_url = f'/g/{self.club.group.pk}/debts/settle/'
        self.data = {'unit': 'php', 'member_a': self.ana.pk, 'member_b': self.ben.pk,
            'transfer_id': [self.club.unpaid(n)[0].pk for n in self.nights], 'net': 20000, 'request_id': str(uuid.uuid4())}

    def test_player_sees_own_pair_and_host_sees_every_pair(self):
        self.client.force_login(self.ben.user)
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['debt_rows']), 1)
        self.assertContains(response, 'Got ₱200 from Ana')
        self.assertContains(response, 'from 2 sessions')
        self.client.force_login(self.club.host.user)
        self.assertEqual(len(self.client.get(self.url).context['debt_rows']), 2)
        self.client.force_login(self.ana.user)
        response = self.client.get(self.url)
        self.assertContains(response, 'Ben confirms when paid')
        self.assertNotContains(response, 'data-sheet-open="debt-php-')

    def test_receiver_can_settle_and_receipt_disappears_after_reload(self):
        self.client.force_login(self.ben.user)
        response = self.client.post(self.post_url, self.data, follow=True)
        self.assertContains(response, 'Settled with Ana: ₱200')
        self.assertContains(response, 'Undo')
        self.assertEqual(Clearance.objects.count(), 1)
        self.assertNotContains(self.client.get(self.url), 'Settled with Ana: ₱200')

    def test_stale_page_refuses_and_keeps_debts(self):
        self.client.force_login(self.ben.user)
        services.mark_paid(self.nights[0], self.club.host, self.data['transfer_id'][0], uuid.uuid4())
        response = self.client.post(self.post_url, self.data, follow=True)
        self.assertContains(response, 'These debts changed. Look again.')
        self.assertContains(response, 'id="debts"')
        self.assertEqual(Clearance.objects.count(), 0)

    def test_nonmember_is_404_and_payer_post_is_403(self):
        outsider = get_user_model().objects.create_user(username='outsider')
        self.client.force_login(outsider)
        self.assertEqual(self.client.post(self.post_url, self.data).status_code, 404)
        self.client.force_login(self.ana.user)
        self.assertEqual(self.client.post(self.post_url, self.data).status_code, 403)

    @override_settings(DEBTS_VIEW=False)
    def test_switch_off_hides_section_and_refuses_routes(self):
        self.client.force_login(self.ben.user)
        self.assertNotContains(self.client.get(self.url), 'id="debts"')
        self.assertEqual(self.client.post(self.post_url, self.data).status_code, 404)

    def test_undo_route_restores_pair_and_checks_permission(self):
        self.client.force_login(self.ben.user)
        self.client.post(self.post_url, self.data)
        clearance = Clearance.objects.get()
        undo = f'/g/{self.club.group.pk}/debts/{clearance.pk}/undo/'
        self.client.force_login(self.ana.user)
        self.assertEqual(self.client.post(undo, {'reason': 'Mistake'}).status_code, 403)
        self.client.force_login(self.ben.user)
        response = self.client.post(undo, {'reason': 'Mistake'}, follow=True)
        self.assertContains(response, 'Got ₱200 from Ana')

    def test_rake_payer_sees_fund_row_without_a_pair_settle_button(self):
        from settlement.tests.test_rake_fund import raked, to_fund, finish
        n = raked('A', 'B')
        to_fund(n)
        n.buy('A', 1000); n.buy('B', 1000)
        finish(n, A=1400, B=500)
        plan = services.close_night(n.session.night_id, n.host)
        payer = plan.transfers.get(to_rake_fund=True).payer
        payer.user = get_user_model().objects.create_user(username='rake-payer')
        payer.save(update_fields=['user'])
        self.client.force_login(payer.user)
        response = self.client.get(reverse('group', args=[n.group.pk]))
        self.assertContains(response, 'pays the Rake fund')
        self.assertContains(response, 'A host confirms when paid.')

    def test_viewer_without_debts_has_no_debts_section(self):
        from groups import services as groups
        member = groups.add_roster_player(self.club.host, 'Eli')
        member.user = get_user_model().objects.create_user(username='no-debts')
        member.save(update_fields=['user'])
        self.client.force_login(member.user)
        response = self.client.get(self.url)
        self.assertEqual(response.context['debt_rows'], [])
        self.assertNotContains(response, 'id="debts"')

    def test_exact_cancel_has_a_zero_clear_button(self):
        self.club.closed({'Ana': 200, 'Ben': -200})
        self.client.force_login(self.ana.user)
        self.assertContains(self.client.get(self.url), 'Clear ₱0: these cancel out')
