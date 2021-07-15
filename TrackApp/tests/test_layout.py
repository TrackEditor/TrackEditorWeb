from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver

from TrackApp.models import User


class LayoutTest(StaticLiveServerTestCase):
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

    def setUp(self):
        options = webdriver.ChromeOptions()
        options.headless = True
        self.driver = webdriver.Chrome(chrome_options=options)        
        self.driver.get(self.live_server_url)
        self.user = self.create_user()

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
        self.login(driver=self.driver,
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
