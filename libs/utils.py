"""UTILS
General purpose functions

Author: alguerre
License: MIT
"""
import hashlib
import string
import random
import math

from libs.constants import Constants as c


def md5sum(file: str) -> str:
    """
    Create a strings with the md5 of a given file
    :param file: filename of the file whose md5 is computed for
    :return: md5 string
    """
    md5_hash = hashlib.md5()

    with open(file, "rb") as file:
        content = file.read()

    md5_hash.update(content)

    digest = md5_hash.hexdigest()

    return digest


def id_generator(size=6):
    """
    Creates a string with random characters
    :param size: length of the output string
    :return: random string
    """
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(size))


def deg2num(lat_deg: float, lon_deg: float, zoom: int) -> (int, int):
    """
    Get OSM tiles from coordinates and zoom.
    :param lat_deg: latitude in degrees
    :param lon_deg: longitude in degrees
    :param zoom: zoom grade
    :return: x-y tile
    """
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return xtile, ytile


def auto_zoom(lat_min: float, lat_max: float,
              lon_min: float, lon_max: float) -> int:
    """
    Compute the best zoom to show a complete track. It must contain the full
    track in a box of nxn tails (n is specified in constants.py).
    :param lat_min: furthest south point
    :param lon_min: furthest west point
    :param lat_max: furthest north point
    :param lon_max: furthest east point
    :return: zoom to use to show full track
    """
    if lat_min == lat_max == lon_min == lon_max == 0:
        return 1

    for zoom in range(c.max_zoom):
        num_x_min, num_y_min = deg2num(lat_min, lon_min, zoom)
        num_x_max, num_y_max = deg2num(lat_max, lon_max, zoom)

        width = abs(num_x_max - num_x_min)
        height = abs(num_y_max - num_y_min)

        if width > c.map_size or height > c.map_size:
            return zoom - 1  # in this case previous zoom is the good one

        if (width == c.map_size and height < c.map_size) or \
                (width < c.map_size and height == c.map_size):
            # this provides bigger auto_zoom than using >= in previous case
            return zoom - 1

    return c.max_zoom


def map_center(lat_min: float, lat_max: float,
               lon_min: float, lon_max: float) -> list[float]:
    return [(lon_min + lon_max) / 2, (lat_min + lat_max) / 2]


def randomize_filename(filename: str):
    """
    Insert a random string into a filename to obtain a (almost)unique name
    """
    filename_split = filename.split('.', 1)
    filename_split.insert(1, '_' + id_generator() + '.')
    return ''.join(filename_split)
