from django.contrib.staticfiles.testing import StaticLiveServerTestCase

import tests.testing_utils as testing_utils


class LayoutTest(StaticLiveServerTestCase):

    def setUp(self):
        self.driver = testing_utils.get_webdriver()
        self.driver.get(self.live_server_url)
        self.user = testing_utils.create_user()

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
        testing_utils.login(driver=self.driver,
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
