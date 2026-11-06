"""PostgreSQL contention at the public service boundary. No private-helper mocks."""
import queue
import threading
import time
import uuid
from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.db import connection, connections, transaction
from django.test import TransactionTestCase, override_settings

from groups import services as groups
from groups.errors import NotAllowed, RuleError
from groups.models import GameGroup
from settlement import services
from settlement.models import Clearance, Payment
from settlement.tests.test_carried import Club


@skipUnless(connection.vendor == 'postgresql', 'Requires PostgreSQL row locks')
@override_settings(DEBTS_VIEW=True)
class ClearanceConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.club = Club('Ana', 'Ben')
        self.ana, self.ben = self.club.members.values()
        self.ben.user = get_user_model().objects.create_user(username='receiver')
        self.ben.save(update_fields=['user'])
        self.night = self.club.closed({'Ana': -500, 'Ben': 500})
        self.ids = [t.pk for t in self.club.unpaid(self.night)]

    def settle(self, request_id=None):
        return services.settle_pair(self.club.group.pk, self.ben, 'php', self.ana.pk, self.ben.pk,
                                    self.ids, 50000, request_id or uuid.uuid4())

    def run_waiting_action(self, action, change):
        """Make the real service wait while the host changes access in a transaction."""
        started, result = queue.Queue(), {}
        def worker():
            try:
                with connections['default'].cursor() as cursor:
                    cursor.execute('SELECT pg_backend_pid()')
                    started.put(cursor.fetchone()[0])
                result['value'] = action()
            except Exception as error:
                result['error'] = error
            finally:
                connections.close_all()
        with transaction.atomic():
            GameGroup.objects.select_for_update().get(pk=self.club.group.pk)
            thread = threading.Thread(target=worker)
            thread.start()
            pid = started.get(timeout=5)
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                with connection.cursor() as cursor:
                    cursor.execute('SELECT wait_event_type FROM pg_stat_activity WHERE pid = %s', [pid])
                    waiting = cursor.fetchone()
                if waiting and waiting[0] == 'Lock':
                    break
                time.sleep(.01)
            else:
                self.fail('The service did not wait on the locked group.')
            change()
        thread.join(timeout=10)
        self.assertFalse(thread.is_alive(), 'The service stayed blocked after commit.')
        return result

    def test_removed_receiver_cannot_complete_waiting_settlement(self):
        result = self.run_waiting_action(self.settle, lambda: groups.remove_member(self.club.host, self.ben.pk))
        self.assertIsInstance(result.get('error'), NotAllowed, result)
        self.assertEqual(Clearance.objects.count(), 0)

    def test_removed_recorder_cannot_complete_waiting_undo(self):
        clearance = self.settle()
        result = self.run_waiting_action(
            lambda: services.undo_clearance(self.club.group.pk, self.ben, clearance.pk, 'Mistake'),
            lambda: groups.remove_member(self.club.host, self.ben.pk),
        )
        self.assertIsInstance(result.get('error'), NotAllowed, result)
        clearance.refresh_from_db()
        self.assertTrue(clearance.active)

    def test_archived_group_refuses_waiting_settlement(self):
        result = self.run_waiting_action(self.settle, lambda: groups.archive_group(self.club.host))
        self.assertIsInstance(result.get('error'), NotAllowed, result)
        self.assertEqual(Clearance.objects.count(), 0)

    def race(self, *actions):
        barrier, results = threading.Barrier(len(actions)), []
        def worker(action):
            try:
                barrier.wait(timeout=5)
                results.append(('ok', action()))
            except RuleError as error:
                results.append(('refused', str(error)))
            except Exception as error:
                results.append(('error', repr(error)))
            finally:
                connections.close_all()
        threads = [threading.Thread(target=worker, args=(action,)) for action in actions]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)
            self.assertFalse(thread.is_alive())
        return results

    def test_two_clearances_cannot_close_the_same_transfers(self):
        results = self.race(self.settle, self.settle)
        self.assertEqual(sorted(kind for kind, _ in results), ['ok', 'refused'], results)
        self.assertEqual(Clearance.objects.filter(active=True).count(), 1)

    def test_simultaneous_retry_returns_the_same_clearance(self):
        request_id = uuid.uuid4()
        results = self.race(lambda: self.settle(request_id), lambda: self.settle(request_id))
        self.assertEqual([kind for kind, _ in results], ['ok', 'ok'], results)
        self.assertEqual(len({value.pk for _, value in results}), 1)
        self.assertEqual(Clearance.objects.count(), 1)

    def test_paid_mark_and_clearance_cannot_both_win(self):
        results = self.race(self.settle,
            lambda: services.mark_paid(self.night, self.club.host, self.ids[0], uuid.uuid4()))
        self.assertEqual(sorted(kind for kind, _ in results), ['ok', 'refused'], results)
        self.assertEqual(Clearance.objects.filter(active=True).count() + Payment.objects.filter(active=True).count(), 1)
