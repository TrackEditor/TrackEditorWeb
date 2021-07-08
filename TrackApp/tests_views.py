from django.test import TestCase, LiveServerTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver

from .models import User


class LayoutTest(StaticLiveServerTestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()
        self.driver.get(self.live_server_url)

    def tearDown(self):
        self.driver.quit()

    def check_link(self, html_id, endpoint):
        link = self.driver.find_element_by_id(html_id)
        if link:
            link.click()
            url = self.driver.current_url
            if url == f'{self.live_server_url}/{endpoint}':
                return True

        return False

    def test_link_register(self):
        self.assertTrue(
            self.check_link(html_id='a_register',
                            endpoint='register')
        )

    def test_link_login(self):
        self.assertTrue(
            self.check_link(html_id='a_login',
                            endpoint='login')
        )

    def test_link_combine_tracks(self):
        self.assertTrue(
            self.check_link(html_id='a_combine_tracks',
                            endpoint='combine_tracks')
        )

    def test_link_insert_timestamp(self):
        self.assertTrue(
            self.check_link(html_id='a_insert_timestamp',
                            endpoint='insert_timestamp')
        )


class ViewsTest(StaticLiveServerTestCase):

    def setUp(self):
        self.driver = webdriver.Firefox()

        if not User.objects.filter(username='default_user'):
            user = User.objects.create(username='default_user',
                                       email='default_user@example.com',
                                       password='!')
            user.set_password('default_password_1234')
            user.save()

    def tearDown(self):
        self.driver.quit()

    def test_register(self):
        self.driver.get(self.live_server_url + '/register')
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

    def test_login(self):
        self.driver.get(self.live_server_url + '/login')
        self.driver.find_element_by_id('input_txt_username').send_keys('default_user')
        self.driver.find_element_by_id('input_txt_password').send_keys('default_password_1234')
        self.driver.find_element_by_id('input_btn_login').click()

        self.assertEqual(self.driver.current_url.rstrip('/'), self.live_server_url)

    def test_log_out(self):
        # Create user
        if not User.objects.filter(username='default_user'):
            user = User.objects.create(username='default_user',
                                       email='default_user@example.com',
                                       password='!')
            user.set_password('default_password_1234')
            user.save()

        # Login
        self.driver.get(self.live_server_url + '/login')
        self.driver.find_element_by_id('input_txt_username').send_keys('default_user')
        self.driver.find_element_by_id('input_txt_password').send_keys('default_password_1234')
        self.driver.find_element_by_id('input_btn_login').click()

        # Check endpoint
        link = self.driver.find_element_by_id('a_logout')
        link.click()
        self.assertEqual(self.driver.current_url.rstrip('/'), self.live_server_url)
