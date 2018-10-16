from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class ToolAdminTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create admin user.
        cls.test_admin = User.objects.create_superuser(
            username='testadmin',
            email='myemail@test.com',
            password='12345',
            first_name='Bob',
            last_name='Smit'
        )
        cls.test_admin.save()

    def test_admin_team(self):
        self.client.login(username='testadmin', password='12345')
        resp = self.client.get('/admin/core/team/')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'admin/base.html')

        resp = self.client.get('/admin/core/team/add/')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'admin/change_form.html')

    def test_admin_athlete(self):
        self.client.login(username='testadmin', password='12345')
        resp = self.client.get('/admin/core/athlete/')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'admin/base.html')

        resp = self.client.get('/admin/core/athlete/add/')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'admin/change_form.html')

    def test_admin_athletelist(self):
        self.client.login(username='testadmin', password='12345')
        resp = self.client.get('/admin/core/athleteslist/')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'admin/base.html')

        resp = self.client.get('/admin/core/athleteslist/add/')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'admin/change_form.html')

    def test_admin_teamslist(self):
        self.client.login(username='testadmin', password='12345')
        resp = self.client.get('/admin/core/teamslist/')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'admin/base.html')

        resp = self.client.get('/admin/core/teamslist/add/')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'admin/change_form.html')

    def test_admin_leagueslist(self):
        self.client.login(username='testadmin', password='12345')
        resp = self.client.get('/admin/core/leagueslist/')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'admin/base.html')

        resp = self.client.get('/admin/core/leagueslist/add/')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'admin/change_form.html')
