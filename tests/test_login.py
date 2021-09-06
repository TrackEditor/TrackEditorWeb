import os
from unittest import skip
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase

import tests.testing_utils as testing_utils


@skip('Not implemented')
class LoginViewTest(TestCase):
    def test_login(self):
        assert False

    def test_logout(self):
        assert False

    def test_wrong_password(self):
        assert False

    def test_wrong_user(self):
        assert False


class LoginIntegrationTest(StaticLiveServerTestCase):

    def setUp(self):
        self.driver = testing_utils.get_webdriver(headless=True)
        self.test_path = os.path.dirname(__file__)
        self.user = testing_utils.create_user()

    def tearDown(self):
        self.driver.quit()

    def test_login(self):
        testing_utils.login(driver=self.driver,
                    live_server_url=self.live_server_url,
                    username='default_user',
                    password='default_password_1234')

        self.assertEqual(self.driver.current_url.rstrip('/'),
                         self.live_server_url)

    def test_log_out(self):
        testing_utils.login(driver=self.driver,
                    live_server_url=self.live_server_url,
                    username='default_user',
                    password='default_password_1234')

        link = self.driver.find_element_by_id('a_logout')
        link.click()
        self.assertEqual(self.driver.current_url.rstrip('/'),
                         self.live_server_url)

    def test_wrong_password(self):
        testing_utils.login(driver=self.driver,
                    live_server_url=self.live_server_url,
                    username='default_user',
                    password='wrong_password')
        error_msg = self.driver.find_element_by_id('div_error_msg').text
        self.assertIn('Invalid username and/or password.', error_msg)

    def test_wrong_user(self):
        testing_utils.login(driver=self.driver,
                    live_server_url=self.live_server_url,
                    username='wrong_user',
                    password='default_password_1234')

        error_msg = self.driver.find_element_by_id('div_error_msg').text
        self.assertIn('Invalid username and/or password.', error_msg)
