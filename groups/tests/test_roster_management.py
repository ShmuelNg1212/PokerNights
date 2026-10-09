from django.test import TestCase, override_settings

from audit.models import AuditEvent
from groups import services
from groups.errors import NotAllowed, RuleError
from groups.models import Member

from .helpers import add_player, make_group


class RemoveAndRestoreTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.ben = add_player(self.group, "ben")
        self.guest = services.add_roster_player(self.host, "Guest")

    def events(self, action):
        return AuditEvent.objects.filter(action=action, group_id=self.group.pk)

    def test_restore_keeps_the_same_row_for_a_player_without_a_login(self):
        services.remove_member(self.host, self.guest.pk)
        member, old = services.restore_member(self.host, self.guest.pk)
        self.assertEqual((member.pk, member.status, old), (self.guest.pk, "active", "Guest"))
        self.assertEqual(Member.objects.filter(group=self.group, display_name="Guest").count(), 1)
        self.assertEqual(self.events("member.restored").count(), 1)

    def test_a_former_host_comes_back_as_a_player(self):
        services.set_role(self.host, self.ben.pk, "host")
        services.remove_member(self.host, self.ben.pk)
        member, _ = services.restore_member(self.host, self.ben.pk)
        self.assertEqual((member.status, member.role, member.user_id), ("active", "player", self.ben.user_id))

    def test_a_taken_name_comes_back_under_the_next_free_one(self):
        services.remove_member(self.host, self.ben.pk)
        Member.objects.create(group=self.group, display_name="Ben")  # another Ben arrived meanwhile
        member, old = services.restore_member(self.host, self.ben.pk)
        self.assertEqual((old, member.display_name), ("ben", "ben (2)"))

    def test_restore_is_for_hosts_of_this_group_and_removed_members(self):
        services.remove_member(self.host, self.guest.pk)
        with self.assertRaises(NotAllowed):
            services.restore_member(self.ben, self.guest.pk)
        _, other_host = make_group("omar", "Other")
        with self.assertRaisesMessage(RuleError, "not in this group"):
            services.restore_member(other_host, self.guest.pk)
        with self.assertRaisesMessage(RuleError, "not in this group"):
            services.restore_member(self.host, 999999)

    def test_repeated_restore_and_remove_change_nothing(self):
        services.remove_member(self.host, self.guest.pk)
        services.remove_member(self.host, self.guest.pk)
        self.assertEqual(self.events("member.removed").count(), 1)
        services.restore_member(self.host, self.guest.pk)
        member, old = services.restore_member(self.host, self.guest.pk)
        self.assertEqual((member.status, old), ("active", "Guest"))
        self.assertEqual(self.events("member.restored").count(), 1)

    def test_a_guard_refuses_removal_and_the_page_can_ask_first(self):
        def guard(member):
            if member.pk == self.guest.pk:
                raise RuleError("Guest is at the table.")

        services.REMOVE_GUARDS.append(guard)
        self.addCleanup(services.REMOVE_GUARDS.remove, guard)
        self.assertEqual(services.removal_refusal(self.host, self.guest.pk), "Guest is at the table.")
        self.assertIsNone(services.removal_refusal(self.host, self.ben.pk))
        with self.assertRaisesMessage(RuleError, "at the table"):
            services.remove_member(self.host, self.guest.pk)
        self.assertEqual(Member.objects.get(pk=self.guest.pk).status, "active")

    def test_the_only_host_is_refused_with_what_to_do(self):
        reason = services.removal_refusal(self.host, self.host.pk)
        self.assertEqual(reason, "A group needs at least one host. Make someone else a host first.")
        with self.assertRaisesMessage(RuleError, "at least one host"):
            services.remove_member(self.host, self.host.pk)

    def test_a_removed_name_is_not_added_as_a_second_player(self):
        services.remove_member(self.host, self.guest.pk)
        with self.assertRaisesMessage(RuleError, "Removed from this group: guest. Bring them back"):
            services.add_roster_player(self.host, "guest")
        self.assertEqual(Member.objects.filter(group=self.group).count(), 3)

    @override_settings(ROSTER_TOOLS=False)
    def test_switch_off_refuses_restore_and_keeps_the_old_re_add(self):
        services.remove_member(self.host, self.guest.pk)
        with self.assertRaisesMessage(RuleError, "turned off"):
            services.restore_member(self.host, self.guest.pk)
        self.assertEqual(services.add_roster_player(self.host, "Guest").display_name, "Guest")


class NamesAndDetailsTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.ben = add_player(self.group, "ben")

    def renamed(self):
        return AuditEvent.objects.filter(action="member.renamed", group_id=self.group.pk)

    def test_a_host_and_a_player_change_their_own_name(self):
        self.assertEqual(services.rename_self(self.ben, "  Benjie  ").display_name, "Benjie")
        self.assertEqual(services.rename_self(self.host, "Hana R").display_name, "Hana R")
        self.assertEqual(self.renamed().count(), 2)
        self.assertIn("ben", self.renamed().order_by("pk").first().summary)

    def test_own_name_follows_the_name_rule(self):
        with self.assertRaisesMessage(RuleError, "already in this group"):
            services.rename_self(self.ben, self.host.display_name.upper())
        with self.assertRaisesMessage(RuleError, "required"):
            services.rename_self(self.ben, "   ")
        self.assertEqual(services.rename_self(self.ben, "BEN").display_name, "BEN")  # own name in other capitals

    def test_edit_writes_only_what_changed(self):
        guest = services.add_roster_player(self.host, "Guest")
        services.edit_member(self.host, guest.pk, "Guest", "0917 555")
        guest.refresh_from_db()
        self.assertEqual((guest.display_name, guest.contact), ("Guest", "0917 555"))
        event = AuditEvent.objects.get(action="member.contact_changed")
        self.assertNotIn("0917", event.summary)
        services.edit_member(self.host, guest.pk, "Guest One", "0917 555")
        self.assertEqual(self.renamed().count(), 1)
        self.assertEqual(AuditEvent.objects.filter(action="member.contact_changed").count(), 1)
        services.edit_member(self.host, guest.pk, "Guest One", "0917 555")  # nothing changed
        self.assertEqual(self.renamed().count(), 1)
        services.edit_member(self.host, guest.pk, "Guest Two", "")
        guest.refresh_from_db()
        self.assertEqual((guest.display_name, guest.contact), ("Guest Two", ""))

    def test_edit_is_for_hosts_and_checks_clashes_and_length(self):
        guest = services.add_roster_player(self.host, "Guest")
        with self.assertRaises(NotAllowed):
            services.edit_member(self.ben, guest.pk, "X", "")
        with self.assertRaisesMessage(RuleError, "already in this group"):
            services.edit_member(self.host, guest.pk, "BEN", "")
        with self.assertRaisesMessage(RuleError, "120"):
            services.edit_member(self.host, guest.pk, "Guest", "x" * 121)

    @override_settings(ROSTER_TOOLS=False)
    def test_switch_off(self):
        guest = services.add_roster_player(self.host, "Guest")
        with self.assertRaisesMessage(RuleError, "turned off"):
            services.rename_self(self.ben, "Benjie")
        with self.assertRaisesMessage(RuleError, "turned off"):
            services.edit_member(self.host, guest.pk, "Guest", "0917")
        self.assertEqual(services.edit_member(self.host, guest.pk, "Guest One", "").display_name, "Guest One")


class AddSeveralTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.ben = add_player(self.group, "Ben")

    def names(self):
        return sorted(Member.objects.filter(group=self.group, status="active").values_list("display_name", flat=True))

    def test_everyone_is_added_and_audited(self):
        added = services.add_roster_players(self.host, ["  Ana  ", "", "Carlo   Jr", "Dani"])
        self.assertEqual([m.display_name for m in added], ["Ana", "Carlo Jr", "Dani"])
        self.assertTrue(all(not m.has_login and m.role == "player" for m in added))
        self.assertEqual(AuditEvent.objects.filter(action="member.added", group_id=self.group.pk).count(), 3)

    def test_every_problem_is_named_and_nobody_is_added(self):
        carlo = services.add_roster_player(self.host, "Carlo")
        services.remove_member(self.host, carlo.pk)
        before = self.names()
        with self.assertRaises(RuleError) as caught:
            services.add_roster_players(self.host, ["Ana", "ben", "ana", "CARLO", "x" * 61, "Eli"])
        message = str(caught.exception)
        self.assertIn("Already in this group: ben.", message)
        self.assertIn("Typed twice: ana.", message)
        self.assertIn("Removed from this group: CARLO. Bring them back from Removed players, or use a different name.", message)
        self.assertIn("Too long (60 characters at most): " + "x" * 20 + "…", message)
        self.assertEqual(self.names(), before)

    def test_limits_and_roles(self):
        with self.assertRaisesMessage(RuleError, "Type at least one name."):
            services.add_roster_players(self.host, ["", "  "])
        with self.assertRaisesMessage(RuleError, "Add 30 players at most at a time."):
            services.add_roster_players(self.host, [f"P{n}" for n in range(31)])
        self.assertEqual(len(services.add_roster_players(self.host, [f"P{n}" for n in range(30)])), 30)
        with self.assertRaises(NotAllowed):
            services.add_roster_players(self.ben, ["Ana"])

    @override_settings(ROSTER_TOOLS=False)
    def test_switch_off_takes_one_name(self):
        with self.assertRaisesMessage(RuleError, "turned off"):
            services.add_roster_players(self.host, ["Ana", "Dani"])
        self.assertEqual(len(services.add_roster_players(self.host, ["Ana"])), 1)
