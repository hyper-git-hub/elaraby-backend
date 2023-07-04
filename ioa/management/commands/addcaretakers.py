from datetime import timedelta
from random import randint

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from customer.models import Customer
from options.models import Options
from user.models import User, Role
from user.enums import RoleTypeEnum
import string
import random

VOWELS = "aeiou"
CONSONANTS = "".join(set(string.ascii_lowercase) - set(VOWELS))


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

    def handle(self, *args, **options):
        try:
            if User.objects.count() <= 30:
                for customer in Customer.objects.all():
                    for i in range(1, 5):
                        user = User()
                        user.email = 'caretaker_' + str(generate_word(5)) + '@metis.com'
                        user.first_name = generate_word(6)
                        user.last_name = generate_word(5)
                        user.is_staff = True
                        user.customer = customer
                        user.status = Options.objects.get(value='Active', key='recordstatus')
                        user.password = make_password('12345678')
                        user.role_id = randint(4, 5)
                        user.preferred_module = 2.0
                        user.modified_by = User.objects.get(is_superuser=True)
                        user.save()
            self.stdout.write(self.style.SUCCESS('Successful.'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(str(e) + ' ' + 'Failed.'))
            raise CommandError('Failed to Add Caretakers')
