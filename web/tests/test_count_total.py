import uuid
from django.test import TestCase
from django.urls import reverse
from groups.tests.helpers import add_player, make_user
from ledger.tests.test_counts import counting, count


class CountTotalPageTests(TestCase):
    def setUp(self):
        self.night = counting('A', 'B')
        self.url = reverse('session', args=[self.night.session.pk])
        self.client.force_login(self.night.host.user)

    def test_confirmed_baseline_and_host_data_are_exact(self):
        count(self.night, 'A', 2000)
        count(self.night, 'B', 0)
        page = self.client.get(self.url)
        self.assertContains(page, 'data-count-accounted>₱2,000', count=1)  # the host has one total, with the next action
        self.assertContains(page, 'All counts match buy-ins.', count=2)  # that total, and the dock bar
        self.assertContains(page, 'data-tone="good">All counts match buy-ins.', count=2)
        self.assertContains(page, 'data-saved="200000"')
        self.assertContains(page, 'data-saved="0"')
        self.assertContains(page, 'data-bought="200000"')
        self.assertContains(page, 'js/counts.js')
        self.assertNotContains(page, 'Finalize results')

    def test_player_gets_confirmed_total_without_host_drafts(self):
        member = add_player(self.night.group, 'reader')
        self.client.force_login(member.user)
        page = self.client.get(self.url)
        self.assertContains(page, 'Confirmed counts', count=1)
        self.assertNotContains(page, 'data-count-preview')
        self.assertNotContains(page, 'data-count-input')

    def test_nonmember_cannot_read_counter_or_poll(self):
        self.client.force_login(make_user('outsider'))
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.get(reverse('session_state', args=[self.night.session.pk])).status_code, 404)

    def test_refused_drafts_remain_separate_from_confirmed_total(self):
        page = self.client.post(reverse('count_confirm', args=[self.night.session.pk]), {
            'request_id': str(uuid.uuid4()),
            f'count_{self.night.players["A"].pk}': '2000',
            f'count_{self.night.players["B"].pk}': 'bad',
        }, follow=True)
        self.assertContains(page, 'value="bad" data-keep=')
        self.assertContains(page, 'data-count-accounted>₱0', count=1)
        self.assertEqual(page.context['count_total'].missing, 2)

    def test_poll_contains_updated_confirmed_baseline(self):
        count(self.night, 'A', 1000)
        page = self.client.get(reverse('session_state', args=[self.night.session.pk]))
        self.assertIn('data-count-accounted>₱1,000', page.json()['html'])
        self.assertIn('data-saved="100000"', page.json()['html'])
