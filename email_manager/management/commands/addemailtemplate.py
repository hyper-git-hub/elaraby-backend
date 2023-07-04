import traceback
from django.core.management.base import BaseCommand, CommandError

from email_manager.email_util import create_default_email_template


class Command(BaseCommand):
    """"
        Command python manage.py setupcustomer <name>
    """
    def handle(self, *args, **options):
        try:
            create_default_email_template()
            self.stdout.write(self.style.SUCCESS('template added succesfully.'))
        except Exception as e:
            traceback.print_exc()
            self.stdout.write(self.style.WARNING(str(e) + 'Failed.'))
            raise CommandError('Failed to create email template.')

