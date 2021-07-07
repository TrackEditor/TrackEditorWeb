from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse


def index(request):
    return render(request, "TrackApp/index.html")


def register(request):
    return HttpResponse('Register')


def login(request):
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

    return HttpResponse('Log In')


def log_out(request):
    return HttpResponse('Log Out')


def combine_tracks(request):
    return HttpResponse('Combine Tracks')


def insert_timestamp(request):
    return HttpResponse('Insert Timestamp')
