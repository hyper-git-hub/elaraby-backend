import math

from django.core.management.base import BaseCommand

from hypernet.enums import ModuleEnum
from hypernet.constants import player_options_dict
from options.models import Options

class Command(BaseCommand):
    """"
        Command python manage.py setupstatuses
    """

    def handle(self, *args, **options):
        try:
            for o in player_options_dict:
                option = Options()
                option.id = o.get('id')
                option.key = o.get('key')
                option.value = o.get('value')
                option.label = o.get('value')
                option.module = ModuleEnum.PPP
                option.save()
            self.stdout.write(self.style.SUCCESS('Successful.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(str(e) + 'Failed.'))

