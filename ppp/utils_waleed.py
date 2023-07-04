from rest_framework.response import Response
from rest_framework.permissions import (
    AllowAny,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Avg, Max, Min, Sum, Count
from datetime import datetime

from hypernet import constants, enums
from hypernet.models import Entity
from hypernet.enums import *
from .models import *
from hypernet.enums import OptionsEnum, PPPOptionsEnum
import datetime
# Create your views here.


# class GetEntity(APIView):
#     """
#     """
#     """
#             @api {get} /hypernet/entity/
#             @apiName GetEntity
#             @apiGroup Entity
#             @apiDescription Return the entity of the id specified
#             @apiParam {Integer} [id] device_id
#
#     """
#     permission_classes = [AllowAny]
#
#     def get(self, request):
###############################################
########### Player Performance Info ###########
###############################################

def get_player_meta_info(p_id):
    try:
        return Entity.objects.get(id=p_id).as_player_json()
    except:
        return None



###############################################
########### Trainings Utilities ###############
###############################################

def get_team_trainings_incomplete(customer_id, total):
    try:
        if total:
            return TrainingMetrics.objects.filter(customer__id=customer_id,
                                                  training_status=PPPOptionsEnum.TRAINING_INCOMPLETE).order_by(
                '-timestamp')
        else:
            return TrainingMetrics.objects.filter(customer__id=customer_id,
                                                  training_status=PPPOptionsEnum.TRAINING_INCOMPLETE,
                                                  end_timestamp__gte=datetime.now(),
                                                  start_timestamp__lte=datetime.now()).order_by('-timestamp')
    except:
        return None


def get_team_trainings_completed(customer_id, total):
    try:
        if total:
            return TrainingMetrics.objects.filter(customer__id=customer_id,
                                                  training_status=PPPOptionsEnum.TRAINING_COMPLETED).order_by(
                '-timestamp')
        else:
            return TrainingMetrics.objects.filter(customer__id=customer_id,
                                                  training_status=PPPOptionsEnum.TRAINING_COMPLETED,
                                                  end_timestamp__gte=datetime.now(),
                                                  start_timestamp__lte=datetime.now()).order_by('-timestamp')
    except:
        return None


def get_team_trainings_current(customer_id, total):
    try:
        if total:
            return TrainingMetrics.objects.filter(customer__id=customer_id,
                                                  training_status=PPPOptionsEnum.TRAINING_INPROGRESS).order_by(
                '-timestamp')
        else:
            return TrainingMetrics.objects.filter(customer__id=customer_id,
                                                  training_status=PPPOptionsEnum.TRAINING_INPROGRESS,
                                                  end_timestamp__gte=datetime.now(),
                                                  start_timestamp__lte=datetime.now()).order_by('-timestamp')
    except:
        return None


def get_player_trainings_incomplete(p_id, total):
    try:
        if total:
            return TrainingMetrics.objects.filter(player__id=p_id,
                                                  training_status=PPPOptionsEnum.TRAINING_INCOMPLETE).order_by(
                '-timestamp')
        else:
            return TrainingMetrics.objects.filter(player__id=p_id, training_status=PPPOptionsEnum.TRAINING_INCOMPLETE,
                                                  end_timestamp__gte=datetime.now(),
                                                  start_timestamp__lte=datetime.now()).order_by('-timestamp')
    except:
        return None


def get_player_trainings_completed(p_id, total):
    try:
        if total:
            return TrainingMetrics.objects.filter(player__id=p_id,
                                                  training_status=PPPOptionsEnum.TRAINING_COMPLETED).order_by(
                '-timestamp')
        else:
            return TrainingMetrics.objects.filter(player__id=p_id, training_status=PPPOptionsEnum.TRAINING_COMPLETED,
                                                  end_timestamp__gte=datetime.now(),
                                                  start_timestamp__lte=datetime.now()).order_by('-timestamp')
    except:
        return None


def get_player_trainings_current(p_id, total):
    try:
        if total:
            return TrainingMetrics.objects.filter(player__id=p_id).order_by('-timestamp')
        else:
            return TrainingMetrics.objects.filter(player__id=p_id, end_timestamp__gte=datetime.now(), start_timestamp__lte=datetime.now()).order_by('-timestamp')
    except:
        return None


def get_training_sessions(training_id):
    try:
        return SessionMetrics.objects.filter(training__id=training_id).order_by('-timestamp')
    except:
        return None


############################################
########### Injury Utilities ###############
############################################

def get_injured_players(start_datetime = None, end_datetime = None):
    try:
        if start_datetime and end_datetime:
            return Injury.objects.filter(timestamp__range=[start_datetime,end_datetime])
        else:
            return Injury.objects.all()
    except:
        return None

def get_reported_team_injuries(c_id,start_datetime = None, end_datetime = None):
    try:
        if c_id and start_datetime and end_datetime:
            return ReportedInjury.objects.filter(customer__id = c_id, timestamp__range=[start_datetime,end_datetime])
        else:
            return ReportedInjury.objects.filter(customer__id=c_id)
    except:
        return None

def get_current_team_injuries(customer_id):
    try:
        return Injury.objects.filter(customer__id=customer_id, injury_status=PPPOptionsEnum.INJURED).order_by(
            '-timestammp')
    except:
        return None

def get_confirmed_injuries_last_seven_days(customer_id):
    try:
        today = datetime.date.today()
        last_seven_days = today - datetime.timedelta(days=7)
        return Injury.objects.filter(timestammp__gte = last_seven_days)
    except:
        return None

def get_past_team_injuries(customer_id,year=None):
    try:
        if year:
            return Injury.objects.filter(customer__id=customer_id, injury_status__key__icontains="Not Injured", timestammp__year=year).order_by('-timestammp')
        else:
            return Injury.objects.filter(customer__id=customer_id,
                                         injury_status__key__icontains="Not Injured").order_by('-timestammp')
    except:
        return None

def get_confirmed_injuries_today(customer_id):
    try:
        return Injury.objects.filter(timestammp__gte = datetime.date.today())
    except:
        return None

def get_reported_team_injuries_last_seven_days(customer_id):
    try:
        today = datetime.date.today()
        last_seven_days = today - datetime.timedelta(days=7)
        return ReportedInjury.objects.filter(timestammp__gte = last_seven_days)
    except:
        return None

def get_reported_team_injuries_today(customer_id):
    try:
        return ReportedInjury.objects.filter(timestammp__gte = datetime.date.today())
    except:
        return None

def get_player_injuries(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return Injury.objects.filter(player_id=p_id, timestamp__range=[start_datetime,end_datetime])
        else:
            return Injury.objects.filter(player_id=p_id)
    except:
        return None


def get_player_reported_injuries(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return ReportedInjury.objects.filter(player_id=p_id, timestamp__range=[start_datetime,end_datetime])
        else:
            return ReportedInjury.objects.filter(player_id=p_id)
    except:
        return None


def get_backup_substitute(p_id):
    try:
        return Injury.objects.get(player_id=p_id).order_by('-timestamp')[0].backup_substitute
    except:
        return None


def get_injury_position(p_id):
    try:
        return Injury.objects.filter(player_id=p_id).order_by('-timestamp')[0].injury_position
    except:
        return None


def get_injury_status(p_id):
    try:
        return Injury.objects.filter(player_id=p_id).order_by('-timestamp')[0].injury_status
    except:
        return None


def get_avg_recovery_time(p_id):
    try:
        return Injury.objects.filter(player_id=p_id).order_by('-timestamp').aggregate(Avg('recovery_time'))
    except:
        return None


def get_injury_location(p_id):
    try:
        return Injury.objects.filter(player_id=p_id).order_by('-timestamp')[0].injury_location
    except:
        return None


def get_recovery_time(p_id):
    try:
        return Injury.objects.filter(player_id=p_id).order_by('-timestamp')[0].recovery_time
    except:
        return None

##############################################
########## Match Statistics Utilities ##########
##############################################

def get_match_team_names(m_id):
    try:
        if m_id:
            match = MatchDetails.objects.get(match__id=m_id)
            return match.home_team_name, match.away_team_name
        else:
            match = MatchDetails.objects.all().order_by('-match__date_of_match')[0]
            return match.home_team_name, match.away_team_name
    except:
        return None


def get_match_goals(m_id):
    try:
        if m_id:
            match = MatchDetails.objects.get(match__id=m_id)
            return match.home_team_goals, match.away_team_goals
        else:
            match = MatchDetails.objects.all().order_by('-match__date_of_match')[0]
            return match.home_team_goals, match.away_team_goals
    except:
        return None


def get_match_shots_on_target(m_id):
    try:
        if m_id:
            match = MatchDetails.objects.get(match__id=m_id)
            return match.home_team_shots_on_target, match.away_team_shots_on_target
        else:
            match = MatchDetails.objects.all().order_by('-date_of_match')[0]
            return match.home_team_shots_on_target, match.home_team_shots_on_target
    except:
        return None


def get_match_shots_off_target(m_id):
    try:
        if m_id:
            match = MatchDetails.objects.get(match__id=m_id)
            return match.home_team_shots_off_target, match.away_team_shots_off_target
        else:
            match = MatchDetails.objects.all().order_by('-date_of_match')[0]
            return match.home_team_shots_off_target, match.away_team_shots_off_target
    except:
        return None


def get_match_interceptions(m_id):
    try:
        if m_id:
            match = MatchDetails.objects.get(match__id=m_id)
            return match.home_team_interceptions, match.away_team_interceptions
        else:
            match = MatchDetails.objects.all().order_by('-date_of_match')[0]
            return match.home_team_interceptions, match.away_team_interceptions
    except:
        return None


def get_match_corners(m_id):
    try:
        if m_id:
            match = MatchDetails.objects.get(match__id=m_id)
            return match.home_team_corners, match.away_team_corners
        else:
            match = MatchDetails.objects.all().order_by('-date_of_match')[0]
            return match.home_team_corners, match.away_team_corners
    except:
        return None


def get_match_passing_accuracy(m_id):
    try:
        if m_id:
            match = MatchDetails.objects.get(match__id=m_id)
            return match.home_team_passing_accuracy, match.away_team_passing_accuracy
        else:
            match = MatchDetails.objects.all().order_by('-date_of_match')[0]
            return match.home_team_passing_accuracy, match.away_team_passing_accuracy
    except:
        return None


def get_match_passes(m_id):
    try:
        if m_id:
            match = MatchDetails.objects.get(match__id=m_id)
            return match.home_team_passes, match.away_team_passes
        else:
            match = MatchDetails.objects.all().order_by('-date_of_match')[0]
            return match.home_team_passes, match.away_team_passes
    except:
        return None


def get_match_assists(m_id):
    try:
        if m_id:
            match = MatchDetails.objects.get(match__id=m_id)
            return match.home_team_assists, match.away_team_assists
        else:
            match = MatchDetails.objects.all().order_by('-date_of_match')[0]
            return match.home_team_assists, match.away_team_assists
    except:
        return None


def get_match_possession(m_id):
    try:
        if m_id:
            match = MatchDetails.objects.get(match__id=m_id)
            return match.home_team_possession, match.away_team_possession
        else:
            match = MatchDetails.objects.all().order_by('-date_of_match')[0]
            return match.home_team_possession, match.away_team_possession
    except:
        return None


def get_match_offsides(m_id):
    try:
        if m_id:
            match = MatchDetails.objects.get(match__id=m_id)
            return match.home_team_offsides, match.away_team_offsides
        else:
            match = MatchDetails.objects.all().order_by('-date_of_match')[0]
            return match.home_team_offsides, match.away_team_offsides
    except:
        return None


def get_match_yellow_cards(m_id):
    try:
        if m_id:
            match = MatchDetails.objects.get(match__id=m_id)
            return match.home_team_yellow_cards, match.away_team_yellow_cards
        else:
            match = MatchDetails.objects.all().order_by('-date_of_match')[0]
            return match.home_team_yellow_cards, match.away_team_yellow_cards
    except:
        return None


def get_match_red_cards(m_id):
    try:
        if m_id:
            match = MatchDetails.objects.get(match__id=m_id)
            return match.home_team_red_cards, match.away_team_red_cards
        else:
            match = MatchDetails.objects.all().order_by('-date_of_match')[0]
            return match.home_team_red_cards, match.away_team_red_cards
    except:
        return None


def get_match_injuries(m_id):
    try:
        if m_id:
            match = MatchDetails.objects.get(match__id=m_id)
            return match.home_team_injuries, match.away_team_injuries
        else:
            match = MatchDetails.objects.all().order_by('-date_of_match')[0]
            return match.home_team_injuries, match.away_team_injuries
    except:
        return None


def get_match_venue(m_id):
    try:
        if m_id:
            return MatchDetails.objects.get(match__id=m_id).venue.namename
        else:
            return MatchDetails.objects.all().order_by('-match__date_of_match')[0].venue.name
    except:
        return None

def get_match_date(m_id):
    try:
        if m_id:
            return MatchDetails.objects.get(id=m_id).match.date_of_match
        else:
            return MatchDetails.objects.all().order_by('-match__date_of_match')[0].match.date_of_match
    except:
        return None

def get_match_competition(m_id):
    try:
        if m_id:
            return MatchDetails.objects.get(match__id=m_id).competition.name
        else:
            return MatchDetails.objects.all().order_by('-match__date_of_match')[0].competition.name
    except:
        return None

def get_all_match_details(n):

        return MatchDetails.objects.filter().order_by('-match__date_of_match').values('venue__name','competition__name','home_team_name','away_team_name','home_team_goals','away_team_goals')[:n]

##################################################
####### Player Fitness Utilities #################
##################################################

def get_player_fitness_index(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id, timestamp__range=[start_datetime,end_datetime]).aggregate(Avg('fitness_index_of_player'))
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').fitness_index_of_player
    except:
        return None


def get_player_sleep_time(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id, timestamp__range=[start_datetime,end_datetime]).aggregate(Sum('sleepTotalTime'))
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').sleepTotalTime
    except:
        return None


def get_player_sleep_latency(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id, timestamp__range=[start_datetime,end_datetime]).aggregate(Avg('sleep_latency'))
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').sleep_latency
    except:
        return None


def get_player_sleep_efficiency(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id, timestamp__range=[start_datetime,end_datetime]).aggregate(Avg('sleep_efficiency'))
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').sleep_efficiency
    except:
        return None


def get_player_sleep_average(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id, timestamp__range=[start_datetime,end_datetime]).aggregate(Avg('sleepTotalTime'))
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).aggregate(Avg('sleepTotalTime'))
    except:
        return None


def get_player_sleep_efficiency_avg(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id, timestamp__range=[start_datetime,end_datetime]).aggregate(Avg('sleep_efficiency'))
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).aggregate(Avg('sleepTotalTime'))
    except:
        return None


def get_player_sleep_latency_avg(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id, timestamp__range=[start_datetime,end_datetime]).aggregate(Avg('sleep_latency'))
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).aggregate(Avg('sleep_latency'))
    except:
        return None


def get_player_sleep_waketime(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id,
                                                  timestamp__range=[start_datetime, end_datetime]).aggregate(
                Avg('sleepWakeTime'))['sleepWakeTime__avg']
        if start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id, timestamp__year=start_datetime.year, timestamp__month=start_datetime.month, timestamp__day=start_datetime.day).sleepWakeTime
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').sleepWakeTime
    except:
        return None


def get_player_calories_burnt_avg(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id, timestamp__range=[start_datetime,end_datetime]).aggregate(Avg('calories_burnt'))['calories_burnt__avg']
        elif start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id,
                                               timestamp__year=start_datetime.year,
                                               timestamp__month=start_datetime.month,
                                               timestamp__day=start_datetime.day).calories_burnt
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').calories_burnt
    except:
        return None


def get_player_energy_level_total(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id, timestamp__range=[start_datetime,end_datetime]).aggregate(Sum('energy_total'))
        elif start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id,
                                               timestamp__year=start_datetime.year,
                                               timestamp__month=start_datetime.month,
                                               timestamp__day=start_datetime.day).energy_total
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').energy_total
    except:
        return None


def get_player_energy_level_min(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id, timestamp__range=[start_datetime,end_datetime]).aggregate(Min('energy_min'))
        elif start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id,
                                               timestamp__year=start_datetime.year,
                                               timestamp__month=start_datetime.month,
                                               timestamp__day=start_datetime.day).energy_min
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').energy_min
    except:
        return None


def get_player_energy_level_max(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id,
                                                  timestamp__range=[start_datetime, end_datetime]).aggregate(
                Max('energy_max'))
        elif start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id,
                                               timestamp__year=start_datetime.year,
                                               timestamp__month=start_datetime.month,
                                               timestamp__day=start_datetime.day).energy_max
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').energy_max
    except:
        return None


def get_player_calories_min(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id, timestamp__range=[start_datetime,end_datetime]).aggregate(Min('calories_min'))
        elif start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id,
                                               timestamp__year=start_datetime.year,
                                               timestamp__month=start_datetime.month,
                                               timestamp__day=start_datetime.day).calories_min
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').calories_min
    except:
        return None


def get_player_calories_max(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id,
                                                  timestamp__range=[start_datetime, end_datetime]).aggregate(
                Max('calories_max'))
        elif start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id,
                                               timestamp__year=start_datetime.year,
                                               timestamp__month=start_datetime.month,
                                               timestamp__day=start_datetime.day).calories_max
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').calories_max
    except:
        return None


def get_player_heart_rate_avg(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id,
                                                  timestamp__range=[start_datetime, end_datetime]).aggregate(
                Avg('heartrate_avg'))
        elif start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id,
                                               timestamp__year=start_datetime.year,
                                               timestamp__month=start_datetime.month,
                                               timestamp__day=start_datetime.day).heartrate_avg
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').heartrate_avg
    except:
        return None


def get_player_heartrate_min(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id, timestamp__range=[start_datetime,end_datetime]).aggregate(Min('heartrate_min'))
        elif start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id,
                                               timestamp__year=start_datetime.year,
                                               timestamp__month=start_datetime.month,
                                               timestamp__day=start_datetime.day).heartrate_min
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').heartrate_min
    except:
        return None


def get_player_heartrate_max(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id,
                                                  timestamp__range=[start_datetime, end_datetime]).aggregate(
                Max('heartrate_max'))
        elif start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id,
                                               timestamp__year=start_datetime.year,
                                               timestamp__month=start_datetime.month,
                                               timestamp__day=start_datetime.day).heartrate_max
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').heartrate_max
    except:
        return None


def get_player_intensity(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id,
                                                  timestamp__range=[start_datetime, end_datetime]).aggregate(
                Avg('intensity'))
        elif start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id,
                                               timestamp__year=start_datetime.year,
                                               timestamp__month=start_datetime.month,
                                               timestamp__day=start_datetime.day).intensity
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').intensity
    except:
        return None


def get_player_activity(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id,
                                                  timestamp__range=[start_datetime, end_datetime]).aggregate(
                Avg('activity_value'))
        elif start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id,
                                               timestamp__year=start_datetime.year,
                                               timestamp__month=start_datetime.month,
                                               timestamp__day=start_datetime.day).activity_value
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').activity_value
    except:
        return None


def get_player_activity_avg(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id,
                                                  timestamp__range=[start_datetime, end_datetime]).aggregate(
                Avg('activity_avg'))
        elif start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id,
                                               timestamp__year=start_datetime.year,
                                               timestamp__month=start_datetime.month,
                                               timestamp__day=start_datetime.day).activity_avg
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').activity_avg
    except:
        return None


def get_player_activity_min(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id,
                                                  timestamp__range=[start_datetime, end_datetime]).aggregate(
                Min('activity_min'))
        elif start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id,
                                               timestamp__year=start_datetime.year,
                                               timestamp__month=start_datetime.month,
                                               timestamp__day=start_datetime.day).activity_min
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').activity_min
    except:
        return None


def get_player_activity_max(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id,
                                                  timestamp__range=[start_datetime, end_datetime]).aggregate(
                Max('activity_max'))
        elif start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id,
                                               timestamp__year=start_datetime.year,
                                               timestamp__month=start_datetime.month,
                                               timestamp__day=start_datetime.day).activity_max
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').activity_max
    except:
        return None


def get_player_speed(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id,
                                                  timestamp__range=[start_datetime, end_datetime]).aggregate(
                Avg('speed_value'))
        elif start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id,
                                               timestamp__year=start_datetime.year,
                                               timestamp__month=start_datetime.month,
                                               timestamp__day=start_datetime.day).speed_value
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').speed_value
    except:
        return None


def get_player_speed_avg(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id,
                                                  timestamp__range=[start_datetime, end_datetime]).aggregate(
                Avg('speed_avg'))
        elif start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id,
                                               timestamp__year=start_datetime.year,
                                               timestamp__month=start_datetime.month,
                                               timestamp__day=start_datetime.day).speed_avg
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').speed_avg
    except:
        return None


def get_player_speed_max(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id,
                                                  timestamp__range=[start_datetime, end_datetime]).aggregate(
                Max('speed_max'))
        elif start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id,
                                               timestamp__year=start_datetime.year,
                                               timestamp__month=start_datetime.month,
                                               timestamp__day=start_datetime.day).speed_max
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').speed_max
    except:
        return None


def get_player_HRVHF_avg(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id,
                                                  timestamp__range=[start_datetime, end_datetime]).aggregate(
                Avg('HRVHF_avg'))
        elif start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id,
                                               timestamp__year=start_datetime.year,
                                               timestamp__month=start_datetime.month,
                                               timestamp__day=start_datetime.day).HRVHF_avg
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').HRVHF_avg
    except:
        return None


def get_player_HRVHFnorm_avg(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id,
                                                  timestamp__range=[start_datetime, end_datetime]).aggregate(
                Avg('HRVHFnorm_avg'))
        elif start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id,
                                               timestamp__year=start_datetime.year,
                                               timestamp__month=start_datetime.month,
                                               timestamp__day=start_datetime.day).HRVHFnorm_avg
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').HRVHFnorm_avg
    except:
        return None


def get_player_HRVHFnorm_min(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id,
                                                  timestamp__range=[start_datetime, end_datetime]).aggregate(
                Min('HRVHFnorm_min'))
        elif start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id,
                                               timestamp__year=start_datetime.year,
                                               timestamp__month=start_datetime.month,
                                               timestamp__day=start_datetime.day).HRVHFnorm_min
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').HRVHFnorm_min
    except:
        return None


def get_player_HRVHFnorm_max(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id,
                                                  timestamp__range=[start_datetime, end_datetime]).aggregate(
                Max('HRVHFnorm_max'))
        elif start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id,
                                               timestamp__year=start_datetime.year,
                                               timestamp__month=start_datetime.month,
                                               timestamp__day=start_datetime.day).HRVHFnorm_max
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').HRVHFnorm_max
    except:
        return None


def get_player_vo2(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id,
                                                  timestamp__range=[start_datetime, end_datetime]).aggregate(
                Avg('vo2_value'))
        elif start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id,
                                               timestamp__year=start_datetime.year,
                                               timestamp__month=start_datetime.month,
                                               timestamp__day=start_datetime.day).vo2_value
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').vo2_value
    except:
        return None


def get_player_vo2_min(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id,
                                                  timestamp__range=[start_datetime, end_datetime]).aggregate(
                Min('vo2_min_value'))
        elif start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id,
                                               timestamp__year=start_datetime.year,
                                               timestamp__month=start_datetime.month,
                                               timestamp__day=start_datetime.day).vo2_min_value
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').vo2_min_value
    except:
        return None


def get_player_vo2_max(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id,
                                                  timestamp__range=[start_datetime, end_datetime]).aggregate(
                Max('vo2_max_value'))
        elif start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id,
                                               timestamp__year=start_datetime.year,
                                               timestamp__month=start_datetime.month,
                                               timestamp__day=start_datetime.day).vo2_max_value
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').vo2_max_value
    except:
        return None


def get_player_vo2_avg(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id,
                                                  timestamp__range=[start_datetime, end_datetime]).aggregate(
                Avg('vo2_avg'))
        elif start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id,
                                               timestamp__year=start_datetime.year,
                                               timestamp__month=start_datetime.month,
                                               timestamp__day=start_datetime.day).vo2_avg
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').vo2_avg
    except:
        return None


def get_player_asvnn(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id,
                                                  timestamp__range=[start_datetime, end_datetime]).aggregate(
                Avg('AVNN'))
        elif start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id,
                                               timestamp__year=start_datetime.year,
                                               timestamp__month=start_datetime.month,
                                               timestamp__day=start_datetime.day).AVNN
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').AVNN
    except:
        return None


def get_player_asddn(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id,
                                                  timestamp__range=[start_datetime, end_datetime]).aggregate(
                Avg('ASDNN'))
        elif start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id,
                                               timestamp__year=start_datetime.year,
                                               timestamp__month=start_datetime.month,
                                               timestamp__day=start_datetime.day).ASDNN
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').ASDNN
    except:
        return None


def get_player_sleepNonREMTime(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id,
                                                  timestamp__range=[start_datetime, end_datetime]).aggregate(
                Avg('sleepNonREMTime'))
        elif start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id,
                                               timestamp__year=start_datetime.year,
                                               timestamp__month=start_datetime.month,
                                               timestamp__day=start_datetime.day).sleepNonREMTime
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').sleepNonREMTime
    except:
        return None


def get_player_sleepNonTime(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id,
                                                  timestamp__range=[start_datetime, end_datetime]).aggregate(
                Avg('sleepREMTime'))
        elif start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id,
                                               timestamp__year=start_datetime.year,
                                               timestamp__month=start_datetime.month,
                                               timestamp__day=start_datetime.day).sleepREMTime
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').sleepREMTime
    except:
        return None


def get_player_step_count(p_id, start_datetime, end_datetime):
    try:
        if start_datetime and end_datetime:
            return PlayerProcessed.objects.filter(player__id=p_id,
                                                  timestamp__range=[start_datetime, end_datetime]).aggregate(
                Sum('step_count'))
        elif start_datetime:
            return PlayerProcessed.objects.get(player__id=p_id,
                                               timestamp__year=start_datetime.year,
                                               timestamp__month=start_datetime.month,
                                               timestamp__day=start_datetime.day).step_count
        else:
            return PlayerProcessed.objects.filter(player__id=p_id).latest('timestamp').step_count
    except:
        return None