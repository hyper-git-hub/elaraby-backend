"""Hypernet URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url

from ppp.wrappers import \
    last_match_stats, \
    last_n_matches, \
    get_top_position_players, \
    get_top_n_players, \
    get_team_stats, \
    get_training_info, \
    get_injury_info, \
    get_team_reported_injuries, \
    get_team_current_injuries,\
    get_team_past_injuries

from ppp.wrappers_waleed import \
    get_player_performance_stats, \
    get_player_competition_stats,\
    get_player_info, \
    get_player_fitness_data, \
    get_player_trainings, \
    get_player_injuries_data

from .views import PlayerProfile, TeamTrainings


urlpatterns = [
    #Dashboard APIs
    url(r'^get_last_match/', last_match_stats),
    url(r'^get_n_matches/', last_n_matches),
    url(r'^get_top_position_players/', get_top_position_players),
    url(r'^get_top_n_players/', get_top_n_players),
    url(r'^get_team_stats/', get_team_stats),
    url(r'^get_training_info/', get_training_info),
    url(r'^get_injury_info/', get_injury_info),

    # Player Profile API
    url(r'^player_profile/', PlayerProfile.as_view()),
    url(r'^team_trainings/', TeamTrainings.as_view()),



    #Team Injuries APIs
    url(r'^get_team_reported_injuries/', get_team_reported_injuries),
    url(r'^get_team_current_injuries/', get_team_current_injuries),
    url(r'^get_team_past_injuries/', get_team_past_injuries),
]
