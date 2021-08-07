import os
import json
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required

from libs import track, constants as c
from TrackApp.models import Track
from libs.utils import id_generator, auto_zoom


@login_required
def editor(request, index=None):
    config = {'maximum_file_size': c.maximum_file_size,
              'maximum_files': c.maximum_files,
              'valid_extensions': c.valid_extensions}

    if index:  # load existing session
        request.session['json_track'] = Track.objects.get(id=index).track
        request.session['index_db'] = index
        json_track = json.loads(request.session['json_track'])

        return render(
            request,
            'editor/editor.html',
            {'track_list': [n for n in json_track['segment_names'] if n],
             'segment_list': list(set(json_track['segment'])),
             'title': json_track['title'],
             **config})

    if request.method == 'POST':  # add files to session
        fs = FileSystemStorage()
        uploaded_file = request.FILES['document']
        filename = fs.save(uploaded_file.name, uploaded_file)
        filepath = os.path.join(fs.location, filename)

        obj_track = track.Track(track_json=request.session['json_track'])
        obj_track.add_gpx(filepath)

        request.session['json_track'] = obj_track.to_json()

        return render(request, 'editor/editor.html',
                      {'track_list': [n for n in obj_track.segment_names if n],
                       'segment_list': list(obj_track.df_track['segment'].unique()),
                       'title': obj_track.title,
                       **config})

        # TODO control exceptions

    # Create new session
    request.session['json_track'] = track.Track().to_json()
    request.session['index_db'] = None
    return render(request, 'editor/editor.html', {**config})


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

                return JsonResponse({'message': 'Session has been saved'},
                                    status=201)
            else:
                return JsonResponse({'error': 'save is not True'},
                                    status=492)
        else:
            return JsonResponse({'error': 'No track is available'}, status=491)

    return JsonResponse({'error': 'POST request required'}, status=400)


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
                s_next = segments[i + 1]
                init = df_track[df_track['segment'] == s].iloc[-1][['lat', 'lon']]
                end = df_track[df_track['segment'] == s_next].iloc[0][['lat', 'lon']]
                links.append([init.to_list(), end.to_list()])

            return JsonResponse({'links': str(links)}, status=200)

        else:
            return JsonResponse({'error': 'No available track'}, status=500)
    else:
        return JsonResponse({'error': 'GET request required'}, status=400)


def check_view(method, error_code):
    print(f'{method=}')
    print(f'{error_code=}')

    def decorator_function(func):
        print(f'{func.__name__=}')

        def wrapper(request, *args, **kwargs):
            if request.method != method:
                return JsonResponse({'error': f'{method} request required'},
                                    status=400)
            if not exist_track(request):
                return JsonResponse({'error': f'No available track'},
                                    status=520)
            try:
                return func(request, *args, **kwargs)
            except Exception as e:
                return JsonResponse(
                    {'error': f'Unexpected error ({error_code}): {e}'},
                    status=error_code)

        return wrapper
    return decorator_function


@login_required
@csrf_exempt
@check_view('POST', 521)
def reverse_segment(request, index):
    obj_track = track.Track(track_json=request.session['json_track'])
    obj_track.reverse_segment(index)
    request.session['json_track'] = obj_track.to_json()
    return JsonResponse({'message': 'Segment is reversed'}, status=200)
