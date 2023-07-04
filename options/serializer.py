from .models import Options
from rest_framework import serializers

class OptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Options
        fields = ('key', 'value')
