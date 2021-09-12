import os
from ast import literal_eval
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase
from django.test.utils import tag

import tests.testing_utils as testing_utils
from libs import track
from TrackApp.models import Track


class DashboardViewTest(TestCase):
    def create_user(self,
                    username='default_user',
                    password='default_password_1234',
                    email='default_user@example.com'):
        user = testing_utils.create_user(username=username,
                                         password=password,
                                         email=email)

        self.user, self.username, self.password = user, username, password
        return user, username, password

    def login(self):
        self.client.login(username=self.username,
                          password=self.password)

    def load_tracks(self, n):
        for i in range(n):
            Track(user=self.user,
                  track=track.Track().to_json(),
                  title=f'title_{i}').save()

    def setUp(self):
        # Tag to skip the login
        method = getattr(self, self._testMethodName)
        tags = getattr(method, 'tags', {})
        if 'skip_setup' in tags:
            return

        # Set up function not skipped
        self.create_user()
        self.login()

    def test_dashboard_template(self):
        response = self.client.get('/dashboard')
        self.assertTemplateUsed(response, 'TrackApp/dashboard.html')

    @tag('skip_setup')
    def test_dashboard_not_logged(self):
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 302)

    @tag('skip_setup')
    def test_get_tracks_from_db_not_logged(self):
        response = self.client.get('/get_tracks_from_db/1')
        self.assertEqual(response.status_code, 302)

    def test_dashboard_context(self):
        self.load_tracks(n := 25)
        response = self.client.get('/dashboard')
        self.assertEqual(response.context['pages'], list(range(1, n//10 + 1 + 1)))
        self.assertEqual(response.context['number_pages'], n//10 + 1)

    def test_get_tracks_from_db(self):
        self.load_tracks(n := 25)
        title_n = n

        for i in range(1, n//10 + 2):
            response = self.client.get(f'/get_tracks_from_db/{i}')
            content = literal_eval(str(response.content, encoding='utf8'))

            self.assertLessEqual(len(content), 10)
            for record in content:
                title_n -= 1
                self.assertEqual(record['title'], f'title_{title_n}')

    def test_dashboard_context_no_records(self):
        response = self.client.get('/dashboard')
        self.assertEqual(response.context['pages'], [])
        self.assertEqual(response.context['number_pages'], 0)

    def test_get_tracks_from_db_no_records(self):
        response = self.client.get(f'/get_tracks_from_db/1')
        content = literal_eval(str(response.content, encoding='utf8'))
        self.assertEqual(content, [])


class DashboardIntegrationTest(StaticLiveServerTestCase):

    def setUp(self):
        self.driver = testing_utils.get_webdriver(headless=True)

        self.test_path = os.path.dirname(__file__)
        self.user = testing_utils.create_user()

    def tearDown(self):
        self.driver.quit()

    # TODO solve the spinner issue for no tracks
    # TODO check "no track" message if no track available
    # TODO test editor and remove buttons
    # TODO test pagination for 1 and > 1 pages
