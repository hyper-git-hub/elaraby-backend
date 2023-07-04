from datetime import timedelta
from random import randint

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from customer.models import Customer
from options.models import Options
from user.models import User, Role, Module
from user.enums import RoleTypeEnum
import string
import random
from hypernet.enums import DeviceTypeEntityEnum, OptionsEnum, FFPOptionsEnum
from hypernet.models import Entity, DeviceType
from django.utils import timezone
VOWELS = "aeiou"
CONSONANTS = "".join(set(string.ascii_lowercase) - set(VOWELS))
import traceback

def generate_word(length):
    word = ""
    for i in range(length):
        if i % 2 == 0:
            word += random.choice(CONSONANTS)
        else:
            word += random.choice(VOWELS)
    return word


class Command(BaseCommand):
    """"
        Command python manage.py setupstatuses
    """

    def add_arguments(self, parser):
        parser.add_argument('type', nargs='+', type=str)

    def handle(self, *args, **options):
        try:
            arr = ['employee', 'truck', 'bin', 'driver']
            type = options['type'][0]
            type = int(type)
            print(type)
            for i in range(10):
                entity = Entity()
                if type == DeviceTypeEntityEnum.EMPLOYEE:
                    entity.name = 'employee ' +str(generate_word(5))
                if type == DeviceTypeEntityEnum.TRUCK:
                    entity.name = 'truck ' + str(generate_word(5))
                if type == DeviceTypeEntityEnum.BIN:
                    entity.name = 'bin ' + str(generate_word(5))
                if type == DeviceTypeEntityEnum.DRIVER:
                    entity.name = 'driver ' + str(generate_word(5))
                if type == DeviceTypeEntityEnum.TRUCK:
                    entity.module= Module.objects.get(id=1)
                    print(entity.module)
                if type == DeviceTypeEntityEnum.TRUCK:
                    entity.module = Module.objects.get(id=4)
                entity.status = Options.objects.get(id=OptionsEnum.ACTIVE)
                entity.customer = Customer.objects.get(id=5)
                entity.type = DeviceType.objects.get(id=type)
                entity.modified_by = User.objects.get(id=48)
                if type in [DeviceTypeEntityEnum.DRIVER, DeviceTypeEntityEnum.EMPLOYEE]:
                    entity.cnic = '111-111-111'
                    entity.dob = timezone.now()
                    entity.date_of_joining = timezone.now()
                    entity.gender = Options.objects.get(id=OptionsEnum.MALE)
                    entity.marital_status = Options.objects.get(id=OptionsEnum.SINGLE)

                if type == DeviceTypeEntityEnum.EMPLOYEE:
                    entity.entity_sub_type = Options.objects.get(id=FFPOptionsEnum.LABOUR)

                if type in [DeviceTypeEntityEnum.TRUCK, DeviceTypeEntityEnum.BIN]:
                    entity.volume = False
                    entity.speed = False
                    entity.density = False
                    entity.temperature = False
                    entity.location = False
                    entity.location = False
                if type == DeviceTypeEntityEnum.TRUCK:
                    entity.make = 'Honda'
                    entity.model = '2012'
                    entity.color = 'Black'
                entity.save()
            self.stdout.write(self.style.SUCCESS('Successful.'))

        except Exception as e:
            print (traceback.print_exc())
            self.stdout.write(self.style.WARNING(str(e) + ' ' + 'Failed.'))
            raise CommandError('Failed to Add entities')
