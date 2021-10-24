# flake8: noqa: W504
import os
import json
import time
from urllib.parse import urljoin
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from glob import glob

import libs.track as track
import tests.testing_utils as testing_utils
import TrackApp.models as models


class EditorIntegrationTest(StaticLiveServerTestCase):
    """
    Integration tests for the editor functionality. These tests are done with
    selenium, so they directly use the front-end as io interface.
    """

    def setUp(self):
        self.driver = testing_utils.get_webdriver(headless=True)
        self.downloads_dir = testing_utils.get_downloads_dir()

        # Test configuration
        self.test_path = os.path.dirname(__file__)
        self.user = testing_utils.create_user()

        # Open editor
        testing_utils.login(driver=self.driver,
                            live_server_url=self.live_server_url,
                            username='default_user',
                            password='default_password_1234')
        self.driver.get(urljoin(self.live_server_url, 'editor'))
        time.sleep(5)  # wait to load map and elevation

    def tearDown(self):
        self.driver.quit()

    def wait_spinner(self, timeout=5):
        WebDriverWait(self.driver, timeout).\
            until(EC.invisibility_of_element_located((By.ID, 'div_spinner')))

    def add_gpx(self, sample_file):
        self.driver.find_element_by_id('select-file').send_keys(sample_file)
        self.wait_spinner()
        time.sleep(3)  # wait while page is reloaded

    def save(self):
        self.driver.find_element_by_id('btn_save').click()
        self.wait_spinner()
        return models.Track.objects.filter(user=self.user).order_by('-last_edit')[0]

    def download(self, pattern):
        self.driver.find_element_by_id('btn_download').click()
        self.wait_spinner()
        time.sleep(5)

        downloaded_file = glob(os.path.join(self.downloads_dir, pattern))[-1]
        return downloaded_file

    def rename_segment(self, index, new_name):
        WebDriverWait(self.driver, 10). \
            until(
            EC.visibility_of_element_located((By.ID, f'span_rename_{index}')))
        element = self.driver.find_element_by_id(f'span_rename_{index}')
        element.click()
        self.driver.execute_script(
            f"arguments[0].innerText = '{new_name}'", element)
        element.send_keys(Keys.ENTER)

    def remove_segment(self, index):
        WebDriverWait(self.driver, 5).\
            until(EC.visibility_of_element_located((By.ID, f'btn_remove_{index}')))
        self.driver.find_element_by_id(f'btn_remove_{index}').click()
        self.wait_spinner()
        time.sleep(1)  # js code to be executed behind

    def rename_session(self, new_title):
        e_session_name = self.driver.find_element_by_id('h_session_name')
        e_session_name.click()
        self.driver.execute_script(
            f"arguments[0].innerText = '{new_title}'",
            e_session_name)
        e_session_name.send_keys(Keys.ENTER)
        time.sleep(0.5)  # small time to rename session

    def remove_downloads(self, pattern):
        # Remove previous testing files
        for file in glob(os.path.join(self.downloads_dir, pattern)):
            os.remove(file)

    def test_save_session(self):
        """
        Save session in web browser and compare versus direct use of track
        object.
        """
        # Include files
        sample_file = os.path.join(self.test_path,
                                   'samples',
                                   'simple_numbers.gpx')
        self.add_gpx(sample_file)

        # Save session
        saved_session = self.save()
        saved_track = json.loads(saved_session.track)

        # Replicate session
        obj_track = track.Track()
        obj_track.add_gpx(sample_file)
        reference_track = json.loads(obj_track.to_json())

        for k in saved_track:
            if k == 'segment_names':
                for saved, reference in zip(saved_track[k], reference_track[k]):
                    self.assertIn(os.path.splitext(reference)[0], saved)
            else:
                self.assertEqual(saved_track[k], reference_track[k])

    def test_remove_segment(self):
        """
        Remove segment in web browser and compare versus direct use of track
        object.
        """
        # Include files
        for _ in range(2):
            sample_file = os.path.join(self.test_path,
                                       'samples',
                                       'simple_numbers.gpx')
            self.add_gpx(sample_file)

        # Delete track
        self.remove_segment(1)
        saved_session = self.save()
        saved_track = json.loads(saved_session.track)

        # Replicate session
        obj_track = track.Track()
        obj_track.add_gpx(sample_file)
        reference_track = json.loads(obj_track.to_json())

        for k in saved_track:
            if k == 'segment_names':
                saved_track[k] = [s for s in saved_track[k] if s]
                for saved, reference in zip(saved_track[k], reference_track[k]):
                    self.assertIn(os.path.splitext(reference)[0], saved)
            elif k == 'last_segment_idx':
                self.assertEqual(saved_track[k], 2)
            elif k == 'segment':
                self.assertEqual(saved_track[k], [2] * 5)
            else:
                self.assertEqual(saved_track[k], reference_track[k])

    def test_rename_segment(self):
        """
        Rename segment in web browser and compare versus direct use of track
        object.
        """
        # Include files
        sample_file = os.path.join(self.test_path,
                                   'samples',
                                   'simple_numbers.gpx')
        self.add_gpx(sample_file)

        # Rename
        self.rename_segment(1, 'simple_numbers.gpx')
        saved_session = self.save()
        saved_track = json.loads(saved_session.track)

        # Replicate session
        obj_track = track.Track()
        obj_track.add_gpx(sample_file)
        reference_track = json.loads(obj_track.to_json())

        self.assertEqual(saved_track, reference_track)

    def test_rename_and_download_session(self):
        """
        Load two tracks, rename the session and download. The product file is
        compared versus reference.
        """
        self.remove_downloads(pattern='test_rename_and_download_session*.gpx')

        # Add files
        for i in range(1, 3):
            sample_file = os.path.join(self.test_path,
                                       'samples',
                                       f'island_{i}.gpx')
            self.add_gpx(sample_file)

        # Rename and download
        self.rename_session(new_title='test_rename_and_download_session')
        downloaded_file = self.download(pattern='test_rename_and_download_session*.gpx')

        # Replicate session
        sample_file = os.path.join(self.test_path, 'references', 'test_combine_tracks.gpx')

        self.assertTrue(
            testing_utils.compare_tracks(downloaded_file, sample_file))

    def test_editor_non_logged(self):
        """
        Editor is not available for non logged users. Logout before accesing to
        editor.
        """
        self.driver.get(self.live_server_url)
        self.driver.find_element_by_id('a_logout').click()

        link = self.driver.find_element_by_id('a_editor')
        link.click()

        warning_msg = self.driver.find_element_by_id('div_warning_msg')

        self.assertIn('only available for users', warning_msg.text)

        self.assertEqual(self.driver.current_url.rstrip('/'),
                         urljoin(self.live_server_url, 'users_only'))

    def test_editor_logged(self):
        """
        Editor for logged users is available
        """
        self.driver.get(self.live_server_url)

        link = self.driver.find_element_by_id('a_editor')
        link.click()
        self.assertEqual(self.driver.current_url.rstrip('/'),
                         urljoin(self.live_server_url, 'editor'))
