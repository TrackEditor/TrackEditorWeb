from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    return render(request, "TrackApp/index.html")


def register(request):
    return HttpResponse('Register')


def log_in(request):
    return HttpResponse('Log In')


def log_out(request):
    return HttpResponse('Log Out')


def combine_tracks(request):
    return HttpResponse('Combine Tracks')


def insert_timestamp(request):
    return HttpResponse('Insert Timestamp')
