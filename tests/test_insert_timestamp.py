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


class ViewsTest(StaticLiveServerTestCase):

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

    def test_insert_time(self):
        self.login(driver=self.driver,
                   live_server_url=self.live_server_url,
                   username='default_user',
                   password='default_password_1234')

        # Remove previous testing files
        for file in glob(os.path.join(self.downloads_dir,
                                      'TrackEditor_insert_timestamp_*.gpx')):
            os.remove(file)

        self.driver.get(urljoin(self.live_server_url, 'insert_timestamp'))

        self.driver.\
            find_element_by_id('select-file-1').\
            send_keys(os.path.join(self.test_path,
                                   'samples',
                                   'island_full.gpx'))

        self.driver.find_element_by_id('input_date').send_keys('01012011')
        if os.name == 'nt':
            self.driver.find_element_by_id('input_time').send_keys('0150')
        else:
            self.driver.find_element_by_id('input_time').send_keys('0150AM')
        self.driver.find_element_by_id('input_desired_speed').send_keys('15')
        self.driver.find_element_by_id('span_checkmark').click()

        self.driver.find_element_by_id('input_btn_insert_timestamp').click()
        WebDriverWait(self.driver, 5).\
            until(EC.invisibility_of_element_located((By.ID, 'div_spinner')))

        self.driver.find_element_by_id('input_btn_download').click()
        time.sleep(2)  # time to download file

        downloaded_file = \
            glob(os.path.join(self.downloads_dir,
                              'TrackEditor_insert_timestamp_*.gpx'))[-1]

        self.assertEqual(
            md5sum(downloaded_file),
            md5sum(os.path.join(self.test_path,
                                'references',
                                'test_insert_time.gpx')
                   )
        )
        self.assertIsNotNone(self.driver.find_element_by_id('js-map'))


class InsertTimestampTest(StaticLiveServerTestCase):
    def setUp(self):
        # Firefox does not properly work to input date and time with selenium
        options = webdriver.ChromeOptions()
        options.headless = True
        self.driver = webdriver.Chrome(chrome_options=options)
        self.test_path = os.path.dirname(__file__)
        self.driver.get(urljoin(self.live_server_url, 'insert_timestamp'))

    def tearDown(self):
        self.driver.quit()

    def insert_data(self, file, date, init_time, speed):
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

    def test_upload_wrong_extension(self):
        self.driver.\
            find_element_by_id('select-file-1').\
            send_keys(os.path.join(self.test_path,
                                   'samples',
                                   'wrong_extension.txt'))

        error_msg = self.driver.find_element_by_id('div_error_msg_js')

        self.assertEqual(
            error_msg.text,
            "Extension for wrong_extension.txt is not valid ['gpx'].")

    def test_no_file(self):
        self.insert_data(file=None,
                         date='01012011',
                         init_time='0150',
                         speed='1')
        self.driver.find_element_by_id('input_btn_insert_timestamp').click()
        error_msg = self.driver.find_element_by_id('div_error_msg_js')
        self.assertEqual(error_msg.text, 'No file has been selected.')

    def test_bad_formed_file(self):
        self.insert_data(file='bad_formed.gpx',
                         date='01012011',
                         init_time='0150',
                         speed='1')

        self.driver.find_element_by_id('input_btn_insert_timestamp').click()
        WebDriverWait(self.driver, 5).\
            until(EC.invisibility_of_element_located((By.ID, 'div_spinner')))

        error_msg = self.driver.find_element_by_id('div_error_msg')
        self.assertEqual(error_msg.text, 'Error loading files')

    def test_missing_desired_speed(self):
        self.insert_data(file='island_1.gpx',
                         date='01012011',
                         init_time='0150',
                         speed=None)
        self.driver.find_element_by_id('input_btn_insert_timestamp').click()
        error_msg = self.driver.find_element_by_id('div_error_msg_js')
        self.assertEqual(error_msg.text,
                         'The maximum desired average speed is blank.')

    def test_missing_time(self):
        self.insert_data(file='island_1.gpx',
                         date='01012011',
                         init_time=None,
                         speed='1')
        self.driver.find_element_by_id('input_btn_insert_timestamp').click()
        error_msg = self.driver.find_element_by_id('div_error_msg_js')
        self.assertEqual(error_msg.text, 'Time has wrong format.')

    def test_missing_date(self):
        self.insert_data(file='island_1.gpx',
                         date=None,
                         init_time='0150',
                         speed='1')
        self.driver.find_element_by_id('input_btn_insert_timestamp').click()
        error_msg = self.driver.find_element_by_id('div_error_msg_js')
        self.assertEqual(error_msg.text, 'Date has wrong format.')

    def test_high_speed(self):
        self.insert_data(file='island_1.gpx',
                         date='01012011',
                         init_time='0150',
                         speed='500')
        self.driver.find_element_by_id('input_btn_insert_timestamp').click()
        error_msg = self.driver.find_element_by_id('div_error_msg_js')
        self.assertEqual(
            error_msg.text,
            f'The maximum desired average speed cannot exceed {c.maximum_speed} km/h.')

    def test_low_speed(self):
        self.insert_data(file='island_1.gpx',
                         date='01012011',
                         init_time='0150',
                         speed='0')
        self.driver.find_element_by_id('input_btn_insert_timestamp').click()
        error_msg = self.driver.find_element_by_id('div_error_msg_js')
        self.assertEqual(error_msg.text,
                         'The maximum desired average speed must be > 0 km/h.')
