"""Hosts archive, restore and delete sessions. Money records are never removed."""

import uuid

from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from audit.models import AuditEvent
from games import services as games
from games.models import GameNight, GameSession
from groups.errors import NotAllowed, RuleError
from groups.tests.helpers import add_player, make_user
from ledger import queries as ledger_queries
from ledger import services as ledger
from ledger.models import BuyIn
from ledger.tests.helpers import Night
from ledger.tests.test_balance import worked_example
from settlement import queries, services
from settlement.models import Transfer
from web.home import home_cards


def closed_example():
    """The worked example, finalized and closed: B and C each owe A."""
    night = worked_example()
    services.finalize(night.session.pk, night.host)
    services.close_night(night.session.night_id, night.host)
    return night


class ArchiveRulesTests(TestCase):
    def setUp(self):
        self.night = closed_example()
        self.host, self.night_id = self.night.host, self.night.session.night_id

    def game_night(self):
        return GameNight.objects.get(pk=self.night_id)

    def test_archive_and_restore_keep_every_record(self):
        before = (BuyIn.objects.count(), Transfer.objects.count())
        version = self.night.refresh().version
        archived = games.archive_night(self.night_id, self.host)
        self.assertTrue(archived.is_archived)
        self.assertEqual(archived.archived_by, self.host.user)
        self.assertEqual(self.night.refresh().version, version + 1)  # open set pages reload
        self.assertEqual((BuyIn.objects.count(), Transfer.objects.count()), before)
        restored = games.restore_night(self.night_id, self.host)
        self.assertFalse(restored.is_archived)
        self.assertIsNone(restored.archived_by)
        self.assertTrue(restored.is_closed)
        actions = list(AuditEvent.objects.filter(action__startswith="night.").values_list("action", flat=True))
        self.assertEqual(actions[-2:], ["night.archived", "night.restored"])

    def test_repeat_is_a_no_op(self):
        games.archive_night(self.night_id, self.host)
        first = self.game_night().archived_at
        games.archive_night(self.night_id, self.host)
        self.assertEqual(self.game_night().archived_at, first)
        self.assertEqual(AuditEvent.objects.filter(action="night.archived").count(), 1)
        games.restore_night(self.night_id, self.host)
        games.restore_night(self.night_id, self.host)
        self.assertEqual(AuditEvent.objects.filter(action="night.restored").count(), 1)

    def test_player_cannot_archive_restore_or_delete(self):
        player = add_player(self.night.group, "reader")
        for action in (games.archive_night, games.restore_night, games.delete_night):
            with self.assertRaises(NotAllowed):
                action(self.night_id, player)
        self.assertFalse(self.game_night().is_archived)

    def test_another_groups_host_cannot_reach_it(self):
        other = Night("X").host
        for action in (games.archive_night, games.restore_night, games.delete_night):
            with self.assertRaisesMessage(RuleError, "not in this group"):
                action(self.night_id, other)

    def test_unfinished_set_blocks_archive_and_delete(self):
        for state in ("open", "running", "reconciliation"):
            live = Night("A", state=state)
            for action in (games.archive_night, games.delete_night):
                with self.assertRaisesMessage(RuleError, "Finish or cancel every set"):
                    action(live.session.night_id, live.host)

    def test_session_with_money_cannot_be_deleted(self):
        with self.assertRaisesMessage(RuleError, "cannot be deleted"):
            games.delete_night(self.night_id, self.host)
        games.archive_night(self.night_id, self.host)
        with self.assertRaisesMessage(RuleError, "cannot be deleted"):
            games.delete_night(self.night_id, self.host)
        self.assertTrue(GameNight.objects.filter(pk=self.night_id).exists())

    def test_reversed_buy_in_still_blocks_delete(self):
        night = Night("A")
        buy_in = night.buy("A", 1000)
        ledger.reverse_buy_in(night.session.pk, night.host, buy_in.pk, "typo")
        games.transition(night.session.pk, night.host, "cancel", "never played")
        self.assertTrue(games.night_has_records(night.session.night))
        with self.assertRaisesMessage(RuleError, "cannot be deleted"):
            games.delete_night(night.session.night_id, night.host)
        games.archive_night(night.session.night_id, night.host)  # archive stays possible

    def test_database_refuses_to_delete_a_session_with_money(self):
        with self.assertRaises(ProtectedError):
            GameSession.objects.filter(night_id=self.night_id).delete()


class DeleteTests(TestCase):
    def setUp(self):
        self.night = Night("A", "B")
        self.host, self.night_id, self.set_id = self.night.host, self.night.session.night_id, self.night.session.pk
        games.transition(self.set_id, self.host, "cancel", "nobody came")

    def test_delete_removes_the_session_and_keeps_the_log(self):
        self.assertFalse(games.night_has_records(self.night.session.night))
        events = AuditEvent.objects.filter(session_id=self.set_id).count()
        games.delete_night(self.night_id, self.host)
        self.assertFalse(GameNight.objects.filter(pk=self.night_id).exists())
        self.assertFalse(GameSession.objects.filter(pk=self.set_id).exists())
        self.assertEqual(AuditEvent.objects.filter(session_id=self.set_id).count(), events + 1)
        event = AuditEvent.objects.get(action="night.deleted")
        self.assertEqual((event.actor, event.data["sets"], event.target_id), (self.host.user, 1, self.night_id))
        self.assertEqual(self.night.group.members.count(), 3)  # the roster stays

    def test_archived_empty_session_can_be_deleted(self):
        games.archive_night(self.night_id, self.host)
        games.delete_night(self.night_id, self.host)
        self.assertFalse(GameNight.objects.filter(pk=self.night_id).exists())

    def test_second_delete_is_refused(self):
        games.delete_night(self.night_id, self.host)
        with self.assertRaisesMessage(RuleError, "not in this group"):
            games.delete_night(self.night_id, self.host)


class ArchivedSessionTakesNoWriteTests(TestCase):
    def setUp(self):
        self.night = closed_example()
        self.host, self.night_id, self.set_id = self.night.host, self.night.session.night_id, self.night.session.pk
        self.transfer = Transfer.objects.order_by("position").first()
        self.buy_in = BuyIn.objects.first()
        games.archive_night(self.night_id, self.host)

    def test_every_write_service_refuses(self):
        player = self.night.players["A"].pk
        writes = {
            "buy-in": lambda: ledger.record_buy_in(self.set_id, self.host, player, 100000, uuid.uuid4()),
            "reverse buy-in": lambda: ledger.reverse_buy_in(self.set_id, self.host, self.buy_in.pk, "x"),
            "cash-out": lambda: ledger.record_cash_out(self.set_id, self.host, player, 100000, uuid.uuid4()),
            "count": lambda: ledger.confirm_count(self.set_id, self.host, player, 100000, uuid.uuid4()),
            "transition": lambda: games.transition(self.set_id, self.host, "resume"),
            "settings": lambda: games.update_settings(self.set_id, self.host, {}),
            "add player": lambda: games.add_participant(self.set_id, self.host, self.host.pk),
            "next set": lambda: games.start_next_set(self.night_id, self.host),
            "finalize": lambda: services.finalize(self.set_id, self.host),
            "close": lambda: services.close_night(self.night_id, self.host),
            "mark paid": lambda: services.mark_paid(self.night_id, self.host, self.transfer.pk, uuid.uuid4()),
            "mark unpaid": lambda: services.mark_unpaid(self.night_id, self.host, self.transfer.pk),
        }
        for name, write in writes.items():
            with self.subTest(name), self.assertRaisesMessage(RuleError, "archived"):
                write()

    def test_restore_reopens_writes(self):
        games.restore_night(self.night_id, self.host)
        services.mark_paid(self.night_id, self.host, self.transfer.pk, uuid.uuid4())


class ArchivedSessionLeavesTheTotalsTests(TestCase):
    def setUp(self):
        self.night = closed_example()
        self.host, self.group, self.night_id = self.night.host, self.night.group, self.night.session.night_id
        self.members = [p.member_id for p in self.night.players.values()]

    def figures(self):
        return {
            "stats": [(s.member.display_name, s.net, s.sessions) for s in queries.group_stats(self.group, "php")],
            "periods": queries.stat_periods(self.group),
            "records": {m: {u: (s.net, s.sessions) for u, s in units.items()} for m, units in queries.member_records(self.members).items()},
            "dues": [(t.payer_id, t.payee_id, t.amount) for t in queries.unpaid_transfers(self.members)],
            "rake": ledger_queries.group_rake(self.group)[0],
        }

    def test_archive_empties_and_restore_returns_them(self):
        before = self.figures()
        self.assertTrue(before["stats"] and before["dues"] and before["records"])
        games.archive_night(self.night_id, self.host)
        self.assertEqual(self.figures(), {"stats": [], "periods": {}, "records": {}, "dues": [], "rake": {"php": 0, "chips": 0}})
        games.restore_night(self.night_id, self.host)
        self.assertEqual(self.figures(), before)

    def test_rake_total_excludes_an_archived_session(self):
        from ledger.tests.test_rake import configure
        night = Night("A", state="open")
        configure(night, rake_mode="percent", rake_basis_points=500)
        night.go("running")
        night.buy("A", 1000)
        self.assertEqual(ledger_queries.group_rake(night.group)[0]["php"], 5000)
        games.transition(night.session.pk, night.host, "end")
        night.cash("A", 950)
        services.finalize(night.session.pk, night.host)
        games.archive_night(night.session.night_id, night.host)
        self.assertEqual(ledger_queries.group_rake(night.group), ({"php": 0, "chips": 0}, []))

    def test_home_card_drops_the_archived_session(self):
        card = home_cards(self.host.user)[0]
        self.assertEqual(card.last_night.pk, self.night_id)
        games.archive_night(self.night_id, self.host)
        card = home_cards(self.host.user)[0]
        self.assertIsNone(card.last_night)
        self.assertEqual((card.dues, card.records), ([], []))


class ArchivePagesTests(TestCase):
    def setUp(self):
        self.night = closed_example()
        self.host, self.group, self.night_id = self.night.host, self.night.group, self.night.session.night_id
        self.client.force_login(self.host.user)
        self.night_url = reverse("night", args=[self.night_id])
        self.group_url = reverse("group", args=[self.group.pk])

    def test_host_sees_manage_section_with_archive_and_no_delete(self):
        page = self.client.get(self.night_url)
        self.assertContains(page, "Manage this session")
        self.assertContains(page, reverse("night_archive", args=[self.night_id]))
        self.assertNotContains(page, reverse("night_delete", args=[self.night_id]))
        self.assertContains(page, "cannot be deleted")

    def test_player_sees_no_manage_section_and_cannot_use_the_urls(self):
        player = add_player(self.group, "reader")
        self.client.force_login(player.user)
        self.assertNotContains(self.client.get(self.night_url), "Manage this session")
        for name in ("night_archive", "night_delete"):
            self.assertEqual(self.client.get(reverse(name, args=[self.night_id])).status_code, 403)
            self.assertEqual(self.client.post(reverse(name, args=[self.night_id])).status_code, 403)
        self.assertEqual(self.client.post(reverse("night_restore", args=[self.night_id])).status_code, 403)
        self.assertFalse(GameNight.objects.get(pk=self.night_id).is_archived)

    def test_outsider_gets_404(self):
        self.client.force_login(make_user("outsider"))
        for name in ("night_archive", "night_delete", "night_restore"):
            self.assertEqual(self.client.post(reverse(name, args=[self.night_id])).status_code, 404)

    def test_confirmation_lists_unpaid_transfers(self):
        page = self.client.get(reverse("night_archive", args=[self.night_id]))
        self.assertContains(page, "2 transfers not marked paid")
        self.assertContains(page, "Archive with unpaid transfers")
        self.assertContains(page, "₱300")
        self.assertFalse(GameNight.objects.get(pk=self.night_id).is_archived)  # GET changes nothing

    def test_archive_flow_hides_and_restore_returns(self):
        self.assertContains(self.client.get(self.group_url), "Past sessions")
        page = self.client.post(reverse("night_archive", args=[self.night_id]), follow=True)
        self.assertRedirects(page, self.group_url)
        self.assertContains(page, "Session archived")
        self.assertNotContains(page, "Past sessions")
        self.assertContains(page, "Archived sessions (1)")
        # The page stays readable, with one action: restore.
        page = self.client.get(self.night_url)
        self.assertContains(page, "This session is archived")
        self.assertContains(page, "Restore session")
        self.assertNotContains(page, "Mark paid")
        self.assertNotContains(page, reverse("night_archive", args=[self.night_id]))
        set_page = self.client.get(reverse("session", args=[self.night.session.pk]))
        self.assertContains(set_page, "This session is archived")
        page = self.client.post(reverse("night_restore", args=[self.night_id]), follow=True)
        self.assertContains(page, "Session restored")
        self.assertContains(page, "Mark paid")
        self.assertContains(self.client.get(self.group_url), "Past sessions")

    def test_player_does_not_see_the_archived_list(self):
        games.archive_night(self.night_id, self.host)
        player = add_player(self.group, "reader")
        self.client.force_login(player.user)
        page = self.client.get(self.group_url)
        self.assertNotContains(page, "Archived sessions")
        self.assertNotContains(self.client.get(self.night_url), "Restore session")

    def test_refused_write_on_archived_session_shows_the_reason(self):
        games.archive_night(self.night_id, self.host)
        transfer = Transfer.objects.first()
        page = self.client.post(reverse("transfer_paid", args=[self.night_id, transfer.pk]), follow=True)
        self.assertContains(page, "This session is archived")

    def test_delete_flow_for_an_empty_session(self):
        empty = Night("A")
        games.transition(empty.session.pk, empty.host, "cancel", "nobody came")
        self.client.force_login(empty.host.user)
        night_id = empty.session.night_id
        page = self.client.get(reverse("night", args=[night_id]))
        self.assertContains(page, reverse("night_delete", args=[night_id]))
        page = self.client.get(reverse("night_delete", args=[night_id]))
        self.assertContains(page, "Delete the session")
        page = self.client.post(reverse("night_delete", args=[night_id]), follow=True)
        self.assertRedirects(page, reverse("group", args=[empty.group.pk]))
        self.assertContains(page, "Deleted the session")
        self.assertEqual(self.client.get(reverse("night", args=[night_id])).status_code, 404)
        self.assertEqual(self.client.get(reverse("session_state", args=[empty.session.pk])).status_code, 404)

    def test_posting_delete_for_a_session_with_money_is_refused(self):
        page = self.client.post(reverse("night_delete", args=[self.night_id]), follow=True)
        self.assertContains(page, "cannot be deleted")
        self.assertTrue(GameNight.objects.filter(pk=self.night_id).exists())
        self.assertContains(self.client.get(reverse("night_delete", args=[self.night_id])), "Archive instead")
