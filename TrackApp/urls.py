from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register', views.register, name='register'),
    path('login', views.login, name='login'),
    path('log_out', views.log_out, name='log_out'),
    path('combine_tracks', views.combine_tracks, name='combine_tracks'),
    path('insert_timestamp', views.insert_timestamp, name='insert_timestamp')
]
