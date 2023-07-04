from django.core.management.base import BaseCommand, CommandError
from django.db.models import Sum

from hypernet.models import Assignment
from ioa.crons.scheduler import *
from hypernet.constants import ACTIVITY_TYPE,MILKING,FEEDING
import datetime
from datetime import timedelta


class Command(BaseCommand):
    """"
        Command python manage.py setupdevicetypes
    """

    def handle(self, *args, **options):
        try:
            time_range = datetime.date.today() - timedelta(days=100)
            time_range_mins = datetime.date.today() - timedelta(minutes=1)
            time_range_mins = time_range_mins - timedelta(hours=5)
            milking_activities = ActivityList.objects.filter(performed_end_time__gte=time_range,
                                                             activity_type__key=ACTIVITY_TYPE,
                                                             activity_type__value=MILKING)
            if milking_activities.count() > 0:
                animals = milking_activities.values('animal', 'customer').annotate(
                    total=Sum('individual_value')).order_by('animal')
                for obj in animals:
                    assignment = Assignment.objects.filter(child_id=obj['animal'])
                    for o in assignment:
                        aggregation = Aggregation()
                        aggregation.animal_id = obj['animal']
                        aggregation.avg_milk_yield = obj['total']
                        aggregation.customer_aggregations_id = obj['customer']
                        aggregation.herd_id = o.parent_id
                        aggregation.save()
                herds = Aggregation.objects.filter(
                    created_datetime__gte=time_range_mins).values(
                    'herd', 'customer_aggregations').annotate(total=Sum('avg_milk_yield')).order_by('herd')
                for obj in herds:
                    aggregation = Aggregation()
                    aggregation.herd_id = obj['herd']
                    aggregation.customer_aggregations_id = obj['customer_aggregations']
                    aggregation.avg_milk_yield = obj['total']
                    aggregation.save()
                customers = Aggregation.objects.filter(created_datetime__gte=time_range_mins, animal_id=None)\
                    .values('customer_aggregations')\
                    .annotate(total=Sum('avg_milk_yield')).order_by('customer_aggregations')
                for obj in customers:
                    aggregation = Aggregation()
                    aggregation.customer_aggregations_id = obj['customer_aggregations']
                    aggregation.avg_milk_yield = obj['total']
                    aggregation.save()

            feeding_activities = ActivityList.objects.filter(performed_end_time__gte=time_range,
                                                             activity_type__key=ACTIVITY_TYPE,
                                                             activity_type__value=FEEDING).distinct('group')
            data_dict = {}
            for obj in feeding_activities:
                if obj.animal.get_parent.id not in data_dict.keys():
                    data_dict[obj.animal.get_parent.id] = obj.group_value
                else:
                    data_dict[obj.animal.get_parent.id] += obj.group_value
            if feeding_activities.count() > 0:
                for feeding_activity in feeding_activities:
                    aggregation = Aggregation()
                    aggregation.feeding_value = data_dict.get(feeding_activity.animal.get_parent.id)
                    aggregation.customer_aggregations_id = feeding_activity.customer_id
                    aggregation.herd_id = feeding_activity.animal.get_parent.id
                    aggregations = Aggregation.objects.filter(created_datetime__gte=time_range_mins,
                                                              herd_id=feeding_activity.animal.get_parent.id,
                                                              feeding_value=data_dict.get(
                                                              feeding_activity.animal.get_parent.id))
                    if aggregations.count() == 0:
                        aggregation.save()
                customers = Aggregation.objects.filter(created_datetime__gte=time_range_mins,
                                                       animal_id=None,avg_milk_yield=None) \
                                                .values('customer_aggregations') \
                                                .annotate(total=Sum('feeding_value'))
                for obj in customers:
                    aggregation = Aggregation()
                    aggregation.customer_aggregations_id = obj['customer_aggregations']
                    aggregation.feeding_value = obj['total']
                    aggregation.save()



            self.stdout.write(self.style.SUCCESS('Successful.'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(str(e) + 'Failed.'))
            raise CommandError('Failed to Create aggregations')
