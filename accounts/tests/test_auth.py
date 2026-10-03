from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AuthTests(TestCase):
    def test_pages_require_login(self):
        response = self.client.get(reverse("home"))
        self.assertRedirects(response, f"{reverse('login')}?next=/")

    def test_signup_logs_in_and_goes_home(self):
        response = self.client.post(
            reverse("signup"),
            {"username": "ana", "password1": "tablestakes-91", "password2": "tablestakes-91"},
        )
        self.assertRedirects(response, reverse("home"))
        self.assertTrue(get_user_model().objects.filter(username="ana").exists())
        self.assertContains(self.client.get(reverse("home")), "ana")

    def test_signup_follows_a_local_next_only(self):
        data = {"username": "ben", "password1": "tablestakes-91", "password2": "tablestakes-91"}
        response = self.client.post(reverse("signup"), {**data, "next": "/healthz"})
        self.assertRedirects(response, "/healthz", fetch_redirect_response=False)
        self.client.post(reverse("logout"))
        data["username"] = "cy"
        response = self.client.post(reverse("signup"), {**data, "next": "https://evil.example/"})
        self.assertRedirects(response, reverse("home"))

    def test_login_and_logout(self):
        get_user_model().objects.create_user("dee", password="tablestakes-91")
        response = self.client.post(reverse("login"), {"username": "dee", "password": "tablestakes-91"})
        self.assertRedirects(response, reverse("home"))
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))
        self.assertEqual(self.client.get(reverse("home")).status_code, 302)

    def test_wrong_password_is_refused(self):
        get_user_model().objects.create_user("eve", password="tablestakes-91")
        response = self.client.post(reverse("login"), {"username": "eve", "password": "nope"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
