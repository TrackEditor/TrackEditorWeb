import os
import traceback
import json
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

from . import track
from . import constants as c
from .models import User, Track
from .utils import id_generator, auto_zoom

# DEBUGGING
import pandas
pandas.set_option('display.max_rows', None)
pandas.set_option('display.max_columns', None)
pandas.set_option('display.max_colwidth', None)
pandas.set_option('display.expand_frame_repr', False)


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
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']

        # Ensure password matches confirmation
        password = request.POST['password']
        confirmation = request.POST['confirmation']
        if password != confirmation:
            return render(request, 'TrackApp/register.html', {
                'error': 'Passwords must match.'
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, 'TrackApp/register.html', {
                'error': 'Username already taken.'
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
                'error': 'Invalid username and/or password.'
            })
    else:
        return render(request, 'TrackApp/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'See you soon!')
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
            # Load files
            for uploaded_file in request.FILES.getlist('document'):
                filename = fs.save(uploaded_file.name, uploaded_file)
                filepath = os.path.join(fs.location, filename)
                obj_track.add_gpx(filepath)

            # Process files
            output_filename = \
                c.tool + '_combine_tracks_' + \
                datetime.now().strftime('%d%m%Y_%H%M%S') + '_' + \
                id_generator(size=8) + '.gpx'
            output_location = os.path.join(fs.location, output_filename)
            output_url = fs.url(output_filename)
            obj_track.save_gpx(output_location)

        except Exception as e:
            error = 'Error loading files'
            print(e)
            return render(request, 'TrackApp/combine_tracks.html',
                          {'download': False,
                           'error': error,
                           **config})

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

        return render(request, 'TrackApp/combine_tracks.html',
                      {'download': True,
                       'file': output_url,
                       'lat': lat,
                       'lon': lon,
                       'ele': ele,
                       'map_center': map_center,
                       'map_zoom': auto_zoom(*obj_track.extremes),
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

        except Exception as e:
            error = 'Error loading files'
            print(f'Exception: {e}')
            traceback.print_exc()
            return render(request, 'TrackApp/insert_timestamp.html',
                          {'download': False,
                           'error': error,
                           **config})

        return render(request, 'TrackApp/insert_timestamp.html',
                      {'download': True,
                       'file': output_url,
                       'lat': list(obj_track.df_track.lat.values),
                       'lon': list(obj_track.df_track.lon.values),
                       'ele': list(obj_track.df_track.ele.values),
                       **config})

    return render(request, 'TrackApp/insert_timestamp.html',
                  {'download': False,
                   **config})


def users_only(request):
    return render(request, 'TrackApp/login.html', {
        'warning': 'The selected option is only available for users. Please, login or register.'
    })


@login_required
def editor(request, index=None):
    config = {'maximum_file_size': c.maximum_file_size,
              'maximum_files': c.maximum_files,
              'valid_extensions': c.valid_extensions}

    if index:  # load existing session
        request.session['json_track'] = Track.objects.get(id=index).track
        request.session['index_db'] = index
        json_track = json.loads(request.session['json_track'])
        obj_track = track.Track(track_json=request.session['json_track'])

        return render(
            request,
            'TrackApp/editor.html',
            {'track_list': [n for n in json_track['segment_names'] if n],
             'segment_list': list(set(json_track['segment'])),
             'title': json_track['title'],
             **config})

    if 'index_db' in request.session:
        index = request.session['index_db']

    print(f'{index=}')
    if request.method == 'POST':  # add files to session
        fs = FileSystemStorage()
        uploaded_file = request.FILES['document']
        filename = fs.save(uploaded_file.name, uploaded_file)
        filepath = os.path.join(fs.location, filename)

        obj_track = track.Track(track_json=request.session['json_track'])
        obj_track.add_gpx(filepath)

        request.session['json_track'] = obj_track.to_json()

        # debug prints
        print('--- ADD GPX ---')
        print(obj_track)

        return render(request, 'TrackApp/editor.html',
                      {'track_list': [n for n in obj_track.segment_names if n],
                       'segment_list': list(obj_track.df_track['segment'].unique()),
                       'title': obj_track.title,
                       **config})

        # TODO control exceptions

    # Create new session
    request.session['json_track'] = track.Track().to_json()
    request.session['index_db'] = None
    return render(request, 'TrackApp/editor.html', {**config})


@login_required
@csrf_exempt
def rename_segment(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        index = data['index']
        new_name = data['new_name']

        dict_track = json.loads(request.session['json_track'])
        dict_track['segment_names'][index] = new_name
        request.session['json_track'] = json.dumps(dict_track)

        return JsonResponse({'message': 'Segment is successfully renamed'},
                            status=201)

        # TODO manage exceptions ->
        # TODO at the same time implement manage error in js fetch

    else:
        return JsonResponse({'error': 'POST request required'}, status=400)


@login_required
@csrf_exempt
def remove_segment(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        index = data['index']

        # # TODO how faster is working with the dictionary?
        # # TODO update extremes and distance
        # dict_track = json.loads(request.session['json_track'])
        # segment_init_idx = dict_track['segment'].index(index)
        # segment_end_idx = len(dict_track['segment']) - \
        #                   dict_track['segment'][::-1].index(index)
        #
        # df_keys = ['lat', 'lon', 'ele', 'segment',
        #            'ele_pos_cum', 'ele_neg_cum', 'distance']
        # for k in df_keys:
        #     del dict_track[k][segment_init_idx:segment_end_idx]
        #
        # request.session['json_track'] = json.dumps(dict_track)

        obj_track = track.Track(track_json=request.session['json_track'])
        obj_track.remove_segment(index)
        request.session['json_track'] = obj_track.to_json()

        print('--- REMOVE SEGMENT ---')
        print(obj_track.df_track)
        return JsonResponse({'message': 'Segment is successfully renamed'},
                            status=201)

        # TODO manage exceptions ->
        # TODO at the same time implement manage error in js fetch

    else:
        return JsonResponse({'error': 'POST request required'}, status=400)


@login_required
def get_segment(request, index):
    if request.method == 'GET':
        if request.session['json_track']:
            json_track = json.loads(request.session['json_track'])

            if index not in json_track['segment']:
                return JsonResponse(
                    {'error': 'Invalid index request', 'size': 0},
                    status=400)

            if index == 0:
                index = json_track['last_segment_idx']

            segment_init_idx = json_track['segment'].index(index)
            segment_end_idx = \
                len(json_track['segment']) - \
                json_track['segment'][::-1].index(index)

            lat = json_track['lat'][segment_init_idx:segment_end_idx]
            lon = json_track['lon'][segment_init_idx:segment_end_idx]
            ele = json_track['ele'][segment_init_idx:segment_end_idx]
            extremes = json_track['extremes']

            return JsonResponse({'size': len(lat),
                                 'lat': lat,
                                 'lon': lon,
                                 'ele': ele,
                                 'map_center': [sum(extremes[2:]) / 2,
                                                sum(extremes[:2]) / 2],
                                 'map_zoom': int(auto_zoom(*extremes)),
                                 'index': index
                                 }, status=200)
        else:
            return JsonResponse({'error': 'No track is loaded'}, status=400)
    else:
        return JsonResponse({'error': 'GET request required'}, status=400)


@login_required
def get_summary(request):
    if request.method == 'GET':
        if 'json_track' in request.session:
            obj_track = track.Track(track_json=request.session['json_track'])
            obj_track.update_summary()
            summary = obj_track.get_summary()

            return JsonResponse({'summary': summary}, status=200)
        else:
            return JsonResponse({'error': 'No track is loaded'}, status=500)

    return JsonResponse({'error': 'POST request required'}, status=400)


@login_required
@csrf_exempt
def save_session(request):
    if request.method == 'POST':
        if 'json_track' in request.session:
            data = json.loads(request.body)
            save = data['save'] == 'True'

            if save:
                obj_track = track.Track(track_json=request.session['json_track'])
                json_track = obj_track.to_json()

                if request.session['index_db']:
                    index = request.session['index_db']
                    new_track = Track.objects.get(id=index)
                    new_track.track = json_track
                    new_track.title = obj_track.title
                    new_track.last_edit = datetime.now()
                    new_track.save()
                else:
                    new_track = Track(user=request.user,
                                      track=json_track,
                                      title=obj_track.title)
                    new_track.save()
                    request.session['index_db'] = new_track.id

                print('save_session:', request.session['index_db'])

                return JsonResponse({'message': 'Session has been saved'},
                                    status=201)
            else:
                return JsonResponse({'error': 'save is not True'},
                                    status=492)
        else:
            return JsonResponse({'error': 'No track is available'}, status=491)

    return JsonResponse({'error': 'POST request required'}, status=400)


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


@login_required
@csrf_exempt
def remove_session(request, index):
    if request.method == 'POST':
        try:
            Track.objects.get(id=index, user=request.user).delete()

            return JsonResponse({'message': 'Track is successfully removed'},
                                status=201)
        except Exception:
            return JsonResponse({'message': 'Unable to remove track'},
                                status=500)
    else:
        return JsonResponse({'error': 'POST request required'}, status=400)


@login_required
@csrf_exempt
def rename_session(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_name = data['new_name']

            dict_track = json.loads(request.session['json_track'])
            dict_track['title'] = new_name.replace('\n', '').strip()
            request.session['json_track'] = json.dumps(dict_track)

            print('--- RENAME SESSION ---')
            print(dict_track)

            return JsonResponse({'message': 'Session is successfully renamed'},
                                status=201)
        except Exception:
            return JsonResponse({'error': 'Unable to rename session'},
                                status=500)
    else:
        return JsonResponse({'error': 'POST request required'}, status=400)


@login_required
@csrf_exempt
def download_session(request):
    if request.method == 'POST':

        if request.session['json_track']:
            try:
                obj_track = track.Track(track_json=request.session['json_track'])

                if obj_track.size > 0:
                    fs = FileSystemStorage()

                    output_filename = \
                        obj_track.title + '_' + id_generator(size=8) + '.gpx'
                    output_location = os.path.join(fs.location, output_filename)
                    output_url = fs.url(output_filename)
                    obj_track.save_gpx(output_location, exclude_time=True)

                    return JsonResponse({'url': output_url,
                                         'filename': output_filename},
                                        status=200)
                else:
                    return JsonResponse({'error': 'No track is loaded'},
                                        status=500)
            except Exception:
                return JsonResponse(
                    {'error': 'Unable to generate session file'},
                    status=500)
        else:
            return JsonResponse({'error': 'No track is loaded'}, status=500)
    else:
        return JsonResponse({'error': 'POST request required'}, status=400)


def exist_track(request):
    if 'json_track' in request.session:
        if request.session['json_track']:
            return True
    return False


@login_required
def get_segments_links(request):
    if request.method == 'GET':
        if exist_track(request):
            obj_track = track.Track(track_json=request.session['json_track'])

            df_track = obj_track.df_track
            segments = obj_track.df_track['segment'].unique()
            links = []

            for i in range(len(segments) - 1):
                s = segments[i]
                s_next = segments[i+1]
                init = df_track[df_track['segment'] == s].iloc[-1][['lat', 'lon']]
                end = df_track[df_track['segment'] == s_next].iloc[0][['lat', 'lon']]
                links.append([init.to_list(), end.to_list()])

            return JsonResponse({'links': str(links)}, status=200)

        else:
            return JsonResponse({'error': 'No available track'}, status=500)
    else:
        return JsonResponse({'error': 'GET request required'}, status=400)
