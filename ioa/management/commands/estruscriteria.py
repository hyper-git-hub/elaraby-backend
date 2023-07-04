from django.core.management.base import BaseCommand, CommandError

from hypernet.enums import ModuleEnum, IOAOPTIONSEnum
from ioa.models import EstrusCriteria
from hypernet.models import DeviceViolation


class Command(BaseCommand):
    """"
        Command python manage.py estruscriteria
    """

    def handle(self, *args, **options):
        try:
            estrus_violations = DeviceViolation.objects.filter(module=ModuleEnum.IOA,
                                                               violation_type=IOAOPTIONSEnum.ALERT_TYPE_ESTRUS
                                                               )
            print("Total estrus alerts - {0}".format(estrus_violations.count()))
            for entry in estrus_violations:
                ec = EstrusCriteria()
                ec.animal = entry.device
                ec.save()
            self.stdout.write(self.style.SUCCESS('Successful.'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(str(e) + 'Failed.'))
            raise CommandError('Failed to Setup IOA EstrusCriteria')
