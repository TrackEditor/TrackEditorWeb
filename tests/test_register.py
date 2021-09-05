import os
import time
from urllib.parse import urljoin
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from glob import glob
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import libs.constants as c
from libs.utils import md5sum
from TrackApp.models import User


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
        self.downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        preferences = \
            {'download.default_directory': self.downloads_dir,
             'safebrowsing.enabled': 'false'}
        options.add_experimental_option('prefs', preferences)

        self.driver = webdriver.Chrome(chrome_options=options)

        self.test_path = os.path.dirname(__file__)
        self.user = self.create_user()

    def tearDown(self):
        self.driver.quit()

    def test_register(self):
        self.driver.get(urljoin(self.live_server_url, 'register'))
        self.driver.find_element_by_id('input_txt_username').send_keys('new_user')
        self.driver.find_element_by_id('input_txt_email').send_keys('new_user@example.com')
        self.driver.find_element_by_id('input_txt_password').send_keys('new_password_1234')
        self.driver.find_element_by_id('input_txt_confirmation').send_keys('new_password_1234')
        self.driver.find_element_by_id('input_btn_register').click()
        try:
            user = User.objects.get(username='new_user')
            self.assertEqual(user.username, 'new_user')
            self.assertEqual(user.email, 'new_user@example.com')
            self.assertEqual(len(user.password), 88)
            self.assertTrue(not user.is_superuser)
            self.assertTrue(not user.is_staff)
            self.assertTrue(user.is_active)
            self.assertEqual(self.driver.current_url.rstrip('/'), self.live_server_url)
        except User.DoesNotExist:
            self.assertTrue(False)
