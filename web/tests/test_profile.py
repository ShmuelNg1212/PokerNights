"""A person's profile: their record across groups, their one name and their password."""

from django.contrib.auth import authenticate
from django.test import TestCase
from django.urls import reverse

from groups import services as groups
from groups.models import Member
from groups.tests.helpers import make_user
from settlement.tests.test_stats import OCT_1, SEP_30, Club

OLD = "tablestakes-91"
NEW = "river-card-4417"


class ProfileTests(TestCase):
    def setUp(self):
        self.user = make_user("ana")
        self.friday, self.sunday = Club(), Club()
        self.sunday.group.name = "Sunday Game"
        self.sunday.group.save()
        for club in (self.friday, self.sunday):
            club.members["Ana"] = Member.objects.create(group=club.group, user=self.user, display_name="Ana")
        self.client.force_login(self.user)

    def page(self, **params):
        return self.client.get(reverse("profile"), params)

    def test_a_login_is_needed(self):
        self.client.logout()
        self.assertRedirects(self.page(), reverse("login") + "?next=" + reverse("profile"), fetch_redirect_response=False)

    def test_pesos_add_up_across_groups_and_each_group_links_to_its_player_page(self):
        self.friday.session(SEP_30, {"Ana": (1000, 1500), "B": (1000, 500)})
        self.sunday.session(OCT_1, {"Ana": (1000, 800), "B": (1000, 1200)})
        response = self.page()
        self.assertEqual(response.context["record"].net, 30000)
        lines = response.context["pesos_groups"]
        self.assertEqual([(line.name, line.record.net) for line in lines], [("Friday Game", 50000), ("Sunday Game", -20000)])
        self.assertEqual(lines[0].url, reverse("player", args=[self.friday.group.pk, self.friday.member("Ana").pk]) + "?period=all&unit=php")
        self.assertContains(response, "+₱300")
        self.assertEqual(response.context["chips_groups"], [])

    def test_chips_are_shown_per_group_and_never_added(self):
        self.friday.session(OCT_1, {"Ana": (500, 600), "B": (500, 400)}, unit="chips")
        self.sunday.session(OCT_1, {"Ana": (500, 300), "B": (500, 700)}, unit="chips")
        response = self.page()
        self.assertEqual([(line.name, line.record.net) for line in response.context["chips_groups"]], [("Friday Game", 100), ("Sunday Game", -200)])
        self.assertEqual(response.context["record"].sessions, 0)
        self.assertContains(response, "not added together")
        self.assertNotContains(response, "−100 chips")

    def test_this_year_and_a_left_group_without_a_link(self):
        self.friday.session(SEP_30.replace(year=2025), {"Ana": (1000, 1500), "B": (1000, 500)})
        self.sunday.session(OCT_1, {"Ana": (1000, 800), "B": (1000, 1200)})
        groups.remove_member(self.sunday.host, self.sunday.member("Ana").pk)
        lines = self.page(period="year").context["pesos_groups"]
        self.assertEqual([(line.name, line.url, line.left) for line in lines], [("Sunday Game", "", True)])
        self.assertContains(self.page(), "You left this group")

    def test_an_archived_group_and_another_persons_results_stay_out(self):
        self.friday.session(SEP_30, {"B": (1000, 1500), "C": (1000, 500)})
        self.sunday.session(OCT_1, {"Ana": (1000, 800), "B": (1000, 1200)})
        groups.archive_group(self.sunday.host)
        response = self.page()
        self.assertFalse(response.context["has_any"])
        self.assertContains(response, "after your first closed session")

    def test_queries_do_not_grow_with_groups_or_sessions(self):
        self.friday.session(SEP_30, {"Ana": (1000, 1100), "B": (1000, 900)})
        before = self._count()
        for club in (self.friday, self.sunday):
            club.session(OCT_1, {"Ana": (1000, 1100), "B": (1000, 900)})
        third = Club()
        Member.objects.create(group=third.group, user=self.user, display_name="Ana")
        self.assertEqual(self._count(), before)

    def _count(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as seen:
            self.page()
        return len(seen)

    def test_the_name_shows_once_or_by_group(self):
        self.assertEqual(self.page().context["own_name"], "Ana")
        groups.rename_self(self.sunday.member("Ana"), "Annie")
        response = self.page()
        self.assertEqual((response.context["own_name"], response.context["names_by_group"]),
                         ("", [("Friday Game", "Ana"), ("Sunday Game", "Annie")]))
        self.assertContains(response, "Differs by group")


class ProfileNameTests(TestCase):
    def setUp(self):
        self.user = make_user("ana")
        self.friday, self.sunday = Club(), Club()
        self.sunday.group.name = "Sunday Game"
        self.sunday.group.save()
        for club in (self.friday, self.sunday):
            Member.objects.create(group=club.group, user=self.user, display_name="Ana")
        self.client.force_login(self.user)

    def post(self, name):
        return self.client.post(reverse("profile_name"), {"name": name}, follow=True)

    def test_every_group_takes_the_name(self):
        response = self.post("Annie")
        self.assertRedirects(response, reverse("profile"))
        self.assertContains(response, "Your name is now Annie.")
        self.assertEqual(set(Member.objects.filter(user=self.user).values_list("display_name", flat=True)), {"Annie"})

    def test_a_taken_name_names_the_group_it_skipped(self):
        groups.add_roster_player(self.sunday.host, "Annie")
        response = self.post("Annie")
        self.assertContains(response, "Your name is now Annie.")
        self.assertContains(response, "Not changed in Sunday Game: another Annie is in that group.")

    def test_a_refused_name_keeps_the_form_open_with_its_error(self):
        response = self.post("   ")
        self.assertTrue(response.context["name_form"].errors)
        self.assertContains(response, 'id="name" open')

    def test_get_is_refused(self):
        self.assertEqual(self.client.get(reverse("profile_name")).status_code, 405)


class ProfilePasswordTests(TestCase):
    def setUp(self):
        self.user = make_user("ana")
        self.client.force_login(self.user)

    def post(self, current, new=NEW, repeat=None):
        return self.client.post(reverse("password_change"), {
            "current_password": current, "new_password1": new, "new_password2": repeat or new,
        }, follow=True)

    def test_the_change_keeps_this_login(self):
        response = self.post(OLD)
        self.assertContains(response, "Password changed. Other phones and browsers are logged out.")
        self.assertIsNotNone(authenticate(username="ana", password=NEW))
        self.assertEqual(self.client.get(reverse("profile")).status_code, 200)  # still logged in

    def test_other_logins_end(self):
        other = self.client_class()
        other.force_login(self.user)
        self.post(OLD)
        self.assertEqual(other.get(reverse("profile")).status_code, 302)

    def test_a_wrong_current_password_is_shown_and_no_password_is_kept(self):
        response = self.post("guess-one-91")
        self.assertContains(response, "That is not your current password.")
        self.assertContains(response, 'id="password" open')
        self.assertNotContains(response, "guess-one-91")
        self.assertNotContains(response, NEW)
        self.assertIsNotNone(authenticate(username="ana", password=OLD))

    def test_a_weak_new_password_is_refused_without_testing_the_current_one(self):
        from audit.models import AuditEvent

        response = self.post("guess-one-91", new="12345678")
        self.assertContains(response, "Use more than digits.")
        self.assertFalse(AuditEvent.objects.filter(action="password.change_refused").exists())

    def test_the_errors_show_once(self):
        self.post("guess-one-91")
        self.assertNotContains(self.client.get(reverse("profile")), "not your current password")
