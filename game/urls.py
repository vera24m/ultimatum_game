from django.conf.urls import patterns, url

from game import views

urlpatterns = patterns('',
    url(r'^start/$', views.start_game, name='start_game'),
    url(r'^instructions/$', views.view_instructions, name='view_instructions'),
)
