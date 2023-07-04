from __future__ import unicode_literals

import dateutil
from django.db.models import Sum
import itertools
from .models import ActivityData, \
    TruckTrips, \
    LogisticsDerived, \
    LogisticMaintenance, \
    LogisticAggregations, IofShifts

from hypernet.models import HypernetNotification, \
    Entity, \
    HypernetPostData, \
    DeviceCalibration, \
    Assignment, \
    DeviceViolation

from hypernet.enums import *
from hypernet.enums import OptionsEnum, ModuleEnum
from django.utils import timezone
from django.db.models import Avg, Sum, Max, Min, DateTimeField, DateField, F
from django.core.mail import send_mail, EmailMultiAlternatives
from hypernet import constants

def get_generic_jobs(c_id, e_id, p_id, g_id, t_id, s_id, j_id, start_datetime, end_datetime):

    result = None
    if g_id:
        result = ActivityData.objects.filter(primary_entity__assignment_child__parent_id=g_id,customer__id=c_id)
    elif e_id:
        result = ActivityData.objects.filter(primary_entity_id=e_id,customer__id=c_id)
    elif p_id and s_id:
        result = ActivityData.objects.filter(actor_id=p_id, customer_id=c_id, activity_status_id = s_id)
    elif j_id and s_id:
        result = ActivityData.objects.get(id=j_id, customer_id=c_id, activity_status_id=s_id)
    elif s_id:
        result = ActivityData.objects.filter(customer_id=c_id, activity_status_id=s_id)

    # Type is not available in Activity Data, need to discuss if we need type - FIX WALEED
    # elif t_id:
    #     result = ActivityData.objects.filter(customer__id=c_id, device__type_id=t_id)

        
    if start_datetime and end_datetime:
        result = result.filter(timestamp__range=[start_datetime, end_datetime])

    return result


def get_generic_entity_jobs(c_id, e_id, p_id, s_id, start_datetime=None, end_datetime=None):
    result = {}
    if e_id:
        result = Assignment.objects.filter(parent_id=e_id, child__type=DeviceTypeEntityEnum.JOB, customer__id=c_id).values_list('child')
        if result:
            result = Entity.objects.filter(id__in=result, status_id__in=[OptionsEnum.ACTIVE, OptionsEnum.INACTIVE]).values()
            if s_id:
                result = result.filter(job_status_id=s_id).values()
    elif p_id:
        temp_result = []
        queryset = Assignment.objects.filter(child_id=p_id, parent__type=DeviceTypeEntityEnum.TRUCK).values('parent', 'created_datetime',
                                                                            'end_datetime')
        for obj in queryset:
            if obj["end_datetime"]:
                result = Assignment.objects.filter(parent_id=obj["parent"], customer__id=c_id, child__type=DeviceTypeEntityEnum.JOB,
                                                   created_datetime__lte=obj["created_datetime"],
                                                   end_datetime__lte=obj["end_datetime"]).values_list('child')
            else:
                result = Assignment.objects.filter(parent_id=obj["parent"], customer__id=c_id,
                                                   child__type=DeviceTypeEntityEnum.JOB).values_list('child')
            if s_id:
                temp_result.append(Entity.objects.filter(id__in=result, job_status_id=s_id,
                                                         status_id__in=[OptionsEnum.ACTIVE, OptionsEnum.INACTIVE]))
            else:
                temp_result.append(Entity.objects.filter(id__in=result, status_id__in=[OptionsEnum.ACTIVE, OptionsEnum.INACTIVE]))
        result = temp_result
    elif c_id:
        result = Entity.objects.filter(customer_id=c_id, type_id=DeviceTypeEntityEnum.JOB,
                                       job_status_id=s_id, status_id__in=[OptionsEnum.ACTIVE, OptionsEnum.INACTIVE])
    return result


'''
def get_generic_completed_jobs(c_id, e_id, p_id, g_id, t_id, start_datetime, end_datetime):
    if g_id:
        result = LogisticJobs.objects.filter(truck__assignment_child__parent_id=g_id,customer__id=c_id, job_status= IOFOptionsEnum.ACCOMPLISHED)
    elif e_id:
        result = LogisticJobs.objects.filter(entity_id=e_id,customer__id=c_id, job_status= IOFOptionsEnum.ACCOMPLISHED)
    elif p_id:
        result = LogisticJobs.objects.filter(person_id=p_id, customer_id = c_id,  job_status= IOFOptionsEnum.ACCOMPLISHED)
    else:
        result = LogisticJobs.objects.filter(customer__id=c_id, entity__type_id = t_id,  job_status= IOFOptionsEnum.ACCOMPLISHED)

    if start_datetime and end_datetime:
        result = result.filter(job_start_timestamp__range=[start_datetime, end_datetime])
    return result


def get_generic_failed_jobs(c_id, e_id, p_id, g_id, t_id, start_datetime, end_datetime):
    if g_id:
        result = LogisticJobs.objects.filter(truck__assignment_child__parent_id=g_id,customer__id=c_id, job_status = IOFOptionsEnum.FAILED)
    elif e_id:
        result = LogisticJobs.objects.filter(entity_id=e_id,customer__id=c_id,job_status = IOFOptionsEnum.FAILED)
    elif p_id:
        result = LogisticJobs.objects.filter(person_id=p_id, customer_id = c_id, job_status = IOFOptionsEnum.FAILED)
    else:
        result = LogisticJobs.objects.filter(customer__id=c_id, entity__type_id = t_id, job_status = IOFOptionsEnum.FAILED)

    if start_datetime and end_datetime:
        result = result.filter(job_start_timestamp__range=[start_datetime, end_datetime])
    return result

def get_generic_scheduled_jobs(c_id, e_id, p_id, g_id, t_id, start_datetime, end_datetime):
    if g_id:
        result = LogisticJobs.objects.filter(truck__assignment_child__parent_id=g_id,customer__id=c_id, job_status = IOFOptionsEnum.PENDING)
    elif e_id:
        result = LogisticJobs.objects.filter(entity_id=e_id,customer__id=c_id,job_status = IOFOptionsEnum.PENDING)
    elif p_id:
        result = LogisticJobs.objects.filter(person_id=p_id, customer_id = c_id, job_status = IOFOptionsEnum.PENDING)
    else:
        result = LogisticJobs.objects.filter(customer__id=c_id, entity__type_id = t_id, job_status = IOFOptionsEnum.PENDING)

    if start_datetime and end_datetime:
        result = result.filter(job_start_timestamp__range=[start_datetime, end_datetime])
    return result

'''

def start_generic_job(c_id, e_id, start_datetime):
    if e_id:
        job = Assignment.objects.get(parent_id=e_id, type_id=DeviceTypeAssignmentEnum.JOB_ASSIGNMENT, customer_id=c_id)
        result = ActivityData.objects.get(device_id=job.child.id)
        result.actual_job_start_timestamp = start_datetime
        result.job_status.id = IOFOptionsEnum.RUNNING
        result.save()
        return result
    else:
        return None


def get_generic_violations(c_id, e_id, g_id, d_id, j_id, t_id, start_datetime, end_datetime):

    if g_id:
        result = HypernetNotification.objects.filter(device__assignment_child__parent_id=g_id, customer__id=c_id)
    elif e_id:
        result = HypernetNotification.objects.filter(device__id=e_id, customer__id=c_id)
    elif d_id:
        result = HypernetNotification.objects.filter(driver__id=d_id, customer__id=c_id)
    elif j_id:
        result = HypernetNotification.objects.filter(activity_id=j_id, customer__id=c_id)
    else:
        result = HypernetNotification.objects.filter(customer_id=c_id, device__type_id=t_id)

    if start_datetime and end_datetime:
        result = result.filter(timestamp__range=[start_datetime, end_datetime])
    return result.filter(type_id__in=[]).order_by('-timestamp')


'''
def get_driver_violations(c_id, e_id, t_id, start_datetime, end_datetime):
    if e_id:
        result = HypernetNotification.objects.filter(driver_id=e_id, customer__id=c_id).order_by('timestamp')
    else:
        result = HypernetNotification.objects.filter(customer__id=c_id, device__type_id=t_id).order_by('timestamp')
    if start_datetime and end_datetime:
        result = result.filter(timestamp__range=[start_datetime, end_datetime])
    return result


def get_job_violations(c_id, e_id, t_id, start_datetime, end_datetime):

    if e_id:
        result = HypernetNotification.objects.filter(job_id=e_id, customer__id=c_id).order_by('timestamp')
    else:
        result = HypernetNotification.objects.filter(customer__id=c_id, device__type_id=t_id).order_by('timestamp')
    if start_datetime and end_datetime:
        result = result.filter(timestamp__range=[start_datetime, end_datetime])
    return result

'''


def get_generic_maintenances(c_id, e_id, g_id, t_id, start_datetime, end_datetime):
    if g_id:
        result = ActivityData.objects.filter(primary_entity__assignment_child__parent_id=g_id,
                                                    customer__id=c_id).order_by('timestamp')
    elif e_id:
        result = ActivityData.objects.filter(primary_entity_id=e_id, customer__id=c_id).order_by('timestamp')
    else:
        result = ActivityData.objects.filter(customer_id=c_id, primary_entity__type_id=t_id).order_by('timestamp')
    if start_datetime and end_datetime:
        result = result.filter(timestamp__range=[start_datetime, end_datetime])
    return result


def get_generic_fillups(c_id, e_id, g_id, t_id, start_datetime, end_datetime):

    kwargs = dict()
    kwargs['post_fill_vol__isnull'] = False
    kwargs['pre_fill_vol__isnull'] = False
    kwargs['customer__id'] = c_id
    if g_id:
        kwargs['device__assignment_child__parent_id'] =g_id
    elif e_id:
        kwargs['device__id'] =e_id
    elif t_id:
        kwargs['device__type_id'] = t_id

    fillups = LogisticsDerived.objects.filter(**kwargs).order_by('timestamp')

    if start_datetime and end_datetime:
        fillups = fillups.filter(timestamp__range=[start_datetime,end_datetime])

    #  Now that I have all the fill ups for the respective truck, I need to find a way to delete the unnecessary records
    #  and clean the data.
    i = 0
    pre = 0
    post = 0
    timestamp = None
    fill_data = dict()
    fillup_data = []
    for f in fillups:
        if f.pre_fill_vol and f.post_fill_vol:
            if pre == 0:  # Base condition, set the variable for next iterations
                pre = f.pre_fill_vol
            else:
                # Variable is set, check against post now if it is less or equal
                if post <= f.pre_fill_vol:
                    if (f.timestamp - timestamp).total_seconds() > 600:  # If time has passed atleast 10 minutes
                        fillup_data.append({'pre_volume': pre, 'post_volume': post, 'timestamp': timestamp,
                                            'lat': f.latitude, 'long': f.longitude,
                                            'distance_travelled': f.distance_travelled,
                                            'fuel_filled': f.fuel_consumed,
                                            'fuel_avg': f.fuel_avg, })
                        pre = f.pre_fill_vol
                    else:
                        pass
                else:
                    fillup_data.append({'pre_volume':pre, 'post_volume':post, 'timestamp':timestamp,
                                        'lat':f.latitude, 'long': f.longitude,'distance_travelled':f.distance_travelled,
                                        'fuel_filled': f.fuel_consumed,
                                        'fuel_avg':f.fuel_avg,})
                    pre = f.pre_fill_vol
            post = f.post_fill_vol
            timestamp = f.timestamp
            i += 1
            if fillups.count() == i:
                fillup_data.append({'pre_volume': pre, 'post_volume': post, 'timestamp': f.timestamp,
                                    'lat': f.latitude, 'long': f.longitude,'distance_travelled':f.distance_travelled,
                                    'fuel_filled': f.fuel_consumed,
                                    'fuel_avg':f.fuel_avg,})
        else:
            fillup_data.append({'distance_travelled':f.distance_travelled, 'fuel_filled': f.fuel_consumed,
                                'fuel_avg':f.fuel_avg,'pre_volume': None, 'post_volume': None, 'timestamp': f.timestamp,
                                'lat': f.latitude, 'long': f.longitude})
    return fillup_data


def get_generic_decantation(c_id, e_id, g_id, t_id, start_datetime, end_datetime):

    if g_id:
        decants = LogisticsDerived.objects.filter(device__assignment_child__parent_id=g_id, post_dec_vol__isnull=False, pre_dec_vol__isnull=False, customer__id=c_id).order_by('timestamp')
    elif e_id:
        decants = LogisticsDerived.objects.filter(device__id=e_id,post_dec_vol__isnull=False, pre_dec_vol__isnull=False, customer__id=c_id).order_by('timestamp')
    else:
        decants = LogisticsDerived.objects.filter(customer__id=c_id, post_dec_vol__isnull=False,pre_dec_vol__isnull=False, device__type_id=t_id).order_by('timestamp')

    if start_datetime and end_datetime:
        decants = decants.filter(timestamp__range=[start_datetime,end_datetime])

    # i = 0
    # pre = 0
    # post = 0
    timestamp = None
    decant_data = dict()
    decantation_data = []
    for f in decants:
        decant_data['pre_volume'] = f.pre_dec_vol
        decant_data['post_volume'] = f.post_dec_vol
        decant_data['timestamp'] = f.timestamp
        decantation_data.append(decant_data)
        decant_data = dict()
        # if pre == 0:
        #     pre = f.pre_dec_vol
        # else:
        #     if post >= f.pre_dec_vol:
        #         pass
        #     else:
        #         decant_data['pre_volume'] = pre
        #         decant_data['post_volume'] = post
        #         decant_data['timestamp'] = timestamp
        #         decantation_data.append(decant_data)
        #         pre = f.pre_dec_vol
        # post = f.post_dec_vol
        # timestamp = f.timestamp
        # i += 1
        # if decants.count() == i:
        #     decant_data['pre_volume'] = pre
        #     decant_data['post_volume'] = post
        #     decant_data['timestamp'] = timestamp
        #     decantation_data.append(decant_data)
    return decantation_data


def get_generic_device_aggregations(c_id, e_id, g_id, t_id, truck_ids=None):
    if g_id:
        result = LogisticAggregations.objects.filter(device__assignment_child__parent_id=g_id, customer__id=c_id)
    elif e_id:
        result = LogisticAggregations.objects.get(device__id=e_id, customer__id=c_id)
    else:
        result = LogisticAggregations.objects.filter(device__type_id=t_id, customer__id =c_id)
    if truck_ids:
        result = LogisticAggregations.objects.filter(device__id__in=truck_ids, customer__id=c_id)
    return result


def get_generic_distance_travelled(c_id, e_id, g_id, t_id, start_datetime, end_datetime):
    if g_id:
        result = HypernetPostData.objects.filter(device__assignment_child__parent_id=g_id, customer__id=c_id)
    elif e_id:
        result = HypernetPostData.objects.filter(device_id=e_id, customer__id=c_id)
    else:
        result = HypernetPostData.objects.filter(customer_id=c_id,  device__type_id=t_id)

    if start_datetime and end_datetime:
        result = result.filter(timestamp__range=[start_datetime, end_datetime])
    return result.aggregate(Sum('distance_travelled'))['distance_travelled__sum'] or 0


def get_generic_volume_consumed(c_id, e_id, g_id, t_id, start_datetime, end_datetime):

    if g_id:
        result = HypernetPostData.objects.filter(device__assignment_child__parent_id=g_id, customer__id=c_id)
    elif e_id:
        result = HypernetPostData.objects.filter(device_id=e_id, customer__id=c_id)
    else:
        result = HypernetPostData.objects.filter(customer_id=c_id,  device__type_id=t_id)

    if start_datetime and end_datetime:
        result = result.filter(timestamp__range=[start_datetime, end_datetime])
    return result.aggregate(Sum('volume_consumed'))['volume_consumed__sum'] or 0


def get_generic_devices(c_id, e_id, t_id, client_id=None, truck_ids=None):
    if e_id:
        result = Entity.objects.get(id = e_id,customer__id=c_id, status_id__in=[OptionsEnum.ACTIVE,OptionsEnum.INACTIVE])
    elif client_id:
        result = Entity.objects.filter(client__name=client_id, customer__id=c_id, status_id__in=[OptionsEnum.ACTIVE,OptionsEnum.INACTIVE]).distinct().order_by('-created_datetime')
    elif truck_ids:
        result = Entity.objects.filter(id__in=truck_ids, customer__id=c_id, status_id__in=[OptionsEnum.ACTIVE,OptionsEnum.INACTIVE])
    else:
        result = Entity.objects.filter(customer_id=c_id, type_id=t_id,
                                       status_id__in=[OptionsEnum.ACTIVE, OptionsEnum.INACTIVE]).distinct().order_by('-created_datetime')

    return result


def get_generic_trips(c_id, e_id, g_id, t_id, start_datetime, end_datetime):

    if g_id:
        result = TruckTrips.objects.filter(truck__assignment_child__parent_id=g_id,customer__id=c_id).order_by('trip_start_timestamp')
    elif e_id:
        result = TruckTrips.objects.filter(device__id=e_id, customer__id=c_id).order_by('trip_start_timestamp')
    else:
        result = TruckTrips.objects.filter(customer_id=c_id, type__id = t_id).order_by('trip_start_timestamp')

    if start_datetime and end_datetime:
        result = result.filter(trip_start_timestamp__range=[start_datetime, end_datetime])
    return result


def entity_calibration(c_id, e_id):
    if e_id:
        try:
            return DeviceCalibration.objects.get(device_id=e_id, customer_id=c_id).as_json()
        except Exception as e:
            print(str(e))
    else:
        return None


def get_generic_maintenances_snapshot(c_id, e_id, d_id, s_id, m_type_id, start_datetime, end_datetime):

    if e_id:
        maintenances = ActivityData.objects.filter(primary_entity_id=e_id, scheduled_activity__activity_schedule__activity_type_id=DeviceTypeEntityEnum.MAINTENANCE)

    elif d_id:
        maintenances = ActivityData.objects.filter(actor_id=d_id, scheduled_activity__activity_schedule__activity_type_id=DeviceTypeEntityEnum.MAINTENANCE)

    else:
        maintenances = ActivityData.objects.filter(customer_id=c_id, scheduled_activity__activity_schedule__activity_type_id=DeviceTypeEntityEnum.MAINTENANCE)

    if start_datetime and end_datetime:
        maintenances = maintenances.filter(timestamp__gte=start_datetime,
                                           timestamp__lte=end_datetime)
    if s_id:
        maintenances = maintenances.filter(activity_status_id=s_id)

    # if m_type_id:
    #     maintenances = maintenances.filter(maintenance_type_id=m_type_id)


    return maintenances


def get_generic_territories(c_id, e_id, t_id):
    if e_id:
        territories = Entity.objects.filter(id = e_id, customer_id = c_id, type = DeviceTypeEntityEnum.TERRITORY,
                                            status = OptionsEnum.ACTIVE)
    else:
        territories = Entity.objects.filter(customer_id = c_id, type = DeviceTypeEntityEnum.TERRITORY, status = OptionsEnum.ACTIVE)
    if t_id:

        territories = territories.filter(territory_type_id = t_id)

    return territories


def get_uassigned_jobs(c_id, start_datetime, end_datetime):
    ent_obj = Entity.objects.filter(customer_id=c_id, type_id=DeviceTypeEntityEnum.JOB,
                                    status_id__in=[OptionsEnum.ACTIVE, OptionsEnum.INACTIVE])
    ent_list = ent_obj.values_list('id')
    ass_jobs = Assignment.objects.filter(child_id__in=ent_list).values_list('child_id')

    if ass_jobs.count() <= 0:
        ent_obj = None
        # print(ent_obj)
    else:
        ent_obj = ent_obj.exclude(id__in=ass_jobs)

    if start_datetime and end_datetime:
        ent_obj = ent_obj.filter(created_datetime__range=[start_datetime, end_datetime])

    return ent_obj


# TODO TWICE DUE TO AWESOME DATETIME FILEDS IN LOGISTIC JOBS AND ENTITY
def util_get_jobs_chart(query_set, from_date, group_by, job_type):
    final_data = {}
    final_data[job_type] = {}
    alerts_list = query_set.filter(created_datetime__gte=from_date).distinct('created_datetime')

    grouped = itertools.groupby(alerts_list, lambda alert: alert.created_datetime.strftime(group_by))
    inner_dict = []
    alert_dict = {}
    for time, alerts_this_day in grouped:
        inner_alerts = list(alerts_this_day)
        # print(inner_alerts)
        if inner_alerts:
            inner_dict.append({'date': time, 'count': len(inner_alerts)})
    final_data[job_type] = inner_dict
    # print("---Final data---")
    # print(final_data)
    return final_data


# TODO TWICE DUE TO AWESOME DATETIME FILEDS IN LOGISTIC JOBS AND ENTITY
def util_get_jobs_chart_twice(query_set, from_date, group_by, job_type):
    final_data = {}
    final_data[job_type] = {}
    # TODO <<< job_start_timestamp will changed later to ____??>>>
    alerts_list = query_set.filter(job_start_timestamp__gte=from_date).distinct('job_start_timestamp')
    grouped = itertools.groupby(alerts_list, lambda alert: alert.job_start_timestamp.strftime(group_by))
    inner_dict = []
    alert_dict = {}
    for time, alerts_this_day in grouped:
        inner_alerts = list(alerts_this_day)
        # print(time, inner_alerts)
        if inner_alerts:
            inner_dict.append({'date': time, 'count': len(inner_alerts)})
    final_data[job_type] = inner_dict
    # print("---Final data---")
    # print(final_data)
    return final_data


def get_maintenance_details(c_id, e_id, m_type_id, start_datetime, end_datetime):
    if e_id:
        maintenances = Entity.objects.filter(id=e_id, customer_id=c_id, type = DeviceTypeEntityEnum.MAINTENANCE,
                                            status = OptionsEnum.ACTIVE)
    else:
        maintenances = Entity.objects.filter(customer_id=c_id, type = DeviceTypeEntityEnum.MAINTENANCE,
                                            status = OptionsEnum.ACTIVE)
    if m_type_id:
        maintenances = maintenances.filter(maintenance_type_id = m_type_id, status = OptionsEnum.ACTIVE)

    if start_datetime and end_datetime:
        maintenances = maintenances.filter(end_datetime__range=[start_datetime, end_datetime])

    return maintenances


def calculate_fuel_avgs(truck, fuel_consumed,fillup_time):

    result = {}
    last_agg = None
    flag = True

    if not fillup_time:
        fillup_time = timezone.now()
    try:
        last_agg = LogisticAggregations.objects.get(device = truck)
    except last_agg.DoesNotExist:
        last_agg = LogisticAggregations.objects.create(device=truck,
                                            customer=truck.customer,
                                            module=truck.module,
                                            timestamp = timezone.now(),
                                            last_fillup=fillup_time)
        flag = False
    if last_agg:

        #last_fillup = last_agg.last_fillup if last_agg.last_fillup else timezone.now()

        if not last_agg.last_fillup:
            last_agg.last_fillup = timezone.now()
            last_agg.save()
        result = fillup_summary(truck, last_agg, fillup_time, fuel_consumed)
    return result, flag


def fillup_summary(truck, last_agg, fillup_time, fuel_consumed):
    result = dict()
    data_pts = HypernetPostData.objects.filter(device_id=truck, timestamp__range=[last_agg.last_fillup, fillup_time])
    
    total_fuel_consumed = fuel_consumed
    total_distance = data_pts.aggregate(sum=Sum('distance_travelled'))
    if not total_distance['sum']:
        total_distance['sum'] = 0
    total_distance = float(total_distance['sum']) / 1000
    fuel_avg = total_distance / float(total_fuel_consumed)
    
    result['distance'] = total_distance
    result['total_fuel_consumed'] = total_fuel_consumed
    result['fuel_avg'] = fuel_avg
    
    return result

def create_fillup_data(result,truck,customer_id, module_id, latitude,longitude, flag, fillup_time):
    from django.utils.timezone import make_aware
    import traceback
    from dateutil.parser import parse
    fillup = LogisticsDerived (
        device = truck,
        customer_id = customer_id,
        module_id = module_id,
        latitude = latitude,
        longitude = longitude,
        fuel_avg = result['fuel_avg'],
        fuel_consumed = result['total_fuel_consumed'],
        distance_travelled = result['distance'],
        timestamp = fillup_time,
    )
    fillup.save()

    send_mail('Staging Truck Fillup',
              'Truck: ' + fillup.device.name + ' filled at: ' + str(
                  fillup.timestamp) + '. Location: https://www.google.com/maps/search/?api=1&query=' + str(
                  fillup.latitude) + ',' + str(fillup.longitude) +
              '. Fuel filled: ' + str(fillup.fuel_consumed),
              'support@hypernymbiz.com',
              constants.email_list, fail_silently=True)
    try:
        last_fillup =LogisticAggregations.objects.get(device=truck)
        print(flag)

        if flag is True:
            fillup_time = parse(fillup_time)

            print("Fillup time",fillup_time)
            print("Fillup time type",type(fillup_time))

            l_fillup = last_fillup.last_fillup
            l_fillup = l_fillup.replace(tzinfo=None)

            print("Last fillup", l_fillup)
            print("Last fillup Type", type(l_fillup))

            if fillup_time > l_fillup:
                print("Fillup time greater than last fillup")
                last_fillup.last_fillup = fillup_time
                last_fillup.save()
    except:
        last_fillup=None
        print(traceback.print_exc())

