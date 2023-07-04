from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError

from user.enums import RoleTypeEnum
from user.models import Role
from options.models import Options


class Command(BaseCommand):
    """"
        Command python manage.py setuproles
    """

    def handle(self, *args, **options):
        try:
            for choice in RoleTypeEnum.choices():
                name = str(choice[1]).title()
                id = choice[0]
                # print(id)
                try:
                    Role.objects.create(pk=id, name=name, status=Options.objects.get(value='Active', key='recordstatus'))
                except IntegrityError as e:
                    pass
            self.stdout.write(self.style.SUCCESS('Successful.'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(str(e) + 'Failed.'))
            raise CommandError('Failed to Setup Role Types')
