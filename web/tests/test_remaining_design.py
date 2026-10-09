from django.test import TestCase
from django.urls import reverse
from groups import services
from groups.tests.helpers import make_group, add_player
from games.models import Table


class RemainingFormsTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.client.force_login(self.host.user)
        self.group_url = reverse('group', args=[self.group.pk])
        self.settings_url = self.group_url + '?view=settings'

    def test_group_name_error_keeps_input_once(self):
        value = 'G' * 61
        page = self.client.post(reverse('group_create'), {'name': value}, follow=True)
        self.assertEqual(page.context['form']['name'].value(), value)
        self.assertTrue(page.context['form'].errors)
        self.assertFalse(self.client.get(reverse('home')).context['form'].is_bound)

    def test_duplicate_roster_and_rename_keep_local_form(self):
        first = services.add_roster_player(self.host, 'Ada')
        second = services.add_roster_player(self.host, 'Bea')
        page = self.client.post(reverse('member_add', args=[self.group.pk]), {'name': 'Ada'}, follow=True)
        self.assertEqual(page.context['add_form']['names'].value(), 'Ada')
        self.assertIn('already', str(page.context['add_form'].errors))
        page = self.client.post(reverse('member_rename', args=[self.group.pk, second.pk]), {'name': 'Ada'}, follow=True)
        member = next(m for m in page.context['members'] if m.pk == second.pk)
        self.assertEqual(member.rename_form['name'].value(), 'Ada')
        self.assertTrue(member.rename_form.errors)
        second.refresh_from_db()
        self.assertEqual(second.display_name, 'Bea')

    def test_table_error_retains_name_and_seats_without_writing(self):
        page = self.client.post(reverse('table_create', args=[self.group.pk]), {'name': 'Kitchen', 'seat_count': '13'}, follow=True)
        self.assertEqual(page.context['table_form']['name'].value(), 'Kitchen')
        self.assertEqual(page.context['table_form']['seat_count'].value(), '13')
        self.assertIn('seat_count', page.context['table_form'].errors)
        self.assertFalse(Table.objects.filter(group=self.group).exists())

    def test_failure_drafts_are_group_scoped_and_not_shown_to_player(self):
        other, _ = make_group(host_name='other')
        self.client.post(reverse('member_add', args=[self.group.pk]), {'name': ''})
        player = add_player(self.group, 'viewer')
        self.client.force_login(player.user)
        page = self.client.get(self.settings_url)
        self.assertNotIn('add_form', page.context)
        self.assertEqual(self.client.get(reverse('group', args=[other.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('member_add', args=[self.group.pk]), {'name': 'Cannot'}).status_code, 403)

    def test_group_title_contains_no_form_and_invite_shown_once(self):
        self.client.post(reverse('invite_create', args=[self.group.pk]))
        page = self.client.get(self.settings_url)
        title = page.content.decode().split('<title>')[1].split('</title>')[0]
        self.assertNotIn('<form', title)
        self.assertTrue(page.context['new_invite_url'])
        self.assertIsNone(self.client.get(self.settings_url).context['new_invite_url'])
