from django.test import TestCase
import datetime as dt
import os

from TrackApp import gpx


class GpxTest(TestCase):
    def setUp(self):
        self.test_path = os.path.dirname(__file__)

    def test_load_file(self):
        file = os.path.join(self.test_path, 'samples/basic_sample.gpx')
        route = gpx.Gpx(file)
        self.assertTrue(route._load_file())

    def test_load_file_big(self):
        file = os.path.join(self.test_path, 'samples/over_10mb.gpx')

        with self.assertRaises(gpx.LoadGpxError):
            gpx.Gpx(file)

    def test_to_dict(self):
        file = os.path.join(self.test_path, 'samples/basic_sample.gpx')
        route = gpx.Gpx(file)
        route_dict = route.to_dict()

        # Extract data to check
        first = [route_dict['lat'][0], route_dict['lon'][0],
                 route_dict['ele'][0]]
        last = [route_dict['lat'][-1], route_dict['lon'][-1],
                route_dict['ele'][-1]]

        # Insert time in an easy-to-compare format
        first_time = route_dict['time'][0]
        first.append(dt.datetime(first_time.year, first_time.month,
                                 first_time.day, first_time.hour,
                                 first_time.minute, first_time.second))

        last_time = route_dict['time'][-1]
        last.append(dt.datetime(last_time.year, last_time.month,
                                last_time.day, last_time.hour,
                                last_time.minute, last_time.second))

        # Reference data
        first_ref = [46.2406490, 6.0342000, 442.0,
                     dt.datetime(2015, 7, 24, 6, 44, 14)]
        last_ref = [46.2301180, 6.0525330, 428.2,
                    dt.datetime(2015, 7, 24, 6, 52, 24)]

        # Compare lists with reference and read data
        self.assertTrue(all([a == b for a, b in zip(first + last, first_ref + last_ref)]))

    def test_to_pandas(self):
        file = os.path.join(self.test_path, 'samples/basic_sample.gpx')
        route = gpx.Gpx(file)
        route_df = route.to_pandas()

        self.assertAlmostEqual(route_df.iloc[0].lat, 46.240649)
        self.assertAlmostEqual(route_df.iloc[0].lon, 6.0342)
        self.assertAlmostEqual(route_df.iloc[0].ele, 442.0)

        self.assertAlmostEqual(route_df.iloc[-1].lat, 46.230118)
        self.assertAlmostEqual(route_df.iloc[-1].lon, 6.052533)
        self.assertAlmostEqual(route_df.iloc[-1].ele, 428.2)
