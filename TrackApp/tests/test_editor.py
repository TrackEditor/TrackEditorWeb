import os
import json
import time
from urllib.parse import urljoin
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase, RequestFactory
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


import TrackApp.track as track
import TrackApp.models as models
import TrackApp.views as views


class EditorIntegrationTest(StaticLiveServerTestCase):

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
            {'download.default_directory': self.downloads_dir,
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


class EditorAPITest(TestCase):
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
        return user, username, password

    def setUp(self):
        self.factory = RequestFactory()
        self.test_path = os.path.dirname(__file__)
        self.user, self.username, self.password = self.create_user()

    def login(self):
        self.client.login(username=self.username,
                          password=self.password)

    def create_session(self):
        response = self.client.get('/editor')
        session = self.client.session
        return response, session

    def get_sample_file(self, filename='simple_numbers.gpx'):
        return os.path.join(self.test_path, 'samples', filename)

    def compare_tracks(self, session_track, reference_track):
        for k in session_track:
            if k == 'segment_names':
                for s, r in zip(session_track[k], reference_track[k]):
                    self.assertIn(os.path.splitext(r)[0], s)
            else:
                self.assertEqual(session_track[k], reference_track[k])

    def test_endpoint(self):
        request = self.factory.get('/editor')
        request.user = self.user
        request.session = {}
        response = views.editor(request)
        self.assertEqual(response.status_code, 200)

    def test_create_session(self):
        self.login()
        response, session = self.create_session()

        self.assertEqual(response.status_code, 200)
        self.assertIn('json_track', session.keys())
        self.assertIn('index_db', session.keys())

    def test_add_gpx(self):
        self.login()
        self.create_session()

        # Add file
        sample_file = self.get_sample_file()
        with open(sample_file, 'r') as f:
            self.client.post('/editor', {'document': f})
        session_track = json.loads(self.client.session['json_track'])

        # Create expected output
        obj_track = track.Track()
        obj_track.add_gpx(sample_file)
        reference_track = json.loads(obj_track.to_json())

        self.compare_tracks(session_track, reference_track)
        self.assertIsNone(self.client.session['index_db'])  # not saved session

    def test_load_session(self):
        self.login()
        self.create_session()

        sample_file = self.get_sample_file()
        with open(sample_file, 'r') as f:
            self.client.post('/editor', {'document': f})

        self.client.post('/editor/save_session',
                         json.dumps({'save': 'True'}),
                         content_type='application/json')

        # Add another file to force that the last active session is not
        # the same than the loaded one
        with open(sample_file, 'r') as f:
            self.client.post('/editor', {'document': f})

        # Load track
        response = self.client.get(f'/editor/{self.client.session["index_db"]}')
        session_track = json.loads(self.client.session['json_track'])

        # Create expected output
        obj_track = track.Track()
        obj_track.add_gpx(sample_file)
        reference_track = json.loads(obj_track.to_json())

        self.compare_tracks(session_track, reference_track)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(self.client.session['index_db'])

    def test_save_session(self):
        self.login()
        self.create_session()

        # Add file
        sample_file = self.get_sample_file()
        with open(sample_file, 'r') as f:
            self.client.post('/editor', {'document': f})
        session_track = json.loads(self.client.session['json_track'])

        # Save session
        response = self.client.post('/editor/save_session',
                                    json.dumps({'save': 'True'}),
                                    content_type='application/json')

        # Get reference data
        saved_track = models.Track.objects.\
            get(id=self.client.session['index_db'])
        saved_track = json.loads(saved_track.track)

        self.assertEqual(session_track, saved_track)
        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(self.client.session['index_db'])

    def test_save_session_wrong_request(self):
        self.login()
        self.create_session()
        response = self.client.post('/editor/save_session',
                                    json.dumps({'save': 'False'}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 492)

    def test_load_session_get(self):
        self.login()
        self.create_session()
        response = self.client.get('/editor/save_session')
        self.assertEqual(response.status_code, 400)

    def test_load_session_no_track(self):
        self.login()
        response = self.client.post('/editor/save_session',
                                    json.dumps({'save': 'False'}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 491)

    # def test_remove_session(self):
    #     raise NotImplementedError

    # def test_rename_session(self):
    #     raise NotImplementedError
