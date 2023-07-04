import random

from django.db.models import Sum
from hypernet.entity.utils import random_date
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
from hypernet.entity.job_V2.utils import get_dates, util_create_activity_queue, util_get_schedules, util_get_activities, \
    util_get_bins_location, util_get_activity_data, util_get_bin_with_location, util_upcoming_activities, \
    get_conflicts, suspend_activity_schedule, util_get_bins_action_data, \
    util_get_schedule_total_count, util_get_bins_collection_data, check_suspend, \
    get_activity_bins, delete_bincollection_data, update_activity_schedule, \
    check_sleep_mode_conflicts, check_generic_conflicts, \
    revert_schedules, suggest_events_on_usage, updated_check_conflicts_with_use_now, \
    query_all_schedules, updated_conflicts, appliance_error
from hypernet.constants import *
from hypernet.enums import OptionsEnum, IopOptionsEnums, IOFOptionsEnum, ModuleEnum, DeviceTypeEntityEnum
from hypernet.models import HypernetNotification, Entity
from hypernet.utils import generic_response, exception_handler, get_default_param, get_list_param
import hypernet.utils as h_utils
from customer.models import CustomerPreferences
from iof.models import ActivitySchedule, ActivityQueue, BinCollectionData, Activity,LogisticAggregations
from iof.serializers import ActivityScheduleSerializer, ActivityDataSerializer, BinCollectionDataSerializer
from iof.serializers import ActivitySerializer
from iof.utils import create_bin_collection_data, create_activity_data
from hypernet.notifications.utils import send_action_notification, save_users_group, send_notification_violations
from hypernet.enums import IopOptionsEnums,Enum
# ---------------------------------------------------------------------------------------------------------
from options.models import Options
import traceback
from user.models import User
import datetime
import time
from collections import OrderedDict
from iop.utils import get_user_privelages_info, check_overlapping_schedules, calculcate_ttr, calculate_tau, \
    select_rand_qs_duration, set_device_temperature,set_device_temperature_for_quick_sch, TTR_calculation_use_now_events,calculate_overlapping,calculate_temperature_time_to_ready
from dateutil.parser import parse
enum=Enum()

@transaction.atomic()
@api_view(['POST', 'PATCH'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def add_activity_scehdule(request):
    from dateutil.parser import parse
    days_list = get_default_param(request, 'days_list', None)
    custom_days = get_default_param(request, 'custom_days', None)

    request.POST._mutable = True
    request.data['status'] = OptionsEnum.ACTIVE
    request.data['customer'] = h_utils.get_customer_from_request(request, None)
    request.data['module'] = h_utils.get_module_from_request(request, None)
    request.data['activity_type'] = IOFOptionsEnum.BIN_COLLECTION_JOB
    request.data['schedule_activity_status'] = OptionsEnum.ACTIVE
    if request.data.get('id'):
        request.data['start_date'] = (timezone.now().date()).strftime('%Y-%m-%d')
    # request.data['modified_by'] = 1
    request.data['modified_by'] = h_utils.get_user_from_request(request, None).id
    if days_list:
        request.data['days_list'] = ",".join(str(bit) for bit in days_list)
    # elif custom_days:

    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: HTTP_ERROR_CODE, RESPONSE_DATA: []}
    http_status = HTTP_SUCCESS_CODE
    pk = request.data.get('id')
    if pk:
        ActivityQueue.objects.filter(activity_schedule_id=pk, customer=request.data.get('customer')).delete()
        queue_obj = ActivitySchedule.objects.get(pk=pk, customer_id=int(request.data.get('customer')))
        serializer = ActivityScheduleSerializer(queue_obj, data=request.data, partial=True,
                                                context={'request': request})
    else:
        serializer = ActivityScheduleSerializer(data=request.data, partial=True, context={'request': request})
    try:
        preferences = CustomerPreferences.objects.get(customer_id=h_utils.get_customer_from_request(request, None))
    except:
        response_body[RESPONSE_MESSAGE] = {'message': 'Customer invalid.'}
        http_status = 400
        response_body[RESPONSE_STATUS] = STATUS_ERROR

    if serializer.is_valid():
        activity_datetime = str(serializer.validated_data.get('start_date')) + ' ' + str(
            serializer.validated_data.get('activity_start_time'))
        activity_datetime = parse(activity_datetime)
        activity_datetime = activity_datetime.replace(tzinfo=timezone.utc)

        if serializer.validated_data.get('end_date'):
            activity_end_datetime = str(serializer.validated_data.get('end_date')) + ' ' + str(
                serializer.validated_data.get('activity_start_time'))
            activity_end_datetime = parse(activity_end_datetime)
            activity_end_datetime = activity_end_datetime.replace(tzinfo=timezone.utc)
        else:
            activity_end_datetime = None
        now_time = timezone.now()
        time_diff = now_time + timezone.timedelta(minutes=15)

        if activity_datetime < now_time:
            if activity_end_datetime:
                if now_time > activity_end_datetime:
                    response_body[RESPONSE_MESSAGE] = {
                        'message': 'Invalid Date Selected. You cannot select a past date.', 'time': False}
                    http_status = 200
                    response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                    return generic_response(response_body=response_body, http_status=http_status)
            else:
                response_body[RESPONSE_MESSAGE] = {'message': 'Invalid Date Selected. You cannot select a past date.',
                                                   'time': False}
                http_status = 200
                response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                return generic_response(response_body=response_body, http_status=http_status)

        if serializer.is_valid():
            if request.data.get('activity_type') == IOFOptionsEnum.BIN_COLLECTION_JOB:
                if days_list is None and custom_days is None:
                    if activity_datetime >= time_diff:
                        if pk:
                            if serializer.validated_data.get('end_date') is None:
                                conflict, activity_schedule, conflict_time = get_conflicts(preferences=preferences,
                                                                                           data=serializer.validated_data,
                                                                                           days_list=None)
                            else:
                                conflict, activity_schedule, conflict_time = get_conflicts(preferences=preferences,
                                                                                           data=serializer.validated_data,
                                                                                           days_list=None,
                                                                                           start_date=timezone.now().date())

                        else:
                            conflict, activity_schedule, conflict_time = get_conflicts(preferences=preferences,
                                                                                       data=serializer.validated_data,
                                                                                       days_list=None)
                        if conflict:
                            user = h_utils.get_user_from_request(request, None)
                            if activity_schedule is None:
                                response_body[RESPONSE_MESSAGE] = {
                                    'message': 'Schedule Conflicts with an ongoing activity',
                                    'conflict': True,
                                    'suspend': False}
                            elif type(activity_schedule) is ActivitySchedule:
                                if activity_schedule.modified_by == user:
                                    response_body[RESPONSE_MESSAGE] = {'message': 'Schedule Conflicts with ' +
                                                                                  activity_schedule.get_name(),
                                                                       'time': str(conflict_time),
                                                                       'conflict': True,
                                                                       'suspend': True, 'id': activity_schedule.id}
                                else:
                                    response_body[RESPONSE_MESSAGE] = {'message': 'Schedule Conflicts with ' +
                                                                                  activity_schedule.get_name(),
                                                                       'time': str(conflict_time),
                                                                       'conflict': True,
                                                                       'suspend': False}
                            else:
                                response_body[RESPONSE_MESSAGE] = {
                                    'message': 'Schedule Conflicts with activity on ',
                                    'conflict': True,
                                    'time': str(activity_schedule),
                                    'suspend': False}
                            http_status = HTTP_SUCCESS_CODE
                        else:
                            ser = serializer.save()
                            if pk:
                                if serializer.data.get('end_date') is None:
                                    util_create_activity_queue(serializer=ser, days_list=None,
                                                               start_date=None)
                                else:
                                    util_create_activity_queue(serializer=ser, days_list=None,
                                                               start_date=timezone.now().date())
                            else:
                                util_create_activity_queue(serializer=ser, days_list=None)

                            response_body[RESPONSE_MESSAGE] = {'message': TEXT_OPERATION_SUCCESSFUL, 'conflict': False}
                            http_status = HTTP_SUCCESS_CODE
                    else:
                        response_body[RESPONSE_MESSAGE] = {
                            'message': 'Schedules cannot be created within next 15 mins, \n NOTE: \n select time atleast 15 mins ahead.'}
                        http_status = HTTP_SUCCESS_CODE
                        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                        return generic_response(response_body=response_body, http_status=http_status)

                if days_list is not None and custom_days is None:
                    # if activity_datetime >=time_diff:
                    if pk:
                        conflict, activity_schedule, conflict_time = get_conflicts(preferences=preferences,
                                                                                   data=serializer.validated_data,
                                                                                   days_list=days_list,
                                                                                   start_date=timezone.now().date())
                    else:
                        conflict, activity_schedule, conflict_time = get_conflicts(preferences=preferences,
                                                                                   data=serializer.validated_data,
                                                                                   days_list=days_list)

                    if conflict:
                        user = h_utils.get_user_from_request(request, None)
                        if activity_schedule is None:
                            response_body[RESPONSE_MESSAGE] = {'message': 'Schedule Conflicts with Activity',
                                                               'conflict': True,
                                                               'suspend': False}
                        elif type(activity_schedule) is ActivitySchedule:
                            if activity_schedule.modified_by == user:
                                response_body[RESPONSE_MESSAGE] = {'message': 'Schedule Conflicts with ' +
                                                                              activity_schedule.get_name(),
                                                                   'time': str(conflict_time),
                                                                   'conflict': True, 'suspend': True,
                                                                   'id': activity_schedule.id}
                            else:
                                response_body[RESPONSE_MESSAGE] = {'message': 'Schedule Conflicts with ' +
                                                                              activity_schedule.get_name(),
                                                                   'conflict': True,
                                                                   'time': str(conflict_time),
                                                                   'suspend': False}
                        else:
                            response_body[RESPONSE_MESSAGE] = {'message': 'Schedule Conflicts with Activity on ',
                                                               'conflict': True,
                                                               'time': str(activity_schedule),
                                                               'suspend': False}

                        http_status = HTTP_SUCCESS_CODE
                    else:
                        ser = serializer.save()
                        if pk:
                            util_create_activity_queue(serializer=ser, days_list=days_list,
                                                       start_date=timezone.now().date())
                        else:
                            util_create_activity_queue(serializer=ser, days_list=days_list)

                        response_body[RESPONSE_MESSAGE] = {'message': TEXT_SUCCESSFUL, 'conflict': False}
                        http_status = HTTP_SUCCESS_CODE

                # New custom datepicker
                if days_list is None and custom_days is not None:
                    if pk:
                        conflict, activity_schedule, conflict_time = get_conflicts(preferences=preferences,
                                                                                   data=serializer.validated_data,
                                                                                   days_list=None,
                                                                                   start_date=timezone.now().date(),
                                                                                   custom_dates=custom_days)
                    else:
                        conflict, activity_schedule, conflict_time = get_conflicts(preferences=preferences,
                                                                                   data=serializer.validated_data,
                                                                                   days_list=None,
                                                                                   custom_dates=custom_days)

                    if conflict:
                        user = h_utils.get_user_from_request(request, None)
                        if activity_schedule is None:
                            response_body[RESPONSE_MESSAGE] = {'message': 'Schedule Conflicts with Activity',
                                                               'conflict': True,
                                                               'suspend': False}
                        elif type(activity_schedule) is ActivitySchedule:
                            if activity_schedule.modified_by == user:
                                response_body[RESPONSE_MESSAGE] = {'message': 'Schedule Conflicts with ' +
                                                                              activity_schedule.get_name(),
                                                                   'time': str(conflict_time),
                                                                   'conflict': True, 'suspend': True,
                                                                   'id': activity_schedule.id}
                            else:
                                response_body[RESPONSE_MESSAGE] = {'message': 'Schedule Conflicts with ' +
                                                                              activity_schedule.get_name(),
                                                                   'conflict': True,
                                                                   'time': str(conflict_time),
                                                                   'suspend': False}
                        else:
                            response_body[RESPONSE_MESSAGE] = {'message': 'Schedule Conflicts with Activity on ',
                                                               'conflict': True,
                                                               'time': str(activity_schedule),
                                                               'suspend': False}

                        http_status = HTTP_SUCCESS_CODE
                    else:
                        ser = serializer.save()
                        if pk:
                            util_create_activity_queue(serializer=ser, days_list=days_list,
                                                       start_date=timezone.now().date(), custom_days=custom_days)
                        else:
                            util_create_activity_queue(serializer=ser, days_list=days_list, custom_days=custom_days)

                        response_body[RESPONSE_MESSAGE] = {'message': TEXT_SUCCESSFUL, 'conflict': False}
                        http_status = HTTP_SUCCESS_CODE

        else:
            error_list = []
            for errors in serializer.errors:
                error_list.append("invalid  " + errors + "  given.")
            response_body[RESPONSE_MESSAGE] = error_list

        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        return generic_response(response_body=response_body, http_status=http_status)

    else:
        response_body[RESPONSE_MESSAGE] = {'message': h_utils.error_message_serializers(serializer.errors)}
        http_status = 200
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
        return generic_response(response_body=response_body, http_status=http_status)


@api_view(['POST'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def suspend_schedule(request):
    schedule_id = h_utils.get_default_param(request, 'id', None)
    suspend = h_utils.get_default_param(request, 'suspend', None)

    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: HTTP_ERROR_CODE, RESPONSE_DATA: []}
    http_status = HTTP_SUCCESS_CODE
    if schedule_id:
        try:
            activity_schedule = ActivitySchedule.objects.get(id=schedule_id)
            if suspend:
                flag = check_suspend(schedule_id)
                if flag:
                    suspend_activity_schedule(schedule_id)
                    activity_schedule.schedule_activity_status_id = IOFOptionsEnum.SUSPENDED
                    activity_schedule.save()
                    response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
                    response_body[RESPONSE_MESSAGE] = "Schedule suspended successfully"
                else:
                    response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                    response_body[RESPONSE_MESSAGE] = "Cannot suspended successfully, it has ongoing activities"
            else:
                response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
        except:
            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['PATCH'])
# @append_request_params
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def mark_activity_inactive(request):
    status = int(h_utils.get_data_param(request, 'status', None))
    # activity_id = h_utils.get_data_param(request, 'activity_id', None)
    list_id = h_utils.get_data_param(request, 'id_list', None)

    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    http_status = HTTP_ERROR_CODE

    for id in list_id:
        if status in [OptionsEnum.INACTIVE]:
            activity_schedule = ActivitySchedule.objects.get(id=id)
            activity_schedule.schedule_activity_status = OptionsEnum.INACTIVE
            activity_schedule.save()

            response_body[RESPONSE_MESSAGE] = {'success_message': TEXT_OPERATION_SUCCESSFUL}
            http_status = HTTP_SUCCESS_CODE
            response_body[RESPONSE_STATUS] = STATUS_OK

        else:
            response_body[RESPONSE_MESSAGE] = {'success_message': TEXT_OPERATION_UNSUCCESSFUL}
            http_status = HTTP_ERROR_CODE
            response_body[RESPONSE_STATUS] = STATUS_ERROR

    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['PATCH'])
# @append_request_params
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def edit_activity_scehdule(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    try:

        return add_activity_scehdule(request=request)

    except:
        response_body[RESPONSE_MESSAGE] = {'error_message': TEXT_OPERATION_UNSUCCESSFUL}
        http_status = HTTP_ERROR_CODE
        response_body[RESPONSE_STATUS] = STATUS_ERROR
        return generic_response(response_body=response_body, http_status=http_status)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_activity_schedules(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    customer_id = h_utils.get_customer_from_request(request, None)
    sch_id = h_utils.get_default_param(request, 'schedule_id', None)
    s_id = h_utils.get_default_param(request, 'status_id', None)
    t_id = h_utils.get_default_param(request, 'truck_id', None)
    d_id = h_utils.get_default_param(request, 'driver_id', None)
    a_id = h_utils.get_default_param(request, 'activity_id', None)
    start_date = h_utils.get_default_param(request, 'start_date', None)
    end_date = h_utils.get_default_param(request, 'end_date', None)
    http_status = HTTP_SUCCESS_CODE
    activities_list = []
    schedules_list = []

    result_list = {}
    # Adding a single schedule
    schedules = util_get_schedules(c_id=customer_id, t_id=t_id, d_id=d_id, sch_id=sch_id, s_id=s_id)
    for obj in schedules:
        schedules_data = ActivityScheduleSerializer(obj, context={'request': request})
        sch_dict = schedules_data.data.copy()
        sch_dict['action_items'] = util_get_bins_location(action_items=schedules_data.data['action_items'])
        sch_dict['completion_percentage'] = util_get_schedule_total_count(sch_id=obj.id)
        schedules_list.append(sch_dict)
    result_list['schedules'] = schedules_list

    activities = util_get_activities(c_id=customer_id, t_id=t_id, d_id=d_id, sch_id=sch_id, s_id=s_id,
                                     a_id=a_id, start_date=start_date, end_date=end_date)
    for obj in activities:
        activities_data = ActivitySerializer(obj, context={'request': request})
        act_dict = activities_data.data.copy()
        act_dict['action_items'] = util_get_bins_location(action_items=activities_data.data['action_items'])
        activities_list.append(act_dict)
    result_list['activities'] = activities_list

    upcoming_activity = util_upcoming_activities(c_id=customer_id, sch_id=sch_id, t_id=t_id, d_id=d_id,
                                                 start_date=start_date, end_date=end_date)
    if upcoming_activity:
        upcoming_activity = upcoming_activity[0]
        result_list['upcoming_activity'] = upcoming_activity.as_queue_json()

    response_body[RESPONSE_DATA] = result_list
    response_body[RESPONSE_MESSAGE] = {'success': TEXT_OPERATION_SUCCESSFUL}
    response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    return generic_response(response_body=response_body, http_status=http_status)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_activities_data(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    customer_id = h_utils.get_customer_from_request(self, None)
    sch_id = h_utils.get_default_param(self, 'schedule_id', None)
    s_id = h_utils.get_default_param(self, 'status_id', None)
    t_id = h_utils.get_default_param(self, 'truck_id', None)
    d_id = h_utils.get_default_param(self, 'driver_id', None)
    a_id = h_utils.get_default_param(self, 'activity_id', None)
    start_date = h_utils.get_default_param(self, 'start_date', None)
    end_date = h_utils.get_default_param(self, 'end_date', None)

    activities_list = []
    schedules_list = []

    result_dict = {}
    activity_data = []
    # Adding a single schedule
    if customer_id:

        if a_id:
            activity_data = util_get_activity_data(c_id=customer_id, t_id=t_id, d_id=d_id, a_id=a_id, s_id=s_id,
                                                   start_date=start_date, end_date=end_date)

        activities = util_get_activities(c_id=customer_id, t_id=t_id, d_id=d_id, sch_id=sch_id, s_id=s_id,
                                         a_id=a_id, start_date=start_date, end_date=end_date)

        for obj in activities:
            activities_data = ActivitySerializer(obj, context={'request': self})
            act_dict = activities_data.data.copy()
            if obj.activity_status.id not in [IOFOptionsEnum.COMPLETED, IOFOptionsEnum.ABORTED]:
                act_dict[
                    'truck_device_id'] = obj.primary_entity.device_name.device_id if obj.primary_entity.device_name.device_id else None
            act_dict[
                'truck_type'] = obj.primary_entity.entity_sub_type.id if obj.primary_entity.entity_sub_type else None
            act_dict[
                'truck_type_label'] = obj.primary_entity.entity_sub_type.label if obj.primary_entity.entity_sub_type else None

            invoices = util_get_bins_collection_data(c_id=customer_id, b_id=None, s_id=s_id, a_id=a_id, sup_id=None,
                                                     d_id=d_id, t_id=t_id, start_date=start_date, end_date=end_date). \
                filter(status_id=IOFOptionsEnum.COLLECTED).values('invoice') \
                .annotate(total_invoice=Sum('invoice'))

            # act_dict['total_invoice'] = invoices['invoice']0
            if act_dict['action_items']:
                act_dict['action_items'] = util_get_bins_location(action_items=None, activity_id=obj.id)

            activities_list.append(act_dict)
        result_dict['activity'] = activities_list

        for obj in activity_data:
            schedules_data = ActivityDataSerializer(obj, context={'request': self})
            sch_dict = schedules_data.data.copy()
            if sch_dict['action_items']:
                sch_dict['action_items'] = util_get_bin_with_location(bin=sch_dict['action_items'])

            if sch_dict['supervisor']:
                sch_dict['supervisor'] = util_get_bin_with_location(bin=sch_dict['supervisor'])

            schedules_list.append(sch_dict)
        result_dict['activity_data'] = schedules_list

        response_body[RESPONSE_DATA] = result_dict
        response_body[RESPONSE_MESSAGE] = {'success': TEXT_OPERATION_SUCCESSFUL}
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    else:
        response_body[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_activities_details(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
    customer_id = h_utils.get_customer_from_request(self, None)
    sch_id = h_utils.get_default_param(self, 'schedule_id', None)
    s_id = h_utils.get_default_param(self, 'status_id', None)
    t_id = h_utils.get_default_param(self, 'truck_id', None)
    d_id = h_utils.get_default_param(self, 'driver_id', None)
    a_id = h_utils.get_default_param(self, 'activity_id', None)
    start_date = h_utils.get_default_param(self, 'start_date', None)
    end_date = h_utils.get_default_param(self, 'end_date', None)

    activities_list = []
    schedules_list = []
    result_list = {}

    activities = util_get_activities(c_id=customer_id, t_id=t_id, d_id=d_id, sch_id=sch_id, s_id=s_id,
                                     a_id=a_id, start_date=start_date, end_date=end_date)
    for obj in activities:
        activities_data = ActivitySerializer(obj, context={'request': self})
        act_dict = activities_data.data.copy()
        act_dict['action_items'] = util_get_bins_location(action_items=activities_data.data['action_items'])
        activities_list.append(act_dict)
    result_list['activity'] = activities_list

    response_body[RESPONSE_DATA] = result_list
    response_body[RESPONSE_MESSAGE] = {'success': TEXT_OPERATION_SUCCESSFUL}

    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_upcoming_activities(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    customer_id = h_utils.get_customer_from_request(self, None)
    start_date = h_utils.get_default_param(self, 'start_date', None)
    end_date = h_utils.get_default_param(self, 'end_date', None)

    upcoming_activities_list = []

    upcoming_activities_dict = {}
    upcoming_activity = util_upcoming_activities(c_id=customer_id, sch_id=None, t_id=None, d_id=None,
                                                 start_date=start_date, end_date=end_date)
    for obj in upcoming_activity:
        upcoming_activities_dict['upcoming_activity'] = obj.as_queue_json()
        upcoming_activities_list.append(upcoming_activities_dict.copy())

    response_body[RESPONSE_DATA] = upcoming_activities_list
    response_body[RESPONSE_MESSAGE] = {'success': TEXT_OPERATION_SUCCESSFUL}

    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_bins_activities(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    customer_id = h_utils.get_customer_from_request(request, None)
    bin = h_utils.get_default_param(request, 'bin_id', None)
    status_id = h_utils.get_default_param(request, 'status_id', None)
    start_date = h_utils.get_default_param(request, 'start_datetime', None)
    end_date = h_utils.get_default_param(request, 'end_datetime', None)

    bin_collections_list = []

    upcoming_activities_dict = {}
    upcoming_activity = util_get_bins_action_data(c_id=customer_id, b_id=bin, s_id=status_id, start_date=start_date,
                                                  end_date=end_date).order_by('-timestamp')
    for obj in upcoming_activity:
        bin_data = ActivityDataSerializer(obj, context={'request': request})
        bin_data = bin_data.data.copy()
        bin_collections_list.append(bin_data)
    upcoming_activities_dict['bins_collection_data'] = bin_collections_list
    response_body[RESPONSE_DATA] = bin_collections_list
    response_body[RESPONSE_MESSAGE] = {'success': TEXT_OPERATION_SUCCESSFUL}
    response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE

    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['POST'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def update_running_activity(request):
    response_body = {RESPONSE_MESSAGE: "Updated Successfully!", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
    http_status = HTTP_SUCCESS_CODE
    customer_id = h_utils.get_customer_from_request(request, None)
    activity_id = h_utils.get_default_param(request, 'activity_id', None)
    bins_list = h_utils.get_default_param(request, 'bins', None)
    action = h_utils.get_default_param(request, 'action', None)

    activity = util_get_activities(customer_id, None, None, None, None, activity_id, None, None).first()

    if activity.activity_status.id not in [IOFOptionsEnum.COMPLETED, IOFOptionsEnum.ABORTED]:
        logistic_job = create_activity_data(activity_id, activity.primary_entity.id, activity.actor.id, timezone.now(),
                                            IOFOptionsEnum.ACTIVITY_UPDATED, None, None, customer_id,
                                            activity.module_id,
                                            supervisor=None)
        logistic_job.save()
        if action:
            activity.activity_status = Options.objects.get(id=IOFOptionsEnum.ABORTED)
            activity.save()
            a_data = create_activity_data(activity.id, activity.primary_entity.id,
                                          activity.actor.id, timezone.now(),
                                          IOFOptionsEnum.ABORTED, None, None, activity.customer_id,
                                          activity.module_id)
            a_data.save()
            BinCollectionData.objects.filter(activity=activity, status_id=IOFOptionsEnum.UNCOLLECTED).update(
                status_id=IOFOptionsEnum.ABORT_COLLECTION)
            if (activity.activity_schedule.end_date is None) or (
                        activity.activity_schedule.end_date <= timezone.now().date()):
                activity.activity_schedule.schedule_activity_status = Options.objects.get(id=OptionsEnum.INACTIVE)
                activity.activity_schedule.save()
            try:
                HypernetNotification.objects.filter(
                    type_id__in=[IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW,
                                 IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_NO_ACTION_ACCEPT_REJECT,
                                 IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_DRIVER_REJECT],
                    activity_id=activity.id,
                ).update(status_id=OptionsEnum.INACTIVE)
            except:
                pass
            notification = send_action_notification(activity.primary_entity.id, activity.actor.id, activity.id,
                                                    activity,
                                                    "This Activity has been aborted by your administrator. It is no longer valid.",
                                                    IOFOptionsEnum.NOTIFICATION_DRIVER_ACKNOWLEDGE_ACTIVITY_ABORT)
            notification.save()
            save_users_group(notification, [User.objects.get(associated_entity=activity.actor).id])

            response_body[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: True}
            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
            return generic_response(response_body=response_body, http_status=http_status)
        else:
            if not bins_list:
                response_body[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: True}
                response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                response_body[
                    RESPONSE_MESSAGE] = "Bin list cannot be empty. Please select at least one bin."
                return generic_response(response_body=response_body, http_status=http_status)
            bins_in_activity = get_activity_bins(activity_id)

            for b1 in bins_in_activity:
                if b1 in bins_list:
                    pass
                else:
                    check, message = delete_bincollection_data(b1, activity_id)
                    if not check:
                        response_body[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: True}
                        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                        response_body[
                            RESPONSE_MESSAGE] = message
                        return generic_response(response_body=response_body, http_status=http_status)
            for b2 in bins_list:
                if b2 in bins_in_activity:
                    pass
                else:
                    data = create_bin_collection_data(activity_id, activity.primary_entity.id, activity.actor.id,
                                                      timezone.now(),
                                                      IOFOptionsEnum.UNCOLLECTED, b2, customer_id, activity.module.id)
                    if data.activity_id != activity_id:
                        response_body[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: True}
                        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                        response_body[
                            RESPONSE_MESSAGE] = "Bin is already part of another running activity. Bin: " + data.action_item.name
                        return generic_response(response_body=response_body, http_status=http_status)
                    if data.status_id == IOFOptionsEnum.UNCOLLECTED:
                        data.save()
                    else:
                        response_body[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: True}
                        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                        response_body[
                            RESPONSE_MESSAGE] = "Bin is already collected in an ongoing activity and cannot be collected again. Bin: " + data.action_item.name
                        return generic_response(response_body=response_body, http_status=http_status)

            activity.action_items = ','.join(map(str, bins_list))
            activity.save()
            notification = send_action_notification(activity.primary_entity.id, activity.actor.id, activity.id,
                                                    activity, "Bins have been updated by your administrator.",
                                                    IOFOptionsEnum.NOTIFICATION_DRIVER_ACKNOWLEDGE_BINS_UPDATE)
            notification.save()
            save_users_group(notification, [User.objects.get(associated_entity=activity.actor).id])
            return generic_response(response_body=response_body, http_status=http_status)

    else:
        response_body[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: True}
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
        response_body[
            RESPONSE_MESSAGE] = "Activity can no longer be updated. It may have been completed already."
        return generic_response(response_body=response_body, http_status=http_status)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_collection_events(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    customer_id = h_utils.get_customer_from_request(request, None)
    truck = h_utils.get_default_param(request, 'truck_id', None)
    driver = h_utils.get_default_param(request, 'driver_id', None)
    start_date = h_utils.get_default_param(request, 'start_date', None)
    end_date = h_utils.get_default_param(request, 'end_date', None)

    bin_collections_list = []

    collection_events = util_get_bins_collection_data(customer_id, None, None, None, None, driver, truck, start_date,
                                                      end_date)
    for obj in collection_events:
        collection_data = BinCollectionDataSerializer(obj, context={'request': request})
        collection_data = collection_data.data.copy()
        bin_collections_list.append(collection_data)

    response_body[RESPONSE_DATA] = bin_collections_list
    response_body[RESPONSE_MESSAGE] = {'success': TEXT_OPERATION_SUCCESSFUL}
    response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE

    return generic_response(response_body=response_body, http_status=200)


@transaction.atomic()
@api_view(['POST', 'PATCH'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def add_activity_scehdule_appliance(request):
    from dateutil.parser import parse
    # days_list = get_default_param(request, 'days_list', None)
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: HTTP_ERROR_CODE, RESPONSE_DATA: []}
    http_status = HTTP_SUCCESS_CODE
    try:
        request.POST._mutable = True
        device_id=request.data['primary_entity']
        appliance_check=appliance_error(device_id)
        check_error=appliance_check.pop('error',True)
        device = Entity.objects.get(id=device_id)
        try:
            online_status_device = LogisticAggregations.objects.get(device=device_id).online_status
        except Exception as e:
            print(e)
            online_status_device = False
        print(online_status_device)
        if online_status_device is False:
            response_body[RESPONSE_DATA] = []
            response_body[RESPONSE_MESSAGE] = {'message':"You cannot create an event for " + device.name + " due to offline appliance."}
            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
            return generic_response(response_body=response_body, http_status=http_status)
        if check_error:
            response_body[RESPONSE_DATA] = []
            response_body[RESPONSE_MESSAGE] = {'message':"You cannot create an event for " + device.name + " due to fault mode."}
            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
            return generic_response(response_body=response_body, http_status=http_status)
        else: 
            request.data['status'] = OptionsEnum.ACTIVE
            request.data['customer'] = h_utils.get_customer_from_request(request, None)
            request.data['module'] = h_utils.get_module_from_request(request, None)
            request.data['user'] = h_utils.get_user_from_request(request, None)
            request.data['schedule_activity_status'] = OptionsEnum.ACTIVE
            activity_route=h_utils.get_data_param(request, 'activity_route', None)
            start_times = h_utils.get_data_param(request, 'start_times', None)
            start_dt = h_utils.get_data_param(request, 'start_date', None)
            end_times = h_utils.get_data_param(request, 'end_times', None)
            days_list = h_utils.get_data_param(request, 'days_list', None)
            multiple = h_utils.get_data_param(request, 'multiple', None)
            print("===============================================")
            print("DAYS LIST: ", days_list)
            print("====================================================")
            day_count = int(h_utils.get_data_param(request, 'day_count', 0))
            print('day_count:   ', day_count)
            start_times = list(OrderedDict.fromkeys(start_times))
            end_times = list(OrderedDict.fromkeys(end_times))
            schs_ids = []
            timezone_info = time.tzname
            customer = request.data['customer']

            t2 = h_utils.get_data_param(request, 't2', 0)
            if int(t2) is not 0:
                request.data['current_ctt']=t2
            sch_id = h_utils.get_data_param(request, 'sch_id', None)
            print("on start request sch id : ",sch_id)
            last_sch_id = h_utils.get_data_param(request, 'schedule_id', None)
            delay_min = int(h_utils.get_data_param(request, 'delay_mins', 0))
            if last_sch_id:
                try:
                    if delay_min is 0:
                        ActivitySchedule.objects.filter(id=last_sch_id).update(suggestion=True)
                except Exception as e:
                    print(e)

            request.data['modified_by'] = h_utils.get_user_from_request(request, None).id
            tbd_sm = []
            if days_list:
                request.data['days_list'] = ",".join(str(bit) for bit in days_list)

            try:
                appliance = Entity.objects.get(id=request.data['primary_entity'])
                print(appliance.id, ' ', appliance.model)
                '''
                try:
                    status = LogisticAggregations.objects.get(device_id=appliance.id)
                    if status.online_status == True:
                        pass
                    else:
                        response_body[RESPONSE_MESSAGE] = {
                            'message': "Cannot create schedule. Device currently offline",
                            }
                        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                        return generic_response(response_body=response_body, http_status=http_status)
                except:
                    pass
                '''
                user_device_info = get_user_privelages_info(request.data['user'], appliance.id)
                
                if request.data.get('activity_type') in [IopOptionsEnums.IOP_SCHEDULE_ON_DEMAND,
                                                        IopOptionsEnums.IOP_QUICK_SCHEDULE,
                                                        IopOptionsEnums.IOP_SCHEDULE_DAILY]:
                    if user_device_info.can_edit is False:
                        response_body[RESPONSE_MESSAGE] = {
                            'message': "You don't have enough privilege to perform this action",
                            'conflict': True}
                        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                        return generic_response(response_body=response_body, http_status=http_status)

                elif request.data.get('activity_type') == IopOptionsEnums.IOP_SLEEP_MODE:
                    if user_device_info.can_remove is True:
                        response_body[RESPONSE_MESSAGE] = {
                            'message': "You don't have enough privilege to perform this action",
                            'conflict': True}
                        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                        return generic_response(response_body=response_body, http_status=http_status)

            except:
                pass

            if int(request.data.get('activity_type')) == IopOptionsEnums.IOP_SLEEP_MODE:  # quick fix for sleep mode


                start_times = start_times[-1]
                end_times = end_times[-1]

                start_times = [start_times]
                end_times = [end_times]
            print("START TIMES: ", start_times)
            print("END TIMES: ", end_times)
            print(request.data)
            for st, et in zip(start_times, end_times):

                if timezone_info[0] == 'UTC':
                    todays_date = datetime.datetime.now()
                else:
                    todays_date = datetime.datetime.now()

                todays_date = todays_date + datetime.timedelta(days=day_count)
                print('todays_date:     ', todays_date)
                st = parse(str(todays_date) + ' ' + str(st))
                et = parse(str(todays_date) + ' ' + str(et))

                st = st.replace(second=0, microsecond=0)
                et = et.replace(second=0, microsecond=0)
                if int(request.data.get('activity_type')) == IopOptionsEnums.IOP_QUICK_SCHEDULE:
                    
                    
                    for act in activity_route:
                        
                        print(act)
                        request.data['activity_route']=act
                        print("INSIDE QUICK SCHEDULE")
                        days_list = [0, 1, 2, 3, 4, 5, 6]
                        print(days_list)
                        today = datetime.datetime.now()

                        if timezone_info[0] == 'UTC':
                            today = today
                        today = today.replace(second=0, microsecond=0)

                        u_st = st
                        u_et = et

                        if type(u_st) is datetime.time and type(u_et) is datetime.time:
                            u_st = parse(u_st)
                            u_et = parse(u_et)

                        if u_et < u_st:
                            u_et = u_et + datetime.timedelta(days=1)
                            # print("IN IF UET<UST: UET= ", u_et)
                        print(u_st, u_et,'start time and end time in quick schules')
                        rand_st = random_date(u_st, u_et)
                        print("RANDOM ST: ", rand_st)

                        # rand_et = rand_st + datetime.timedelta(hours=1)
                        rand_st = rand_st.replace(second=0)
                        # print("RANDOM ST after sec0: ", rand_st)
                        duration, temp = select_rand_qs_duration(rand_st, appliance.model)
                        # print("DURATION : ",duration)
                        # print("TEMP: ", temp)
                        request.data['action_items'] = temp
                        rand_et = rand_st + datetime.timedelta(minutes=duration)
                        # print("RANDOM ET: ", rand_et)
                        rand_et = rand_et.replace(second=0)
                        # print("RANDOM ET after sec0: ", rand_et)
                        ttr, t2 = calculcate_ttr(appliance, temp, duration=duration)
                        # print("TTR : ", ttr)
                        # print("T2: ", t2)

                        tau = calculate_tau(t2, request.data['action_items'], duration=duration, ent=appliance)
                        # print("TAU= ", tau)
                        request.data['temp_after_usage'] = tau
                        for d in days_list:
                            u_st = rand_st
                            u_et = rand_et

                            if today.date().weekday() == d and today.time() > u_st.time():  # changed from today.date().today().weekday() to today.date().weekday()
                                upcoming_date = today + datetime.timedelta(days=6)
                                print("IN TODAY>DATE>WEEKDAY IF CHECK: upcoming_date=", upcoming_date)

                            else:
                                upcoming_date = today + datetime.timedelta(
                                    (d - today.date().weekday()) % 7)  # calculating upcoming start date for the weekday
                                print("IN TODAY>DATE>WEEKDAY ELSE CHECK: upcoming_date=", upcoming_date)

                            upcoming_date = upcoming_date.date()
                            # print("Upcoming_date_date: ", upcoming_date)
                            d = str(d)
                            request.data['days_list'] = d
                            request.data['u_days_list'] = d
                            if u_et.date() == u_st.date():
                                request.data['start_date'] = upcoming_date
                                request.data['end_date'] = upcoming_date
                                
                            else:
                                request.data['start_date'] = upcoming_date
                                request.data['end_date'] = upcoming_date + datetime.timedelta(days=1)
                                
                                u_et = u_et + datetime.timedelta(days=1)
                                request.data['multi_days'] = True

                            start_date = request.data['start_date']
                            end_date = request.data['end_date']
                    

                            request.data['old_start_dt'] = parse(str(start_date) + '-' + str(u_st.time()))
                            request.data['new_start_dt'] = parse(str(start_date) + '-' + str(u_st.time()))
                            request.data['old_end_dt'] = parse(str(end_date) + '-' + str(u_et.time()))
                            request.data['new_end_dt'] = parse(str(end_date) + '-' + str(u_et.time()))

                            u_st = u_st.time()
                            u_et = u_et.time()

                            request.data['activity_start_time'] = u_st
                            request.data['activity_end_time'] = u_et
                            request.data['u_activity_start_time'] = u_st
                            request.data['u_activity_end_time'] = u_et

                            request.data['days_list'] = d

                            request.data['notes'] = duration

                            serializer = ActivityScheduleSerializer(data=request.data, partial=True,
                                                                    context={'request': request})
                            if serializer.is_valid():
                                # print("DATA FROM SERIALIZER JUST BEFORE SAVE", serializer.validated_data)
                                ser = serializer.save()
                                schs_ids.append(ser.id)  # serializers that are saved for comparison, to be deleted.

                                schs = check_sleep_mode_conflicts(new_obj=ser, start_dt=request.data['new_start_dt'],
                                                                end_dt=request.data['new_end_dt'],
                                                                days_of_week=d)
                                if schs is False:
                                    for id in schs_ids:
                                        ActivitySchedule.objects.filter(id=id).delete()
                                    response_body[RESPONSE_MESSAGE] = {
                                        'message': 'Cannot create schedule due to conflicting sleep mode.',
                                        'conflict': False,
                                    }
                                    response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                                    return generic_response(response_body=response_body, http_status=http_status)
                                
                            else:
                                error_list = []
                                for errors in serializer.errors:
                                    error_list.append("invalid  " + errors + "  given.")
                                response_body[RESPONSE_MESSAGE] = error_list
                                return generic_response(response_body=response_body, http_status=http_status)

                    response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
                    response_body[RESPONSE_MESSAGE] = {'message': TEXT_SUCCESSFUL}

                
                
                if int(request.data.get('activity_type')) == IopOptionsEnums.IOP_SCHEDULE_ON_DEMAND:
                    print('=-=-     IOP_SCHEDULE_ON_DEMAND      -=-=')
                    try:
                        if timezone_info[0] == 'UTC':
                            current_datetime = datetime.datetime.now()
                        else:
                            current_datetime = datetime.datetime.now()

                        current_datetime = current_datetime + datetime.timedelta(days=day_count)
                        print(current_datetime,'current_date_time check')
                        start_date = current_datetime.date()  # change to timezone.now()
                        d = start_date.weekday()
                        print('start date IOP_SCHEDULE_ON_DEMAND',start_date,'')
                        request.data['days_list'] = str(start_date.weekday())
                        request.data['u_days_list'] = str(start_date.weekday())

                        print('current_datetime:    ', current_datetime)
                        print('start_datetime:    ', st)
                        print('start_datetime:    ', st  + datetime.timedelta(hours=5))

                        if day_count > 0:
                            current_datetime = current_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
                        if current_datetime > st:  # change to timezone.now()
                            print('\nin IF statement \n')
                            start_date = current_datetime + datetime.timedelta(days=1) #change 7 day to 1 for check
                        else:
                            print('\nin ELSE statement \n')
                            start_date = current_datetime + datetime.timedelta((d - current_datetime.weekday()) % 7)
                            print("Start date: =-= ", start_date)
                        if et < st:
                            end_date = start_date + datetime.timedelta(days=1)
                            request.data['multi_days'] = True
                            et = et + datetime.timedelta(days=1)
                            duration = ((et - st).total_seconds() / 60)
                            if float(duration) == 0.0:
                                duration = 1.0
                        else:
                            end_date = start_date
                            duration = ((et - st).total_seconds() / 60)
                            if float(duration) == 0.0:
                                duration = 1.0

                        print(duration, 'duration =-=-==-=-=-=')

                        start_date = start_date.date()
                        end_date = end_date.date()

                        request.data['start_date'] = start_date
                        request.data['end_date'] = end_date

                        request.data['old_start_dt'] = parse(str(start_date) + '-' + str(st.time()))
                        request.data['new_start_dt'] = parse(str(start_date) + '-' + str(st.time()))
                        request.data['old_end_dt'] = parse(str(end_date) + '-' + str(et.time()))
                        request.data['new_end_dt'] = parse(str(end_date) + '-' + str(et.time()))
                        # new_st, new_et, ttr, ttr_flag = shift_schedule_times_with_ttr(appliance, request.data['action_items'],
                        #                                                           todays_date, st, et, duration)

                        #    if ttr is None:
                        #        response_body[RESPONSE_MESSAGE] = {
                        #            'message': "Cannot create schedule due to insufficient appliance data inorder to calculate ETA for your schedule. Try again later",
                        #            'conflict': True}
                        #        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                        #        return generic_response(response_body=response_body, http_status=http_status)


                        st = st.time()
                        et = et.time()
                        print(st,'check start time why delay')
                        request.data['notes'] = duration
                        request.data['activity_start_time'] = st
                        request.data['activity_end_time'] = et
                        request.data['u_activity_start_time'] = st
                        request.data['u_activity_end_time'] = et

                        dest_temp = int(request.data['action_items'])

                        print('t2 from request', t2)

                        try:

                            if t2 > 0:
                                tau = calculate_tau(t2, dest_temp, duration=duration, ent=appliance)
                            else:
                                ttr, t2 = calculcate_ttr(appliance, request.data['action_items'], duration=duration)
                                tau = calculate_tau(t2, request.data['action_items'], duration=duration, ent=appliance)
                        except Exception as e:
                            print(e)
                        request.data['temp_after_usage'] = tau

                        schs = check_sleep_mode_conflicts(new_obj=None, start_dt=request.data['new_start_dt'],
                                                        end_dt=request.data['new_end_dt'],
                                                        days_of_week=d, primary_entity=request.data['primary_entity'])

                        if schs is False:
                            message = "Cannot create event due to conflicting sleep mode"
                            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                            response_body[RESPONSE_MESSAGE] = {'message': message, 'conflict': True}
                            return generic_response(response_body=response_body, http_status=http_status)

                        else:
                            if sch_id:
                                try:
                                    obj = ActivitySchedule.objects.get(id=sch_id)
                                    ActivitySchedule.objects.filter(suspended_by=obj).update(suspended_by=None)
                                    obj.suspended_by = None
                                    obj.save()
                                    try:
                                        print("on update : sch id :  ", sch_id)
                                        print("array: ", obj)
                                        if obj:
                                            print("query_set: ", obj)
                                            all_schedules_of_that_week = ActivitySchedule.objects.filter(
                                                primary_entity_id=obj.primary_entity_id,
                                                activity_start_time=obj.activity_start_time,
                                                activity_end_time=obj.activity_end_time).exclude(id=sch_id)
                                            print("all week schedules : ", all_schedules_of_that_week)
                                        else:
                                            pass
                                    except Exception as e:
                                        print(e)
                                        pass
                                    obj.delete()
                                except:
                                    traceback.print_exc()
                                    pass

                        serializer = ActivityScheduleSerializer(data=request.data, partial=True,
                                                                context={'request': request})
                        if serializer.is_valid():
                            print(serializer.validated_data)
                            print("serizlizer is valid -------------------")
                            # try:
                            #     activity_schedule = ActivitySchedule.objects.filter(id=(int(sch_id)-1))
                            #     print("on update : sch id :  ", sch_id)
                            #     print("array: " , activity_schedule)
                            #     if activity_schedule:
                            #         print("query_set: " , activity_schedule[0] )
                            #         all_schedules_of_that_week = ActivitySchedule.objects.filter(primary_entity_id=activity_schedule[0].primary_entity_id ,
                            #                                                                  activity_start_time=activity_schedule[0].activity_start_time,
                            #                                                                  activity_end_time=activity_schedule[0].activity_end_time)
                            #         print("all week schedules : " , all_schedules_of_that_week)
                            #     else:
                            #         pass
                            # except Exception as e:
                            #     print(e)
                            #     pass
                            ser = serializer.save()

                            try:
                                if multiple == True or multiple == "True" and ser:
                                    print(multiple)
                                    all_schedules_of_that_week.update(activity_route=serializer.validated_data.get("activity_route"),
                                                                      activity_start_time=serializer.validated_data.get("activity_start_time"),
                                                                      activity_end_time=serializer.validated_data.get("activity_end_time"),
                                                                      u_activity_start_time=serializer.validated_data.get("u_activity_start_time"),
                                                                      u_activity_end_time=serializer.validated_data.get("u_activity_end_time"),
                                                                      notes=serializer.validated_data.get("notes"))
                            except Exception as e:
                                print(e)
                                pass
                            flag, result, message = updated_check_conflicts_with_use_now(ser, request.data['new_start_dt'],
                                                                                        request.data['new_end_dt'],
                                                                                        start_date,
                                                                                        days_of_week=request.data[
                                                                                            'u_days_list'])
                        
            
                    
                            if flag is False:
                                response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE

                                response_body[RESPONSE_MESSAGE] = {'message': message, 'conflict': True}
                                try:
                                    revert_schedules(result)
                                    ActivitySchedule.objects.filter(suspended_by=ser).update(suspended_by=None)
                                    ActivitySchedule.objects.get(pk=ser.pk).delete()
                                except:
                                    traceback.print_exc()

                                return generic_response(response_body=response_body, http_status=http_status)

                            else:
                                if result:
                                    update_activity_schedule(result)
                                    
                                response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE

                                # send notification to users tellnig them that their schedule has been marked inactive
                                pass
                                response_body[RESPONSE_MESSAGE] = {'message': TEXT_SUCCESSFUL, 'conflict': False,
                                                                }
                        else:
                            traceback.print_exc()
                            error_list = []
                            for errors in serializer.errors:
                                print(errors)
                                error_list.append("invalid  " + errors + "  given.")
                            response_body[RESPONSE_MESSAGE] = error_list
                            return generic_response(response_body=response_body, http_status=http_status)
                    except Exception as e:
                        print('in execption =--------------------')
                        print(e)
                        traceback.print_exc()

                if int(request.data.get('activity_type')) == IopOptionsEnums.IOP_SCHEDULE_DAILY:
        
                    if days_list is not None:
                        for d in days_list:
                            print("DAY IN DAYS LIST: ", d)
                            if isinstance(st, datetime.time):
                                st = parse(str(todays_date) + ' ' + str(st))
                            if isinstance(et, datetime.time):
                                et = parse(str(todays_date) + ' ' + str(et))

                            u_st = st
                            u_et = et
                            print("U_ST: ", u_st)
                            print("U_ET: ", u_et)
                            print("DAY COUNT: ", day_count)
                            if timezone_info[0] == 'UTC':
                                current_datetime = datetime.datetime.now()
                            else:
                                current_datetime = datetime.datetime.now()
                            current_datetime = current_datetime + datetime.timedelta(days=day_count)

                            current_datetime = current_datetime.replace(second=0, microsecond=0)
                            today = current_datetime.date()  # changed from current_datetime.date().today() to current_datetime.date()
                            print("TODAY : ", today)
                            print(today.weekday(),'weekday')
                            if today.weekday() not in days_list:  # check if weekday schedule is made that doesnot include current day.
                                # This is to avoid if user wants to make schedule for
                                #  Monday 1 PM: current day is sunday 3:00 PM.
                                # Then it wil create schedule on upcming monday and not for monday after that.

                                current_datetime = current_datetime.replace(hour=0, minute=0, second=0)
                                print("CURRENT DATETIME IN IF TODAY.WEEKDAY NOT IN DAYS_LIST: ", current_datetime)

                            if today.weekday() == d and current_datetime > u_st:  # change to timezone.now()
                                upcoming_date = today + datetime.timedelta(days=7)
                                print("UPCOMING DATE IN IF TODAY.WEEKDAY == D and CURRENT_DATETIME> u_st", upcoming_date)

                            else:
                                hour_check = u_st.time().hour
                                if hour_check >= 19:
                                    time_delta_value = ((d-1) - today.weekday()) % 7
                                    print("TIME GREATER OR EQUAL TO 19 ")
                                else:
                                    time_delta_value = (d - today.weekday()) % 7
                                    print("TIME LESS THAN 19")
                                print("TIME DELTA VALUE FOR UPCOMING DATE", time_delta_value)
                                upcoming_date = today + datetime.timedelta(time_delta_value)  # calculating upcoming start date for the weekday
                                print("UPCOMING DATE IN ELSE:", upcoming_date)

                            d = str(d)
                            request.data['days_list'] = d
                            request.data['u_days_list'] = d

                            if u_et.time() > u_st.time():
                                print("UPCOMING DATE(start_date and end_date) IN IF U_ET > U_ST", upcoming_date)
                                request.data['start_date'] = upcoming_date
                                request.data['end_date'] = upcoming_date

                                duration = ((u_et - u_st).total_seconds() / 60)
                                print("DURATION IN IF U_ET > U_ST: ", duration)
                            else:
                                request.data['start_date'] = upcoming_date
                                request.data['end_date'] = upcoming_date + datetime.timedelta(days=1)
                                print("UPCOMING DATE(start_date and end_date) IN ELSE", upcoming_date)
                                print("END DATE AFTER +1 in upcoming date", request.data['end_date'] )
                                u_et = u_et + datetime.timedelta(days=1)
                                print("U_et in ELSE(AFter adding 1 day time delta): ",u_et )
                                duration = ((u_et - u_st).total_seconds() / 60)
                                print("Duration in else: ", duration)
                                request.data['multi_days'] = True
                            request.data['notes'] = duration

                            start_date = request.data['start_date']
                            end_date = request.data['end_date']
                            print("START DATE", start_date)
                            print("END DATE", end_date)
                            request.data['old_start_dt'] = parse(str(start_date) + '-' + str(st.time()))
                            request.data['new_start_dt'] = parse(str(start_date) + '-' + str(st.time()))
                            request.data['old_end_dt'] = parse(str(end_date) + '-' + str(et.time()))
                            request.data['new_end_dt'] = parse(str(end_date) + '-' + str(et.time()))
                            st = st.time()
                            et = et.time()
                            u_st = u_st.time()
                            u_et = u_et.time()
                            print("ST", st)
                            print("ET", et)
                            print("U_ST", u_st)
                            print("U_ET", u_et)
                            request.data['activity_start_time'] = st
                            request.data['activity_end_time'] = et
                            request.data['u_activity_start_time'] = u_st
                            request.data['u_activity_end_time'] = u_et

                            dest_temp = int(request.data['action_items'])

                            if t2 > 0:
                                tau = calculate_tau(t2, dest_temp, duration=duration, ent=appliance)
                                print("IN T2 >0 , TAU= ", tau)
                            else:
                                ttr, t2 = calculcate_ttr(appliance, request.data['action_items'], duration=duration)
                                tau = calculate_tau(t2, request.data['action_items'], duration=duration, ent=appliance)
                                print("IN ELSE OF T2>0")
                                print("TAU= ", tau)
                                print("TTR =", ttr)
                                print("T2= ", t2)
                            request.data['temp_after_usage'] = tau

                            schs = check_sleep_mode_conflicts(new_obj=None, start_dt=request.data['new_start_dt'],
                                                            end_dt=request.data['new_end_dt'],
                                                            days_of_week=d,
                                                            primary_entity=request.data['primary_entity'])

                            if schs is False:
                                message = "Cannot create event due to conflicting sleep mode"
                                response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                                response_body[RESPONSE_MESSAGE] = {'message': message, 'conflict': True}
                                return generic_response(response_body=response_body, http_status=http_status)

                            else:
                                if sch_id:
                                    try:
                                        obj = ActivitySchedule.objects.get(id=sch_id)
                                        ActivitySchedule.objects.filter(suspended_by=obj).update(suspended_by=None)
                                        obj.suspended_by = None
                                        obj.save()
                                        try:
                                            print("on update : sch id :  ", sch_id)
                                            print("array: ", obj)
                                            if obj:
                                                print("query_set: ", obj)
                                                all_schedules_of_that_week = ActivitySchedule.objects.filter(
                                                    primary_entity_id=obj.primary_entity_id,
                                                    activity_start_time=obj.activity_start_time,
                                                    activity_end_time=obj.activity_end_time).exclude(id=sch_id)
                                                print("all week schedules : ", all_schedules_of_that_week)
                                            else:
                                                pass
                                        except Exception as e:
                                            print(e)
                                            pass
                                        obj.delete()
                                    except:
                                        traceback.print_exc()
                                        pass

                            serializer = ActivityScheduleSerializer(data=request.data, partial=True,
                                                                    context={'request': request})
                            if serializer.is_valid():
                                ser = serializer.save()
                                print("SERIALIZER SAVED : ", ser)
                                print("SERIALIZER SAVED Data : ", serializer.validated_data)

                                try:
                                    if multiple == True or multiple == "True" and ser:
                                        print(multiple)
                                        all_schedules_of_that_week.update(
                                            activity_route=serializer.validated_data.get("activity_route"),
                                            activity_start_time=serializer.validated_data.get("activity_start_time"),
                                            activity_end_time=serializer.validated_data.get("activity_end_time"),
                                            u_activity_start_time=serializer.validated_data.get(
                                                "u_activity_start_time"),
                                            u_activity_end_time=serializer.validated_data.get("u_activity_end_time"),
                                            notes=serializer.validated_data.get("notes"))

                                except Exception as e:
                                    print(e)
                                    pass

                                flag, result, message = updated_check_conflicts_with_use_now(ser,
                                                                                            request.data['new_start_dt'],
                                                                                            request.data['new_end_dt'],
                                                                                            start_date,
                                                                                            days_of_week=request.data[
                                                                                                'u_days_list'])
                                if flag is False:
                                    response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE

                                    response_body[RESPONSE_MESSAGE] = {'message': message, 'conflict': True}
                                    try:
                                        revert_schedules(result)
                                        ActivitySchedule.objects.filter(suspended_by=ser).update(suspended_by=None)
                                        ActivitySchedule.objects.get(pk=ser.pk).delete()
                                    except:
                                        traceback.print_exc()

                                    return generic_response(response_body=response_body, http_status=http_status)

                                else:
                                    if result:
                                        update_activity_schedule(result)
                                    response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE

                                    # send notification to users tellnig them that their schedule has been marked inactive
                                    pass
                                    response_body[RESPONSE_MESSAGE] = {'message': TEXT_SUCCESSFUL, 'conflict': False,
                                                                    }
                            else:
                                traceback.print_exc()
                                error_list = []
                                for errors in serializer.errors:
                                    print(errors)
                                    error_list.append("invalid  " + errors + "  given.")
                                response_body[RESPONSE_MESSAGE] = error_list
                                return generic_response(response_body=response_body, http_status=http_status)

                if int(request.data.get('activity_type')) == IopOptionsEnums.IOP_SLEEP_MODE:

                    if timezone_info[0] == 'UTC':
                        current_datetime = datetime.datetime.now()
                    else:
                        current_datetime = datetime.datetime.now()

                    current_datetime = current_datetime + datetime.timedelta(days=day_count)
                    start_date = current_datetime.date()  # change to timezone.now()
                    d = start_date.weekday()
                    request.data['days_list'] = str(start_date.weekday())
                    request.data['u_days_list'] = str(start_date.weekday())

                    if day_count > 0:
                        current_datetime = current_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
                    if current_datetime > st:  # change to timezone.now()
                        start_date = current_datetime + datetime.timedelta(days=7)

                    else:
                        start_date = current_datetime + datetime.timedelta((d - current_datetime.weekday()) % 7)

                    if et <= st:
                        end_date = start_date + datetime.timedelta(days=1)
                        request.data['multi_days'] = True
                        et = et + datetime.timedelta(days=1)
                        duration = ((et - st).total_seconds() / 60)
                    else:
                        end_date = start_date
                        duration = ((et - st).total_seconds() / 60)

                    start_date = start_date.date()
                    end_date = end_date.date()

                    request.data['start_date'] = start_date
                    request.data['end_date'] = end_date

                    request.data['old_start_dt'] = parse(str(start_date) + '-' + str(st.time()))
                    request.data['new_start_dt'] = parse(str(start_date) + '-' + str(st.time()))
                    request.data['old_end_dt'] = parse(str(end_date) + '-' + str(et.time()))
                    request.data['new_end_dt'] = parse(str(end_date) + '-' + str(et.time()))

                    start_dt = request.data['new_start_dt']
                    end_dt = request.data['new_end_dt']

                    st = st.time()
                    et = et.time()

                    request.data['notes'] = duration
                    request.data['activity_start_time'] = st
                    request.data['activity_end_time'] = et
                    request.data['u_activity_start_time'] = st
                    request.data['u_activity_end_time'] = et

                    serializer = ActivityScheduleSerializer(data=request.data, partial=True,
                                                            context={'request': request})
                    if serializer.is_valid():
                        ser = serializer.save()

                        flag = check_sleep_mode_conflicts(ser, start_dt, end_dt, request.data['u_days_list'])

                        if flag is False:
                            response_body[RESPONSE_MESSAGE] = {
                                'message': 'Conflicting sleepmode. Please select a different time', 'conflict': True}
                            try:
                                ActivitySchedule.objects.get(id=ser.pk).delete()
                            except:
                                traceback.print_exc()
                            return generic_response(response_body=response_body, http_status=http_status)

                        response_body[RESPONSE_MESSAGE] = {'message': TEXT_SUCCESSFUL, 'conflict': False}

                    else:
                        error_list = []
                        for errors in serializer.errors:
                            error_list.append("invalid  " + errors + "  given.")
                        response_body[RESPONSE_MESSAGE] = error_list
                        return generic_response(response_body=response_body, http_status=http_status)

                if int(request.data.get('activity_type')) == IopOptionsEnums.IOP_USE_NOW:

                    start_date = todays_date.date()  # change to timezone.now()
                    request.data['start_date'] = start_date
                    request.data['current_ctt']=t2
                    request.data['days_list'] = str(start_date.weekday())
                    request.data['u_days_list'] = str(start_date.weekday())

                    if et < st:
                        request.data['end_date'] = start_date + datetime.timedelta(days=1)
                        request.data['multi_days'] = True
                        et = et + datetime.timedelta(days=1)
                        duration = ((et - st).total_seconds() / 60)
                    else:
                        request.data['end_date'] = start_date
                        duration = ((et - st).total_seconds() / 60)

                    end_date = request.data['end_date']

                    request.data['old_start_dt'] = parse(str(start_date) + '-' + str(st.time()))
                    request.data['new_start_dt'] = parse(str(start_date) + '-' + str(st.time()))
                    request.data['old_end_dt'] = parse(str(end_date) + '-' + str(et.time()))
                    request.data['new_end_dt'] = parse(str(end_date) + '-' + str(et.time()))

                    st = st.time()
                    et = et.time()

                    request.data['notes'] = duration
                    request.data['activity_start_time'] = st
                    request.data['activity_end_time'] = et
                    request.data['u_activity_start_time'] = st
                    request.data['u_activity_end_time'] = et

                    dest_temp = int(request.data['action_items'])

                    print('=-=-=    IOP_USE_NOW     =-=-=')
                    tau = calculate_tau(t2, dest_temp, duration=duration, ent=appliance)

                    request.data['temp_after_usage'] = tau

                    schs = check_sleep_mode_conflicts(new_obj=None, start_dt=request.data['new_start_dt'],
                                                    end_dt=request.data['new_end_dt'],
                                                    days_of_week=request.data['u_days_list'],
                                                    primary_entity=request.data['primary_entity'])

                    if schs is False:
                        message = "Cannot create event due to conflicting sleep mode"
                        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                        response_body[RESPONSE_MESSAGE] = {'message': message, 'conflict': True}
                        return generic_response(response_body=response_body, http_status=http_status)

                    else:
                        if sch_id:
                            try:
                                obj = ActivitySchedule.objects.get(id=sch_id)
                                ActivitySchedule.objects.filter(suspended_by=obj).update(suspended_by=None)
                                obj.suspended_by = None
                                obj.save()
                                obj.delete()
                            except:
                                traceback.print_exc()
                                pass

                    serializer = ActivityScheduleSerializer(data=request.data, partial=True,
                                                            context={'request': request})
                    if serializer.is_valid():
                        ser = serializer.save()

                        flag, result, message = updated_check_conflicts_with_use_now(ser, request.data['new_start_dt'],
                                                                                    request.data['new_end_dt'], start_date,
                                                                                    days_of_week=request.data[
                                                                                        'u_days_list'])

                        if flag is False:
                            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE

                            response_body[RESPONSE_MESSAGE] = {'message': message, 'conflict': True}
                            try:
                                ActivitySchedule.objects.filter(suspended_by=ser).update(suspended_by=None)
                                ActivitySchedule.objects.get(pk=ser.pk).delete()
                            except:
                                traceback.print_exc()

                            return generic_response(response_body=response_body, http_status=http_status)

                        else:
                            if result:
                                update_activity_schedule(result)
                            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE

                            # send notification to users tellnig them that their schedule has been marked inactive
                            pass
                            response_body[RESPONSE_MESSAGE] = {'message': TEXT_SUCCESSFUL, 'conflict': False,
                                                            }
                    else:
                        traceback.print_exc()
                        error_list = []
                        for errors in serializer.errors:
                            print(errors)
                            error_list.append("invalid  " + errors + "  given.")
                        response_body[RESPONSE_MESSAGE] = error_list
                        return generic_response(response_body=response_body, http_status=http_status)

                if int(request.data.get('activity_type')) == IopOptionsEnums.RECURRING_SLEEP_MODE:
                    if days_list is not None:
                        for d in days_list:
                            if isinstance(st, datetime.time):
                                st = parse(str(todays_date) + ' ' + str(st))
                            if isinstance(et, datetime.time):
                                et = parse(str(todays_date) + ' ' + str(et))

                            u_st = st
                            u_et = et
                            if timezone_info[0] == 'UTC':
                                current_datetime = datetime.datetime.now()
                            else:
                                current_datetime = datetime.datetime.now()
                            current_datetime = current_datetime + datetime.timedelta(days=day_count)

                            current_datetime = current_datetime.replace(second=0, microsecond=0)
                            today = current_datetime.date()  # changed from current_datetime.date().today() to current_datetime.date()

                            if today.weekday() not in days_list:  # check if weekday schedule is made that doesnot include current day.
                                # This is to avoid if user wants to make schedule for
                                #  Monday 1 PM: current day is sunday 3:00 PM.
                                # Then it wil create schedule on upcming monday and not for monday after that.

                                current_datetime = current_datetime.replace(hour=0, minute=0, second=0)

                            if today.weekday() == d and current_datetime > u_st:  # change to timezone.now()
                                upcoming_date = today + datetime.timedelta(days=7)

                            else:
                                upcoming_date = today + datetime.timedelta(
                                    (d - today.weekday()) % 7)  # calculating upcoming start date for the weekday

                            d = str(d)
                            request.data['days_list'] = d
                            request.data['u_days_list'] = d

                            if u_et.time() > u_st.time():
                                request.data['start_date'] = upcoming_date
                                request.data['end_date'] = upcoming_date

                                duration = ((u_et - u_st).total_seconds() / 60)
                            else:
                                request.data['start_date'] = upcoming_date
                                request.data['end_date'] = upcoming_date + datetime.timedelta(days=1)

                                u_et = u_et + datetime.timedelta(days=1)
                                duration = ((u_et - u_st).total_seconds() / 60)
                                request.data['multi_days'] = True
                            request.data['notes'] = duration

                            start_date = request.data['start_date']
                            end_date = request.data['end_date']

                            request.data['old_start_dt'] = parse(str(start_date) + '-' + str(st.time()))
                            request.data['new_start_dt'] = parse(str(start_date) + '-' + str(st.time()))
                            request.data['old_end_dt'] = parse(str(end_date) + '-' + str(et.time()))
                            request.data['new_end_dt'] = parse(str(end_date) + '-' + str(et.time()))

                            start_dt = request.data['new_start_dt']
                            end_dt = request.data['new_end_dt']

                            st = st.time()
                            et = et.time()
                            u_st = u_st.time()
                            u_et = u_et.time()
                            request.data['activity_start_time'] = st
                            request.data['activity_end_time'] = et
                            request.data['u_activity_start_time'] = u_st
                            request.data['u_activity_end_time'] = u_et

                            serializer = ActivityScheduleSerializer(data=request.data, partial=True,
                                                                    context={'request': request})
                            if serializer.is_valid():
                                ser = serializer.save()
                                tbd_sm.append(ser.id)
                                flag = check_sleep_mode_conflicts(ser, start_dt, end_dt, request.data['u_days_list'])

                                if flag is False:
                                    response_body[RESPONSE_MESSAGE] = {
                                        'message': 'Conflicting sleepmode. Please select a different time',
                                        'conflict': True}
                                    try:
                                        ActivitySchedule.objects.filter(id__in=tbd_sm).delete()
                                    except:
                                        traceback.print_exc()
                                    return generic_response(response_body=response_body, http_status=http_status)

                        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
                        response_body[RESPONSE_MESSAGE] = {'message': TEXT_SUCCESSFUL}
                        return generic_response(response_body=response_body, http_status=http_status)

            if int(request.data.get('activity_type')) == IopOptionsEnums.IOP_QUICK_SCHEDULE:

                q_schedules = ActivitySchedule.objects.filter(primary_entity=appliance,
                                                            activity_type_id__in=[IopOptionsEnums.IOP_QUICK_SCHEDULE,
                                                                                    IopOptionsEnums.IOP_USE_NOW,
                                                                                    IopOptionsEnums.IOP_SCHEDULE_ON_DEMAND,
                                                                                    IopOptionsEnums.IOP_SCHEDULE_DAILY])
                if q_schedules:
                    q_schedules = q_schedules.exclude(id__in=schs_ids)
                    set_device_temperature_for_quick_sch(appliance,str(DEFAULT_TEMP))
                    q_schedules.delete()

      
            
    except Exception as e:
        print(e)

    # CHECK and remove if any duplicate created
    ents = Entity.objects.filter(module_id=ModuleEnum.IOP,
                                 type_id=DeviceTypeEntityEnum.IOP_DEVICE,
                                 status_id=OptionsEnum.ACTIVE)
    for ent in ents:
        print("ENT : ", ent.id)

        for row in ActivitySchedule.objects.filter(module=ModuleEnum.IOP, primary_entity=ent).reverse():
            if ActivitySchedule.objects.filter(new_start_dt=row.new_start_dt, primary_entity=ent).count() > 1:
                row.delete()
                print("DUPLICATE DELETED !")

    response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    print(response_body)
    return generic_response(response_body=response_body, http_status=http_status)


##################  END points for E2E TODO: Remove later
@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_e2e_activity_data(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    customer_id = h_utils.get_customer_from_request(request, None)
    result = dict()
    try:
        activities_list = []
        bin_collections_list = []
        user = User.objects.get(email='driver_e2e@hypernymbiz.com', customer_id=customer_id)
        driver = user.associated_entity

        b_data = util_get_bins_collection_data(customer_id, None, None, None, None, driver.id, None, None, None)
        for obj in b_data:
            collection_data = BinCollectionDataSerializer(obj, context={'request': request})
            collection_data = collection_data.data.copy()
            collection_data['entity_location'] = obj.action_item.source_latlong
            bin_collections_list.append(collection_data)
        result['assets'] = bin_collections_list

        activity_data = util_get_activity_data(customer_id, None, driver.id, None, None, None, None)
        for obj in activity_data:
            a_data = ActivityDataSerializer(obj, context={'request': request})
            a_data = a_data.data.copy()
            activities_list.append(a_data)
        result['activity_data'] = activities_list
    except:
        traceback.print_exc()

    response_body[RESPONSE_DATA] = result
    response_body[RESPONSE_MESSAGE] = {'success': TEXT_OPERATION_SUCCESSFUL}
    response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE

    return generic_response(response_body=response_body, http_status=200)


@api_view(['POST', 'PATCH'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def add_activity_schedule_e2e(request):
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: HTTP_ERROR_CODE, RESPONSE_DATA: []}
    user_email = 'driver_e2e@hypernymbiz.com'
    driver_user = User.objects.get(email=user_email)

    bins_list = get_default_param(request, 'bins_list', None)
    for b in bins_list:
        bin = Entity.objects.get(name=b, type_id=21)
        driver = driver_user.associated_entity
        b_data = create_bin_collection_data(None, None, driver.id, timezone.now(), IOFOptionsEnum.UNCOLLECTED, bin.id,
                                            bin.customer_id, bin.module_id)
        b_data.save()
    send_notification_violations(None, None, driver_user.customer_id, bin.module_id, "Start Activity Now!",
                                 [driver_user], threshold=None,
                                 value=None)

    response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    response_body[RESPONSE_MESSAGE] = "Job created successfully!"
    return generic_response(response_body=response_body, http_status=200)


@transaction.atomic()
@api_view(['POST'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def delete_sleep_mode(request):
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: HTTP_ERROR_CODE, RESPONSE_DATA: []}
    sleep_mode_id = request.data['sleep_mode_id']
    if time.tzname[0] == 'UTC':
        current_datetime = datetime.datetime.now()
    else:
        current_datetime = datetime.datetime.now()
    if sleep_mode_id:
        try:
            sleep_mode = ActivitySchedule.objects.get(id=sleep_mode_id,  # Query sleep mode by id
                                                      schedule_activity_status_id=OptionsEnum.ACTIVE)

            if sleep_mode.sleep_mode is True:  # Check if sleep mode is running
                suspended_schedules = check_overlapping_schedules(sleep_mode, sleep_mode.u_activity_start_time,
                                                                  sleep_mode.u_activity_end_time,sleep_mode.u_days_list)  # returns schedules that conflict with the running sleep mode.

                if suspended_schedules:
                    for sch in suspended_schedules:
                        try:
                            queue = ActivityQueue.objects.get(activity_schedule=sch)  # Queue of the schedule
                            # if queue.suspend is True:
                            # sleep_mode_end_datetime = parse(str(sleep_mode.end_date) + ' ' + str(sleep_mode.u_activity_end_time))
                            # if sleep_mode_end_datetime.replace(tzinfo=timezone.utc) < queue.activity_end_datetime:
                            # queue.suspend = False
                            # queue.activity_datetime = sleep_mode_end_datetime

                            # queue.save()

                            # else:
                            if sch.activity_type.id in [IopOptionsEnums.IOP_SCHEDULE_ON_DEMAND,
                                                        IopOptionsEnums.IOP_USE_NOW]:  # if schedule is of type use now or once, mark it inactive
                                sch.schedule_activity_status = Options.objects.get(id=OptionsEnum.INACTIVE)
                                sch.save()

                            else:  # Shift schedule to next weekday.
                                today = current_datetime.date()

                                if today.weekday() == int(sch.u_days_list):
                                    upcoming_date = today + datetime.timedelta(days=7)
                                else:
                                    upcoming_date = today + datetime.timedelta(
                                        (int(sch.u_days_list) - today.weekday()) % 7)

                                sch.start_date = upcoming_date

                                if sch.multi_days is True:
                                    sch.end_date = upcoming_date + datetime.timedelta(days=1)

                                else:
                                    sch.end_date = upcoming_date

                                queue.delete()
                                sch.save()
                        except:
                            queue = None

            sleep_mode.sleep_mode = False  # Set the sleepmode flag to false.
           

            sleep_mode.primary_entity.temperature = False  # Set entity temperature flag to false indicating that sleep mode on this water heater is now inactive
            sleep_mode.primary_entity.save()
            sleep_mode.primary_entity.weight = None  # Redundant check.

            sleep_mode.delete()
            # sleep_mode.schedule_activity_status = Options.objects.get(
            #     id=OptionsEnum.INACTIVE)  # Mark sleep mode as inactive.
            # sleep_mode.save()
            from hypernet.cron_task import get_chs_device
            queryset=get_chs_device(sleep_mode.primary_entity)
            if queryset.heartrate_value is 3 or queryset.heartrate_value is 4: 
                set_device_temperature(sleep_mode, str(DEFAULT_TEMP))
            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
            response_body[
                RESPONSE_MESSAGE] = "Sleep mode deleted successfully. Schedules affected by sleep mode might have been altered."

        except:
            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
            response_body[RESPONSE_MESSAGE] = "Sleep mode doesnot exist"
    return generic_response(response_body=response_body, http_status=200)


'''
This call returns the directy conflicting schedules with the datetimes provided from request.
'''


@api_view(['POST'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def check_potential_conflicts(request):
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: HTTP_ERROR_CODE, RESPONSE_DATA: []}
    http_status = HTTP_SUCCESS_CODE
    appliance_id = h_utils.get_data_param(request, 'primary_entity_id', None)
    start_time = h_utils.get_data_param(request, 'start_time', None)
    end_time = h_utils.get_data_param(request, 'end_time', None)
    sch_id = h_utils.get_data_param(request, 'sch_id', None)
    day_count = int(h_utils.get_data_param(request, 'day_count', 0))

    try:
        appliance = Entity.objects.get(id=appliance_id)
    except:
        appliance = None

    if appliance:
        try:
            today = datetime.datetime.now()
            result_list = []
            timezone_info = time.tzname

            # Taking last item from start_time (list). A fix added to cover discrepency from Android side.
            start_time = start_time[-1]

            # Taking last item from end_time (list). A fix added to cover discrepency from Android side.
            end_time = end_time[-1]

            today = today.replace(second=0, microsecond=0)

            # Day count send from request. Added in current_datetime when schedule is made on day other than current day.
            today = today + datetime.timedelta(days=day_count)

            previous_date = (today - datetime.timedelta(days=1)).date()
            next_date = (today + datetime.timedelta(days=1)).date()

            days_of_week = today.date().weekday()  # today.date().today().weekday() to today.date().weekday()

            start_dt = parse(str(today.date()) + '-' + str(start_time))
            end_dt = parse(str(today.date()) + '-' + str(end_time))

            schedules = updated_conflicts(new_obj=None, start_dt=start_dt,
                                          # Returns Schedules directly conflicting with datetimes provided from request.
                                          end_dt=end_dt, days_of_week=days_of_week,
                                          sch_type=[IopOptionsEnums.IOP_SCHEDULE_DAILY,
                                                    IopOptionsEnums.IOP_SCHEDULE_ON_DEMAND,
                                                    IopOptionsEnums.IOP_USE_NOW,
                                                    IopOptionsEnums.IOP_QUICK_SCHEDULE,
                                                    ], start_date=None, primary_entity=appliance)
            if sch_id:  # This schedule id is sent from request when a schedule is edited. So a schedule being edited won't be sent to the user.
                schedules = schedules.exclude(id=sch_id)
            schedules = schedules.filter(start_date__range=[previous_date, next_date])
            if schedules:
                for o in schedules:
                    result = {}
                    result['scheduled_by'] = o.modified_by.first_name + ' ' + o.modified_by.last_name
                    result['duration'] = o.notes
                    result['start_date'] = o.start_date
                    result['end_date'] = o.end_date
                    result['usage'] = o.activity_route if o.activity_route else None
                    result['temperature'] = o.action_items
                    result['type'] = o.activity_type.id
                    result['sch_id'] = o.id
                    try:
                        q = ActivityQueue.objects.get(activity_schedule=o)

                        result['start_time'] = q.activity_datetime.time().replace(second=0)
                        result['end_time'] = q.activity_end_datetime.time().replace(second=0)
                    except:
                        result['start_time'] = o.u_activity_start_time.replace(second=0)
                        result['end_time'] = o.u_activity_end_time.replace(second=0)

                    try:
                        act = Activity.objects.get(
                            activity_schedule_id=o.id)  # State will be fetched from the corresponding activity of a schedule.
                        result['state'] = act.activity_status.label
                    except:
                        pass
                    # Delay will occur only if a schedule has been shifted. Or created at a time other than user's desired time.
                    # We check if old_start_time and new_start_time are not same. So the delay will occur when these two times are not same
                    if o.u_activity_start_time != o.activity_start_time:
                        # Delay is the differnce between end_datetime and start_datetime of schedule
                        delay = ((o.new_end_dt - o.new_start_dt).total_seconds() / 60)
                        result['delay'] = round(delay)
                    else:
                        result[
                            'delay'] = 0  # No delay if both times (old start time and updated start time are the same).
                    result_list.append(result)

                response_body[RESPONSE_DATA] = result_list
                response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
                response_body[RESPONSE_MESSAGE] = 'Operation Successful'
            else:
                response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
                response_body[RESPONSE_MESSAGE] = 'No conflicts with other schedules.'
        except:
            traceback.print_exc()
    else:
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
        response_body[RESPONSE_MESSAGE] = 'Appliance Doesnot exist.'

    return h_utils.generic_response(response_body, http_status)


'''
This call returns the available to the user when the user wants to create use now schedule
'''


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def fetch_next_available_time(request):
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: HTTP_ERROR_CODE, RESPONSE_DATA: []}
    http_status = HTTP_SUCCESS_CODE
    appliance_id = h_utils.get_default_param(request, 'primary_entity_id', None)
    duration = h_utils.get_default_param(request, 'duration', None)
    dest_temp = h_utils.get_default_param(request, 'dest_temp', None)
    print(dest_temp,'dest_temp')
    current_datetime = h_utils.get_default_param(request, 'current_datetime', None)
    IS_USE_NOW = h_utils.get_default_param(request, 'use_now', 0)

    try:
        ent = Entity.objects.get(id=appliance_id)
        ttr, t2 = calculcate_ttr(ent, dest_temp, duration=duration)  # calculates ttr for the device.
        current_datetime = datetime.datetime.strptime(current_datetime, '%Y-%m-%d %H:%M:%S')

        print('USE_NOW value:  ', IS_USE_NOW, int(IS_USE_NOW) == 1)
        if int(IS_USE_NOW) == 1:
            ttr,t2 = TTR_calculation_use_now_events(ent=ent, duration=duration, des_temp=dest_temp)
            if ttr is 0:
                ttr=3
            print('ttr in USE_NOW:  ', ttr,t2)
            result = current_datetime + datetime.timedelta(minutes=ttr)
        elif ttr is not None and ttr > 0:  # ttr is added to the current_datetime. The result is a datetime object at which heater will be ready
            result = current_datetime + datetime.timedelta(minutes=ttr)
        else:
            # Else if heater is already ready. Add a buffer of 2 mins. Can be changed to 0.
            result = current_datetime + datetime.timedelta(minutes=2)

        print('result is', result)
        response_body[RESPONSE_DATA] = {'result': result, 't2': t2}
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        response_body[RESPONSE_MESSAGE] = 'Operation Successful'

    except Entity.DoesNotExist:
        print("entity not found")
    except Exception as e:
        print(e)
        traceback.print_exc()
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
        response_body[RESPONSE_MESSAGE] = 'No such appliance. Contact your administrator'
    return h_utils.generic_response(response_body, http_status)


'''
This event suggests time to user. If a user creates schedule right after an already created schedule (in the other schedule's buffer time)
Our system will return two suggestions at which water heater will be ready. 
'''


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def event_suggesstion(request):
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: HTTP_ERROR_CODE, RESPONSE_DATA: []}
    http_status = HTTP_SUCCESS_CODE
    print(request)
    appliance_id = h_utils.get_default_param(request, 'primary_entity', None)
    start_time = h_utils.get_default_param(request, 'start_time', None)
    end_time = h_utils.get_default_param(request, 'end_time', None)
    des_temp = h_utils.get_default_param(request, 'des_temp', None)
    duration = h_utils.get_default_param(request, 'duration', None)
    t2 = h_utils.get_default_param(request, 't2', None)
    day_count = int(h_utils.get_default_param(request, 'day_count', 0))
    volume_capacity = int(h_utils.get_default_param(request, 'volume_capacity', 0))
    print(volume_capacity,'volume_capacity')

    sch_id = h_utils.get_default_param(request, 'sch_id', None)
    try:
        if appliance_id:
            try:
                appliance = Entity.objects.get(id=appliance_id)
            except:
                appliance = None
            today = datetime.datetime.now()
            result_list = []
            timezone_info = time.tzname

            if timezone_info[0] == 'UTC':
                today = today
            today = today.replace(second=0, microsecond=0)
            today = today + datetime.timedelta(days=day_count)
            days_of_week = today.date().weekday()
            # print(des_temp,'des_temp')
            # ctt1=calculate_overlapping(None,duration,des_temp)
            # if ctt1==None:
            #     print(ctt1)
            # print(ctt1,'ctt1 check in function view')
            start_time = parse(str(today.date()) + '-' + str(start_time))  # Parse start_time to datetime object
            end_time = parse(str(today.date()) + '-' + str(end_time))  # Parse end_time to datetime object
            
            # retuns list of all schedules on previous, current and next weekday
            all_schedules = query_all_schedules(new_obj=None, days_of_week=days_of_week, appliance_id=appliance_id,
                                                start_dt=today.date())
            if sch_id:  # This id is sent when user wants to edit schedule. Execule the scheule from suggestion which will be edited.
                all_schedules = all_schedules.exclude(id=sch_id)

            previous_day = str(int(days_of_week) - 1)
            if days_of_week == '0' or days_of_week == 0:
                previous_day = '6'

            # Query Schedules that lie before the datetime provided by the user.Sort the schedules by their end_datetime
            objs_before = all_schedules.filter(new_end_dt__lte=start_time,
                                               u_days_list__in=[previous_day, days_of_week]).order_by('new_end_dt')

            print('existing schedlues:  ',objs_before.count())
            if objs_before:
                objs = objs_before.last()  # pick the last object

                tau_old_sch = objs.temp_after_usage  # select temperature after usage of this last object. Used in buffer calculation

                ttr_for_new_sch, t2 = calculcate_ttr(appliance, duration=duration,
                                                     # User the tau_old_sch as t1 for ttr (buffer) calculation. t2 is calulated for schedule that is being created
                                                     desired_temp=des_temp, t1=tau_old_sch)
                
                
                temp_time = start_time - datetime.timedelta(
                    minutes=ttr_for_new_sch)  # subtract this buffer time from start time (now a datetimefield) provided by the user and see if this resultant time is less than the end datetime of previous schedule that we just queried

                objs_end_dt = objs.new_end_dt #check

                temp_time = temp_time.replace(tzinfo=None)
                objs_end_dt = objs_end_dt.replace(tzinfo=None)
                print(temp_time,'temp_time check')
                print(objs_end_dt,'obj_end_dt')
                print(objs.id,'id for scehel')
                print(t2,'after use_now function')
                try:
                    # activity=Activity.objects.get(activity_schedule=objs,activity_status=IopOptionsEnums.IOP_SCHEDULE_READY)
                    # print('zone 2')
                    suggestion=objs.suggestion
                    suggestion=False
                    if suggestion is False:
                        if temp_time < objs_end_dt:
                            
                            objs.new_end_dt = objs.new_end_dt.replace(tzinfo=None)
                            time_diff = ((
                                            start_time - objs.new_end_dt).total_seconds() / 60)  # Subtract user time with the schedule's end_datetime. This is used for buffer to be added (buffer tba) calculation

                            buffer_tba = ttr_for_new_sch - time_diff  # Now subtract ttr calculated from the time diff to get buffer that will be added in schedule
                            if buffer_tba < 0:
                                buffer_tba = 0
                            # buffer_tba=0
                            new_start_time = start_time + datetime.timedelta(minutes=buffer_tba)
                            new_end_time = new_start_time + datetime.timedelta(minutes=float(duration))
                            ttr_for_new_sch,t2 = TTR_calculation_use_now_events(ent=appliance, duration=duration, des_temp=des_temp)
                            print('ttr for new schedule: ', ttr_for_new_sch)
                            
                            

                            print('\n\n\n\n\n\n ============ \n\n\n\n\n\n\n\n')
                            print('start time   ',  new_start_time)
                            print('end time   ',  new_end_time)
                            result_list.append({'delay': buffer_tba ,
                                                'delay_mins':buffer_tba,
                                                'start_time': new_start_time.time(),
                                                'end_time': new_end_time.time(),
                                                'usage': int(des_temp),
                                                'old_t2': t2,
                                                'schedule_id':objs.id,
                                                'duration': int(duration)})

                            # The suggestion below is the next suggestion. This suggestion will return
                            # temperature and calculate buffer according to the following rule:
                            # On left side are the temperatures sent by user at which he wants to create schedules. We calculated buffer based on that temperature
                            # Now we suggest user some different temperature. We calculate buffers according to this suggested temperatrues (2nd suggestion) and return user both suggestions
                            # Very hot ---> Hot (2nd suggestion)
                            # Hot ---> Warm (2nd suggestion)
                            # Warm ----> Warm (2nd suggestion) but with duration halved.

                            st, et, duration_after, delay, new_usage, t2 = suggest_events_on_usage(appliance, start_time, end_time,
                                                                                            des_temp, duration, today,
                                                                                            tau_old_sch, time_diff)

                            if delay is None:
                                delay = 0

                            if t2 is None:
                                t2 = 0

                            buffer_tba=0
                            new_start_time = start_time + datetime.timedelta(minutes=buffer_tba)
                            new_end_time = new_start_time + datetime.timedelta(minutes=float(duration))
        
                            # new_ttr, new_t2 = calculcate_ttr(appliance, new_usage, duration=duration, t2=tau_old_sch)
                            # print(new_t2)
                            if int(des_temp) is not int(new_usage):

                                result_list.append({'delay': 0,
                                                    'delay_mins':buffer_tba,
                                                    'start_time': new_start_time.time(),
                                                    'end_time': new_end_time.time(),
                                                    'usage': new_usage,
                                                    'new_t2': t2,
                                                    'schedule_id':objs.id,
                                                    'duration': int(duration)}),
                                                    

                            print(result_list)
                            response_body[RESPONSE_DATA] = result_list
                            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
                            response_body[RESPONSE_MESSAGE] = 'Operation Successful'


                        else:
                            response_body[RESPONSE_DATA] = []
                            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
                            response_body[RESPONSE_MESSAGE] = 'Operation Successful'
                    else:
                        response_body[RESPONSE_DATA] = []
                        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
                        response_body[RESPONSE_MESSAGE] = 'Operation Successful'
                    
                except Exception as e:
                    response_body[RESPONSE_DATA] = []
                    response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
                    response_body[RESPONSE_MESSAGE] = 'Operation Successful'
            else:
                response_body[RESPONSE_DATA] = []
                response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
                response_body[RESPONSE_MESSAGE] = 'Operation Successful'
    except:
        traceback.print_exc()

    return h_utils.generic_response(response_body, http_status)
