from __future__ import unicode_literals

import traceback

from django.db.models import Avg, Sum, Max, Min, DateTimeField, DateField, F
from django.db.models.functions import Trunc, TruncDate
from dateutil.parser import parse
from datetime import timezone
import datetime as date_time
from hypernet.models import HypernetPostData, HypernetNotification, Assignment, HypernetPreData
from iof.models import ActivityData, LogisticMaintenance, TruckTrips, Activity, IofShifts, LogisticMaintenanceData, \
    CMSVehicleReporting
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
        final_result[label_index]['series'].append({"name": variable, "value": float(obj['variable']) if obj['variable'] else None})
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
        if obj.get('variable'):
            val = dict()
            val['name'] = obj['date'].strftime('%Y')
            val['series'] = []
            val['series'].append({"name": AggregationEnum.labels[aggregation]+' '+variable.title(), "value":float(obj['variable']) if obj['variable'] else None})
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
        if obj.get('variable'):
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
        if obj.get('variable'):
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
        if obj.get('variable'):
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
        if obj.get('variable'):
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
        if obj.get('variable'):
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
    # elif source == DrillTableEnum.HypernetMaintenance:
    #     return create_queryset_maintenance_data(c_id, g_id, e_id, t_id, start_datetime, end_datetime)


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


def create_queryset_pre_data(c_id, g_id, e_id, t_id, start_datetime, end_datetime):
    result = None
    if g_id:
        result = HypernetPreData.objects.filter(device__assignment_child__parent_id=g_id, customer_id=c_id)
    elif e_id:
        result = HypernetPreData.objects.filter(device_id=e_id, customer_id=c_id)
    elif t_id:
        result = HypernetPreData.objects.filter(customer_id=c_id, type_id=t_id)

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


def create_queryset_maintenance_data(c_id, m_id, t_id, d_id, type_id, start_datetime, end_datetime):
    result = None
    if m_id:
        result = LogisticMaintenanceData.objects.filter(maintenance_id=m_id, customer_id=c_id)
    elif t_id:
        result = LogisticMaintenanceData.objects.filter(truck_id=t_id, customer_id=c_id)
    elif d_id:
        result = LogisticMaintenanceData.objects.filter(driver_id=d_id, customer_id=c_id)
    elif type_id:
        result = LogisticMaintenanceData.objects.filter(cost_type_id=type_id, customer_id=c_id)
    else:
        result = LogisticMaintenanceData.objects.filter(customer_id=c_id)
    if start_datetime and end_datetime:
        result = result.filter(timestamp__range=[start_datetime, end_datetime])
    return result.order_by('-timestamp')


def create_queryset_maintenance(c_id, m_id, t_id, d_id, type_id, start_datetime, end_datetime):
    result = None
    # if g_id:
    #     result = LogisticMaintenance.objects.filter(truck__assignment_child__parent_id=g_id, customer_id=c_id)
    if m_id:
        result = LogisticMaintenance.objects.filter(id=m_id, customer_id=c_id)
    elif t_id:
        result = LogisticMaintenance.objects.filter(truck_id=t_id, customer_id=c_id)
    elif d_id:
        result = LogisticMaintenance.objects.filter(driver_id=d_id, customer_id=c_id)
    elif type_id:
        result = LogisticMaintenance.objects.filter(customer_id=c_id, maintenance_type_id=type_id)
    else:
        result = LogisticMaintenance.objects.filter(customer_id=c_id)
    if start_datetime and end_datetime:
        result = result.filter(issued_datetime__range=[start_datetime, end_datetime])
    return result.order_by('-issued_datetime')


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
        traceback.print_exc()


def get_assigned_drivers_datetime(t_id, start_datetime, end_datetime):
    try:
        if t_id:
            driver = None
            start_datetime = parse(start_datetime).replace(tzinfo=timezone.utc)

            shifts = IofShifts.objects.filter(parent_id=t_id)
                                              # shift_start_time__year=start_datetime.year,
                                              # shift_start_time__month=start_datetime.month,
                                              # shift_start_time__day=start_datetime.day)
            for shift in shifts:
                if shift.shift_end_time:
                    if shift.shift_start_time <= start_datetime <= shift.shift_end_time:
                        driver = shift.child.as_entity_json()
                        return driver
                else:
                    if shift.shift_start_time <= start_datetime:
                        driver = shift.child.as_entity_json()
            return driver
            # driver_ass_truck = Assignment.objects.filter(parent_id=t_id,
            #                                              child__type=DeviceTypeEntityEnum.DRIVER,
            #                                              status_id=OptionsEnum.ACTIVE,
            #                                              created_datetime__lte=start_datetime,
            #                                              )
            # result = driver_ass_truck.first()
            # return result
        return None
    except Exception as e:
        traceback.print_exc()


def get_jobs_of_trucks_datetime(t_id, start_datetime):
    try:
        if t_id:
            start = parse(start_datetime).replace(tzinfo=timezone.utc)

            jobs = Activity.objects.filter(primary_entity_id=t_id,
                                           start_datetime__year=start.year,
                                           start_datetime__month=start.month,
                                           start_datetime__day=start.day).order_by('start_datetime')
            for j in jobs:
                if j.end_datetime:
                    if j.start_datetime <= start <= j.end_datetime:
                        return j
                else:
                    if j.start_datetime <= start:
                        return j
            return None
    except Exception as e:
        traceback.print_exc()


def create_queryset_cms_truck_data(c_id, truck_id, d_location, s_location, wheels,office, supervisor_id, start_datetime, end_datetime):
    result = None
    try:
        kwargs = dict()
        kwargs['customer_id'] = c_id
        if truck_id:
            kwargs['vehicle_id'] = truck_id
        if wheels:
            kwargs['vehicle__wheels'] = wheels
        if d_location:
            kwargs['destination_id'] = d_location
        if s_location:
            kwargs['loading_location_id'] = s_location
        if office:
            kwargs['office'] = office
        if supervisor_id:
            kwargs['supervisor_id'] = supervisor_id
        result = CMSVehicleReporting.objects.filter(**kwargs)

        if start_datetime and end_datetime:
            result = result.filter(timestamp__range=[start_datetime, end_datetime])
    except:
        traceback.print_exc()
    return result


def calculate_stops(queryset):
    data = []
    last_lat = None
    last_lng = None
    start_time = None
    end_time = None

    for obj in queryset:
        if last_lng is None and last_lng is None:
            # Set the variables for the first iteration
            last_lat = obj['latitude']
            last_lng = obj['longitude']
            start_time = obj['timestamp']

        elif obj['latitude'] == last_lat and obj['longitude'] == last_lng:
            # check to see if next iteration matches last one
            # if they dont then update end time so we have an existing start time and now an updated end time
            end_time = obj['timestamp']
        else:
            # if they dont match then check if we have start and end time both initialized
            if start_time and end_time:
                # if they both have values meaning we need to calculate duration and create an object for the list
                stop = dict()
                stop['duration'] = (end_time - start_time).total_seconds()/60
                stop['start_time'] = str(start_time)
                stop['end_time'] = str(end_time)
                stop['latitude'] = last_lat
                stop['longitude'] = last_lng
                data.append(stop)
                last_lat = obj['latitude']
                last_lng = obj['longitude']
                start_time = obj['timestamp']
                end_time = None
    if start_time and end_time:
        stop = dict()
        stop['duration'] = (end_time - start_time).total_seconds() / 60
        stop['start_time'] = str(start_time)
        stop['end_time'] = str(end_time)
        stop['latitude'] = last_lat
        stop['longitude'] = last_lng
        data.append(stop)
    return data

