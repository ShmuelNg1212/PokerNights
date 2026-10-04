"""Rake selection through real forms, creation, and opening buy-ins."""
import datetime
import uuid

from django import forms
from django.test import TestCase
from django.urls import reverse

from audit.models import AuditEvent
from games import services
from games.forms import SessionForm, SettingsForm
from games.models import GameNight, GameSession, SettingsVersion
from games.tests.helpers import STAKES, make_session, make_table
from groups.errors import RuleError
from groups.tests.helpers import make_group, make_user
from ledger.models import BuyIn


class RakeControlsTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.table = make_table(self.host)
        self.client.force_login(self.host.user)
        self.data = {name: str(value // 100) for name, value in STAKES.items()}
        self.data.update(table_id=self.table.pk, game_date='2026-10-04', game_type='nlh', unit='php')
        self.create_url = reverse('session_create', args=[self.group.pk])

    def test_new_session_has_native_choices_and_no_inactive_browser_constraints(self):
        page = self.client.get(self.create_url)
        self.assertContains(page, 'Percentage of buy-in')
        self.assertContains(page, 'type="radio"', count=3)
        self.assertContains(page, 'name="rake_flat"', count=1)
        self.assertContains(page, 'name="rake_percentage"', count=1)
        self.assertIsInstance(page.context['form'].fields['rake_mode'].widget, forms.RadioSelect)
        self.assertNotContains(page, 'min="0.01"')

    def test_only_selected_value_is_validated_in_both_forms_and_units(self):
        for form_type in (SettingsForm, SessionForm):
            for unit in ('php', 'chips'):
                for mode, flat, rate, expected in (
                    ('flat', '20', '0', (0, 2000 if unit == 'php' else 20)),
                    ('flat', '20', 'oops', (0, 2000 if unit == 'php' else 20)),
                    ('percent', 'oops', '5.25', (525, 0)),
                    ('off', 'oops', 'oops', (0, 0)),
                ):
                    with self.subTest(form=form_type.__name__, unit=unit, mode=mode, rate=rate):
                        options = {'tables': [self.table]} if form_type is SessionForm else {}
                        f = form_type({**self.data, 'unit': unit, 'rake_mode': mode,
                                       'rake_flat': flat, 'rake_percentage': rate}, unit=unit, **options)
                        self.assertTrue(f.is_valid(), f.errors)
                        self.assertEqual((f.cleaned_data['rake_basis_points'], f.cleaned_data['rake_flat']), expected)

    def test_active_errors_preserve_values_and_selected_mode_without_creating_session(self):
        for rate in ('', '0', '100', '5.001', 'NaN', 'oops'):
            page = self.client.post(self.create_url, {**self.data, 'rake_mode': 'percent', 'rake_percentage': rate})
            self.assertEqual(page.status_code, 200)
            self.assertIn('rake_percentage', page.context['form'].errors)
            self.assertEqual(page.context['form']['rake_percentage'].value(), rate)
            self.assertEqual(page.context['form']['rake_mode'].value(), 'percent')
        for unit, amount in (('php', ''), ('php', '0'), ('php', '-1'), ('chips', '1.5')):
            page = self.client.post(self.create_url, {**self.data, 'unit': unit, 'rake_mode': 'flat', 'rake_flat': amount})
            self.assertIn('rake_flat', page.context['form'].errors)
        self.assertFalse(GameNight.objects.exists())
        self.assertFalse(GameSession.objects.exists())

    def test_creation_rule_precedes_exact_opening_fees_and_lock(self):
        for unit in ('php', 'chips'):
            for mode, expected in (('off', 0), ('flat', 20), ('percent', 50)):
                page = self.client.post(self.create_url, {**self.data, 'unit': unit, 'rake_mode': mode,
                                                          'rake_flat': '20', 'rake_percentage': '5'})
                self.assertEqual(page.status_code, 302)
                session = GameSession.objects.latest('pk')
                settings = services.current_settings(session)
                self.assertEqual(settings.rake_mode, mode)
                services.add_participant(session.pk, self.host, self.host.pk)
                page = self.client.get(reverse('session', args=[session.pk]))
                self.assertContains(page, 'Choose rake before buy-ins')
                services.transition(session.pk, self.host, 'open')
                services.transition(session.pk, self.host, 'start', request_id=uuid.uuid4())
                buy = session.buy_ins.get()
                factor = 100 if unit == 'php' else 1
                self.assertEqual((buy.amount, buy.rake_amount, buy.playable_amount),
                                 (1000 * factor, expected * factor, (1000 - expected) * factor))
                settings_url = reverse('session_settings', args=[session.pk])
                page = self.client.get(settings_url)
                for field in ('rake_mode', 'rake_flat', 'rake_percentage'):
                    self.assertTrue(page.context['form'].fields[field].disabled)
                self.assertContains(page, 'Default opening buy-ins also lock the rule')
                response = self.client.post(settings_url, {**self.data, 'max_buy_in': '3000', 'rake_mode': 'off',
                                                          'request_id': uuid.uuid4()})
                self.assertEqual(response.status_code, 302)
                self.assertEqual(services.current_settings(session).rake(), settings.rake())
                self.assertNotContains(self.client.get(reverse('session', args=[session.pk])), 'Choose rake before buy-ins')

    def test_service_invalid_creation_has_no_partial_rows(self):
        before = (GameNight.objects.count(), GameSession.objects.count(), SettingsVersion.objects.count(), AuditEvent.objects.count())
        for rule in ({'rake_mode': 'percent', 'rake_basis_points': 10000}, {'rake_mode': 'flat', 'rake_flat': 0}):
            with self.assertRaises(RuleError):
                services.create_session(self.host, {**STAKES, 'table_id': self.table.pk,
                                                    'game_date': datetime.date(2026, 10, 4), 'game_type': 'nlh', **rule})
        self.assertEqual((GameNight.objects.count(), GameSession.objects.count(), SettingsVersion.objects.count(), AuditEvent.objects.count()), before)

    def test_initial_flat_consuming_buy_in_refuses_start_atomically(self):
        session = make_session(self.host, table=self.table, state='open', rake_mode='flat', rake_flat=100000)
        services.add_participant(session.pk, self.host, self.host.pk)
        session.refresh_from_db()
        before = (AuditEvent.objects.count(), session.version)
        with self.assertRaises(RuleError):
            services.transition(session.pk, self.host, 'start', request_id=uuid.uuid4())
        session.refresh_from_db()
        self.assertEqual(session.state, 'open')
        self.assertFalse(BuyIn.objects.exists())
        self.assertEqual((AuditEvent.objects.count(), session.version), before)

    def test_outsider_cannot_read_or_submit_configuration(self):
        session = make_session(self.host, table=self.table)
        self.client.force_login(make_user('outsider'))
        for url in (self.create_url, reverse('session_settings', args=[session.pk])):
            self.assertEqual(self.client.get(url).status_code, 404)
            self.assertEqual(self.client.post(url, self.data).status_code, 404)
