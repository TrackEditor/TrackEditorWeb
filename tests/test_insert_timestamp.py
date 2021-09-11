import os
import time
from urllib.parse import urljoin
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from glob import glob
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

import tests.testing_utils as testing_utils
import libs.constants as c
from libs.utils import md5sum


class InsertTimestampIntegrationTest(StaticLiveServerTestCase):

    def setUp(self):
        self.driver = testing_utils.get_webdriver(headless=True)
        self.test_path = os.path.dirname(__file__)
        self.user = testing_utils.create_user()
        self.downloads_dir = testing_utils.get_downloads_dir()
        self.driver.get(urljoin(self.live_server_url, 'insert_timestamp'))

        # Remove previous testing files
        for file in glob(os.path.join(self.downloads_dir,
                                      'TrackEditor_insert_timestamp_*.gpx')):
            os.remove(file)

    def tearDown(self):
        self.driver.quit()

    def insert_data(self, file: str, date: str, init_time: str, speed: str,
                    consider_elevation: bool = False):
        if file:
            self.driver.\
                find_element_by_id('select-file-1').\
                send_keys(os.path.join(self.test_path, 'samples', file))

        if date:
            self.driver.find_element_by_id('input_date').send_keys(date)

        if init_time:
            if os.name == 'posix':
                if int(init_time[:2]) > 12:
                    init_time += 'AM'
                else:
                    init_time += 'PM'
            self.driver.find_element_by_id('input_time').send_keys(init_time)

        if speed:
            self.driver.find_element_by_id('input_desired_speed').send_keys(speed)

        if consider_elevation:
            self.driver.find_element_by_id('span_checkmark').click()

    def test_insert_timestamp_logged_user(self):
        testing_utils.login(driver=self.driver,
                            live_server_url=self.live_server_url,
                            username='default_user',
                            password='default_password_1234')

        self.driver.get(urljoin(self.live_server_url, 'insert_timestamp'))

        self.insert_data(file='island_full.gpx',
                         date='01012011',
                         init_time='0150',
                         speed='15',
                         consider_elevation=True)

        self.driver.find_element_by_id('input_btn_insert_timestamp').click()
        WebDriverWait(self.driver, 5).\
            until(EC.invisibility_of_element_located((By.ID, 'div_spinner')))

        self.driver.find_element_by_id('input_btn_download').click()
        time.sleep(2)  # time to download file

        # downloaded_file = \
        #     glob(os.path.join(self.downloads_dir,
        #                       'TrackEditor_insert_timestamp_*.gpx'))[-1]
        #
        # self.assertEqual(
        #     md5sum(downloaded_file),
        #     md5sum(os.path.join(self.test_path,
        #                         'references',
        #                         'test_insert_time.gpx')
        #            )
        # )

        self.assertTrue(
            self.driver.find_element_by_id('js-map').is_displayed())
        self.assertTrue(
            self.driver.find_element_by_class_name('ol-viewport').is_displayed())

    def test_insert_timestamp(self):
        self.insert_data(file='island_full.gpx',
                         date='01012011',
                         init_time='0150',
                         speed='15',
                         consider_elevation=True)

        self.driver.find_element_by_id('input_btn_insert_timestamp').click()
        WebDriverWait(self.driver, 5).\
            until(EC.invisibility_of_element_located((By.ID, 'div_spinner')))

        self.driver.find_element_by_id('input_btn_download').click()
        time.sleep(2)  # time to download file

        # downloaded_file = \
        #     glob(os.path.join(self.downloads_dir,
        #                       'TrackEditor_insert_timestamp_*.gpx'))[-1]
        #
        # self.assertEqual(
        #     md5sum(downloaded_file),
        #     md5sum(os.path.join(self.test_path,
        #                         'references',
        #                         'test_insert_time.gpx')
        #            )
        # )

        self.assertRaises(NoSuchElementException,
                          self.driver.find_element_by_id,
                          'js-map')

    def test_timestamp_upload_wrong_extension(self):
        self.driver.\
            find_element_by_id('select-file-1').\
            send_keys(os.path.join(self.test_path,
                                   'samples',
                                   'wrong_extension.txt'))

        error_msg = self.driver.find_element_by_id('div_error_msg_js')

        self.assertEqual(
            error_msg.text,
            "Extension for wrong_extension.txt is not valid ['gpx'].")

    def test_timestamp_no_file(self):
        self.insert_data(file='',
                         date='01012011',
                         init_time='0150',
                         speed='1')
        self.driver.find_element_by_id('input_btn_insert_timestamp').click()
        error_msg = self.driver.find_element_by_id('div_error_msg_js')
        self.assertEqual(error_msg.text, 'No file has been selected.')

    def test_timestamp_bad_formed_file(self):
        self.insert_data(file='bad_formed.gpx',
                         date='01012011',
                         init_time='0150',
                         speed='1')

        self.driver.find_element_by_id('input_btn_insert_timestamp').click()
        WebDriverWait(self.driver, 5).\
            until(EC.invisibility_of_element_located((By.ID, 'div_spinner')))

        error_msg = self.driver.find_element_by_id('div_error_msg')
        self.assertEqual(error_msg.text, 'Error loading files')

    def test_timestamp_missing_desired_speed(self):
        self.insert_data(file='island_1.gpx',
                         date='01012011',
                         init_time='0150',
                         speed='')
        self.driver.find_element_by_id('input_btn_insert_timestamp').click()
        error_msg = self.driver.find_element_by_id('div_error_msg_js')
        self.assertEqual(error_msg.text,
                         'The maximum desired average speed is blank.')

    def test_timestamp_missing_time(self):
        self.insert_data(file='island_1.gpx',
                         date='01012011',
                         init_time='',
                         speed='1')
        self.driver.find_element_by_id('input_btn_insert_timestamp').click()
        error_msg = self.driver.find_element_by_id('div_error_msg_js')
        self.assertEqual(error_msg.text, 'Time has wrong format.')

    def test_timestamp_missing_date(self):
        self.insert_data(file='island_1.gpx',
                         date='',
                         init_time='0150',
                         speed='1')
        self.driver.find_element_by_id('input_btn_insert_timestamp').click()
        error_msg = self.driver.find_element_by_id('div_error_msg_js')
        self.assertEqual(error_msg.text, 'Date has wrong format.')

    def test_timestamp_high_speed(self):
        self.insert_data(file='island_1.gpx',
                         date='01012011',
                         init_time='0150',
                         speed='500')
        self.driver.find_element_by_id('input_btn_insert_timestamp').click()
        error_msg = self.driver.find_element_by_id('div_error_msg_js')
        self.assertEqual(
            error_msg.text,
            f'The maximum desired average speed cannot exceed {c.maximum_speed} km/h.')

    def test_timestamp_low_speed(self):
        self.insert_data(file='island_1.gpx',
                         date='01012011',
                         init_time='0150',
                         speed='0')
        self.driver.find_element_by_id('input_btn_insert_timestamp').click()
        error_msg = self.driver.find_element_by_id('div_error_msg_js')
        self.assertEqual(error_msg.text,
                         'The maximum desired average speed must be > 0 km/h.')
