import os
from time import sleep
from ast import literal_eval
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase
from django.test.utils import tag
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import tests.testing_utils as testing_utils


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
        testing_utils.record_tracks(self.user, n := 25)
        response = self.client.get('/dashboard')
        self.assertEqual(response.context['pages'], list(range(1, n // 10 + 1 + 1)))
        self.assertEqual(response.context['number_pages'], n // 10 + 1)

    def test_get_tracks_from_db(self):
        testing_utils.record_tracks(self.user, n := 25)
        title_n = n

        for i in range(1, n // 10 + 2):
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
        response = self.client.get('/get_tracks_from_db/1')
        content = literal_eval(str(response.content, encoding='utf8'))
        self.assertEqual(content, [])


class DashboardIntegrationTest(StaticLiveServerTestCase):

    def check_page(self, page: int, starting_id: int, expected_elements: int,
                   click: bool = False):
        if click:
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight)")
            sleep(0.5)
            self.driver.find_element_by_id(f'page_{page}').click()
            WebDriverWait(self.driver, 5). \
                until(
                EC.invisibility_of_element_located((By.ID, 'div_spinner')))

        titles = self.driver.find_elements_by_class_name('dashboard-title')
        self.assertEqual(len(titles), expected_elements)
        for t in titles:
            starting_id -= 1
            self.assertEqual(t.text, f'title_{starting_id}')

    def setUp(self):
        self.driver = testing_utils.get_webdriver(headless=True)
        self.user = testing_utils.create_user()
        self.test_path = os.path.dirname(__file__)

        method = getattr(self, self._testMethodName)
        tags = getattr(method, 'tags', {})
        if 'no_login' not in tags:
            testing_utils.login(driver=self.driver,
                                live_server_url=self.live_server_url,
                                username='default_user',
                                password='default_password_1234')

    def tearDown(self):
        self.driver.quit()

    def test_dashboard_load(self):
        self.assertEqual(self.driver.title, 'Dashboard')

    @tag('no_login')
    def test_dashboard_table(self):
        testing_utils.record_tracks(self.user, n := 25)

        testing_utils.login(driver=self.driver,
                            live_server_url=self.live_server_url,
                            username='default_user',
                            password='default_password_1234')
        WebDriverWait(self.driver, 5).\
            until(EC.invisibility_of_element_located((By.ID, 'div_spinner')))

        self.check_page(1, n, 10, False)
        self.check_page(2, n - 10, 10, True)
        self.check_page(3, n - 20, 5, True)

    @tag('no_login')
    def test_dashboard_table_one_page(self):
        testing_utils.record_tracks(self.user, n := 2)

        testing_utils.login(driver=self.driver,
                            live_server_url=self.live_server_url,
                            username='default_user',
                            password='default_password_1234')
        WebDriverWait(self.driver, 5).\
            until(EC.invisibility_of_element_located((By.ID, 'div_spinner')))

        self.check_page(1, n, n, False)

    def test_dashboard_no_track(self):
        WebDriverWait(self.driver, 5).\
            until(EC.invisibility_of_element_located((By.ID, 'div_spinner')))
        self.assertIn('No tracks have been found',
                      self.driver.find_element_by_id('div_no_track').text)
