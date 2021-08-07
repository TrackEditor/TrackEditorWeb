# flake8: noqa: W504
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
from glob import glob

import libs.track as track
from libs.utils import md5sum
import TrackApp.models as models


class EditorTestUtils(TestCase):
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

    def login(self):
        self.client.login(username=self.username,
                          password=self.password)

    def create_session(self):
        """
        Get request to the /editor endpoint to generate track in session
        """
        response = self.client.get('/editor/')
        session = self.client.session
        return response, session

    def get_sample_file(self, filename='simple_numbers.gpx'):
        """
        Get a file to be used as input
        """
        return os.path.join(self.test_path, 'samples', filename)

    def compare_tracks(self, session_track, reference_track):
        """
        Comparison of tracks is encapsulated in this function. It can be
        particularly sensitive for segment_names since suffix may be added
        according to the loaded name file in /media
        """
        for k in session_track:
            if k == 'segment_names':
                for s, r in zip(session_track[k], reference_track[k]):
                    self.assertIn(os.path.splitext(r)[0], s)
            else:
                self.assertEqual(session_track[k], reference_track[k])


class EditorAPITest(EditorTestUtils):
    """
    Test the editor API functions from views. All the available operations for
    the user are tested. These operations are commanded from the JS code.
    """

    def setUp(self):
        self.test_path = os.path.dirname(__file__)
        self.user, self.username, self.password = self.create_user()
        self.login()

    def test_create_session(self):
        """
        Check that empty session is created
        """
        response, session = self.create_session()

        self.assertEqual(response.status_code, 200)
        self.assertIn('json_track', session.keys())
        self.assertIn('index_db', session.keys())

    def test_add_gpx(self):
        """
        Add one gpx file and check it is included in session
        """
        self.create_session()

        # Add file
        sample_file = self.get_sample_file()
        with open(sample_file, 'r') as f:
            self.client.post('/editor/', {'document': f})
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
        self.create_session()

        sample_file = self.get_sample_file()
        with open(sample_file, 'r') as f:
            self.client.post('/editor/', {'document': f})

        self.client.post('/editor/save_session',
                         json.dumps({'save': 'True'}),
                         content_type='application/json')

        # Add another file to force that the last active session is not
        # the same than the loaded one
        with open(sample_file, 'r') as f:
            self.client.post('/editor/', {'document': f})

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
        self.create_session()

        # Add file
        sample_file = self.get_sample_file()
        with open(sample_file, 'r') as f:
            self.client.post('/editor/', {'document': f})
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
        self.create_session()

        sample_file = self.get_sample_file()
        with open(sample_file, 'r') as f:
            self.client.post('/editor/', {'document': f})
        self.client.post('/editor/save_session',
                         json.dumps({'save': 'True'}),
                         content_type='application/json')

        with open(sample_file, 'r') as f:
            self.client.post('/editor/', {'document': f})
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
        self.create_session()

        # Load files and save session
        for i in range(1, 6):
            sample_file = self.get_sample_file(f'island_{i}.gpx')
            with open(sample_file, 'r') as f:
                self.client.post('/editor/', {'document': f})

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
                         ['island_1.gpx', None,
                          'island_3.gpx', None,
                          'island_5.gpx'])

    def test_save_rename_save(self):
        """
        Create and save session with one gpx file. Add a new one, save an check
        that the db record is properly updated.
        """
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
        self.create_session()
        response = self.client.get('/editor/save_session')
        self.assertEqual(response.status_code, 400)

    def test_save_session_wrong_request(self):
        """
        Check response of request with False value in the save option
        """
        self.create_session()
        response = self.client.post('/editor/save_session',
                                    json.dumps({'save': 'False'}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 492)

    def test_save_session_no_track(self):
        """
        Try to save a non existing session
        """
        response = self.client.post('/editor/save_session',
                                    json.dumps({'save': 'False'}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 491)

    def test_remove_session(self):
        """
        Create a session, save and remove it from db
        """
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
        response = self.client.post('/editor/remove_session/25')

        self.assertEqual(response.status_code, 500)

    def test_remove_session_get(self):
        """
        Use get request instead of post and check response
        """
        response = self.client.get('/editor/remove_session/25')

        self.assertEqual(response.status_code, 400)

    def test_rename_session(self):
        """
        Create a session, rename and save
        """
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
        response = self.client.post('/editor/rename_session',
                                    json.dumps({'new_name': 'test_rename_session_no_track'}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 500)

    def test_rename_session_get(self):
        """
        Use get request instead of post and check response
        """
        response = self.client.get('/editor/rename_session')
        self.assertEqual(response.status_code, 400)

    def test_get_summary(self):
        """
        Call the get_summary endpoint to check the return JSON
        """
        self.create_session()

        sample_file = self.get_sample_file()
        with open(sample_file, 'r') as f:
            self.client.post('/editor/', {'document': f})

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
        response = self.client.get('/editor/get_summary')
        self.assertEqual(response.status_code, 500)

    def test_get_summary_post(self):
        """
        Use post request instead of get and check response
        """
        response = self.client.post('/editor/get_summary')
        self.assertEqual(response.status_code, 400)

    def test_download_session(self):
        """
        Load a gpx and download the session
        """
        self.create_session()

        sample_file = self.get_sample_file()
        with open(sample_file, 'r') as f:
            self.client.post('/editor/', {'document': f})

        self.client.post('/editor/rename_session',
                         json.dumps({'new_name': 'test_download_session'}),
                         content_type='application/json')

        response = self.client.post('/editor/download_session')
        resp_json = json.loads(response.content)

        self.assertRegex(resp_json['url'], '/media/test_download_session_.{8}.gpx')
        self.assertRegex(resp_json['filename'], 'test_download_session_.{8}.gpx')
        self.assertEqual(os.path.basename(resp_json['url']), resp_json['filename'])

        self.assertEqual(response.status_code, 200)

    def test_download_session_get(self):
        """
        Use get request instead of post and check response
        """
        self.create_session()

        sample_file = self.get_sample_file()
        with open(sample_file, 'r') as f:
            self.client.post('/editor/', {'document': f})

        response = self.client.get('/editor/download_session')

        self.assertEqual(response.status_code, 400)

    def test_download_session_no_track(self):
        """
        Test download session with no available track
        """
        self.create_session()

        response = self.client.post('/editor/download_session')
        self.assertEqual(response.status_code, 500)

    def test_get_segments_links(self):
        """
        Test download session with no available track
        """
        self.create_session()

        for file in ['simple_numbers.gpx', 'simple_numbers_down.gpx',
                     'simple_numbers_left.gpx', 'simple_numbers_up.gpx']:
            sample_file = self.get_sample_file(file)
            with open(sample_file, 'r') as f:
                self.client.post('/editor/', {'document': f})

        response = self.client.get('/editor/get_segments_links')

        resp_json = json.loads(response.content)
        links = eval(resp_json['links'])

        self.assertEqual(links, [[[1.0, 5.0], [1.0, 6.0]],
                                 [[-3.0, 6.0], [-3.0, 5.0]],
                                 [[-3.0, 1.0], [-3.0, 0.0]]])
        self.assertEqual(response.status_code, 200)

    def test_get_segments_links_no_track(self):
        """
        Try to get segments with no available track
        """
        response = self.client.get('/editor/get_segments_links')
        self.assertEqual(response.status_code, 500)

    def test_get_segments_links_post(self):
        """
        Send post instead of get
        """
        response = self.client.post('/editor/get_segments_links')
        self.assertEqual(response.status_code, 400)


class ReverseSegmentTest(EditorTestUtils):
    """
    Test the reverse segment view of the editor api
    """

    def setUp(self):
        self.test_path = os.path.dirname(__file__)
        self.user, self.username, self.password = self.create_user()
        self.login()

    def test_reverse_segment(self):
        """
        Test reverse segments
        """
        self.create_session()

        for file in ['simple_numbers.gpx', 'simple_numbers_down.gpx',
                     'simple_numbers_left.gpx']:
            sample_file = self.get_sample_file(file)
            with open(sample_file, 'r') as f:
                self.client.post('/editor/', {'document': f})

        response_1 = self.client.post('/editor/reverse_segment/1')
        response_2 = self.client.post('/editor/reverse_segment/2')
        response_3 = self.client.post('/editor/reverse_segment/3')
        json_track = json.loads(self.client.session['json_track'])

        simple_numbers = {'lat': [1] * 5, 'lon': list(range(1, 6))}
        simple_numbers_down = {'lat': list(range(1, -4, -1)), 'lon': [6] * 5}
        simple_numbers_left = {'lat': [-3] * 5, 'lon': list(range(5, 0, -1))}

        self.assertEqual(response_1.status_code, 200)
        self.assertEqual(response_2.status_code, 200)
        self.assertEqual(response_3.status_code, 200)
        self.assertEqual(json_track['lat'],
                         simple_numbers['lat'][::-1] +
                         simple_numbers_down['lat'][::-1] +
                         simple_numbers_left['lat'][::-1])
        self.assertEqual(json_track['lon'],
                         simple_numbers['lon'][::-1] +
                         simple_numbers_down['lon'][::-1] +
                         simple_numbers_left['lon'][::-1])

    def test_reverse_segment_get_no_track(self):
        """
        Try to get segments with no available track
        """
        response = self.client.post('/editor/reverse_segment/1')
        self.assertEqual(response.status_code, 520)

    def test_reverse_segment_get_no_index(self):
        """
        Do not provide segment index to reverse
        """
        response = self.client.post('/editor/reverse_segment')
        self.assertEqual(response.status_code, 404)

    def test_reverse_segment_get(self):
        """
        Send get instead of get
        """
        response = self.client.get('/editor/reverse_segment/1')
        self.assertEqual(response.status_code, 400)

    def test_reverse_segment_non_existing_segment(self):
        """
        Request to reverse a non-existing segment
        """
        self.create_session()

        sample_file = self.get_sample_file()
        with open(sample_file, 'r') as f:
            self.client.post('/editor/', {'document': f})

        response = self.client.post('/editor/reverse_segment/5')

        self.assertEqual(response.status_code, 521)


class LoginRequiredTest(TestCase):
    """
    All tests to check the login required are groupd in this class
    """
    def test_editor(self):
        response = self.client.get('/editor/')
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

    def test_download_session(self):
        response = self.client.get('/editor/download_session')
        self.assertEqual(response.status_code, 302)

    def test_get_segments_links(self):
        response = self.client.get('/editor/get_segments_links')
        self.assertEqual(response.status_code, 302)

    def test_reverse_segment(self):
        response = self.client.get('/editor/reverse_segment/1')
        self.assertEqual(response.status_code, 302)
