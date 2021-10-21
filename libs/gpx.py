"""GPX
This module manages load and save operations on GPX files.

Author: alguerre
License: MIT
"""
import os
import pandas as pd
import numpy as np
import gpxpy

from libs.constants import Constants as c


class LoadGpxError(Exception):
    pass


class Gpx:
    """
    Management of load and save operations for GPX files.
    """
    def __init__(self):
        # Private attributes
        self.filename = None
        self.filepath = None
        self._state = False
        self._gpx = None
        self._gpx_dict = None

        # Public attributes
        self.df = None

    @classmethod
    def from_path(cls, filepath: str):
        gpx = cls()
        gpx.filename = os.path.basename(filepath)
        gpx.filepath = os.path.abspath(filepath)

        if os.stat(filepath).st_size < c.maximum_file_size:
            try:
                with open(filepath, 'r') as gpx_file:
                    gpx._gpx = gpxpy.parse(gpx_file)
                return gpx

            except Exception as e:
                raise LoadGpxError(f'Not able to load {gpx.filename} - {e}')

        else:
            raise LoadGpxError(f'Too big file: {gpx.filename}')

    @classmethod
    def from_bytes(cls, file: bytes, filename: str):
        gpx = cls()
        gpx.filename = filename

        try:
            gpx._gpx = gpxpy.parse(file)
            return gpx

        except Exception as e:
            raise LoadGpxError(f'Not able to load {gpx.filename} - {e}')

    def to_dict(self):
        self._gpx_dict = {'lat': [], 'lon': [], 'ele': [], 'time': [],
                          'track': [], 'segment': []}

        n_tracks = len(self._gpx.tracks)
        n_segments = [len(track.segments) for track in self._gpx.tracks]

        for i_track in range(n_tracks):
            for i_seg in range(n_segments[i_track]):
                for i_point in self._gpx.tracks[i_track].segments[i_seg].points:
                    self._gpx_dict['lat'].append(i_point.latitude)
                    self._gpx_dict['lon'].append(i_point.longitude)
                    self._gpx_dict['ele'].append(i_point.elevation if i_point.elevation else np.nan)
                    self._gpx_dict['time'].append(i_point.time if i_point.time else np.nan)
                    self._gpx_dict['track'].append(i_seg)
                    self._gpx_dict['segment'].append(i_track)
        return self._gpx_dict

    def to_pandas(self):
        if not self._gpx_dict:
            self.to_dict()

        self.df = pd.DataFrame(self._gpx_dict,
                               columns=['lat', 'lon', 'ele',
                                        'time', 'track', 'segment'])

        self.df['time'] = pd.to_datetime(self.df['time'], utc=True)

        return self.df.copy()
