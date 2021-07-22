from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('register', views.register_view, name='register'),
    path('login', views.login_view, name='login'),
    path('log_out', views.logout_view, name='log_out'),
    path('combine_tracks', views.combine_tracks, name='combine_tracks'),
    path('insert_timestamp', views.insert_timestamp, name='insert_timestamp'),
    path('editor', views.editor, name='editor'),
    path('users_only', views.users_only, name='users_only'),
]

# DEBUG will only be available during development in other case a more powerful
# server, like nginx, would be use
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
