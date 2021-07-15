import os
import time
from urllib.parse import urljoin
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from glob import glob

import TrackApp.constants as c
from TrackApp.utils import md5sum
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
            {'download.default_directory':  self.downloads_dir,
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

    def test_login(self):
        self.login(driver=self.driver,
                   live_server_url=self.live_server_url,
                   username='default_user',
                   password='default_password_1234')

        self.assertEqual(self.driver.current_url.rstrip('/'), self.live_server_url)
        # TODO extra check is needed to verify that there is a logged user

    def test_log_out(self):
        self.login(driver=self.driver,
                   live_server_url=self.live_server_url,
                   username='default_user',
                   password='default_password_1234')

        link = self.driver.find_element_by_id('a_logout')
        link.click()
        self.assertEqual(self.driver.current_url.rstrip('/'), self.live_server_url)
        # TODO extra check is needed to verify that there is no logged user

    def test_combine_tracks(self):
        # Remove previous testing files
        for file in glob(os.path.join(self.downloads_dir, 'TrackEditor*.gpx')):
            os.remove(file)

        self.driver.get(urljoin(self.live_server_url, 'combine_tracks'))

        self.driver.\
            find_element_by_id('select-file-1').\
            send_keys(os.path.join(self.test_path,
                                   'samples',
                                   'Inaccessible_Island_part1.gpx'))

        self.driver.\
            find_element_by_id('select-file-2').\
            send_keys(os.path.join(self.test_path,
                                   'samples',
                                   'Inaccessible_Island_part2.gpx'))

        self.driver.find_element_by_id('input_btn_combine').click()
        self.driver.find_element_by_id('input_btn_download').click()
        time.sleep(2)  # some time is needed to download the file

        downloaded_file = \
            glob(os.path.join(self.downloads_dir, 'TrackEditor*.gpx'))[-1]

        self.assertTrue(
            md5sum(downloaded_file),
            'd0730d6a0d813b3b62b11f58ff3b9edb')

    def test_insert_time(self):
        # Remove previous testing files
        for file in glob(os.path.join(self.downloads_dir,
                                      'TrackEditor_insert_timestamp_*.gpx')):
            os.remove(file)

        self.driver.get(urljoin(self.live_server_url, 'insert_timestamp'))

        self.driver.\
            find_element_by_id('select-file-1').\
            send_keys(os.path.join(self.test_path,
                                   'samples',
                                   'bike_ride.gpx'))

        self.driver.find_element_by_id('input_date').send_keys('01012011')
        if os.name == 'nt':
            self.driver.find_element_by_id('input_time').send_keys('0150')
        else:
            self.driver.find_element_by_id('input_time').send_keys('0150AM')
        self.driver.find_element_by_id('input_desired_speed').send_keys('15')
        self.driver.find_element_by_id('span_checkmark').click()

        self.driver.find_element_by_id('input_btn_insert_timestamp').click()
        time.sleep(1)  # processing time
        self.driver.find_element_by_id('input_btn_download').click()
        time.sleep(2)  # time to download file

        downloaded_file = \
            glob(os.path.join(self.downloads_dir,
                              'TrackEditor_insert_timestamp_*.gpx'))[-1]

        self.assertEqual(
            md5sum(downloaded_file),
            '5db822d744c323d6b17b0e78ddc4e6bb')


class CombineTracksTest(StaticLiveServerTestCase):
    def setUp(self):
        options = webdriver.ChromeOptions()
        options.headless = True
        self.driver = webdriver.Chrome(chrome_options=options)
        self.test_path = os.path.dirname(__file__)
        self.driver.get(urljoin(self.live_server_url, 'combine_tracks'))

    def tearDown(self):
        self.driver.quit()

    def test_upload_too_many_tracks(self):
        for i in range(1, 6):
            self.driver.\
                find_element_by_id(f'select-file-{i}').\
                send_keys(os.path.join(self.test_path,
                                       'samples',
                                       f'Inaccessible_Island_part{i}.gpx'))
        self.driver.\
            find_element_by_id('select-file-6').\
            send_keys(os.path.join(self.test_path,
                                   'samples',
                                   'basic_sample.gpx'))

        error_msg = self.driver.find_element_by_id('div_error_msg_js')

        self.assertEqual(error_msg.text, 'No more than 5 files are allowed.')

    def test_upload_wrong_extension(self):
        self.driver.\
            find_element_by_id('select-file-1').\
            send_keys(os.path.join(self.test_path,
                                   'samples',
                                   'wrong_extension.txt'))

        error_msg = self.driver.find_element_by_id('div_error_msg_js')

        self.assertEqual(
            error_msg.text,
            "Extension for wrong_extension.txt is not valid ['gpx']")

    def test_upload_repeated_files(self):
        for i in range(1, 3):
            self.driver. \
                find_element_by_id(f'select-file-{i}'). \
                send_keys(os.path.join(self.test_path,
                                       'samples',
                                       'Inaccessible_Island_part1.gpx'))

        error_msg = self.driver.find_element_by_id('div_error_msg_js')

        self.assertEqual(
            error_msg.text,
            'Repeated file is selected: Inaccessible_Island_part1.gpx')

    def test_upload_big_file(self):
        self.driver. \
            find_element_by_id('select-file-1'). \
            send_keys(os.path.join(self.test_path,
                                   'samples',
                                   'over_10mb.gpx'))

        error_msg = self.driver.find_element_by_id('div_error_msg_js')

        self.assertEqual(
            error_msg.text,
            'File over_10mb.gpx is 14 Mb. It must be smaller than 10 Mb')

    def test_combine_no_file(self):
        self.driver.find_element_by_id('input_btn_combine').click()
        warning_msg = self.driver.find_element_by_id('div_warning_msg')

        self.assertEqual(warning_msg.text, 'No file has been selected.')

    def test_bad_formed_file(self):
        self.driver. \
            find_element_by_id('select-file-1'). \
            send_keys(os.path.join(self.test_path,
                                   'samples',
                                   'bad_formed.gpx'))

        self.driver.find_element_by_id('input_btn_combine').click()
        error_msg = self.driver.find_element_by_id('div_error_msg')
        self.assertEqual(error_msg.text, 'Error loading files')


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

    def insert_data(self, file, date, time, speed):
        if file:
            self.driver.\
                find_element_by_id('select-file-1').\
                send_keys(os.path.join(self.test_path, 'samples', file))

        if date:
            self.driver.find_element_by_id('input_date').send_keys(date)

        if time:
            if os.name == 'posix':
                if int(time[:2]) > 12:
                    time += 'AM'
                else:
                    time += 'PM'
            self.driver.find_element_by_id('input_time').send_keys(time)

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
                         time='0150',
                         speed='1')
        self.driver.find_element_by_id('input_btn_insert_timestamp').click()
        error_msg = self.driver.find_element_by_id('div_error_msg_js')
        self.assertEqual(error_msg.text, 'No file has been selected.')

    def test_bad_formed_file(self):
        self.insert_data(file='bad_formed.gpx',
                         date='01012011',
                         time='0150',
                         speed='1')

        self.driver.find_element_by_id('input_btn_insert_timestamp').click()
        time.sleep(1)
        
        error_msg = self.driver.find_element_by_id('div_error_msg')
        self.assertEqual(error_msg.text, 'Error loading files')

    def test_missing_desired_speed(self):
        self.insert_data(file='Inaccessible_Island_part1.gpx',
                         date='01012011',
                         time='0150',
                         speed=None)
        self.driver.find_element_by_id('input_btn_insert_timestamp').click()
        error_msg = self.driver.find_element_by_id('div_error_msg_js')
        self.assertEqual(error_msg.text,
                         'The maximum desired average speed is blank.')

    def test_missing_time(self):
        self.insert_data(file='Inaccessible_Island_part1.gpx',
                         date='01012011',
                         time=None,
                         speed='1')
        self.driver.find_element_by_id('input_btn_insert_timestamp').click()
        error_msg = self.driver.find_element_by_id('div_error_msg_js')
        self.assertEqual(error_msg.text, 'Time has wrong format.')
        time.sleep(5)

    def test_missing_date(self):
        self.insert_data(file='Inaccessible_Island_part1.gpx',
                         date=None,
                         time='0150',
                         speed='1')
        self.driver.find_element_by_id('input_btn_insert_timestamp').click()
        error_msg = self.driver.find_element_by_id('div_error_msg_js')
        self.assertEqual(error_msg.text, 'Date has wrong format.')

    def test_high_speed(self):
        self.insert_data(file='Inaccessible_Island_part1.gpx',
                         date='01012011',
                         time='0150',
                         speed='500')
        self.driver.find_element_by_id('input_btn_insert_timestamp').click()
        error_msg = self.driver.find_element_by_id('div_error_msg_js')
        self.assertEqual(
            error_msg.text,
            f'The maximum desired average speed cannot exceed {c.maximum_speed} km/h.')

    def test_low_speed(self):
        self.insert_data(file='Inaccessible_Island_part1.gpx',
                         date='01012011',
                         time='0150',
                         speed='0')
        self.driver.find_element_by_id('input_btn_insert_timestamp').click()
        error_msg = self.driver.find_element_by_id('div_error_msg_js')
        self.assertEqual(error_msg.text,
                         'The maximum desired average speed must be > 0 km/h.')
