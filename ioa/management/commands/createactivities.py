from random import randint
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Max
from ioa.models import Scheduling, ActivityList
from datetime import datetime
from datetime import timedelta
from hypernet.constants import DAILY,WEEKLY
from hypernet.enums import IOAOPTIONSEnum
from ioa.utils import get_random_group_value,get_random_individual_value


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
                    group_id += 1
                    group_value = get_random_group_value()
                    print(group_id)
                    for cow in schedule_obj.animal.all():
                        schedule_time_start = datetime.combine(schedule_obj.scheduled_next_date,schedule_obj.scheduled_start_time)
                        schedule_time_end = datetime.combine(schedule_obj.scheduled_next_date,schedule_obj.scheduled_end_time)
                        activity_list = ActivityList()
                        activity_list.animal = cow
                        activity_list.scheduled_start_time = schedule_time_start
                        activity_list.scheduled_end_time = schedule_time_end
                        activity_list.group = group_id
                        activity_list.perform_individually = schedule_obj.perform_individually
                        activity_list.action_status_id = randint(1005, 1007)
                        activity_list.activity_type = schedule_obj.activity_type
                        activity_list.scheduling_comments = schedule_obj.comments
                        activity_list.customer = schedule_obj.customer
                        activity_list.activity_priority = schedule_obj.activity_priority
                        activity_list.performed_start_time = schedule_time_start + timedelta(minutes=30)
                        activity_list.performed_end_time = schedule_time_start + timedelta(hours=1)
                        activity_list.performed_comments = 'performed succesfully'
                        activity_list.assigned_to_activity_id = schedule_obj.assigned_to_id
                        if schedule_obj.perform_individually:
                            activity_list.individual_value = get_random_individual_value()
                        else:
                            activity_list.group_value = group_value
                        activity_list.is_on_time = True
                        activity_list.save()
                        # print(str(schedule_obj.activity_type.value+' activity created for '+cow.name))


                    if schedule_obj.routine_type.__dict__['value'] == DAILY:
                        schedule_obj.scheduled_next_date += timedelta(days=1)

                    elif schedule_obj.routine_type.__dict__['value'] == WEEKLY:
                        schedule_obj.scheduled_next_date += timedelta(days=7)
                    schedule_obj.save()



            self.stdout.write(self.style.SUCCESS('Successful.'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(str(e) + 'Failed.'))
            raise CommandError('Failed to Create Activity Data')
