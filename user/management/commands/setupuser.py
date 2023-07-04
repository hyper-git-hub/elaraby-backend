from django.core.management.base import BaseCommand
from django.db import IntegrityError

from hypernet.enums import OptionsEnum
from user.models import User
from options.models import Options



class Command(BaseCommand):
    """"
        Command python manage.py setuproles
    """
    def add_arguments(self, parser):
        parser.add_argument('email', nargs='+', type=str)
        parser.add_argument('password', nargs='+', type=str)
        parser.add_argument('customer', nargs='+', type=int)
        parser.add_argument('role', nargs='+', type=int)
        parser.add_argument('modified_by', nargs='+', type=int)
        
    def handle(self, *args, **options):
        try:
            email = options['email'][0]
            password = options['password'][0]
            customer = options['customer'][0]
            role = options['role'][0]
            modified_by = options['modified_by'][0]
            
            u = User()
            u.email = email
            u.set_password(password)
            u.status_id = OptionsEnum.ACTIVE
            u.customer_id = customer
            u.is_staff = False
            u.modified_by_id = modified_by
            u.role_id = role
            u.save()
            
            self.stdout.write(self.style.SUCCESS('Successful.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(str(e) + 'Failed.'))
