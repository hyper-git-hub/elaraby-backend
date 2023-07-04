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
from .wrappers_waleed import *


class PlayerProfile(APIView):
    def get(self, request):
        action = get_param(request, 'action', None)
        if action:
            if get_param(request, 'p_id', None):
                if action == 'player_info':
                    return get_player_info(request)
                elif action == 'player_performance':
                    return get_player_performance_stats(request)
                elif action == 'player_trainings':
                    return get_player_trainings(request)
                elif action == 'player_competition':
                    return get_player_competition_stats(request)
                elif action == 'player_injuries':
                    return get_player_injuries_data(request)
                elif action == 'player_fitness':
                    return get_player_fitness_data(request)
                else:
                    return generic_response(response_json(False, None, constants.METHOD_DOES_NOT_EXIST), http_status=500)
            else:
                return generic_response(response_json(False, None, constants.TEXT_PARAMS_MISSING), http_status=500)
        else:
            return generic_response(response_json(False, None, constants.TEXT_PARAMS_MISSING), http_status=500)


class TeamTrainings(APIView):
    def get(self, request):
        action = get_param(request, 'action', None)
        if action:
            if get_param(request, 'c_id', None):
                if action == 'player_trainings':
                    return get_team_trainings(request)
                else:
                    return generic_response(response_json(False, None, constants.METHOD_DOES_NOT_EXIST), http_status=500)
            else:
                return generic_response(response_json(False, None, constants.TEXT_PARAMS_MISSING), http_status=500)
        else:
            return generic_response(response_json(False, None, constants.TEXT_PARAMS_MISSING), http_status=500)
