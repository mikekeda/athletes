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

    def test_views_athletes_api(self):
        resp = self.client.get(reverse('core:athletes-api'))
        self.assertRedirects(resp, '/login?next=/api/athletes')

        self.client.login(username='testuser', password='12345')
        resp = self.client.get(reverse('core:athletes-api'))
        self.assertEqual(resp.status_code, 200)
