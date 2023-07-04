import datetime
from dateutil.parser import parse
from django.db.models.functions import Concat
from urllib3.connectionpool import xrange
from django.utils import timezone
import traceback
from hypernet.enums import OptionsEnum, ModuleEnum, DeviceTypeEntityEnum, IOFOptionsEnum, DeviceTypeAssignmentEnum
from hypernet.models import Assignment

from iof.models import ActivitySchedule, Activity, ActivityData, ActivityQueue, BinCollectionData, Entity


def get_dates(from_date, to_date, day_list=[]):
    tmp_list = list()
    date_list = list()

    for x in xrange((to_date - from_date).days + 1):
        tmp_list.append(from_date + datetime.timedelta(days=x))
    for date_record in tmp_list:
        if date_record.weekday() in day_list:
            date_list.append(date_record.strftime('%Y-%m-%d'))
    return date_list


def get_conflicts(preferences, data, days_list, start_date=None):
    primary_entity = data.get('primary_entity')
    actor = data.get('actor')
    activity_start_time = data.get('activity_start_time')
    if start_date is None:
        start_date = data.get('start_date')
    end_date = data.get('end_date')
    try:
        # For recurring schedule, days list will be calculated and conflict will be searched.
        if end_date:
            dates_list = get_dates(from_date=start_date, to_date=end_date, day_list=days_list)
            for d in dates_list:
                start_time = (parse(d +' '+str(activity_start_time))).replace(tzinfo=timezone.utc)
                end_time = (start_time + datetime.timedelta(minutes=preferences.average_activity_time))
                try:
                    # DRIVER QUEUE.
                    aq = ActivityQueue.objects.get(actor_id=actor.id,
                                                   activity_schedule__schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                   activity_datetime__range=[start_time, end_time]).activity_schedule

                    return True, aq
                except ActivityQueue.DoesNotExist:
                    traceback.print_exc()
                    try:
                        # TRUCK QUEUE.
                        aq = ActivityQueue.objects.get(primary_entity_id=primary_entity.id,
                                                       activity_schedule__schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                       activity_datetime__range=[start_time, end_time]).activity_schedule
                        return True, aq
                    except ActivityQueue.DoesNotExist:
                        traceback.print_exc()
                        pass

                # Reversing time stamps to check conflict in past
                end_time = (start_time - datetime.timedelta(minutes=preferences.average_activity_time))
                try:
                    # DRIVER QUEUE.
                    aq = ActivityQueue.objects.get(actor_id=actor.id,
                                                   activity_schedule__schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                   activity_datetime__range=[end_time, start_time]).activity_schedule

                    return True, aq
                except ActivityQueue.DoesNotExist:
                    traceback.print_exc()
                    try:
                        # TRUCK QUEUE.
                        aq = ActivityQueue.objects.get(primary_entity_id=primary_entity.id,
                                                       activity_schedule__schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                       activity_datetime__range=[end_time, start_time]).activity_schedule
                        return True, aq
                    except ActivityQueue.DoesNotExist:
                        traceback.print_exc()
                        pass

                # ACTIVITY PART FOR CONFLICTS.
                end_time = (start_time + datetime.timedelta(minutes=preferences.average_activity_time))
                try:
                    # DRIVER ACTIVITY
                    act = Activity.objects.get(actor_id=actor.id,
                                               activity_start_time__range=[start_time, end_time],
                                               activity_status_id__in=[IOFOptionsEnum.ACCEPTED,
                                                                       IOFOptionsEnum.PENDING,
                                                                       IOFOptionsEnum.REVIEWED,
                                                                       IOFOptionsEnum.FAILED,
                                                                       IOFOptionsEnum.REJECTED,
                                                                       ])
                    return True, None
                except:
                    try:
                        # TRUCK ACTIVITY
                        act = Activity.objects.get(primary_entity_id=primary_entity.id,
                                                   activity_start_time__range=[start_time, end_time],
                                                   activity_status_id__in=[
                                                       IOFOptionsEnum.ACCEPTED,
                                                       IOFOptionsEnum.PENDING,
                                                       IOFOptionsEnum.REVIEWED,
                                                       IOFOptionsEnum.FAILED,
                                                       IOFOptionsEnum.REJECTED,
                                                   ])
                        return True, None
                    except:
                        pass
                        # return False, None

                end_time = (start_time - datetime.timedelta(minutes=preferences.average_activity_time))
                try:
                    # DRIVER ACTIVITY
                    act = Activity.objects.get(actor_id=actor.id,
                                               activity_start_time__range=[end_time, start_time],
                                               activity_status_id__in=[IOFOptionsEnum.ACCEPTED,
                                                                       IOFOptionsEnum.PENDING,
                                                                       IOFOptionsEnum.REVIEWED,
                                                                       IOFOptionsEnum.FAILED,
                                                                       IOFOptionsEnum.REJECTED,
                                                                       ])
                    return True, None
                except:
                    try:
                        # TRUCK ACTIVITY
                        act = Activity.objects.get(primary_entity_id=primary_entity.id,
                                                   activity_start_time__range=[end_time, start_time],
                                                   activity_status_id__in=[
                                                       IOFOptionsEnum.ACCEPTED,
                                                       IOFOptionsEnum.PENDING,
                                                       IOFOptionsEnum.REVIEWED,
                                                       IOFOptionsEnum.FAILED,
                                                       IOFOptionsEnum.REJECTED,
                                                   ])
                        return True, None
                    except:
                        pass


                # ACTIVITY filter for both truck or driver.
                try:
                    # TODO DRY RUN AND REFACTOR
                    act = Activity.objects.get(actor_id=actor.id, activity_status_id__in=[IOFOptionsEnum.SUSPENDED,
                                                                                          IOFOptionsEnum.RUNNING])
                except:
                    try:
                        act = Activity.objects.get(primary_entity_id=primary_entity.id,
                                                   activity_status_id__in=[IOFOptionsEnum.SUSPENDED,
                                                                           IOFOptionsEnum.RUNNING])
                    except:
                        return False, None
                        # DRIVER CHECK FOR ACTIVITY CONFLICT
                try:
                    end_time = (act.start_datetime + datetime.timedelta(minutes=preferences.average_activity_time))
                    Activity.objects.get(actor_id=actor.id, activity_status_id__in=[IOFOptionsEnum.SUSPENDED,
                                                                                    IOFOptionsEnum.RUNNING],
                                         start_datetime__range=[start_time, end_time])
                    return True, None
                except:
                    end_time = (act.start_datetime - datetime.timedelta(minutes=preferences.average_activity_time))
                    try:
                        Activity.objects.get(actor_id=actor.id,
                                             activity_status_id__in=[IOFOptionsEnum.SUSPENDED,
                                                                     IOFOptionsEnum.RUNNING],
                                             start_datetime__range=[end_time, start_time])
                        return True, None
                    except:
                        pass
                # TRUCK CHECK FOR ACTIVITY CONFLICT
                try:
                    end_time = (act.start_datetime + datetime.timedelta(minutes=preferences.average_activity_time))
                    Activity.objects.get(primary_entity_id=primary_entity.id,
                                         activity_status_id__in=[IOFOptionsEnum.SUSPENDED,
                                                                 IOFOptionsEnum.RUNNING],
                                         start_datetime__range=[start_time, end_time])
                    return True, None
                except:
                    end_time = (act.start_datetime - datetime.timedelta(minutes=preferences.average_activity_time))
                    try:
                        Activity.objects.get(primary_entity_id=primary_entity.id,
                                             activity_status_id__in=[IOFOptionsEnum.SUSPENDED,
                                                                     IOFOptionsEnum.RUNNING],
                                             start_datetime__range=[end_time, start_time])
                        return True, None
                    except:
                        return False, None

        # For once schedule, datetime will be constructed and checked against activity queue for conflicts
        else:
            #TODO Refactor for Driver and Truck conflicts.
            activity_datetime = str(start_date) + ' ' + str(activity_start_time)
            activity_datetime = parse(activity_datetime)
            activity_datetime = activity_datetime.replace(tzinfo=timezone.utc)
            end_time = (activity_datetime + datetime.timedelta(minutes=preferences.average_activity_time))
            # Reversing time stamps to check conflict in future
            try:
                # DRIVER QUEUE.
                aq = ActivityQueue.objects.get(actor_id=actor.id,
                                               activity_schedule__schedule_activity_status_id=OptionsEnum.ACTIVE,
                                               activity_datetime__range=[activity_datetime, end_time]).activity_schedule

                return True, aq
            except:
                try:
                    # TRUCK QUEUE.
                    aq = ActivityQueue.objects.get(primary_entity_id=primary_entity.id,
                                                   activity_schedule__schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                   activity_datetime__range=[activity_datetime, end_time]).activity_schedule
                    return True, aq
                except:
                    pass

            #ACTIVITY QUEUE ON COMMING schedules conflicts

            # Reversing time stamps to check conflict in past
            end_time = (activity_datetime - datetime.timedelta(minutes=preferences.average_activity_time))
            try:
                # DRIVER QUEUE.
                aq = ActivityQueue.objects.get(actor_id=actor.id,
                                               activity_schedule__schedule_activity_status_id=OptionsEnum.ACTIVE,
                                               activity_datetime__range=[end_time, activity_datetime]).activity_schedule

                return True, aq
            except:
                try:
                    # TRUCK QUEUE.
                    aq = ActivityQueue.objects.get(primary_entity_id=primary_entity.id,
                                                   activity_schedule__schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                   activity_datetime__range=[end_time, activity_datetime]).activity_schedule
                    return True, aq
                except:
                    pass

            #ACTIVITY PART FOR CONFLICTS.
            end_time = (activity_datetime + datetime.timedelta(minutes=preferences.average_activity_time))
            try:
                # DRIVER ACTIVITY
                act = Activity.objects.get(actor_id=actor.id, activity_start_time__range=[activity_datetime, end_time],
                                           activity_status_id__in=[IOFOptionsEnum.ACCEPTED,
                                                                   IOFOptionsEnum.PENDING,
                                                                   IOFOptionsEnum.REVIEWED,
                                                                   IOFOptionsEnum.FAILED,
                                                                   IOFOptionsEnum.REJECTED,
                                                                   ])
                return True, None
            except:
                try:
                    # TRUCK ACTIVITY
                    act = Activity.objects.get(primary_entity_id=primary_entity.id,
                                               activity_start_time__range=[activity_datetime, end_time],
                                               activity_status_id__in=[
                                                                       IOFOptionsEnum.ACCEPTED,
                                                                       IOFOptionsEnum.PENDING,
                                                                       IOFOptionsEnum.REVIEWED,
                                                                       IOFOptionsEnum.FAILED,
                                                                       IOFOptionsEnum.REJECTED,
                                                                       ])
                    return True, None
                except:
                    pass

            end_time = (activity_datetime - datetime.timedelta(minutes=preferences.average_activity_time))
            try:
                # DRIVER ACTIVITY
                act = Activity.objects.get(actor_id=actor.id,
                                           activity_start_time__range=[end_time, activity_datetime],
                                           activity_status_id__in=[IOFOptionsEnum.ACCEPTED,
                                                                   IOFOptionsEnum.PENDING,
                                                                   IOFOptionsEnum.REVIEWED,
                                                                   IOFOptionsEnum.FAILED,
                                                                   IOFOptionsEnum.REJECTED,
                                                                   ])
                return True, None
            except:
                try:
                    # TRUCK ACTIVITY
                    act = Activity.objects.get(primary_entity_id=primary_entity.id,
                                               activity_start_time__range=[end_time, activity_datetime],
                                               activity_status_id__in=[
                                                   IOFOptionsEnum.ACCEPTED,
                                                   IOFOptionsEnum.PENDING,
                                                   IOFOptionsEnum.REVIEWED,
                                                   IOFOptionsEnum.FAILED,
                                                   IOFOptionsEnum.REJECTED,
                                               ])
                    return True, None
                except:
                    pass
                # return False, None

            #Running/suspended ACTIVITY filter for both truck or driver.
            try:
                act = Activity.objects.get(actor_id=actor.id, activity_status_id__in=[IOFOptionsEnum.SUSPENDED,
                                                                                      IOFOptionsEnum.RUNNING])
                end_time = (act.start_datetime + datetime.timedelta(minutes=preferences.average_activity_time))
                if act.start_datetime <= activity_datetime <= end_time:
                    return True, None
                else:
                    try:
                        act = Activity.objects.get(primary_entity_id=primary_entity.id,
                                                   activity_status_id__in=[IOFOptionsEnum.SUSPENDED,
                                                                           IOFOptionsEnum.RUNNING])
                        end_time = (act.start_datetime + datetime.timedelta(minutes=preferences.average_activity_time))
                        if act.start_datetime <= activity_datetime <= end_time:
                            return True, None
                        else:
                            return False, None
                    except:
                        return False, None

            except:
                try:
                    act = Activity.objects.get(primary_entity_id=primary_entity.id, activity_status_id__in=[IOFOptionsEnum.SUSPENDED,
                                                                                          IOFOptionsEnum.RUNNING])
                    end_time = (act.start_datetime + datetime.timedelta(minutes=preferences.average_activity_time))
                    if act.start_datetime <= activity_datetime <= end_time:
                        return True, None
                    else:
                        return False, None
                except:
                    return False, None

                #TODO Reverse date time check.
                #DRIVER CHECK FOR ACTIVITY CONFLICT
    except:
        traceback.print_exc()
        return True, None


def util_create_activity_queue(serializer, days_list, start_date=None):
    if serializer:
        if serializer.end_date:
            if start_date:
                # if Activity.objects.filter(activity_schedule_id=serializer.id, activity_start_time__date=start_date).exists():
                #     start_date = start_date + datetime.timedelta(days=1)
                dates_list = get_dates(from_date=start_date, to_date=serializer.end_date, day_list=days_list)
            else:
                dates_list = get_dates(from_date=serializer.start_date, to_date=serializer.end_date, day_list=days_list)

            for days in dates_list:
                try:
                    date_time = days + ' ' + str(serializer.activity_start_time)
                    date_time = parse(date_time)
                    date_time = date_time.replace(tzinfo=timezone.utc)
                    if date_time <= timezone.now():
                        continue
                    scheduled_activity = ActivityQueue()
                    scheduled_activity.activity_schedule_id = serializer.id
                    scheduled_activity.activity_datetime = date_time
                    scheduled_activity.primary_entity_id = serializer.primary_entity_id
                    scheduled_activity.actor_id = serializer.actor_id
                    scheduled_activity.action_items = serializer.action_items
                    scheduled_activity.activity_end_point_id = serializer.activity_end_point_id
                    scheduled_activity.customer_id = serializer.customer_id
                    scheduled_activity.module_id = serializer.module_id
                    scheduled_activity.activity_check_point_id = serializer.activity_check_point_id
                    scheduled_activity.save()

                except:
                    traceback.print_exc()

        else:
            activity_datetime = str(serializer.start_date) + ' ' + str(serializer.activity_start_time)
            activity_datetime = parse(activity_datetime)
            activity_datetime = activity_datetime.replace(tzinfo=timezone.utc)
            scheduled_activity = ActivityQueue()
            scheduled_activity.activity_schedule_id = serializer.id
            # activity_datetime = activity_datetime
            scheduled_activity.activity_datetime = activity_datetime
            scheduled_activity.primary_entity_id = serializer.primary_entity_id
            scheduled_activity.actor_id = serializer.actor_id
            scheduled_activity.action_items = serializer.action_items
            scheduled_activity.activity_end_point_id = serializer.activity_end_point_id
            scheduled_activity.customer_id = serializer.customer_id
            scheduled_activity.module_id = serializer.module_id
            scheduled_activity.activity_check_point_id = serializer.activity_check_point_id
            scheduled_activity.save()
    
    return True


def util_get_schedules(c_id, t_id, d_id, sch_id, s_id):

    if t_id:
        schedules = ActivitySchedule.objects.filter(primary_entity_id=t_id, customer_id=c_id)

    elif d_id:
        schedules = ActivitySchedule.objects.filter(actor_id=d_id, customer_id=c_id)

    elif s_id:
        schedules = ActivitySchedule.objects.filter(schedule_activity_status_id=s_id, customer_id=c_id)

    elif sch_id:
        schedules = ActivitySchedule.objects.filter(pk=sch_id)

    else:
        schedules = ActivitySchedule.objects.filter(customer_id=c_id, module_id=ModuleEnum.IOL)

    return schedules.order_by('-created_datetime')


def suspend_activity_schedule(schedule_id):
    ActivityQueue.objects.filter(activity_schedule_id=schedule_id).delete()

def check_suspend(schedule_id):
    if ActivityQueue.objects.filter(activity_schedule_id=schedule_id).count() > 0:
        suspend = True
    else:
        suspend = False

    try:
        Activity.objects.get(activity_schedule_id=schedule_id,
                             activity_status_id__in=[IOFOptionsEnum.ACCEPTED, IOFOptionsEnum.RUNNING,
                                                     IOFOptionsEnum.SUSPENDED, IOFOptionsEnum.FAILED])
        suspend = False

    except Activity.DoesNotExist:
        print('Activity Does not exists')
        suspend = True

    except Activity.MultipleObjectsReturned:
        print('multiple objs returned')
        suspend = False

    return suspend

def util_get_activities(c_id, t_id, d_id, sch_id, s_id, a_id, start_date, end_date):

    if t_id:
        activities = Activity.objects.filter(primary_entity_id=t_id, customer_id=c_id)

    elif d_id:
        activities = Activity.objects.filter(actor_id=d_id, customer_id=c_id)

    elif a_id:
        activities = Activity.objects.filter(pk=a_id)

    elif sch_id:
        activities = Activity.objects.filter(activity_schedule_id=sch_id, customer_id=c_id)

    else:
        activities = Activity.objects.filter(customer_id=c_id, module_id=ModuleEnum.IOL)
    
    if s_id:
        activities = Activity.objects.filter(activity_status_id=s_id, customer_id=c_id)

    if start_date and end_date:
        s_date = parse(start_date)
        e_date = parse(end_date)
        e_date = e_date + datetime.timedelta(days=1)
        activities = activities.filter(created_datetime__range=[s_date, e_date])

    return activities.order_by('-created_datetime')


def util_get_activity_data(c_id, t_id, d_id, s_id, a_id, start_date, end_date):
    if t_id:
        activity_data = ActivityData.objects.filter(primary_entity_id=t_id, customer_id=c_id)

    elif d_id:
        activity_data = ActivityData.objects.filter(actor_id=d_id, customer_id=c_id)

    elif s_id:
        activity_data = ActivityData.objects.filter(activity_status_id=s_id, customer_id=c_id)

    elif a_id:
        activity_data = ActivityData.objects.filter(scheduled_activity_id=a_id, customer_id=c_id)

    else:
        activity_data = ActivityData.objects.filter(customer_id=c_id, module_id=ModuleEnum.IOL)

    if start_date and end_date:
        s_date = parse(start_date)
        e_date = parse(end_date)
        activity_data = activity_data.filter(start_datetime__range=[s_date, e_date])

    return activity_data.order_by('-timestamp')


def util_get_bins_location(action_items, activity_id=None):
    bins_list = action_items.split(',')
    result = []

    for id in bins_list:
        try:
            obj = Entity.objects.get(pk=id, type_id=DeviceTypeEntityEnum.BIN)
        except:
            # For debugging
            # traceback.print_exc()
            return None
        try:
            contract = Assignment.objects.get(parent_id=obj.id, type_id= DeviceTypeAssignmentEnum.CONTRACT_ASSIGNMENT, status_id=OptionsEnum.ACTIVE).child
            area = Assignment.objects.get(child_id=contract.id, type_id=DeviceTypeAssignmentEnum.AREA_CONTRACT_ASSIGNMENT, status_id=OptionsEnum.ACTIVE).parent
        except:
            # For debugging
            # traceback.print_exc()
            return None
        try:
            bin_data = BinCollectionData.objects.get(action_item_id=id, activity_id=activity_id)
            data = {'id': obj.id, 'label': obj.name, 'entity_location': obj.source_latlong,
                    'status': bin_data.status.label if bin_data else None,
                    'contract_name': contract.name,
                    'area': area.name,
                    'weight': bin_data.weight,
                    'invoice': bin_data.invoice if bin_data else None,
                    'type': obj.entity_sub_type.label if obj.entity_sub_type else None,
                    'client': obj.client.party_code if obj.client else None,
                    'client_name': obj.client.name if obj.client else None,
                    'verified': bin_data.verified if bin_data else None,
                    'entity_sub_type': bin_data.contract.leased_owned.label if bin_data.contract else None,
                    'timestamp': bin_data.timestamp
                    }
            if bin_data.supervisor:
                data['supervisor'] = bin_data.supervisor.name
            result.append(data)
    
        except Exception as e:
            # traceback.print_exc()
            result.append({'id': obj.id, 'label': obj.name, 'entity_location': obj.source_latlong,
                           'status': 'Pending',
                           'contract_name': contract.name,
                           'area': area.name,
                           'weight': None ,
                           'invoice': None,
                           'type':None,
                           'client': obj.client.party_code if obj.client else None,
                           'client_name': obj.client.name if obj.client else None,
                           'verified': None,
                           'entity_sub_type': None,
                           'timestamp': None
                           }
                          )

    return result


def util_get_bin_with_location(bin):
    if bin:
        obj = Entity.objects.get(pk=bin)
        return {'id': obj.id, 'label': obj.name, 'type': obj.type.id, 'entity_sub_type': obj.entity_sub_type.label if obj.entity_sub_type else None}


def util_upcoming_activities(c_id, sch_id, t_id, d_id, start_date, end_date):

    if t_id:
        activity_queue = ActivityQueue.objects.filter(primary_entity_id=t_id, customer_id=c_id, activity_schedule__schedule_activity_status_id = OptionsEnum.ACTIVE).order_by('activity_datetime')

    elif sch_id:
        activity_queue = ActivityQueue.objects.filter(activity_schedule_id=sch_id, customer_id=c_id, activity_schedule__schedule_activity_status_id = OptionsEnum.ACTIVE).order_by('activity_datetime')

    elif d_id:
        activity_queue = ActivityQueue.objects.filter(actor_id=d_id, customer_id=c_id, activity_schedule__schedule_activity_status_id = OptionsEnum.ACTIVE).order_by('activity_datetime')

    else:
        activity_queue = ActivityQueue.objects.filter(customer_id=c_id, activity_schedule__schedule_activity_status_id = OptionsEnum.ACTIVE).order_by('activity_datetime')

    if start_date and end_date:
        s_date = parse(start_date)
        e_date = parse(end_date)
        activity_queue.filter(activity_datetime__range=[s_date, e_date])

    return activity_queue


def util_get_bins_activities(b_id, s_id, start_date, end_date):
    if b_id:
        activtiy = Activity.objects.filter(action_items__exact=b_id)
    elif s_id:
        activtiy = Activity.objects.filter(activity_status_id=s_id, action_items__exact=b_id)

    if start_date and end_date:
        s_date = parse(start_date)
        e_date = parse(end_date)
        activtiy.filter(activity_datetime__range=[s_date, e_date])

    return activtiy



def util_get_bins_action_data(c_id, b_id, s_id, start_date, end_date):
    if b_id:
        bin_actions_data = ActivityData.objects.filter(action_items_id=b_id)
    elif s_id:
        bin_actions_data = ActivityData.objects.filter(activity_status_id=s_id, action_item_id=b_id)
    else:
        bin_actions_data = ActivityData.objects.filter(customer_id=c_id)

    if start_date and end_date:
        s_date = parse(start_date)
        e_date = parse(end_date)
        bin_actions_data = bin_actions_data.filter(timestamp__range=[s_date, e_date])

    return bin_actions_data


def util_get_bins_collection_data(c_id, b_id, s_id, a_id, sup_id, d_id, t_id, start_date, end_date):
    if b_id:
        bin_collection_data = BinCollectionData.objects.filter(action_item_id=b_id)

    elif s_id:
        bin_collection_data = BinCollectionData.objects.filter(status_id=s_id, action_item_id=b_id)

    elif sup_id:
        bin_collection_data = BinCollectionData.objects.filter(supervisor_id=sup_id)

    elif d_id:
        bin_collection_data = BinCollectionData.objects.filter(actor_id=d_id)

    elif t_id:
        bin_collection_data = BinCollectionData.objects.filter(entity_id=t_id)

    elif a_id:
        bin_collection_data = BinCollectionData.objects.filter(activity_id=a_id)

    else:
        bin_collection_data = BinCollectionData.objects.filter(customer_id=c_id)

    if start_date and end_date:
        s_date = parse(start_date)
        e_date = parse(end_date)
        bin_collection_data.filter(timestamp__range=[s_date, e_date])

    return bin_collection_data


def util_get_schedule_total_count(sch_id):

    count_activity = Activity.objects.filter(activity_schedule_id=sch_id).count()

    total_count_activity = Activity.objects.filter(activity_schedule_id=sch_id, activity_status_id__in=[IOFOptionsEnum.ABORTED,
                                                                                                        IOFOptionsEnum.COMPLETED]).count()

    count_queue = ActivityQueue.objects.filter(activity_schedule_id=sch_id).count()

    total = count_activity + count_queue
    if total > 0:
        return  (total_count_activity/total) * 100
    else:
        return 0


