import os
import json
import traceback
import logging

from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.conf import settings
from django.core.files.base import ContentFile
from django.http import HttpResponseNotFound

import libs.track as track
from libs.constants import Constants as c
from TrackApp.models import Track, Upload
from libs.utils import id_generator, auto_zoom, map_center, randomize_filename
from editor.error_codes import EditorError


logger = logging.getLogger('django')


def error_handler(error_code: EditorError, expected_track: bool = True):
    """
    Function to be used as a decorator to manage any unexpected exception and 
    return it as Json
    :param error_code: numeric number to provide in case of exception
    :param expected_track: true if a track is expected to be already defined
    :return: function called through wrapper
    """
    def exist_track(request):
        if request.session.get('json_track') is not None:
            return True
        return False

    def decorator_function(func):
        def wrapper(request, *args, **kwargs):
            if not exist_track(request) and expected_track:
                return JsonResponse({'error': 'No available track'},
                                    status=520)
            try:
                return func(request, *args, **kwargs)
            except Exception as e:
                msg = f'Error in function: {func.__name__}\n' + \
                      f'Call: {func.__name__}({args}, {kwargs})\n' + \
                      traceback.format_exc()
                logger.error(msg)
                return JsonResponse(
                    {'error': f'Unexpected error ({error_code.value}): {e}'},
                    status=error_code.value)
        return wrapper
    return decorator_function


@login_required
@error_handler(EditorError.EDITOR, expected_track=False)
@require_http_methods(['GET', 'POST'])
def editor(request, index: int = None):
    template_editor = 'editor/editor.html'
    config = {'maximum_file_size': c.maximum_file_size,
              'maximum_files': c.maximum_files,
              'valid_extensions': c.valid_extensions,
              'error': False}

    if request.method == 'GET' and index is not None:
        if index >= 0:
            return load_editor(request, index, template_editor, config)

    elif request.method == 'POST':  # add files to session
        return load_segment(request, template_editor, config)

    # Create new session
    request.session['json_track'] = track.Track().to_json()
    request.session['index_db'] = None
    return render(request, template_editor, {**config})


def load_editor(request, index: int, template_editor: str, config: dict):
    if index == 0:  # reload
        obj_track = track.Track.from_json(request.session['json_track'])

        try:
            return render(request,
                          template_editor,
                          {'track_list': [n for n in obj_track.segment_names if n],
                           'segment_list':
                               list(obj_track.df_track['segment'].unique()),
                           'title': obj_track.title,
                           **config})
        except Exception as e:
            logging.error('Unexpected error loading editor')
            config['error'] = True
            return render(request,
                          template_editor,
                          {'track_list': [n for n in obj_track.segment_names if n],
                           'segment_list': list(
                               obj_track.df_track['segment'].unique()),
                           'title': obj_track.title,
                           'error_msg': f'Unexpected error loading editor (521): {e}',
                           **config})

    elif index > 0:  # load existing session
        try:
            request.session['json_track'] = Track.objects.get(id=index, user=request.user).track
        except Track.DoesNotExist:
            return HttpResponseNotFound(f'Not found track {index} for {request.user.username}')

        request.session['index_db'] = index
        json_track = json.loads(request.session['json_track'])

        return render(
            request,
            template_editor,
            {'track_list': [n for n in json_track['segment_names'] if n],
             'segment_list': list(set(json_track['segment'])),
             'title': json_track['title'],
             **config})


def load_segment(request, template_editor: str, config: dict):
    obj_track = track.Track.from_json(request.session['json_track'])

    try:
        uploaded_file = request.FILES['document']

        if settings.USE_S3:
            upload = Upload(file=uploaded_file)
            filename = randomize_filename(upload.file.url.split('/')[-1])
            upload.file.name = filename
            upload.save()

            with upload.file.open() as f:
                gpx_file = f.read()
                obj_track.add_gpx_bytes(file=gpx_file, filename=filename)

        else:
            fs = FileSystemStorage()
            filename = fs.save(uploaded_file.name, uploaded_file)
            filepath = os.path.join(fs.location, filename)
            obj_track.add_gpx(filepath)

        request.session['json_track'] = obj_track.to_json()

        return render(request,
                      template_editor,
                      {'track_list': [n for n in obj_track.segment_names if n],
                       'segment_list':
                           list(obj_track.df_track['segment'].unique()),
                       'title': obj_track.title,
                       **config})
    except Exception as e:
        logging.error('Unexpected error loading files to editor')
        config['error'] = True
        return render(request,
                      template_editor,
                      {'track_list': [n for n in obj_track.segment_names if n],
                       'segment_list':
                           list(obj_track.df_track['segment'].unique()),
                       'title': obj_track.title,
                       'error_msg': f'Unexpected error loading files to editor (521): {e}',
                       **config})


@login_required
@require_POST
@error_handler(EditorError.RENAME_SEGMENT)
def rename_segment(request, index, new_name):
    dict_track = json.loads(request.session['json_track'])
    dict_track['segment_names'][index - 1] = new_name
    request.session['json_track'] = json.dumps(dict_track)

    return JsonResponse({'message': 'Segment is successfully renamed'},
                        status=201)


@login_required
@require_POST
@error_handler(EditorError.REMOVE_SEGMENT)
def remove_segment(request, index):
    obj_track = track.Track.from_json(request.session['json_track'])
    obj_track.remove_segment(index)
    request.session['json_track'] = obj_track.to_json()

    return JsonResponse({'message': 'Segment is successfully removed'},
                        status=201)


@login_required
@require_GET
@error_handler(EditorError.GET_SEGMENT)
def get_segment(request, index):
    json_track = json.loads(request.session['json_track'])

    segment_init_idx = json_track['segment'].index(index)
    segment_end_idx = \
        len(json_track['segment']) - \
        json_track['segment'][::-1].index(index)

    lat = json_track['lat'][segment_init_idx:segment_end_idx]
    lon = json_track['lon'][segment_init_idx:segment_end_idx]
    ele = json_track['ele'][segment_init_idx:segment_end_idx]
    distance = json_track['distance'][segment_init_idx:segment_end_idx]
    extremes = json_track['extremes']

    return JsonResponse({'size': len(lat),
                         'lat': lat,
                         'lon': lon,
                         'ele': ele,
                         'distance': distance,
                         'map_center': [sum(extremes[2:]) / 2,
                                        sum(extremes[:2]) / 2],
                         'map_zoom': int(auto_zoom(*extremes)),
                         'index': index
                         }, status=200)


@login_required
@require_GET
@error_handler(EditorError.GET_TRACK)
def get_track(request):
    obj_track = track.Track.from_json(request.session['json_track'])
    df_track = obj_track.df_track
    segments_indexing = obj_track.df_track['segment'].unique()

    track_json = {'title': obj_track.title,
                  'size': len(segments_indexing),
                  'segments': [],
                  'links_coor': [],
                  'links_ele': [],
                  'map_center': map_center(*obj_track.extremes),
                  'map_zoom': int(auto_zoom(*obj_track.extremes))}

    for i, segment_idx in enumerate(segments_indexing):
        obj_segment = df_track[df_track['segment'] == segment_idx]
        track_json['segments'].append(
            {'lat': obj_segment['lat'].to_list(),
             'lon': obj_segment['lon'].to_list(),
             'ele': obj_segment['ele'].to_list(),
             'distance': obj_segment['distance'].to_list(),
             'segment_distance': obj_segment['segment_distance'].to_list(),
             'index': int(segment_idx),  # ensure serializable value
             'name': obj_track.segment_names[segment_idx - 1],
             'size': obj_segment.shape[0]})

        if i < track_json['size'] - 1 and track_json['size'] > 1:
            obj_next_segment = df_track[df_track['segment'] ==
                                        segments_indexing[i + 1]]
            track_json['links_coor'].append(
                {'from': int(segment_idx),
                 'to': int(segments_indexing[i + 1]),
                 'from_coor': {'lon': float(obj_segment['lon'].iloc[-1]),
                               'lat': float(obj_segment['lat'].iloc[-1])},
                 'to_coor': {'lon': float(obj_next_segment['lon'].iloc[0]),
                             'lat': float(obj_next_segment['lat'].iloc[0])}})
            track_json['links_ele'].append(
                {'from': int(segment_idx),
                 'to': int(segments_indexing[i + 1]),
                 'from_ele': {'x': float(obj_segment['distance'].iloc[-1]),
                              'y': float(obj_segment['ele'].iloc[-1])},
                 'to_ele': {'x': float(obj_next_segment['distance'].iloc[0]),
                            'y': float(obj_next_segment['ele'].iloc[0])}})

    return JsonResponse(track_json, status=200)


@login_required
@require_GET
@error_handler(EditorError.GET_SUMMARY)
def get_summary(request):
    obj_track = track.Track.from_json(request.session['json_track'])
    obj_track.update_summary()
    summary = obj_track.get_summary()

    return JsonResponse({'summary': summary}, status=200)


@login_required
@require_POST
@error_handler(EditorError.SAVE_SESSION)
def save_session(request):
    obj_track = track.Track.from_json(request.session['json_track'])
    json_track = obj_track.to_json()

    if request.session['index_db']:
        index = request.session['index_db']
        new_track = Track.objects.get(id=index, user=request.user)
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

    logger.info(f'Saving session {request.session["index_db"]}')
    return JsonResponse({'message': 'Session has been saved'},
                        status=201)


@login_required
@require_POST
@error_handler(EditorError.REMOVE_SESSION)
def remove_session(request, index):
    Track.objects.get(id=index, user=request.user).delete()
    return JsonResponse({'message': 'Track is successfully removed'},
                        status=201)


@login_required
@require_POST
@error_handler(EditorError.RENAME_SESSION)
def rename_session(request, new_name):
    dict_track = json.loads(request.session['json_track'])
    dict_track['title'] = new_name.replace('\n', '').strip()
    request.session['json_track'] = json.dumps(dict_track)

    return JsonResponse({'message': 'Session is successfully renamed'},
                        status=201)


@login_required
@require_POST
@error_handler(EditorError.DOWNLOAD_SESSION)
def download_session(request):
    obj_track = track.Track.from_json(request.session['json_track'])
    fs = FileSystemStorage()

    output_filename = \
        obj_track.title + '_' + id_generator(size=8) + '.gpx'

    if settings.USE_S3:
        gpx_str = obj_track.get_gpx(exclude_time=True).encode('utf-8')
        upload = Upload(file=ContentFile(gpx_str))
        upload.file.name = output_filename
        output_url = upload.file.url
        upload.save()
    else:
        output_location = os.path.join(fs.location, output_filename)
        output_url = fs.url(output_filename)
        obj_track.save_gpx(output_location, exclude_time=True)

    logger.info(f'Downloading file {output_url}')
    return JsonResponse({'url': output_url,
                         'filename': output_filename},
                        status=200)


@login_required
@require_GET
@error_handler(EditorError.GET_SEGMENTS_LINKS)
def get_segments_links(request):
    obj_track = track.Track.from_json(request.session['json_track'])
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
@require_POST
@error_handler(EditorError.REVERSE_SEGMENT)
def reverse_segment(request, index):
    obj_track = track.Track.from_json(request.session['json_track'])
    obj_track.reverse_segment(index)
    request.session['json_track'] = obj_track.to_json()
    return JsonResponse({'message': 'Segment is reversed'}, status=200)


@login_required
@require_POST
@error_handler(EditorError.CHANGE_SEGMENTS_ORDER)
def change_segments_order(request):
    data = json.loads(request.body)
    new_order = data['new_order']
    order_dict = {n: i + 1 for i, n in enumerate(new_order)}

    obj_track = track.Track.from_json(request.session['json_track'])
    obj_track.change_order(order_dict)
    request.session['json_track'] = obj_track.to_json()

    return JsonResponse({'message': 'Successful reordering'}, status=200)


@login_required
@require_POST
@error_handler(EditorError.DIVIDE_SEGMENT)
def divide_segment(request, index: int, div_index: int):
    obj_track = track.Track.from_json(request.session['json_track'])
    obj_track.divide_segment(index, div_index)
    request.session['json_track'] = obj_track.to_json()

    return JsonResponse({'message': 'Successful split'}, status=201)


@login_required
@require_http_methods(['GET', 'POST'])
@error_handler(588)
def hello(request, var):
    if request.method == 'POST':
        data = json.loads(request.body)
        return JsonResponse({'message': 'hello-post', 'var': var, **data}, status=201)
    elif request.method == 'GET':
        return JsonResponse({'message': 'hello-get'}, status=200)
