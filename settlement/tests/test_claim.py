"""A claim keeps the player's records, and an account with records of its own cannot claim."""

import uuid

from django.test import TestCase

from games import services as games
from games.tests.helpers import make_session
from groups import services as groups
from groups.errors import RuleError
from groups.models import Member
from groups.tests.helpers import make_user
from ledger import services as ledger
from ledger.models import PlayerResult
from settlement import queries
from settlement.models import Transfer

from .test_stats import OCT_1, Club


class ClaimWithRecordsTests(TestCase):
    def setUp(self):
        self.club = Club()
        self.club.session(OCT_1, {"Ana": (1000, 1500), "Tito": (1000, 500)})
        self.tito = self.club.member("Tito")
        self.user = make_user("titoboy")
        self.token = groups.create_claim_link(self.club.host, self.tito.pk)[2]

    def test_results_stats_and_transfers_are_untouched_and_now_theirs(self):
        results = list(PlayerResult.objects.values_list("pk", "member_id", "net").order_by("pk"))
        transfers = list(Transfer.objects.values_list("pk", "payer_id", "payee_id", "amount"))
        stats, activity = self.club.stats(), queries.roster_activity([self.tito.pk])
        member = groups.claim_member(self.user, self.token)
        self.assertEqual(member.pk, self.tito.pk)
        self.assertEqual(list(PlayerResult.objects.values_list("pk", "member_id", "net").order_by("pk")), results)
        self.assertEqual(list(Transfer.objects.values_list("pk", "payer_id", "payee_id", "amount")), transfers)
        self.assertEqual((self.club.stats(), queries.roster_activity([self.tito.pk])), (stats, activity))

    def test_the_claimed_player_records_their_own_rebuy(self):
        running = make_session(self.club.host, table=self.club.table, state="open")
        seat = games.add_participants(running.pk, self.club.host, [self.tito.pk], uuid.uuid4())[0]
        games.transition(running.pk, self.club.host, "start", opening_buy_ins=False)
        ledger.record_buy_in(running.pk, self.club.host, seat.pk, 100000, uuid.uuid4())
        member = groups.claim_member(self.user, self.token)
        rebuy = ledger.record_buy_in(running.pk, member, seat.pk, 100000, uuid.uuid4(), seen_count=1)
        self.assertEqual(rebuy.amount, 100000)

    def test_an_account_with_records_of_its_own_is_refused_and_nothing_changes(self):
        own = Member.objects.create(group=self.club.group, user=self.user, display_name="titoboy")
        cases = {
            "a seat": lambda: games.add_participants(
                make_session(self.club.host, table=self.club.table, state="open").pk, self.club.host, [own.pk], uuid.uuid4()),
        }
        for name, build in cases.items():
            with self.subTest(name):
                build()
                preview = groups.claim_preview(self.user, self.token)
                self.assertEqual(preview.refusal, "You already have games recorded in this group as titoboy. Two records cannot be joined yet. Ask a host of the group.")
                with self.assertRaisesMessage(RuleError, "Two records cannot be joined yet"):
                    groups.claim_member(self.user, self.token)
                self.assertIsNone(Member.objects.get(pk=self.tito.pk).user_id)
                self.assertTrue(Member.objects.filter(pk=own.pk).exists())

    def test_a_removed_account_with_records_is_sent_to_a_host(self):
        self.club.members["titoboy"] = Member.objects.create(group=self.club.group, user=self.user, display_name="titoboy")
        self.club.session(OCT_1, {"Ana": (1000, 1000), "titoboy": (1000, 1000)})
        groups.remove_member(self.club.host, self.club.members["titoboy"].pk)
        preview = groups.claim_preview(self.user, self.token)
        self.assertEqual(preview.refusal, "You were in this group as titoboy. Ask a host to bring you back.")
        with self.assertRaisesMessage(RuleError, "Ask a host to bring you back"):
            groups.claim_member(self.user, self.token)
