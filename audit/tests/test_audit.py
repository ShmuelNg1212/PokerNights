from django.contrib.auth import get_user_model
from django.db import transaction
from django.test import TestCase

from audit import services
from audit.admin import AuditEventAdmin
from audit.models import AuditEvent


class AuditTests(TestCase):
    def test_record_stores_actor_target_and_reason(self):
        user = get_user_model().objects.create_user("ana", password="x")
        event = services.record(
            "thing.done", actor=user, group_id=3, session_id=7, target=user, summary="Did it", reason="Because"
        )
        self.assertEqual(event.target_type, "accounts.user")
        self.assertEqual(event.target_id, user.pk)
        self.assertEqual((event.group_id, event.session_id, event.reason), (3, 7, "Because"))

    def test_event_rolls_back_with_its_caller(self):
        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                services.record("thing.done")
                raise RuntimeError("the business write failed")
        self.assertEqual(AuditEvent.objects.count(), 0)

    def test_admin_is_read_only(self):
        model_admin = AuditEventAdmin(AuditEvent, None)
        self.assertFalse(model_admin.has_add_permission(None))
        self.assertFalse(model_admin.has_change_permission(None))
        self.assertFalse(model_admin.has_delete_permission(None))
