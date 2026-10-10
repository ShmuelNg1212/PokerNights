"""Players record their own rebuy and enter their own final count. The host still confirms every count."""

import uuid

from django.db import connection
from django.test import TestCase, TransactionTestCase, override_settings, skipUnlessDBFeature
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from audit.models import AuditEvent
from games import services as games
from groups.errors import NotAllowed, RuleError
from groups.tests.helpers import make_group, make_user
from ledger import queries, services
from ledger.models import BuyIn, CashOut, CountEntry, FinalCount
from ledger.tests.helpers import Night
from web.tests.test_concurrency import kinds, race


def night_with_logins(state="running", **stakes):
    """Host hana; maria and ben have logins; Lolo is a roster player. maria, ben and Lolo have one buy-in each."""
    night = Night("Lolo", state="open", **stakes)
    night.maria = night.add_login_player("maria")
    night.ben = night.add_login_player("ben")
    for name in ("Lolo", "maria", "ben"):
        night.buy(name, 1000)
    night.go(state)
    return night


class OwnRebuyTests(TestCase):
    def setUp(self):
        self.night = night_with_logins()
        self.sid = self.night.session.pk

    def rebuy(self, actor=None, name="maria", pesos=1000, **kwargs):
        actor = actor or self.night.maria
        return services.record_buy_in(self.sid, actor, self.night.players[name].pk, pesos * 100, uuid.uuid4(), **kwargs)

    def test_player_records_their_own_rebuy(self):
        before = self.night.refresh().version
        buy_in = self.rebuy()
        self.assertEqual((buy_in.participant, buy_in.amount, buy_in.recorded_by), (self.night.players["maria"], 100000, self.night.maria.user))
        self.assertEqual(self.night.refresh().version, before + 1)
        line = self.night.line("maria")
        self.assertEqual((line.buy_in_count, line.buy_in_total), (2, 200000))
        event = AuditEvent.objects.filter(action="buy_in.recorded").order_by("-id").first()
        self.assertEqual((event.actor, event.session_id, event.summary), (self.night.maria.user, self.sid, "maria bought in for ₱1,000"))

    def test_own_rebuy_needs_no_participant_id_and_takes_limits_and_rake(self):
        self.assertEqual(services.record_buy_in(self.sid, self.night.maria, None, 100000, uuid.uuid4()).participant, self.night.players["maria"])
        with self.assertRaisesMessage(RuleError, "A buy-in must be between"):
            self.rebuy(pesos=1)
        raked = Night("A", state="open", rake_mode="percent", rake_basis_points=500)
        zed = raked.add_login_player("zed")
        raked.buy("zed", 1000)
        buy_in = services.record_buy_in(raked.session.pk, zed, None, 100000, uuid.uuid4())
        self.assertEqual((buy_in.rake_amount, buy_in.playable_amount), (5000, 95000))

    def test_only_for_yourself(self):
        for name in ("ben", "Lolo"):
            with self.assertRaises(NotAllowed):
                self.rebuy(name=name)
        with self.assertRaises(NotAllowed):
            services.record_buy_in(self.sid, self.night.maria, 999999, 100000, uuid.uuid4())
        self.assertEqual(BuyIn.objects.count(), 3)

    def test_refusals(self):
        late = self.night.add_login_player("cy")
        with self.assertRaisesMessage(RuleError, "The host records your first buy-in."):
            self.rebuy(late, "cy")
        watcher = self.night.group.members.model.objects.create(group=self.night.group, user=make_user("dee"), display_name="dee")
        with self.assertRaisesMessage(RuleError, "You are not in this set."):
            services.record_buy_in(self.sid, watcher, None, 100000, uuid.uuid4())
        self.night.cash("ben", 500, left=True)
        with self.assertRaises(RuleError):
            self.rebuy(self.night.ben, "ben")
        games.set_left(self.sid, self.night.host, self.night.players["maria"].pk)
        with self.assertRaisesMessage(RuleError, "maria is not at the table."):
            self.rebuy()
        self.assertEqual(BuyIn.objects.count(), 3)

    def test_a_partial_cash_out_keeps_the_rebuy_and_a_final_one_ends_it(self):
        self.night.cash("maria", 500)  # takes some off the table and plays on
        self.assertEqual(CashOut.objects.get().kind, CashOut.Kind.PARTIAL)
        self.assertEqual(self.rebuy().amount, 100000)
        # Back at the table after a final cash-out: the host records the rebuy, because it reclassifies that cash-out.
        CashOut.objects.update(kind=CashOut.Kind.FINAL)
        with self.assertRaisesMessage(RuleError, "You are cashed out. Ask the host to record this rebuy."):
            self.rebuy()
        self.assertFalse(services.can_rebuy_own(self.night.session, self.night.line("maria")))

    def test_not_after_play_has_ended(self):
        self.night.go("reconciliation")
        with self.assertRaisesMessage(RuleError, "Buy-ins can be recorded only while the set is open or running."):
            self.rebuy()

    @override_settings(PLAYER_ENTRIES=False)
    def test_switch_off_makes_it_host_only(self):
        with self.assertRaises(NotAllowed):
            self.rebuy()
        self.night.buy("maria", 1000)
        self.assertFalse(services.can_rebuy_own(self.night.session, self.night.line("maria")))

    def test_a_stale_page_records_nothing_and_names_the_other_record(self):
        self.rebuy(seen_count=1)
        for actor in (self.night.host, self.night.maria):
            with self.assertRaisesRegex(RuleError, r"^maria already has a new rebuy \(₱1,000, recorded by maria at \d\d:\d\d\)\. Nothing was added\. Check, then try again if this is another one\.$"):
                self.rebuy(actor, seen_count=1)
        self.assertEqual(self.night.line("maria").buy_in_count, 2)
        self.rebuy(self.night.host, seen_count=2)
        self.assertEqual(self.night.line("maria").buy_in_count, 3)

    def test_a_reversal_also_makes_the_page_stale(self):
        extra = self.rebuy()
        services.reverse_buy_in(self.sid, self.night.host, extra.pk, "typo")
        with self.assertRaisesMessage(RuleError, "maria's buy-ins changed since this page was drawn."):
            self.rebuy(seen_count=2)

    def test_a_repeated_request_returns_the_same_row_even_when_stale(self):
        request_id = uuid.uuid4()
        first = services.record_buy_in(self.sid, self.night.maria, None, 100000, request_id, seen_count=1)
        again = services.record_buy_in(self.sid, self.night.maria, None, 100000, request_id, seen_count=1)
        self.assertEqual(first, again)
        self.assertEqual(self.night.line("maria").buy_in_count, 2)

    def test_first_buy_in_is_named_as_one(self):
        night = Night("A", state="open")
        night.buy("A", 1000)
        with self.assertRaisesRegex(RuleError, "A already has a new buy-in"):
            services.record_buy_in(night.session.pk, night.host, night.players["A"].pk, 100000, uuid.uuid4(), seen_count=0)


class EnterCountTests(TestCase):
    def setUp(self):
        self.night = night_with_logins("reconciliation")
        self.sid = self.night.session.pk

    def enter(self, pesos, actor=None, request_id=None):
        return services.enter_count(self.sid, actor or self.night.maria, pesos * 100 if pesos is not None else None, request_id or uuid.uuid4())

    def confirm(self, amounts=None, entries=None):
        amounts = {self.night.players[name].pk: pesos * 100 for name, pesos in (amounts or {}).items()}
        entries = {self.night.players[name].pk: entry.pk for name, entry in (entries or {}).items()}
        return services.confirm_counts(self.sid, self.night.host, amounts, uuid.uuid4(), entries=entries)

    def test_player_enters_and_changes_their_count(self):
        before = self.night.refresh().version
        first = self.enter(1450)
        self.assertEqual((first.participant, first.amount, first.version, first.entered_by), (self.night.players["maria"], 145000, 1, self.night.maria.user))
        second = self.enter(1500)
        first.refresh_from_db()
        self.assertEqual((first.is_current, second.is_current, second.version), (False, True, 2))
        self.assertEqual(self.night.refresh().version, before + 2)
        events = list(AuditEvent.objects.filter(action="count.entered").values_list("summary", flat=True))
        self.assertEqual(events, ["maria entered their final count: ₱1,450", "maria entered their final count: ₱1,500 (version 2)"])
        self.assertEqual(self.enter(0).amount, 0)

    def test_an_entered_count_is_not_a_count(self):
        self.enter(1450)
        line = self.night.line("maria")
        self.assertEqual((line.status, line.status_label, line.entered.amount, line.count), ("awaiting", "Awaiting count", 145000, None))
        summary = queries.summary(self.night.session)
        self.assertEqual(len(summary.awaiting_lines), 3)
        total = queries.count_total(summary)
        self.assertEqual((total.remaining, total.missing), (0, 3))
        self.assertFalse(FinalCount.objects.exists())
        self.assertFalse(CashOut.objects.exists())
        with self.assertRaisesMessage(RuleError, "No player has a confirmed count yet."):
            services.cash_out_counted(self.sid, self.night.host, [], uuid.uuid4())

    def test_refusals(self):
        with self.assertRaisesMessage(RuleError, "Enter your count, 0 or more."):
            self.enter(None)
        with self.assertRaisesMessage(RuleError, "Enter your count, 0 or more."):
            self.enter(-1)
        late = Night("A", state="open")
        cy = late.add_login_player("cy")
        late.buy("A", 1000)
        late.go("running")
        with self.assertRaisesMessage(RuleError, "You can enter your count after the host ends play."):
            services.enter_count(late.session.pk, cy, 100, uuid.uuid4())
        late.go("reconciliation")
        with self.assertRaisesMessage(RuleError, "You have no buy-in, so there is nothing to count."):
            services.enter_count(late.session.pk, cy, 100, uuid.uuid4())
        with self.assertRaisesMessage(RuleError, "You are not in this set."):
            services.enter_count(late.session.pk, late.host, 100, uuid.uuid4())
        self.night.cash("ben", 500)
        with self.assertRaisesMessage(RuleError, "You are already cashed out."):
            self.enter(500, self.night.ben)
        self.assertFalse(CountEntry.objects.exists())

    def test_a_repeated_request_writes_once(self):
        request_id = uuid.uuid4()
        self.assertEqual(self.enter(1450, request_id=request_id), self.enter(1450, request_id=request_id))
        self.assertEqual(CountEntry.objects.count(), 1)

    @override_settings(PLAYER_ENTRIES=False)
    def test_switch_off(self):
        with self.assertRaises(NotAllowed):
            self.enter(1450)

    def test_host_confirms_what_the_player_entered(self):
        entry = self.enter(1450)
        written = self.confirm(entries={"maria": entry})
        self.assertEqual([(c.amount, c.entry, c.confirmed_by) for c in written], [(145000, entry, self.night.host.user)])
        line = self.night.line("maria")
        self.assertEqual((line.status, line.count.amount, line.entered), ("ready", 145000, None))
        self.assertIn("as the player entered it", AuditEvent.objects.filter(action="count.confirmed").get().summary)
        with self.assertRaisesMessage(RuleError, "The host has confirmed your count. Ask the host to change it."):
            self.enter(1500)

    def test_typed_and_entered_together_and_typed_wins(self):
        maria, ben = self.enter(1450), self.enter(900, self.night.ben)
        written = self.confirm(amounts={"Lolo": 650, "ben": 950}, entries={"maria": maria, "ben": ben})
        by_name = {c.participant.member.display_name: c for c in written}
        self.assertEqual({name: c.amount for name, c in by_name.items()}, {"Lolo": 65000, "ben": 95000, "maria": 145000})
        self.assertEqual((by_name["maria"].entry, by_name["ben"].entry, by_name["Lolo"].entry), (maria, None, None))
        self.assertEqual(self.night.line("ben").entry.amount, 90000)  # the statement stays in the record

    def test_a_changed_entry_saves_nothing(self):
        old = self.enter(1450)
        self.enter(1500)
        with self.assertRaisesMessage(RuleError, "maria changed their count to ₱1,500."):
            self.confirm(amounts={"Lolo": 650}, entries={"maria": old})
        self.assertFalse(FinalCount.objects.exists())

    def test_an_entry_from_another_set_or_made_up_saves_nothing(self):
        self.enter(1450)
        with self.assertRaises(RuleError):
            services.confirm_counts(self.sid, self.night.host, {}, uuid.uuid4(), entries={self.night.players["maria"].pk: 999999})
        with self.assertRaisesMessage(RuleError, "ben's entered count is no longer there."):
            services.confirm_counts(self.sid, self.night.host, {}, uuid.uuid4(), entries={self.night.players["ben"].pk: 1})
        self.assertFalse(FinalCount.objects.exists())

    def test_an_entry_never_replaces_a_count_already_in_force(self):
        entry = self.enter(1450)
        self.confirm(amounts={"maria": 1400})
        self.assertEqual(self.confirm(amounts={"Lolo": 650}, entries={"maria": entry})[0].participant, self.night.players["Lolo"])
        self.assertEqual(self.night.line("maria").count.amount, 140000)

    def test_only_a_host_confirms(self):
        entry = self.enter(1450)
        with self.assertRaises(NotAllowed):
            services.confirm_counts(self.sid, self.night.maria, {}, uuid.uuid4(), entries={self.night.players["maria"].pk: entry.pk})

    def test_clear_and_resume_let_the_player_enter_again(self):
        entry = self.enter(1450)
        self.confirm(entries={"maria": entry})
        services.clear_count(self.sid, self.night.host, self.night.players["maria"].pk)
        line = self.night.line("maria")
        self.assertEqual((line.status, line.entry), ("awaiting", None))
        self.enter(1400)
        self.enter(700, self.night.ben)
        games.transition(self.sid, self.night.host, "resume")
        self.assertFalse(CountEntry.objects.filter(is_current=True).exists())
        games.transition(self.sid, self.night.host, "end")
        self.assertEqual(self.enter(1300).version, 3)

    def test_results_come_from_confirmed_counts_only(self):
        self.enter(5000)  # a wild statement the host does not accept
        self.confirm(amounts={"maria": 1450, "ben": 900, "Lolo": 650})
        ready = [line.participant.final_counts.get(is_current=True).pk for line in queries.summary(self.night.session).ready_lines]
        services.cash_out_counted(self.sid, self.night.host, ready, uuid.uuid4())
        balance = queries.balance(self.night.session)
        self.assertTrue(balance.ok)
        self.assertEqual(self.night.line("maria").cashed_out, 145000)

    @override_settings(PLAYER_ENTRIES=False)
    def test_switch_off_ignores_entries_already_sent(self):
        with override_settings(PLAYER_ENTRIES=True):
            entry = self.enter(1450)
        self.assertIsNone(self.night.line("maria").entered)
        with self.assertRaisesMessage(RuleError, "Type at least one final count."):
            self.confirm(entries={"maria": entry})

    def test_summary_reads_entries_in_one_query_whatever_the_number(self):
        def count():
            with CaptureQueriesContext(connection) as found:
                queries.summary(self.night.session)
            return len(found)
        before = count()
        self.enter(1450)
        self.enter(900, self.night.ben)
        self.assertEqual(count(), before)


class PlayerEntryViewTests(TestCase):
    def setUp(self):
        self.night = night_with_logins()
        self.sid = self.night.session.pk
        self.page = reverse("session", args=[self.sid])
        self.buy_url = reverse("buy_in_add", args=[self.sid])
        self.enter_url = reverse("count_enter", args=[self.sid])
        self.confirm_url = reverse("count_confirm", args=[self.sid])
        self.maria_pk, self.ben_pk, self.lolo_pk = (self.night.players[n].pk for n in ("maria", "ben", "Lolo"))

    def as_(self, member):
        self.client.force_login(member.user)
        return self.client

    def test_player_sees_rebuy_on_their_own_row_only(self):
        page = self.as_(self.night.maria).get(self.page)
        self.assertContains(page, f'data-sheet-open="buy-{self.maria_pk}"', count=1)
        self.assertContains(page, 'aria-label="Rebuy for yourself"')
        self.assertNotContains(page, f'data-sheet-open="buy-{self.ben_pk}"')
        self.assertNotContains(page, f'data-sheet-open="buy-{self.lolo_pk}"')
        self.assertContains(page, 'name="seen_count" value="1"', count=1)
        self.assertContains(page, "Confirm rebuy", count=1)
        self.assertNotContains(page, "cashouts/add")
        self.assertNotContains(page, "/reverse/")

    def test_host_page_is_unchanged_but_carries_seen_count(self):
        page = self.as_(self.night.host).get(self.page)
        for pk in (self.maria_pk, self.ben_pk, self.lolo_pk):
            self.assertContains(page, f'data-sheet-open="buy-{pk}"', count=1)
        self.assertContains(page, 'name="seen_count" value="1"', count=3)

    def test_player_without_a_buy_in_or_cashed_out_sees_no_rebuy(self):
        cy = self.night.add_login_player("cy")
        self.assertNotContains(self.as_(cy).get(self.page), "buyins/add")
        self.night.cash("maria", 500, left=True)
        self.assertNotContains(self.as_(self.night.maria).get(self.page), "buyins/add")

    @override_settings(PLAYER_ENTRIES=False)
    def test_switch_off_removes_the_player_actions(self):
        self.assertNotContains(self.as_(self.night.maria).get(self.page), "buyins/add")
        self.assertEqual(self.client.post(self.buy_url, {"amount": "1000"}).status_code, 403)
        self.night.go("reconciliation")
        self.assertNotContains(self.client.get(self.page), "counts/enter")
        self.assertEqual(self.client.post(self.enter_url, {"amount": "1000"}).status_code, 403)

    def test_player_rebuy_post_and_the_polling_endpoint(self):
        host = self.as_(self.night.host)
        version = self.night.refresh().version
        state_url = reverse("session_state", args=[self.sid])
        self.assertEqual(host.get(state_url, {"v": version}).status_code, 204)
        response = self.as_(self.night.maria).post(self.buy_url, {"participant_id": self.maria_pk, "amount": "1,000", "seen_count": "1"}, follow=True)
        self.assertContains(response, "1 buy-in + 1 rebuy")
        fresh = self.as_(self.night.host).get(state_url, {"v": version})
        self.assertEqual(fresh.status_code, 200)
        self.assertIn("₱2,000", fresh.json()["html"])
        self.assertIn("1 buy-in + 1 rebuy", fresh.json()["html"])
        stale = self.client.post(self.buy_url, {"participant_id": self.maria_pk, "amount": "1000", "seen_count": "1"}, follow=True)
        self.assertContains(stale, "maria already has a new rebuy (₱1,000, recorded by maria at ")
        self.assertEqual(BuyIn.objects.filter(participant_id=self.maria_pk).count(), 2)

    def test_player_cannot_post_for_another_row_and_outsider_finds_nothing(self):
        self.assertEqual(self.as_(self.night.maria).post(self.buy_url, {"participant_id": self.ben_pk, "amount": "1000"}).status_code, 403)
        _, other_host = make_group("otto", "Other Game")
        self.assertEqual(self.as_(other_host).post(self.buy_url, {"amount": "1000"}).status_code, 404)
        self.assertEqual(self.client.post(self.enter_url, {"amount": "1000"}).status_code, 404)
        self.assertEqual(BuyIn.objects.count(), 3)

    def test_count_entry_states_for_the_player(self):
        self.night.go("reconciliation")
        client = self.as_(self.night.maria)
        page = client.get(self.page)
        self.assertContains(page, "counts/enter", count=1)
        self.assertContains(page, "Your count (₱)")
        self.assertContains(page, "Send to host", count=1)
        self.assertNotContains(page, "counts-form")
        self.assertNotContains(page, "own-count-change")
        sent = client.post(self.enter_url, {"amount": "1,450"}, follow=True)
        self.assertContains(sent, "Count sent to the host.")
        self.assertContains(sent, 'You entered <strong class="num">₱1,450</strong>. Waiting for the host to confirm.')
        self.assertContains(sent, '<summary class="small">Change</summary>')
        self.assertContains(sent, '<small>Entered</small><span class="num">₱1,450</span>')
        self.assertContains(client.post(self.enter_url, {"amount": ""}, follow=True), "Enter an amount")
        self.assertContains(client.post(self.enter_url, {"amount": "0"}, follow=True), '<small>Entered</small><span class="num">₱0</span>')
        entry = CountEntry.objects.get(is_current=True)
        services.confirm_counts(self.sid, self.night.host, {self.maria_pk: 140000}, uuid.uuid4())
        done = client.get(self.page)
        self.assertNotContains(done, "counts/enter")
        self.assertContains(done, "The host confirmed ₱1,400. You entered ₱0.")
        services.clear_count(self.sid, self.night.host, self.maria_pk)
        self.assertEqual(entry.version, 2)
        self.assertContains(client.get(self.page), "counts/enter", count=1)

    def test_everyone_sees_an_entered_count_and_the_host_can_accept_it(self):
        self.night.go("reconciliation")
        entry = services.enter_count(self.sid, self.night.maria, 145000, uuid.uuid4())
        other = self.as_(self.night.ben).get(self.page)
        self.assertContains(other, '<small>Entered</small><span class="num">₱1,450</span>', count=1)
        self.assertContains(other, "counts/enter", count=1)  # ben's own field, not maria's
        host = self.as_(self.night.host).get(self.page)
        self.assertContains(host, f'<input type="hidden" form="counts-form" name="entry_{self.maria_pk}" value="{entry.pk}">', count=1)
        self.assertContains(host, 'data-entered="145000"', count=1)
        self.assertContains(host, 'placeholder="1450"')
        self.assertContains(host, "maria entered ₱1,450. Leave the field empty to accept it, or type another number.")
        self.assertNotContains(host, "counts/enter")
        confirmed = self.client.post(self.confirm_url, {f"entry_{self.maria_pk}": entry.pk, f"count_{self.lolo_pk}": "650"}, follow=True)
        self.assertContains(confirmed, "2 counts confirmed.")
        self.assertEqual(FinalCount.objects.get(participant_id=self.maria_pk, is_current=True).entry, entry)
        self.assertContains(self.as_(self.night.maria).get(self.page), "The host confirmed your count.")

    def test_host_typing_wins_and_a_stale_entry_saves_nothing(self):
        self.night.go("reconciliation")
        old = services.enter_count(self.sid, self.night.maria, 145000, uuid.uuid4())
        services.enter_count(self.sid, self.night.maria, 150000, uuid.uuid4())
        host = self.as_(self.night.host)
        refused = host.post(self.confirm_url, {f"entry_{self.maria_pk}": old.pk, f"count_{self.lolo_pk}": "650"}, follow=True)
        self.assertContains(refused, "maria changed their count to ₱1,500. Nothing was saved.")
        self.assertContains(refused, 'value="650"')  # what the host typed is shown again
        self.assertFalse(FinalCount.objects.exists())
        host.post(self.confirm_url, {f"entry_{self.maria_pk}": old.pk, f"count_{self.maria_pk}": "1,400"})
        self.assertEqual(FinalCount.objects.get(is_current=True).amount, 140000)
        self.assertIsNone(FinalCount.objects.get(is_current=True).entry)

    def test_a_player_cannot_confirm(self):
        self.night.go("reconciliation")
        entry = services.enter_count(self.sid, self.night.maria, 145000, uuid.uuid4())
        self.assertEqual(self.as_(self.night.maria).post(self.confirm_url, {f"entry_{self.maria_pk}": entry.pk}).status_code, 403)

    def test_set_page_queries_do_not_grow_with_entries(self):
        self.night.go("reconciliation")
        client = self.as_(self.night.host)

        def count():
            with CaptureQueriesContext(connection) as found:
                client.get(self.page)
            return len(found)
        before = count()
        services.enter_count(self.sid, self.night.maria, 145000, uuid.uuid4())
        services.enter_count(self.sid, self.night.ben, 90000, uuid.uuid4())
        self.assertEqual(count(), before)

    def test_the_log_shows_who_entered_and_who_recorded(self):
        services.record_buy_in(self.sid, self.night.maria, None, 100000, uuid.uuid4())
        self.night.go("reconciliation")
        services.enter_count(self.sid, self.night.maria, 145000, uuid.uuid4())
        log = self.as_(self.night.host).get(reverse("session_log", args=[self.sid]))
        self.assertContains(log, "maria entered their final count: ₱1,450")


@skipUnlessDBFeature("has_select_for_update")
class PlayerEntryRaceTests(TransactionTestCase):
    def test_host_and_player_record_the_same_rebuy_once(self):
        night = night_with_logins()
        pk = night.players["maria"].pk
        outcomes = race(
            lambda: services.record_buy_in(night.session.pk, night.host, pk, 100000, uuid.uuid4(), seen_count=1),
            lambda: services.record_buy_in(night.session.pk, night.maria, pk, 100000, uuid.uuid4(), seen_count=1),
        )
        self.assertEqual(kinds(outcomes), ["ok", "refused"], outcomes)
        self.assertEqual(BuyIn.objects.filter(participant_id=pk).count(), 2)

    def test_a_player_changes_their_count_while_the_host_confirms(self):
        night = night_with_logins("reconciliation")
        pk = night.players["maria"].pk
        entry = services.enter_count(night.session.pk, night.maria, 145000, uuid.uuid4())
        outcomes = race(
            lambda: services.confirm_counts(night.session.pk, night.host, {}, uuid.uuid4(), entries={pk: entry.pk}),
            lambda: services.enter_count(night.session.pk, night.maria, 150000, uuid.uuid4()),
        )
        # Either the host confirmed the number on their screen first, or the change came first and nothing was saved.
        self.assertEqual(kinds(outcomes), ["ok", "refused"], outcomes)
        counts = list(FinalCount.objects.filter(participant_id=pk, is_current=True))
        if outcomes[0][0] == "ok":
            self.assertEqual([(c.amount, c.entry) for c in counts], [(145000, entry)])
            self.assertEqual(CountEntry.objects.filter(participant_id=pk).count(), 1)
        else:
            self.assertEqual(counts, [])
            self.assertEqual(CountEntry.objects.get(participant_id=pk, is_current=True).amount, 150000)

    def test_two_entries_at_once_leave_one_current(self):
        night = night_with_logins("reconciliation")
        outcomes = race(*[lambda: services.enter_count(night.session.pk, night.maria, 145000, uuid.uuid4())] * 2)
        self.assertEqual(kinds(outcomes), ["ok", "ok"], outcomes)
        self.assertEqual(CountEntry.objects.filter(is_current=True).count(), 1)
        self.assertEqual(sorted(CountEntry.objects.values_list("version", flat=True)), [1, 2])
