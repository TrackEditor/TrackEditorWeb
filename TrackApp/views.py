import os
import traceback
import math
from datetime import datetime

from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.conf import settings
from django.core.files.base import ContentFile

import libs.track as track
from libs.constants import Constants as c
from .models import User, Track, Upload
from libs.utils import id_generator, auto_zoom, randomize_filename


def index_view(request):
    if request.user.is_authenticated:
        number_pages = math.ceil(Track.objects.order_by("-last_edit").
                                 filter(user=request.user).count() / 10)
        return render(request, 'TrackApp/dashboard.html',
                      {'pages': list(range(1, number_pages + 1)),
                       'number_pages': number_pages,
                       'welcome': f'Hi, {request.user.username}!'})

    return render(request, 'TrackApp/index.html')


def register_view(request):
    template_register = 'TrackApp/register.html'

    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']

        # Ensure password matches confirmation
        password = request.POST['password']
        confirmation = request.POST['confirmation']
        if password != confirmation:
            return render(request, template_register, {
                'error': 'Passwords must match.'
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, template_register, {
                'error': 'Username already taken.'
            })
        login(request, user)
        return HttpResponseRedirect(reverse('index'))
    else:
        return render(request, template_register)


def login_view(request):
    template_login = 'TrackApp/login.html'

    if request.method == 'POST':

        # Attempt to sign user in
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse('index'))
        else:
            return render(request, template_login, {
                'error': 'Invalid username and/or password.'
            })
    else:
        return render(request, template_login)


def logout_view(request):
    logout(request)
    messages.success(request, 'See you soon!')
    return HttpResponseRedirect(reverse('index'))


@csrf_exempt
def combine_tracks(request):
    template_combine = 'TrackApp/combine_tracks.html'
    config = {'maximum_file_size': c.maximum_file_size,
              'maximum_files': c.maximum_files,
              'valid_extensions': c.valid_extensions}

    if request.method == 'POST':
        obj_track = track.Track()

        output_filename = \
            c.tool + '_combine_tracks_' + \
            datetime.now().strftime('%d%m%Y_%H%M%S') + '_' + \
            id_generator(size=8) + '.gpx'

        if len(request.FILES.getlist('document')) == 0:
            warning = 'No file has been selected.'
            return render(request, template_combine,
                          {'download': False,
                           'warning': warning,
                           **config})

        # try:
        # Load files
        if settings.USE_S3:
            for uploaded_file in request.FILES.getlist('document'):
                upload = Upload(file=uploaded_file)
                filename = randomize_filename(upload.file.url.split('/')[-1])
                upload.file.name = filename
                upload.save()

                with upload.file.open() as f:
                    gpx_file = f.read()
                    obj_track.add_gpx_bytes(file=gpx_file, filename=filename)

            upload_output = Upload(file=ContentFile(obj_track.get_gpx().encode('utf-8')))
            upload_output.file.name = output_filename
            output_url = upload_output.file.url
            upload_output.save()

        else:
            fs = FileSystemStorage()
            for uploaded_file in request.FILES.getlist('document'):
                filename = fs.save(uploaded_file.name, uploaded_file)
                filepath = os.path.join(fs.location, filename)
                obj_track.add_gpx(filepath)

            output_location = os.path.join(fs.location, output_filename)
            output_url = fs.url(output_filename)
            obj_track.save_gpx(output_location)

        # except Exception as e:
        #     error = 'Error loading files'
        #     print(e)
        #     return render(request, template_combine,
        #                   {'download': False,
        #                    'error': error,
        #                    **config})

        map_center = [sum(obj_track.extremes[2:]) / 2,
                      sum(obj_track.extremes[:2]) / 2]

        lat = []
        lon = []
        ele = []
        for s in obj_track.df_track.segment.unique():
            segment = obj_track.df_track[obj_track.df_track['segment'] == s]
            lat.append(list(segment['lat'].values))
            lon.append(list(segment['lon'].values))
            ele.append(list(segment['ele'].values))

        return render(request, template_combine,
                      {'download': True,
                       'file': output_url,
                       'lat': lat,
                       'lon': lon,
                       'ele': ele,
                       'map_center': map_center,
                       'map_zoom': auto_zoom(*obj_track.extremes),
                       **config})

    return render(request, template_combine,
                  {'download': False,
                   **config})


def insert_timestamp(request):
    template_timestamp = 'TrackApp/insert_timestamp.html'
    config = {'maximum_file_size': c.maximum_file_size,
              'maximum_speed': c.maximum_speed,
              'valid_extensions': c.valid_extensions}

    if request.method == 'POST':
        obj_track = track.Track()
        fs = FileSystemStorage()

        try:
            # Load file
            uploaded_file = request.FILES['document']
            filename = fs.save(uploaded_file.name, uploaded_file)
            filepath = os.path.join(fs.location, filename)

            time = request.POST['input_time']
            date = request.POST['input_date']
            speed = float(request.POST['input_desired_speed'])
            elevation_speed = request.POST['input_elevation_speed'] == 'True'

            initial_time = \
                datetime.strptime(f'{date}T{time}:00', '%Y-%m-%dT%H:%M:%S')

            obj_track.add_gpx(filepath)
            obj_track.insert_timestamp(initial_time, speed,
                                       consider_elevation=elevation_speed)

            # Process file
            output_filename = \
                c.tool + '_insert_timestamp_' + \
                datetime.now().strftime('%d%m%Y_%H%M%S') + '_' + \
                id_generator(size=8) + '.gpx'
            output_location = os.path.join(fs.location, output_filename)
            output_url = fs.url(output_filename)
            obj_track.save_gpx(output_location)

            map_center = [sum(obj_track.extremes[2:]) / 2,
                          sum(obj_track.extremes[:2]) / 2]

        except Exception as e:
            error = 'Error loading files'
            print(f'Exception: {e}')
            traceback.print_exc()
            return render(request, template_timestamp,
                          {'download': False,
                           'error': error,
                           **config})

        return render(request, template_timestamp,
                      {'download': True,
                       'file': output_url,
                       'lat': list(obj_track.df_track.lat.values),
                       'lon': list(obj_track.df_track.lon.values),
                       'ele': list(obj_track.df_track.ele.values),
                       'map_center': map_center,
                       'map_zoom': auto_zoom(*obj_track.extremes),
                       **config})

    return render(request, template_timestamp,
                  {'download': False,
                   **config})


def users_only(request):
    return render(request, 'TrackApp/login.html', {
        'warning':
            'The selected option is only available for users. Please, login or register.'
    })


@login_required
def get_tracks_from_db(request, page):
    all_tracks = Track.objects.order_by("-last_edit").filter(user=request.user)
    page_tracks = Paginator(all_tracks, 10).page(page).object_list

    response = []
    for page in page_tracks:
        response.append(
            {'id': page.id,
             'title': page.title,
             'last_edit': page.last_edit.strftime('%d %B %Y %H:%M')}
        )

    return JsonResponse(response, safe=False)


@login_required
def dashboard(request):
    number_pages = math.ceil(Track.objects.order_by("-last_edit").
                             filter(user=request.user).count() / 10)
    return render(request, 'TrackApp/dashboard.html',
                  {'pages': list(range(1, number_pages + 1)),
                   'number_pages': number_pages})
