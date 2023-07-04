import calendar
import json
import datetime
from dateutil.parser import parse
from django.db.models import ExpressionWrapper, F, DurationField, Q
from hypernet.notifications.utils import send_notification_violations
from iop.utils import calculcate_ttr, check_overlapping_schedules, create_iop_activity
from urllib3.connectionpool import xrange
from django.utils import timezone
import traceback
from hypernet.enums import OptionsEnum, ModuleEnum, DeviceTypeEntityEnum, IOFOptionsEnum, DeviceTypeAssignmentEnum, \
    IopOptionsEnums
from hypernet.models import Assignment, HypernetPostData,HypernetPreData
from iof.models import ActivitySchedule, Activity, ActivityData, ActivityQueue, BinCollectionData, Entity
from datetime import timedelta
import time
from user.models import User
from hypernet import constants
from options.models import Options


def get_dates(from_date, to_date, day_list=[]):
    tmp_list = list()
    date_list = list()

    for x in xrange((to_date - from_date).days + 1):
        tmp_list.append(from_date + datetime.timedelta(days=x))
    for date_record in tmp_list:
        if date_record.weekday() in day_list:
            date_list.append(date_record.strftime('%Y-%m-%d'))
    return date_list


def get_conflicts(preferences, data, days_list, start_date=None, custom_dates=None):
    primary_entity = data.get('primary_entity')
    actor = data.get('actor')
    activity_start_time = data.get('activity_start_time')
    if start_date is None:
        start_date = data.get('start_date')
    end_date = data.get('end_date')
    try:
        # For recurring schedule, days list will be calculated and conflict will be searched.
        if end_date:
            if custom_dates:
                dates_list = custom_dates
            else:
                dates_list = get_dates(from_date=start_date, to_date=end_date, day_list=days_list)
            for d in dates_list:
                now_time = timezone.now()
                time_diff = now_time + timezone.timedelta(minutes=15)

                start_time = (parse(d + ' ' + str(activity_start_time))).replace(tzinfo=timezone.utc)
                end_time = (start_time + datetime.timedelta(minutes=preferences.average_activity_time))
                if start_time >= time_diff:
                    try:
                        # DRIVER QUEUE.
                        aq = ActivityQueue.objects.get(actor_id=actor.id,
                                                       activity_schedule__schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                       activity_datetime__range=[start_time, end_time])

                        return True, aq.activity_schedule, aq.activity_datetime
                    except ActivityQueue.DoesNotExist:
                        # traceback.print_exc()
                        try:
                            # TRUCK QUEUE.
                            aq = ActivityQueue.objects.get(primary_entity_id=primary_entity.id,
                                                           activity_schedule__schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                           activity_datetime__range=[start_time, end_time])
                            return True, aq.activity_schedule, aq.activity_datetime
                        except ActivityQueue.DoesNotExist:
                            # traceback.print_exc()
                            pass

                    # Reversing time stamps to check conflict in past
                    end_time = (start_time - datetime.timedelta(minutes=preferences.average_activity_time))
                    try:
                        # DRIVER QUEUE.
                        aq = ActivityQueue.objects.get(actor_id=actor.id,
                                                       activity_schedule__schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                       activity_datetime__range=[end_time, start_time])

                        return True, aq.activity_schedule, aq.activity_datetime
                    except ActivityQueue.DoesNotExist:
                        # traceback.print_exc()
                        try:
                            # TRUCK QUEUE.
                            aq = ActivityQueue.objects.get(primary_entity_id=primary_entity.id,
                                                           activity_schedule__schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                           activity_datetime__range=[end_time, start_time])
                            return True, aq.activity_schedule, aq.activity_datetime
                        except ActivityQueue.DoesNotExist:
                            # traceback.print_exc()
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
                        return True, start_time, None
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
                            return True, start_time, None
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
                        return True, start_time, None
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
                            return True, start_time, None
                        except:
                            pass

                    # ACTIVITY check for Running activity for both truck and driver.
                    try:
                        act = Activity.objects.get(actor_id=actor.id, activity_status_id__in=[IOFOptionsEnum.SUSPENDED,
                                                                                              IOFOptionsEnum.ACCEPTED,
                                                                                              IOFOptionsEnum.RUNNING])
                        end_time = (act.start_datetime + datetime.timedelta(minutes=preferences.average_activity_time))
                        if act.start_datetime <= start_time <= end_time:
                            return True, start_time, None
                        else:
                            try:
                                act = Activity.objects.get(primary_entity_id=primary_entity.id,
                                                           activity_status_id__in=[IOFOptionsEnum.SUSPENDED,
                                                                                   IOFOptionsEnum.ACCEPTED,
                                                                                   IOFOptionsEnum.RUNNING])
                                end_time = (
                                    act.start_datetime + datetime.timedelta(minutes=preferences.average_activity_time))
                                if act.start_datetime <= start_time <= end_time:
                                    return True, start_time, None
                                else:
                                    pass
                            except:
                                pass

                    except:
                        try:
                            act = Activity.objects.get(primary_entity_id=primary_entity.id,
                                                       activity_status_id__in=[IOFOptionsEnum.SUSPENDED,
                                                                               IOFOptionsEnum.ACCEPTED,
                                                                               IOFOptionsEnum.RUNNING])
                            end_time = (
                                act.start_datetime + datetime.timedelta(minutes=preferences.average_activity_time))
                            if act.start_datetime <= start_time <= end_time:
                                return True, start_time, None
                            else:
                                pass
                        except:
                            pass
            return False, None, None
        # For once schedule, datetime will be constructed and checked against activity queue for conflicts
        else:
            # TODO Refactor for Driver and Truck conflicts.
            activity_datetime = str(start_date) + ' ' + str(activity_start_time)
            activity_datetime = parse(activity_datetime)
            activity_datetime = activity_datetime.replace(tzinfo=timezone.utc)
            end_time = (activity_datetime + datetime.timedelta(minutes=preferences.average_activity_time))
            # Reversing time stamps to check conflict in future
            try:
                # DRIVER QUEUE.
                aq = ActivityQueue.objects.get(actor_id=actor.id,
                                               activity_schedule__schedule_activity_status_id=OptionsEnum.ACTIVE,
                                               activity_datetime__range=[activity_datetime, end_time])

                return True, aq.activity_schedule, aq.activity_datetime
            except:
                try:
                    # TRUCK QUEUE.
                    aq = ActivityQueue.objects.get(primary_entity_id=primary_entity.id,
                                                   activity_schedule__schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                   activity_datetime__range=[activity_datetime, end_time])
                    return True, aq.activity_schedule, aq.activity_datetime
                except:
                    pass

            # ACTIVITY QUEUE ON COMMING schedules conflicts

            # Reversing time stamps to check conflict in past
            end_time = (activity_datetime - datetime.timedelta(minutes=preferences.average_activity_time))
            try:
                # DRIVER QUEUE.
                aq = ActivityQueue.objects.get(actor_id=actor.id,
                                               activity_schedule__schedule_activity_status_id=OptionsEnum.ACTIVE,
                                               activity_datetime__range=[end_time, activity_datetime])

                return True, aq.activity_schedule, aq.activity_datetime
            except:
                try:
                    # TRUCK QUEUE.
                    aq = ActivityQueue.objects.get(primary_entity_id=primary_entity.id,
                                                   activity_schedule__schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                   activity_datetime__range=[end_time, activity_datetime])
                    return True, aq.activity_schedule, aq.activity_datetime
                except:
                    pass

            # ACTIVITY PART FOR CONFLICTS.
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
                return True, None, None
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
                    return True, None, None
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
                return True, None, None
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
                    return True, None, None
                except:
                    pass
                    # return False, None

            # Running/suspended ACTIVITY filter for both truck or driver.
            try:
                act = Activity.objects.get(actor_id=actor.id, activity_status_id__in=[IOFOptionsEnum.SUSPENDED,
                                                                                      IOFOptionsEnum.ACCEPTED,
                                                                                      IOFOptionsEnum.RUNNING])
                end_time = (act.start_datetime + datetime.timedelta(minutes=preferences.average_activity_time))
                if act.start_datetime <= activity_datetime <= end_time:
                    return True, None, None
                else:
                    try:
                        act = Activity.objects.get(primary_entity_id=primary_entity.id,
                                                   activity_status_id__in=[IOFOptionsEnum.SUSPENDED,
                                                                           IOFOptionsEnum.ACCEPTED,
                                                                           IOFOptionsEnum.RUNNING])
                        end_time = (act.start_datetime + datetime.timedelta(minutes=preferences.average_activity_time))
                        if act.start_datetime <= activity_datetime <= end_time:
                            return True, None, None
                        else:
                            return False, None, None
                    except:
                        return False, None, None

            except:
                try:
                    act = Activity.objects.get(primary_entity_id=primary_entity.id,
                                               activity_status_id__in=[IOFOptionsEnum.SUSPENDED,
                                                                       IOFOptionsEnum.ACCEPTED,
                                                                       IOFOptionsEnum.RUNNING])
                    end_time = (act.start_datetime + datetime.timedelta(minutes=preferences.average_activity_time))
                    if act.start_datetime <= activity_datetime <= end_time:
                        return True, None, None
                    else:
                        return False, None, None
                except:
                    return False, None, None

                    # TODO Reverse date time check.
                    # DRIVER CHECK FOR ACTIVITY CONFLICT
    except:
        traceback.print_exc()
        return True, None, None


def util_create_activity_queue(serializer, days_list, start_date=None, custom_days=None):
    if serializer:
        if serializer.end_date:
            if start_date:
                if custom_days:
                    dates_list = custom_days
                else:
                    dates_list = get_dates(from_date=start_date, to_date=serializer.end_date, day_list=days_list)
            else:
                if custom_days:
                    dates_list = custom_days
                else:
                    dates_list = get_dates(from_date=serializer.start_date, to_date=serializer.end_date,
                                           day_list=days_list)

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
        # print('Activity Does not exists')
        suspend = True

    except Activity.MultipleObjectsReturned:
        # print('multiple objs returned')
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
        # s_date = parse(start_date)
        # e_date = parse(end_date)
        activities = activities.filter(activity_start_time__range=[start_date, end_date])

    return activities.order_by('-created_datetime')


def util_get_activity_data(c_id, t_id, d_id, s_id, a_id, start_date, end_date):
    if t_id:
        activity_data = ActivityData.objects.filter(primary_entity_id=t_id, customer_id=c_id)

    elif d_id:
        # activity_data = ActivityData.objects.filter(actor_id=d_id, customer_id=c_id)
        # Temp removal of customer check for e2e TODO: revert it after demo
        activity_data = ActivityData.objects.filter(actor_id=d_id)

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
    result = []
    if action_items:
        bins_list = action_items.split(',')
        for id in bins_list:
            try:
                obj = Entity.objects.get(pk=id, type_id=DeviceTypeEntityEnum.BIN)
            except:
                # For debugging
                # traceback.print_exc()
                return None
            try:
                contract = Assignment.objects.get(parent_id=obj.id,
                                                  type_id=DeviceTypeAssignmentEnum.CONTRACT_ASSIGNMENT,
                                                  status_id=OptionsEnum.ACTIVE).child
                area = Assignment.objects.get(child_id=contract.id,
                                              type_id=DeviceTypeAssignmentEnum.AREA_CONTRACT_ASSIGNMENT,
                                              status_id=OptionsEnum.ACTIVE).parent
            except:
                # For debugging
                # traceback.print_exc()
                return None
            try:
                bin_data = BinCollectionData.objects.get(action_item_id=id, activity_id=activity_id)
                data = {'id': obj.id, 'label': obj.name, 'entity_location': obj.source_latlong,
                        'status': bin_data.status.label if bin_data else None,
                        'status_id': bin_data.status.id if bin_data else None,
                        'contract_name': contract.name,
                        'area': area.name,
                        'weight': bin_data.weight,
                        'invoice': bin_data.invoice if bin_data else None,
                        'type': obj.entity_sub_type.label if obj.entity_sub_type else None,
                        'client': obj.client.party_code if obj.client else None,
                        'client_name': obj.client.name if obj.client else None,
                        'verified': bin_data.verified if bin_data else None,
                        'entity_sub_type': bin_data.contract.leased_owned.label if bin_data.contract.leased_owned else None,
                        'timestamp': bin_data.timestamp,
                        'skip_size': obj.skip_size.id if obj.skip_size else None,
                        'skip_size_name': obj.skip_size.label if obj.skip_size else None
                        }
                if bin_data.supervisor:
                    data['supervisor'] = bin_data.supervisor.name
                result.append(data)

            except Exception as e:
                # traceback.print_exc()
                result.append({'id': obj.id, 'label': obj.name, 'entity_location': obj.source_latlong,
                               'status': IOFOptionsEnum.labels.get(IOFOptionsEnum.PENDING),
                               'status_id': IOFOptionsEnum.PENDING,
                               'contract_name': contract.name,
                               'area': area.name,
                               'weight': None,
                               'invoice': None,
                               'type': None,
                               'client': obj.client.party_code if obj.client else None,
                               'client_name': obj.client.name if obj.client else None,
                               'verified': None,
                               'entity_sub_type': None,
                               'timestamp': None,
                               'skip_size': obj.skip_size.id if obj.skip_size else None,
                               'skip_size_name': obj.skip_size.label if obj.skip_size else None
                               }
                              )
    elif activity_id:
        collection_data = BinCollectionData.objects.filter(activity_id=activity_id)
        if collection_data:
            for obj in collection_data:
                data = {'id': obj.action_item.id, 'label': obj.action_item.name,
                        'entity_location': obj.action_item.source_latlong,
                        'status': obj.status.label if obj.status else None,
                        'status_id': obj.status.id if obj.status else None,
                        'contract_name': obj.contract.name if obj.contract else None,
                        'area': obj.area.name if obj.area else None,
                        'weight': obj.weight,
                        'invoice': obj.invoice,
                        'type': obj.action_item.entity_sub_type.label if obj.action_item.entity_sub_type else None,
                        'client': obj.client.party_code if obj.client else None,
                        'client_name': obj.client.name if obj.client else None,
                        'verified': obj.verified,
                        'entity_sub_type': obj.contract.leased_owned.label if obj.contract.leased_owned else None,
                        'timestamp': obj.timestamp,
                        'skip_size': obj.action_item.skip_size.id if obj.action_item.skip_size else None,
                        'skip_size_name': obj.action_item.skip_size.label if obj.action_item.skip_size else None
                        }
                result.append(data)
        else:
            act = Activity.objects.get(id=activity_id)
            bins_list = act.action_items.split(',')
            for obj in bins_list:
                try:
                    b = Entity.objects.get(pk=obj, type_id=DeviceTypeEntityEnum.BIN)
                except:
                    return None
                try:
                    contract = Assignment.objects.get(parent_id=b.id,
                                                      type_id=DeviceTypeAssignmentEnum.CONTRACT_ASSIGNMENT,
                                                      status_id=OptionsEnum.ACTIVE).child
                    try:
                        area = Assignment.objects.get(child_id=contract.id,
                                                      type_id=DeviceTypeAssignmentEnum.AREA_CONTRACT_ASSIGNMENT,
                                                      status_id=OptionsEnum.ACTIVE).parent
                    except:
                        area = None
                except:
                    contract = None
                    area = None

                result.append({'id': b.id, 'label': b.name, 'entity_location': b.source_latlong,
                               'status': IOFOptionsEnum.labels.get(IOFOptionsEnum.PENDING),
                               'status_id': IOFOptionsEnum.PENDING,
                               'contract_name': contract.name if contract else None,
                               'area': area.name if area else None,
                               'weight': None,
                               'invoice': None,
                               'type': None,
                               'client': b.client.party_code if b.client else None,
                               'client_name': b.client.name if b.client else None,
                               'verified': None,
                               'entity_sub_type': None,
                               'timestamp': None,
                               'skip_size': b.skip_size.id if b.skip_size else None,
                               'skip_size_name': b.skip_size.label if b.skip_size else None
                               }
                              )

    return result


def util_get_bin_with_location(bin):
    if bin:
        obj = Entity.objects.get(pk=bin)
        return {'id': obj.id, 'label': obj.name, 'type': obj.type.id,
                'entity_sub_type': obj.entity_sub_type.label if obj.entity_sub_type else None}


def util_upcoming_activities(c_id, sch_id, t_id, d_id, start_date, end_date):
    if t_id:
        activity_queue = ActivityQueue.objects.filter(primary_entity_id=t_id, customer_id=c_id,
                                                      activity_schedule__schedule_activity_status_id=OptionsEnum.ACTIVE).order_by(
            'activity_datetime')

    elif sch_id:
        activity_queue = ActivityQueue.objects.filter(activity_schedule_id=sch_id, customer_id=c_id,
                                                      activity_schedule__schedule_activity_status_id=OptionsEnum.ACTIVE).order_by(
            'activity_datetime')

    elif d_id:
        activity_queue = ActivityQueue.objects.filter(actor_id=d_id, customer_id=c_id,
                                                      activity_schedule__schedule_activity_status_id=OptionsEnum.ACTIVE).order_by(
            'activity_datetime')

    else:
        activity_queue = ActivityQueue.objects.filter(customer_id=c_id,
                                                      activity_schedule__schedule_activity_status_id=OptionsEnum.ACTIVE).order_by(
            'activity_datetime')

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
        bin_collection_data = bin_collection_data.filter(timestamp__range=[s_date, e_date])

    return bin_collection_data


def util_get_schedule_total_count(sch_id):
    count_activity = Activity.objects.filter(activity_schedule_id=sch_id).count()

    total_count_activity = Activity.objects.filter(activity_schedule_id=sch_id,
                                                   activity_status_id__in=[IOFOptionsEnum.ABORTED,
                                                                           IOFOptionsEnum.COMPLETED]).count()

    count_queue = ActivityQueue.objects.filter(activity_schedule_id=sch_id).count()

    total = count_activity + count_queue
    if total > 0:
        return (total_count_activity / total) * 100
    else:
        return 0


def check_bin_in_activity(activity_id, bin_id):
    try:
        BinCollectionData.objects.get(activity_id=activity_id, action_item_id=bin_id)
        return True
    except:
        return False


def get_activity_bins(activity_id):
    try:
        return BinCollectionData.objects.filter(activity_id=activity_id).values_list('action_item', flat=True)
    except:
        return None


def delete_bincollection_data(bin_id, activity):
    try:
        bc = BinCollectionData.objects.get(action_item_id=bin_id, activity_id=activity)
        if bc.status.id == IOFOptionsEnum.UNCOLLECTED:
            bc.delete()
            return True, None
        else:
            if bc.status.id != IOFOptionsEnum.BIN_PICKED_UP:
                return False, "Bin is already collected in the activity and cannot be removed from the activity. \nBin ID:" + bc.action_item.name
            return True, None
    except:
        return True, None


def once_to_many_conflict(new_obj, start_time, end_time, start_date):
    days_of_week = start_date.weekday()
    # days_of_week = '1'#str(day_of_week)
    conflicts = True
    suspending_obj = new_obj
    processed = []
    list = []
    message = None
    start_time_to_next_date = False
    end_time_to_next_date = False

    current_datetime = fetch_current_datetime_with_tz_info()

    while conflicts:
        schs = check_generic_conflicts(new_obj, start_time, end_time, days_of_week, [IopOptionsEnums.IOP_SLEEP_MODE])

        # schs = schs.filter(sleep_mode = True)

        if schs:
            return False, list, "Cannot create event due to conflicting sleep mode"

        flag = check_conflict_with_queue(new_obj, start_time, end_time, days_of_week)
        if flag is False:
            return False, list, "Time provided conflicts with an already running activity"

        all_schedules = check_generic_conflicts(new_obj,
                                                start_time,
                                                end_time,
                                                days_of_week, [IopOptionsEnums.IOP_SCHEDULE_DAILY,
                                                               IopOptionsEnums.IOP_SCHEDULE_ON_DEMAND])

        all_schedules = all_schedules.exclude(id=new_obj.id)
        all_schedules = all_schedules.order_by('u_activity_start_time')

        if all_schedules:
            for o in all_schedules:
                if processed:
                    all_schedules = all_schedules.exclude(pk__in=processed)
                try:
                    queue = ActivityQueue.objects.get(activity_schedule=o)
                    if queue.is_on:
                        return False, list, "Cannot create schedule at the provided time since it affects an already running schedule."
                    else:
                        queue.delete()
                except ActivityQueue.DoesNotExist:
                    queue = None

                if o.start_date < new_obj.end_date:
                    start_time_to_next_date = True

                o.u_activity_start_time = new_obj.u_activity_end_time

                end_dt = str(current_datetime.date()) + ' ' + str(
                    o.u_activity_start_time)  # change to timezone.now()
                end_dt = parse(end_dt)

                new_d_t = end_dt + timedelta(minutes=float(o.notes))

                if new_d_t.date() != end_dt.date():
                    end_time_to_next_date = True

                if start_time_to_next_date is True:
                    if int(o.days_list) == 6:
                        o.u_days_list = str(0)
                    else:
                        o.u_days_list = str(int(o.days_list) + 1)
                    o.start_date = o.start_date + timedelta(
                        days=1)  # Incrementing start date since the date is changed due to shifting
                    o.multi_days = False

                if end_time_to_next_date is True:
                    o.end_date = o.end_date + timedelta(
                        days=1)  # End time is being shifted to another date so date is incremented.
                    o.multi_days = True

                # if start_time_to_next_date and end_time_to_next_date:
                #    o.multi_days = False
                updated_time = new_d_t.time()
                o.u_activity_end_time = updated_time
                o.suspended_by = suspending_obj

                list.append({'pk': o.id, 'u_activity_start_time': o.u_activity_start_time,
                             'u_activity_end_time': o.u_activity_end_time, 'suspended_by': o.suspended_by,
                             'updated_days_list': o.u_days_list,
                             'start_date': o.start_date, 'end_date': o.end_date, 'user': o.modified_by,
                             'multi_days': o.multi_days})

                start_time = o.u_activity_start_time
                end_time = o.u_activity_end_time

                days_of_week = o.u_days_list
                processed.append(new_obj.id)

                new_obj = o
                start_time_to_next_date = False
                end_time_to_next_date = False

        else:
            conflicts = False

    return True, list, message


def many_to_once(new_obj, start_time, end_time, days_of_week):
    # day_of_week = start_date.weekday()

    conflicts = True
    suspending_obj = new_obj
    processed = []
    list = []
    message = None
    start_time_to_next_date = False
    end_time_to_next_date = False
    while conflicts:
        schs = check_generic_conflicts(new_obj, start_time, end_time, days_of_week, [
            IopOptionsEnums.IOP_SLEEP_MODE])  # checking conflict of schedule with a running sleep mode
        schs = schs.filter(sleep_mode=True)
        if schs:
            return False, list, "Cannot create event due to conflicting sleep mode"

        flag = check_conflict_with_queue(new_obj, start_time, end_time, days_of_week)
        if flag is False:
            return False, list, "Time provided conflicts with an already running activity"
        all_schedules = check_generic_conflicts(new_obj,
                                                start_time,
                                                end_time,
                                                days_of_week, [IopOptionsEnums.IOP_SCHEDULE_DAILY,
                                                               IopOptionsEnums.IOP_SCHEDULE_ON_DEMAND])
        all_schedules = all_schedules.exclude(id=new_obj.id)
        all_schedules = all_schedules.order_by('u_activity_start_time')
        if all_schedules:
            for o in all_schedules:
                if processed:
                    all_schedules = all_schedules.exclude(pk__in=processed)
                try:
                    queue = ActivityQueue.objects.get(activity_schedule=o)
                    if queue.is_on:
                        return False, list, "Cannot create schedule at the provided time since it affects an already running schedule."
                    else:
                        queue.delete()
                except ActivityQueue.DoesNotExist:
                    queue = None

                if o.start_date < new_obj.end_date:
                    start_time_to_next_date = True

                o.u_activity_start_time = new_obj.u_activity_end_time

                if time.tzname[0] == 'UTC':
                    current_datetime = datetime.datetime.now() + datetime.timedelta(
                        hours=2)  # -2 for egpyt standard time. FIXME.
                else:
                    current_datetime = datetime.datetime.now()

                end_dt = str(current_datetime.date()) + ' ' + str(o.u_activity_start_time)  # change to timezone.now()
                end_dt = parse(end_dt)

                new_d_t = end_dt + timedelta(minutes=float(o.notes))

                if new_d_t.date() != end_dt.date():
                    end_time_to_next_date = True

                if start_time_to_next_date is True:
                    if int(o.days_list) == 6:
                        o.u_days_list = str(0)
                    else:
                        o.u_days_list = str(int(o.days_list) + 1)
                    o.start_date = o.start_date + timedelta(
                        days=1)  # Incrementing start date since the date is changed due to shifting
                    o.multi_days = False

                if end_time_to_next_date is True:
                    o.end_date = o.end_date + timedelta(
                        days=1)  # End time is being shifted to another date so date is incremented.
                    o.multi_days = True

                updated_time = new_d_t.time()
                o.u_activity_end_time = updated_time
                o.suspended_by = suspending_obj

                list.append({'pk': o.id, 'u_activity_start_time': o.u_activity_start_time,
                             'u_activity_end_time': o.u_activity_end_time, 'suspended_by': o.suspended_by,
                             'updated_days_list': o.u_days_list,
                             'start_date': o.start_date, 'end_date': o.end_date, 'user': o.modified_by,
                             'multi_days': o.multi_days})

                start_time = o.u_activity_start_time
                end_time = o.u_activity_end_time

                days_of_week = o.u_days_list
                processed.append(new_obj.id)

                new_obj = o

        else:
            conflicts = False

    return True, list, message


def update_activity_schedule(result_list):
    # temp_start_time = ""
    # temp_end_time = ""
    for l in result_list:
        try:
            # temmp_schedule = ActivitySchedule.objects.get(pk=l['pk'])
            # temp_start_time = temmp_schedule.u_activity_start_time
            # print("TEMPPPP SCHEDULE: ", temmp_schedule)
            # print("TEMPPP START TIME", temp_start_time)
            # print("L START NEW START DT", l['new_start_dt'].time())

            a_sch = ActivitySchedule.objects.get(pk=l['pk'])
            # print(a_sch[0],'schedule in check')

            # previous_time = a_sch.u_activity_start_time
            # previous_day = int(a_sch.u_days_list)
            # print( l['new_start_dt'].time(),'check time here ')
            a_sch.u_activity_start_time = l['new_start_dt'].time()
            a_sch.u_activity_end_time = l['new_end_dt'].time()
            a_sch.suspended_by = l['suspended_by']
            a_sch.start_date = l['new_start_dt'].date()
            a_sch.end_date = l['new_end_dt'].date()
            a_sch.u_days_list = l['updated_days_list']
            a_sch.multi_days = l['multi_days_new']
            a_sch.save()

            user = User.objects.get(id=a_sch.modified_by.id)
            print(a_sch.old_start_dt)
            previous_time = l['old_start_dt']
            previous_day = int(a_sch.days_list)
            new_time = a_sch.new_start_dt

            # previous_time = previous_time.time().replace(second=0).strftime("%I:%M %p")
            # new_time = new_time.time().replace(second=0).strftime("%I:%M %p")

            print("previous time    ", previous_time)
            print("new time    ", new_time)
            
            try:
                suspended_by = ActivitySchedule.objects.get(id=a_sch.suspended_by.id)
            except:
                suspended_by = None

            temp = int(a_sch.action_items)

            temp_name = 'Hot'
            for name, temp_range in constants.water_ranges.items():
                if temp in temp_range:
                    temp_name = name

            if suspended_by:
                first_name = suspended_by.modified_by.first_name
                last_name = suspended_by.modified_by.last_name

                name = first_name + ' ' + last_name if last_name else first_name

                # message = str(previous_time) + ',' + str(new_time)
                message = str(previous_time) + ',' + str(new_time)
                print("message    ", message)

                title = "Your {} {} schedule at @st has been shifted by {}. It will now be ready at @et" \
                    .format(temp_name, a_sch.activity_route, name)
                # title = "Your {} {} schedule at @st has been shifted by {}. It will now be ready at @et" \
                #     .format(temp_name, a_sch.activity_route, name)
            else:

                message = previous_time + ',' + new_time
                title = "Your {} {} schedule at @st has been shifted. It will now be ready at @et" \
                    .format(temp_name, a_sch.activity_route)

            send_notification_violations(None, driver_id=None,
                                         customer_id=a_sch.customer.id, module_id=a_sch.module.id,
                                         title=title, users_list=[user], type_id=2, description=message)
        except:
            traceback.print_exc()
            a_sch = None


def check_conflicts_multi_days(all_schs,
                               new_obj):  # This util checks for conflicts where a schedule is scheduled at midnight (multi days). For example 11:50-1:00 am overlaps with 11:55 - 00:20 am.
    for o in all_schs:
        if o.pk == new_obj.pk:
            all_schs = all_schs.exclude(pk=o.pk)
            continue
        if time.tzname[0] == 'UTC':
            current_datetime = datetime.datetime.now()
        else:
            current_datetime = datetime.datetime.now()

        today = current_datetime.date()  # changed from current_datetime.date().today() to current_datetime.date()
        if o.multi_days:
            start_dt = today
            end_dt = today + timedelta(days=1)

        else:
            start_dt = today
            end_dt = start_dt

        if new_obj.multi_days:
            new_start_dt = today
            new_end_dt = today + timedelta(days=1)

        else:
            new_start_dt = today
            new_end_dt = start_dt

        new_start_datetime = parse(str(new_start_dt) + ' - ' + str(new_obj.u_activity_start_time))
        new_end_datetime = parse(str(new_end_dt) + ' - ' + str(new_obj.u_activity_end_time))

        start_datetime = parse(str(start_dt) + ' - ' + str(o.u_activity_start_time))
        end_datetime = parse(str(end_dt) + ' - ' + str(o.u_activity_end_time))

        if end_datetime >= new_start_datetime and start_datetime <= new_end_datetime and start_datetime != new_end_datetime:
            pass
        else:
            all_schs = all_schs.exclude(pk=o.pk)

    return all_schs


def revised_check_conflicts_multi_days(all_schs, start_time,
                                       end_time):  # This util checks for conflicts where a schedule is scheduled at midnight (multi days). For example 11:50-1:00 am overlaps with 11:55 - 00:20 am.
    for o in all_schs:
        if time.tzname[0] == 'UTC':
            current_datetime = datetime.datetime.now()
        else:
            current_datetime = datetime.datetime.now()

        today = current_datetime.date()  # changed from current_datetime.date().today() to current_datetime.date()
        if o.multi_days:
            start_dt = today
            end_dt = today + timedelta(days=1)

        else:
            start_dt = today
            end_dt = start_dt

        if start_time > end_time:
            new_start_dt = today
            new_end_dt = today + timedelta(days=1)

        else:
            new_start_dt = today
            new_end_dt = start_dt

        new_start_datetime = parse(str(new_start_dt) + ' - ' + str(start_time))
        new_end_datetime = parse(str(new_end_dt) + ' - ' + str(end_time))

        start_datetime = parse(str(start_dt) + ' - ' + str(o.u_activity_start_time))
        end_datetime = parse(str(end_dt) + ' - ' + str(o.u_activity_end_time))

        if end_datetime >= new_start_datetime and start_datetime <= new_end_datetime and start_datetime != new_end_datetime:
            pass
        else:
            all_schs = all_schs.exclude(pk=o.pk)

    return all_schs


def check_conflicts_days_after(new_obj, days_of_week,
                               sch_type=None):  # This util checks for a new schedule scheduled at midnight. Checking here whether this new schedule overlapps with schedules that completely lie in the other day. For example. 11:50-12:15 conflicts with 00:05-00:10

    new_days_list = str(int(days_of_week) + 1)

    if sch_type:
        schedules = ActivitySchedule.objects.filter(primary_entity_id=new_obj.primary_entity.id,
                                                    u_days_list=new_days_list,
                                                    schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                    suspend_status=False,
                                                    u_activity_end_time__gte=new_obj.u_activity_end_time,
                                                    u_activity_start_time__lt=new_obj.u_activity_end_time,
                                                    activity_type_id__in=sch_type).order_by(
            'u_activity_start_time')

    else:
        schedules = ActivitySchedule.objects.filter(primary_entity_id=new_obj.primary_entity.id,
                                                    u_days_list=new_days_list,
                                                    schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                    suspend_status=False,
                                                    u_activity_end_time__gte=new_obj.u_activity_end_time,
                                                    u_activity_start_time__lt=new_obj.u_activity_end_time,
                                                    activity_type_id__in=[IopOptionsEnums.IOP_SCHEDULE_ON_DEMAND,
                                                                          IopOptionsEnums.IOP_SCHEDULE_DAILY]).order_by(
            'u_activity_start_time')

    return schedules


def revised_check_conflicts_days_after(primary_entity_id, end_time,
                                       days_of_week):  # This util checks for a new schedule scheduled at midnight. Checking here whether this new schedule overlapps with schedules that completely lie in the other day. For example. 11:50-12:15 conflicts with 00:05-00:10

    new_days_list = str(int(days_of_week) + 1)
    schedules = ActivitySchedule.objects.filter(primary_entity_id=primary_entity_id, u_days_list=new_days_list,
                                                schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                suspend_status=False, u_activity_end_time__gte=end_time,
                                                u_activity_start_time__lt=end_time,
                                                activity_type_id__in=[IopOptionsEnums.IOP_SCHEDULE_ON_DEMAND,
                                                                      IopOptionsEnums.IOP_SCHEDULE_DAILY]).order_by(
        'u_activity_start_time')

    return schedules


def check_conflicts_day_before(new_obj, days_of_week,
                               sch_type=None):  # This utl checks for a new schedule scheduled after midnight. For example at 00:15-00:30. Checking here whether this new schedule overlapps with schedules that lie in the previous day. For example. 11:50-12:30 conflicts with it since it's ending time conflicts with new schedule

    new_obj_start_datetime = parse(str(new_obj.start_date) + ' ' + str(new_obj.u_activity_start_time))
    new_obj_end_datetime = parse(str(new_obj.end_date) + ' ' + str(new_obj.u_activity_end_time))
    if sch_type:
        schedules = ActivitySchedule.objects.filter(
            primary_entity_id=new_obj.primary_entity.id,
            u_days_list=str(int(days_of_week) - 1),
            schedule_activity_status_id=OptionsEnum.ACTIVE,
            suspend_status=False,
            activity_type_id__in=sch_type).order_by(
            'u_activity_start_time')

    else:
        schedules = ActivitySchedule.objects.filter(
            primary_entity_id=new_obj.primary_entity.id,
            u_days_list=str(int(days_of_week) - 1),
            schedule_activity_status_id=OptionsEnum.ACTIVE,
            suspend_status=False,
            activity_type_id__in=[IopOptionsEnums.IOP_SCHEDULE_ON_DEMAND,
                                  IopOptionsEnums.IOP_SCHEDULE_DAILY]).order_by(
            'u_activity_start_time')

    schedules = schedules.exclude(pk=new_obj.pk)

    for sch in schedules:
        sch_datetime = parse(str(sch.start_date) + ' ' + str(sch.u_activity_start_time))
        sch_endtime = parse(str(sch.end_date) + ' ' + str(sch.u_activity_end_time))

        if (sch_datetime < new_obj_start_datetime < sch_endtime) or (
                        sch_datetime < new_obj_end_datetime <= sch_endtime):
            pass
        else:
            schedules = schedules.exclude(pk=sch.id)

    return schedules


def revised_check_conflicts_day_before(end_time, primary_entity_id,
                                       days_of_week):  # This utl checks for a new schedule scheduled after midnight. For example at 00:15-00:30. Checking here whether this new schedule overlapps with schedules that lie in the previous day. For example. 11:50-12:30 conflicts with it since it's ending time conflicts with new schedule
    schedules = ActivitySchedule.objects.filter(primary_entity_id=primary_entity_id,
                                                u_days_list=str(int(days_of_week) - 1),
                                                schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                suspend_status=False,
                                                u_activity_end_time__gt=end_time,
                                                u_activity_start_time__lte=end_time,
                                                activity_type_id__in=[IopOptionsEnums.IOP_SCHEDULE_ON_DEMAND,
                                                                      IopOptionsEnums.IOP_SCHEDULE_DAILY]).order_by(
        'u_activity_start_time')

    return schedules


def check_conflict_with_queue(new_obj, start_time, end_time,
                              days_of_week):  # This util checks the new activity with running schedule whose start time has changed in queue due to ttr. For example 2:00 activity has to run at 1:50 due to ttr.

    running_queues = ActivityQueue.objects.filter(is_on=True, is_off=False, module_id=ModuleEnum.IOP,
                                                  activity_schedule__u_days_list=days_of_week,
                                                  activity_schedule__activity_type_id__in=[
                                                      IopOptionsEnums.IOP_SCHEDULE_DAILY,
                                                      IopOptionsEnums.IOP_SCHEDULE_ON_DEMAND])

    previous_day = str(int(days_of_week) - 1)

    next_day = str(int(days_of_week) + 1)

    if days_of_week in [6, '6']:
        next_day = '0'

    elif days_of_week in [0, '0']:
        previous_day = '6'

    all_schedules = ActivityQueue.objects.filter(
        Q(activity_datetime__date__lte=start_time) & Q(activity_end_datetime__date__gt=start_time) | Q(
            activity_datetime__date__lt=end_time) & Q(activity_end_datetime__date__gt=end_time),
        primary_entity_id=new_obj.primary_entity.id,
        activity_schedule__u_days_list__in=[days_of_week, previous_day, next_day],
        is_on=True, is_off=False, module_id=ModuleEnum.IOP)

    if all_schedules:
        return False

    return True

    # Check to be added for midnight


def check_generic_conflicts(new_obj, start_time, end_time, days_of_week, sch_type):
    if end_time > start_time:
        all_schedules = ActivitySchedule.objects.filter(primary_entity_id=new_obj.primary_entity.id,
                                                        u_days_list__in=[days_of_week],
                                                        schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                        suspend_status=False, u_activity_end_time__gt=start_time,
                                                        u_activity_start_time__lt=end_time,
                                                        activity_type_id__in=sch_type).order_by(
            'u_activity_start_time')

        all_schedules = all_schedules.exclude(id=new_obj.id)

        a_chs = check_conflicts_day_before(new_obj, days_of_week, sch_type)

        all_schedules = all_schedules.union(a_chs)

        #   all_schedules = all_schedules.exclude(id=new_obj.id)


    else:  # when end time falls after midnight (next day) and start time on previous day
        all_schedules = ActivitySchedule.objects.filter(primary_entity_id=new_obj.primary_entity.id,
                                                        u_days_list__in=[days_of_week],
                                                        schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                        suspend_status=False,
                                                        activity_type_id__in=sch_type).order_by(
            'u_activity_start_time')

        all_schedules = check_conflicts_multi_days(all_schedules, new_obj)

        a_chs = check_conflicts_days_after(new_obj, days_of_week, sch_type)

        all_schedules = all_schedules.union(a_chs)

        all_schedules = all_schedules.order_by('u_days_list')

    all_schedules = all_schedules.exclude(id=new_obj.id)

    return all_schedules


def check_sleep_mode_conflicts(new_obj, start_dt, end_dt, days_of_week, primary_entity=None):
    previous_day = str(int(days_of_week) - 1)

    next_day = str(int(days_of_week) + 1)

    if days_of_week in [6, '6']:
        next_day = '0'

    elif days_of_week in [0, '0']:
        previous_day = '6'

    all_schedules = ActivitySchedule.objects.filter(
        Q(new_start_dt__lte=end_dt) & Q(new_end_dt__gte=start_dt),
        u_days_list__in=[days_of_week, previous_day, next_day],
        schedule_activity_status_id=OptionsEnum.ACTIVE,
        suspend_status=False,
        activity_type_id__in=[IopOptionsEnums.IOP_SLEEP_MODE, IopOptionsEnums.RECURRING_SLEEP_MODE]).order_by(
        'new_start_dt')

    if new_obj:
        all_schedules = all_schedules.filter(primary_entity_id=new_obj.primary_entity.id)
        all_schedules = all_schedules.exclude(id=new_obj.id)
    else:
        all_schedules = all_schedules.filter(primary_entity_id=primary_entity)

    if all_schedules:
        return False
    return True


def shift_schedule_times_with_ttr(appliance, desired_temp, todays_date, st, et, duration):
    import datetime
    duration = int(duration)

    ttr = calculcate_ttr(appliance, desired_temp, duration=duration)

    if ttr is None:
        flag = None
        return st, et, ttr, flag
    ttr = int(ttr)
    flag = False

    resultant_datetime = todays_date + datetime.timedelta(minutes=ttr)

    if resultant_datetime < st or ttr <= 0:
        pass
        flag = True
    else:
        st = resultant_datetime  # st + timedelta(minutes=ttr)
        et = st + timedelta(minutes=duration)
        flag = False
    return st, et, ttr, flag


def revised_check_generic_conflicts(primary_entity_id, start_time, end_time, days_of_week, sch_type, date=None):
    if end_time > start_time:
        all_schedules = ActivitySchedule.objects.filter(primary_entity_id=primary_entity_id,
                                                        u_days_list__in=[days_of_week],
                                                        schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                        suspend_status=False, u_activity_end_time__gt=start_time,
                                                        u_activity_start_time__lt=end_time,
                                                        activity_type_id__in=sch_type).order_by(
            'u_activity_start_time')


    else:  # when end time falls after midnight (next day) and start time on previous day
        all_schedules = ActivitySchedule.objects.filter(primary_entity_id=primary_entity_id,
                                                        u_days_list__in=[days_of_week],
                                                        schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                        suspend_status=False,
                                                        activity_type_id__in=sch_type).order_by(
            'u_activity_start_time')

        all_schedules = revised_check_conflicts_multi_days(all_schedules, start_time, end_time)

        a_chs = revised_check_conflicts_days_after(primary_entity_id, end_time, days_of_week)

        all_schedules = all_schedules.union(a_chs)

        all_schedules = all_schedules.order_by('u_days_list')

    if date:
        all_schedules = all_schedules.filter(start_date=date)

    return all_schedules


def fetch_current_datetime_with_tz_info():
    if time.tzname[0] == 'UTC':
        current_datetime = datetime.datetime.now()
    else:
        current_datetime = datetime.datetime.now()

    return current_datetime


def check_conflicts_with_use_now(new_obj, start_time, end_time, start_date, days_of_week=None):
    if not days_of_week:
        days_of_week = start_date.weekday()
    # days_of_week = '1'#str(day_of_week)
    conflicts = True
    suspending_obj = new_obj
    processed = []
    list = []
    message = None
    start_time_to_next_date = False
    end_time_to_next_date = False

    current_datetime = fetch_current_datetime_with_tz_info()

    while conflicts:
        schs = check_generic_conflicts(new_obj, start_time, end_time, days_of_week, [IopOptionsEnums.IOP_SLEEP_MODE])

        # schs = schs.filter(sleep_mode = True)

        if schs:
            return False, list, "Cannot create event due to conflicting sleep mode"

        flag = check_conflict_with_queue(new_obj, start_time, end_time, days_of_week)
        if flag is False:
            return False, list, "Time provided conflicts with an already running activity"

        all_schedules = check_generic_conflicts(new_obj,
                                                start_time,
                                                end_time,
                                                days_of_week, [IopOptionsEnums.IOP_SCHEDULE_DAILY,
                                                               IopOptionsEnums.IOP_SCHEDULE_ON_DEMAND,
                                                               IopOptionsEnums.IOP_USE_NOW,
                                                               IopOptionsEnums.IOP_QUICK_SCHEDULE,
                                                               ])

        all_schedules = all_schedules.exclude(pk=new_obj.id)
        all_schedules = all_schedules.order_by('u_activity_start_time')

        if all_schedules:
            sch = all_schedules[0]
            tau_old_sch = new_obj.temp_after_usage  # sch.temp_after_usage

            ttr_for_new_sch, t2 = calculcate_ttr(new_obj.primary_entity, duration=sch.notes,
                                                 desired_temp=sch.action_items, t1=tau_old_sch)
            try:
                queue = ActivityQueue.objects.get(activity_schedule=sch)
                if queue.is_on:
                    return False, list, "Cannot create schedule at the provided time since it affects an already running schedule."
                else:
                    queue.delete()
            except ActivityQueue.DoesNotExist:
                print('ActivtyQueue does not xis')
                queue = None
            except Exception as e:
                print(e)

            if sch.start_date < new_obj.end_date:
                start_time_to_next_date = True

            old_start_dt = parse(str(current_datetime.date()) + '-' + str(new_obj.u_activity_end_time))
            sch.u_activity_start_time = parse(
                str(current_datetime.date()) + '-' + str(new_obj.u_activity_end_time)) + timedelta(
                minutes=ttr_for_new_sch)

            if sch.u_activity_start_time.date() > old_start_dt.date():  # Added for quick schedule
                start_time_to_next_date = True

            print('-=-=-=-=-=-=-=-=     first')
            print('ttr value {} added in schedule {}'.format(ttr_for_new_sch, sch.id))

            end_dt = sch.u_activity_start_time

            sch.u_activity_start_time = sch.u_activity_start_time.time()

            # end_dt = str(current_datetime.date()) + ' ' + str(
            #    sch.u_activity_start_time)  # change to timezone.now()
            # end_dt = parse(end_dt)

            new_d_t = end_dt + timedelta(minutes=float(sch.notes))

            if new_d_t.date() != end_dt.date():
                end_time_to_next_date = True

            if start_time_to_next_date is True:
                if int(sch.days_list) == 6:
                    sch.u_days_list = str(0)
                else:
                    sch.u_days_list = str(int(sch.days_list) + 1)
                sch.start_date = sch.start_date + timedelta(
                    days=1)  # Incrementing start date since the date is changed due to shifting
                sch.multi_days = False

            if end_time_to_next_date is True:
                sch.end_date = sch.end_date + timedelta(
                    days=1)  # End time is being shifted to another date so date is incremented.
                sch.multi_days = True

            updated_time = new_d_t.time()
            sch.u_activity_end_time = updated_time
            sch.suspended_by = suspending_obj

            list.append({'pk': sch.id, 'u_activity_start_time': sch.u_activity_start_time,
                         'u_activity_end_time': sch.u_activity_end_time, 'suspended_by': sch.suspended_by,
                         'updated_days_list': sch.u_days_list,
                         'start_date': sch.start_date, 'end_date': sch.end_date, 'user': sch.modified_by,
                         'multi_days': sch.multi_days,
                         'activity_start_time': sch.activity_start_time,
                         'activity_end_time': sch.activity_end_time
                         })

            start_time = sch.u_activity_start_time
            end_time = sch.u_activity_end_time

            days_of_week = sch.u_days_list
            processed.append(new_obj.id)

            new_obj = sch
            start_time_to_next_date = False
            end_time_to_next_date = False


        else:
            all_schedules = ActivitySchedule.objects.filter(primary_entity_id=new_obj.primary_entity.id,
                                                            u_days_list__in=[days_of_week],
                                                            schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                            suspend_status=False,
                                                            activity_type_id__in=[IopOptionsEnums.IOP_USE_NOW,
                                                                                  IopOptionsEnums.IOP_SCHEDULE_ON_DEMAND,
                                                                                  IopOptionsEnums.IOP_SCHEDULE_DAILY,
                                                                                  IopOptionsEnums.IOP_QUICK_SCHEDULE,
                                                                                  ]).order_by('u_activity_end_time')

            all_schedules = all_schedules.exclude(id=new_obj.id)

            print('Schedules count:  ', all_schedules.count())
            objs = all_schedules.filter(u_activity_end_time__lte=new_obj.u_activity_start_time).order_by(
                'u_activity_end_time')

            # if objs:
            #     objs_after = all_schedules.filter(u_activity_end_time__gt = new_obj.u_activity_start_time).order_by('u_activity_end_time')
            # else:
            objs_after = all_schedules.filter(u_activity_end_time__gte=new_obj.u_activity_start_time).order_by(
                'u_activity_end_time')
            if objs:

                objs = objs.last()

                tau_old_sch = objs.temp_after_usage

                ttr_for_new_sch, t2 = calculcate_ttr(new_obj.primary_entity, duration=new_obj.notes,
                                                     desired_temp=new_obj.action_items, t1=tau_old_sch)

                temp_time = parse(str(new_obj.start_date) + '-' + str(new_obj.u_activity_start_time)) - timedelta(
                    minutes=ttr_for_new_sch)

                objs_end_dt = parse(str(objs.end_date) + '-' + str(objs.u_activity_end_time))

                if temp_time < objs_end_dt:  # objs_st_dt <= temp_time < objs_end_dt:


                    new_obj.u_activity_start_time = parse(
                        str(objs.start_date) + '-' + str(objs.u_activity_end_time)) + timedelta(minutes=ttr_for_new_sch)
                    new_obj.u_activity_end_time = new_obj.u_activity_start_time + timedelta(
                        minutes=float(new_obj.notes))

                    new_obj.suspended_by = objs
                    print('-=-=-=-=-=-=-=-=     second')
                    print('ttr value {} added in schedule {}'.format(ttr_for_new_sch, new_obj.id))

                    new_obj.u_activity_start_time = new_obj.u_activity_start_time.time()
                    new_obj.u_activity_end_time = new_obj.u_activity_end_time.time()

                    new_obj.save()

                    start_time = new_obj.u_activity_start_time
                    end_time = new_obj.u_activity_end_time
                    days_of_week = new_obj.u_days_list
                    list.append({'pk': new_obj.id, 'u_activity_start_time': new_obj.u_activity_start_time,
                                 'u_activity_end_time': new_obj.u_activity_end_time,
                                 'suspended_by': new_obj.suspended_by,
                                 'updated_days_list': new_obj.u_days_list,
                                 'start_date': new_obj.start_date, 'end_date': new_obj.end_date,
                                 'user': new_obj.modified_by,
                                 'multi_days': new_obj.multi_days,
                                 'activity_start_time': new_obj.activity_start_time,
                                 'activity_end_time': new_obj.activity_end_time,
                                 })

                    all_schedules = check_generic_conflicts(new_obj,
                                                            new_obj.u_activity_start_time,
                                                            new_obj.u_activity_end_time,
                                                            days_of_week, [IopOptionsEnums.IOP_SCHEDULE_DAILY,
                                                                           IopOptionsEnums.IOP_SCHEDULE_ON_DEMAND,
                                                                           IopOptionsEnums.IOP_USE_NOW,
                                                                           IopOptionsEnums.IOP_QUICK_SCHEDULE,
                                                                           ])

                    all_schedules = all_schedules.exclude(pk=new_obj.id)
                    all_schedules = all_schedules.order_by('u_activity_start_time')

                    if len(
                            all_schedules) == 0:  # if the current schedule conflicts with any other schedule then current_obj will be this obj other wise the next_in_line object will become the current object
                        schs = ActivitySchedule.objects.filter(
                            u_activity_start_time__gt=new_obj.u_activity_start_time).order_by(
                            'u_activity_start_time')  # checking the next in line schedule that lies next to this schedule
                        if schs:
                            new_obj = schs[0]
                            start_time = new_obj.u_activity_start_time
                            end_time = new_obj.u_activity_end_time
                else:  # checking if the current object isn't conflicting with the buffer then make the next in line object the current object
                    if objs_after:
                        objs_after = objs_after[0]
                        new_obj = objs_after
                        start_time = objs_after.u_activity_start_time
                        end_time = objs_after.u_activity_end_time
                        days_of_week = objs_after.u_days_list
                    else:
                        conflicts = False


            elif objs_after:
                objs = objs_after.first()

                tau_old_sch = new_obj.temp_after_usage

                ttr_for_new_sch, t2 = calculcate_ttr(objs.primary_entity, duration=objs.notes,
                                                     desired_temp=objs.action_items, t2=tau_old_sch)

                print('ttr for new schedule', ttr_for_new_sch)
                temp_time = parse(str(new_obj.start_date) + '-' + str(objs.u_activity_start_time)) - timedelta(
                    minutes=ttr_for_new_sch)

                objs_end_dt = parse(str(new_obj.end_date) + '-' + str(new_obj.u_activity_end_time))

                if temp_time < objs_end_dt:  # objs_st_dt <= temp_time < objs_end_dt:


                    objs.u_activity_start_time = parse(
                        str(new_obj.start_date) + '-' + str(new_obj.u_activity_end_time)) + timedelta(
                        minutes=ttr_for_new_sch)

                    objs.u_activity_end_time = objs.u_activity_start_time + timedelta(
                        minutes=float(objs.notes))

                    objs.u_activity_start_time = objs.u_activity_start_time.time()
                    objs.u_activity_end_time = objs.u_activity_end_time.time()

                    objs.suspended_by = new_obj
                    objs.save()

                    start_time = objs.u_activity_start_time
                    end_time = objs.u_activity_end_time
                    days_of_week = objs.u_days_list

                    list.append({'pk': objs.id, 'u_activity_start_time': objs.u_activity_start_time,
                                 'u_activity_end_time': objs.u_activity_end_time,
                                 'suspended_by': objs.suspended_by,
                                 'updated_days_list': objs.u_days_list,
                                 'start_date': objs.start_date, 'end_date': objs.end_date,
                                 'user': objs.modified_by,
                                 'multi_days': objs.multi_days,
                                 'activity_start_time': objs.activity_start_time,
                                 'activity_end_time': objs.activity_end_time})

                    all_schedules = check_generic_conflicts(objs,
                                                            objs.u_activity_start_time,
                                                            objs.u_activity_end_time,
                                                            days_of_week, [IopOptionsEnums.IOP_SCHEDULE_DAILY,
                                                                           IopOptionsEnums.IOP_SCHEDULE_ON_DEMAND,
                                                                           IopOptionsEnums.IOP_USE_NOW,
                                                                           IopOptionsEnums.IOP_QUICK_SCHEDULE,
                                                                           ])

                    all_schedules = all_schedules.exclude(pk=objs.id)
                    all_schedules = all_schedules.order_by('u_activity_start_time')

                    if len(
                            all_schedules) == 0:  # if the current schedule conflicts with any other schedule then current_obj will be this obj other wise the next_in_line object will become the current object
                        schs = ActivitySchedule.objects.filter(
                            u_activity_start_time__gt=objs.u_activity_start_time).order_by(
                            'u_activity_start_time')  # checking the next in line schedule that lies next to this schedule
                        if schs:
                            new_obj = schs[0]
                            start_time = new_obj.u_activity_start_time
                            end_time = new_obj.u_activity_end_time
                            days_of_week = new_obj.u_days_list
                else:
                    new_obj = objs
                    start_time = objs.u_activity_start_time
                    end_time = objs.u_activity_end_time
                    days_of_week = objs.u_days_list

            else:
                return True, list, None
    return True, list, None


def revert_schedules(schs):
    if schs:
        for sch in schs:
            try:
                obj = ActivitySchedule.objects.get(id=sch['pk'])
                obj.new_start_dt = sch['old_start_dt']
                obj.new_end_dt = sch['old_end_dt']
                obj.u_days_list = sch['old_days_list']
                obj.multi_days = sch['multi_days_old']
                obj.start_date = sch['old_start_dt'].date()
                obj.end_date = sch['old_end_dt'].date()
                obj.u_activity_start_time = sch['old_start_dt'].time()
                obj.u_activity_end_time = sch['old_end_dt'].time()
            except:
                continue


def suggest_events_on_usage(ent, start_time, end_time, usage, duration, today, tau, time_diff=None):
    try:
        ttr = None
        buffer_tba = None
        new_usage = None
        t2 = None
        usage = int(usage)
        duration = int(duration)
        if usage == constants.very_hot_water:  # If user wanted very hot water.
            ttr, t2 = calculcate_ttr(ent, constants.hot_water, duration=duration,
                                     t1=tau)  # Calculate new ttr of hot water
            new_usage = constants.hot_water

        elif usage == constants.hot_water:  # If user wanted hot water.
            ttr, t2 = calculcate_ttr(ent, constants.warm_water, duration=duration,
                                     t1=tau)  # Calculate new ttr of warm water
            new_usage = constants.warm_water

        elif usage == constants.warm_water:  # If user wanted warm water.
            duration = int(duration / 2)  # Half the duration
            new_usage = constants.warm_water

        else:
            pass

        if ttr:
            # calculate buffer for this new usage by subtracting ttr with time diff. This time diff is
            # calculated by subtracting user sent start_time from the schedule's end_datetime. This schedule
            # is the one with which the user's sent start_time is conflicting with it's buffer.
            buffer_tba = ttr - time_diff
            if buffer_tba < 0:
                buffer_tba = 0
            new_start_time = start_time + datetime.timedelta(minutes=buffer_tba)  # Add buffer to the start_time.
            end_time = new_start_time + datetime.timedelta(minutes=duration)

        else:  # ttr is 0 or None in this case
            new_start_time = start_time  # In this case no buffer is added
            end_time = new_start_time + timedelta(minutes=duration)

        start_time = new_start_time.time()

        end_time = end_time.time()
    except:
        traceback.print_exc()
    return start_time, end_time, duration, buffer_tba, new_usage, t2


def query_all_schedules(new_obj, days_of_week, appliance_id=None, start_dt=None):
    previous_day = str(int(days_of_week) - 1)
    next_day = str(int(days_of_week) + 1)

    if days_of_week == '6' or days_of_week == 6:
        next_day = '0'

    elif days_of_week == '0' or days_of_week == 0:
        previous_day = '6'

    if new_obj:
        all_schedules = ActivitySchedule.objects.filter(primary_entity_id=new_obj.primary_entity.id,
                                                        u_days_list__in=[previous_day, days_of_week, next_day],
                                                        schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                        suspend_status=False,
                                                        activity_type_id__in=[IopOptionsEnums.IOP_USE_NOW,
                                                                              IopOptionsEnums.IOP_SCHEDULE_ON_DEMAND,
                                                                              IopOptionsEnums.IOP_SCHEDULE_DAILY,
                                                                              IopOptionsEnums.IOP_QUICK_SCHEDULE,
                                                                              ]).order_by('new_end_dt')

        all_schedules = all_schedules.exclude(id=new_obj.id)

    elif appliance_id:
        all_schedules = ActivitySchedule.objects.filter(primary_entity_id=appliance_id,
                                                        u_days_list__in=[previous_day, days_of_week, next_day],
                                                        schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                        suspend_status=False,
                                                        activity_type_id__in=[IopOptionsEnums.IOP_USE_NOW,
                                                                              IopOptionsEnums.IOP_SCHEDULE_ON_DEMAND,
                                                                              IopOptionsEnums.IOP_SCHEDULE_DAILY,
                                                                              IopOptionsEnums.IOP_QUICK_SCHEDULE,
                                                                              ]).order_by('new_end_dt')
    else:
        all_schedules = None

    if start_dt:
        previous_date = start_dt - timedelta(days=1)
        next_date = start_dt + timedelta(days=1)
        all_schedules = all_schedules.filter(start_date__range=[previous_date, next_date])

    return all_schedules


def updated_conflicts(new_obj, start_dt, end_dt, days_of_week, sch_type, start_date=None, primary_entity=None,
                      tbd_obj=None):
    previous_day = str(int(days_of_week) - 1)

    next_day = str(int(days_of_week) + 1)
    print(start_dt,end_dt,'sajndjsandjnasj check for this value  ')
    if days_of_week in [6, '6']:
        next_day = '0'

    elif days_of_week in [0, '0']:
        previous_day = '6'

    if new_obj:

        all_schedules = ActivitySchedule.objects.filter(
            Q(new_start_dt__lte=end_dt) & Q(new_end_dt__gte=start_dt),
            primary_entity_id=new_obj.primary_entity.id,
            u_days_list__in=[days_of_week, previous_day, next_day],
            schedule_activity_status_id=OptionsEnum.ACTIVE,
            suspend_status=False,
            activity_type_id__in=sch_type).order_by('new_start_dt')

        all_schedules = all_schedules.exclude(id=new_obj.id)


    else:

        all_schedules = ActivitySchedule.objects.filter(
            Q(new_start_dt__lte=end_dt) & Q(new_end_dt__gte=start_dt),
            primary_entity_id=primary_entity.id,
            u_days_list__in=[days_of_week, previous_day, next_day],
            schedule_activity_status_id=OptionsEnum.ACTIVE,
            suspend_status=False,
            activity_type_id__in=sch_type).order_by('new_start_dt')

    if start_date:
        previous_date = start_date - timedelta(days=1)
        next_date = start_date + timedelta(days=1)
        all_schedules = all_schedules.filter(start_date__range=[previous_date, next_date])

    if tbd_obj:
        all_schedules = all_schedules.exclude(id=tbd_obj)
    return all_schedules


def updated_check_conflicts_with_use_now(new_obj, start_dt, end_dt, start_date, days_of_week=None):
    print("updated_check_conflicts_with_use_now ==--==--")
    if not days_of_week:
        days_of_week = start_date.weekday()
    # days_of_week = '1'#str(day_of_week)
    conflicts = True
    suspending_obj = new_obj
    processed = []
    list = []
    
    while conflicts:
        # schs = check_sleep_mode_conflicts(new_obj=new_obj, start_dt=start_dt, end_dt=end_dt, days_of_week=days_of_week)

        # schs = schs.filter(sleep_mode = True)

        # if schs is False:
        #     return False, list, "Cannot create activity due to conflicting sleep mode"
        print(start_dt,'start_dt updated_check_conflicts_with_use_now ')
        print(end_dt,'end_dt updated_check_conflicts_with_use_now ')
        print(start_date,'start date updated_check_conflicts_with_use_now ')
        flag = check_conflict_with_queue(new_obj, start_dt, end_dt, days_of_week)
    
        if flag is False:
            return False, list, "Time provided conflicts with an already running activity"

        all_schedules = updated_conflicts(new_obj,
                                          start_dt,
                                          end_dt,
                                          days_of_week, [IopOptionsEnums.IOP_SCHEDULE_DAILY,
                                                         IopOptionsEnums.IOP_SCHEDULE_ON_DEMAND,
                                                         IopOptionsEnums.IOP_USE_NOW,
                                                         IopOptionsEnums.IOP_QUICK_SCHEDULE,
                                                         ], start_date=start_date)

        all_schedules = all_schedules.exclude(pk=new_obj.id)
        all_schedules = all_schedules.order_by('new_start_dt')

        if all_schedules:
            sch = all_schedules[0]
            tau_old_sch = new_obj.temp_after_usage  # sch.temp_after_usage
            print('tau old sch   ', tau_old_sch)
            ttr_for_new_sch, t2 = calculcate_ttr(new_obj.primary_entity, duration=sch.notes,
                                                 desired_temp=sch.action_items, t1=tau_old_sch)
            # if ttr_for_new_sch <30:
            #     ttr_for_new_sch=0
            print(ttr_for_new_sch,sch.new_start_dt,'this check for asdas')
            try:
                queue = ActivityQueue.objects.get(activity_schedule=sch)
                if queue.is_on:
                    return False, list, "Cannot create schedule at the provided time since it affects an already running schedule."
                else:
                    queue.delete()
            except ActivityQueue.DoesNotExist:
                print("ActivityQueue.DoesNotExist:")
                queue = None
            except Exception as e:
                print(e)

            print('new_obj.new_end_dt ', new_obj.new_end_dt)
            print('new_obj.new_end_dt after', new_obj.new_end_dt + timedelta(minutes=ttr_for_new_sch))

            sch.u_activity_start_time = new_obj.new_end_dt + timedelta(minutes=ttr_for_new_sch)
           
            old_multi_days = sch.multi_days
            old_start_dt = sch.new_start_dt
            old_start_dt = old_start_dt.replace(tzinfo=None)

            # CHANGE THIS FOR NOTIFICATION TIME ISSUE
            # sch.old_start_dt = sch.new_start_dt
            # sch.old_end_dt = sch.new_end_dt
            sch.new_start_dt = sch.u_activity_start_time

            new_start_dt = sch.new_start_dt
            new_start_dt = new_start_dt.replace(tzinfo=None)

            print('time ', (new_start_dt.date() - old_start_dt.date()).days)
            old_days_list = sch.u_days_list


            if ((new_start_dt.date() - old_start_dt.date()).days) > 0:  # Added for quick schedule

                if int(sch.days_list) == 6:
                    sch.u_days_list = str(0)
                else:
                    sch.u_days_list = str(int(sch.days_list) + 1)
                sch.start_date = sch.start_date + timedelta(
                    days=1)  # Incrementing start date since the date is changed due to shifting

                sch.multi_days = False

            print('-=-=-=-=-=-=-=-=     third')
            print('ttr value {} added in schedule {}'.format(ttr_for_new_sch, sch.id))

            old_end_dt = sch.new_end_dt

            # end_dt = sch.new_start_dt

            sch.u_activity_start_time = sch.u_activity_start_time.time()

            new_d_t = sch.new_start_dt + timedelta(minutes=float(sch.notes))

            sch.new_end_dt = new_d_t

            if (new_d_t.date() - old_end_dt.date()).days > 0:
                sch.end_date = sch.end_date + timedelta(
                    days=1)  # End time is being shifted to another date so date is incremented.

            updated_time = new_d_t.time()
            sch.u_activity_end_time = updated_time
            sch.suspended_by = suspending_obj #for check delay

            if (sch.new_end_dt.date() - sch.new_start_dt.date()).days > 0:
                sch.multi_days = True
            else:
                sch.multi_days = False
            sch.save()
            print(sch,'check here 1 ')
            print('hereeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee 1111111111')
            ''''
            list.append({'pk': sch.id, 'u_activity_start_time': sch.u_activity_start_time,
                         'u_activity_end_time': sch.u_activity_end_time, 'suspended_by': sch.suspended_by,
                         'updated_days_list': sch.u_days_list,
                         'start_date': sch.start_date, 'end_date': sch.end_date, 'user': sch.modified_by,
                         'multi_days': sch.multi_days,
                         'activity_start_time': sch.activity_start_time,
                         'activity_end_time': sch.activity_end_time
                         })
            '''
            print('zone 1')
            list.append({'pk': sch.id, 'old_start_dt': old_start_dt,
                         'new_start_dt': new_start_dt,
                         'suspended_by': sch.suspended_by,
                         'old_end_dt': old_end_dt,
                         'new_end_dt': new_d_t,
                         'updated_days_list': sch.u_days_list,
                         'old_days_list': old_days_list,
                         'user': sch.modified_by,
                         'multi_days_new': sch.multi_days,
                         'multi_days_old': old_multi_days
                         })

            start_dt = sch.new_start_dt
            end_dt = sch.new_end_dt

            days_of_week = sch.u_days_list
            processed.append(new_obj.id)

            new_obj = sch

        else:
            all_schedules = query_all_schedules(new_obj, days_of_week, start_dt=start_date)

            all_schedules = all_schedules.exclude(id=new_obj.id)
            previous_day = str(int(days_of_week) - 1)

            next_day = str(int(days_of_week) + 1)

            if days_of_week == '6' or days_of_week == 6:
                next_day = '0'

            elif days_of_week == '0' or days_of_week == 0:
                previous_day = '6'

            objs = all_schedules.filter(new_end_dt__lte=new_obj.new_start_dt).order_by(
                'new_end_dt')

            objs = objs.filter(u_days_list__in=[days_of_week, previous_day])

            objs_after = all_schedules.filter(new_end_dt__gt=new_obj.new_start_dt).order_by(
                'new_end_dt')

            objs_after = objs_after.filter(u_days_list__in=[days_of_week, next_day])

            # if objs:

            #     objs = objs.last()

            #     tau_old_sch = objs.temp_after_usage

            #     ttr_for_new_sch, t2 = calculcate_ttr(new_obj.primary_entity, duration=new_obj.notes,
            #                                          desired_temp=new_obj.action_items, t1=tau_old_sch)

            #     temp_time = new_obj.new_start_dt - timedelta(
            #         minutes=ttr_for_new_sch)

            #     objs_end_dt = objs.new_end_dt

            #     if temp_time < objs_end_dt:  # objs_st_dt <= temp_time < objs_end_dt:
            #         old_multi_days = new_obj.multi_days
            #         old_start_dt = new_obj.new_start_dt
            #         old_end_dt = new_obj.new_end_dt
            #         new_obj.new_start_dt = objs.new_end_dt + timedelta(minutes=ttr_for_new_sch)
            #         new_obj.new_end_dt = new_obj.new_start_dt + timedelta(minutes=float(new_obj.notes))

            #         new_obj.suspended_by = objs
            #         print('-=-=-=-=-=-=-=-=     4th')
            #         print('ttr value {} added in schedule {}'.format(ttr_for_new_sch, new_obj.id))

            #         new_obj.u_activity_start_time = new_obj.old_start_dt.time() # change new start time to old time 
            #         new_obj.u_activity_end_time = new_obj.old_end_dt.time()# change new start time to old time

            #         old_start_date = new_obj.start_date
            #         new_obj.start_date = new_obj.new_start_dt.date()  
            #         new_obj.end_date = new_obj.new_end_dt.date() 

            #         if (new_obj.end_date - new_obj.start_date).days > 0:
            #             new_obj.multi_days = True
            #         else:
            #             new_obj.multi_days = False

            #         old_days_list = new_obj.u_days_list
            #         if (new_obj.start_date - old_start_date).days > 0:
            #             new_obj.u_days_list = str(int(new_obj.u_days_list) + 1)
            #         # new_obj.save()
            #         # new_obj.save()
            #         days_of_week = new_obj.u_days_list
            #         print(new_obj.u_activity_start_time)
            #         start_dt = new_obj.old_start_dt# check for testing change new start time to old
            #         end_dt = new_obj.old_end_dt # check for testing change new start time to old
            #         print('hereeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee 22222222222222')
            #         print('zone 2')
            #         list.append({'pk': new_obj.id, 'old_start_dt': old_start_dt,
            #                      'new_start_dt': new_obj.new_start_dt,
            #                      'suspended_by': suspending_obj,
            #                      'old_end_dt': old_end_dt,
            #                      'new_end_dt': new_obj.new_end_dt,
            #                      'updated_days_list': new_obj.u_days_list,
            #                      'old_days_list': old_days_list,
            #                      'user': new_obj.modified_by,
            #                      'multi_days_new': new_obj.multi_days,
            #                      'multi_days_old': old_multi_days
            #                      })

            #     else:
            #         objs = query_all_schedules(new_obj, days_of_week)
            #         next_day = str(int(days_of_week) + 1)

            #         if days_of_week == '6' or days_of_week == 6:
            #             next_day = '0'

            #         objs_after = all_schedules.filter(new_end_dt__gt=new_obj.new_start_dt,
            #                                           u_days_list__in=[days_of_week, next_day]).order_by(
            #             'new_end_dt')
            #         if objs_after:
            #             objs_after = objs_after[0]
            #             new_obj = objs_after
            #             days_of_week = new_obj.u_days_list
            #             start_dt = new_obj.new_start_dt
            #             end_dt = new_obj.new_end_dt
            #         else:
            #             conflicts = False

            
            
            if objs_after:
                objs = objs_after.first()

                tau_old_sch = new_obj.temp_after_usage

                ttr_for_new_sch, t2 = calculcate_ttr(objs.primary_entity, duration=objs.notes,
                                                     desired_temp=objs.action_items, t1=tau_old_sch)

                print('ttr for new schedule', ttr_for_new_sch)
                temp_time = objs.new_start_dt - timedelta(
                    minutes=ttr_for_new_sch)

                new_obj_end_dt = new_obj.new_end_dt

                if temp_time < new_obj_end_dt:  # objs_st_dt <= temp_time < objs_end_dt:


                    old_start_dt = objs.new_start_dt
                    old_end_dt = objs.new_end_dt
                    objs.new_start_dt = new_obj.new_end_dt + timedelta(
                        minutes=ttr_for_new_sch)

                    objs.new_end_dt = objs.new_start_dt + timedelta(
                        minutes=float(objs.notes))

                    objs.u_activity_start_time = objs.new_start_dt.time()
                    objs.u_activity_end_time = objs.new_end_dt.time() #for check

                    objs.suspended_by = new_obj #for check

                    old_start_date = objs.start_date
                    objs.start_date = objs.new_start_dt.date()
                    objs.end_date = objs.new_end_dt.date()

                    old_multi_days = objs.multi_days
                    if (objs.end_date - objs.start_date).days > 0:
                        objs.multi_days = True
                    else:
                        objs.multi_days = False

                    old_days_list = objs.u_days_list
                    if (objs.start_date - old_start_date).days > 0:
                        objs.u_days_list = str(int(objs.u_days_list) + 1)
                        if objs.u_days_list == '6':
                            objs.u_days_list = 0

                    objs.save()
                    print('hereeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee 3333333333')
                    '''
                    list.append({'pk': objs.id, 'u_activity_start_time': objs.u_activity_start_time,
                                 'u_activity_end_time': objs.u_activity_end_time,
                                 'suspended_by': objs.suspended_by,
                                 'updated_days_list': objs.u_days_list,
                                 'start_date': objs.start_date, 'end_date': objs.end_date,
                                 'user': objs.modified_by,
                                 'multi_days': objs.multi_days,
                                 'activity_start_time': objs.activity_start_time,
                                 'activity_end_time': objs.activity_end_time})
                    '''
                    print('zone 3')
                    list.append({'pk': objs.id, 'old_start_dt': old_start_dt,
                                 'new_start_dt': objs.new_start_dt,
                                 'suspended_by': objs.suspended_by,
                                 'old_end_dt': old_end_dt,
                                 'new_end_dt': objs.new_end_dt,
                                 'updated_days_list': objs.u_days_list,
                                 'old_days_list': old_days_list,
                                 'user': objs.modified_by,
                                 'multi_days_new': new_obj.multi_days,
                                 'multi_days_old': old_multi_days
                                 })

                    all_schedules = updated_conflicts(objs,
                                                      objs.new_start_dt,
                                                      objs.new_end_dt,
                                                      days_of_week, [IopOptionsEnums.IOP_SCHEDULE_DAILY,
                                                                     IopOptionsEnums.IOP_SCHEDULE_ON_DEMAND,
                                                                     IopOptionsEnums.IOP_USE_NOW,
                                                                     IopOptionsEnums.IOP_QUICK_SCHEDULE,
                                                                     ])

                    all_schedules = all_schedules.exclude(pk=new_obj.id)

                    if len(
                            all_schedules) == 0:  # if the current schedule conflicts with any other schedule then current_obj will be this obj other wise the next_in_line object will become the current object
                        schs = ActivitySchedule.objects.filter(
                            new_start_dt__gt=objs.new_end_dt).order_by(
                            'new_start_dt')  # checking the next in line schedule that lies next to this schedule
                        if schs:
                            new_obj = schs[0]
                            days_of_week = new_obj.u_days_list

                            start_dt = new_obj.new_start_dt
                            end_dt = new_obj.new_end_dt

                        else:
                            new_obj = objs
                            days_of_week = objs.u_days_list
                            start_dt = new_obj.new_start_dt
                            end_dt = new_obj.new_end_dt


                    else:
                        new_obj = objs
                        days_of_week = objs.u_days_list

                        start_dt = objs.new_start_dt
                        end_dt = objs.new_end_dt
                else:
                    new_obj = objs
                    days_of_week = objs.u_days_list
                    start_dt = new_obj.new_start_dt
                    end_dt = new_obj.new_end_dt

            else:
                conflicts = False

    return True, list, None


def suspend_overlapping_schedules(sleepmode):
    # when sleep mode is active, this util is called to suspend all overlapping schedules

    if time.tzname[0] == 'UTC':
        current_datetime = datetime.datetime.now()
    else:
        current_datetime = datetime.datetime.now()

    start_datetime = sleepmode.new_start_dt
    end_datetime = sleepmode.new_end_dt
    days_of_week = sleepmode.u_days_list

    # returns schedules that conflict with this sleep mode.
    all_schedules = updated_conflicts(new_obj=sleepmode, start_dt=start_datetime,
                                      end_dt=end_datetime, days_of_week=days_of_week,
                                      sch_type=[IopOptionsEnums.IOP_SCHEDULE_ON_DEMAND,
                                                IopOptionsEnums.IOP_QUICK_SCHEDULE,
                                                IopOptionsEnums.IOP_USE_NOW,
                                                IopOptionsEnums.IOP_SCHEDULE_DAILY])

    for a_s in all_schedules:

        try:
            act = Activity.objects.get(
                activity_schedule=a_s)  # check if there's an activity of the corresponding schedule
            act.activity_status = Options.objects.get(
                id=IopOptionsEnums.IOP_SCHEDULE_SKIPPED)  # Marks the activity as cancelled
            act.save()
        except:
            act = create_iop_activity(a_s,
                                      state=IopOptionsEnums.IOP_SCHEDULE_SKIPPED)  # create an activity with cancelled state
            act.save()
        try:
            a_q = ActivityQueue.objects.get(activity_schedule=a_s)  # Fethces queue
            if a_q.activity_schedule.activity_type.id in [IopOptionsEnums.IOP_SCHEDULE_ON_DEMAND,
                                                          IopOptionsEnums.IOP_USE_NOW]:  # Check if schedule is of type once or use now
                a_s.schedule_activity_status = Options.objects.get(id=OptionsEnum.INACTIVE)

            else:  # if the schedule is of type recurring/quick, shift it to next weekday
                u_days_list = a_s.u_days_list

                today = current_datetime.date()  # changed from current_datetime.date().today() to current_datetime.date()

                if today.weekday() != int(a_s.u_days_list):
                    days_diff = (a_s.start_date - today).days
                    today = today + timedelta(days=days_diff)

                upcoming_date = today + timedelta(days=7)

                a_s.start_date = upcoming_date

                if a_s.multi_days is True:
                    a_s.end_date = upcoming_date + timedelta(days=1)

                else:
                    a_s.end_date = upcoming_date

            a_s.new_start_dt = parse(str(a_s.start_date) + '-' + str(a_s.u_activity_start_time))
            a_s.new_end_dt = parse(str(a_s.end_date) + '-' + str(a_s.u_activity_start_time))
            a_s.save()
            a_q.delete()

        except:
            pass

def appliance_error(device_id):
    try:
        querysets = HypernetPreData.objects.filter(device_id=device_id).latest('timestamp')
        if querysets.heartrate_value is 5 or querysets.heartrate_value is 1 or querysets.heartrate_value is 2 or querysets.inactive_score is not 0:
            erro_dict={'error':True,'error_score':querysets.inactive_score, 'chs': querysets.heartrate_value}
            return erro_dict
        return {'error':False,'check':True}
    except:
        try:
            querysets = HypernetPostData.objects.filter(device_id=device_id).latest('timestamp')
            if querysets.heartrate_value is 5 or querysets.heartrate_value is 1 or querysets.heartrate_value is 2 or querysets.inactive_score is not 0:
                erro_dict={'error':True,'error_score':querysets.inactive_score, 'chs': querysets.heartrate_value}
                return erro_dict
            return {'error':False,'check':True}
        except:
            return {'error':False}

def get_chs_value_from_hyperpredata_hyperpostdata(device_id):
    try:
        querysets = HypernetPreData.objects.filter(device_id=device_id).latest('timestamp')
        if querysets.heartrate_value is not 5 or querysets.heartrate_value is not 4:
            return querysets.heartrate_value
        return None
    except:
        try:
            querysets = HypernetPostData.objects.filter(device_id=device_id).latest('timestamp')
            if querysets.heartrate_value is not 5 or querysets.heartrate_value is not 4:
                return querysets.heartrate_value
            return None
        except:
            return None
