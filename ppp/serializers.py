from rest_framework import serializers
from hypernet.models import Entity
from ppp.models import *

class MatchDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchDetails
        fields = ('competition','home_team_name', 'away_team_name', 'home_team_goals',
                  'away_team_goals', 'home_team_red_cards', 'away_team_red_cards', 'home_team_injuries', 'away_team_injuries')


class PlayerDerived(serializers.ModelSerializer):
    class Meta:
        model = PlayerDerived
        fields = ('player', 'customer' 'competition', 'module', 'goals',
                  'assists', 'chances_created', 'passes', 'wins',
                  'losses', 'yellow_cards', 'red_cards', 'player_of_month', 'player_rating')


