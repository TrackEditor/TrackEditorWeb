from django.test import TestCase
import os

from TrackApp import utils


class UtilsTest(TestCase):
    def test_md5sum(self):
        test_path = os.path.dirname(__file__)
        file = os.path.join(test_path, 'samples/basic_sample.gpx')
        self.assertEqual(utils.md5sum(file), '0a06c43d730d35cde308f0d0bd608fe4')

    def test_id_generator(self):
        self.assertEqual(len(utils.id_generator(8)), 8)
