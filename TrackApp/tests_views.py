from django.test import TestCase
from selenium import webdriver


class LayoutTest(TestCase):
    def setUp(self):
        self.base_url = 'http://127.0.0.1:8000'
        self.driver = webdriver.Firefox(executable_path='C:/Users/Alonso/OneDrive/proyectos/geckodriver-v0.29.1-win64/geckodriver.exe')
        self.driver.get(self.base_url)

    def tearDown(self):
        self.driver.quit()

    def check_link(self, html_id, endpoint):
        link = self.driver.find_element_by_id(html_id)
        if link:
            link.click()
            url = self.driver.current_url
            if url == f'{self.base_url}/{endpoint}':
                return True

        return False

    def test_link_register(self):
        self.assertTrue(
            self.check_link(html_id='a_register',
                            endpoint='register')
        )

    def test_link_log_in(self):
        self.assertTrue(
            self.check_link(html_id='a_log_in',
                            endpoint='log_in')
        )

    def test_link_log_out(self):
        self.assertTrue(
            self.check_link(html_id='a_log_out',
                            endpoint='log_out')
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
