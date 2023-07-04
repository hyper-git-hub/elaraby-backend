from __future__ import unicode_literals
from hypernet.enums import IOFOptionsEnum
from django.db.models import Sum
from .models import LogisticMaintenance, \
    LogisticAggregations, \
    ActivityData, \
    TruckTrips
from hypernet.models import Entity, \
    Assignment, \
    HypernetNotification, \
    HypernetPostData
from hypernet.enums import *


def get_pending_jobs(c_id, f_id, t_id, d_id):
    if f_id:
        result = Assignment.objects.filter(child_job_status_id=IOFOptionsEnum.PENDING,
                                           child__type_id=DeviceTypeEntityEnum.JOB, customer__id=c_id).filter(
            parent__assignment_child__parent_id=f_id)
    elif t_id:
        result = Assignment.objects.filter(child_job_status_id=IOFOptionsEnum.PENDING,
                                           child__type_id=DeviceTypeEntityEnum.JOB, customer__id=c_id).filter(
            parent_id=t_id)
    elif d_id:
        result = Assignment.objects.filter(child_job_status_id=IOFOptionsEnum.PENDING,
                                           child__type_id=DeviceTypeEntityEnum.JOB, customer__id=c_id).filter(
            parent__assignment_child_id=d_id)
    else:
        return Entity.objects.filter(customer__id=c_id, type_id=DeviceTypeEntityEnum.JOB,
                                     job_status_id=IOFOptionsEnum.PENDING)

    return result


def get_unassigned_jobs(c_id, f_id, t_id, d_id):
    if f_id:
        result = Entity.objects.filter(id=f_id, job_status_id=IOFOptionsEnum.ABORTED, customer__id=c_id)
    elif t_id:
        result = Entity.objects.filter(id=t_id, status_id=IOFOptionsEnum.ABORTED, customer__id=c_id)
    elif d_id:
        result = Entity.objects.filter(id=d_id, status_id=IOFOptionsEnum.ABORTED, customer__id=c_id)
    else:
        result = Entity.objects.filter(status_id=IOFOptionsEnum.ABORTED, customer__id=c_id)
    return result


def get_device_aggregations(c_id, e_id, t_id):
    if e_id:
        result = LogisticAggregations.objects.get(device_id=e_id, customer__id=c_id)
    else:
        result = LogisticAggregations.objects.filter(customer__id=c_id, device__type_id=t_id)

    return result


def get_jobs(c_id, f_id, t_id, d_id, start_datetime, end_datetime):

    if f_id:
        result = ActivityData.objects.filter(truck__assignment_child__parent_id=f_id,customer__id=c_id)
    elif t_id:
        result = ActivityData.objects.filter(truck_id=t_id,customer__id=c_id)
    elif d_id:
        result = ActivityData.objects.filter(driver_id=d_id,customer__id=c_id)
    else:
        result = ActivityData.objects.filter(customer__id=c_id)

    if start_datetime and end_datetime:
        result = result.filter(job_start_timestamp__range=[start_datetime, end_datetime])
    return result


def get_job_trips(c_id, j_id):
    if j_id:
        result = TruckTrips.objects.filter(job_id=j_id,customer__id=c_id).order_by('trip_start_timestamp')
    else:
        result = TruckTrips.objects.filter(customer__id=c_id).order_by('trip_start_timestamp')

    return result


def get_trips(c_id, f_id, t_id, start_datetime, end_datetime):

    if f_id:
        result = TruckTrips.objects.filter(truck__assignment_child__parent_id=f_id,customer__id=c_id).order_by('trip_start_timestamp')
    elif t_id:
        result = TruckTrips.objects.filter(device__id=t_id, customer__id=c_id).order_by('trip_start_timestamp')
    else:
        result = TruckTrips.objects.filter(customer_id=c_id).order_by('trip_start_timestamp')

    if start_datetime and end_datetime:
        result = result.filter(trip_start_timestamp__range=[start_datetime, end_datetime])
    return result



def get_device_aggregations(c_id, f_id, t_id, d_id):

    if f_id:
        result = LogisticAggregations.objects.filter(device__assignment_child__parent_id=f_id, device__type_id=DeviceTypeEntityEnum.FLEET, customer__id=c_id)
    elif t_id:
        result = LogisticAggregations.objects.filter(device__id=t_id,  device__type_id=DeviceTypeEntityEnum.TRUCK, customer__id=c_id)
    elif d_id:
        result = LogisticAggregations.objects.filter(device_id=d_id, device__type_id=DeviceTypeEntityEnum.DRIVER, customer__id =c_id)

    return result.aggregate(Sum('total_distance'),
                       Sum('total_volume_consumed'),
                       Sum('total_trips'),
                       Sum('total_jobs_completed'),
                       Sum('total_jobs_failed'),
                       Sum('total_maintenances'),
                       Sum('total_violations'),
                       Sum('total_fillups'))




def get_driver_details(c_id, d_id):
    data = dict()
    driver_list = []
    result = dict()
    on_job = 0
    assigned = 0
    unassigned = 0
    available = 0
    if d_id:
        if Assignment.objects.get(child_id=d_id, parent__type_id=DeviceTypeEntityEnum.TRUCK).exists():
            data["assigned_truck"] = Assignment.objects.get(child_id=d_id,
                                                            parent__type_id=DeviceTypeEntityEnum.TRUCK).parent.as_truck_json()
            if Assignment.objects.get(parent_id=data["assigned_truck"].id,
                                      child__type_id=DeviceTypeEntityEnum.TRUCK).exists():
                data["assigned_job"] = Assignment.objects.get(parent_id=data["assigned_truck"].id,
                                                              child__type_id=DeviceTypeEntityEnum.TRUCK).child.as_job_json()
            else:
                data["assigned_job"] = "Not Assigned"
        else:
            data["assigned_truck"] = "Not Assigned"
        data["driver_rating"] = LogisticAggregations.objects.get(device_id=d_id).performance_rating
        return data
    else:
        drivers = Entity.objects.filter(customer_id=c_id, device__type_id=DeviceTypeEntityEnum.DRIVER)
        for dr in drivers:
            if Assignment.objects.get(child_id=dr.id, parent__type_id=DeviceTypeEntityEnum.TRUCK).exists():
                data["assigned_truck"] = Assignment.objects.get(child_id=dr.id, parent__type_id=DeviceTypeEntityEnum.TRUCK).parent.as_truck_json()
                assigned += 1
                if Assignment.objects.get(parent_id=data["assigned_truck"].id, child__type_id=DeviceTypeEntityEnum.TRUCK).exists():
                    data["assigned_job"] = Assignment.objects.get(parent_id=data["assigned_truck"].id, child__type_id=DeviceTypeEntityEnum.TRUCK).child.as_job_json()
                    data["availability"] = "Not Available"
                    on_job +=1
                else:
                    data["assigned_job"] = "Not Assigned"
                    data["availability"] = "Available"
                    available += 1
            else:
                data["assigned_truck"] = "Not Assigned"
                unassigned += 1
            data["driver_rating"] = LogisticAggregations.objects.get(device_id=dr.id).performance_rating
            driver_list.append(data)
        result["assigned"] = assigned
        result["unassigned"] = unassigned
        result["on_job"] = on_job
        result["available"] = available
        result["driver_list"] = driver_list
        result["driver_count"] = len(driver_list)
        return result





def get_distance_travelled(c_id, f_id, t_id, d_id, start_datetime, end_datetime):

    if f_id:
        result = HypernetPostData.objects.filter(device__assignment_child__parent_id=f_id, customer__id=c_id)
    elif t_id:
        result = HypernetPostData.objects.filter(device_id=t_id, customer__id=c_id)
    elif d_id:
        result = HypernetPostData.objects.filter(device_id=d_id, customer__id=c_id)
    else:
        result = HypernetPostData.objects.filter(customer_id=c_id)

    if start_datetime and end_datetime:
        result = result.filter(timestamp__range=[start_datetime, end_datetime])
    return result.aggregate(Sum('distance_travelled'))['distance_travelled__sum']




def get_volume_consumed(c_id, f_id, t_id, d_id, start_datetime, end_datetime):

    if f_id:
        result = HypernetPostData.objects.filter(device__assignment_child__parent_id=f_id, customer__id=c_id)
    elif t_id:
        result = HypernetPostData.objects.filter(device_id=t_id, customer__id=c_id)
    elif d_id:
        result = HypernetPostData.objects.filter(device_id=d_id, customer__id=c_id)
    else:
        result = HypernetPostData.objects.filter(customer_id=c_id)
    if start_datetime and end_datetime:
        result = result.filter(timestamp__range=[start_datetime, end_datetime])
    return result.aggregate(Sum('volume_consumed'))['volume_consumed__sum']



def get_driver_jobs(d_id, job_status, start_datetime, end_datetime):
    if start_datetime and end_datetime:
        result = TruckTrips.objects.filter(driver_id=d_id, timestamp__range=[start_datetime, end_datetime]).values('job').distinct()
    if d_id:
        job_data = []
        if result:
            pass
        else:
            result = TruckTrips.objects.filter(driver_id=d_id).values('job').distinct()
        for obj in result:
            if job_status:
                job_data.append(Entity.objects.get(id=obj.id, job_status=job_status).as_json())
            else:
                job_data.append(Entity.objects.get(id=obj.id).as_json())
    return job_data



def get_maintenances(c_id, f_id, t_id, start_datetime, end_datetime):

    if f_id:
        result = ActivityData.objects.filter(device__assignment_child__parent_id=f_id, customer__id=c_id).order_by('timestamp')
    elif t_id:
        result = ActivityData.objects.filter(device_id=t_id, customer__id=c_id).order_by('timestamp')
    else:
        result = ActivityData.objects.filter(customer_id=c_id).order_by('timestamp')
    if start_datetime and end_datetime:
        result = result.filter(timestamp__range=[start_datetime,end_datetime])
    return result



def get_violations(c_id, f_id, t_id, d_id, j_id, start_datetime, end_datetime):

    if f_id:
        result = HypernetNotification.objects.filter(device__assignment_child__parent_id=f_id, customer__id=c_id).order_by('timestamp')
    elif t_id:
        result = HypernetNotification.objects.filter(device__id=t_id, customer__id=c_id).order_by('timestamp')
    elif d_id:
        result = HypernetNotification.objects.filter(driver_id=d_id, customer__id=c_id).order_by('timestamp')
    elif j_id:
        result = HypernetNotification.objects.filter(job_id=j_id, customer__id=c_id).order_by('timestamp')
    else:
        result = HypernetNotification.objects.filter(customer_id=c_id).order_by('timestamp')

    if start_datetime and end_datetime:
        result = result.filter(timestamp__range=[start_datetime, end_datetime])
    return result


def get_bins_maintenance(c_id, b_id, start_datetime, end_datetime):
    if b_id:
        result = ActivityData.objects.filter(device_id=b_id,customer__id=c_id).order_by('timestamp')
    else:
        result = ActivityData.objects.filter(customer__id=c_id, device__type_id=DeviceTypeEntityEnum.BIN).order_by('timestamp')
    if start_datetime and end_datetime:
        result = result.filter(timestamp__range=[start_datetime,end_datetime])
    return result


def get_bins_aggregations(c_id, b_id):
    if b_id:
        result = LogisticAggregations.objects.get(device_id=b_id)
    else:
        result = LogisticAggregations.objects.filter(customer__id=c_id, device__type_id=DeviceTypeEntityEnum.BIN)

    return result


def get_bins_violations(c_id, b_id, start_datetime, end_datetime):
     if b_id:
         result = HypernetNotification.objects.filter(device__id = b_id,customer__id=c_id)
     else:
         result = HypernetNotification.objects.filter(customer__id = c_id, device__type__id=DeviceTypeEntityEnum.BIN)
     if start_datetime and end_datetime:
         result = result.filter(timestamp__range=[start_datetime, end_datetime])
     return result


def get_customer_entity(c_id, b_id):
    if b_id:
        result = Entity.objects.get(id = b_id,customer__id=c_id)
    else:
        result = Entity.objects.filter(customer__id=c_id, type__id=DeviceTypeEntityEnum.BIN)

    return result

