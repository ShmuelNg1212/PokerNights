import uuid
from django.test import TestCase
from django.urls import reverse
from games import services as games
from games.forms import SettingsForm
from games.tests.helpers import STAKES
from groups.tests.helpers import make_user
from ledger.tests.helpers import Night
from ledger.tests.test_rake import configure
from ledger import queries
from settlement import services as settle


class RakeWebTests(TestCase):
    def setUp(self):
        self.n = Night('A', 'B', state='open')
        self.client.force_login(self.n.host.user)
        self.url = reverse('session_settings', args=[self.n.session.pk])
        self.data = {name: str(value // 100) for name, value in STAKES.items()}

    def test_native_settings_exact_rate_and_request_replay_after_buy_in(self):
        key = str(uuid.uuid4())
        data = {**self.data, 'rake_mode': 'percent', 'rake_percentage': '5.25', 'request_id': key}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        version = games.current_settings(self.n.session)
        self.assertEqual(version.rake_basis_points, 525)
        self.n.buy('A', 1000)
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(games.current_settings(self.n.session).pk, version.pk)
        page = self.client.get(self.url)
        self.assertContains(page, 'Rake is locked')
        self.assertContains(page, 'value="5.25"')

    def test_invalid_percentage_preserves_typed_input_and_error(self):
        for value in ('5.001', '100', '0', ''):
            page = self.client.post(self.url, {**self.data, 'rake_mode': 'percent', 'rake_percentage': value})
            self.assertEqual(page.status_code, 200)
            self.assertTrue(page.context['form'].errors)
        page = self.client.post(self.url, {**self.data, 'rake_mode': 'flat', 'rake_flat': '20.50'})
        self.assertEqual(page.status_code, 302)
        self.assertEqual(games.current_settings(self.n.session).rake_flat, 2050)

    def test_group_totals_include_live_and_reversals_and_isolate_units(self):
        configure(self.n, rake_mode='flat', rake_flat=2000)
        self.n.buy('A', 1000)
        page = self.client.get(reverse('group', args=[self.n.group.pk]))
        self.assertContains(page, 'Group rake account')
        self.assertEqual(page.context['rake_totals'], {'php': 2000, 'chips': 0})
        self.assertContains(page, '0 chips')
        self.assertContains(page, reverse('session', args=[self.n.session.pk]))
        self.client.force_login(make_user('outsider'))
        self.assertEqual(self.client.get(reverse('group', args=[self.n.group.pk])).status_code, 404)

    def test_count_preview_and_final_session_result_copy(self):
        configure(self.n, rake_mode='percent', rake_basis_points=500)
        self.n.buy('A', 1000); self.n.buy('B', 1000)
        self.n.go('reconciliation')
        page = self.client.get(reverse('session', args=[self.n.session.pk]))
        self.assertContains(page, 'data-rake="10000"')
        self.assertContains(page, '+ ₱100 rake')
        self.n.cash('A', 950); self.n.cash('B', 950)
        settle.finalize(self.n.session.pk, self.n.host)
        page = self.client.get(reverse('session', args=[self.n.session.pk]))
        self.assertContains(page, 'Cash-outs plus rake equal gross buy-ins')
        self.assertContains(page, 'Results include rake already collected')
        settle.close_night(self.n.session.night_id, self.n.host)
        page = self.client.get(reverse('night', args=[self.n.session.night_id]))
        self.assertContains(page, 'No positive result after rake')
        self.assertNotContains(page, 'Everyone broke even')
        self.assertContains(page, 'Nobody owes anything')
        self.assertEqual(queries.group_rake(self.n.group)[0]['php'], 10000)

    def test_chip_flat_whole_amount_and_unused_fields(self):
        def form(mode, flat='', rate=''):
            return SettingsForm({**self.data, 'unit':'chips', 'rake_mode':mode, 'rake_flat':flat, 'rake_percentage':rate}, unit='chips')
        self.assertFalse(form('flat', '1.5').is_valid())
        f = form('flat', '20'); self.assertTrue(f.is_valid(), f.errors)
        self.assertEqual(f.cleaned_data['rake_flat'], 20)
        f = form('off', '20', '5'); self.assertTrue(f.is_valid(), f.errors)
        self.assertEqual((f.cleaned_data['rake_flat'], f.cleaned_data['rake_basis_points']), (0, 0))
