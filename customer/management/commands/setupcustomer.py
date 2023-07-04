from django.core.management.base import BaseCommand, CommandError

from customer.models import Customer
from customer.utils import create_customer_prefrences
from hypernet.enums import OptionsEnum
from options.models import Options
from user.models import ModuleAssignment, Module


class Command(BaseCommand):
    """"
        Command python manage.py setupcustomer <name>
    """

    def add_arguments(self, parser):
        parser.add_argument('name', nargs='+', type=str)
        parser.add_argument('module', nargs='+', type=int)

    def handle(self, *args, **options):
        try:
            name = options['name'][0]
            module_name = options['module'][0]
            customer = Customer.objects.create(name=name,
                                               status=Options.objects.get(value='Active', key='recordstatus'),
                                               subscription_is_valid=True)
            if customer.id:
                ModuleAssignment.objects.create(customer=Customer.objects.get(id=customer.id),
                                                module=Module.objects.get(id=module_name))

                create_customer_prefrences(customer)

            self.stdout.write(self.style.SUCCESS('Successful.'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(str(e) + 'Failed.'))
            raise CommandError('Failed to Setup Customer')
