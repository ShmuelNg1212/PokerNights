"""The Copy button beside a link that is shown once. What the button does is checked in copy.mjs."""

from django.test import TestCase
from django.urls import reverse

from groups.tests.helpers import add_player, make_group


class CopyLinkMarkupTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.maria = add_player(self.group, "maria")
        self.settings_url = reverse("group", args=[self.group.pk]) + "?view=settings"
        self.client.force_login(self.host.user)

    def assertCopyField(self, page, field_id, url, label):
        self.assertContains(page, f'<input type="text" readonly id="{field_id}" value="{url}" aria-label="{label}"', count=1)
        # Hidden until the script shows it, so a browser without scripts offers no dead button.
        self.assertContains(page, f'<button type="button" class="copy-button" data-copy="{field_id}" aria-label="Copy link" hidden>Copy</button>', count=1)
        self.assertContains(page, f'data-copy-status="{field_id}" role="status"', count=1)

    def test_page_without_a_new_link_has_no_copy_button_but_loads_the_script(self):
        page = self.client.get(self.settings_url)
        self.assertNotContains(page, "data-copy")
        self.assertContains(page, "js/copy.js")

    def test_new_invite_link_has_a_copy_button(self):
        self.client.post(reverse("invite_create", args=[self.group.pk]))
        page = self.client.get(self.settings_url)
        self.assertCopyField(page, "new-invite-link", page.context["new_invite_url"], "Invite link")

    def test_new_reset_link_has_a_copy_button(self):
        self.client.post(reverse("member_reset_link", args=[self.group.pk, self.maria.pk]))
        page = self.client.get(self.settings_url)
        self.assertCopyField(page, "new-reset-link", page.context["new_reset_link"]["url"], "Password reset link for maria")

    def test_both_links_at_once_keep_separate_fields(self):
        self.client.post(reverse("invite_create", args=[self.group.pk]))
        self.client.post(reverse("member_reset_link", args=[self.group.pk, self.maria.pk]))
        page = self.client.get(self.settings_url)
        self.assertContains(page, 'class="copy-button"', count=2)
        self.assertContains(page, 'data-copy="new-invite-link"', count=1)
        self.assertContains(page, 'data-copy="new-reset-link"', count=1)
