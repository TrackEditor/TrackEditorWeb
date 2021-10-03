from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.editor, name='editor'),
    path('<int:index>', views.editor, name='editor'),
    path('rename_segment/<int:index>/<str:new_name>', views.rename_segment,
         name='rename_segment'),
    path('remove_segment/<int:index>', views.remove_segment, name='remove_segment'),
    path('get_segment/<int:index>', views.get_segment, name='get_segment'),
    path('get_track', views.get_track, name='get_track'),
    path('get_summary', views.get_summary, name='get_summary'),
    path('save_session', views.save_session, name='save_session'),
    path('remove_session/<int:index>', views.remove_session, name='remove_session'),
    path('rename_session/<str:new_name>', views.rename_session, name='rename_session'),
    path('download_session', views.download_session, name='download_session'),
    path('get_segments_links', views.get_segments_links, name='get_segments_links'),
    path('reverse_segment/<int:index>', views.reverse_segment, name='reverse_segment'),
    path('change_segments_order', views.change_segments_order, name='change_segments_order')
]

# DEBUG will only be available during development in other case a more powerful
# server, like nginx, would be use
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
