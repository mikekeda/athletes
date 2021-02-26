from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Profile

User = get_user_model()


class AthletesViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create regular user.
        cls.password = User.objects.make_random_password()
        test_user = User.objects.create_user(username="testuser", password=cls.password)
        test_user.save()

        # Create user profile.
        Profile.objects.create(user=test_user)

    def test_views_team_page(self):
        resp = self.client.get(reverse("core:team_parse"))
        self.assertRedirects(resp, "/admin/login/?next=/team")

        self.client.login(username="testuser", password=self.password)
        resp = self.client.get(reverse("core:team_parse"))
        self.assertEqual(resp.status_code, 302)

    def test_views_league_page(self):
        resp = self.client.get(reverse("core:league_parse"))
        self.assertRedirects(resp, "/admin/login/?next=/league")

        self.client.login(username="testuser", password=self.password)
        resp = self.client.get(reverse("core:league_parse"))
        self.assertEqual(resp.status_code, 302)

    def test_views_athletes_page(self):
        resp = self.client.get(reverse("core:athletes"))
        self.assertRedirects(resp, "/login?next=/athletes")

        self.client.login(username="testuser", password=self.password)
        resp = self.client.get(reverse("core:athletes"))
        self.assertEqual(resp.status_code, 200)

    def test_views_teams_page(self):
        resp = self.client.get(reverse("core:teams"))
        self.assertRedirects(resp, "/login?next=/teams")

        self.client.login(username="testuser", password=self.password)
        resp = self.client.get(reverse("core:teams"))
        self.assertEqual(resp.status_code, 200)

    def test_views_home_page(self):
        resp = self.client.get(reverse("core:home"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "about.html")

    def test_views_map_page(self):
        resp = self.client.get(reverse("core:map"))
        self.assertRedirects(resp, "/login?next=/map")

        self.client.login(username="testuser", password=self.password)
        resp = self.client.get(reverse("core:map"))
        self.assertEqual(resp.status_code, 200)

    def test_views_terms_page(self):
        resp = self.client.get(reverse("core:terms"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "terms.html")

    def test_views_profile_page(self):
        resp = self.client.get(reverse("core:user", args=["testuser"]))
        self.assertEqual(resp.status_code, 403)
        self.client.login(username="testuser", password=self.password)
        resp = self.client.get(reverse("core:user", args=["testuser"]))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "profile.html")

    def test_views_login_page(self):
        resp = self.client.get(reverse("core:login"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "login.html")

    def test_views_logout_page(self):
        resp = self.client.get(reverse("core:logout"))
        self.assertRedirects(resp, "/login?next=/logout")
        self.client.login(username="testuser", password=self.password)
        resp = self.client.get(reverse("core:logout"))
        self.assertRedirects(resp, reverse("core:login"))
