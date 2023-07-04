from __future__ import unicode_literals

from django.db import models
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
from rest_framework.decorators import api_view, APIView, permission_classes
from .serializers import *

from hypernet.constants import ERROR_RESPONSE_BODY, RESPONSE_DATA, STATUS_OK, RESPONSE_STATUS, RESPONSE_MESSAGE

from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAdminUser,
    IsAuthenticatedOrReadOnly,

)

###Wrappers for dashboard###

#def last_match_stats(m_id):
#   if m_id:
#    last_match_goals = get_match_goals(m_id)
#     last_match_assists = get_match_assists(m_id)
#       last_match_possession = get_match_possession(m_id)
#    last_match_yellow_cards = get_match_yellow_cards(m_id)
#    last_match_red_cards = get_match_yellow_cards(m_id)

#    return last_match_goals, last_match_assists, last_match_possession, last_match_yellow_cards, last_match_red_cards
#   else:
#      return Response(response_json(False, None, "MatchID not defined"))

@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_player_info(request):
    p_id = int(get_param(request, 'p_id', None))
    data = {}
    data['player_info'] = get_player_meta_info(p_id)
    return generic_response(data, http_status=200)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_player_performance_stats(request):
    p_id = get_default_param(request, 'p_id', None)
    m_id = get_default_param(request, 'm_id', None)
    c_id = get_default_param(request, 'c_id', None)
    start_datetime = get_default_param(request, 'start_datetime', None)
    end_datetime = get_default_param(request, 'end_datetime', None)
    data = {}
    data['player_goals'] =  get_player_goals(p_id, m_id, c_id, start_datetime, end_datetime)
    data['player_wins'] =  get_player_wins(p_id, c_id)
    data['player_losses'] =  get_player_total_losses(p_id, c_id)
    data['player_index'] =  get_player_rating(p_id, c_id)
    return generic_response(data, http_status=200)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def  get_player_competition_stats(request):
    p_id = get_default_param(request, 'p_id', None)
    c_id = get_default_param(request, 'c_id', None)
    start_datetime = get_default_param(request, 'start_datetime', None)
    end_datetime = get_default_param(request, 'end_datetime', None)
    data = dict()
    discipline_data = dict()

    discipline_data['player_yellow_cards'] =  get_player_total_yellow_cards(p_id, c_id)
    discipline_data['player_red_cards'] =  get_player_total_red_cards(p_id, c_id)
    discipline_data['player_fouls_given'] =  get_player_fouls_given(p_id, c_id, start_datetime, end_datetime)
    discipline_data['player_fouls_committed'] =  get_player_fouls_commited(p_id, c_id, start_datetime, end_datetime)

    data['player_wins'] =  get_player_red_cards(p_id, c_id)
    data['player_losses'] =  get_player_total_losses(p_id, c_id, )
    data['player_index'] =  get_player_rating(p_id, c_id )

    data = response_json(True, data)
    return generic_response(data, http_status=200)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_player_trainings(request):

    p_id = get_default_param(request, 'p_id', None)

    result = dict()
    data = dict()
    session_data = dict()

    data['trainings_completed'] =  get_player_trainings_completed(p_id,True)
    data['trainings_incomplete'] =  get_player_trainings_incomplete(p_id,True)
    for training in data['trainings_completed']:
        session_data[training.pk]=get_training_sessions(training.pk)
    for training in data['trainings_incomplete']:
        session_data[training.pk]=get_training_sessions(training.pk)

    result['trainings'] = data
    result['sessions'] = session_data

    result = response_json(True, result)
    return generic_response(result, http_status=200)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_player_injuries_data(request):

    p_id = get_default_param(request, 'p_id', None)
    start_datetime = get_default_param(request, 'start_datetime', None)
    end_datetime = get_default_param(request, 'end_datetime', None)

    result = dict()
    data = dict()

    result['attended_injuries'] =  get_player_injuries(p_id,start_datetime, end_datetime)
    result['reported_injuries'] =  get_player_reported_injuries(p_id,start_datetime, end_datetime)
    data['injury_status'] =  get_injury_status(p_id)
    data['recovery_time'] =  get_recovery_time(p_id)
    data['injury_position'] =  get_injury_position(p_id)
    data['injury_location'] =  get_injury_location(p_id)
    data['backup_substitute'] =  get_backup_substitute(p_id)

    result['current_injuries'] = data
    result = response_json(True, result)
    return generic_response(result, http_status=200)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_player_fitness_data(request):
    p_id = get_default_param(request, 'p_id', None)
    start_datetime = get_default_param(request, 'start_datetime', None)
    end_datetime = get_default_param(request, 'end_datetime', None)
    data = {}

    data['player_fitness_index'] =  get_player_fitness_index (p_id, start_datetime, end_datetime)
    data['player_sleep_time'] =  get_player_sleep_time(p_id, start_datetime, end_datetime)
    data['player_sleep_latency'] =  get_player_sleep_latency(p_id, start_datetime, end_datetime)
    data['player_sleep_efficiency'] =  get_player_sleep_efficiency(p_id, start_datetime, end_datetime)
    data['player_sleep_wake_time'] =  get_player_sleep_waketime(p_id, start_datetime, end_datetime)
    data['player_sleep_calories_avg'] =  get_player_calories_burnt_avg(p_id, start_datetime, end_datetime)

    data = response_json(True, data)
    return generic_response(data)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_team_trainings(request):

    c_id = get_default_param(request, 'c_id', None)
    aggregate = get_default_param(request, 'aggregate', None)
    result = dict()
    data = dict()
    session_data = dict()


    data['trainings_current'] =  get_team_trainings_current(c_id, aggregate)
    data['trainings_completed'] =  get_team_trainings_completed(c_id, aggregate)
    data['trainings_incomplete'] =  get_team_trainings_incomplete(c_id, aggregate)
    for training in data['trainings_ccurrent']:
        session_data[training.pk] = get_training_sessions(training.pk)
    for training in data['trainings_completed']:
        session_data[training.pk] = get_training_sessions(training.pk)
    for training in data['trainings_incomplete']:
        session_data[training.pk] = get_training_sessions(training.pk)

    result['trainings'] = data
    result['sessions'] = session_data

    return generic_response(response_json(True, result), http_status=200)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_team_fitness(request):

    p_id = get_default_param(request, 'p_id', None)
    start_datetime = get_default_param(request, 'start_datetime', None)
    end_datetime = get_default_param(request, 'end_datetime', None)
    result = dict()
    data = dict()

    data['trainings_current'] =  get_team_trainings_current(p_id, start_datetime, end_datetime)
    data['trainings_completed'] =  get_team_trainings_completed(p_id, start_datetime, end_datetime)
    data['trainings_incomplete'] =  get_team_trainings_incomplete(p_id, start_datetime, end_datetime)

    result['fitness'] = data

    return generic_response(response_json(True, result), http_status=200)