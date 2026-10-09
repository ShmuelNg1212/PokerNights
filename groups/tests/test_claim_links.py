"""A claim link lets an account take over a roster player who had no login."""

from datetime import timedelta

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from audit.models import AuditEvent
from groups import services
from groups.errors import NotAllowed, RuleError
from groups.models import ClaimLink, Member

from .helpers import add_player, make_group, make_user


class ClaimLinkServiceTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.tito = services.add_roster_player(self.host, "Tito Boy")
        self.newcomer = make_user("titoboy")

    def issue(self, member=None):
        return services.create_claim_link(self.host, (member or self.tito).pk)

    def test_issue_stores_a_hash_and_a_second_issue_cancels_the_first(self):
        member, link, token = self.issue()
        self.assertEqual(member, self.tito)
        self.assertNotIn(token, [link.token_hash])
        self.assertEqual(link.token_hash, services.hash_token(token))
        self.assertAlmostEqual(link.expires_at, timezone.now() + timedelta(days=7), delta=timedelta(minutes=1))
        _, second, token2 = self.issue()
        with self.assertRaisesMessage(RuleError, "not valid"):
            services.usable_claim_link(token)
        self.assertEqual(services.usable_claim_link(token2), second)
        self.assertEqual(services.live_claim_links([self.tito.pk]), {self.tito.pk: second})
        self.assertEqual(AuditEvent.objects.filter(action="claim_link.issued", group_id=self.group.pk).count(), 2)

    def test_only_a_host_of_the_group_for_an_active_player_without_a_login(self):
        ben = add_player(self.group, "ben")
        with self.assertRaises(NotAllowed):
            services.create_claim_link(ben, self.tito.pk)
        with self.assertRaisesMessage(RuleError, "ben already has a login."):
            self.issue(ben)
        _, other_host = make_group("omar", "Other")
        with self.assertRaisesMessage(RuleError, "not in this group"):
            services.create_claim_link(other_host, self.tito.pk)
        services.remove_member(self.host, self.tito.pk)
        with self.assertRaisesMessage(RuleError, "not in this group"):
            self.issue()

    def test_an_archived_group_takes_no_link_and_its_links_stop(self):
        _, _, token = self.issue()
        services.archive_group(self.host)
        with self.assertRaises(RuleError):
            self.issue()
        with self.assertRaisesMessage(RuleError, "not valid"):
            services.usable_claim_link(token)

    def test_cancel_is_audited_once(self):
        _, _, token = self.issue()
        services.cancel_claim_link(self.host, self.tito.pk)
        services.cancel_claim_link(self.host, self.tito.pk)
        with self.assertRaisesMessage(RuleError, "not valid"):
            services.usable_claim_link(token)
        self.assertEqual(AuditEvent.objects.filter(action="claim_link.cancelled").count(), 1)

    def test_dead_links_say_why(self):
        _, link, token = self.issue()
        with self.assertRaisesMessage(RuleError, "This claim link is not valid."):
            services.usable_claim_link("nope")
        ClaimLink.objects.filter(pk=link.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
        with self.assertRaisesMessage(RuleError, "This claim link has expired."):
            services.usable_claim_link(token)
        _, _, token = self.issue()
        services.remove_member(self.host, self.tito.pk)
        with self.assertRaisesMessage(RuleError, "not valid"):
            services.usable_claim_link(token)

    def test_an_account_outside_the_group_becomes_the_player(self):
        _, link, token = self.issue()
        preview = services.claim_preview(self.newcomer, token)
        self.assertEqual((preview.member, preview.own, preview.refusal), (self.tito, None, None))
        member = services.claim_member(self.newcomer, token)
        self.assertEqual((member.pk, member.user, member.display_name, member.role), (self.tito.pk, self.newcomer, "Tito Boy", "player"))
        link.refresh_from_db()
        self.assertEqual(link.used_by, self.newcomer)
        self.assertIsNotNone(link.used_at)
        event = AuditEvent.objects.get(action="member.claimed")
        self.assertEqual((event.actor, event.group_id, event.target_id), (self.newcomer, self.group.pk, self.tito.pk))
        self.assertEqual(services.claim_member(self.newcomer, token).pk, self.tito.pk)  # a repeated tap
        self.assertEqual(AuditEvent.objects.filter(action="member.claimed").count(), 1)
        with self.assertRaisesMessage(RuleError, "already been used"):
            services.claim_member(make_user("someone"), token)
        with self.assertRaisesMessage(RuleError, "already has a login"):
            self.issue()

    def test_an_empty_entry_is_replaced_and_a_host_stays_a_host(self):
        own = Member.objects.create(group=self.group, user=self.newcomer, display_name="titoboy", role="host")
        _, _, token = self.issue()
        preview = services.claim_preview(self.newcomer, token)
        self.assertEqual((preview.own, preview.refusal), (own, None))
        member = services.claim_member(self.newcomer, token)
        self.assertEqual((member.pk, member.user, member.role), (self.tito.pk, self.newcomer, "host"))
        self.assertFalse(Member.objects.filter(pk=own.pk).exists())
        self.assertTrue(AuditEvent.objects.filter(action="member.replaced", group_id=self.group.pk).exists())

    def test_an_empty_removed_entry_is_replaced_too(self):
        own = Member.objects.create(group=self.group, user=self.newcomer, display_name="titoboy", status="removed")
        _, _, token = self.issue()
        self.assertEqual(services.claim_member(self.newcomer, token).user, self.newcomer)
        self.assertFalse(Member.objects.filter(pk=own.pk).exists())

    @override_settings(CLAIM_LINKS=False)
    def test_switch_off(self):
        with override_settings(CLAIM_LINKS=True):
            _, _, token = self.issue()
        with self.assertRaisesMessage(RuleError, "Claim links are turned off."):
            self.issue()
        with self.assertRaisesMessage(RuleError, "not valid"):
            services.usable_claim_link(token)
        self.assertEqual(services.live_claim_links([self.tito.pk]), {})


class ClaimLinkViewTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.tito = services.add_roster_player(self.host, "Tito Boy")
        self.create = reverse("member_claim_link", args=[self.group.pk, self.tito.pk])
        self.cancel = reverse("member_claim_link_cancel", args=[self.group.pk, self.tito.pk])
        self.settings_url = reverse("group", args=[self.group.pk]) + "?view=settings"
        self.client.force_login(self.host.user)

    def link(self):
        return reverse("claim", args=[services.create_claim_link(self.host, self.tito.pk)[2]])

    def test_the_host_sees_the_link_once_and_can_cancel(self):
        self.assertContains(self.client.get(self.settings_url), self.create)
        self.assertRedirects(self.client.post(self.create), self.settings_url + "#players", fetch_redirect_response=False)
        page = self.client.get(self.settings_url)
        self.assertContains(page, "<strong>Claim link for Tito Boy.</strong> Send it to Tito Boy only. Whoever opens it becomes Tito Boy in this group.")
        url = page.context["new_claim_link"]["url"]
        self.assertTrue(url.startswith("http://testserver/claim/"))
        self.assertContains(page, f'value="{url}"')
        again = self.client.get(self.settings_url)
        self.assertNotContains(again, "/claim/")
        self.assertContains(again, "Claim link active until ")
        self.client.post(self.cancel)
        self.assertNotContains(self.client.get(self.settings_url), "Claim link active until ")
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_offered_only_to_hosts_and_only_for_players_without_a_login(self):
        ben = add_player(self.group, "ben")
        page = self.client.get(self.settings_url)
        self.assertNotContains(page, reverse("member_claim_link", args=[self.group.pk, ben.pk]))
        self.client.force_login(ben.user)
        self.assertNotContains(self.client.get(self.settings_url), "claim-link")
        self.assertEqual(self.client.post(self.create).status_code, 403)
        _, other = make_group("omar", "Other")
        self.client.force_login(other.user)
        self.assertEqual(self.client.post(self.create).status_code, 404)

    def test_a_logged_in_account_confirms_then_is_the_player(self):
        url = self.link()
        user = make_user("titoboy")
        self.client.force_login(user)
        page = self.client.get(url)
        self.assertContains(page, "Join Friday Game as Tito Boy")
        self.assertContains(page, "You are logged in as <strong>titoboy</strong>.")
        self.assertContains(page, "Claim Tito Boy")
        self.assertEqual(page["Referrer-Policy"], "same-origin")
        self.assertIn("no-store", page["Cache-Control"])
        self.assertIsNone(Member.objects.get(pk=self.tito.pk).user)  # opening changes nothing
        response = self.client.post(url, follow=True)
        self.assertRedirects(response, reverse("group", args=[self.group.pk]))
        self.assertContains(response, "Welcome to Friday Game. You&#x27;re in as Tito Boy.")
        self.assertEqual(Member.objects.get(pk=self.tito.pk).user, user)
        self.assertRedirects(self.client.get(url), reverse("group", args=[self.group.pk]))  # their own used link
        self.client.force_login(make_user("late"))
        self.assertContains(self.client.get(url), "This claim link doesn't work", status_code=404)

    def test_an_empty_entry_is_named_before_it_is_replaced(self):
        url = self.link()
        ben = add_player(self.group, "ben")
        self.client.force_login(ben.user)
        self.assertContains(self.client.get(url), "You are already in this group as ben, with nothing recorded. That entry is replaced by Tito Boy.")
        self.client.post(url)
        self.assertFalse(Member.objects.filter(pk=ben.pk).exists())

    def test_a_signed_out_visitor_goes_to_sign_up_and_arrives_as_the_player(self):
        url = self.link()
        self.client.logout()
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('signup')}?next={url.replace('/', '%2F')}", fetch_redirect_response=False)
        with override_settings(SIGNUP_REQUIRES_INVITE=True):
            page = self.client.get(reverse("signup"), {"next": url})
            self.assertEqual(page.status_code, 200)
            self.assertContains(page, "Friday Game")
            response = self.client.post(reverse("signup"), {
                "username": "titoboy", "password1": "tablestakes-91", "password2": "tablestakes-91", "next": url,
            }, follow=True)
        self.assertRedirects(response, reverse("group", args=[self.group.pk]))
        self.assertContains(response, "You&#x27;re in as Tito Boy.")
        self.assertEqual(Member.objects.get(pk=self.tito.pk).user.username, "titoboy")
        self.assertEqual(Member.objects.filter(group=self.group).count(), 2)

    def test_a_dead_link_does_not_open_sign_up_where_an_invite_is_needed(self):
        self.client.logout()
        with override_settings(SIGNUP_REQUIRES_INVITE=True):
            self.assertEqual(self.client.get(reverse("signup"), {"next": "/claim/nope/"}).status_code, 403)
        self.assertContains(self.client.get("/claim/nope/"), "This claim link is not valid.", status_code=404)

    def test_the_settings_tab_does_not_ask_more_as_the_roster_grows(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        def count():
            with CaptureQueriesContext(connection) as queries:
                self.client.get(self.settings_url)
            return len(queries)

        services.create_claim_link(self.host, self.tito.pk)
        before = count()
        for member in services.add_roster_players(self.host, [f"P{n}" for n in range(8)]):
            services.create_claim_link(self.host, member.pk)
        self.assertEqual(count(), before)

    @override_settings(CLAIM_LINKS=False)
    def test_switch_off_hides_the_action(self):
        self.assertNotContains(self.client.get(self.settings_url), "claim-link")
        self.client.post(self.create, follow=True)
        self.assertFalse(ClaimLink.objects.exists())
