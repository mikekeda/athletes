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

    def test_views_home(self):
        resp = self.client.get(reverse('core:home'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'home.html')

    def test_views_about(self):
        resp = self.client.get(reverse('core:about'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'about.html')

    def test_views_login(self):
        resp = self.client.get(reverse('core:login'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'login.html')

    def test_views_logout(self):
        resp = self.client.get(reverse('core:logout'))
        self.assertRedirects(resp, '/login?next=/logout')
        self.client.login(username='testuser', password='12345')
        resp = self.client.get(reverse('core:logout'))
        self.assertRedirects(resp, reverse('core:login'))
