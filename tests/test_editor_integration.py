# flake8: noqa: W504
import os
import json
import time
from urllib.parse import urljoin
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from glob import glob

import libs.track as track
from libs.utils import md5sum
import TrackApp.models as models


class EditorIntegrationTest(StaticLiveServerTestCase):
    """
    Integration tests for the editor functionality. These tests are done with
    selenium, so they directly use the front-end as io interface.
    """

    def login(self, username, password):
        self.driver.get(urljoin(self.live_server_url, 'login'))
        self.driver.find_element_by_id('input_txt_username').send_keys(username)
        self.driver.find_element_by_id('input_txt_password').send_keys(password)
        self.driver.find_element_by_id('input_btn_login').click()

    def create_user(self,
                    username='default_user',
                    password='default_password_1234',
                    email='default_user@example.com'):
        if not models.User.objects.filter(username=username):
            user = models.User.objects.create(username=username,
                                              email=email,
                                              password='!')
            user.set_password(password)
            user.save()
        else:
            user = models.User.objects.get(username=username)
        return user

    def setUp(self):
        # Selenium configuration
        options = webdriver.ChromeOptions()
        options.headless = True
        self.downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        preferences = \
            {'download.default_directory': self.downloads_dir,
             'safebrowsing.enabled': 'false'}
        options.add_experimental_option('prefs', preferences)

        self.driver = webdriver.Chrome(chrome_options=options)

        # Test configuration
        self.test_path = os.path.dirname(__file__)
        self.user = self.create_user()

        # Open editor
        self.login(username='default_user',
                   password='default_password_1234')
        self.driver.get(urljoin(self.live_server_url, 'editor'))

    def tearDown(self):
        self.driver.quit()

    def test_save_session(self):
        """
        Save session in web browser and compare versus direct use of track
        object.
        """
        sample_file = os.path.join(self.test_path,
                                   'samples',
                                   'simple_numbers.gpx')
        self.driver.find_element_by_id('select-file').send_keys(sample_file)
        WebDriverWait(self.driver, 5).\
            until(EC.invisibility_of_element_located((By.ID, 'div_spinner')))

        self.driver.find_element_by_id('btn_save').click()
        WebDriverWait(self.driver, 5).\
            until(EC.invisibility_of_element_located((By.ID, 'div_spinner')))

        saved_track = models.Track.objects.filter(user=self.user).\
            order_by('-last_edit')[0]
        saved_track = json.loads(saved_track.track)
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
        sample_file = os.path.join(self.test_path,
                                   'samples',
                                   'simple_numbers.gpx')
        self.driver.find_element_by_id('select-file').send_keys(sample_file)
        WebDriverWait(self.driver, 5).\
            until(EC.invisibility_of_element_located((By.ID, 'div_spinner')))

        self.driver.find_element_by_id('select-file').send_keys(sample_file)
        WebDriverWait(self.driver, 5).\
            until(EC.invisibility_of_element_located((By.ID, 'div_spinner')))

        # Delete track
        WebDriverWait(self.driver, 1).\
            until(EC.visibility_of_element_located((By.ID, 'btn_remove_1')))
        self.driver.find_element_by_id('btn_remove_1').click()
        time.sleep(0.2)  # js code to be executed behind

        self.driver.find_element_by_id('btn_save').click()
        WebDriverWait(self.driver, 5).\
            until(EC.invisibility_of_element_located((By.ID, 'div_spinner')))

        saved_track = models.Track.objects.filter(user=self.user).\
            order_by('-last_edit')[0]
        saved_track = json.loads(saved_track.track)
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
        sample_file = os.path.join(self.test_path,
                                   'samples',
                                   'simple_numbers.gpx')
        self.driver.find_element_by_id('select-file').send_keys(sample_file)
        WebDriverWait(self.driver, 5).\
            until(EC.invisibility_of_element_located((By.ID, 'div_spinner')))

        # Rename
        element = self.driver.find_element_by_id('span_rename_1')
        element.click()
        self.driver.execute_script(
            "arguments[0].innerText = 'simple_numbers.gpx'", element)
        self.driver.find_element_by_xpath("//html").click()

        self.driver.find_element_by_id('btn_save').click()
        WebDriverWait(self.driver, 5).\
            until(EC.invisibility_of_element_located((By.ID, 'div_spinner')))

        saved_track = models.Track.objects.filter(user=self.user).\
            order_by('-last_edit')[0]
        saved_track = json.loads(saved_track.track)
        obj_track = track.Track()
        obj_track.add_gpx(sample_file)
        reference_track = json.loads(obj_track.to_json())

        self.assertEqual(saved_track, reference_track)

    def test_rename_and_download_session(self):
        """
        Load two tracks, rename the session and download. The product file is
        compared versus reference.
        """
        # Remove previous testing files
        for file in glob(os.path.join(self.downloads_dir, 'test_download_session*.gpx')):
            os.remove(file)

        # Add files
        for i in range(1, 3):
            sample_file = os.path.join(self.test_path,
                                       'samples',
                                       f'island_{i}.gpx')
            self.driver.find_element_by_id('select-file').send_keys(sample_file)
            WebDriverWait(self.driver, 5).\
                until(EC.invisibility_of_element_located((By.ID, 'div_spinner')))

        # Rename session
        e_session_name = self.driver.find_element_by_id('h_session_name')
        e_session_name.click()
        self.driver.execute_script(
            "arguments[0].innerText = 'test_download_session'", e_session_name)
        self.driver.find_element_by_xpath("//html").click()
        time.sleep(0.5)  # small time to rename session

        # Download file
        self.driver.find_element_by_id('btn_download').click()
        WebDriverWait(self.driver, 5).\
            until(EC.invisibility_of_element_located((By.ID, 'div_spinner')))
        time.sleep(2)

        downloaded_file = \
            glob(os.path.join(self.downloads_dir, 'test_download_session*.gpx'))[-1]

        self.assertEqual(
            md5sum(downloaded_file),
            md5sum(os.path.join(self.test_path,
                                'references',
                                'test_combine_tracks.gpx')
                   )
        )
