from __future__ import unicode_literals

from django.db import models

from user.enums import RoleTypeEnum
from backend import settings
from hypernet.enums import OptionsEnum
from hypernet.enums import IOFOptionsEnum
from django.db.models import Avg, Sum, Min, Max
from .models import *
from hypernet import constants, enums
from hypernet.models import Entity
from hypernet.enums import *
from hypernet.utils import *
from rest_framework.response import Response
#This file contains player match stats and player derived utils.

####Player Stats Utilities####


def get_player_goals(p_id,m_id, c_id, start_time,end_time):
    try:
        if c_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, competition__id=c_id).goal_normal
        elif m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).goal_normal
        elif m_id and c_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id, competition__id=c_id).goal_normal
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id, timestamp__range=(start_time, end_time)).aggregate(Sum('goal_normal'))
        else:
            return PlayerDerived.objects.get(player__id=p_id).goals

    except:
        return None

def get_player_head_goals(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).goal_head
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id, timestamp__range=(start_time, end_time)).aggregate(Sum('goal_head'))
        else:
            return PlayerPerformanceStats.objects.filter(id=p_id).aggregate(Sum('goal_head'))
    except:
        return None

def get_player_open_play_goals(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).goal_open_play
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id, timestamp__range=(start_time, end_time)).aggregate(Sum('goal_open_play'))
        else:
            return PlayerPerformanceStats.objects.filter(id=p_id).aggregate(Sum('goal_open_play'))
    except:
        return None

def get_player_goals_per_match(p_id,start_time,end_time):
    try:
        if start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Avg('goal_normal'))
        else:
            return PlayerPerformanceStats.objects.filter(player=p_id).aggregate(Avg('goal_normal'))

    except:
        return None

def get_player_goals_per_match(p_id,start_time,end_time):
    try:
        if start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Avg('goal_normal'))
        else:
            return PlayerPerformanceStats.objects.filter(player=p_id).aggregate(Avg('goal_normal'))

    except:
        return None

def get_player_assists(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).assists
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id, timestamp__range=(start_time, end_time)).aggregate(Sum('assists'))
        else:
            return PlayerDerived.objects.get(id=p_id).assists
    except:
        return None

def get_player_assists_per_match(p_id,start_time,end_time):
    try:
        if start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Avg('assists'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Avg('assists'))

    except:
        return None

def get_player_blocks(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).shot_blocked
        elif start_time and end_time:
            return PlayerDerived.objects.filter(player__id=p_id, timestamp__range=(start_time, end_time)).aggregate(Sum('shot_blocked'))
        else:
            return PlayerDerived.objects.filter(id=p_id).aggregate(Sum('shot_blocked'))
    except:
        return None

def get_outfielder_block(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).outfielder_block
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id, timestamp__range=(start_time, end_time)).aggregate(Sum('outfielder_block'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('outfielder_block'))
    except:
        return None

def get_player_defensive_third(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).defensive_third
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id, timestamp__range=(start_time, end_time)).aggregate(Sum('defensive_third'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('defensive_third'))
    except:
        return None

def get_player_mid_third(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).mid_third
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id, timestamp__range=(start_time, end_time)).aggregate(Sum('mid_third'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('mid_third'))
    except:
        return None

def get_player_final_third(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).final_third
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id, timestamp__range=(start_time, end_time)).aggregate(Sum('final_third'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('final_third'))
    except:
        return None

def get_player_right_passes(p_id, m_id, start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).pass_left
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id, timestamp__range=(start_time, end_time)).aggregate(Sum('pass_left'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('pass_left'))
    except:
        return None

def get_player_left_passes(p_id, m_id, start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).pass_right
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id, timestamp__range=(start_time, end_time)).aggregate(Sum('pass_right'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('pass_right'))
    except:
        return None

def get_player_forward_passes(p_id, m_id, start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).pass_forward
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('pass_forward'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('pass_forward'))
    except:
        return None

def get_player_backward_passes(p_id, m_id, start_time, end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).pass_back
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('pass_back'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('pass_back'))
    except:
        return None


def get_player_passes(p_id, m_id, start_time, end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).passes
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('passes'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('passes'))
    except:
        return None

def get_player_accurate_passes(p_id, m_id, start_time, end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).pass_accurate
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('pass_accurate'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('pass_accurate'))
    except:
        return None

def get_player_inaccurate_passes(p_id, m_id, start_time, end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).pass_inaccurate
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('pass_inaccurate'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('pass_inaccurate'))
    except:
        return None

def get_player_short_passes(p_id, m_id, start_time, end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).short_pass_accurate
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('short_pass_accurate'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('short_pass_accurate'))
    except:
        return None

def get_player_inaccurate_short_passes(p_id, m_id, start_time, end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).short_pass_inaccurate
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('short_pass_inaccurate'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('short_pass_inaccurate'))
    except:
        return None

def get_player_final_third_passes(p_id, m_id, start_time, end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).successful_final_third_passes
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('successful_final_third_passes'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('successful_final_third_passes'))
    except:
        return None

def get_player_pass_per_match(p_id,start_time,end_time):
    try:
        if start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Avg('passes'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Avg('passes'))

    except:
        return None

def get_player_cross_pass(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).pass_cross_accurate
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('pass_cross_accurate'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('pass_cross_accurate'))
    except:
        return None

def get_player_inaccurate_cross_pass(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).pass_cross_inaccurate
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('pass_cross_inaccurate'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('pass_cross_inaccurate'))
    except:
        return None

def get_played_dispossessed(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).dispossessed
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('dispossessed'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('dispossessed'))
    except:
        return None

def get_chances_created(p_id, m_id, start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).big_chance_created
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('big_chance_created'))
        else:
            return PlayerDerived.objects.get(played__id=p_id).chances_created

    except:
        return None


def get_performance_index(p_id):
    try:
        return PlayerProcessed.objects.get(player__id=p_id).player_performance_index
    except:
        return None

def get_mins_played(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).mins_played
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('mins_played'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('mins_played'))
    except:
        return None

def get_player_interceptions(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).interception_all
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('interception_all'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('interception_all'))
    except:
        return None

def get_player_challenge_lost(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).challenge_lost
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('challenge_lost'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('challenge_lost'))
    except:
        return None

def get_player_interceptions(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).interception_all
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('interception_all'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('interception_all'))
    except:
        return None

def get_player_goal_left_foot(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).goal_left_foot
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('goal_left_foot'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('goal_left_foot'))
    except:
        return None

def get_player_goal_counter(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).goal_counter
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('goal_counter'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('goal_counter'))
    except:
        return None


def get_player_key_pass(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).key_pass_other
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('key_pass_other'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('key_pass_other'))
    except:
        return None

def get_player_accurate_passes(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).pass_accurate
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('pass_accurate'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('pass_accurate'))
    except:
        return None


def get_player_chipped_passes(p_id, m_id, start_time, end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).pass_accurate
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('pass_chipped'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('pass_chipped'))
    except:
        return None

def get_player_corner_passes(p_id, m_id, start_time, end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).pass_corner_accurate
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('pass_corner_accurate'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('pass_corner_accurate'))
    except:
        return None

def get_player_corner_inaccurate_passes(p_id, m_id, start_time, end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).pass_corner_inaccurate
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('pass_corner_inaccurate'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('pass_corner_inaccurate'))
    except:
        return None

def get_player_corner_awarded(p_id, m_id, start_time, end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).corner_awarded
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('corner_awarded'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('corner_awarded'))
    except:
        return None


def get_player_touches(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).touches
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('touches'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('touches'))
    except:
        return None

def get_player_touch_per_match(p_id,start_time,end_time):
    try:
        if start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Avg('touches'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Avg('touches'))

    except:
        return None

def get_player_accurate_longballs(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).pass_long_ball_accurate
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('pass_long_ball_accurate'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('pass_long_ball_accurate'))
    except:
        return None

def get_player_inaccurate_longballs(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).pass_long_ball_inaccurate
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('pass_long_ball_inaccurate'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('pass_long_ball_inaccurate'))
    except:
        return None

def get_player_duel_aerial_won(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).duel_aerial_won
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('duel_aerial_won'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('duel_aerial_won'))
    except:
        return None

def get_player_duel_aerial_won_per_match(p_id,start_time,end_time):
    try:
        if start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Avg('duel_aerial_won'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Avg('duel_aerial_won'))
    except:
        return None

def get_player_duel_aerial_lost(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).duel_aerial_lost
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('duel_aerial_lost'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('duel_aerial_lost'))
    except:
        return None

def get_player_duel_aerial_lost_per_match(p_id,start_time,end_time):
    try:
        if start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Avg('duel_aerial_lost'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Avg('duel_aerial_lost'))
    except:
        return None

def get_player_total_shots(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).shots_total
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('shots_total'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('shots_total'))
    except:
        return None

def get_player_left_foot_shots(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).shot_left_foot
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('shot_left_foot'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('shot_left_foot'))
    except:
        return None

def get_player_right_foot_shots(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).shot_right_foot
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('shot_right_foot'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('shot_right_foot'))
    except:
        return None

def get_player_set_piece_shots(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).shot_set_piece
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('shot_set_piece'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('shot_set_piece'))
    except:
        return None

def get_player_open_play_shots(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).shot_open_play
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('shot_open_play'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('shot_open_play'))
    except:
        return None

def get_player_throw_ins(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).throw_in
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('throw_in'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('throw_in'))
    except:
        return None

def get_player_block_per_match(p_id,start_time,end_time):
    try:
        if start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Avg('shot_blocked'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Avg('shot_blocked'))
    except:
        return None

def get_player_tackles_won(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).tackle_won
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('tackle_won'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('tackle_won'))
    except:
        return None

def get_player_tackles_lost(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).tackle_lost
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('tackle_lost'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('tackle_lost'))
    except:
        return None

def get_player_ball_recovery(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).ball_recovery
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('ball_recovery'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('ball_recovery'))
    except:
        return None

def get_player_yellow_cards(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).yellow_cards
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('yellow_cards'))['yellow_cards__sum']
        else:
            return PlayerDerived.objects.get(player__id=p_id).yellow_cards
    except:
        return None

def get_player_fouls_commited(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).foul_committed
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('foul_committed'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('foul_committed'))
    except:
        return None

def get_player_fouls_given(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).foul_given
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('foul_given'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('foul_given'))
    except:
        return None

def get_player_red_cards(p_id,m_id, c_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).red_card
        if c_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, competition__id=c_id).red_card
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('red_card'))['red_card__sum']
        else:
            return PlayerDerived.objects.get(player__id=p_id).red_cards
    except:
        return None

def get_yellow_cards_per_match(p_id,start_time,end_time):
    try:
        if start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Avg('yellow_card'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Avg('yellow_card'))
    except:
        return None

def get_red_cards_per_match(p_id,start_time,end_time):
    try:
        if start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Avg('red_card'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Avg('red_card'))
    except:
        return None

def get_player_offensive_duels(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).offensive_duel
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('offensive_duel'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('offensive_duel'))
    except:
        return None

def get_offensive_duels_per_match(p_id,start_time,end_time):
    try:
        if start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Avg('offensive_duel'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Avg('offensive_duel'))
    except:
        return None

def player_defensive_duels(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).defensive_duel
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('defensive_duel'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('defensive_duel'))
    except:
        return None

def defensive_duels_per_match(p_id,start_time,end_time):
    try:
        if start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Avg('yellow_card'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Avg('yellow_card'))
    except:
        return None

def get_player_possession(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).possession
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('possession'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('possession'))
    except:
        return None

def possession_per_match(p_id,start_time,end_time):
    try:
        if start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Avg('possession'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Avg('possession'))
    except:
        return None

def get_player_clearance(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).clearance_total
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('clearance_total'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('clearance_total'))
    except:
        return None

def get_player_sub_on(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).sub_on
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('sub_on'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('sub_on'))
    except:
        return None

def get_player_sub_off(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).sub_off
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('sub_off'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('sub_off'))
    except:
        return None

def get_player_head_clearance(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).clearance_head
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('clearance_head'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('clearance_head'))
    except:
        return None

def get_player_clearance_effective(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).clearance_effective
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('clearance_effective'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('clearance_effective'))
    except:
        return None


def get_player_offside(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).offside_given
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('offside_given'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('offside_given'))
    except:
        return None


def get_keeper_save_hands(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).save_hands
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id, timestamp__range=(start_time,end_time)).aggregate(Sum('save_hands'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('save_hands'))
    except:
        return None

def get_keeper_save_penalty_area(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).save_penalty_area
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id, timestamp__range=(start_time,end_time)).aggregate(Sum('save_penalty_area'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('save_penalty_area'))
    except:
        return None

def get_keeper_punches(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).punches
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id, timestamp__range=(start_time,end_time)).aggregate(Sum('punches'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('punches'))
    except:
        return None

def get_keeper_diving_save(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).keeper_diving_save
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id, timestamp__range=(start_time,end_time)).aggregate(Sum('keeper_diving_save'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('keeper_diving_save'))
    except:
        return None

def get_keeper_standing_save(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).standing_save
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id, timestamp__range=(start_time,end_time)).aggregate(Sum('standing_save'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('standing_save'))
    except:
        return None

def get_keeper_save_total(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).keeper_save_total
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id, timestamp__range=(start_time,end_time)).aggregate(Sum('keeper_save_total'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('keeper_save_total'))
    except:
        return None

def get_keeper_box_save(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).keeper_save_in_the_box
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id, timestamp__range=(start_time,end_time)).aggregate(Sum('keeper_save_in_the_box'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('keeper_save_in_the_box'))
    except:
        return None

def get_keeper_claim_high_won(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).keeper_claim_high_won
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id, timestamp__range=(start_time,end_time)).aggregate(Sum('keeper_claim_high_won'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('keeper_claim_high_won'))
    except:
        return None

def get_keeper_smother(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).keeper_smother
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id, timestamp__range=(start_time,end_time)).aggregate(Sum('keeper_smother'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('keeper_smother'))
    except:
        return None

def get_parried_save(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).parried_safe
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id, timestamp__range=(start_time,end_time)).aggregate(Sum('parried_safe'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('parried_safe'))
    except:
        return None

def get_player_offside(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).offside_given
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('offside_given'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('offside_given'))
    except:
        return None

def get_goal_six_yard(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).goal_six_yard_box
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('goal_six_yard_box'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('goal_six_yard_box'))
    except:
        return None

def get_player_penalty_goals(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).goal_penalty_area
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('goal_penalty_area'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('goal_penalty_area'))
    except:
        return None

def get_player_overrun(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).overrun
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('overrun'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('overrun'))
    except:
        return None

def get_player_dribbles_won(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).dribble_won
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('dribble_won'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('dribble_won'))
    except:
        return None

def get_player_dribbles_lost(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).dribble_lost
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('dribble_lost'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('dribble_lost'))
    except:
        return None

def get_player_chances_missed(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).big_chance_missed
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('big_chance_missed'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('big_chance_missed'))
    except:
        return None

def get_player_chances_created(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).big_chance_created
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('big_chance_created'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('big_chance_created'))
    except:
        return None

def get_player_closs_miss_left(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).close_miss_left
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('close_miss_left'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('close_miss_left'))
    except:
        return None

def get_player_closs_miss_right(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).close_miss_right
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('close_miss_right'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('close_miss_right'))
    except:
        return None

def get_player_throughball(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).key_pass_throughball
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('key_pass_throughball'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('key_pass_throughball'))
    except:
        return None


def get_player_accurate_throughball(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).pass_through_ball_accurate
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('pass_through_ball_accurate'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('pass_through_ball_accurate'))
    except:
        return None

def get_player_filed_reports(p_id,m_id,start_time,end_time):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).filed_reports
        elif start_time and end_time:
            return PlayerPerformanceStats.objects.filter(player__id=p_id,timestamp__range=(start_time, end_time)).aggregate(Sum('filed_reports'))
        else:
            return PlayerPerformanceStats.objects.filter(player__id=p_id).aggregate(Sum('filed_reports'))
    except:
        return None

def is_motm(p_id,m_id):
    try:
        if m_id:
            return PlayerPerformanceStats.objects.get(player__id=p_id, match__id=m_id).man_of_the_match
        else:
            return Response(response_json(False, {"match_id": str(m_id)}, "Failed" + constants.TEXT_PARAMS_MISSING))
    except:
        return None

def get_match_home_team_name(m_id):
    try:
        return PlayerPerformanceStats.objects.get(match__id=m_id).home_team_name
    except:
        return None


def get_match_away_team_name(m_id):
    try:
        return PlayerPerformanceStats.objects.get(match__id=m_id).away_team_name
    except:
        return None

####Player Derived Utilities####


def get_top_n_players():
    try:
        PlayerDerived.objects.all().order_by('-player_rating').values('player__name','player_rating')
    except:
        return None

def get_player_total_goals(p_id, c_id):
    try:
        if c_id:
            return PlayerDerived.objects.get(player__id=p_id, competition__id=c_id).goals
        else:
            return PlayerDerived.objects.filter(player__id=p_id).aggregate(Sum('goals'))
    except:
        return None


def get_player_total_assists(p_id, c_id):
    try:
        if c_id:
            return PlayerDerived.objects.get(player__id=p_id, competition__id=c_id).assists
        else:
            return PlayerDerived.objects.filter(player__id=p_id).aggregate(Sum('assists'))
    except:
        return None


def get_player_total_chances_created(p_id, c_id):
    try:
        if c_id:
            return PlayerDerived.objects.get(player__id=p_id, competition__id=c_id).chances_created
        else:
            return PlayerDerived.objects.filter(player__id=p_id).aggregate(Sum('chances_created'))
    except:
        return None


def get_player_wins(p_id, c_id):
    try:
        if c_id:
            return PlayerDerived.objects.get(player__id=p_id, competition__id=c_id).wins
        else:
            return PlayerDerived.objects.filter(player__id=p_id).aggregate(Sum('wins'))['wins__sum']
    except:
        return None


def get_player_total_losses(p_id, c_id):
    try:
        if c_id:
            return PlayerDerived.objects.get(player__id=p_id, competition__id=c_id).losses
        else:
            return PlayerDerived.objects.filter(player__id=p_id).aggregate(Sum('losses'))['losses__sum']
    except:
        return None


def get_player_total_yellow_cards(p_id, c_id):
    try:
        if c_id:
            return PlayerDerived.objects.get(player__id=p_id, competition__id=c_id).yellow_cards
        else:
            return PlayerDerived.objects.filter(player__id=p_id).aggregate(Sum('yellow_cards'))['yellow_cards__sum']

    except:
        return None


def get_player_total_red_cards(p_id, c_id):
    try:
        if c_id:
            return PlayerDerived.objects.get(player__id=p_id, competition__id=c_id).red_cards
        else:
            return PlayerDerived.objects.filter(player__id=p_id).aggregate(Sum('red_cards'))['red_cards__sum']
    except:
        return None


def get_player_total_foul_committed(p_id, c_id):
    try:
        if c_id:
            return PlayerDerived.objects.get(player__id=p_id, competition__id=c_id).foul_committed
        else:
            return PlayerDerived.objects.filter(player__id=p_id).aggregate(Sum('foul_committed'))
    except:
        return None


def get_player_total_foul_given(p_id, c_id):
    try:
        if c_id:
            return PlayerDerived.objects.get(player__id=p_id, competition__id=c_id).foul_given
        else:
            return PlayerDerived.objects.filter(player__id=p_id).aggregate(Sum('foul_given'))
    except:
        return None


def get_player_total_potm(p_id, c_id):
    try:
        if c_id:
            return PlayerDerived.objects.get(player__id=p_id, competition__id=c_id).player_of_month
        else:
            return PlayerDerived.objects.filter(player__id=p_id).aggregate(Sum('player_of_month'))
    except:
        return None


def get_player_rating(p_id, c_id):
    try:
        if c_id:
            return PlayerDerived.objects.get(player__id=p_id, competition__id=c_id).player_rating
        else:
            return PlayerDerived.objects.filter(player__id=p_id).aggregate(Avg('player_rating'))['player_rating__sum']
    except:
        return None
##Team Derived utils

def get_team_competition(c_id):
    try:
        return TeamDerived.objects.get(competition__id=c_id).competition.name
    except:
        return None

def get_team_apps(c_id):
    try:
        return TeamDerived.objects.get(competition__id=c_id).total_games_played
    except:
        return None

def get_team_wins(c_id):
    try:
        return TeamDerived.objects.get(competition__id=c_id).total_wins
    except:
        return None

def get_team_draws(c_id):

    try:
        return TeamDerived.objects.get(competition__id=c_id).total_wins
    except:
        return None


def get_team_losses(c_id):
    try:
        return TeamDerived.objects.get(competition__id=c_id).total_losses
    except:
        return None


def get_team_goals_for(c_id):
    try:
        return TeamDerived.objects.get(competition__id=c_id).total_goals_by_team
    except:
        return None


def get_team_goals_against(c_id):
    try:
        return TeamDerived.objects.get(competition__id=c_id).total_goals_against_team
    except:
        return None

def get_highest_rated_player():
    try:
        return PlayerDerived.objects.all().order_by('-rating')[0].player.name
    except:
        return None

def get_lowest_rated_player():
    try:
        return PlayerDerived.objects.all().order_by('rating')[0].player.name
    except:
        return None


def get_most_fit_player():
    try:
        return PlayerProcessed.objects.all().order_by('-fitness_index_of_player')[0].player.name
    except:
        return None


def get_least_fit_player():
    try:
        return PlayerProcessed.objects.all().order_by('fitness_index_of_player')[0].player.name
    except:
        return None

def get_all_players_stats(c_id):
    try:
        if c_id:
            return PlayerDerived.objects.filter(customer__id = c_id)
        else:
            return PlayerDerived.objects.all()
    except:
        return None


def get_players_position(c_id,position):
    try:
        if c_id:
            return PlayerDerived.objects.filter(customer__id=c_id,player__player_position__icontains = position).order_by('-player_rating')
        else:
            return PlayerDerived.objects.all()
    except:
        return None

def get_upcoming_match(c_id):
    try:
        Entity.objects.filter(customer__id=c_id).order_by('-date_of_match').values('name','date_of_match','weather_forecast','match_type')[0]
    except:
        return None
