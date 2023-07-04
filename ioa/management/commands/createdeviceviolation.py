from django.core.management.base import BaseCommand, CommandError

from hypernet.constants import IOA_VIOLATION_THRESHOLD, IOA_VIOLATION_TYPES
from hypernet.enums import ModuleEnum, DeviceTypeEntityEnum
from hypernet.models import DeviceViolation, Entity
from customer.models import Customer

class Command(BaseCommand):
    """"
        Command python manage.py createdeviceviolation
    """

    def handle(self, *args, **options):
        try:
            # for customer in Customer.objects.all():
            # animals = Entity.objects.filter(module=ModuleEnum.IOA, customer=customer)

            customer = Customer.objects.get(pk=1)
            if customer:
                animals = Entity.objects.filter(module=ModuleEnum.IOA, customer=customer, type=DeviceTypeEntityEnum.ANIMAL)
                if animals:
                    self.stdout.write(self.style.SUCCESS('{0} animals found for {1}'.format(animals.count(), customer)))
                    for animal in animals:
                        for violation in IOA_VIOLATION_TYPES:
                            dv = DeviceViolation()
                            dv.threshold_number = IOA_VIOLATION_THRESHOLD.get(violation)
                            dv.enabled = True
                            dv.customer = customer
                            dv.modified_by_id = 1
                            dv.device = animal
                            dv.status_id = 1
                            dv.module_id = ModuleEnum.IOA
                            dv.violation_type_id = eval("IOAOPTIONSEnum.ALERT_TYPE_{0}".format(violation.upper()))
                            dv.save()
                    self.stdout.write(self.style.SUCCESS('Successful.'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(str(e) + 'Failed.'))
            raise CommandError('Failed to Setup IOA DeviceViolations')
