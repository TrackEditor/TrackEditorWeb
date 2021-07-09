import os
from datetime import datetime
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage

from . import track
from . import constants as c
from .models import User
from .utils import id_generator


def index_view(request):
    return render(request, "TrackApp/index.html")


def register_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "TrackApp/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "TrackApp/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "TrackApp/register.html")


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "TrackApp/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "TrackApp/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


@csrf_exempt
def combine_tracks(request):
    if request.method == 'POST':
        obj_track = track.Track()
        fs = FileSystemStorage()

        for uploaded_file in request.FILES.getlist('document'):
            filename = fs.save(uploaded_file.name, uploaded_file)
            filepath = os.path.join(fs.location, filename)
            obj_track.add_gpx(filepath)

        output_filename = c.tool + '_' + \
                          datetime.now().strftime("%d%m%Y_%H%M%S") + '_' + \
                          id_generator(size=8) + '.gpx'
        output_location = os.path.join(fs.location, output_filename)
        output_url = fs.url(output_filename)
        obj_track.save_gpx(output_location)

        print(output_url)
        return render(request, 'TrackApp/combine_tracks.html',
                      {'download': True,
                       'file': output_url})

    return render(request, 'TrackApp/combine_tracks.html', {'download': False})


def insert_timestamp(request):
    return HttpResponse('Insert Timestamp')
