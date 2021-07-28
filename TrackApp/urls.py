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
    path('users_only', views.users_only, name='users_only'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('get_tracks_from_db/<int:page>', views.get_tracks_from_db, name='get_tracks_from_db'),
    path('editor', views.editor, name='editor'),
    path('editor/rename_segment', views.rename_segment, name='rename_segment'),
    path('editor/remove_segment', views.remove_segment, name='remove_segment'),
    path('editor/get_segment/<int:index>', views.get_segment, name='get_segment'),
    path('editor/get_summary', views.get_summary, name='get_summary'),
    path('editor/save_session', views.save_session, name='save_session'),
    path('editor/remove_session/<int:index>', views.remove_session, name='remove_session'),
    path('editor/rename_session', views.rename_session, name='rename_session'),
    path('editor/session/<int:index>', views.load_session, name='load_session')
]

# DEBUG will only be available during development in other case a more powerful
# server, like nginx, would be use
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
