from __future__ import unicode_literals
from django.db.models import Sum
from .models import TruckTrips, \
    LogisticsDerived


def get_job_trips(c_id, j_id):
    if j_id:
        result = TruckTrips.objects.filter(job_id=j_id,customer__id=c_id).order_by('trip_start_timestamp')
    else:
        result = TruckTrips.objects.filter(customer__id=c_id).order_by('trip_start_timestamp')

    return result



def get_fillups(c_id, f_id, t_id, start_datetime, end_datetime):

    if f_id:
        fillups = LogisticsDerived.objects.filter(device__assignment_child__parent_id=f_id, post_fill_vol__isnull=False, pre_fill_vol__isnull=False, customer__id=c_id).order_by('timestamp')
    elif t_id:
        fillups = LogisticsDerived.objects.filter(device__id=t_id,post_fill_vol__isnull=False, pre_fill_vol__isnull=False, customer__id=c_id).order_by('timestamp')
    else:
        fillups = LogisticsDerived.objects.filter(customer__id=c_id, post_fill_vol__isnull=False,pre_fill_vol__isnull=False).order_by('timestamp')

    if start_datetime and end_datetime:
        fillups = fillups.filter(timestamp__range=[start_datetime,end_datetime])

    i = 0
    pre = 0
    post = 0
    timestamp = None
    fill_data = dict()
    fillup_data = []
    for f in fillups:
        if pre == 0:
            pre = f.pre_fill_vol
        else:
            if post <= f.pre_fill_vol:
                pass
            else:
                fill_data['pre_volume'] = pre
                fill_data['post_volume'] = post
                fill_data['timestamp'] = timestamp
                fillup_data.append(fill_data)
                pre = f.pre_fill_vol
        post = f.post_fill_vol
        timestamp = f.timestamp
        i += 1
        if fillups.count() == i:
            fill_data['pre_volume'] = pre
            fill_data['post_volume'] = pre
            fill_data['timestamp'] = timestamp
            fillup_data.append(fill_data)
    return fillup_data


