"""TRACK
The track class defines how the loaded GPX files are internally represented.
Each of them is loaded in one Track object as a segment. It includes methods
to manipulate these segments. From the user perspective, this manipulation is
carried out througout the Edit Menu.

Author: alguerre
License: MIT
"""
import datetime as dt
import pandas as pd
import numpy as np
import geopy.distance
import gpxpy.gpx
import json
import os
import io
from time import time

from libs import constants as c, gpx


class Track:
    """
    This class is designed to store gpx like data consisting of latitude-
    longitude-elevation-time and manipulate them. All these operations are
    done with pandas.
    The data representation is:
        - A pandas dataframe stores all data
        - segments: each compoment of the track, each gpx file is a segment
        - The dataframe have some extra columns not from gpx file, like
        cumulated distance or elevation.
        - Properties to store overall information
    """
    def __init__(self, track_json=None):
        # Define dataframe and types
        self.columns = ['lat', 'lon', 'ele', 'segment', 'time']
        self.df_track = pd.DataFrame(columns=self.columns)
        self._force_columns_type()

        # General purpose properties
        self.size = 0  # number of gpx in track
        self.last_segment_idx = 0
        self.extremes = [0, 0, 0, 0]  # lat min, lat max, lon min, lon max
        self.total_distance = 0
        self.total_uphill = 0
        self.total_downhill = 0
        self.segment_names = []  # indexing in line with segment index, diff 1
        self.title = 'track_name (edit me)'

        if track_json:
            self.from_json(track_json)

    def __str__(self):
        return f'title: {self.title}\n' + \
               f'df_track: \n{self.df_track.head(3)}\n' + \
               f'{self.df_track.tail(3)}\n\n' + \
               f'shape: {self.df_track.shape}\n' + \
               f'size: {self.size}\n' + \
               f'last_segment_idx: {self.last_segment_idx}\n' + \
               f'extremes: {self.extremes}\n' + \
               f'total_distance: {self.total_distance}\n' + \
               f'total_uphill: {self.total_uphill}\n' + \
               f'total_downhill: {self.total_downhill}\n' + \
               f'segment_names: {self.segment_names}\n'

    def __eq__(self, other):
        for col in self.columns:
            if not self.df_track[col].equals(other.df_track[col]):
                return False
        return True

    def to_json(self) -> str:
        if self.size > 0:
            # Convert objet to json file
            copy_df_track = self.df_track.copy().drop(columns=['time'])
            # TODO manage time
            track_dict = copy_df_track.to_dict('list')
            track_dict['size'] = float(self.size)
            track_dict['last_segment_idx'] = int(self.last_segment_idx)
            track_dict['extremes'] = list(map(float, self.extremes))
            track_dict['total_distance'] = float(self.total_distance)
            track_dict['total_uphill'] = float(self.total_uphill)
            track_dict['total_downhill'] = float(self.total_downhill)
            track_dict['segment_names'] = self.segment_names
            track_dict['title'] = self.title
            return json.dumps(track_dict)
        else:
            track_dict = {'lat': {}, 'lon': {}, 'ele': {}, 'segment': {},
                          'ele_pos_cum': {}, 'ele_neg_cum': {}, 'distance': {},
                          'size': 0, 'last_segment_idx': 0,
                          'extremes': [0, 0, 0, 0], 'total_distance': 0,
                          'total_uphill': 0, 'total_downhill': 0,
                          'segment_names': [], 'title': self.title}
            return json.dumps(track_dict)

    def from_json(self, json_string: str) -> bool:
        json_dict = json.loads(json_string)
        if json_dict['size'] == 0:
            if 'title' in json_dict:
                if json_dict['title']:
                    self.title = json_dict['title']
            return False  # there are no data to load

        df_keys = ['lat', 'lon', 'ele', 'segment',
                   'ele_pos_cum', 'ele_neg_cum', 'distance']

        df_dict = dict((k, json_dict[k]) for k in df_keys if k in json_dict)

        # Load dataframe
        self.df_track = pd.DataFrame(df_dict)
        self.insert_timestamp(dt.datetime(2000, 1, 1, 0, 0, 0), 1)
        # TODO consider time within json
        self._force_columns_type()

        # Load metadata
        self.size = json_dict['size']
        self.last_segment_idx = json_dict['last_segment_idx']
        self.extremes = json_dict['extremes']
        self.total_distance = json_dict['total_distance']
        self.total_uphill = json_dict['total_uphill']
        self.total_downhill = json_dict['total_downhill']
        self.segment_names = json_dict['segment_names']
        self.title = json_dict['title']

        return True

    def add_gpx(self, file: str):
        gpx_track = gpx.Gpx(file)
        df_gpx = gpx_track.to_pandas()
        df_gpx = df_gpx[self.columns]
        self.size += 1
        self.last_segment_idx += 1
        df_gpx['segment'] = self.last_segment_idx

        self.df_track = pd.concat([self.df_track, df_gpx])
        self.df_track = self.df_track.reset_index(drop=True)
        self.update_summary()  # for full track
        self.segment_names.append(os.path.basename(file))
        self._force_columns_type()

    def get_segment(self, index: int):
        return self.df_track[self.df_track['segment'] == index]

    def reverse_segment(self, index: int):
        segment = self.get_segment(index)
        time = self.df_track.time  # using time is problematic, is managed
        # separately
        segment = segment.drop(columns=['time'])

        rev_segment = pd.DataFrame(segment.values[::-1],
                                   segment.index,
                                   segment.columns)
        rev_segment['time'] = time[::-1]
        self.df_track.loc[self.df_track['segment'] == index] = rev_segment
        self._force_columns_type()  # ensure proper type for columns

        self.update_summary()  # for full track

    def _get_speed_factor_to_slope(self, slope: float) -> float:
        """
        Get param_a speed factor to compensate the mean speed with slope
        effects.
        Uphill the speed is reduced up to 1/3 when slope is -20%.
        Downhill the speed is increased up to 3 times when slops is +20%.
        The equation has been got using the matlab fitting tool in the set of
        inputs values:
        Flat terrain: x = linspace(-0.5, 0.5, 10);
                      y = linspace(1.05, 0.95, 10);
        Uphill terrain: x = linspace(-18, -20, 10);
                        y = linspace(2.8, 3.0, 10);
        Downhill terrain: x = linspace(18, 20, 10);
                          y = linspace(1/2.8, 1/3, 10);
        Formula to express slope in %:
            angle % = tan(angle) * 100%

        :param slope: in %
        :return: speed factor
        """

        param_a = 1.005
        param_b = -0.05725
        param_c = -1.352e-8
        param_d = 0.8164

        if slope < 0:
            param_b = -0.07  # accelerate the model when downhill

        if slope > 17.8:  # at this point the speed is x1/3
            speed_factor = 1 / 3
        elif slope < -15.9:    # at this point the speed is x3
            speed_factor = 3
        else:
            speed_factor = param_a * np.exp(param_b * slope) + \
                           param_c * np.exp(param_d * slope)

        return speed_factor

    def insert_timestamp(self, initial_time: dt.datetime,
                         desired_speed: float,
                         consider_elevation: bool = False):
        if not consider_elevation:
            self.df_track['time'] = \
                self.df_track.apply(
                    lambda row:
                    initial_time +
                    dt.timedelta(
                        seconds=round(
                            3600 * row['distance'] / desired_speed, 3
                        )),
                    axis=1)
        else:
            ele_diff = np.diff(self.df_track['ele'].values)
            dist_diff = np.diff(self.df_track['distance'].values)

            # Remove 0 diff distances, not moving
            self.df_track = self.df_track[np.append(dist_diff != 0, True)]
            ele_diff = ele_diff[dist_diff != 0]
            dist_diff = dist_diff[dist_diff != 0]

            slope = np.tan(np.arcsin(1e-3 * ele_diff/dist_diff)) * 100
            slope -= np.mean(slope)  # when mean slope mean speed
            speed_factor = np.array(
                list(map(self._get_speed_factor_to_slope, slope))
            )
            speed_elevation = desired_speed * speed_factor

            used_time = 0
            start = time()
            avg_speed = desired_speed * 10
            time_delta = np.nan  # this default value would force and error

            while abs(avg_speed - desired_speed) > 0.05 * desired_speed and \
                    used_time < 0.5:
                time_delta = dist_diff / speed_elevation
                avg_speed = sum(dist_diff)/sum(time_delta)
                speed_elevation -= avg_speed - desired_speed
                used_time = time() - start

            relative_time = np.append(0, np.cumsum(time_delta))
            self.df_track['relative_time'] = relative_time
            self.df_track['time'] = \
                self.df_track.apply(
                    lambda row:
                    initial_time +
                    dt.timedelta(seconds=round(3600*row['relative_time'], 3)),
                    axis=1)

    def save_gpx(self, gpx_filename: str, exclude_time=False):
        # Sort by timestamp
        self.df_track = self.df_track.sort_values(by=['time'],
                                                  ascending=True,
                                                  na_position='last')

        # Create track
        ob_gpxpy = gpxpy.gpx.GPX()
        gpx_track = gpxpy.gpx.GPXTrack()
        ob_gpxpy.tracks.append(gpx_track)

        # Insert default metadata
        ob_gpxpy.creator = c.device
        ob_gpxpy.author_email = c.author_email
        ob_gpxpy.description = c.description
        ob_gpxpy.author_name = c.author_name

        # Create segments in track
        for seg_id in self.df_track.segment.unique():
            gpx_segment = gpxpy.gpx.GPXTrackSegment()
            gpx_track.segments.append(gpx_segment)

            df_segment = self.get_segment(seg_id)

            # Insert points to segment
            for idx in df_segment.index:
                latitude = df_segment.loc[idx, 'lat']
                longitude = df_segment.loc[idx, 'lon']
                elevation = df_segment.loc[idx, 'ele']
                time = df_segment.loc[idx, 'time']

                if pd.isnull(time) and pd.isnull(elevation):
                    gpx_point = gpxpy.gpx.GPXTrackPoint(latitude, longitude)
                elif pd.isnull(time) or exclude_time:
                    gpx_point = gpxpy.gpx.GPXTrackPoint(latitude, longitude,
                                                        elevation=elevation)
                elif pd.isnull(elevation):
                    gpx_point = gpxpy.gpx.GPXTrackPoint(latitude, longitude,
                                                        time=time)
                else:
                    gpx_point = gpxpy.gpx.GPXTrackPoint(latitude, longitude,
                                                        elevation=elevation,
                                                        time=time)
                gpx_segment.points.append(gpx_point)

        # Write file
        with io.open(gpx_filename, 'w', newline='\n') as f:
            f.write(ob_gpxpy.to_xml())

    def smooth_elevation(self, index: int):
        # Apply moving average to fix elevation

        df_segment = self.get_segment(index)
        elevation = df_segment.ele.to_numpy()

        # Moving average
        n = int(np.ceil(df_segment.shape[0]*0.05))
        elevation_ma = self._moving_average(elevation, n)

        # Concatenate moving average and initial line
        smooth_elevation = np.concatenate(
            (np.array([elevation[0] + i*(elevation_ma[0]-elevation[0])/n
                       for i in range(1, n)]),
             elevation_ma)
        )

        # Insert new elevation in track
        df_segment = df_segment.drop(columns=['ele'])
        df_segment['ele'] = smooth_elevation
        self.df_track.loc[self.df_track['segment'] == index] = df_segment

    # flake8: noqa: E712
    def fix_elevation(self, index: int):
        df_segment = self.get_segment(index)

        # Identify and remove steep zones
        steep_zone = [False] * df_segment.shape[0]
        last_steep = 0

        for i, (e, d) in enumerate(zip(df_segment['ele'].diff(),
                                       df_segment['distance'])):
            if abs(e) > c.steep_gap:
                steep_zone[i] = True
                last_steep = d

            elif d - last_steep < c.steep_distance:
                if d > c.steep_distance:
                    steep_zone[i] = True

        df_segment['steep_zone'] = steep_zone
        df_no_steep = df_segment.copy()
        df_no_steep['ele_to_fix'] = np.where(df_segment['steep_zone'] == False,
                                             df_segment['ele'], -1)

        # Fill steep zones
        fixed_elevation = df_no_steep['ele_to_fix'].copy().to_numpy()
        original_elevation = df_no_steep['ele'].copy().to_numpy()
        fixed_steep_zone = df_no_steep['steep_zone'].copy()
        before_x = before_y = after_x = after_y = None

        for i in range(1, len(fixed_elevation)):
            if not df_no_steep['steep_zone'].loc[i - 1] and \
                    df_no_steep['steep_zone'].loc[i]:
                before_x = np.arange(i - 11, i - 1)
                before_y = fixed_elevation[i - 11:i - 1]
                after_x = None
                after_y = None

            if df_no_steep['steep_zone'].loc[i - 1] and not \
                    df_no_steep['steep_zone'].loc[i]:
                after_x = np.arange(i, i + 10)
                after_y = fixed_elevation[i:i + 10]
                coef = np.polyfit(np.concatenate((before_x, after_x)),
                                  np.concatenate((before_y, after_y)),
                                  3)
                for i in range(before_x[-1], after_x[0]):
                    fixed_elevation[i] = np.polyval(coef, i)
                    fixed_steep_zone[i] = False

        # Apply moving average on tail
        if after_y is None and after_x is None:
            n = c.steep_k_moving_average
            fixed_elevation[before_x[-1]:] = np.concatenate((
                original_elevation[before_x[-1]:before_x[-1] + n - 1],
                self._moving_average(original_elevation[before_x[-1]:], n)))
            fixed_steep_zone[before_x[-1]:] = True

        # Insert new elevation in track
        df_segment['ele'] = fixed_elevation
        self.df_track.loc[self.df_track['segment'] == index] = df_segment

    def remove_segment(self, index: int):
        # Drop rows in dataframe
        idx_segment = self.df_track[(self.df_track['segment'] == index)].index
        self.df_track = self.df_track.drop(idx_segment)
        self.df_track = self.df_track.reset_index(drop=True)
        self.size -= 1
        self.segment_names[index-1] = None

        # Update metadata
        self.update_summary()

        # Clean full track if needed
        if self.size == 0:
            self.df_track = self.df_track.drop(self.df_track.index)

        return self.size

    def divide_segment(self, div_index: int):
        """
        :param div_index: refers to the index of the full df_track, not segment
        """
        self.df_track['index'] = self.df_track.index

        def segment_index_modifier(row):
            if row['index'] < div_index:
                return row['segment']
            else:
                return row['segment'] + 1

        self.df_track['segment'] = \
            self.df_track.apply(lambda row: segment_index_modifier(row),
                                axis=1)

        self.df_track = self.df_track.drop(['index'], axis=1)
        self.size += 1
        self.last_segment_idx = max(self.df_track['segment'])

        return True

    def change_order(self, new_order: dict):
        if len(new_order.keys()) != len(self.df_track.segment.unique()):
            raise ValueError('Wrong new_order dict in change_order')

        self.df_track.segment = self.df_track.apply(
            lambda row: new_order[row.segment],
            axis=1)

        self.df_track['index1'] = self.df_track.index
        self.df_track = self.df_track.sort_values(by=['segment', 'index1'])
        self.df_track = self.df_track.drop(labels=['index1'], axis=1)
        self.df_track = self.df_track.reset_index(drop=True)

        new_order_list = [new_order[i] for i in sorted(list(new_order.keys()))]
        self.segment_names = [self.segment_names[i-1] for i in new_order_list]
        self.update_summary()  # for full track

    def rename_segment(self, index: int, new_name: str) -> bool:
        try:
            self.segment_names[index] = new_name
        except IndexError:
            return False
        return True

    def _moving_average(self, a, n: int = 3):
        """
        Naive moving average implementation
        :param a: numpy array
        :param n: point mean values
        :return: smooth numpy array
        """
        ret = np.cumsum(a, dtype=float)
        ret[n:] = ret[n:] - ret[:-n]
        return ret[n - 1:] / n

    def update_summary(self):
        self._insert_positive_elevation()
        self._insert_negative_elevation()
        self._insert_distance()
        self._update_extremes()
        self.total_distance = self.df_track.distance.iloc[-1]
        self.total_uphill = self.df_track.ele_pos_cum.iloc[-1]
        self.total_downhill = self.df_track.ele_neg_cum.iloc[-1]

    def get_summary(self):
        summary = {}

        if self.size == 0:
            return {'total': {
                'distance': 'n/a',
                'uphill': 'n/a',
                'downhill': 'n/a'}}

        for seg_id in self.df_track.segment.unique():
            distance_lbl = \
                SummaryUtils.get_distance_label(self, segment_id=seg_id)
            gained_elevation_lbl = \
                SummaryUtils.get_elevation_label(self,
                                                 'ele_pos_cum',
                                                 segment_id=seg_id)
            lost_elevation_lbl = \
                SummaryUtils.get_elevation_label(self,
                                                 'ele_neg_cum',
                                                 segment_id=seg_id)
            summary[self.segment_names[seg_id-1]] = \
                {'distance': distance_lbl,
                 'uphill': gained_elevation_lbl,
                 'downhill': lost_elevation_lbl}

        distance_lbl = SummaryUtils.get_distance_label(self, -1, total=True)
        gained_elevation_lbl = \
            SummaryUtils.get_elevation_label(self, 'ele_pos_cum', total=True)
        lost_elevation_lbl = \
            SummaryUtils.get_elevation_label(self, 'ele_neg_cum', total=True)

        summary['total'] = \
            {'distance': distance_lbl,
             'uphill': gained_elevation_lbl,
             'downhill': lost_elevation_lbl}

        return summary

    def _force_columns_type(self):
        # At some points it is needed to ensure the data type of each column
        self.df_track['lat'] = self.df_track['lat'].astype('float32')
        self.df_track['lon'] = self.df_track['lon'].astype('float32')
        self.df_track['ele'] = self.df_track['ele'].astype('float32')
        self.df_track['segment'] = self.df_track['segment'].astype('int32')
        self.df_track['time'] = pd.to_datetime(self.df_track['time'], utc=True)

    def _insert_positive_elevation(self):
        self.df_track['ele diff'] = self.df_track['ele'].diff()
        negative_gain = self.df_track['ele diff'] < 0
        self.df_track.loc[negative_gain, 'ele diff'] = 0

        # Define new column
        self.df_track['ele_pos_cum'] = \
            self.df_track['ele diff'].cumsum().astype('float32')

        # Drop temporary columns
        self.df_track = self.df_track.drop(labels=['ele diff'], axis=1)

    def _insert_negative_elevation(self):
        self.df_track['ele diff'] = self.df_track['ele'].diff()
        negative_gain = self.df_track['ele diff'] > 0
        self.df_track.loc[negative_gain, 'ele diff'] = 0

        # Define new column
        self.df_track['ele_neg_cum'] = \
            self.df_track['ele diff'].cumsum().astype('float32')

        # Drop temporary columns
        self.df_track = self.df_track.drop(labels=['ele diff'], axis=1)

    def _insert_distance(self):
        # Shift latitude and longitude (such way that first point is 0km)
        self.df_track['lat_shift'] = pd.concat(
            [pd.Series(np.nan), self.df_track.lat[0:-1]]). \
            reset_index(drop=True)
        self.df_track['lon_shift'] = pd.concat(
            [pd.Series(np.nan), self.df_track.lon[0:-1]]). \
            reset_index(drop=True)

        def compute_distance(row):
            from_coor = (row.lat, row.lon)
            to_coor = (row.lat_shift, row.lon_shift)
            try:
                return abs(geopy.distance.geodesic(from_coor, to_coor).km)
            except ValueError:
                return 0

        # Define new columns
        self.df_track['p2p_distance'] = self.df_track.apply(compute_distance,
                                                            axis=1)
        self.df_track['distance'] = \
            self.df_track.p2p_distance.cumsum().astype('float32')

        # Drop temporary columns
        self.df_track = self.df_track.drop(
            labels=['lat_shift', 'lon_shift', 'p2p_distance'], axis=1)

    def _update_extremes(self):
        self.extremes = \
            (self.df_track["lat"].min(), self.df_track["lat"].max(),
             self.df_track["lon"].min(), self.df_track["lon"].max())


class SummaryUtils:
    @staticmethod
    def get_distance_label(ob_track: Track, segment_id: int = 1,
                           total: bool = False) -> str:
        if total:
            distance = ob_track.total_distance
        else:
            segment = ob_track.get_segment(segment_id)
            first = segment.iloc[0]
            last = segment.iloc[-1]

            if np.isnan(first['distance']):
                distance = last['distance']
            else:
                distance = last['distance'] - first['distance']

        if distance < 5:
            label = f'{distance:.2f} km'
        else:
            label = f'{distance:.1f} km'

        return label

    @staticmethod
    def get_elevation_label(ob_track: Track, magnitude: str,
                            segment_id: int = 1, total: bool = False) -> str:
        if total:
            if 'pos' in magnitude:
                elevation = ob_track.total_uphill
            elif 'neg' in magnitude:
                elevation = ob_track.total_downhill
            else:
                elevation = 0
        else:
            segment = ob_track.get_segment(segment_id)
            first = segment.iloc[0]
            last = segment.iloc[-1]

            if np.isnan(first[magnitude]):
                elevation = last[magnitude]
            else:
                elevation = last[magnitude] - first[magnitude]

        if abs(elevation) < 10:
            label = f'{elevation:.1f} m'
        else:
            label = f'{int(elevation)} m'

        if elevation > 0:
            label = f'+{label}'

        return label
