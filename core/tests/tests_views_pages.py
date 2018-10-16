from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class AthletesViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create usual user.
        test_user = User.objects.create_user(username='testuser',
                                             password='12345')
        test_user.save()

    def test_views_team_page(self):
        resp = self.client.get(reverse('core:team'))
        self.assertRedirects(resp, '/admin/login/?next=/team')

        self.client.login(username='testuser', password='12345')
        resp = self.client.get(reverse('core:team'))
        self.assertEqual(resp.status_code, 302)

    def test_views_teams_page(self):
        resp = self.client.get(reverse('core:league'))
        self.assertRedirects(resp, '/admin/login/?next=/league')

        self.client.login(username='testuser', password='12345')
        resp = self.client.get(reverse('core:league'))
        self.assertEqual(resp.status_code, 302)

    def test_views_crm_page(self):
        resp = self.client.get(reverse('core:crm'))
        self.assertRedirects(resp, '/login?next=/crm')

        self.client.login(username='testuser', password='12345')
        resp = self.client.get(reverse('core:crm'))
        self.assertEqual(resp.status_code, 200)

    def test_views_home_page(self):
        resp = self.client.get(reverse('core:home'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'about.html')

    def test_views_map_page(self):
        resp = self.client.get(reverse('core:map'))
        self.assertRedirects(resp, '/login?next=/map')

        self.client.login(username='testuser', password='12345')
        resp = self.client.get(reverse('core:map'))
        self.assertEqual(resp.status_code, 200)

    def test_views_terms_page(self):
        resp = self.client.get(reverse('core:terms'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'terms.html')

    def test_views_login_page(self):
        resp = self.client.get(reverse('core:login'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'login.html')

    def test_views_logout_page(self):
        resp = self.client.get(reverse('core:logout'))
        self.assertRedirects(resp, '/login?next=/logout')
        self.client.login(username='testuser', password='12345')
        resp = self.client.get(reverse('core:logout'))
        self.assertRedirects(resp, reverse('core:login'))
