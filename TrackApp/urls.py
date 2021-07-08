from django.urls import path

from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('register', views.register_view, name='register'),
    path('login', views.login_view, name='login'),
    path('log_out', views.logout_view, name='log_out'),
    path('combine_tracks', views.combine_tracks, name='combine_tracks'),
    path('insert_timestamp', views.insert_timestamp, name='insert_timestamp')
]
