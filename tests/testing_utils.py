import os
from urllib.parse import urljoin
from selenium import webdriver

from TrackApp.models import User, Track
from libs import track


def login(driver: webdriver,
          live_server_url: str,
          username: str,
          password: str):
    driver.get(urljoin(live_server_url, 'login'))
    driver.find_element_by_id('input_txt_username').send_keys(username)
    driver.find_element_by_id('input_txt_password').send_keys(password)
    driver.find_element_by_id('input_btn_login').click()


def create_user(username: str = 'default_user',
                password: str = 'default_password_1234',
                email: str = 'default_user@example.com'):
    if not User.objects.filter(username=username):
        user = User.objects.create(username=username,
                                   email=email,
                                   password='!')
        user.set_password(password)
        user.save()
    else:
        user = User.objects.get(username=username)
    return user


def get_downloads_dir():
    return os.path.join(os.path.expanduser('~'), 'Downloads')


def get_webdriver(headless: bool = True):
    options = webdriver.ChromeOptions()
    options.headless = headless
    downloads_dir = get_downloads_dir()
    preferences = \
        {'download.default_directory': downloads_dir,
         'safebrowsing.enabled': 'false'}
    options.add_experimental_option('prefs', preferences)

    driver = webdriver.Chrome(chrome_options=options)
    return driver


def compare_tracks(reference_file: str, checked_file: str):
    track_ref = track.Track().add_gpx(reference_file)
    track_check = track.Track().add_gpx(checked_file)

    return track_ref == track_check


def record_tracks(user: User, n: int, title='title'):
    for i in range(n):
        Track(user=user,
              track=track.Track().to_json(),
              title=f'{title}_{i}').save()
