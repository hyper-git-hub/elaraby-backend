from random import randint, randrange
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Max
import datetime as dt
from hypernet.enums import DeviceTypeEntityEnum
from ioa.models import AnimalStates, CustomerDevice
from customer.models import Customer
from hypernet.models import Entity


class Command(BaseCommand):
    """"
        Command python manage.py animalstates
        Required argument:
            number - the number of animals for which to generate states.
    """

    def add_arguments(self, parser):
        parser.add_argument('number', nargs='+', type=int)

    def handle(self, *args, **options):

        number = options['number'][0]
        animal_states = ['estrus', 'feeding', 'moving', 'moving-rumination', 'sitting', 'sitting-lameness',
                         'sitting-rumination', 'standing', 'standing-lameness', 'standing-rumination']
        try:
            for animal in Entity.objects.filter(type=DeviceTypeEntityEnum.ANIMAL)[:number]:
                for i in range(1, 3):
                    for animal_s in animal_states:
                        state = AnimalStates()
                        state.customer = animal.customer
                        state.module = animal.module
                        state.animal = animal
                        state.device = CustomerDevice.objects.get(id=1)  # TODO remove the hard-code
                        state.animal_state = animal_s
                        state.frequency = 10
                        state.created_datetime = dt.date.today() - dt.timedelta(hours=randrange(23),
                                                                                minutes=randint(1, 59),
                                                                                seconds=randint(1, 59))
                        state.save()

            self.stdout.write(self.style.SUCCESS('Successful.'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(str(e) + 'Failed.'))
            raise CommandError('Failed to Create IOA Dummy Data')
