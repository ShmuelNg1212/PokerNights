"""A group's chip presets. A session copies one; a later edit changes no session."""
import uuid

from django.test import TestCase

from audit.models import AuditEvent
from games import services
from games.models import ChipPreset
from games.tests.helpers import make_session
from groups.errors import NotAllowed, RuleError
from groups.tests.helpers import add_player, make_group

RED = [{'colour': 'red', 'label': 'Small', 'value': 2500}]


class ChipPresetTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()

    def save(self, actor=None, preset_id=None, request_id=None, **data):
        data = {'name': 'Home set', 'unit': 'php', 'values': RED, **data}
        return services.save_chip_preset(actor or self.host, data, request_id or uuid.uuid4(), preset_id=preset_id)

    def test_host_saves_a_preset_with_canonical_values(self):
        preset = self.save()
        self.assertEqual((preset.group, preset.name, preset.unit), (self.group, 'Home set', 'php'))
        self.assertEqual(preset.values, [{'id': 'red', 'colour': 'red', 'label': 'Small', 'value': 2500}])
        self.assertTrue(AuditEvent.objects.filter(action='chip_preset.created').exists())

    def test_edit_replaces_name_unit_and_values(self):
        preset = self.save()
        edited = self.save(preset_id=preset.pk, name='Tournament', unit='chips', values=[{'colour': 'blue', 'value': 5}])
        self.assertEqual(edited.pk, preset.pk)
        self.assertEqual((edited.name, edited.unit, edited.values[0]['value']), ('Tournament', 'chips', 5))
        self.assertTrue(AuditEvent.objects.filter(action='chip_preset.updated').exists())

    def test_the_same_request_writes_once(self):
        rid = uuid.uuid4()
        first = self.save(request_id=rid)
        again = self.save(request_id=rid, name='Something else')
        self.assertEqual(again.pk, first.pk)
        self.assertEqual(ChipPreset.objects.count(), 1)
        self.assertEqual(ChipPreset.objects.get().name, 'Home set')

    def test_invalid_presets_are_refused(self):
        for data in [{'name': ''}, {'unit': 'usd'}, {'values': []}, {'values': [{'colour': 'red', 'value': 0}]},
                     {'values': [{'colour': 'red', 'value': 1}, {'colour': 'red', 'value': 2}]},
                     {'values': [{'colour': 'red', 'value': 1.5}]}]:
            with self.subTest(data=data), self.assertRaises(RuleError):
                self.save(**data)
        self.assertFalse(ChipPreset.objects.exists())

    def test_active_names_are_unique_and_an_archived_name_is_free(self):
        preset = self.save()
        with self.assertRaisesRegex(RuleError, 'already'):
            self.save()
        services.archive_chip_preset(self.host, preset.pk, uuid.uuid4())
        self.assertIsNotNone(ChipPreset.objects.get(pk=preset.pk).archived_at)
        self.save()
        self.assertEqual(ChipPreset.objects.filter(archived_at__isnull=True).count(), 1)

    def test_players_and_other_groups_cannot_write(self):
        preset = self.save()
        player = add_player(self.group, 'player')
        with self.assertRaises(NotAllowed):
            self.save(actor=player, name='Mine')
        with self.assertRaises(NotAllowed):
            services.archive_chip_preset(player, preset.pk, uuid.uuid4())
        _, other_host = make_group('olga', 'Other')
        with self.assertRaisesRegex(RuleError, 'not in this group'):
            self.save(actor=other_host, preset_id=preset.pk, name='Taken')
        with self.assertRaisesRegex(RuleError, 'not in this group'):
            services.archive_chip_preset(other_host, preset.pk, uuid.uuid4())
        preset.refresh_from_db()
        self.assertEqual((preset.name, preset.archived_at), ('Home set', None))

    def test_presets_for_a_unit_are_active_and_in_the_group(self):
        php = self.save()
        self.save(name='Chips', unit='chips', values=[{'colour': 'blue', 'value': 5}])
        gone = self.save(name='Old')
        services.archive_chip_preset(self.host, gone.pk, uuid.uuid4())
        _, other_host = make_group('olga', 'Other')
        services.save_chip_preset(other_host, {'name': 'Theirs', 'unit': 'php', 'values': RED}, uuid.uuid4())
        self.assertEqual(list(services.chip_presets_for(self.group, 'php')), [php])

    def test_editing_a_preset_changes_no_session(self):
        preset = self.save()
        session = make_session(self.host, state='open')
        services.set_chip_values(session.night_id, self.host, preset.values, uuid.uuid4(), revision=0)
        self.save(preset_id=preset.pk, values=[{'colour': 'red', 'value': 9900}])
        session.night.refresh_from_db()
        self.assertEqual(session.night.chip_values[0]['value'], 2500)
