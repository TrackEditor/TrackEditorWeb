import os
import datetime as dt
from django.test import TestCase

import TrackApp.models as models
import libs.track as track


class ModelsTest(TestCase):
    def setUp(self):
        self.test_path = os.path.dirname(__file__)
        self.user = models.User.objects.create_user('foo', password='bar')
        self.user.save()

    def tearDown(self):
        pass

    def record_track(self, filename='island_1.gpx'):
        obj_track = track.Track()
        obj_track.add_gpx(os.path.join(self.test_path, 'samples', filename))
        json_track = obj_track.to_json()

        new_track = models.Track(user=self.user, track=json_track)
        new_track.save()

        return new_track, json_track, obj_track

    def test_new_track(self):
        new_track, json_track, _ = self.record_track()

        self.assertEqual(new_track.track, json_track)
        self.assertIsNotNone(new_track.id)
        self.assertIsInstance(new_track.id, int)
        self.assertTrue(
            new_track.last_edit - new_track.creation < dt.timedelta(microseconds=50))

    def test_last_edit(self):
        new_track, _, _ = self.record_track()

        new_track.last_edit = dt.datetime(2000, 3, 27, 0, 0, 0)
        new_track.save()

        self.assertEqual(new_track.last_edit, dt.datetime(2000, 3, 27, 0, 0, 0))

    def test_delete_track(self):
        new_track, _, _ = self.record_track()
        track_id = new_track.id

        count_before = models.Track.objects.filter(id=track_id).count()
        new_track.delete()
        count_after = models.Track.objects.filter(id=track_id).count()

        self.assertEqual(count_before, 1)
        self.assertEqual(count_after, 0)

    def test_delete_tracks_for_user(self):
        for i in range(1, 6):
            new_track, _, _ = self.record_track(f'Inaccessible_Island_part{i}.gpx')

        total_tracks_before = models.Track.objects.filter(user=self.user).count()
        self.user.delete()
        total_tracks_after = models.Track.objects.filter(user=self.user).count()

        self.assertEqual(total_tracks_before, 5)
        self.assertEqual(total_tracks_after, 0)
