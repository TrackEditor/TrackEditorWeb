import os
from unittest import skip, expectedFailure
from urllib.parse import urljoin
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase
from selenium import webdriver

from TrackApp.models import User


@skip('Not implemented')
class RegisterViewTest(TestCase):
    def test_register(self):
        assert False

    def test_wrong_confirmation(self):
        assert False

    def test_existing_user(self):
        assert False

    def test_wrong_email_format(self):
        assert False


class RegisterIntegrationTest(StaticLiveServerTestCase):

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

    def register_user(self,
                      username='new_user',
                      email='new_user@example.com',
                      password='new_password_1234',
                      confirmation='new_password_1234'):
        self.driver.get(urljoin(self.live_server_url, 'register'))
        self.driver.find_element_by_id('input_txt_username').send_keys(username)
        self.driver.find_element_by_id('input_txt_email').send_keys(email)
        self.driver.find_element_by_id('input_txt_password').send_keys(password)
        self.driver.find_element_by_id('input_txt_confirmation').send_keys(confirmation)
        self.driver.find_element_by_id('input_btn_register').click()

    def test_register(self):
        self.register_user(username='new_user',
                           email='new_user@example.com',
                           password='new_password_1234',
                           confirmation='new_password_1234')

        user = User.objects.get(username='new_user')
        self.assertEqual(user.username, 'new_user')
        self.assertEqual(user.email, 'new_user@example.com')
        self.assertEqual(len(user.password), 88)
        self.assertTrue(not user.is_superuser)
        self.assertTrue(not user.is_staff)
        self.assertTrue(user.is_active)
        self.assertEqual(self.driver.current_url.rstrip('/'), self.live_server_url)

    def test_wrong_confirmation(self):
        self.register_user(username='new_user',
                           email='new_user@example.com',
                           password='new_password_1234',
                           confirmation='wrong_confirmation')
        error_msg = self.driver.find_element_by_id('div_error_msg').text
        self.assertIn('Passwords must match.', error_msg)

    def test_existing_user(self):
        self.register_user(username='default_user')
        error_msg = self.driver.find_element_by_id('div_error_msg').text
        self.assertIn('Username already taken.', error_msg)

    @expectedFailure  # Not implemented functionality
    def test_existing_email(self):
        self.register_user(username='a1s2d3f4',
                           email='default_user@example.com')
        error_msg = self.driver.find_element_by_id('div_error_msg').text
        self.assertIn('Username already taken.', error_msg)
