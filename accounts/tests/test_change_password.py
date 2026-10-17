"""A logged-in person changes their own password. Wrong current passwords are limited."""

from datetime import timedelta

from django.contrib.auth import authenticate
from django.test import TestCase
from django.utils import timezone

from accounts import services
from accounts.forms import ChangePasswordForm
from audit.models import AuditEvent
from groups.tests.helpers import make_user

OLD = "tablestakes-91"
NEW = "river-card-4417"


class ChangePasswordTests(TestCase):
    def setUp(self):
        self.user = make_user("ana")

    def test_the_right_current_password_changes_it_and_cancels_reset_links(self):
        link, _ = services.issue_reset_link(self.user, created_by=make_user("hana"))
        services.change_password(self.user, OLD, NEW)
        self.assertIsNone(authenticate(username="ana", password=OLD))
        self.assertIsNotNone(authenticate(username="ana", password=NEW))
        link.refresh_from_db()
        self.assertIsNotNone(link.revoked_at)
        event = AuditEvent.objects.get(action="password.changed")
        self.assertEqual((event.actor, event.group_id), (self.user, None))
        self.assertNotIn(NEW, str(event.summary) + str(event.data))

    def test_a_wrong_current_password_is_refused_and_recorded(self):
        with self.assertRaisesMessage(services.PasswordChangeError, "not your current password"):
            services.change_password(self.user, "guess-one", NEW)
        self.assertIsNotNone(authenticate(username="ana", password=OLD))
        event = AuditEvent.objects.get(action="password.change_refused")
        self.assertNotIn("guess-one", str(event.summary) + str(event.data))

    def test_five_wrong_tries_stop_even_the_right_one_for_fifteen_minutes(self):
        for n in range(services.CHANGE_TRIES):
            with self.assertRaises(services.PasswordChangeError):
                services.change_password(self.user, f"guess-{n}", NEW)
        with self.assertRaisesMessage(services.PasswordChangeError, "Try again in 15 minutes"):
            services.change_password(self.user, OLD, NEW)
        self.assertIsNotNone(authenticate(username="ana", password=OLD))
        AuditEvent.objects.filter(action="password.change_refused").update(
            created_at=timezone.now() - timedelta(minutes=services.CHANGE_MINUTES, seconds=1)
        )
        services.change_password(self.user, OLD, NEW)
        self.assertIsNotNone(authenticate(username="ana", password=NEW))

    def test_another_persons_wrong_tries_do_not_count(self):
        ben = make_user("ben")
        for n in range(services.CHANGE_TRIES):
            with self.assertRaises(services.PasswordChangeError):
                services.change_password(ben, f"guess-{n}", NEW)
        services.change_password(self.user, OLD, NEW)


class ChangePasswordFormTests(TestCase):
    def setUp(self):
        self.user = make_user("ana")

    def form(self, new, repeat=None):
        return ChangePasswordForm(self.user, {"current_password": OLD, "new_password1": new, "new_password2": repeat or new})

    def test_the_new_password_follows_the_sign_up_rules(self):
        self.assertTrue(self.form(NEW).is_valid())
        weak = self.form("12345678")
        self.assertFalse(weak.is_valid())
        self.assertIn("Use more than digits.", weak.errors["new_password1"])
        self.assertIn("The two passwords don't match.", self.form(NEW, "other-pass-1").errors["new_password2"])

    def test_the_fields_and_no_autofocus_inside_the_profile(self):
        form = ChangePasswordForm(self.user)
        self.assertEqual(list(form.fields), ["current_password", "new_password1", "new_password2"])
        self.assertEqual(form.fields["current_password"].widget.attrs["autocomplete"], "current-password")
        self.assertNotIn("autofocus", form.fields["new_password1"].widget.attrs)


class SentTwiceTests(TestCase):
    def test_the_same_change_sent_twice_succeeds_and_counts_no_wrong_try(self):
        user = make_user("ana")
        services.change_password(user, OLD, NEW)
        services.change_password(user, OLD, NEW)
        self.assertFalse(AuditEvent.objects.filter(action="password.change_refused").exists())
        self.assertEqual(AuditEvent.objects.filter(action="password.changed").count(), 1)
