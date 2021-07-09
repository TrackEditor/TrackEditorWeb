"""UTILS
General purpose functions

Author: alguerre
License: MIT
"""
import hashlib
import string
import random


def md5sum(file: str) -> str:
    """
    Create a strings with the md5 of a given file
    :param file: filename of the file whose md5 is computed for
    :return: md5 string
    """
    md5_hash = hashlib.md5()

    a_file = open(file, "rb")
    content = a_file.read()
    md5_hash.update(content)

    digest = md5_hash.hexdigest()

    return digest


def id_generator(size=6):
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(size))
