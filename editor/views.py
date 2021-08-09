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


def exist_track(request):
    """
    Checks whether a track is already created in the user session
    :param request: from the view call it stores the session
    :return: True if the track exists
    """
    if 'json_track' in request.session:
        if request.session['json_track']:
            return True
    return False


def check_view(method, error_code):
    """
    Function to be used as a decorator to check the expected request method
    and any possible exception
    :param method: request method which is expected to be used (GET, POST, ...)
    :param error_code: numeric number to provide in case of excepction
    :return: function called through wrapper
    """
    def decorator_function(func):
        def wrapper(request, *args, **kwargs):
            if request.method != method:
                return JsonResponse({'error': f'{method} request required'},
                                    status=400)
            if not exist_track(request):
                return JsonResponse({'error': 'No available track'},
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
def editor(request, index=None):
    config = {'maximum_file_size': c.maximum_file_size,
              'maximum_files': c.maximum_files,
              'valid_extensions': c.valid_extensions}

    if index is not None:
        if index == 0:  # reload
            try:
                obj_track = track.Track(track_json=request.session['json_track'])

                return render(request,
                              'editor/editor.html',
                              {'track_list': [n for n in obj_track.segment_names if n],
                               'segment_list':
                                   list(obj_track.df_track['segment'].unique()),
                               'title': obj_track.title,
                               **config})
            except Exception as e:
                return JsonResponse(
                    {'error': f'Unexpected error (521): {e}'},
                    status=521)

        elif index > 0:  # load existing session
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
        try:
            fs = FileSystemStorage()
            uploaded_file = request.FILES['document']
            filename = fs.save(uploaded_file.name, uploaded_file)
            filepath = os.path.join(fs.location, filename)

            obj_track = track.Track(track_json=request.session['json_track'])
            obj_track.add_gpx(filepath)

            request.session['json_track'] = obj_track.to_json()

            return render(request,
                          'editor/editor.html',
                          {'track_list': [n for n in obj_track.segment_names if n],
                           'segment_list':
                               list(obj_track.df_track['segment'].unique()),
                           'title': obj_track.title,
                           **config})
        except Exception as e:
            return JsonResponse(
                {'error': f'Unexpected error (521): {e}'},
                status=521)

    # Create new session
    request.session['json_track'] = track.Track().to_json()
    request.session['index_db'] = None
    return render(request, 'editor/editor.html', {**config})


@login_required
@csrf_exempt
@check_view('POST', 522)
def rename_segment(request, index, new_name):
    dict_track = json.loads(request.session['json_track'])
    dict_track['segment_names'][index] = new_name
    request.session['json_track'] = json.dumps(dict_track)

    return JsonResponse({'message': 'Segment is successfully renamed'},
                        status=201)


@login_required
@csrf_exempt
@check_view('POST', 523)
def remove_segment(request, index):
    obj_track = track.Track(track_json=request.session['json_track'])
    obj_track.remove_segment(index)
    request.session['json_track'] = obj_track.to_json()

    return JsonResponse({'message': 'Segment is successfully removed'},
                        status=201)


@login_required
@check_view('GET', 524)
def get_segment(request, index):
    json_track = json.loads(request.session['json_track'])

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


@login_required
@check_view('GET', 525)
def get_summary(request):
    obj_track = track.Track(track_json=request.session['json_track'])
    obj_track.update_summary()
    summary = obj_track.get_summary()

    return JsonResponse({'summary': summary}, status=200)


@login_required
@csrf_exempt
@check_view('POST', 526)
def save_session(request):
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


@login_required
@csrf_exempt
@check_view('POST', 527)
def remove_session(request, index):
    Track.objects.get(id=index, user=request.user).delete()
    return JsonResponse({'message': 'Track is successfully removed'},
                        status=201)


@login_required
@csrf_exempt
@check_view('POST', 528)
def rename_session(request, new_name):
    dict_track = json.loads(request.session['json_track'])
    dict_track['title'] = new_name.replace('\n', '').strip()
    request.session['json_track'] = json.dumps(dict_track)

    return JsonResponse({'message': 'Session is successfully renamed'},
                        status=201)


@login_required
@csrf_exempt
@check_view('POST', 529)
def download_session(request):
    obj_track = track.Track(track_json=request.session['json_track'])
    fs = FileSystemStorage()

    output_filename = \
        obj_track.title + '_' + id_generator(size=8) + '.gpx'
    output_location = os.path.join(fs.location, output_filename)
    output_url = fs.url(output_filename)
    obj_track.save_gpx(output_location, exclude_time=True)

    return JsonResponse({'url': output_url,
                         'filename': output_filename},
                        status=200)


@login_required
@check_view('GET', 530)
def get_segments_links(request):
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


@login_required
@csrf_exempt
@check_view('POST', 531)
def reverse_segment(request, index):
    obj_track = track.Track(track_json=request.session['json_track'])
    obj_track.reverse_segment(index)
    request.session['json_track'] = obj_track.to_json()
    return JsonResponse({'message': 'Segment is reversed'}, status=200)


@login_required
@csrf_exempt
@check_view('POST', 532)
def change_segments_order(request):
    data = json.loads(request.body)
    new_order = data['new_order']
    order_dict = {n: i + 1 for i, n in enumerate(new_order)}

    obj_track = track.Track(track_json=request.session['json_track'])
    obj_track.change_order(order_dict)
    request.session['json_track'] = obj_track.to_json()

    return JsonResponse({'message': 'Segment is reversed'}, status=200)
