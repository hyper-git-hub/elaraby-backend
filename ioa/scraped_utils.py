from hypernet.enums import DeviceTypeEntityEnum
from ioa.utils import get_herd_animal_ids
from ioa.models import *
from hypernet.utils import exception_handler
from django.db.models import Count, Sum, F, Max, Case, When
from hypernet.constants import *
import itertools
from hypernet.models import *


# UTILS NOT CURRENTLY REQUIRED

# Total no of activitites
# Details of sctivities for all animals in given time range
@exception_handler([])
def get_activities_stats(c_id, s_date, e_date):
    q_set = ActivityList.objects.filter(customer_id=c_id, created_datetime__date__gte=s_date,
                                        created_datetime__date__lte=e_date)
    return q_set.values(status=F('action_status__value'), type=F('activity_type__value'), ).annotate(
        count=Count('id')).order_by('performed_end_time')


def util_get_customer_animals(c_id):
    return Entity.objects.filter(module=1, type=DeviceTypeEntityEnum.ANIMAL, customer_id=c_id)


##### HERD PAGE UTILS NOT MATURE YET ! ######
def get_herd_info(date_range):
    q_set = Assignment.objects.filter(created_datetime__gte=date_range).all()
    data = {}
    for obj in q_set:
        data[obj.parent_id] = obj.get_all_childs()
    return data


def get_herd_stats(s_date, e_date):
    q_set = Aggregation.objects.filter(created_datetime__date__gte=s_date, created_datetime__date__lte=e_date)
    return q_set.values(avg_milk=F('avg_milk_yield'), herd=F('herd_id__name')).order_by('herd_id')


def util_get_alert_graph_data(customer_id, from_date, group_by, herd_id=None, animal_id=None):
    final_data = {}
    for violation_type in IOA_VIOLATION_TYPES:
        final_data[violation_type] = {}
        alerts_list = HypernetNotification.objects.filter(created_datetime__gte=from_date, customer=customer_id,
                                                          violation_type__value=violation_type)
        if animal_id:
            alerts_list = alerts_list.filter(animal_id=animal_id)
        if herd_id:
            animals_list = get_herd_animal_ids(herd_id=herd_id)
            alerts_list = alerts_list.filter(animal_id__in=animals_list)
        grouped = itertools.groupby(alerts_list, lambda alert: alert.created_datetime.strftime(group_by))
        inner_dict = {}
        for time, alerts_this_day in grouped:
            inner_alerts = list(alerts_this_day)
            if inner_alerts:
                inner_dict[time] = len(inner_alerts)
        final_data[violation_type] = inner_dict
    return final_data


def get_herd(c_id):
    q_set = Assignment.objects.filter(customer_id=c_id, parent__type__name='herd')
    return q_set.values(herd_name=F('parent_id__name'), herd_id=F('parent_id')) \
        .annotate(herd_animals_count=Count('child_id'), groups=F('child_id__group__value')).order_by('parent_id')


def get_milking_stats_weekly(from_dtm, c_id):
    q_set = ActivityList.objects.filter(customer=c_id, activity_type__value='milking', created_datetime__gte=from_dtm)
    return q_set.values(animals=F('animal__name'), type=F('activity_type__value'),
                        time=F('performed_end_time'), value=F('individual_value')) \
        .order_by('performed_end_time')


def util_staff_list(c_id, date_range):
    q_set = ActivityList.objects.filter(customer=c_id, created_datetime__date__gte=date_range).distinct(
        'assigned_to_activity')
    data_list = []
    opt = {a_group: 0 for a_group in
           Options.objects.filter(key='activity_action_status').values_list('value', flat=True)}
    for activity in q_set:
        groups = dict(opt)
        childs = activity.activity_caretaker()
        for child in childs:
            action_status = child.action_status.value
            if action_status in groups.keys():
                groups[action_status] += 1
        inner_dict = {
            "caretaker": activity.assigned_to_activity.first_name,
            "caretaker_email": activity.assigned_to_activity.email,
            "role": activity.assigned_to_activity.role.name,
            "id": activity.assigned_to_activity.id,
            "contact no": '001-510-1145',
        }
        inner_dict.update(groups)
        data_list.append(inner_dict)
    return data_list


# Details of activitties per Caretaker
###Modification Required for filtering user instead of customer depends on columns###
def get_staff_activity_list(c_id, u_id):
    pass
    activity = ActivityList.objects.filter(assigned_to_activity=u_id, customer=c_id)
    scheduling = Scheduling.objects.filter(assigned_to=u_id, customer=c_id)
    completed = activity.filter(action_status__value='complete')
    pending = activity.filter(action_status__value='pending')

    activity_list = []
    staff_details = {}
    activity_details = {}

    for staff_activity in activity:
        staff_details['staff_details'] = \
            {
                "name": staff_activity.assigned_to_activity.first_name,
                "date_joined": staff_activity.assigned_to_activity.date_joined,
                "role": staff_activity.assigned_to_activity.role.name,
                "email": staff_activity.assigned_to_activity.email,
            }

    for pending_activities in pending:
        activity_details['pending_activities'] = \
            {
                "status": pending_activities.action_status.value,
                "activity_priority": pending_activities.activity_priority.value,
                "activity_type": pending_activities.activity_type.value,
                "start_time": pending_activities.scheduled_start_time,
                "end_time": pending_activities.performed_end_time,
                "activity_id": pending_activities.id,
            }

    for completed_activities in completed:
        activity_details['completed-activities'] = \
            {
                "status": completed_activities.action_status.value,
                "activity_priority": completed_activities.activity_priority.value,
                "activity_type": completed_activities.activity_type.value,
                "start_time": completed_activities.scheduled_start_time,
                "end_time": completed_activities.performed_end_time,
                "activity_id": completed_activities.id,
            }

    activity_list.append(activity_details)
    activity_list.append(staff_details)
    return activity_list


def update_alert_flag_status(u_id, c_id, m_id):
    q_set = HypernetNotification.objects.filter(customer=c_id, module_id=m_id, user=u_id)
    for users in q_set:
        obj = users.notificationgroups_set.filter(user=u_id, is_viewed=False).update(is_viewed=True)
        print(users.notificationgroups_set.get(user=u_id).is_viewed)
        if obj:
            return True
        else:
            return False
