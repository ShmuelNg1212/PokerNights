"""Opening entries are ordinary money records, committed with the first start."""
import uuid
from unittest.mock import patch

from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature
from django.urls import reverse

from audit.models import AuditEvent
from games import services as games
from games.models import GameSession, Participant, PlayPeriod
from groups.errors import NotAllowed, RuleError
from groups.tests.helpers import add_player, make_group, make_user
from ledger import services as ledger
from ledger.models import BuyIn
from ledger.tests.helpers import Night
from web.tests.test_concurrency import race, kinds


class OpeningBuyInTests(TestCase):
    def start(self, night, rid=None, **kwargs):
        return games.transition(night.session.pk, night.host, 'start', request_id=rid or uuid.uuid4(), **kwargs)

    def test_default_records_each_joined_player_before_clock_and_updates_version(self):
        n = Night('Ana', 'Ben', state='open')
        version = n.refresh().version
        result = self.start(n)
        rows = list(BuyIn.objects.filter(session=n.session))
        self.assertEqual([r.amount for r in rows], [100000, 100000])
        self.assertTrue(all(r.recorded_by == n.host.user for r in rows))
        self.assertTrue(all(r.settings_version == games.current_settings(result) for r in rows))
        period = PlayPeriod.objects.get(session=result)
        self.assertTrue(all(r.created_at <= period.started_at for r in rows))
        self.assertEqual(result.version, version + 3)
        self.assertEqual(AuditEvent.objects.filter(session_id=result.pk, action='buy_in.recorded').count(), 2)
        self.assertEqual(n.line('Ana').buy_in_total, 100000)

    def test_mixed_existing_and_reversed_entries_and_absent_players(self):
        n = Night('Manual', 'Reversed', 'Left', 'Withdrawn', state='open')
        n.buy('Manual', 500)
        old = n.buy('Reversed', 1000)
        ledger.reverse_buy_in(n.session.pk, n.host, old.pk, 'Wrong entry')
        Participant.objects.filter(pk=n.players['Left'].pk).update(status='left')
        games.withdraw_participant(n.session.pk, n.host, n.players['Withdrawn'].pk)
        self.start(n)
        self.assertEqual(n.line('Manual').buy_in_total, 50000)
        self.assertEqual(n.line('Reversed').buy_in_total, 100000)
        self.assertEqual(n.line('Left').buy_in_total, 0)
        self.assertEqual(BuyIn.objects.filter(session=n.session).count(), 3)

    def test_latest_settings_and_chips(self):
        n = Night('Ana', state='open', unit='chips')
        current = games.current_settings(n.session)
        changed = games.update_settings(n.session.pk, n.host, {**current.stakes(), 'default_buy_in': 1500})
        self.start(n)
        row = BuyIn.objects.get(session=n.session)
        self.assertEqual((row.amount, row.settings_version_id), (1500, changed.pk))

    def test_opt_out_and_late_join_and_resume_do_not_add_entries(self):
        n = Night('Ana', state='open')
        self.start(n, opening_buy_ins=False)
        late = add_player(n.group, 'late')
        games.add_participant(n.session.pk, late, late.pk)
        games.transition(n.session.pk, n.host, 'end')
        games.transition(n.session.pk, n.host, 'resume')
        self.assertFalse(BuyIn.objects.filter(session=n.session).exists())

    def test_next_set_is_money_free_until_started_and_previous_is_unchanged(self):
        n = Night('Ana', 'Ben', state='open')
        self.start(n)
        first = list(BuyIn.objects.filter(session=n.session).values_list('pk', 'amount'))
        games.transition(n.session.pk, n.host, 'end')
        second = games.start_next_set(n.session.night_id, n.host)
        self.assertFalse(second.buy_ins.exists())
        games.transition(second.pk, n.host, 'start')
        self.assertEqual(list(second.buy_ins.values_list('amount', flat=True)), [100000, 100000])
        self.assertEqual(list(n.session.buy_ins.values_list('pk', 'amount')), first)

    def test_retry_after_reversal_or_end_does_not_recreate_anything(self):
        n = Night('Ana', state='open')
        rid = uuid.uuid4()
        self.start(n, rid)
        ledger.reverse_buy_in(n.session.pk, n.host, BuyIn.objects.get(session=n.session).pk, 'Not bought in')
        games.transition(n.session.pk, n.host, 'end')
        version = n.refresh().version
        audits = AuditEvent.objects.filter(session_id=n.session.pk).count()
        self.start(n, rid)
        self.assertEqual(BuyIn.objects.filter(session=n.session).count(), 1)
        self.assertEqual(PlayPeriod.objects.filter(session=n.session).count(), 1)
        self.assertEqual(n.refresh().version, version)
        self.assertEqual(AuditEvent.objects.filter(session_id=n.session.pk).count(), audits)
        with self.assertRaises(RuleError):
            self.start(n)

    def test_empty_start_retry_has_durable_marker(self):
        n = Night(state='open')
        rid = uuid.uuid4()
        first = self.start(n, rid)
        self.assertEqual(first.start_request_id, rid)
        version = first.version
        self.assertEqual(self.start(n, rid).version, version)
        self.assertEqual(PlayPeriod.objects.filter(session=n.session).count(), 1)

    def test_failure_after_one_entry_rolls_back_entire_start(self):
        n = Night('Ana', 'Ben', state='open')
        audits = AuditEvent.objects.filter(session_id=n.session.pk).count()
        version = n.refresh().version
        record = ledger.record_buy_in
        calls = 0
        def fail_second(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuleError('Injected refusal')
            return record(*args, **kwargs)
        with patch('ledger.services.record_buy_in', side_effect=fail_second), self.assertRaises(RuleError):
            self.start(n)
        n.refresh()
        self.assertEqual((n.session.state, n.session.version, n.session.start_request_id), ('open', version, None))
        self.assertFalse(n.session.buy_ins.exists())
        self.assertFalse(PlayPeriod.objects.filter(session=n.session).exists())
        self.assertEqual(AuditEvent.objects.filter(session_id=n.session.pk).count(), audits)

    def test_player_and_other_group_cannot_start(self):
        n = Night('Ana', state='open')
        with self.assertRaises(NotAllowed):
            games.transition(n.session.pk, add_player(n.group, 'player'), 'start')
        _, outsider = make_group('outsider', 'Other')
        with self.assertRaises(RuleError):
            games.transition(n.session.pk, outsider, 'start')
        self.assertFalse(n.session.buy_ins.exists())

    def test_legacy_running_set_is_never_backfilled(self):
        n = Night('Ana', state='open')
        games.transition(n.session.pk, n.host, 'start', opening_buy_ins=False)
        GameSession.objects.filter(pk=n.session.pk).update(start_request_id=None)
        with self.assertRaises(RuleError):
            self.start(n)
        self.assertFalse(n.session.buy_ins.exists())


class OpeningStartPageTests(TestCase):
    def test_native_option_defaults_on_and_posts_once(self):
        n = Night('Ana', 'Ben', state='open')
        self.client.force_login(n.host.user)
        page = self.client.get(reverse('session', args=[n.session.pk]))
        self.assertContains(page, 'name="opening_buy_ins" checked')
        self.assertContains(page, 'Add usual buy-in (₱1,000)')
        rid = str(uuid.uuid4())
        data = {'action': 'start', 'opening_buy_ins': 'on', 'request_id': rid}
        url = reverse('session_transition', args=[n.session.pk])
        self.client.post(url, data)
        self.client.post(url, data)
        self.assertEqual(list(n.session.buy_ins.values_list('amount', flat=True)), [100000, 100000])
        self.assertContains(self.client.get(reverse('session_log', args=[n.session.pk])), '₱1,000')

    def test_unchecked_and_permission_gates(self):
        n = Night('Ana', state='open')
        url = reverse('session_transition', args=[n.session.pk])
        self.client.force_login(add_player(n.group, 'player').user)
        self.assertEqual(self.client.post(url, {'action': 'start', 'opening_buy_ins': 'on'}).status_code, 403)
        self.client.force_login(make_user('stranger'))
        self.assertEqual(self.client.post(url, {'action': 'start', 'opening_buy_ins': 'on'}).status_code, 404)
        self.client.force_login(n.host.user)
        self.client.post(url, {'action': 'start', 'request_id': str(uuid.uuid4())})
        self.assertFalse(n.session.buy_ins.exists())
        self.assertEqual(n.refresh().state, 'running')


@skipUnlessDBFeature('has_select_for_update')
class ConcurrentOpeningTests(TransactionTestCase):
    def test_same_request_from_four_threads_starts_once(self):
        n = Night('Ana', 'Ben', state='open')
        rid = uuid.uuid4()
        outcomes = race(*[lambda: games.transition(n.session.pk, n.host, 'start', request_id=rid)] * 4)
        self.assertEqual(kinds(outcomes), ['ok'] * 4, outcomes)
        self.assertEqual(n.session.buy_ins.count(), 2)
        self.assertEqual(PlayPeriod.objects.filter(session=n.session).count(), 1)

    def test_competing_starts_have_one_winner(self):
        n = Night('Ana', state='open')
        outcomes = race(*[lambda: games.transition(n.session.pk, n.host, 'start', request_id=uuid.uuid4())] * 3)
        self.assertEqual(kinds(outcomes), ['ok', 'refused', 'refused'], outcomes)
        self.assertEqual(n.session.buy_ins.count(), 1)

    def test_manual_buy_in_serializes_with_start(self):
        n = Night('Ana', state='open')
        outcomes = race(lambda: games.transition(n.session.pk, n.host, 'start', request_id=uuid.uuid4()),
                        lambda: n.buy('Ana', 500))
        self.assertEqual(kinds(outcomes), ['ok', 'ok'], outcomes)
        amounts = list(n.session.buy_ins.values_list('amount', flat=True))
        self.assertIn(amounts, [[50000], [100000, 50000]])
