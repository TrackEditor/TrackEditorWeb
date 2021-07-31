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
    """
    Test the editor API functions from views. All the available operations for
    the user are tested. These operations are commanded from the JS code.
    """
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

    def test_create_session(self):
        """
        Check that empty session is created
        """
        self.login()
        response, session = self.create_session()

        self.assertEqual(response.status_code, 200)
        self.assertIn('json_track', session.keys())
        self.assertIn('index_db', session.keys())

    def test_add_gpx(self):
        """
        Add one gpx file and check it is included in session
        """
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
        """
        Create a session with one track, save it and load it
        """
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
        """
        Create a session with one track and save it
        """
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

    def test_save_add_save(self):
        """
        Create and save session with one gpx file. Add a new one, save and
        check that the db record is properly updated.
        """
        self.login()
        self.create_session()

        sample_file = self.get_sample_file()
        with open(sample_file, 'r') as f:
            self.client.post('/editor', {'document': f})
        self.client.post('/editor/save_session',
                         json.dumps({'save': 'True'}),
                         content_type='application/json')

        with open(sample_file, 'r') as f:
            self.client.post('/editor', {'document': f})
        self.client.post('/editor/save_session',
                         json.dumps({'save': 'True'}),
                         content_type='application/json')

        # Load track
        response = self.client.get(f'/editor/{self.client.session["index_db"]}')
        session_track = json.loads(self.client.session['json_track'])

        # Create expected output
        obj_track = track.Track()
        obj_track.add_gpx(sample_file)
        obj_track.add_gpx(sample_file)
        reference_track = json.loads(obj_track.to_json())

        self.compare_tracks(session_track, reference_track)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(self.client.session['index_db'])

    def test_save_remove_save(self):
        """
        Create and save session with five gpx file. Remove some, save and check
        that the db record is properly updated.
        """
        self.login()
        self.create_session()

        # Load files and save session
        for i in range(1, 6):
            sample_file = self.get_sample_file(f'Inaccessible_Island_part{i}.gpx')
            with open(sample_file, 'r') as f:
                self.client.post('/editor', {'document': f})

            self.client.post('/editor/rename_segment',
                             json.dumps({'index': i - 1,
                                         'new_name': os.path.basename(sample_file)}),
                             content_type='application/json')

        self.client.post('/editor/rename_session',
                         json.dumps({'new_name': 'test_save_remove_save'}),
                         content_type='application/json')

        self.client.post('/editor/save_session',
                         json.dumps({'save': 'True'}),
                         content_type='application/json')

        # Remove segments and save
        self.client.post('/editor/remove_segment',
                         json.dumps({'index': 2}),
                         content_type='application/json')

        self.client.post('/editor/remove_segment',
                         json.dumps({'index': 4}),
                         content_type='application/json')

        self.client.post('/editor/save_session',
                         json.dumps({'save': 'True'}),
                         content_type='application/json')

        # Load db record
        track_db = json.loads(models.Track.objects.get(id=self.client.session['index_db']).track)

        self.assertEqual(set(track_db['segment']), {1, 3, 5})
        self.assertEqual(track_db['segment_names'],
                         ['Inaccessible_Island_part1.gpx', None,
                          'Inaccessible_Island_part3.gpx', None,
                          'Inaccessible_Island_part5.gpx'])

    def test_save_rename_save(self):
        """
        Create and save session with one gpx file. Add a new one, save an check
        that the db record is properly updated.
        """
        self.login()
        self.create_session()

        self.client.post('/editor/save_session',
                         json.dumps({'save': 'True'}),
                         content_type='application/json')

        self.client.post('/editor/rename_session',
                         json.dumps({'new_name': 'test_save_rename_save'}),
                         content_type='application/json')

        self.client.post('/editor/save_session',
                         json.dumps({'save': 'True'}),
                         content_type='application/json')

        # Load db record
        record = models.Track.objects.get(id=self.client.session['index_db'])

        self.assertEqual(record.title, 'test_save_rename_save')
        self.assertEqual(json.loads(record.track)['title'], 'test_save_rename_save')

    def test_save_session_get(self):
        """
        Use get request instead of post and check response
        """
        self.login()
        self.create_session()
        response = self.client.get('/editor/save_session')
        self.assertEqual(response.status_code, 400)

    def test_save_session_wrong_request(self):
        """
        Check response of request with False value in the save option
        """
        self.login()
        self.create_session()
        response = self.client.post('/editor/save_session',
                                    json.dumps({'save': 'False'}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 492)

    def test_save_session_no_track(self):
        """
        Try to save a non existing session
        """
        self.login()
        response = self.client.post('/editor/save_session',
                                    json.dumps({'save': 'False'}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 491)

    def test_remove_session(self):
        """
        Create a session, save and remove it from db
        """
        self.login()
        self.create_session()
        self.client.post('/editor/save_session',
                         json.dumps({'save': 'True'}),
                         content_type='application/json')

        before = models.Track.objects.\
            filter(id=self.client.session['index_db']).count()

        response = self.client.post(f'/editor/remove_session/{self.client.session["index_db"]}')

        after = models.Track.objects.\
            filter(id=self.client.session['index_db']).count()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(before, 1)
        self.assertEqual(after, 0)

    def test_remove_session_no_track(self):
        """
        Try to save a non existing session
        """
        self.login()
        response = self.client.post('/editor/remove_session/25')

        self.assertEqual(response.status_code, 500)

    def test_remove_session_get(self):
        """
        Use get request instead of post and check response
        """
        self.login()
        response = self.client.get('/editor/remove_session/25')

        self.assertEqual(response.status_code, 400)

    def test_rename_session(self):
        """
        Create a session, rename and save
        """
        self.login()
        self.create_session()
        self.client.post('/editor/save_session',
                         json.dumps({'save': 'True'}),
                         content_type='application/json')
        response = self.client.post('/editor/rename_session',
                                    json.dumps({'new_name': 'test_rename_session'}),
                                    content_type='application/json')
        self.client.post('/editor/save_session',
                         json.dumps({'save': 'True'}),
                         content_type='application/json')

        track_db = models.Track.objects.get(id=self.client.session['index_db'])

        self.assertEqual(response.status_code, 201)
        self.assertEqual(track_db.title, 'test_rename_session')

    def test_rename_session_no_track(self):
        """
        Try to rename a non existing session
        """
        self.login()
        response = self.client.post('/editor/rename_session',
                                    json.dumps({'new_name': 'test_rename_session_no_track'}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 500)

    def test_rename_session_get(self):
        """
        Use get request instead of post and check response
        """
        self.login()
        response = self.client.get('/editor/rename_session')
        self.assertEqual(response.status_code, 400)

    def test_get_summary(self):
        self.login()
        self.create_session()

        sample_file = self.get_sample_file()
        with open(sample_file, 'r') as f:
            self.client.post('/editor', {'document': f})

        response = self.client.get('/editor/get_summary')

        summary = json.loads(response.content)['summary']
        self.assertEqual(summary[list(summary.keys())[0]],
                         {'distance': '445.2 km', 'uphill': '+20 m', 'downhill': '-20 m'})
        self.assertEqual(summary['total'],
                         {'distance': '445.2 km', 'uphill': '+20 m', 'downhill': '-20 m'})
        self.assertEqual(response.status_code, 200)

    def test_get_summary_no_track(self):
        """
        Try to rename a non existing session
        """
        self.login()
        response = self.client.get('/editor/get_summary')
        self.assertEqual(response.status_code, 500)

    def test_get_summary_post(self):
        """
        Use post request instead of get and check response
        """
        self.login()
        response = self.client.post('/editor/get_summary')
        self.assertEqual(response.status_code, 400)


class LoginRequiredTest(TestCase):
    """
    All tests to check the login required are groupd in this class
    """
    def test_editor(self):
        response = self.client.get('/editor')
        self.assertEqual(response.status_code, 302)

    def test_editor_idx(self):
        response = self.client.get('/editor/1')
        self.assertEqual(response.status_code, 302)

    def test_rename_segment(self):
        response = self.client.get('/editor/rename_segment')
        self.assertEqual(response.status_code, 302)

    def test_remove_segment(self):
        response = self.client.get('/editor/remove_segment')
        self.assertEqual(response.status_code, 302)

    def test_get_segment(self):
        response = self.client.get('/editor/get_segment/1')
        self.assertEqual(response.status_code, 302)

    def test_get_summary(self):
        response = self.client.get('/editor/get_summary')
        self.assertEqual(response.status_code, 302)

    def test_save_session(self):
        response = self.client.get('/editor/save_session')
        self.assertEqual(response.status_code, 302)

    def test_remove_session(self):
        response = self.client.get('/editor/remove_session/1')
        self.assertEqual(response.status_code, 302)

    def test_rename_session(self):
        response = self.client.get('/editor/rename_session')
        self.assertEqual(response.status_code, 302)
