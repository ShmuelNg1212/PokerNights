"""One chip per person in a group: the same colour and label on every screen (plan 1795101620)."""
import re

from django.template import Context, Template
from django.test import RequestFactory, TestCase

from games import services as games
from games.models import Participant
from games.tests.helpers import make_session
from groups import services as groups
from groups.models import Member
from ledger.tests.helpers import Night
from web.templatetags.table_tags import member_token, player_token


def chip(html, member):
    """``(colour class, label)`` of the first chip drawn for ``member`` in ``html``."""
    found = re.search(rf'class="chip (k\d+)" data-m="{member.pk}" aria-hidden="true">([^<]+)<', html)
    assert found, f"no chip for {member.display_name}"
    return found.groups()


class OneChipPerMemberTests(TestCase):
    def setUp(self):
        # Miguel joins the group before Ben, and Ben joins the set second: join order and member order differ.
        self.night = Night("Miguel", "Ben")
        self.ben = self.night.players["Ben"].member
        self.miguel = self.night.players["Miguel"].member

    def roster(self):
        return list(Member.objects.filter(group=self.night.group))

    def participants(self, session):
        return list(Participant.objects.filter(session=session).select_related("member").order_by("join_order"))

    def test_a_member_has_one_chip_in_a_set_and_in_the_roster(self):
        in_set = self.participants(self.night.session)
        ben_in_set = next(p for p in in_set if p.member_id == self.ben.pk)
        self.assertEqual(player_token(ben_in_set, in_set), member_token(self.ben, self.roster()))

    def test_join_order_in_a_set_does_not_change_the_chip(self):
        first = self.participants(self.night.session)
        other = make_session(self.night.host, state="open", table_name="Second table")
        games.add_participant(other.pk, self.night.host, self.ben.pk)  # Ben first this time
        games.add_participant(other.pk, self.night.host, self.miguel.pk)
        second = self.participants(other)
        token = lambda ps: player_token(next(p for p in ps if p.member_id == self.ben.pk), ps)
        self.assertEqual(token(first), token(second))

    def test_a_set_without_the_namesake_keeps_the_two_letters(self):
        groups.add_roster_player(self.night.host, "Bea")
        alone = make_session(self.night.host, state="open", table_name="Second table")
        games.add_participant(alone.pk, self.night.host, self.ben.pk)
        ps = self.participants(alone)
        bea = Member.objects.get(group=self.night.group, display_name="Bea")
        self.assertEqual(player_token(ps[0], ps), member_token(self.ben, self.roster()))
        self.assertNotEqual(member_token(bea, self.roster()), member_token(self.ben, self.roster()))

    def test_a_later_member_does_not_change_an_earlier_label(self):
        before = member_token(self.ben, self.roster())
        groups.add_roster_player(self.night.host, "Bea")
        self.assertEqual(member_token(self.ben, self.roster()), before)
        self.assertIn(">B<", before)
        bea = Member.objects.get(group=self.night.group, display_name="Bea")
        self.assertIn(">BE<", member_token(bea, self.roster()))

    def test_a_removed_member_keeps_their_chip_and_their_namesake_keeps_theirs(self):
        groups.add_roster_player(self.night.host, "Bea")
        bea = Member.objects.get(group=self.night.group, display_name="Bea")
        ben_before, bea_before = member_token(self.ben, self.roster()), member_token(bea, self.roster())
        Member.objects.filter(pk=self.ben.pk).update(status=Member.Status.REMOVED)
        active = list(Member.objects.filter(group=self.night.group, status=Member.Status.ACTIVE))
        self.assertEqual(member_token(bea, active), bea_before)
        self.assertEqual(member_token(Member.objects.get(pk=self.ben.pk), active), ben_before)

    def test_chips_on_a_page_read_the_roster_once(self):
        for name in ["Bea", "Bong", "Carlo", "Cora", "Dan"]:
            member = groups.add_roster_player(self.night.host, name)
            games.add_participant(self.night.session.pk, self.night.host, member.pk)
        ps = self.participants(self.night.session)
        page = Template("{% load table_tags %}{% for p in ps %}{% player_token p ps %}{% endfor %}")
        context = Context({"ps": ps, "request": RequestFactory().get("/")})
        with self.assertNumQueries(1):
            html = page.render(context)
        self.assertEqual(html.count('class="chip k'), len(ps))

    def test_the_set_page_and_the_players_page_draw_the_same_chip(self):
        self.client.force_login(self.night.host.user)
        set_page = self.client.get(f"/s/{self.night.session.pk}/").content.decode()
        roster_page = self.client.get(f"/g/{self.night.group.pk}/?view=players").content.decode()
        self.assertEqual(chip(set_page, self.ben), chip(roster_page, self.ben))
        self.assertEqual(chip(set_page, self.miguel), chip(roster_page, self.miguel))
