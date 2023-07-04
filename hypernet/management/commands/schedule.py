from django.core.management.base import BaseCommand, CommandError
from django.db.models import Max

from ioa.utils import time_diff_seconds
from ioa.models import Scheduling, ActivityList
from datetime import datetime
from datetime import timedelta
from hypernet.constants import DAILY,WEEKLY,INCOMPLETE,ACTIVITY_ACTION_STATUS
from hypernet.models import Options


class Command(BaseCommand):
    """"
        Command python manage.py setupdevicetypes
    """

    def handle(self, *args, **options):
        try:

            schedule_list = Scheduling.objects.all()
            try:
                group = ActivityList.objects.all().aggregate(Max('group'))
                group_id = int(group.get('group__max'))
            except Exception as e:
                group_id = 0
            for schedule_obj in schedule_list:
                if datetime.now().date() >= schedule_obj.scheduled_next_date and datetime.now().date() <= schedule_obj.scheduled_end_date:
                    if datetime.now().time() >= schedule_obj.scheduled_start_time and datetime.now().time() <= schedule_obj.scheduled_end_time:
                        if time_diff_seconds(datetime.now().time(),schedule_obj.scheduled_start_time) < 600:
                            group_id += 1
                            print(group_id)
                            for cow in schedule_obj.animal.all():
                                activity_list = ActivityList()
                                activity_list.animal = cow
                                activity_list.scheduled_start_time = datetime.combine(schedule_obj.scheduled_next_date,schedule_obj.scheduled_start_time)
                                activity_list.scheduled_end_time = datetime.combine(schedule_obj.scheduled_next_date,schedule_obj.scheduled_end_time)
                                activity_list.group = group_id
                                activity_list.perform_individually = schedule_obj.perform_individually
                                activity_list.action_status = 1006
                                activity_list.activity_type = schedule_obj.activity_type
                                activity_list.scheduling_comments = schedule_obj.comments
                                activity_list.customer = schedule_obj.customer
                                activity_list.activity_priority = schedule_obj.activity_priority
                                activity_list.save()
                                print(str(schedule_obj.activity_type.value+' activity created for '+cow.name))


                            if schedule_obj.routine_type.__dict__['value'] == DAILY:
                                schedule_obj.scheduled_next_date += timedelta(days=1)

                            elif schedule_obj.routine_type.__dict__['value'] == WEEKLY:
                                schedule_obj.scheduled_next_date += timedelta(days=7)
                            schedule_obj.save()
                else:
                    if schedule_obj.scheduled_end_date < datetime.now().date():
                        schedule_obj.is_active = False
                        schedule_obj.save()
                    else:
                        schedule_obj.is_active = True
                        schedule_obj.save()


            self.stdout.write(self.style.SUCCESS('Successful.'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(str(e) + 'Failed.'))
            raise CommandError('Failed to Create Scheduling Data')
