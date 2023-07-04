import hypernet
from ioa.models import ActivityList, Aggregation, Scheduling
__author__ = 'majee'
import calendar
from django.db.models.functions import TruncMonth
from random import randint
from hypernet.enums import DeviceTypeEntityEnum, ModuleEnum
from hypernet.enums import OptionsEnum
from user.enums import RoleTypeEnum
from hypernet.models import Entity, HypernetNotification, Assignment
# from ioa.models import ActivityList, Aggregation, Scheduling
from hypernet.utils import exception_handler
from django.db.models import Count, Sum, F, Max, Case, When
from hypernet import constants
import itertools
from datetime import timedelta
from hypernet.models import *
from hypernet.enums import IOAOPTIONSEnum
from hypernet.constants import *
import datetime
import random
import string
# Total animal count overall
@exception_handler(0)
def util_get_total_animals(customer_id):
    q_set = Entity.objects.filter(customer_id=customer_id)
    return q_set


# Total Herds of Customer
@exception_handler(0)
def util_get_total_herds(customer_id):
    q_set = Entity.objects.filter(customer_id=customer_id, type=DeviceTypeEntityEnum.HERD)
    return q_set.annotate(total_herds=Count('id')).count()


# Total animals for each herd.
@exception_handler(0)
def get_herd_animal_count(herd_id):
    return Assignment.objects.filter(parent_id=herd_id).count()


#Alerts for all animals over given time range.
def get_alerts(c_id, days=LAST_WEEK, a_id=None):
    if a_id:
        q_set = HypernetNotification.objects.filter(customer=c_id, module=ModuleEnum.IOA,
                                                    device=a_id, timestamp__gte=days)
    else:
        q_set = HypernetNotification.objects.filter(customer=c_id, module=ModuleEnum.IOA,
                                                    timestamp__gte=days)

    alert_dict = {}
    for alert in q_set:
        count = q_set.filter(violation_type__value=alert.violation_type.value).count()
        alert_dict[alert.violation_type.value] = count
    return alert_dict


#Alerts of the time range provided for all animals
def get_alerts_recent(customer_id, date_range):
    q_set = HypernetNotification.objects.filter(customer=customer_id, created_datetime__gte=date_range)
    return q_set.values(name=F('violation_type__value')).annotate(value=Count('id'))


#Details of Animal Group for all animals
def util_get_animal_group_count(customer_id, h_id=None):
    info_dict = {}
    if h_id:
        info_dict["total"] = get_total_cows(customer_id, h_id)
        info_dict[IN_LACTATION] = get_total_cows_by_group(customer_id, IN_LACTATION, h_id)
        info_dict[HEIFERS] = get_total_cows_by_group(customer_id, HEIFERS, h_id)
        info_dict[CALFS] = get_total_cows_by_group(customer_id, CALFS, h_id)
    else:
        info_dict["total"] = get_total_cows(customer_id)
        info_dict[IN_LACTATION] = get_total_cows_by_group(customer_id, IN_LACTATION)
        info_dict[HEIFERS] = get_total_cows_by_group(customer_id, HEIFERS)
        info_dict[CALFS] = get_total_cows_by_group(customer_id, CALFS)
    return info_dict

##MILKING VALUE Details per animal GROUPED BY DATE PERFORMED
def get_activity_stats(from_dtm, c_id):
    q_set = ActivityList.objects.filter(customer=c_id, activity_type__value=hypernet.constants.MILKING,
                                        created_datetime__gte=from_dtm)
    return q_set.values(animals=F('animal__name'), type=F('activity_type__value'),
                        time=F('performed_end_time'), value=F('individual_value')) \
        .order_by('performed_end_time')


# Total Milk/feed yield for all animals at given time range for Dashboard
def get_total_milk_feed(act_type, time_range):
    q_set = ActivityList.objects.filter(activity_type__value=act_type, created_datetime__gte=time_range)
    return q_set.values(type=F('activity_type__value')).annotate(total=Sum('individual_value'))


#Maximum milk yielding animal and its value
def util_get_max_milk_yield(c_id, s_date, e_date):
    q_set = ActivityList.objects.filter(customer_id=c_id, created_datetime__gte=s_date, created_datetime__lte=e_date,
                                        activity_type__key=hypernet.constants.ACTIVITY_TYPE,
                                        activity_type__value=hypernet.constants.MILKING)
    return q_set.values(type=F('activity_type__value'), animal_id=F('animal_id')).annotate(
        maximum=Max('individual_value'))


#Total feed consumed, all animals overall
def util_get_feed_consumed(c_id, s_date, e_date):
    q_set = ActivityList.objects.filter(customer_id=c_id, created_datetime__gte=s_date, created_datetime__lte=e_date,
                                        activity_type__key=hypernet.constants.ACTIVITY_TYPE,
                                        activity_type__value=hypernet.constants.FEEDING)
    return q_set.values(type=F('activity_type__value')).annotate(total=Sum('group_value'))


def get_animal_alerts_count(customer_id, animal_id, days):
    q_set = HypernetNotification.objects.filter(created_datetime__gte=days,
                                                device=animal_id, customer=customer_id)
    return q_set.values(alert_type=F('violation_type__value')).annotate(count=Count('violation_type'))


def util_get_recent_alerts(customer_id, status, herd_id=None, animal_id=None,
                           no_alerts=constants.RECENT_DATA):
    if animal_id and status:
        q_set = HypernetNotification.objects.filter(customer=customer_id, status__value=status,
                                                    device_id=animal_id).order_by('-id')[:no_alerts]

    elif animal_id:
        q_set = HypernetNotification.objects.filter(customer=customer_id,
                                                    device_id=animal_id).order_by('-id')[:no_alerts]

    elif herd_id:
        animals_list = Assignment.objects.filter(parent_id=herd_id).values_list('child_id', flat=True)
        q_set = HypernetNotification.objects.filter(customer=customer_id,
                                                    device_id__in=animals_list,
                                                    ).order_by('-id')[:no_alerts]

    elif herd_id and status:
        animals_list = Assignment.objects.filter(parent_id=herd_id).values_list('child_id', flat=True)
        q_set = HypernetNotification.objects.filter(customer=customer_id,
                                                    device_id__in=animals_list,
                                                    status__value=status
                                                    ).order_by('-id')[:no_alerts]

    elif status:
        q_set = HypernetNotification.objects.filter(customer=customer_id,
                                                    device_id__isnull=False,
                                                    status__value=status
                                                    ).order_by('-id')[:no_alerts]

    else:
        q_set = HypernetNotification.objects.filter(customer=customer_id,
                                                    device_id__isnull=False,
                                                    ).order_by('-id')[:no_alerts]

    return q_set


def util_get_animal_details(customer_id, herd_id=None, animal_id=None):
    if animal_id:
        q_set = Entity.objects.filter(customer_id=customer_id, id=animal_id)
        print(q_set)
    elif herd_id:
        animal_list = Assignment.objects.filter(parent_id=herd_id).values_list('child', flat=True)
        q_set = Entity.objects.filter(customer_id=customer_id, id__in=animal_list)
    else:
        q_set = Entity.objects.filter(customer_id=customer_id, type=DeviceTypeEntityEnum.ANIMAL)
        print(q_set)
    return q_set


def get_data_param(request, key, default):
    key = request.data.get(key, default)
    return key or default


def time_diff_seconds(t1,t2):
    return (datetime.combine(datetime.now().today(),t1) - datetime.combine(datetime.now().today(),t2)).total_seconds()


def get_herd_animal_ids(herd_id):
    return Assignment.objects.filter(parent_id=herd_id).values(animal=F('child__name'))


def get_entity_dropdown(c_id, entity_type, m_id, parent=None, bins=None):
    if parent:
        q_set = Assignment.objects.filter(parent=parent, status=OptionsEnum.ACTIVE, module_id=m_id).values_list(
            'child').values(
            id=F('child__id'),
            label=F('child__name'),
            entity_location=F('child__source_latlong')).order_by(
            'id')

    else:
        if entity_type == DeviceTypeEntityEnum.label(DeviceTypeEntityEnum.BIN):
            bins = Entity.objects.filter(customer=c_id, type_id=DeviceTypeEntityEnum.BIN,
                                           status=OptionsEnum.ACTIVE)
            result = []
            for obj in bins:
                try:
                    Assignment.objects.get(parent_id=obj.id, customer=c_id,
                                               parent__type_id=DeviceTypeEntityEnum.BIN,
                                               child__type_id=DeviceTypeEntityEnum.TERRITORY,
                                               status=OptionsEnum.ACTIVE)
                except:
                    result.append({'id': obj.id, 'name': obj.name, 'entity_location':obj.source_latlong})
            q_set = result

        else:
            q_set = Entity.objects.filter(customer_id=c_id, type__name=(entity_type),
                                          status=OptionsEnum.ACTIVE, module_id=m_id) \
                .values('id', label=F('name'), entity_location=F('source_latlong')).order_by('id')
    return q_set



def get_herd_details_list(c_id):
    assigment_list = Assignment.objects.filter(customer_id=c_id, child__type_id=DeviceTypeEntityEnum.ANIMAL).distinct(
        'parent_id')
    data_list = []
    opt = {a_group: 0 for a_group in Options.objects.filter(key=constants.ANIMAL_GROUP).values_list('value', flat=True)}
    for assigment in assigment_list:
        groups = dict(opt)
        childs = assigment.get_all_child_objs()
        for child in childs:
            grp = child.child.group.value
            if grp in groups.keys():
                groups[grp] += 1
        inner_dict = {"herd_id": assigment.parent_id, "herd_name": assigment.parent.name,
                      "total_animals": len(childs)}
        inner_dict.update(groups)
        data_list.append(inner_dict)
    return data_list


def get_animal_by_group(grp, c_id):
    animal_list = []
    q_set = Entity.objects.filter(group_id__value=grp, customer=c_id, type=DeviceTypeEntityEnum.ANIMAL)
    for animal in q_set:
        animal_list.append(util_animal_detail(animal_obj=animal))
    return animal_list


def get_animal_by_status(sts, c_id):
    animal_list = []
    q_set = Entity.objects.filter(lactation_status_id__value=sts, customer=c_id, type=DeviceTypeEntityEnum.ANIMAL)
    for animal in q_set:
        animal_list.append(util_animal_detail(animal_obj=animal))
    return animal_list


def get_alerts_by_type(customer_id, s_date, alert_type):
    q_set = HypernetNotification.objects.filter(customer=customer_id, created_datetime__gte=s_date,
                                                violation_type__value=alert_type)
    return q_set.values(alert=F('violation_type__value')).annotate(count=Count('id'))


def util_herd_alerts_date(customer_id, herd_id=None, d_range=LAST_WEEK):
    if herd_id:
        animals_list = Assignment.objects.filter(parent_id=herd_id).values_list('child_id', flat=True)
        q_set = HypernetNotification.objects.filter(customer=customer_id, device__in=animals_list,
                                                    created_datetime__gte=d_range)

    else:
        q_set = HypernetNotification.objects.filter(customer=customer_id, device__isnull=False).order_by('-id')

    return q_set.values(date=F('created_datetime'), animal=F('device__name'), alert_type=F('violation_type__label'),
                        viewed_flag=F('is_viewed'))


###CALL TO BE CHANGED ON AGGREGATION MODEL
def get_activity_values(from_dtm, c_id, act_type):
    activtity_list = []
    q_set = ActivityList.objects.filter(customer=c_id, activity_type__value=act_type, created_datetime__gte=from_dtm)
    if act_type == 'milking':
        return q_set.values(type=F('activity_type__value'),
                            time=F('performed_end_time'), value=Sum('individual_value')) \
            .order_by('-performed_end_time')

    elif act_type == 'feeding':
        return q_set.values(type=F('activity_type__value'),
                            time=F('performed_end_time'), value=Sum('group_value')) \
            .order_by('-performed_end_time')


def util_get_feed_consumed_today(c_id, s_date):
    q_set = ActivityList.objects.filter(customer_id=c_id, created_datetime__gte=s_date,
                                        activity_type__value=hypernet.constants.FEEDING)
    return q_set.values(type=F('activity_type__value')).annotate(total=Sum('group_value'))


def get_activities_details(c_id, date_range, type=None):
    if type is None:
        q_set = ActivityList.objects.filter(customer_id=c_id, created_datetime__date__gte=date_range)

        return q_set.values(status=F('action_status__value'), type=F('activity_type__value'),
                            priority=F('activity_priority__value'), cow_id=F('animal__name'),
                            caretaker_assigned=F('modified_by__first_name'), date=F('performed_end_time'),
                            comments=F('performed_comments'), scheduled_time=F('scheduled_start_time'),
                            performed_time=F('performed_start_time'),
                            alert=F('derived_alerts_id__violation_type__value'),
                            caretaker_email=F('created_by__email')).order_by('activity_priority')


# def get_users_list(c_id):
#     q_set = User.objects.filter(customer_id=c_id, role_id=RoleTypeEnum.USER)
#     return q_set.values(email_id=F('email'), user_status=F('is_active'), name=F('first_name'),
#                         image=F('avatar'), user_role=F('role_id__name'))


def util_get_alerts_data_modified(customer_id, from_date, group_by, herd_id=None, animal_id=None):
    final_data = {}
    for violation_type in constants.IOA_VIOLATION_TYPES:
        final_data[violation_type] = {}
        alerts_list = HypernetNotification.objects.filter(timestamp__gte=from_date, customer=customer_id,
                                                          violation_type__value=violation_type)
        if animal_id:
            alerts_list = alerts_list.filter(animal_id=animal_id)
        if herd_id:
            animals_list = get_herd_animal_ids(herd_id=herd_id)
            alerts_list = alerts_list.filter(animal_id__in=animals_list)

        grouped = itertools.groupby(alerts_list, lambda alert: alert.timestamp.strftime(group_by))
        inner_dict = []
        alert_dict = {}
        for time, alerts_this_day in grouped:
            inner_alerts = list(alerts_this_day)
            if inner_alerts:
                alert_dict['date'] = time
                alert_dict['count'] = len(inner_alerts)
        inner_dict.append(alert_dict)
        final_data[violation_type] = inner_dict

    return final_data


def get_animal_milk_yield(a_id, time_range, c_id):
    today = datetime.date.today().day
    yesterday = (today - 1)
    q_set = ActivityList.objects.filter(customer=c_id, animal=a_id, activity_type__value=hypernet.constants.MILKING,
                                        performed_end_time__gte=time_range)

    milk = {}
    today_milk = q_set.filter(performed_end_time__day=str(today)).values(value=F('individual_value'))
    yesterday_milk = q_set.filter(performed_end_time__day=str(yesterday)).values(value=F('individual_value'))
    if today_milk & yesterday_milk:
        milk['today'] = float(today_milk.get().individual_value)
        milk['yesterday'] = float(yesterday_milk.get().individual_value)
        return milk
    else:
        return ["no_data"]


def get_animal_milk_yield_last_two_days(from_dtm, c_id, a_id):
    q_set = ActivityList.objects.filter(animal=a_id, customer=c_id, activity_type__value=hypernet.constants.MILKING,
                                        performed_end_time__gte=from_dtm)
    return q_set.values(weight=F('animal__weight'), last_breeding=F('animal__last_breeding'), age=F('animal__age'),
                        lactation_status=F('animal__lactation_status__value'),
                        animal_name=F('animal__name'), type=F('activity_type__value'),
                        time=F('performed_end_time'), milk_yield=F('individual_value')) \
        .order_by('performed_end_time')


def get_animal_activities_cow_page(from_dtm, c_id, a_id):
    q_set = ActivityList.objects.filter(animal=a_id, customer=c_id, performed_end_time__gte=from_dtm)
    return q_set.values(type=F('activity_type__value'), performed_time=F('performed_end_time')) \
        .annotate(total=Count('activity_type')). \
        order_by('performed_end_time')


def animal_alerts(a_id, c_id):
    from_date = datetime.date.today() - timedelta(int(LAST_WEEK))
    obj = HypernetNotification.objects.filter(created_datetime__gte=from_date,
                                              customer=c_id, device_id=a_id).count()
    return obj


def animals_herd_id(a_id, c_id):
    obj = Assignment.objects.filter(child=a_id, customer=c_id)
    herd = {}
    for i in obj:
        herd['herd_name'] = i.parent.name
        herd['herd_id'] = i.parent_id
        return herd


def herd_childs(h_id, c_id):
    animal_list = Assignment.objects.filter(parent_id=h_id).values_list('child', flat=True)
    q_set = Entity.objects.filter(customer_id=c_id, id__in=animal_list)
    return q_set


def get_animals(a_id, c_id, h_id):
    animal_list = []
    if a_id:
        animal_obj = Entity.objects.get(id=int(a_id))
        animal_list.append(util_animal_detail(animal_obj=animal_obj))
    elif h_id:
        animal_objs = herd_childs(h_id=h_id, c_id=c_id)
        for animal_obj in animal_objs:
            animal_list.append(util_animal_detail(animal_obj=animal_obj))
    elif a_id == None:
        animal_objs = Entity.objects.filter(customer=c_id, type=DeviceTypeEntityEnum.ANIMAL)
        for animal_obj in animal_objs:
            animal_list.append(util_animal_detail(animal_obj=animal_obj))
    return animal_list


def util_animal_detail(animal_obj):
    days = datetime.date.today() - timedelta(days=100)
    animal_detail = {}
    animal_detail['animal_details'] = animal_obj.animal_details_to_dict()
    animal_detail['last_week_alerts'] = animal_alerts(a_id=int(animal_obj.id), c_id=animal_obj.customer)
    animal_detail['herd_details'] = animals_herd_id(a_id=int(animal_obj.id), c_id=animal_obj.customer)
    animal_detail['milk_yield'] = get_animal_milk_yield(a_id=int(animal_obj.id), time_range=days,
                                                        c_id=animal_obj.customer)
    animal_detail['today_states'] = animal_states()
    return animal_detail


def animal_states():
    return {
        "rumination": '5h 0m 22s',
        "sitting": '8h 57m 1s',
        "feeding": '3h 1m 40s',
        "standing": '7h 33m 0s',

    }

def get_all_staff(c_id):
    q_set = User.objects.filter(customer=c_id, status=OptionsEnum.ACTIVE, is_active=True)
    return q_set.values(Name=F('first_name')).order_by('created_datetime')


def options_data(options_key):
    q_set = Options.objects.filter(key=options_key)
    return q_set.values('value')


def get_animals_milk_yield_monthly(customer_id,date_time,animal_id):
    animal_id= int(animal_id)
    next_date = (last_day_of_month(date_time) + timedelta(hours=23, minutes=59, seconds=59))
    prev_date = date_time.replace(day=1)
    data = Aggregation.objects.filter(customer_aggregations_id=customer_id,
                                      animal_id=animal_id,
                                      animal_id__isnull=False,
                                      feeding_value__isnull=True,
                                      created_datetime__gt=prev_date,
                                      created_datetime__lt=next_date)
    list = []
    for d in data:
        list.append(d.animal_milk_yield())
    return list


def get_herds_milk_yield_monthly(customer_id,date_time,herd_id):
    herd_id= int(herd_id)
    next_date = (last_day_of_month(date_time) + timedelta(hours=23, minutes=59, seconds=59))
    prev_date = date_time.replace(day=1)
    data = Aggregation.objects.filter(customer_aggregations_id=customer_id,
                                      herd_id=herd_id,
                                      animal_id__isnull=True,
                                      feeding_value__isnull=True,
                                      avg_milk_yield__isnull=False,
                                      created_datetime__gt=prev_date,
                                      created_datetime__lt=next_date)
    list = []
    for d in data:
        list.append(d.herd_milk_yield())
    return list


def get_herds_feed_yield_monthly(customer_id,date_time,herd_id):
    herd_id= int(herd_id)
    next_date = (last_day_of_month(date_time) + timedelta(hours=23, minutes=59, seconds=59))
    prev_date = date_time.replace(day=1)
    data = Aggregation.objects.filter(customer_aggregations_id=customer_id,
                                      herd_id=herd_id,
                                      animal_id__isnull=True,
                                      feeding_value__isnull=False,
                                      avg_milk_yield__isnull=True,
                                      created_datetime__gt=prev_date,
                                      created_datetime__lt=next_date)
    list = []
    for d in data:
        list.append(d.herd_feed())
    return list


def last_day_of_month(any_day):
    import datetime
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)  # this will never fail
    return next_month - datetime.timedelta(days=next_month.day)

def get_json_queryset(queryset,key1,key2,key3):
    return {key1:str(queryset[key1]),
            key2:queryset[key2],
            key3:queryset[key3]}

def get_random_date():
    from datetime import datetime
    d = datetime.now() + timedelta(days=randint(0, 4))
    return d.date()


def get_random_time():
    from datetime import datetime
    t = datetime.now() + timedelta(hours=randint(0, 3))
    t2 = t + timedelta(hours=1)
    return t.time(), t2.time()

def get_random_individual_value():
    return randint(15, 40)

def get_random_group_value():
    return randint(150, 400)

def util_staff_total(c_id):
    q_set_staff = User.objects.filter(customer=c_id, status=OptionsEnum.ACTIVE)
    staff_dict = {"total": len(q_set_staff), "caretaker": q_set_staff.filter(role_id=RoleTypeEnum.CARETAKER).count(),
                  "veterinarian": q_set_staff.filter(role_id=RoleTypeEnum.VET).count()}
    return staff_dict


def util_staff_list(c_id, date_range):
    q_set = ActivityList.objects.filter(customer=c_id, created_datetime__date__gte=date_range).distinct(
        'assigned_to_activity')
    data_list = []
    opt = {a_group: 0 for a_group in
           Options.objects.filter(key=IOA_ACTIVITY_ACTION_STATUS).values_list('value', flat=True)}
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


def get_user_activities_count(user):
    activity = ActivityList.objects.filter(assigned_to_activity=user.id)
    scheduling = Scheduling.objects.filter(assigned_to=user.id)
    return {"pending": activity.filter(action_status__value=hypernet.constants.PENDING).count(),
            "completed": activity.filter(action_status__value=hypernet.constants.COMPLETE).count(),
            "scheduled": scheduling.count()
            }


def get_staff_detail(c_id, staff=None):
    staff_list = []

    if staff:
        staff_objs = User.objects.filter(customer_id=c_id, id=staff)
    else:
        staff_objs = User.objects.filter(customer_id=c_id, is_active=True)

    for staff in staff_objs:
        user_dict = staff.user_as_json()
        user_dict.update(get_user_activities_count(staff))
        staff_list.append(user_dict)
    return staff_list


def util_get_caretakers(c_id):
    user_list = User.objects.filter(customer_id=c_id, is_active=True)
    return [{"id": user.id, "label": user.get_full_name()} for user in user_list]


def util_get_roles():
    roles_list = []
    vetenarian = Role.objects.get(id=RoleTypeEnum.VET)
    cartaker = Role.objects.get(id=RoleTypeEnum.CARETAKER)
    roles_list.append(vetenarian)
    roles_list.append(cartaker)
    return [{"id": role.id, "label": role.name} for role in roles_list]


###-------------------------------------------------------------------------------------------------------
## ENUM REPLACED BY STRINGS FOR TESTING


def get_complete_activities(customer_id, animal_id=None, staff_id=None):
    data = []
    if animal_id:
        list = ActivityList.objects.filter(customer_id=customer_id, animal_id=animal_id,
                                           action_status_id=IOAOPTIONSEnum.ACTIVITY_ACTION_STATUS_COMPLETE)
        groups = list.order_by().values('group').distinct()
        for g in groups:
            activity_list = ActivityList.objects.filter(group=int(g['group']))
            if activity_list[0].perform_individually:
                animal_data = [{"animal_id": o.animal.id,
                                "individual_value": o.individual_value} for o in activity_list]
            else:
                animal_data = [{"animal_id": o.animal.id} for o in activity_list]
            data.append(activity_list[0].to_dict(animal_data))


    elif staff_id:
        list = ActivityList.objects.filter(customer_id=customer_id, assigned_to_activity_id=staff_id,
                                           action_status__value=hypernet.constants.COMPLETE)
        #                                           IOAOPTIONSEnum.ACTIVITY_ACTION_STATUS_COMPLETE)
        groups = list.order_by().values('group').distinct()
        for g in groups:
            activity_list = ActivityList.objects.filter(group=int(g['group']))
            if activity_list[0].perform_individually:
                animal_data = [{"animal_id": o.animal.id,
                                "individual_value": o.individual_value} for o in activity_list]
            else:
                animal_data = [{"animal_id": o.animal.id} for o in activity_list]
            data.append(activity_list[0].to_dict(animal_data))
    else:
        list = ActivityList.objects.filter(customer_id=customer_id,
                                           action_status_id=IOAOPTIONSEnum.ACTIVITY_ACTION_STATUS_COMPLETE)
        groups = list.order_by().values('group').distinct()
        for g in groups:
            activity_list = ActivityList.objects.filter(group=int(g['group']))
            if activity_list[0].perform_individually:
                animal_data = [{"animal_id": o.animal.id,
                                "individual_value": o.individual_value} for o in activity_list]
            else:
                animal_data = [{"animal_id": o.animal.id} for o in activity_list]
            data.append(activity_list[0].to_dict(animal_data))

    return data


def get_pending_activities(customer_id, animal_id=None, staff_id=None):
    data = []
    if animal_id:
        list = ActivityList.objects.filter(customer_id=customer_id, animal_id=animal_id,
                                           action_status_id=IOAOPTIONSEnum.ACTIVITY_ACTION_STATUS_PENDING)
        # IOAOPTIONSEnum.ACTIVITY_ACTION_STATUS_PENDING)
        groups = list.order_by().values('group').distinct()
        for g in groups:
            activity_list = ActivityList.objects.filter(group=int(g['group']))
            if activity_list[0].perform_individually:
                animal_data = [{"animal_id": o.animal.id,
                                "individual_value": o.individual_value} for o in activity_list]
            else:
                animal_data = [{"animal_id": o.animal.id} for o in activity_list]
            data.append(activity_list[0].to_dict(animal_data))

    elif staff_id:
        list = ActivityList.objects.filter(customer_id=customer_id, assigned_to_activity_id=staff_id,
                                           action_status__value=hypernet.constants.PENDING)
        # IOAOPTIONSEnum.ACTIVITY_ACTION_STATUS_PENDING)
        groups = list.order_by().values('group').distinct()
        for g in groups:
            activity_list = ActivityList.objects.filter(group=int(g['group']))
            if activity_list[0].perform_individually:
                animal_data = [{"animal_id": o.animal.id,
                                "individual_value": o.individual_value} for o in activity_list]
            else:
                animal_data = [{"animal_id": o.animal.id} for o in activity_list]
            data.append(activity_list[0].to_dict(animal_data))
    else:
        list = ActivityList.objects.filter(customer_id=customer_id,
                                           action_status_id=IOAOPTIONSEnum.ACTIVITY_ACTION_STATUS_PENDING)
        groups = list.order_by().values('group').distinct()
        for g in groups:
            activity_list = ActivityList.objects.filter(group=int(g['group']))
            if activity_list[0].perform_individually:
                animal_data = [{"animal_id": o.animal.id,
                                "individual_value": o.individual_value} for o in activity_list]
            else:
                animal_data = [{"animal_id": o.animal.id} for o in activity_list]
            data.append(activity_list[0].to_dict(animal_data))

    return data


def get_incomplete_activities(customer_id, animal_id=None, staff_id=None):
    data = []
    if animal_id:
        list = ActivityList.objects.filter(customer_id=customer_id, animal_id=animal_id,
                                           action_status_id=IOAOPTIONSEnum.ACTIVITY_ACTION_STATUS_INCOMPLETE)
        groups = list.order_by().values('group').distinct()
        for g in groups:
            activity_list = ActivityList.objects.filter(group=int(g['group']))
            if activity_list[0].perform_individually:
                animal_data = [{"animal_id": o.animal.id,
                                "individual_value": o.individual_value} for o in activity_list]
            else:
                animal_data = [{"animal_id": o.animal.id} for o in activity_list]
            data.append(activity_list[0].to_dict(animal_data))

    elif staff_id:
        list = ActivityList.objects.filter(customer_id=customer_id, assigned_to_activity_id=staff_id,
                                           action_status__value=hypernet.constants.INCOMPLETE)
        # IOAOPTIONSEnum.ACTIVITY_ACTION_STATUS_PENDING)
        groups = list.order_by().values('group').distinct()
        for g in groups:
            activity_list = ActivityList.objects.filter(group=int(g['group']))
            if activity_list[0].perform_individually:
                animal_data = [{"animal_id": o.animal.id,
                                "individual_value": o.individual_value} for o in activity_list]
            else:
                animal_data = [{"animal_id": o.animal.id} for o in activity_list]
            data.append(activity_list[0].to_dict(animal_data))
    else:
        list = ActivityList.objects.filter(customer_id=customer_id,
                                           action_status_id=IOAOPTIONSEnum.ACTIVITY_ACTION_STATUS_INCOMPLETE)
        groups = list.order_by().values('group').distinct()
        for g in groups:
            activity_list = ActivityList.objects.filter(group=int(g['group']))
            if activity_list[0].perform_individually:
                animal_data = [{"animal_id": o.animal.id,
                                "individual_value": o.individual_value} for o in activity_list]
            else:
                animal_data = [{"animal_id": o.animal.id} for o in activity_list]
            data.append(activity_list[0].to_dict(animal_data))

    return data


def get_scheduled_activities(customer_id, animal_id=None, staff_id=None):
    """

    :param customer_id:
    :param animal_id:
    :param staff_id:
    :return: List of object dictionaries - using to_dict() to convert obj to dict
    """
    if animal_id:
        qs = Scheduling.objects.filter(customer_id=customer_id, animal__id=animal_id)
        data = [obj.to_dict() for obj in qs]

    elif staff_id:
        qs = Scheduling.objects.filter(customer_id=customer_id, assigned_to_id=staff_id)
        data = [obj.to_dict() for obj in qs]

    else:
        qs = Scheduling.objects.filter(customer_id=customer_id)
        data = [obj.to_dict() for obj in qs]
    return data


def get_cows_by_status(status, c_id, h_id=None):
    if h_id:
        herds = Assignment.objects.filter(parent=h_id).values('child_id')
        q_set = Entity.objects.filter(lactation_status__value=status,
                                      id__in=herds, customer_id=c_id,
                                      type=DeviceTypeEntityEnum.ANIMAL)
    else:
        q_set = Entity.objects.filter(lactation_status__value=status,
                                      customer_id=c_id,
                                      type=DeviceTypeEntityEnum.ANIMAL)
    data = [obj.animal_details_to_dict() for obj in q_set]
    return data


def get_cows_by_alerts(status, c_id, h_id=None):
    if h_id:
        herds = Assignment.objects.filter(parent=h_id).values('child_id')
        q_set = HypernetNotification.objects.filter(customer_id=c_id, id__in=herds,
                                                    violation_type__value=status,
                                                    device__type=DeviceTypeEntityEnum.ANIMAL)
    else:
        q_set = HypernetNotification.objects.filter(customer_id=c_id, violation_type__value=status,
                                                device__type=DeviceTypeEntityEnum.ANIMAL)

    data = [obj.device.animal_details_to_dict() for obj in q_set]
    return data


def get_total_cows(c_id, h_id=None):
    if h_id:
        q_set = Assignment.objects.filter(parent=h_id).values('child_id')
        return Entity.objects.filter(customer_id=c_id, type=DeviceTypeEntityEnum.ANIMAL,
                                     id__in=q_set).count()
    else:
        return Entity.objects.filter(customer_id=c_id, type=DeviceTypeEntityEnum.ANIMAL).count()


def get_total_cows_by_group(c_id, group, h_id=None):
    if h_id:
        q_set = Assignment.objects.filter(parent=h_id).values('child_id')
        return Entity.objects.filter(customer_id=c_id, type=DeviceTypeEntityEnum.ANIMAL,
                                     id__in=q_set, group__value=group).count()
    else:
        return Entity.objects.filter(customer_id=c_id, type=DeviceTypeEntityEnum.ANIMAL, group__value=group).count()


def get_this_week_top_cow(c_id, h_id=None):
    from django.utils import dateparse
    from datetime import datetime
    created_date = str(datetime.now().date())
    created_date_time = datetime.combine(dateparse.parse_date(created_date), datetime.min.time())
    next_date = (created_date_time) + timedelta(hours=23, minutes=59, seconds=59)
    prev_date = created_date_time - timedelta(days=7)
    if h_id:
        data = Aggregation.objects.filter(customer_aggregations_id=c_id,
                                          herd_id__isnull=False,
                                          herd_id__exact=h_id,  ##
                                      animal_id__isnull=False,
                                          feeding_value__isnull=True,
                                          created_datetime__gt=prev_date,
                                          created_datetime__lt=next_date)
    else:
        data = Aggregation.objects.filter(customer_aggregations_id=c_id,
                                          herd_id__isnull=False,
                                          animal_id__isnull=False,
                                          feeding_value__isnull=True,
                                          created_datetime__gt=prev_date,
                                          created_datetime__lt=next_date)
    if data:
        total_milk_yeild = data.values('animal_id', 'animal__name').annotate(
            milk_yeild=Sum('avg_milk_yield')).order_by('-milk_yeild')[:1]
        return total_milk_yeild[0]['animal_id'], total_milk_yeild[0]['animal__name'], total_milk_yeild[0]['milk_yeild']
    return 0, "", 0


def get_last_week_top_cow(c_id, h_id=None):
    from django.utils import dateparse
    from datetime import datetime
    created_date = str(datetime.now().date())
    created_date_time = datetime.combine(dateparse.parse_date(created_date), datetime.min.time())
    next_date = created_date_time + timedelta(hours=23, minutes=59, seconds=59)
    next_date = next_date - timedelta(days=7)
    prev_date = created_date_time - timedelta(days=14)
    if h_id:
        data = Aggregation.objects.filter(customer_aggregations_id=c_id,
                                          herd_id__isnull=False,
                                          herd_id__exact=h_id,  ##
                                      animal_id__isnull=False,
                                          feeding_value__isnull=True,
                                          created_datetime__gt=prev_date,
                                          created_datetime__lt=next_date)
    else:
        data = Aggregation.objects.filter(customer_aggregations_id=c_id,
                                          herd_id__isnull=False,
                                          animal_id__isnull=False,
                                          feeding_value__isnull=True,
                                          created_datetime__gt=prev_date,
                                          created_datetime__lt=next_date)

    if data:
        total_milk_yeild = data.values('animal_id', 'animal__name').annotate(
            milk_yeild=Sum('avg_milk_yield')).order_by('-milk_yeild')[:1]
        return total_milk_yeild[0]['animal_id'], total_milk_yeild[0]['animal__name'], total_milk_yeild[0]['milk_yeild']
    return 0, "", 0


def get_completed_activities_count(c_id, next_date, prev_date, activity_type):
    list = ActivityList.objects.filter(customer_id=c_id,
                                       activity_type__value=activity_type,
                                       action_status__value=constants.COMPLETE,
                                       scheduled_start_time__gt=prev_date,
                                       scheduled_start_time__lt=next_date
                                       )
    groups = list.order_by().values('group').distinct()
    return groups.count()


def get_incomplete_activities_count(c_id, next_date, prev_date, activity_type):
    list = ActivityList.objects.filter(customer_id=c_id,
                                       activity_type__value=activity_type,
                                       action_status__value=constants.INCOMPLETE,
                                       scheduled_start_time__gt=prev_date,
                                       scheduled_start_time__lt=next_date
                                       )
    groups = list.order_by().values('group').distinct()
    return groups.count()


def get_pending_activities_count(c_id, next_date, prev_date, activity_type):
    list = ActivityList.objects.filter(customer_id=c_id,
                                       activity_type__value=activity_type,
                                       action_status__value=constants.PENDING,
                                       scheduled_start_time__gt=prev_date,
                                       scheduled_start_time__lt=next_date
                                       )
    groups = list.order_by().values('group').distinct()
    return groups.count()


def get_scheduled_activities_count(c_id, next_date, prev_date, activity_type):
    list = Scheduling.objects.filter(customer_id=c_id,
                                     activity_type__value=activity_type)
    return list.count()


    ###-------------------------------------------------------------------------------------------------------
    ## ENUM REPLACED BY STRINGS FOR TESTING




def get_this_week_feed(c_id, h_id=None):
    from django.utils import dateparse
    from datetime import datetime
    created_date = str(datetime.now().date())
    created_date_time = datetime.combine(dateparse.parse_date(created_date), datetime.min.time())
    next_date = (created_date_time) + timedelta(hours=23, minutes=59, seconds=59)
    prev_date = created_date_time - timedelta(days=7)
    if h_id:
        data = Aggregation.objects.filter(customer_aggregations_id=c_id,
                                          herd_id__exact=h_id,
                                      animal_id__isnull=True,
                                      feeding_value__isnull=False,
                                      created_datetime__gt=prev_date,
                                      created_datetime__lt=next_date)
    else:
        data = Aggregation.objects.filter(customer_aggregations_id=c_id,
                                          herd_id__isnull=True,
                                          animal_id__isnull=True,
                                          feeding_value__isnull=False,
                                          created_datetime__gt=prev_date,
                                          created_datetime__lt=next_date)
    if data.count() > 0:
        total_milk_yeild = data.values('customer_aggregations_id').annotate(total=Sum('feeding_value'))
        result = {"customer_id": total_milk_yeild[0]['customer_aggregations_id'],
                                   "feed_consumed": total_milk_yeild[0]['total']}
        return result["feed_consumed"]
    return 0


def get_last_week_feed(c_id, h_id=None):
    from django.utils import dateparse
    from datetime import datetime
    created_date = str(datetime.now().date())
    created_date_time = datetime.combine(dateparse.parse_date(created_date), datetime.min.time())
    next_date = created_date_time + timedelta(hours=23, minutes=59, seconds=59)
    next_date = next_date - timedelta(days=7)
    prev_date = created_date_time - timedelta(days=14)
    if h_id:
        data = Aggregation.objects.filter(customer_aggregations_id=c_id,
                                          herd_id__exact=h_id,  ######
                                          animal_id__isnull=True,  ######
                                      feeding_value__isnull=False,
                                      created_datetime__gt=prev_date,
                                      created_datetime__lt=next_date)
    else:
        data = Aggregation.objects.filter(customer_aggregations_id=c_id,
                                          herd_id__isnull=True,
                                          animal_id__isnull=True,
                                          feeding_value__isnull=False,
                                          created_datetime__gt=prev_date,
                                          created_datetime__lt=next_date)

    if data.count() > 0:
        total_milk_yeild = data.values('customer_aggregations_id').annotate(total=Sum('feeding_value'))
        result = {"customer_id": total_milk_yeild[0]['customer_aggregations_id'],
                  "feed_consumed": total_milk_yeild[0]['total']}
        return result["feed_consumed"]
    return 0


def get_customer_current_milk_yield(c_id, h_id=None):
    from django.utils import dateparse
    from datetime import datetime
    created_date = str(datetime.now().date())
    created_date_time = datetime.combine(dateparse.parse_date(created_date), datetime.min.time())
    next_date = created_date_time + timedelta(hours=23, minutes=59, seconds=59)
    prev_date = created_date_time.replace(day=1)
    if h_id:
        data = Aggregation.objects.filter(customer_aggregations=c_id,
                                          herd_id__exact=h_id,
                                          animal_id__isnull=True,
                                          feeding_value__isnull=True,
                                          avg_milk_yield__isnull=False,
                                          created_datetime__gt=prev_date,
                                          created_datetime__lt=next_date)
    else:
        data = Aggregation.objects.filter(customer_aggregations=c_id,
                                      herd_id__isnull=True,
                                      animal_id__isnull=True,
                                      feeding_value__isnull=True,
                                      avg_milk_yield__isnull=False,
                                      created_datetime__gt=prev_date,
                                      created_datetime__lt=next_date)

    if data:
        total_milk_yeild = data.values('customer_aggregations_id').annotate(total=Sum('avg_milk_yield'))
        result = {"customer_id": total_milk_yeild[0]['customer_aggregations_id'],
                  "milk_yield": total_milk_yeild[0]['total']}
        return result['milk_yield']
    return 0


def get_this_week_top_herd(c_id):
    from django.utils import dateparse
    from datetime import datetime
    created_date = str(datetime.now().date())
    created_date_time = datetime.combine(dateparse.parse_date(created_date), datetime.min.time())
    next_date = (created_date_time) + timedelta(hours=23, minutes=59, seconds=59)
    prev_date = created_date_time - timedelta(days=7)
    data = Aggregation.objects.filter(customer_aggregations_id=c_id,
                                      herd_id__isnull=False,
                                      animal_id__isnull=True,
                                      feeding_value__isnull=False,
                                      avg_milk_yield__isnull=True,
                                      created_datetime__gt=prev_date,
                                      created_datetime__lt=next_date)
    if data:
        total_feed = data.values('herd_id', 'herd__name').annotate(
            feed_yield=Sum('feeding_value')).order_by('-feed_yield')[:1]
        return total_feed[0]['herd_id'], total_feed[0]['herd__name'], total_feed[0]['feed_yield']
    return 0, "", 0


def get_last_week_top_herd(c_id):
    from django.utils import dateparse
    from datetime import datetime
    created_date = str(datetime.now().date())
    created_date_time = datetime.combine(dateparse.parse_date(created_date), datetime.min.time())
    next_date = created_date_time + timedelta(hours=23, minutes=59, seconds=59)
    next_date = next_date - timedelta(days=7)
    prev_date = created_date_time - timedelta(days=14)
    data = Aggregation.objects.filter(customer_aggregations_id=c_id,
                                      herd_id__isnull=False,
                                      animal_id__isnull=True,
                                      feeding_value__isnull=False,
                                      avg_milk_yield__isnull=True,
                                      created_datetime__gt=prev_date,
                                      created_datetime__lt=next_date)
    if data:
        total_feed = data.values('herd_id', 'herd__name').annotate(
            feed_yield=Sum('feeding_value')).order_by('-feed_yield')[:1]
        return total_feed[0]['herd_id'], total_feed[0]['herd__name'], total_feed[0]['feed_yield']
    return 0, "", 0


def herd_milk_yield_monthly(customer_id):
    if not customer_id:
        return 'customer id not given'
    else:
        customer_id = int(customer_id)
        herds_data = Aggregation.objects.filter(customer_aggregations_id=customer_id,
                                                animal_id__isnull=True,
                                                herd_id__isnull=False,
                                                feeding_value__isnull=True,
                                                avg_milk_yield__isnull=False). \
            annotate(month=TruncMonth('created_datetime')) \
            .values('month', 'herd_id', 'herd__name').annotate(total=Sum('avg_milk_yield')) \
            .order_by('-month')
        if herds_data:
            herd_milk = [{"herd_id": x['herd_id'], "name": x['herd__name'], "total": x['total'],
                          "month": calendar.month_name[x['month'].month] + '/' + str(x['month'].year),
                          "details": get_herds_milk_yield_monthly(customer_id,
                                                                  x['month'],
                                                                  x['herd_id'])} for x in herds_data]
            return herd_milk
        elif not herds_data:
            return 'No_data'


def animal_milk_yield_monthly(customer_id):
    if not customer_id:
        return 'customer id not given'
    else:
        customer_id = int(customer_id)
        animals_data = Aggregation.objects.filter(customer_aggregations_id=customer_id,
                                                  animal_id__isnull=False,
                                                  feeding_value__isnull=True,
                                                  avg_milk_yield__isnull=False). \
            annotate(month=TruncMonth('created_datetime')) \
            .values('month', 'animal_id', 'animal__name', 'herd__name').annotate(total=Sum('avg_milk_yield')) \
            .order_by('-month')
        if animals_data:
            milk_yield_data = [{"animal_id": x['animal_id'],
                                "name": x['animal__name'],
                                "herd": x['herd__name'],
                                "total": x['total'],
                                "month": calendar.month_name[x['month'].month] + '/' + str(x['month'].year),
                                "details": get_animals_milk_yield_monthly(customer_id,
                                                                          x['month'],
                                                                          x['animal_id'])}
                               for x in animals_data]
            return milk_yield_data
        elif not animals_data:
            return 'No_data'


def send_sms_util():
    pass


def util_add_cows(request):
    name = get_data_param(request, 'name', None)
    lactation_days = get_data_param(request, 'lactation_days', None)
    last_breeding = get_data_param(request, 'last_breeding', None)
    age = get_data_param(request, 'age', None)
    weight = get_data_param(request, 'weight', None)
    type_id = get_data_param(request, 'type', None)
    customer = get_data_param(request, 'customer', None)
    module_id = get_data_param(request, 'module', None)
    status_id = get_data_param(request, 'status', None)
    modified_by = get_data_param(request, 'modified_by', None)
    breed = get_data_param(request, 'breed', None)
    lactation_status = get_data_param(request, 'lactation_status', None)
    group = get_data_param(request, 'group', None)
    herd_id = get_data_param(request, 'herd', None)

    cow_data = Entity(
        name=name,
        lactation_days=lactation_days,
        last_breeding=last_breeding,
        age=age,
        weight=weight,
        type=DeviceType.objects.get(id=type_id),
        customer=Customer.objects.get(id=customer),
        module=Module.objects.get(id=module_id),
        status=Options.objects.get(id=status_id),
        modified_by=User.objects.get(id=modified_by),
        breed=Options.objects.get(id=breed),
        lactation_status=Options.objects.get(id=lactation_status),
        group=Options.objects.get(id=group),
    )
    cow_data.save()

    cow_assignment = Assignment(
        name=str(herd_id) + Customer.objects.get(id=customer).name,
        comments='some comment',
        customer=Customer.objects.get(id=customer),
        parent=Entity.objects.get(id=herd_id),
        child=Entity.objects.get(id=cow_data.id),
        modified_by=User.objects.get(id=modified_by),
        module=Module.objects.get(id=module_id),
        status=Options.objects.get(id=status_id),
        type=DeviceType.objects.get(id=DeviceCategoryEnum.ASSIGNMENT),
    )
    cow_assignment.save()
    return 'Cow_added Succesfully' + 'Animal Added to Herd'


# TODO remove this util along with End-point (Moved to Hypernet/entity)
def util_get_devices_dropdown(c_id, assignment=False):
    q_set = CustomerDevice.objects.filter(customer=c_id, status=OptionsEnum.ACTIVE, assigned=assignment)
    return list(q_set.values(device_name=F('device_id'), device=F('id')))


#TODO Remove this util (Use it from Hypernet)
def update_alert_status(id, c_id, status, m_id):
    update_status = False
    try:
        q_set = HypernetNotification.objects.filter(id=id, customer=c_id, module_id=int(m_id))
        opt_obj = Options.objects.get(key=HYPERNET_ALERTS_STATUS, value=status)
        q_set.update(status=opt_obj)
        update_status = True
    except:
        pass
    return update_status


def generate_word(length):
    word = ""
    VOWELS = "aeiou"
    CONSONANTS = "".join(set(string.ascii_lowercase) - set(VOWELS))
    for i in range(length):
        if i % 2 == 0:
            word += random.choice(CONSONANTS)
        else:
            word += random.choice(VOWELS)
    return word