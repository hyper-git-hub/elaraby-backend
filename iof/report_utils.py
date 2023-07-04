from __future__ import unicode_literals
from django.db.models import Avg, Sum, Max, Min, DateTimeField, DateField, F
from django.db.models.functions import Trunc, TruncDate
from dateutil.parser import parse
from datetime import timezone
import datetime as date_time
from hypernet.models import HypernetPostData, HypernetNotification, Assignment
from iof.models import ActivityData, LogisticMaintenance, TruckTrips, Activity
from hypernet.utils import *
from hypernet.enums import AggregationEnum, DrillTableEnum, OptionsEnum, DeviceTypeAssignmentEnum, DeviceTypeEntityEnum


def find(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return i
    return -1


def add_variable(final_result, val, variable, obj, data):
    label_index = find(final_result, 'name', val['name'])
    if label_index >= 0:
        final_result[label_index]['series'].append({"name": variable, "value": float(obj['variable'])})
    else:
        data.append(val)


def set_aggregation_year(aggregation, queryset, variable, tzinfo):
    if aggregation == AggregationEnum.SUM:
        return queryset.annotate(date=Trunc('timestamp', 'year', output_field=DateTimeField(), tzinfo=tzinfo)).values(
            'date').annotate(
            variable=Sum(variable)).order_by('date')
    elif aggregation == AggregationEnum.AVG:
        return queryset.annotate(date=Trunc('timestamp', 'year', output_field=DateTimeField(), tzinfo=tzinfo)).values(
            'date').annotate(
            variable=Avg(variable)).order_by('date')
    elif aggregation == AggregationEnum.MIN:
        return queryset.annotate(date=Trunc('timestamp', 'year', output_field=DateTimeField(), tzinfo=tzinfo)).values(
            'date').annotate(
            variable=Min(variable)).order_by('date')
    elif aggregation == AggregationEnum.MAX:
        return queryset.annotate(date=Trunc('timestamp', 'year', output_field=DateTimeField(), tzinfo=tzinfo)).values(
            'date').annotate(
            variable=Max(variable)).order_by('date')


def set_aggregation_month(aggregation, queryset, variable, time, tzinfo):
    if aggregation == AggregationEnum.SUM:
        return queryset.filter(timestamp__year=time.year).annotate(
            date=Trunc('timestamp', 'month', output_field=DateField(), tzinfo=tzinfo)).values('date').annotate(
          variable=Sum(variable)).order_by('date')
    elif aggregation == AggregationEnum.AVG:
        return queryset.filter(timestamp__year=time.year).annotate(
            date=Trunc('timestamp', 'month', output_field=DateField(), tzinfo=tzinfo)).values('date').annotate(
          variable=Avg(variable)).order_by('date')
    elif aggregation == AggregationEnum.MIN:
        return queryset.filter(timestamp__year=time.year).annotate(
            date=Trunc('timestamp', 'month', output_field=DateField(), tzinfo=tzinfo)).values('date').annotate(
          variable=Min(variable)).order_by('date')
    elif aggregation == AggregationEnum.MAX:
        return queryset.filter(timestamp__year=time.year).annotate(
            date=Trunc('timestamp', 'month', output_field=DateField(), tzinfo=tzinfo)).values('date').annotate(
          variable=Max(variable)).order_by('date')


def set_aggregation_day(aggregation, queryset, variable, time, tzinfo):
    if aggregation == AggregationEnum.SUM:
        return queryset.filter(timestamp__month=time.month, timestamp__year=time.year).annotate(
        date=Trunc('timestamp', 'day', output_field=DateTimeField(), tzinfo=tzinfo)).values('date').annotate(
          variable=Sum(variable)).order_by('date')
    elif aggregation == AggregationEnum.AVG:
        return queryset.filter(timestamp__month=time.month, timestamp__year=time.year).annotate(
        date=Trunc('timestamp', 'day', output_field=DateTimeField(), tzinfo=tzinfo)).values('date').annotate(
          variable=Avg(variable)).order_by('date')
    elif aggregation == AggregationEnum.MIN:
        return queryset.filter(timestamp__month=time.month, timestamp__year=time.year).annotate(
        date=Trunc('timestamp', 'day', output_field=DateTimeField(), tzinfo=tzinfo)).values('date').annotate(
          variable=Min(variable)).order_by('date')
    elif aggregation == AggregationEnum.MAX:
        return queryset.filter(timestamp__month=time.month, timestamp__year=time.year).annotate(
        date=Trunc('timestamp', 'day', output_field=DateTimeField(), tzinfo=tzinfo)).values('date').annotate(
          variable=Max(variable)).order_by('date')


def set_aggregation_hour(aggregation, queryset, variable, start_time, end_time, tzinfo):
    if aggregation == AggregationEnum.SUM:
        return queryset.filter(timestamp__range=[start_time, end_time]).annotate(
        date=Trunc('timestamp', 'hour', output_field=DateTimeField(), tzinfo=tzinfo)).values('date').annotate(
          variable=Sum(variable)).order_by('date')
    elif aggregation == AggregationEnum.AVG:
        return queryset.filter(timestamp__range=[start_time, end_time]).annotate(
        date=Trunc('timestamp', 'hour', output_field=DateTimeField(), tzinfo=tzinfo)).values('date').annotate(
          variable=Avg(variable)).order_by('date')
    elif aggregation ==AggregationEnum.MIN:
        return queryset.filter(timestamp__range=[start_time, end_time]).annotate(
        date=Trunc('timestamp', 'hour', output_field=DateTimeField(), tzinfo=tzinfo)).values('date').annotate(
          variable=Min(variable)).order_by('date')
    elif aggregation == AggregationEnum.MAX:
        return queryset.filter(timestamp__range=[start_time, end_time]).annotate(
        date=Trunc('timestamp', 'hour', output_field=DateTimeField(), tzinfo=tzinfo)).values('date').annotate(
          variable=Max(variable)).order_by('date')


def set_aggregation_minute(aggregation, queryset, variable, time, tzinfo):
    if aggregation == AggregationEnum.SUM:
        return queryset.filter(timestamp__hour=time.hour, timestamp__day=time.day, timestamp__month=time.month, timestamp__year=time.year).annotate(
        date=Trunc('timestamp', 'minute', output_field=DateTimeField(), tzinfo=tzinfo)).values('date').annotate(
          variable=Sum(variable)).extra(select={'my_minute': 'EXTRACT(MINUTE FROM timestamp)'}, order_by=['my_minute'])
    elif aggregation == AggregationEnum.AVG:
        return queryset.filter(timestamp__hour=time.hour,timestamp__day=time.day, timestamp__month=time.month, timestamp__year=time.year).annotate(
        date=Trunc('timestamp', 'minute', output_field=DateTimeField(), tzinfo=tzinfo)).values('date').annotate(
          variable=Avg(variable)).extra(select={'my_minute': 'EXTRACT(MINUTE FROM timestamp)'}, order_by=['my_minute'])
    elif aggregation == AggregationEnum.MIN:
        return queryset.filter(timestamp__hour=time.hour,timestamp__day=time.day, timestamp__month=time.month, timestamp__year=time.year).annotate(
        date=Trunc('timestamp', 'minute', output_field=DateTimeField(), tzinfo=tzinfo)).values('date').annotate(
          variable=Min(variable)).extra(select={'my_minute': 'EXTRACT(MINUTE FROM timestamp)'}, order_by=['my_minute'])
    elif aggregation == AggregationEnum.MAX:
        return queryset.filter(timestamp__hour=time.hour,timestamp__day=time.day, timestamp__month=time.month, timestamp__year=time.year).annotate(
        date=Trunc('timestamp', 'minute', output_field=DateTimeField(), tzinfo=tzinfo)).values('date').annotate(
          variable=Max(variable)).extra(select={'my_minute': 'EXTRACT(MINUTE FROM timestamp)'}, order_by=['my_minute'])


def set_aggregation_second(aggregation, queryset, variable, time, tzinfo):
    if aggregation == AggregationEnum.SUM:
        return queryset.filter(timestamp__minute=time.minute, timestamp__hour=time.hour, timestamp__day=time.day, timestamp__month=time.month, timestamp__year=time.year).annotate(
        date=Trunc('timestamp', 'second', output_field=DateTimeField(), tzinfo=tzinfo)).values('date').annotate(
          variable=Sum(variable)).extra(select={'my_second': 'EXTRACT(SECOND FROM timestamp)'}, order_by=['my_second'])
    elif aggregation == AggregationEnum.AVG:
        return queryset.filter(timestamp__minute=time.minute, timestamp__hour=time.hour,timestamp__day=time.day, timestamp__month=time.month, timestamp__year=time.year).annotate(
        date=Trunc('timestamp', 'second', output_field=DateTimeField(), tzinfo=tzinfo)).values('date').annotate(
          variable=Avg(variable)).extra(select={'my_second': 'EXTRACT(SECOND FROM timestamp)'}, order_by=['my_second'])
    elif aggregation == AggregationEnum.MIN:
        return queryset.filter(timestamp__minute=time.minute, timestamp__hour=time.hour,timestamp__day=time.day, timestamp__month=time.month, timestamp__year=time.year).annotate(
        date=Trunc('timestamp', 'second', output_field=DateTimeField(), tzinfo=tzinfo)).values('date').annotate(
          variable=Min(variable)).extra(select={'my_second': 'EXTRACT(SECOND FROM timestamp)'}, order_by=['my_second'])
    elif aggregation == AggregationEnum.MAX:
        return queryset.filter(timestamp__minute=time.minute, timestamp__hour=time.hour,timestamp__day=time.day, timestamp__month=time.month, timestamp__year=time.year).annotate(
        date=Trunc('timestamp', 'second', output_field=DateTimeField(), tzinfo=tzinfo)).values('date').annotate(
          variable=Max(variable)).extra(select={'my_second': 'EXTRACT(SECOND FROM timestamp)'}, order_by=['my_second'])


def compute_data_year(variable, aggregation, queryset, final_result, tzinfo):
    data = []
    queryset = set_aggregation_year(aggregation, queryset, variable, tzinfo)
    for obj in queryset:
        val = dict()
        val['name'] = obj['date'].strftime('%Y')
        val['series'] = []
        val['series'].append({"name": AggregationEnum.labels[aggregation]+' '+variable.title(), "value":float(obj['variable'])})
        if final_result:
            add_variable(final_result, val, AggregationEnum.labels[aggregation]+' '+variable.title(), obj, data)
        else:
            data.append(val)
    if final_result:
        return final_result
    else:
        return data
    

def compute_data_month(variable, aggregation, queryset, final_result, time, tzinfo):
    data = []
    time = parse(time, None)
    queryset = set_aggregation_month(aggregation, queryset, variable, time, tzinfo)
    for obj in queryset:
        val = dict()
        # val['name'] = obj['date'].strftime('%b-%Y')
        val['name'] = obj['date'].strftime('%b')
        val['series'] = []
        val['series'].append({"name": AggregationEnum.labels[aggregation]+' '+variable.title(), "value": float(obj['variable'])})
        if final_result:
            add_variable(final_result, val, AggregationEnum.labels[aggregation]+' '+variable.title(), obj, data)
        else:
            data.append(val)
    if final_result:
        return final_result
    else:
        return data
    return data


def compute_data_day(variable, aggregation, queryset, final_result, time, tzinfo):
    data = []
    time = parse(time, None)
    queryset = set_aggregation_day(aggregation, queryset, variable, time, tzinfo)
    for obj in queryset:
        val = dict()
        val['name'] = obj['date'].strftime('%d')
        # val['name'] = obj['date'].strftime('%d-%b-%Y')
        val['series'] = []
        val['series'].append({"name": AggregationEnum.labels[aggregation]+' '+variable.title(), "value": float(obj['variable'])})
        if final_result:
            add_variable(final_result, val, AggregationEnum.labels[aggregation]+' '+variable.title(), obj, data)
        else:
            data.append(val)
    if final_result:
        return final_result
    else:
        return data
    return data


def compute_data_hour(variable, aggregation, queryset, final_result, time, tzinfo):
    data = []
    time = parse(time, None)
    time = tzinfo.localize(time)
    time = time.astimezone(timezone.utc)
    time2 = time + date_time.timedelta(days=1)
    queryset = set_aggregation_hour(aggregation, queryset, variable, time, time2, tzinfo)
    for obj in queryset:
        val = dict()
        val['name'] = obj['date'].strftime('%H:00:00')
        val['series'] = []
        val['series'].append({"name": AggregationEnum.labels[aggregation]+' '+variable.title(), "value": float(obj['variable'])})
        if final_result:
            add_variable(final_result, val, AggregationEnum.labels[aggregation]+' '+variable.title(), obj, data)
        else:
            data.append(val)
    if final_result:
        return final_result
    else:
        return data
    return data


def compute_data_minute(variable, aggregation, queryset, final_result, time, tzinfo):
    data = []
    
    time = parse(time, None)
    time = tzinfo.localize(time)
    time = time.astimezone(timezone.utc)
    queryset = set_aggregation_minute(aggregation, queryset, variable, time, timezone.utc)
    for obj in queryset:
        val = dict()
        val['name'] = obj['date'].astimezone(tz=tzinfo).strftime('%H:%M:00')
        val['series'] = []
        val['series'].append({"name": AggregationEnum.labels[aggregation]+' '+variable.title(), "value": float(obj['variable'])})
        if final_result:
            add_variable(final_result, val, AggregationEnum.labels[aggregation]+' '+variable.title(), obj, data)
        else:
            data.append(val)
    if final_result:
        return final_result
    else:
        return data
    return data


def compute_data_second(variable, aggregation, queryset, final_result, time, tzinfo):
    data = []
    time = parse(time, None)
    time = tzinfo.localize(time)
    time = time.astimezone(timezone.utc)
    queryset = set_aggregation_second(aggregation, queryset, variable, time, timezone.utc)
    for obj in queryset:
        val = dict()
        val['name'] = obj['date'].astimezone(tz=tzinfo).strftime('%H:%M:%S')
        val['series'] = []
        val['series'].append({"name": AggregationEnum.labels[aggregation]+' '+variable.title(), "value": float(obj['variable'])})
        if final_result:
            add_variable(final_result, val, AggregationEnum.labels[aggregation]+' '+variable.title(), obj, data)
        else:
            data.append(val)
    if final_result:
        return final_result
    else:
        return data
    return data


def create_queryset_drill_report(source , c_id, g_id, e_id, t_id, start_datetime, end_datetime):
    if source == DrillTableEnum.HypernetPostData:
        return create_queryset_post_data(c_id, g_id, e_id, t_id, start_datetime, end_datetime)
    elif source == DrillTableEnum.LogisticJobs:
        return create_queryset_logistic_jobs(c_id, g_id, e_id, t_id, start_datetime, end_datetime)
    elif source == DrillTableEnum.LogisticTrips:
        return create_queryset_logistic_trips(c_id, g_id, e_id, t_id, start_datetime, end_datetime)
    elif source == DrillTableEnum.HypernetNotification:
        return create_queryset_notification_data(c_id, g_id, e_id, t_id, start_datetime, end_datetime)
    elif source == DrillTableEnum.HypernetMaintenance:
        return create_queryset_maintenance_data(c_id, g_id, e_id, t_id, start_datetime, end_datetime)


def create_queryset_post_data(c_id, g_id, e_id, t_id, start_datetime, end_datetime):
    result = None
    if g_id:
        result = HypernetPostData.objects.filter(device__assignment_child__parent_id=g_id, customer_id=c_id)
    elif e_id:
        result = HypernetPostData.objects.filter(device_id=e_id, customer_id=c_id)
    elif t_id:
        result = HypernetPostData.objects.filter(customer_id=c_id, type_id=t_id)
    
    if start_datetime and end_datetime:
        result = result.filter(timestamp__range=[start_datetime, end_datetime])
    elif start_datetime:
        start_datetime = parse(start_datetime)
        result = result.filter(timestamp__year=start_datetime.year,
                               timestamp__month=start_datetime.month,
                               timestamp__day=start_datetime.day,
                               timestamp__hour=start_datetime.hour
                               , timestamp__minute=start_datetime.minute)
    return result


def create_queryset_notification_data(c_id, g_id, e_id, t_id, start_datetime, end_datetime):
    result = None
    if g_id:
        result = HypernetNotification.objects.filter(device__assignment_child__parent_id=g_id, customer_id=c_id)
    elif e_id:
        result = HypernetNotification.objects.filter(device_id=e_id, customer_id=c_id)
    elif t_id:
        result = HypernetNotification.objects.filter(customer_id=c_id, type_id=t_id)
    
    if start_datetime and end_datetime:
        result = result.filter(timestamp__range=[start_datetime, end_datetime])
    return result


def create_queryset_maintenance_data(c_id, g_id, e_id, t_id, start_datetime, end_datetime):
    result = None
    if g_id:
        result = ActivityData.objects.filter(device__assignment_child__parent_id=g_id, customer_id=c_id)
    elif e_id:
        result = ActivityData.objects.filter(device_id=e_id, customer_id=c_id)
    elif t_id:
        result = ActivityData.objects.filter(customer_id=c_id, type_id=t_id)
    
    if start_datetime and end_datetime:
        result = result.filter(timestamp__range=[start_datetime, end_datetime])
    return result


def create_queryset_logistic_jobs(c_id, g_id, e_id, t_id, start_datetime, end_datetime):
    result = None
    if g_id:
        result = ActivityData.objects.filter(primary_entity__assignment_child__parent_id=g_id, customer_id=c_id)
    elif e_id:
        result = ActivityData.objects.filter(primary_entity_id=e_id, customer_id=c_id)
    elif t_id:
        result = ActivityData.objects.filter(customer_id=c_id, type_id=t_id)
    
    if start_datetime and end_datetime:
        result = result.filter(timestamp__range=[start_datetime, end_datetime])
    return result


def create_queryset_logistic_trips(c_id, g_id, e_id, t_id, start_datetime, end_datetime):
    result = None
    if g_id:
        result = TruckTrips.objects.filter(device__assignment_child__parent_id=g_id, customer_id=c_id)
    elif e_id:
        result = TruckTrips.objects.filter(device_id=e_id, customer_id=c_id)
    elif t_id:
        result = TruckTrips.objects.filter(customer_id=c_id, type_id=t_id)
    
    if start_datetime and end_datetime:
        result = result.filter(timestamp__range=[start_datetime, end_datetime])
    return result
# def create_queryset_notification_data():
# def create_queryset_maintenance_data():
# def create_queryset_jobs_data():
# def create_queryset_sensor_data():


def territories_of_truck(t_id, start_datetime):
    try:
        if t_id:
            territory = Assignment.objects.filter(parent_id=t_id, status=OptionsEnum.ACTIVE,
                                                  type_id=DeviceTypeAssignmentEnum.TERRITORY_ASSIGNMENT,
                                                  created_datetime__lte=start_datetime,
                                                  ).order_by('modified_datetime')

            result = territory.values(territory_name=F('child__name'), territory_location=F('child__territory'),
                                      territory_id=F('child_id'))
            return result
        return None

    except Exception as e:
        print(str(e))


def get_assigned_drivers_datetime(t_id, start_datetime, end_datetime):
    try:
        if t_id:
            driver_ass_truck = Assignment.objects.filter(parent_id=t_id,
                                                         child__type=DeviceTypeEntityEnum.DRIVER,
                                                         status_id=OptionsEnum.ACTIVE,
                                                         created_datetime__lte=start_datetime,
                                                         )
            result = driver_ass_truck.first()
            return result
        return None
    except Exception as e:
        print(str(e))


def get_jobs_of_trucks_datetime(t_id, start_datetime, end_datetime):
    try:
        if t_id:
            dateutil_date = parse(start_datetime)
            jobs_of_truck = Activity.objects.filter(primary_entity_id=t_id,
                                                        created_datetime__year=dateutil_date.year,
                                                        created_datetime__month=dateutil_date.month,
                                                        created_datetime__day=dateutil_date.day,
                                                        created_datetime__hour__lte=dateutil_date.hour
                                                        ,created_datetime__minute__lte=dateutil_date.minute
                                                        )
            return jobs_of_truck
        return None
    except Exception as e:
        print(str(e))