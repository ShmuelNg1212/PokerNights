"""Password reset links: the link's life, and the page a person opens to set a new password."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, TransactionTestCase, override_settings, skipUnlessDBFeature
from django.urls import reverse
from django.utils import timezone

from accounts import services
from accounts.models import PasswordResetLink
from accounts.services import ResetLinkError
from audit.models import AuditEvent
from groups.errors import RuleError
from groups.tests.helpers import make_user
from web.tests.test_concurrency import kinds, race

OLD, NEW = "tablestakes-91", "riverboat-queen-7"


class ResetLinkServiceTests(TestCase):
    def setUp(self):
        self.host, self.user = make_user("hana"), make_user("maria")

    def issue(self):
        return services.issue_reset_link(self.user, created_by=self.host, group_id=7)

    def test_issue_stores_only_the_hash_and_lasts_a_day(self):
        before = timezone.now()
        link, token = self.issue()
        self.assertEqual(link.token_hash, services.hash_token(token))
        self.assertNotIn(token, [str(value) for value in PasswordResetLink.objects.values_list()[0]])
        self.assertEqual((link.user, link.created_by, link.group_id), (self.user, self.host, 7))
        self.assertAlmostEqual(link.expires_at, before + timedelta(hours=24), delta=timedelta(seconds=5))
        self.assertEqual(services.usable_reset_link(token), link)

    def test_a_new_link_cancels_the_earlier_one(self):
        _, first = self.issue()
        _, second = self.issue()
        with self.assertRaisesMessage(ResetLinkError, "This reset link is not valid."):
            services.usable_reset_link(first)
        self.assertEqual(services.usable_reset_link(second).user, self.user)
        self.assertEqual(list(services.live_reset_links([self.user.pk, self.host.pk])), [self.user.pk])

    def test_redeem_sets_the_password_once_and_is_audited(self):
        link, token = self.issue()
        self.assertEqual(services.redeem_reset_link(token, NEW), self.user)
        self.user.refresh_from_db()
        link.refresh_from_db()
        self.assertTrue(self.user.check_password(NEW))
        self.assertIsNotNone(link.used_at)
        event = AuditEvent.objects.get(action="password.reset")
        self.assertEqual((event.actor, event.group_id, event.target_id), (self.user, 7, self.user.pk))
        self.assertNotIn(token, event.summary + str(event.data))
        with self.assertRaisesMessage(ResetLinkError, "This reset link has already been used."):
            services.redeem_reset_link(token, "another-password-3")
        self.assertTrue(get_user_model().objects.get(pk=self.user.pk).check_password(NEW))

    def test_refused_links_change_nothing(self):
        cases = [
            ({"expires_at": timezone.now()}, "This reset link has expired."),
            ({"revoked_at": timezone.now()}, "This reset link is not valid."),
            ({"used_at": timezone.now()}, "This reset link has already been used."),
        ]
        for change, message in cases:
            link, token = self.issue()
            PasswordResetLink.objects.filter(pk=link.pk).update(**change)
            with self.assertRaisesMessage(ResetLinkError, message):
                services.redeem_reset_link(token, NEW)
        for token in ("", "not-a-token"):
            with self.assertRaisesMessage(ResetLinkError, "This reset link is not valid."):
                services.redeem_reset_link(token, NEW)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(OLD))
        self.assertFalse(AuditEvent.objects.filter(action="password.reset").exists())

    def test_a_switched_off_account_cannot_be_reset(self):
        _, token = self.issue()
        get_user_model().objects.filter(pk=self.user.pk).update(is_active=False)
        with self.assertRaisesMessage(ResetLinkError, "This reset link is not valid."):
            services.usable_reset_link(token)

    def test_revoke_cancels_live_links_and_counts_them(self):
        _, token = self.issue()
        self.assertEqual(services.revoke_reset_links(self.user), 1)
        self.assertEqual(services.revoke_reset_links(self.user), 0)
        with self.assertRaises(ResetLinkError):
            services.usable_reset_link(token)

    @override_settings(RESET_LINKS=False)
    def test_switch_off_refuses_every_link(self):
        with override_settings(RESET_LINKS=True):
            _, token = self.issue()
        with self.assertRaisesMessage(ResetLinkError, "This reset link is not valid."):
            services.redeem_reset_link(token, NEW)
        self.assertEqual(services.live_reset_links([self.user.pk]), {})


class ResetPageTests(TestCase):
    def setUp(self):
        self.host, self.user = make_user("hana"), make_user("maria")
        self.link, self.token = services.issue_reset_link(self.user, created_by=self.host, group_id=None)
        self.url = reverse("password_reset", args=[self.token])

    def save(self, first=NEW, second=None, client=None):
        return (client or self.client).post(self.url, {"new_password1": first, "new_password2": first if second is None else second})

    def test_page_names_the_username_and_uses_the_entry_frame(self):
        page = self.client.get(self.url)
        self.assertContains(page, "<h1>Set a new password</h1>")
        self.assertContains(page, "Your username is <strong>maria</strong>.")
        self.assertContains(page, 'class="page entry-page"')
        self.assertNotContains(page, "site-header")
        self.assertContains(page, 'autocomplete="new-password"', count=2)
        self.assertContains(page, "data-password-toggle", count=1)
        self.assertContains(page, "At least 8 characters, not a common password, not only digits, and not like your username.")
        self.assertContains(page, "Repeat password")
        self.assertContains(page, 'data-busy="Saving…"')
        self.assertContains(page, "<title>Reset password · PokerNights</title>")
        self.assertNotIn("maria", page.content.decode().split("</title>")[0])

    def test_page_is_never_stored_and_sends_no_referrer(self):
        for page in (self.client.get(self.url), self.client.get(reverse("password_reset", args=["nope"]))):
            self.assertIn("no-store", page["Cache-Control"])
            self.assertEqual(page["Referrer-Policy"], "no-referrer")

    def test_opening_the_link_never_uses_it(self):
        for _ in range(3):
            self.assertEqual(self.client.get(self.url).status_code, 200)
        self.link.refresh_from_db()
        self.assertIsNone(self.link.used_at)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(OLD))

    def test_saving_logs_in_and_lands_on_your_groups(self):
        response = self.save()
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        home = self.client.get(reverse("home"))
        self.assertEqual(home.context["user"], self.user)
        self.assertContains(home, "Password changed. You&#x27;re logged in.")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(NEW))
        fresh = Client()
        self.assertTrue(fresh.login(username="maria", password=NEW))
        self.assertFalse(fresh.login(username="maria", password=OLD))

    def test_other_devices_are_signed_out(self):
        other = Client()
        other.force_login(self.user)
        self.assertEqual(other.get(reverse("home")).status_code, 200)
        self.save()
        self.assertEqual(other.get(reverse("home")).status_code, 302)

    def test_a_person_logged_in_as_someone_else_becomes_the_link_account(self):
        self.client.force_login(self.host)
        self.assertContains(self.client.get(self.url), "Your username is <strong>maria</strong>.")
        self.save()
        self.assertEqual(self.client.get(reverse("home")).context["user"], self.user)

    def test_each_refused_password_uses_the_plain_words_and_keeps_the_link(self):
        cases = [
            (("short1",), "Too short. Use at least 8 characters."),
            (("password123",), "That password is too common. Pick a less usual one."),
            (("8675309421",), "Use more than digits."),
            (("maria-ma",), "Too close to your username. Pick something different."),
            ((NEW, NEW + "x"), "The two passwords don&#x27;t match."),
        ]
        for passwords, message in cases:
            page = self.save(*passwords)
            self.assertContains(page, message)
            self.assertContains(page, 'class="notice notice-bad" role="alert"', count=1)
            self.assertNotContains(page, f'value="{passwords[0]}"')
        self.assertEqual(list(self.save("12345678").context["form"].errors), ["new_password1"])
        self.assertEqual(list(self.save(NEW, "other").context["form"].errors), ["new_password2"])
        self.link.refresh_from_db()
        self.assertIsNone(self.link.used_at)
        self.assertRedirects(self.save(), reverse("home"), fetch_redirect_response=False)

    def test_a_link_that_does_not_work_says_why(self):
        self.save()
        self.client.post(reverse("logout"))
        used = self.client.get(self.url)
        self.assertContains(used, "<h1>This reset link doesn't work</h1>", status_code=404)
        self.assertContains(used, "This reset link has already been used. Ask a host of your group for a new one.", status_code=404)
        self.assertContains(used, 'class="notice notice-bad" role="alert"', count=1, status_code=404)
        self.assertContains(used, reverse("login"), status_code=404)
        self.assertNotContains(used, "maria", status_code=404)
        self.assertEqual(self.save("another-password-3").status_code, 404)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(NEW))
        unknown = self.client.get(reverse("password_reset", args=["nope"]))
        self.assertContains(unknown, "This reset link is not valid.", status_code=404)

    def test_an_expired_link_is_refused_on_save(self):
        PasswordResetLink.objects.filter(pk=self.link.pk).update(expires_at=timezone.now())
        self.assertContains(self.save(), "This reset link has expired.", status_code=404)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(OLD))

    @override_settings(RESET_LINKS=False)
    def test_switch_off_makes_the_page_refuse(self):
        self.assertContains(self.client.get(self.url), "This reset link is not valid.", status_code=404)
        self.assertEqual(self.save().status_code, 404)


def refusing(action):
    """The race helper reports a RuleError as a refusal; a refused link is one."""
    def run():
        try:
            return action()
        except ResetLinkError as error:
            raise RuleError(str(error)) from error
    return run


@skipUnlessDBFeature("has_select_for_update")
class ResetLinkRaceTests(TransactionTestCase):
    def setUp(self):
        self.host, self.user = make_user("hana"), make_user("maria")

    def test_two_uses_of_one_link_set_one_password(self):
        _, token = services.issue_reset_link(self.user, created_by=self.host, group_id=None)
        outcomes = race(
            refusing(lambda: services.redeem_reset_link(token, "first-password-11")),
            refusing(lambda: services.redeem_reset_link(token, "second-password-22")),
        )
        self.assertEqual(kinds(outcomes), ["ok", "refused"], outcomes)
        self.user.refresh_from_db()
        winner = "first-password-11" if outcomes[0][0] == "ok" else "second-password-22"
        self.assertTrue(self.user.check_password(winner))
        self.assertEqual(AuditEvent.objects.filter(action="password.reset").count(), 1)

    def test_two_issues_leave_one_live_link(self):
        issue = lambda: services.issue_reset_link(self.user, created_by=self.host, group_id=None)  # noqa: E731
        outcomes = race(issue, issue)
        self.assertEqual(kinds(outcomes), ["ok", "ok"], outcomes)
        live = PasswordResetLink.objects.filter(user=self.user, used_at__isnull=True, revoked_at__isnull=True)
        self.assertEqual(live.count(), 1)
