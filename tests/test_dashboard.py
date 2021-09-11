import os
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

import tests.testing_utils as testing_utils


class DashboardTest(StaticLiveServerTestCase):

    def setUp(self):
        self.driver = testing_utils.get_webdriver(headless=True)

        self.test_path = os.path.dirname(__file__)
        self.user = testing_utils.create_user()

    def tearDown(self):
        self.driver.quit()
