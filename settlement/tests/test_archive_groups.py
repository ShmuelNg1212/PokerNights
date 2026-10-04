"""Hosts archive, restore and delete groups. Money records are never removed."""

import datetime

from django.contrib.auth import get_user_model
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from audit.models import AuditEvent
from games import services as games
from games.models import GameNight, GameSession, SettingsPreset, Table
from games.tests.helpers import make_preset, make_table
from groups import services as groups
from groups.errors import NotAllowed, RuleError
from groups.models import GameGroup, GroupRakeAccount, Invite, Member
from groups.tests.helpers import add_player, make_group, make_user
from ledger.models import BuyIn
from ledger.tests.helpers import Night
from web.home import archived_groups, home_cards

from .test_archive import closed_example


def reload(member):
    return Member.objects.select_related("group").get(pk=member.pk)


class GroupArchiveRulesTests(TestCase):
    def setUp(self):
        self.night = closed_example()
        self.host, self.group = self.night.host, self.night.group

    def test_archive_and_restore_keep_everything(self):
        before = (BuyIn.objects.count(), self.group.members.count(), GameNight.objects.count())
        archived = groups.archive_group(self.host)
        self.assertTrue(archived.is_archived)
        self.assertEqual(archived.archived_by, self.host.user)
        self.assertEqual((BuyIn.objects.count(), self.group.members.count(), GameNight.objects.count()), before)
        restored = groups.restore_group(reload(self.host))
        self.assertFalse(restored.is_archived)
        actions = list(AuditEvent.objects.filter(action__startswith="group.").values_list("action", flat=True))
        self.assertEqual(actions[-2:], ["group.archived", "group.restored"])

    def test_repeat_is_a_no_op(self):
        groups.archive_group(self.host)
        groups.archive_group(reload(self.host))
        groups.restore_group(reload(self.host))
        groups.restore_group(reload(self.host))
        self.assertEqual(AuditEvent.objects.filter(action="group.archived").count(), 1)
        self.assertEqual(AuditEvent.objects.filter(action="group.restored").count(), 1)

    def test_player_cannot_archive_restore_or_delete(self):
        player = add_player(self.group, "reader")
        for action in (groups.archive_group, groups.restore_group):
            with self.assertRaises(NotAllowed):
                action(player)
        with self.assertRaises(NotAllowed):
            games.delete_group(player, self.group.name)

    def test_unfinished_set_blocks_archive_and_delete(self):
        for state in ("open", "running", "reconciliation"):
            live = Night("A", state=state)
            with self.subTest(state):
                with self.assertRaisesMessage(RuleError, "Finish or cancel every set"):
                    groups.archive_group(live.host)
                with self.assertRaisesMessage(RuleError, "Finish or cancel every set"):
                    games.delete_group(live.host, live.group.name)

    def test_group_with_money_cannot_be_deleted(self):
        with self.assertRaisesMessage(RuleError, "cannot be deleted"):
            games.delete_group(self.host, self.group.name)
        groups.archive_group(self.host)
        with self.assertRaisesMessage(RuleError, "cannot be deleted"):
            games.delete_group(reload(self.host), self.group.name)
        self.assertTrue(GameGroup.objects.filter(pk=self.group.pk).exists())

    def test_database_refuses_to_delete_a_group_with_money(self):
        with self.assertRaises(ProtectedError):
            self.group.delete()

    def test_archived_group_takes_no_group_write(self):
        groups.archive_group(self.host)
        stale = self.host  # a membership loaded before the archive
        table = Table.objects.filter(group=self.group).first()
        writes = {
            "new session": lambda: games.create_session(stale, {"table_id": table.pk, "game_date": datetime.date(2026, 10, 9)}),
            "invite": lambda: groups.create_invite(stale),
            "add player": lambda: groups.add_roster_player(stale, "Late"),
            "rename": lambda: groups.rename_member(stale, stale.pk, "Other"),
        }
        for name, write in writes.items():
            with self.subTest(name), self.assertRaisesMessage(RuleError, "archived"):
                write()

    def test_invite_stops_working_while_archived(self):
        _, token = groups.create_invite(self.host)
        groups.archive_group(self.host)
        with self.assertRaisesMessage(RuleError, "not valid"):
            groups.usable_invite(token)
        with self.assertRaisesMessage(RuleError, "not valid"):
            groups.accept_invite(make_user("newcomer"), token)
        groups.restore_group(reload(self.host))
        self.assertEqual(groups.accept_invite(make_user("later"), token).group, self.group)


class GroupDeleteTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.player = add_player(self.group, "ben")
        self.table = make_table(self.host, preset=make_preset(self.host))
        groups.create_invite(self.host)
        empty = Night("A")  # another group, untouched by the delete
        self.other_group = empty.group

    def test_delete_removes_the_group_and_keeps_accounts_and_the_log(self):
        from games.tests.helpers import make_session
        session = make_session(self.host, table=self.table, state="open")
        games.transition(session.pk, self.host, "cancel", "nobody came")
        group_id, users = self.group.pk, get_user_model().objects.count()
        games.delete_group(self.host, "Friday Game")
        for model in (GameGroup, GroupRakeAccount):
            self.assertFalse(model.objects.filter(pk=group_id).exists() if model is GameGroup else model.objects.filter(group_id=group_id).exists())
        for model in (Member, Table, SettingsPreset, Invite, GameNight, GameSession):
            self.assertFalse(model.objects.filter(group_id=group_id).exists(), model.__name__)
        self.assertEqual(get_user_model().objects.count(), users)
        self.assertTrue(GameGroup.objects.filter(pk=self.other_group.pk).exists())
        event = AuditEvent.objects.get(action="group.deleted")
        self.assertEqual((event.actor, event.group_id, event.data["name"], event.data["sessions"]),
                         (self.host.user, group_id, "Friday Game", 1))
        self.assertTrue(AuditEvent.objects.filter(group_id=group_id, action="group.created").exists())

    def test_wrong_name_is_refused(self):
        for typed in ("", "friday game", "Friday"):
            with self.assertRaisesMessage(RuleError, "Type the group name exactly"):
                games.delete_group(self.host, typed)
        self.assertTrue(GameGroup.objects.filter(pk=self.group.pk).exists())

    def test_archived_empty_group_can_be_deleted(self):
        groups.archive_group(self.host)
        games.delete_group(reload(self.host), " Friday Game ")
        self.assertFalse(GameGroup.objects.filter(pk=self.group.pk).exists())


class GroupArchivePagesTests(TestCase):
    def setUp(self):
        self.night = closed_example()
        self.host, self.group = self.night.host, self.night.group
        self.player = add_player(self.group, "reader")
        self.client.force_login(self.host.user)
        self.urls = [
            reverse("group", args=[self.group.pk]),
            reverse("group", args=[self.group.pk]) + "?view=settings",
            reverse("night", args=[self.night.session.night_id]),
            reverse("session", args=[self.night.session.pk]),
            reverse("session_state", args=[self.night.session.pk]),
            reverse("session_log", args=[self.night.session.pk]),
            reverse("session_create", args=[self.group.pk]),
            reverse("group_archive", args=[self.group.pk]),
        ]

    def test_settings_offers_archive_and_delete_to_hosts_only(self):
        settings = reverse("group", args=[self.group.pk]) + "?view=settings"
        page = self.client.get(settings)
        self.assertContains(page, "Manage this group")
        self.assertContains(page, reverse("group_archive", args=[self.group.pk]))
        self.assertContains(page, reverse("group_delete", args=[self.group.pk]))
        self.client.force_login(self.player.user)
        self.assertNotContains(self.client.get(settings), "Manage this group")
        for name in ("group_archive", "group_delete", "group_restore"):
            self.assertEqual(self.client.post(reverse(name, args=[self.group.pk])).status_code, 403)
        self.assertFalse(GameGroup.objects.get(pk=self.group.pk).is_archived)

    def test_archive_hides_the_group_from_everyone_and_restore_returns_it(self):
        self.assertEqual(len(home_cards(self.host.user)), 1)
        page = self.client.post(reverse("group_archive", args=[self.group.pk]), follow=True)
        self.assertRedirects(page, reverse("home"))
        self.assertContains(page, "is archived")
        self.assertContains(page, "Archived groups (1)")
        self.assertContains(page, "Start your first group")
        for user in (self.host.user, self.player.user):
            self.client.force_login(user)
            self.assertEqual(home_cards(user), [])
            for url in self.urls:
                self.assertEqual(self.client.get(url).status_code, 404, url)
        self.assertEqual(archived_groups(self.player.user), [])
        self.assertNotContains(self.client.get(reverse("home")), "Archived groups")
        self.assertEqual(self.client.post(reverse("group_restore", args=[self.group.pk])).status_code, 403)
        self.client.force_login(self.host.user)
        page = self.client.post(reverse("group_restore", args=[self.group.pk]), follow=True)
        self.assertRedirects(page, reverse("group", args=[self.group.pk]))
        self.assertContains(page, "is restored")
        self.assertEqual(len(home_cards(self.player.user)), 1)
        self.assertEqual(self.client.get(self.urls[2]).status_code, 200)

    def test_outsider_gets_404(self):
        self.client.force_login(make_user("outsider"))
        for name in ("group_archive", "group_delete", "group_restore"):
            self.assertEqual(self.client.post(reverse(name, args=[self.group.pk])).status_code, 404)

    def test_archive_page_names_an_unfinished_set(self):
        live = Night("A", state="running")
        self.client.force_login(live.host.user)
        page = self.client.get(reverse("group_archive", args=[live.group.pk]))
        self.assertContains(page, "Finish or cancel every set first")
        self.assertNotContains(page, "Archive the group")
        page = self.client.post(reverse("group_archive", args=[live.group.pk]))
        self.assertFalse(GameGroup.objects.get(pk=live.group.pk).is_archived)

    def test_delete_page_refuses_a_group_with_money(self):
        page = self.client.get(reverse("group_delete", args=[self.group.pk]))
        self.assertContains(page, "cannot be deleted")
        self.assertNotContains(page, "Delete the group")
        page = self.client.post(reverse("group_delete", args=[self.group.pk]), {"confirm_name": self.group.name})
        self.assertContains(page, "cannot be deleted")
        self.assertTrue(GameGroup.objects.filter(pk=self.group.pk).exists())

    def test_delete_flow_needs_the_typed_name(self):
        group, host = make_group("solo", "Empty Club")
        self.client.force_login(host.user)
        url = reverse("group_delete", args=[group.pk])
        self.assertContains(self.client.get(url), "Type the group name to confirm")
        page = self.client.post(url, {"confirm_name": "wrong"})
        self.assertContains(page, "Type the group name exactly")
        self.assertContains(page, 'value="wrong"')
        page = self.client.post(url, {"confirm_name": "Empty Club"}, follow=True)
        self.assertRedirects(page, reverse("home"))
        self.assertContains(page, "Deleted the group Empty Club")
        self.assertContains(page, "Start your first group")
        self.assertFalse(GameGroup.objects.filter(pk=group.pk).exists())
