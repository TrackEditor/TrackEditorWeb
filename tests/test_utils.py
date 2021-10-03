from django.test import TestCase
import os

from libs import utils


class UtilsTest(TestCase):
    def test_md5sum(self):
        test_path = os.path.dirname(__file__)
        file = os.path.join(test_path,
                            'samples/basic_sample.gpx')
        self.assertEqual(utils.md5sum(file), '0a06c43d730d35cde308f0d0bd608fe4')

    def test_id_generator(self):
        self.assertEqual(len(utils.id_generator(8)), 8)

    def test_auto_zoom_island(self):
        coordinates = {'lat_min': -37.31371,
                       'lat_max': -37.28434,
                       'lon_min': -12.698120000000001,
                       'lon_max': -12.64469}
        self.assertEqual(utils.auto_zoom(**coordinates), 13)

    def test_auto_zoom_bike_ride(self):
        coordinates = {'lat_min': 40.468258,
                       'lat_max': 40.752925,
                       'lon_min': -3.794208,
                       'lon_max': -3.682484}
        self.assertEqual(utils.auto_zoom(**coordinates), 10)

    def test_auto_zoom_st_james(self):
        coordinates = {'lat_min': 42.258258,
                       'lat_max': 43.010292,
                       'lon_min': -8.547153,
                       'lon_max': -1.319181}
        self.assertEqual(utils.auto_zoom(**coordinates), 6)

    def test_auto_zoom_default(self):
        self.assertEqual(utils.auto_zoom(0, 0, 0, 0), 1)
