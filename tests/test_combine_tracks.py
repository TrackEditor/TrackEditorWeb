import os
import time
from urllib.parse import urljoin
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from glob import glob
from selenium.common.exceptions import NoSuchElementException

import tests.testing_utils as testing_utils


class CombineTracksIntegrationTest(StaticLiveServerTestCase):

    def setUp(self):
        self.driver = testing_utils.get_webdriver(headless=True)
        self.test_path = os.path.dirname(__file__)
        self.user = testing_utils.create_user()
        self.downloads_dir = testing_utils.get_downloads_dir()
        self.driver.get(urljoin(self.live_server_url, 'combine_tracks'))

        # Remove previous testing files
        for file in glob(os.path.join(self.downloads_dir,
                                      'TrackEditor_combine_tracks*.gpx')):
            os.remove(file)

    def tearDown(self):
        self.driver.quit()

    def test_combine_tracks(self):
        self.driver. \
            find_element_by_id('select-file-1'). \
            send_keys(os.path.join(self.test_path,
                                   'samples',
                                   'island_1.gpx'))

        self.driver. \
            find_element_by_id('select-file-2'). \
            send_keys(os.path.join(self.test_path,
                                   'samples',
                                   'island_2.gpx'))

        self.driver.find_element_by_id('input_btn_combine').click()
        self.driver.find_element_by_id('input_btn_download').click()
        time.sleep(2)  # wait download
        downloaded_file = \
            glob(os.path.join(self.downloads_dir,
                              'TrackEditor_combine_tracks*.gpx'))[-1]
        sample_file = os.path.join(self.test_path, 'references', 'test_combine_tracks.gpx')

        self.assertTrue(
            testing_utils.compare_tracks(downloaded_file, sample_file))
        self.assertRaises(NoSuchElementException,
                          self.driver.find_element_by_id,
                          'js-map')

    def test_combine_tracks_logged_user(self):
        testing_utils.login(driver=self.driver,
                            live_server_url=self.live_server_url,
                            username='default_user',
                            password='default_password_1234')

        self.driver.get(urljoin(self.live_server_url, 'combine_tracks'))

        self.driver.\
            find_element_by_id('select-file-1').\
            send_keys(os.path.join(self.test_path,
                                   'samples',
                                   'island_1.gpx'))

        self.driver.\
            find_element_by_id('select-file-2').\
            send_keys(os.path.join(self.test_path,
                                   'samples',
                                   'island_2.gpx'))

        self.driver.find_element_by_id('input_btn_combine').click()
        self.driver.find_element_by_id('input_btn_download').click()
        time.sleep(2)  # wait download
        downloaded_file = \
            glob(os.path.join(self.downloads_dir, 'TrackEditor_combine_tracks*.gpx'))[-1]
        sample_file = os.path.join(self.test_path, 'references', 'test_combine_tracks.gpx')

        self.assertTrue(
            testing_utils.compare_tracks(downloaded_file, sample_file))
        self.assertTrue(
            self.driver.find_element_by_id('js-map').is_displayed())
        self.assertTrue(
            self.driver.find_element_by_class_name('ol-viewport').is_displayed())

    def test_upload_too_many_tracks(self):
        for i in range(1, 6):
            self.driver.\
                find_element_by_id(f'select-file-{i}').\
                send_keys(os.path.join(self.test_path,
                                       'samples',
                                       f'island_{i}.gpx'))
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
                                       'island_1.gpx'))

        error_msg = self.driver.find_element_by_id('div_error_msg_js')

        self.assertEqual(
            error_msg.text,
            'Repeated file is selected: island_1.gpx')

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
