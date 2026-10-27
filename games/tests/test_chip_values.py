"""Each session owns its chip denominations; all its sets share them."""
import uuid

from django.test import TestCase

from audit.models import AuditEvent
from games import services
from games.tests.helpers import make_session
from groups.errors import NotAllowed, RuleError
from groups.tests.helpers import add_player, make_group


class ChipValueTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.session = make_session(self.host, state='open')
        self.night = self.session.night

    def save(self, rows=None, **kwargs):
        return services.set_chip_values(
            self.night.pk, self.host,
            rows if rows is not None else [{'colour': 'red', 'label': 'Small', 'value': 2500}],
            kwargs.pop('request_id', uuid.uuid4()), revision=kwargs.pop('revision', 0), **kwargs,
        )

    def test_values_are_session_specific_and_touch_every_set(self):
        other = make_session(self.host, state='open', table_name='Other table')
        before = self.session.version
        saved = self.save()
        self.assertEqual(saved.chip_values, [{'id': 'red', 'colour': 'red', 'label': 'Small', 'value': 2500}])
        self.assertEqual(saved.chip_values_revision, 1)
        self.session.refresh_from_db()
        other.night.refresh_from_db()
        self.assertEqual(self.session.version, before + 1)
        self.assertEqual(self.session.night.chip_values, saved.chip_values)
        self.assertEqual(other.night.chip_values, [])
        self.assertTrue(AuditEvent.objects.filter(action='night.chip_values').exists())

    def test_repeated_request_does_not_write_twice_and_stale_edit_is_refused(self):
        rid = uuid.uuid4()
        self.save(request_id=rid)
        self.assertEqual(self.save(request_id=rid).chip_values_revision, 1)
        with self.assertRaisesRegex(RuleError, 'changed'):
            self.save()
        self.assertEqual(self.save(revision=1).chip_values_revision, 2)

    def test_invalid_values_and_roles_are_refused_without_changes(self):
        for rows in [[], [{'colour': 'nope', 'value': 100}], [{'colour': 'red', 'value': 0}],
                     [{'colour': 'red', 'value': True}], [{'colour': 'red', 'value': 1.5}],
                     [{'colour': 'red', 'value': 100_000_000_001}],
                     [{'colour': 'red', 'value': 100, 'label': 'x' * 41}],
                     [{'colour': 'red', 'value': 100}, {'colour': 'red', 'value': 200}]]:
            with self.subTest(rows=rows), self.assertRaises(RuleError):
                self.save(rows)
        player = add_player(self.group, 'player')
        with self.assertRaises(NotAllowed):
            services.set_chip_values(self.night.pk, player, [{'colour': 'red', 'value': 100}], uuid.uuid4(), revision=0)
        self.night.refresh_from_db()
        self.assertEqual(self.night.chip_values_revision, 0)

    def test_closed_and_archived_sessions_refuse_edits(self):
        self.night.status = 'closed'
        self.night.save(update_fields=['status'])
        with self.assertRaisesRegex(RuleError, 'closed'):
            self.save()
        self.night.status = 'open'
        from django.utils import timezone
        self.night.archived_at = timezone.now()
        self.night.save(update_fields=['status', 'archived_at'])
        with self.assertRaisesRegex(RuleError, 'archived'):
            self.save()

    def test_unit_change_cannot_reinterpret_saved_denominations(self):
        self.save()
        from games.tests.helpers import CHIP_STAKES
        with self.assertRaisesRegex(RuleError, 'chip values'):
            services.update_settings(self.session.pk, self.host, {'unit': 'chips', **CHIP_STAKES})
        self.session.refresh_from_db()
        self.assertEqual(self.session.unit, 'php')
