import os
from datetime import datetime
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect  # , JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage

from . import track
from . import constants as c
from .models import User
from .utils import id_generator


def index_view(request):
    return render(request, 'TrackApp/index.html')


def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']

        # Ensure password matches confirmation
        password = request.POST['password']
        confirmation = request.POST['confirmation']
        if password != confirmation:
            return render(request, 'TrackApp/register.html', {
                'message': 'Passwords must match.'
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, 'TrackApp/register.html', {
                'message': 'Username already taken.'
            })
        login(request, user)
        return HttpResponseRedirect(reverse('index'))
    else:
        return render(request, 'TrackApp/register.html')


def login_view(request):
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
            return render(request, 'TrackApp/login.html', {
                'message': 'Invalid username and/or password.'
            })
    else:
        return render(request, 'TrackApp/login.html')


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('index'))


@csrf_exempt
def combine_tracks(request):
    config = {'maximum_file_size': c.maximum_file_size,
              'maximum_files': c.maximum_files,
              'valid_extensions': c.valid_extensions}

    if request.method == 'POST':
        obj_track = track.Track()
        fs = FileSystemStorage()

        if len(request.FILES.getlist('document')) == 0:
            warning = 'No file has been selected.'
            return render(request, 'TrackApp/combine_tracks.html',
                          {'download': False,
                           'warning': warning,
                           **config})

        try:
            for uploaded_file in request.FILES.getlist('document'):
                filename = fs.save(uploaded_file.name, uploaded_file)
                filepath = os.path.join(fs.location, filename)
                obj_track.add_gpx(filepath)
        except Exception as e:
            error = 'Error loading files'
            print(e)
            return render(request, 'TrackApp/combine_tracks.html',
                          {'download': False,
                           'error': error,
                           **config})

        try:
            output_filename = \
                c.tool + '_combine_tracks_' + \
                datetime.now().strftime('%d%m%Y_%H%M%S') + '_' + \
                id_generator(size=8) + '.gpx'
            output_location = os.path.join(fs.location, output_filename)
            output_url = fs.url(output_filename)
            obj_track.save_gpx(output_location)
        except Exception as e:
            error = 'Error processing files'
            print(e)
            return render(request, 'TrackApp/combine_tracks.html',
                          {'download': False,
                           'error': error,
                           **config})

        return render(request, 'TrackApp/combine_tracks.html',
                      {'download': True,
                       'file': output_url,
                       **config})

    return render(request, 'TrackApp/combine_tracks.html',
                  {'download': False,
                   **config})


def insert_timestamp(request):
    config = {'maximum_file_size': c.maximum_file_size,
              'maximum_speed': c.maximum_speed,
              'valid_extensions': c.valid_extensions}

    if request.method == 'POST':
        obj_track = track.Track()
        fs = FileSystemStorage()

        try:
            uploaded_file = request.FILES['document']
            filename = fs.save(uploaded_file.name, uploaded_file)
            filepath = os.path.join(fs.location, filename)

            time = request.POST['input_time']
            date = request.POST['input_date']
            speed = float(request.POST['input_desired_speed'])
            elevation_speed = request.POST['input_elevation_speed'] == 'True'
            # TODO elevation_speed is not considered by insert_timestamp method

            initial_time = \
                datetime.strptime(f'{date}T{time}:00', '%Y-%m-%dT%H:%M:%S')

            obj_track.add_gpx(filepath)
            obj_track.insert_timestamp(initial_time, speed)

        except Exception as e:
            error = 'Error loading files'
            print(e)
            return render(request, 'TrackApp/insert_timestamp.html',
                          {'download': False,
                           'error': error,
                           **config})

        try:
            output_filename = \
                c.tool + '_insert_timestamp_' + \
                datetime.now().strftime('%d%m%Y_%H%M%S') + '_' + \
                id_generator(size=8) + '.gpx'
            output_location = os.path.join(fs.location, output_filename)
            output_url = fs.url(output_filename)
            obj_track.save_gpx(output_location)
        except Exception as e:
            error = 'Error processing file'
            print(e)
            return render(request, 'TrackApp/insert_timestamp.html',
                          {'download': False,
                           'error': error,
                           **config})

        return render(request, 'TrackApp/insert_timestamp.html',
                      {'download': True,
                       'file': output_url,
                       **config})

    return render(request, 'TrackApp/insert_timestamp.html',
                  {'download': False,
                   **config})
