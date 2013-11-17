from django.conf.urls import patterns, url

from game import views

urlpatterns = patterns(#'',
    url(r'^start/$', views.start_game, name='start_game'),
    url(r'^instructions/$', views.view_instructions, name='view_instructions'),
    url(r'^intentionality/$', views.intentionality, name='intentionality'),
    url(r'^round/start/$', views.start_round, name='start_round'),
    url(r'^round/play/$', views.play_round, name='play_round'),
    url(r'^round/end/$', views.end_round, name='end_round'),
    url(r'^questionnaire/$', views.questionnaire, name='questionnaire'),
    url('', views.start_game, name='start_game')    
)
