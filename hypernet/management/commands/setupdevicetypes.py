import traceback

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError

from hypernet.models import DeviceType
from hypernet.enums import DeviceTypeEntityEnum, DeviceCategoryEnum, DeviceTypeAssignmentEnum



class Command(BaseCommand):
    """"
        Command python manage.py setupdevicetypes
    """

    def handle(self, *args, **options):
        try:
            for choice in DeviceTypeEntityEnum.choices():
                name = str(choice[1]).title()
                try:
                    DeviceType.objects.update_or_create(id=choice[0], name=name, category=DeviceCategoryEnum.ENTITY,
                                                        defaults={'name': name, })
                except IntegrityError as e:
                    pass
            for choice in DeviceTypeAssignmentEnum.choices():
                name = str(choice[1]).title()
                try:
                    DeviceType.objects.update_or_create(id=choice[0], name=name, category=DeviceCategoryEnum.ASSIGNMENT,
                                                        defaults={'name': name, })
                except IntegrityError as e:
                    pass
            self.stdout.write(self.style.SUCCESS('Successful.'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(str(e) + 'Failed.'))
            raise CommandError('Failed to Setup Device Types')
