from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver

from TrackApp.models import User


class Utils:
    @staticmethod
    def login(driver, live_server_url, username, password):
        driver.get(live_server_url + '/login')
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


class LayoutTest(StaticLiveServerTestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()
        self.driver.get(self.live_server_url)
        self.user = Utils.create_user()

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

    def test_link_logout(self):
        Utils().login(driver=self.driver,
                      live_server_url=self.live_server_url,
                      username='default_user',
                      password='default_password_1234')
        self.assertTrue(
            self.check_link(html_id='a_logout',
                            endpoint='')
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
        self.user = Utils.create_user()

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
        Utils().login(driver=self.driver,
                      live_server_url=self.live_server_url,
                      username='default_user',
                      password='default_password_1234')

        self.assertEqual(self.driver.current_url.rstrip('/'), self.live_server_url)
        # TODO extra check is needed to verify that there is a logged user

    def test_log_out(self):
        Utils().login(driver=self.driver,
                      live_server_url=self.live_server_url,
                      username='default_user',
                      password='default_password_1234')

        link = self.driver.find_element_by_id('a_logout')
        link.click()
        self.assertEqual(self.driver.current_url.rstrip('/'), self.live_server_url)
        # TODO extra check is needed to verify that there is no logged user
