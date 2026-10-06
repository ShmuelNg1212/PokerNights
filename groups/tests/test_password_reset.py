"""A host creates and cancels a password reset link for a member of their group."""

from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from accounts import services as accounts
from accounts.models import PasswordResetLink
from audit.models import AuditEvent
from groups import services
from groups.errors import NotAllowed, RuleError
from groups.models import Member
from groups.tests.helpers import add_player, make_group, make_user


class PasswordResetServiceTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.maria = add_player(self.group, "maria")

    def test_host_issues_for_a_player_and_it_is_audited(self):
        member, link, token = services.create_password_reset(self.host, self.maria.pk)
        self.assertEqual(member, self.maria)
        self.assertEqual((link.user, link.created_by, link.group_id), (self.maria.user, self.host.user, self.group.pk))
        self.assertEqual(accounts.usable_reset_link(token), link)
        event = AuditEvent.objects.get(action="password_reset.issued")
        self.assertEqual((event.actor, event.group_id, event.target_id), (self.host.user, self.group.pk, self.maria.pk))
        self.assertNotIn(token, event.summary + str(event.data))

    def test_host_issues_for_a_co_host(self):
        co_host = add_player(self.group, "ben", role=Member.Role.HOST)
        self.assertEqual(services.create_password_reset(self.host, co_host.pk)[0], co_host)

    def test_a_player_cannot_issue(self):
        ben = add_player(self.group, "ben")
        with self.assertRaises(NotAllowed):
            services.create_password_reset(ben, self.maria.pk)
        with self.assertRaises(NotAllowed):
            services.cancel_password_reset(ben, self.maria.pk)
        self.assertFalse(PasswordResetLink.objects.exists())

    def refused(self, member, message):
        with self.assertRaisesMessage(RuleError, message):
            services.create_password_reset(self.host, member.pk)

    def test_each_refusal(self):
        self.refused(self.host, "This is for another player.")
        roster = services.add_roster_player(self.host, "Lolo")
        self.refused(roster, "Lolo has no login.")
        for flag in ("is_staff", "is_superuser"):
            admin = add_player(self.group, f"admin_{flag}")
            setattr(admin.user, flag, True)
            admin.user.save()
            self.refused(admin, "A site administrator's password is set in the admin.")
        other_group, other_host = make_group("otto", "Other Game")
        here = Member.objects.create(group=self.group, user=other_host.user, display_name="Otto")
        self.refused(here, "Otto hosts another group. The site administrator resets their password.")
        self.assertFalse(PasswordResetLink.objects.exists())
        self.assertFalse(AuditEvent.objects.filter(action="password_reset.issued").exists())

    def test_a_player_of_another_group_can_still_be_helped(self):
        other_group, _ = make_group("otto", "Other Game")
        Member.objects.create(group=other_group, user=self.maria.user, display_name="maria")
        self.assertEqual(services.create_password_reset(self.host, self.maria.pk)[0], self.maria)

    def test_a_member_outside_the_group_or_removed_is_refused(self):
        _, other_host = make_group("otto", "Other Game")
        stranger = add_player(other_host.group, "sam")
        self.refused(stranger, "That member is not in this group.")
        services.remove_member(self.host, self.maria.pk)
        self.refused(self.maria, "That member is not in this group.")

    def test_an_archived_group_takes_no_link(self):
        services.archive_group(self.host)
        with self.assertRaises(RuleError):
            services.create_password_reset(self.host, self.maria.pk)

    def test_cancel_stops_the_link_and_is_audited_once(self):
        _, _, token = services.create_password_reset(self.host, self.maria.pk)
        services.cancel_password_reset(self.host, self.maria.pk)
        services.cancel_password_reset(self.host, self.maria.pk)  # a repeated tap
        with self.assertRaises(accounts.ResetLinkError):
            accounts.usable_reset_link(token)
        event = AuditEvent.objects.get(action="password_reset.cancelled")
        self.assertEqual((event.actor, event.group_id, event.target_id), (self.host.user, self.group.pk, self.maria.pk))

    @override_settings(RESET_LINKS=False)
    def test_switch_off_refuses(self):
        self.refused(self.maria, "Password reset links are turned off.")


class PasswordResetViewTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.maria = add_player(self.group, "maria")
        self.create = reverse("member_reset_link", args=[self.group.pk, self.maria.pk])
        self.cancel = reverse("member_reset_link_cancel", args=[self.group.pk, self.maria.pk])
        self.settings_url = reverse("group", args=[self.group.pk]) + "?view=settings"
        self.client.force_login(self.host.user)

    def test_host_sees_the_link_once(self):
        response = self.client.post(self.create)
        self.assertRedirects(response, self.settings_url + "#players", fetch_redirect_response=False)
        page = self.client.get(self.settings_url)
        self.assertContains(page, "<strong>Reset link for maria.</strong> Send it to maria only. Whoever opens it can set the password.")
        self.assertContains(page, "It works once and expires ")
        url = page.context["new_reset_link"]["url"]
        self.assertTrue(url.startswith("http://testserver/accounts/reset/"))
        self.assertContains(page, f'value="{url}"')
        self.assertEqual(self.client.get(url).status_code, 200)
        again = self.client.get(self.settings_url)
        self.assertNotContains(again, "/accounts/reset/")
        self.assertContains(again, "Reset link active until ")
        self.assertContains(again, self.cancel)

    def test_a_prefetch_does_not_use_up_the_notice(self):
        self.client.post(self.create)
        self.client.get(self.settings_url, headers={"X-Sec-Purpose": "prefetch"})
        self.assertContains(self.client.get(self.settings_url), "Reset link for maria.")

    def test_cancel(self):
        self.client.post(self.create)
        self.client.get(self.settings_url)
        self.client.post(self.cancel)
        page = self.client.get(self.settings_url)
        self.assertContains(page, "Reset link cancelled.")
        self.assertNotContains(page, "Reset link active until")
        self.assertFalse(accounts.live_reset_links([self.maria.user_id]))

    def test_a_refusal_is_a_message(self):
        roster = services.add_roster_player(self.host, "Lolo")
        self.client.post(reverse("member_reset_link", args=[self.group.pk, roster.pk]))
        self.assertContains(self.client.get(self.settings_url), "Lolo has no login.")

    def test_a_player_is_forbidden_and_an_outsider_finds_nothing(self):
        self.client.force_login(self.maria.user)
        self.assertEqual(self.client.post(reverse("member_reset_link", args=[self.group.pk, self.host.pk])).status_code, 403)
        self.client.force_login(make_user("stranger"))
        self.assertEqual(self.client.post(self.create).status_code, 404)
        self.assertEqual(self.client.post(self.cancel).status_code, 404)
        self.assertFalse(PasswordResetLink.objects.exists())

    def test_get_is_not_allowed(self):
        self.assertEqual(self.client.get(self.create).status_code, 405)

    def test_action_is_offered_only_to_hosts_for_members_with_a_login(self):
        roster = services.add_roster_player(self.host, "Lolo")
        page = self.client.get(self.settings_url)
        self.assertContains(page, self.create)
        self.assertContains(page, "Create password reset link", count=1)
        self.assertNotContains(page, reverse("member_reset_link", args=[self.group.pk, roster.pk]))
        self.assertNotContains(page, reverse("member_reset_link", args=[self.group.pk, self.host.pk]))
        self.client.force_login(self.maria.user)
        self.assertNotContains(self.client.get(self.settings_url), "reset link")

    @override_settings(RESET_LINKS=False)
    def test_switch_off_hides_the_action(self):
        self.assertNotContains(self.client.get(self.settings_url), "reset link")

    def test_settings_queries_do_not_grow_with_members(self):
        before = self.count_queries()
        for name in ("ana", "ben", "cy"):
            services.create_password_reset(self.host, add_player(self.group, name).pk)
        self.assertEqual(self.count_queries(), before)

    def count_queries(self):
        with CaptureQueriesContext(connection) as queries:
            self.client.get(self.settings_url)
        return len(queries)
