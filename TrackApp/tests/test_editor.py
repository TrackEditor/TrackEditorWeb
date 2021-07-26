import os
import json
import time
from urllib.parse import urljoin
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver

import TrackApp.track as track
import TrackApp.models as models


class EditorTest(StaticLiveServerTestCase):

    def login(self, driver, live_server_url, username, password):
        driver.get(urljoin(live_server_url, 'login'))
        driver.find_element_by_id('input_txt_username').send_keys(username)
        driver.find_element_by_id('input_txt_password').send_keys(password)
        driver.find_element_by_id('input_btn_login').click()

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
            {'download.default_directory':  self.downloads_dir,
             'safebrowsing.enabled': 'false'}
        options.add_experimental_option('prefs', preferences)

        self.driver = webdriver.Chrome(chrome_options=options)

        # Test configuration
        self.test_path = os.path.dirname(__file__)
        self.user = self.create_user()

        # Open editor
        self.login(driver=self.driver,
                   live_server_url=self.live_server_url,
                   username='default_user',
                   password='default_password_1234')
        self.driver.get(urljoin(self.live_server_url, 'editor'))

    def tearDown(self):
        self.driver.quit()

    def test_save_session(self):
        sample_file = os.path.join(self.test_path, 'samples', 'simple_numbers.gpx')
        self.driver.find_element_by_id('select-file').send_keys(sample_file)
        time.sleep(2)

        self.driver.find_element_by_id('btn_save').click()
        time.sleep(3)

        saved_track = models.Track.objects.filter(user=self.user).order_by('-last_edit')[0]
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
        sample_file = os.path.join(self.test_path, 'samples', 'simple_numbers.gpx')
        self.driver.find_element_by_id('select-file').send_keys(sample_file)
        time.sleep(2)
        self.driver.find_element_by_id('select-file').send_keys(sample_file)
        time.sleep(2)

        # Delete track
        self.driver.find_element_by_id('btn_remove_0').click()
        time.sleep(0.1)
        self.driver.find_element_by_id('btn_save').click()
        time.sleep(3)

        saved_track = models.Track.objects.filter(user=self.user).order_by('-last_edit')[0]
        saved_track = json.loads(saved_track.track)
        obj_track = track.Track()
        obj_track.add_gpx(sample_file)
        reference_track = json.loads(obj_track.to_json())

        for k in saved_track:
            if k == 'segment_names':
                for saved, reference in zip(saved_track[k], reference_track[k]):
                    self.assertIn(os.path.splitext(reference)[0], saved)
            elif k == 'last_segment_idx':
                self.assertEqual(saved_track[k], 2)
            elif k == 'segment':
                self.assertEqual(saved_track[k], [2] * 5)
            else:
                self.assertEqual(saved_track[k], reference_track[k])

    def test_rename_segment(self):
        sample_file = os.path.join(self.test_path, 'samples', 'simple_numbers.gpx')
        self.driver.find_element_by_id('select-file').send_keys(sample_file)
        time.sleep(2)

        # Rename
        element = self.driver.find_element_by_id('span_rename_0')
        element.click()
        self.driver.execute_script("arguments[0].innerText = 'simple_numbers.gpx'", element)
        self.driver.find_element_by_xpath("//html").click()
        time.sleep(1)

        self.driver.find_element_by_id('btn_save').click()
        time.sleep(3)

        saved_track = models.Track.objects.filter(user=self.user).order_by('-last_edit')[0]
        saved_track = json.loads(saved_track.track)
        obj_track = track.Track()
        obj_track.add_gpx(sample_file)
        reference_track = json.loads(obj_track.to_json())

        self.assertEqual(saved_track, reference_track)
