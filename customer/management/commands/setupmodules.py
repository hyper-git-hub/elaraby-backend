from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError
from hypernet.models import Module
from hypernet.enums import ModuleEnum


url_dict = {
1:'/iof/dashboard',
2:'/ioa/dashboard',
3:'/ppp/dashboard'
}


class Command(BaseCommand):
    """"
        Command python manage.py setupdevicetypes
    """

    def handle(self, *args, **options):
        
        
        try:
            for choice in ModuleEnum.choices():
                name = str(choice[1]).title()
                try:
                    Module.objects.create(id=choice[0], name=name, url=url_dict[choice[0]])
                except IntegrityError as e:
                    pass
            self.stdout.write(self.style.SUCCESS('Successful.'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(str(e) + 'Failed.'))
            raise CommandError('Failed to Setup Modules')
