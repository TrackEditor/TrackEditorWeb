import os
from unittest import skip
from urllib.parse import urljoin
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase
from selenium import webdriver

from TrackApp.models import User


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

    @staticmethod
    def login(driver, live_server_url, username, password):
        driver.get(urljoin(live_server_url, 'login'))
        driver.find_element_by_id('input_txt_username').send_keys(username)
        driver.find_element_by_id('input_txt_password').send_keys(password)
        driver.find_element_by_id('input_btn_login').click()

    @staticmethod
    def create_user(username='default_user',
                    password='default_password_1234',
                    email='default_user@example.com'):
        if not User.objects.filter(username=username):
            user = User.objects.create(username=username,
                                       email=email,
                                       password='!')
            user.set_password(password)
            user.save()
        else:
            user = User.objects.get(username=username)
        return user

    def setUp(self):
        options = webdriver.ChromeOptions()
        options.headless = True
        self.driver = webdriver.Chrome(chrome_options=options)
        self.test_path = os.path.dirname(__file__)
        self.user = self.create_user()

    def tearDown(self):
        self.driver.quit()

    def test_login(self):
        self.login(driver=self.driver,
                   live_server_url=self.live_server_url,
                   username='default_user',
                   password='default_password_1234')

        self.assertEqual(self.driver.current_url.rstrip('/'), self.live_server_url)

    def test_log_out(self):
        self.login(driver=self.driver,
                   live_server_url=self.live_server_url,
                   username='default_user',
                   password='default_password_1234')

        link = self.driver.find_element_by_id('a_logout')
        link.click()
        self.assertEqual(self.driver.current_url.rstrip('/'), self.live_server_url)

    def test_wrong_password(self):
        self.login(driver=self.driver,
                   live_server_url=self.live_server_url,
                   username='default_user',
                   password='wrong_password')
        error_msg = self.driver.find_element_by_id('div_error_msg').text
        self.assertIn('Invalid username and/or password.', error_msg)

    def test_wrong_user(self):
        self.login(driver=self.driver,
                   live_server_url=self.live_server_url,
                   username='wrong_user',
                   password='default_password_1234')

        error_msg = self.driver.find_element_by_id('div_error_msg').text
        self.assertIn('Invalid username and/or password.', error_msg)
