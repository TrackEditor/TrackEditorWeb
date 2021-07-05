from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    return render(request, "TrackApp/index.html")
    # return HttpResponse('Hello, World!')
