# flake8: noqa: E501
from django.test import TestCase
import pytest
import numpy as np
import pandas as pd
import datetime as dt
import os
import json

from libs import track


class TrackTest(TestCase):
    def setUp(self):
        self.test_path = os.path.dirname(__file__)

    def datetime_to_integer(self, dt_time):
        return 3600 * 24 * dt_time.days + dt_time.seconds

    def test_add_gpx(self):
        # Load data
        obj_track = track.Track()

        obj_track.add_gpx(
            f'{self.test_path}/samples/island_full.gpx')

        # Check that the file is properly loaded
        self.assertTrue(obj_track.df_track.lat.iloc[0] == pytest.approx(-37.30945))
        self.assertTrue(obj_track.df_track.lon.iloc[0] == pytest.approx(-12.69670))
        self.assertTrue(obj_track.df_track.ele.iloc[0] == pytest.approx(537.61))
        self.assertTrue(obj_track.df_track.lat.iloc[-1] == pytest.approx(-37.30682))
        self.assertTrue(obj_track.df_track.lon.iloc[-1] == pytest.approx(-12.69775))
        self.assertTrue(obj_track.df_track.ele.iloc[-1] == pytest.approx(550.0200))
        self.assertTrue(obj_track.df_track.shape[0] == pytest.approx(141))

    def test_update_summary(self):
        """
        Private method test: executed within add_gpx
        """
        # Load data
        obj_track = track.Track()
        obj_track.add_gpx(
            f'{self.test_path}/samples/island_1.gpx')

        # Initial data
        total_distance = obj_track.total_distance
        total_uphill = obj_track.total_uphill
        total_downhill = obj_track.total_downhill

        # Force to update summary
        obj_track.add_gpx(
            f'{self.test_path}/samples/island_2.gpx')

        # Check that every summary number is updated
        self.assertNotEqual(total_distance, obj_track.total_distance)
        self.assertNotEqual(total_uphill, obj_track.total_uphill)
        self.assertNotEqual(total_downhill, obj_track.total_downhill)

    def test_insert_positive_elevation(self):
        """
        Private method test: executed within add_gpx
        """
        # Load data
        obj_track = track.Track()
        obj_track.add_gpx(
            f'{self.test_path}/samples/island_full.gpx')

        # Overall initial information
        total_pos_elevation = obj_track.df_track.ele_pos_cum.iloc[-1]

        self.assertTrue(total_pos_elevation == pytest.approx(909.71997))

    def test_insert_negative_elevation(self):
        """
        Private method test: executed within add_gpx
        """
        # Load data
        obj_track = track.Track()
        obj_track.add_gpx(
            f'{self.test_path}/samples/island_full.gpx')

        # Overall initial information
        total_neg_elevation = obj_track.df_track.ele_neg_cum.iloc[-1]

        self.assertTrue(total_neg_elevation == pytest.approx(-897.31000))

    def test_insert_distance(self):
        """
        Private method test: executed within add_gpx
        """
        # Load data
        obj_track = track.Track()
        obj_track.add_gpx(
            f'{self.test_path}/samples/island_full.gpx')

        # Overall initial information
        total_distance = obj_track.df_track.distance.iloc[-1]

        self.assertTrue(total_distance == pytest.approx(12.121018))

    def test_update_extremes(self):
        """
        Private method test: executed within add_gpx
        """
        # Load data
        obj_track = track.Track()
        obj_track.add_gpx(
            f'{self.test_path}/samples/island_1.gpx')

        # Get reference data
        extremes = obj_track.extremes

        # Load more data
        for i in range(2, 6):
            obj_track.add_gpx(
                f'{self.test_path}/samples/island_{i}.gpx')

        new_extremes = obj_track.extremes

        self.assertNotEqual(new_extremes, extremes)
        self.assertTrue(new_extremes[0] == pytest.approx(obj_track.df_track["lat"].min()))
        self.assertTrue(new_extremes[1] == pytest.approx(obj_track.df_track["lat"].max()))
        self.assertTrue(new_extremes[2] == pytest.approx(obj_track.df_track["lon"].min()))
        self.assertTrue(new_extremes[3] == pytest.approx(obj_track.df_track["lon"].max()))

    def test_reverse_segment(self):
        """
        Verify that lat, lon and ele are properly inverted. Total distance is not
        applicable since this operation can provoke a change.
        """
        # Load data
        obj_track = track.Track()
        obj_track.add_gpx(
            f'{self.test_path}/samples/island_1.gpx')

        # Overall initial information
        initial_shape = obj_track.df_track.shape

        # Copy for comparison
        lat_comp = obj_track.df_track.lat.copy().to_numpy().astype('float32')
        lon_comp = obj_track.df_track.lon.copy().to_numpy().astype('float32')
        ele_comp = obj_track.df_track.ele.copy().to_numpy().astype('float32')

        # Apply method
        obj_track.reverse_segment(1)

        # Specific checks
        import pytest
        self.assertTrue(np.all(obj_track.df_track.lat.to_numpy() ==
                               pytest.approx(lat_comp[::-1])))
        self.assertTrue(np.all(obj_track.df_track.lon.to_numpy() ==
                               pytest.approx(lon_comp[::-1])))
        self.assertTrue(np.all(obj_track.df_track.ele.to_numpy() ==
                               pytest.approx(ele_comp[::-1])))

        # Non-regression checks, total_distance is not applicable
        self.assertEqual(initial_shape, obj_track.df_track.shape)

    def test_divide_segment(self):
        """
        Split the segment in the index 100, before the segment id must be 1,
        at and after it must be 2.
        """

        # Load data
        obj_track = track.Track()
        obj_track.add_gpx(
            f'{self.test_path}/samples/island_full.gpx')

        # Overall initial information
        initial_total_distance = obj_track.df_track.distance.iloc[-1]
        initial_shape = obj_track.df_track.shape

        # Apply method
        obj_track.divide_segment(100)

        # Specific checks
        self.assertEqual(obj_track.df_track.segment.iloc[99], 1)
        self.assertEqual(obj_track.df_track.segment.iloc[100], 2)

        # Non-regression checks
        self.assertEqual(initial_total_distance, obj_track.df_track.distance.iloc[-1])
        self.assertEqual(initial_shape, obj_track.df_track.shape)
        self.assertEqual(obj_track.size, 2)

    def test_multi_divide_segment(self):
        """
        Split the segment at different indexes and check that the segment id
        is properly updated
        """

        # Load data
        obj_track = track.Track()
        obj_track.add_gpx(
            f'{self.test_path}/samples/island_full.gpx')

        # Overall initial information
        initial_total_distance = obj_track.df_track.distance.iloc[-1]
        initial_shape = obj_track.df_track.shape

        # Apply method
        obj_track.divide_segment(80)
        obj_track.divide_segment(120)
        obj_track.divide_segment(40)

        # Specific checks
        self.assertEqual(obj_track.df_track.segment.iloc[39], 1)
        self.assertEqual(obj_track.df_track.segment.iloc[40], 2)
        self.assertEqual(obj_track.df_track.segment.iloc[80], 3)
        self.assertEqual(obj_track.df_track.segment.iloc[120], 4)
        self.assertEqual(obj_track.df_track.segment.iloc[-1], 4)

        # Non-regression checks
        self.assertEqual(initial_total_distance, obj_track.df_track.distance.iloc[-1])
        self.assertEqual(initial_shape, obj_track.df_track.shape)
        self.assertEqual(obj_track.size, 4)

    def test_change_order(self):
        """
        Check that the order has been properly changed by looking at first and
        last row elements of the segment.
        """

        # Load data
        obj_track = track.Track()

        obj_track.add_gpx(f'{self.test_path}/samples/island_1.gpx')
        obj_track.add_gpx(f'{self.test_path}/samples/island_2.gpx')
        obj_track.add_gpx(f'{self.test_path}/samples/island_3.gpx')
        initial_df = obj_track.df_track[['lat', 'lon', 'ele', 'segment']].copy()

        # Apply function
        new_order = {1: 3, 2: 1, 3: 2}
        obj_track.change_order(new_order)
        after_df = obj_track.df_track[['lat', 'lon', 'ele', 'segment']].copy()

        # Checks
        for n in new_order:
            segment_before = initial_df[
                initial_df['segment'] == n].reset_index().\
                drop(columns=['index', 'segment'])
            segment_after = after_df[
                after_df['segment'] == new_order[n]].reset_index().\
                drop(columns=['index', 'segment'])
            self.assertTrue((segment_before == segment_after).all().all())

    def test_fix_elevation(self):
        """
        The established criteria is to check that the standard deviation and
        maximum peak are lower than at the beginning.
        """
        # Load data
        obj_track = track.Track()
        obj_track.add_gpx(f'{self.test_path}/samples/fix_elevation.gpx')

        # Get initial data
        initial_std = np.std(obj_track.df_track.ele)
        initial_max_peak = max(obj_track.df_track.ele)

        # Apply function
        obj_track.fix_elevation(1)

        final_std = np.std(obj_track.df_track.ele)
        final_max_peak = max(obj_track.df_track.ele)

        self.assertTrue(initial_max_peak > final_max_peak)
        self.assertTrue(initial_std > final_std)

    def test_smooth_elevation(self):
        """
        The established criteria is to check that the standard deviation and
        maximum peak are lower than at the beginning.
        """
        # Load data
        obj_track = track.Track()
        obj_track.add_gpx(
            f'{self.test_path}/samples/island_full.gpx')

        # Get initial data
        initial_std = np.std(obj_track.df_track.ele)
        initial_max_peak = max(obj_track.df_track.ele)

        # Apply function
        obj_track.smooth_elevation(1)

        final_std = np.std(obj_track.df_track.ele)
        final_max_peak = max(obj_track.df_track.ele)

        self.assertTrue(initial_max_peak > final_max_peak)
        self.assertTrue(initial_std > final_std)

    def test_remove_segment(self):
        """
        Remove one segment and check that it is not available after the removal
        """
        # Load data
        obj_track = track.Track()

        obj_track.add_gpx(
            f'{self.test_path}/samples/island_1.gpx')
        obj_track.add_gpx(f'{self.test_path}/samples/island_2.gpx')
        obj_track.add_gpx(f'{self.test_path}/samples/island_3.gpx')

        # Apply method
        obj_track.remove_segment(2)

        # Check
        self.assertNotIn(2, obj_track.df_track.segment.unique())
        self.assertIsNone(obj_track.segment_names[2-1])

    def test_get_segment(self):
        # Load data
        obj_track = track.Track()

        obj_track.add_gpx(f'{self.test_path}/samples/island_1.gpx')
        obj_track.add_gpx(f'{self.test_path}/samples/island_2.gpx')
        obj_track.add_gpx(f'{self.test_path}/samples/island_3.gpx')

        # Reference segment
        ref_df = obj_track.df_track[obj_track.df_track.segment == 2].copy()

        # Get segment 2
        seg_df = obj_track.get_segment(2)

        # Compare segment 2 and copy
        # Take care of NaN since np.nan == np.nan is false
        self.assertTrue((ref_df.fillna(0) == seg_df.fillna(0)).all().all())

    def test_insert_timestamp(self):
        # Load data
        obj_track = track.Track()

        obj_track.add_gpx(
            f'{self.test_path}/samples/island_full.gpx')

        # Apply method
        initial_time = dt.datetime(2010, 1, 1)
        speed = 1.0
        obj_track.insert_timestamp(initial_time, speed)

        # Checks
        resulting_speed = \
            obj_track.df_track['distance'].iloc[-1] / \
            ((obj_track.df_track['time'].iloc[-1] - obj_track.df_track['time'].iloc[0]).seconds/3600.0)
        self.assertTrue(not obj_track.df_track.time.isnull().values.any())  # no NaN
        self.assertEqual(obj_track.df_track.time.iloc[0], initial_time)
        self.assertTrue(
            all(x > 0 for x in
                list(map(self.datetime_to_integer,
                         obj_track.df_track.time.diff().to_list()))[1:]))  # timestamp is increasing
        self.assertTrue(abs(resulting_speed - speed) < 1.5)

    def test_insert_timestamp_consider_elevation(self):
        # Load data
        obj_track = track.Track()
        obj_track.add_gpx(
            f'{self.test_path}/samples/bike_ride.gpx')

        # Apply method
        initial_time = dt.datetime(2010, 1, 1)
        speed = 40.0
        obj_track.insert_timestamp(initial_time, 40.0, consider_elevation=True)

        # Checks
        resulting_speed = \
            obj_track.df_track['distance'].iloc[-1] / \
            ((obj_track.df_track['time'].iloc[-1] - obj_track.df_track['time'].iloc[0]).seconds/3600.0)

        self.assertTrue(not obj_track.df_track.time.isnull().values.any())  # no NaN
        self.assertEqual(obj_track.df_track.time.iloc[0], initial_time)
        self.assertTrue(
            all(x >= 0 for x in
                list(map(self.datetime_to_integer,
                         obj_track.df_track.time.diff().to_list()))[1:]))  # timestamp is increasing
        self.assertTrue(abs(resulting_speed - speed) < 1.5)

    def test_columns_type(self):
        # Load data
        obj_track = track.Track()
        obj_track.add_gpx(os.path.join(self.test_path, 'samples', 'island_full.gpx'))

        # Apply method
        obj_track._force_columns_type()

        # Checks
        types = obj_track.df_track.dtypes
        self.assertTrue(types.lat == np.float32)
        self.assertTrue(types.lon == np.float32)
        self.assertTrue(types.ele == np.float32)
        self.assertTrue(types.segment == np.int32)
        self.assertEqual(str(types.time), 'datetime64[ns, UTC]')

    def test_save_gpx(self):
        # Load data
        obj_track = track.Track()
        obj_track.add_gpx(os.path.join(self.test_path, 'samples', 'island_full.gpx'))

        # Insert timestamp, no timestamp is checked in file_menu.py wrapper
        initial_time = dt.datetime(2010, 1, 1)
        obj_track.insert_timestamp(initial_time, 1.0)

        # Apply method
        filename = f'test_save_gpx_{np.random.randint(1e+6 - 1, 1e+6)}.gpx'
        obj_track.save_gpx(filename)
        obj_track._force_columns_type()

        # Load saved file
        saved_track = track.Track()
        saved_track.add_gpx(filename)

        # Check
        self.assertTrue((obj_track.df_track.lat == saved_track.df_track.lat).all())
        self.assertTrue((obj_track.df_track.lon == saved_track.df_track.lon).all())
        self.assertTrue((obj_track.df_track.ele == saved_track.df_track.ele).all())
        self.assertTrue((obj_track.df_track.time == saved_track.df_track.time).all())

    def test_to_json(self):
        obj_track = track.Track()
        obj_track.add_gpx(os.path.join(self.test_path, 'samples', 'simple_numbers.gpx'))
        json_track = json.loads(obj_track.to_json())

        dataframe_keys = ['lat', 'lon', 'ele', 'segment', 'ele_pos_cum', 'ele_neg_cum', 'distance']
        for k in dataframe_keys:
            self.assertIn(k, json_track)
            self.assertEqual(len(json_track[k]), 5)

        metadata_keys = ['size', 'last_segment_idx', 'extremes', 'total_distance', 'total_uphill', 'total_downhill', 'title']
        for k in metadata_keys:
            self.assertIn(k, json_track)

    def test_to_json_empty(self):
        obj_track = track.Track()
        json_track = json.loads(obj_track.to_json())

        dataframe_keys = ['lat', 'lon', 'ele', 'segment', 'ele_pos_cum', 'ele_neg_cum', 'distance']
        for k in dataframe_keys:
            self.assertIn(k, json_track)
            self.assertEqual(len(json_track[k]), 0)

        metadata_keys = ['size', 'last_segment_idx', 'extremes', 'total_distance', 'total_uphill', 'total_downhill', 'title']
        for k in metadata_keys:
            self.assertIn(k, json_track)

    def test_from_json(self):
        json_string = '{"lat": {"0": 1.0, "1": 1.0, "2": 1.0, "3": 1.0, "4": 1.0},' + \
                      ' "lon": {"0": 1.0, "1": 2.0, "2": 3.0, "3": 4.0, "4": 5.0},' + \
                      ' "ele": {"0": 10.0, "1": 20.0, "2": 30.0, "3": 20.0, "4": 10.0},' + \
                      ' "segment": {"0": 1, "1": 1, "2": 1, "3": 1, "4": 1},' + \
                      ' "ele_pos_cum": {"0": NaN, "1": 10.0, "2": 20.0, "3": 20.0, "4": 20.0},' + \
                      ' "ele_neg_cum": {"0": NaN, "1": 0.0, "2": 0.0, "3": -10.0, "4": -20.0},' + \
                      ' "distance": {"0": 0.0, "1": 111.30265045166016, "2": 222.6053009033203, "3": 333.907958984375, "4": 445.2106018066406},' + \
                      ' "size": 1,' + \
                      ' "last_segment_idx": 1,' + \
                      ' "extremes": [1.0, 1.0, 1.0, 5.0],' +  \
                      ' "total_distance": 445.2106018066406,' + \
                      ' "total_uphill": 20.0,' + \
                      ' "total_downhill": -20.0,' + \
                      ' "segment_names": ["simple_numbers.gpx"],' \
                      ' "title": "tesing track"}'

        obj_track = track.Track(track_json=json_string)

        self.assertEqual(obj_track.df_track.shape, (5, 8))
        self.assertEqual(obj_track.size, 1)
        self.assertEqual(obj_track.extremes, [1.0, 1.0, 1.0, 5.0])
        self.assertAlmostEqual(obj_track.total_distance, 445.2106018066406)
        self.assertEqual(obj_track.total_uphill, 20.0)
        self.assertEqual(obj_track.total_downhill, -20.0)

    def test_from_json_empty(self):
        json_string = '{"lat": {}, "lon": {}, "ele": {}, "segment": {}, ' + \
                      ' "ele_pos_cum": {}, "ele_neg_cum": {}, ' +  \
                      ' "distance": {}, "size": 0, "last_segment_idx": 0, ' + \
                      ' "extremes": [0, 0, 0, 0], "total_distance": 0, ' + \
                      ' "total_uphill": 0, "total_downhill": 0, ' + \
                      ' "segment_names": [], "title": "my_track_name"}'

        obj_track = track.Track(track_json=json_string)

        self.assertEqual(obj_track.df_track.shape, (0, 5))
        self.assertEqual(obj_track.size, 0)
        self.assertEqual(obj_track.extremes, [0, 0, 0, 0])
        self.assertAlmostEqual(obj_track.total_distance, 0)
        self.assertEqual(obj_track.total_uphill, 0)
        self.assertEqual(obj_track.total_downhill, 0)
        self.assertEqual(obj_track.title, "my_track_name")

    def test_rename_segment(self):
        # Load data
        obj_track = track.Track()
        obj_track.add_gpx(f'{self.test_path}/samples/island_1.gpx')
        obj_track.add_gpx(f'{self.test_path}/samples/island_2.gpx')
        obj_track.add_gpx(f'{self.test_path}/samples/island_3.gpx')

        obj_track.rename_segment(0, 'seg0')
        obj_track.rename_segment(1, 'seg1')
        obj_track.rename_segment(2, 'seg2')
        self.assertEqual(obj_track.segment_names, ['seg0', 'seg1', 'seg2'])
        self.assertFalse(obj_track.rename_segment(4, 'seg_4'))

    def test_get_summary(self):
        # Load data
        obj_track = track.Track()
        obj_track.add_gpx(f'{self.test_path}/samples/simple_numbers.gpx')
        obj_track.add_gpx(f'{self.test_path}/samples/simple_numbers.gpx')
        obj_track.rename_segment(0, 'seg0')
        obj_track.rename_segment(1, 'seg1')

        expected_dict = {
            'seg0': {
                'distance': '445.2 km',
                'uphill': '+20 m',
                'downhill': '-20 m'
            },
            'seg1': {
                'distance': '445.2 km',
                'uphill': '+20 m',
                'downhill': '-20 m'
            },
            'total': {
                'distance': '1335.6 km',
                'uphill': '+40 m',
                'downhill': '-40 m'
            }
        }
        summary = obj_track.get_summary()
        self.assertEqual(expected_dict, summary)

    def test_get_summary_no_track(self):
        # Load data
        obj_track = track.Track()

        expected_dict = {'total': {
            'distance': 'n/a',
            'uphill': 'n/a',
            'downhill': 'n/a'}}

        summary = obj_track.get_summary()
        self.assertEqual(expected_dict, summary)

    def test_missing_time_and_elevation(self):
        obj_track = track.Track()
        obj_track.add_gpx(
            os.path.join(self.test_path, 'samples', 'simple_numbers_no_time.gpx'))
        obj_track.add_gpx(
            os.path.join(self.test_path, 'samples', 'simple_numbers_no_ele.gpx'))
        obj_track.add_gpx(
            os.path.join(self.test_path, 'samples', 'simple_numbers.gpx'))
        obj_track.save_gpx('test_missing_time_and_elevation.gpx')

        obj_track_check = track.Track()
        obj_track_check.add_gpx('test_missing_time_and_elevation.gpx')

        self.assertFalse(pd.isnull(obj_track_check.df_track.time.iloc[0]))
        self.assertTrue(pd.isnull(obj_track_check.df_track.time.iloc[-1]))
        self.assertTrue(obj_track_check.df_track.ele.isnull().values.any())
