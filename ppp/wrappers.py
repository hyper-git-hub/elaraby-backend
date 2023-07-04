from __future__ import unicode_literals

from django.db import models
from .models import *
from user.enums import RoleTypeEnum
from backend import settings
from django.db.models import Avg, Sum, Min, Max
from .models import *
from hypernet import constants, enums
from hypernet.models import Entity
from hypernet.enums import *
from hypernet.utils import *
from rest_framework.response import Response
from .utils_functions import *
from .utils_waleed import *
from rest_framework.decorators import api_view, APIView
from .serializers import *
from hypernet.constants import ERROR_RESPONSE_BODY, RESPONSE_DATA, STATUS_OK, RESPONSE_STATUS, RESPONSE_MESSAGE
###Wrappers for dashboard###


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def last_match_stats(request):
    c_id = get_default_param(request,'c_id',None)
    m_id = get_default_param(request,'m_id',None)
    last_match = {}
    if c_id:
        last_match['home_team_name'], last_match['away_team_name']= get_match_team_names(m_id)
        last_match['home_team_goals'],last_match['away_team_goals'] = get_match_goals(m_id)
        last_match['match_venue'] = get_match_venue(m_id)
        last_match['match_date'] = get_match_date(m_id)
        last_match['competition'] = get_match_competition(m_id)
        #serializer = MatchDetailSerializer(last_match,many=True)
        #data = serializer.data
    else:
        return Response(generic_response(response_json(False, None, constants.TEXT_PARAMS_MISSING),
                                http_status=500))

    last_match = Response(response_json(True, last_match))
    return last_match


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def last_n_matches(request):

    n = get_default_param(request, 'limit', None)
    n = int(n)
    if n:
       # last_n_matches = get_all_match_details().values('venue__name','match__date_of_match','competition__name','home_team_name','away_team_name','home_team_goals','away_team_goals')[:n]
        last_n_matches = get_all_match_details(n)
    else:
       return generic_response(response_json(False, None, constants.TEXT_PARAMS_MISSING),http_status=500)
    last_n_matches = response_json(True, last_n_matches)
    return generic_response(last_n_matches)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_top_position_players(request):
    c_id = get_default_param(request,'c_id', None)
    position = get_default_param(request, 'position', None)

    if c_id and position:
        player = get_players_position(position,c_id).values('player__name','player_rating','player__position')[:3]
    else:
        return generic_response(response_json(False, None, constants.TEXT_PARAMS_MISSING),http_status=500)
    player = response_json(True, list(player))
    return player

@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_top_n_players(request):
    c_id = get_default_param(request, 'c_id', None)
    n = get_default_param(request, 'num', None)
    n = int(n)
    if c_id and n:
        player = get_all_players_stats(c_id).order_by('-player_rating').values('player__name', 'player_rating',
                                                                         'player__player_position')[:n]
    else:
        return generic_response(response_json(False, None, constants.TEXT_PARAMS_MISSING),
                                http_status=500)
    player = response_json(True, list(player))
    return generic_response(player)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_team_stats(request):
    comp_id = get_default_param(request,'comp_id', None)
    team_stats = {}
    if comp_id:
        team_stats['total_wins'] = get_team_wins(comp_id)
        team_stats['total_losses'] = get_team_wins(comp_id)
        team_stats['total_draws'] = get_team_wins(comp_id)
        team_stats['total_goals_for'] = get_team_wins(comp_id)
        team_stats['total_goals_against'] = get_team_wins(comp_id)
        team_stats['competition_name'] = get_team_competition(comp_id)
    else:
        return generic_response(response_json(False, None, constants.TEXT_PARAMS_MISSING),http_status=500)
    team_stats = response_json(True, team_stats)
    return generic_response(team_stats)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_training_info(request):
    c_id = get_default_param(request,'c_id', None)
    start_time = get_default_param(request,'start_time',None)
    end_time = get_default_param(request, 'end_time', None)
    total = get_default_param(request, 'total', None)
    trainings = {}
    if c_id:
        trainings['training_inprogress'] = get_team_trainings_current(c_id,total).count()
        trainings['completed'] = get_team_trainings_completed(c_id,total).count()
        trainings['scheduled'] = get_team_trainings_incomplete(c_id,total).count()
    else:
        return generic_response(response_json(False,None,constants.TEXT_PARAMS_MISSING),http_status=500)
    trainings = response_json(True, trainings)
    return  generic_response(trainings)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_injury_info(request):
    c_id = get_default_param(request, 'c_id', None)
    injuries = {}
    if c_id:
        injuries['reported_this_week'] = get_reported_team_injuries_last_seven_days(c_id).count()
        injuries['reported_today'] = get_reported_team_injuries_today(c_id).count()
        injuries['confirmed_this_week'] = get_confirmed_injuries_last_seven_days(c_id).count()
        injuries['confirmed_today'] = get_confirmed_injuries_today(c_id).count()
    else:
        return generic_response(response_json(False,None,constants.TEXT_PARAMS_MISSING),http_status=500)
    injuries = response_json(True, injuries)
    return generic_response(injuries)


#Team Injuries Wrappers
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_team_reported_injuries(request):
    c_id = get_default_param(request, 'c_id', None)
    start_datetime = get_default_param(request, 'start_datetime', None)
    end_datetime = get_default_param(request, 'end_datetime', None)
    if c_id:
        team_injuries = get_reported_team_injuries(c_id,start_datetime,end_datetime).values('player_id__name','injury_geolocation', 'injury_type__key')
    else:
        return generic_response(response_json(False, None, constants.TEXT_PARAMS_MISSING), http_status=500)
    team_injuries = response_json(True, list(team_injuries))
    return generic_response(team_injuries)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_team_current_injuries(request):
    c_id = get_default_param(request, 'c_id', None)

    if c_id:
        team_injuries = get_current_team_injuries(c_id).values('player_id__name','injury_geolocation', 'injury_status__key', 'recovery_time')
    else:
        return generic_response(response_json(False, None, constants.TEXT_PARAMS_MISSING), http_status=500)
    team_injuries = response_json(True, list(team_injuries))
    return generic_response(team_injuries)

@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_team_past_injuries(request):
    c_id = get_default_param(request, 'c_id', None)
    year = get_default_param(request, 'year', None)
    if c_id:
        team_injuries = get_past_team_injuries(c_id,year).values('player_id__name','injury_geolocation', 'injury_status__key', 'injury_position__key')
    else:
        return generic_response(response_json(False, None, constants.TEXT_PARAMS_MISSING), http_status=500)
    team_injuries = response_json(True, list(team_injuries))
    return generic_response(team_injuries)
