"""Group settings → Invite players: active links shown again, the new one marked, past invites as history."""

from datetime import timedelta

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from groups import services
from groups.models import Invite
from groups.tests.helpers import add_player, make_group


class InviteRowsTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.url = reverse("group", args=[self.group.pk]) + "?view=settings"
        self.client.force_login(self.host.user)

    def address(self, token):
        return "http://testserver" + reverse("invite_accept", args=[token])

    def test_an_active_link_is_there_every_time(self):
        invite, token = services.create_invite(self.host)
        for _ in range(2):
            page = self.client.get(self.url)
            self.assertContains(page, f'id="invite-link-{invite.pk}" value="{self.address(token)}"')
            self.assertContains(page, f'data-copy="invite-link-{invite.pk}"')
            self.assertContains(page, f'data-invite-share="{self.address(token)}"')
            self.assertContains(page, "Created by hana")

    def test_after_create_the_new_link_is_the_top_row_marked_new(self):
        services.create_invite(self.host)
        self.client.post(reverse("invite_create", args=[self.group.pk]))
        newest = Invite.objects.filter(group=self.group).first()
        page = self.client.get(self.url)
        body = page.content.decode()
        self.assertNotContains(page, "It is shown only once")
        self.assertContains(page, f'data-invite="{newest.pk}" data-arrived', count=1)
        self.assertContains(page, ">New<", count=1)
        self.assertLess(body.index(f'data-invite="{newest.pk}"'), body.index('data-invite="', body.index(f'data-invite="{newest.pk}"') + 1))
        self.assertNotContains(self.client.get(self.url), "data-arrived")  # once

    def test_the_create_button_steps_back_when_a_link_is_active(self):
        page = self.client.get(self.url)
        self.assertContains(page, "Create invite link")
        self.assertContains(page, "No invite link is active.")
        services.create_invite(self.host)
        page = self.client.get(self.url)
        self.assertContains(page, "Create another link")
        self.assertNotContains(page, "Create invite link")

    def test_a_link_from_before_says_it_cannot_be_shown(self):
        invite = services.create_invite(self.host)[0]
        Invite.objects.filter(pk=invite.pk).update(salt=None)
        page = self.client.get(self.url)
        self.assertContains(page, "This link was made before links could be shown again.")
        self.assertNotContains(page, f'id="invite-link-{invite.pk}"')
        self.assertContains(page, reverse("invite_revoke", args=[self.group.pk, invite.pk]))

    def test_past_invites_are_history_without_an_address(self):
        now = timezone.now()
        made = [services.create_invite(self.host) for _ in range(12)]
        for invite, _ in made:
            services.revoke_invite(self.host, invite.pk)
        old, old_token = made[0]
        Invite.objects.filter(pk=made[1][0].pk).update(revoked_at=None, expires_at=now - timedelta(days=1))
        Invite.objects.filter(pk=made[2][0].pk).update(revoked_at=None, use_count=20)
        page = self.client.get(self.url)
        past = page.context["past_invites"]
        self.assertEqual(len(past), 10)
        self.assertEqual([i.pk for i in past], [i.pk for i, _ in reversed(made)][:10])
        self.assertContains(page, "Past invites")
        for _, token in made:
            self.assertNotContains(page, token)
        self.assertNotIn(old.pk, [i.pk for i in past])

    def test_how_a_past_invite_ended_is_written(self):
        now = timezone.now()
        services.revoke_invite(self.host, services.create_invite(self.host)[0].pk)
        b = services.create_invite(self.host)[0]
        Invite.objects.filter(pk=b.pk).update(expires_at=now - timedelta(days=1))
        c = services.create_invite(self.host)[0]
        Invite.objects.filter(pk=c.pk).update(use_count=20)
        page = self.client.get(self.url)
        self.assertContains(page, "revoked")
        self.assertContains(page, "expired")
        self.assertContains(page, "used up")
        self.assertContains(page, "20 joined")

    def test_a_used_up_link_is_not_active(self):
        invite = services.create_invite(self.host)[0]
        Invite.objects.filter(pk=invite.pk).update(use_count=20)
        page = self.client.get(self.url)
        self.assertNotContains(page, f'id="invite-link-{invite.pk}"')
        self.assertContains(page, "No invite link is active.")

    def test_revoke_marks_past_invites_once(self):
        invite = services.create_invite(self.host)[0]
        self.client.post(reverse("invite_revoke", args=[self.group.pk, invite.pk]))
        self.assertContains(self.client.get(self.url), 'class="invites-past" data-changed')
        self.assertNotContains(self.client.get(self.url), "data-changed")

    def test_a_player_never_receives_a_link(self):
        token = services.create_invite(self.host)[1]
        player = add_player(self.group, "ben")
        self.client.force_login(player.user)
        page = self.client.get(self.url)
        self.assertNotContains(page, token)
        self.assertNotContains(page, "/join/")

    def test_a_prefetch_leaves_the_new_mark_for_the_real_page(self):
        self.client.post(reverse("invite_create", args=[self.group.pk]))
        self.client.get(self.url, headers={"X-Sec-Purpose": "prefetch"})
        self.assertContains(self.client.get(self.url), "data-arrived")

    @override_settings(INVITE_LINKS_SHOWN=False)
    def test_switch_off_is_today(self):
        services.create_invite(self.host)
        self.client.post(reverse("invite_create", args=[self.group.pk]))
        page = self.client.get(self.url)
        self.assertContains(page, "It is shown only once")
        self.assertContains(page, 'id="new-invite-link"')
        self.assertNotContains(page, 'id="invite-link-')
        self.assertNotContains(page, "data-invite-share")
