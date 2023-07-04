import traceback

from django.core.management.base import BaseCommand, CommandError
from customer.utils import create_customer_clients_csv, fixingdata_customer_clients_csv, modifying_zenath_data, \
    modified_fixingdata_customer_clients_csv
import argparse



class Command(BaseCommand):
    """"
        Command python manage.py setupcustomer <name>
    """

    def add_arguments(self, parser):
        parser.add_argument('file',nargs='+', type=str)
        parser.add_argument('customer',nargs='+', type=str)


    def handle(self, *args, **options):
        try:
            print(options)
            file = options['file'][0]
            customer = options['customer'][0]

            #TODO un-comment the util to execute the data insertion.
            """Fresh Data insertion Function"""
            create_customer_clients_csv(customer=int(customer), file=file)
            # modifying_zenath_data(customer=int(customer), file=file)
            # self.stdout.write(self.style.WARNING('operation not allowed, see load_excel_data.py'))
        except Exception as e:
            traceback.print_exc()
            self.stdout.write(self.style.WARNING(str(e) + 'Failed.'))
            raise CommandError('Failed to Load Data.')

