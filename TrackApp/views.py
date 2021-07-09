from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
import json

from .models import User


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


def combine_tracks(request):
    return render(request, "TrackApp/combine_tracks.html")


@csrf_exempt
def combine_tracks_api(request):
    """
    TODO
    mirar esto yo creo que se necesita un get
    hay que buscar la forma de enviar un archivo y recibir un archivo
    o enviar un archivo y poner un boton disponible para descargar el resultado
    Igual hay que usar un PUT https://developer.mozilla.org/es/docs/Web/API/Fetch_API/Using_Fetch#enviando_un_archivo
    """
    if request.method != "POST":
        print('->this is not post')
        return JsonResponse({"error": "POST request required."}, status=400)
    else:
        print('->this is post')

    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)
    print(body['file_list'])

    return JsonResponse({"message": "Files have been received."}, status=201)


def insert_timestamp(request):
    return HttpResponse('Insert Timestamp')
