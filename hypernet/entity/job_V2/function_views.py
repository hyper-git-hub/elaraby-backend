import pytz
from django.db.models import Sum
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
from hypernet.entity.job_V2.utils import get_dates, util_create_activity_queue, util_get_schedules, util_get_activities, \
    util_get_bins_location, util_get_activity_data, util_get_bin_with_location, util_upcoming_activities, \
    get_conflicts, suspend_activity_schedule, util_get_bins_activities, util_get_bins_action_data, \
    util_get_schedule_total_count, util_get_bins_collection_data, check_suspend
from hypernet.constants import *
from hypernet.enums import OptionsEnum, DeviceTypeEntityEnum, DeviceTypeAssignmentEnum, IOFOptionsEnum
from hypernet.utils import generic_response, exception_handler, get_default_param
import hypernet.utils as h_utils
from customer.models import CustomerPreferences
from iof.models import ActivitySchedule, ActivityQueue
from iof.serializers import ActivityScheduleSerializer, ActivityDataSerializer
from iof.serializers import ActivitySerializer
# ---------------------------------------------------------------------------------------------------------


@transaction.atomic()
@api_view(['POST', 'PATCH'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def add_activity_scehdule(request):
    from dateutil.parser import parse
    days_list = get_default_param(request, 'days_list', None)

    request.POST._mutable = True
    request.data['status'] = OptionsEnum.ACTIVE
    request.data['customer'] = h_utils.get_customer_from_request(request, None)
    request.data['module'] = h_utils.get_module_from_request(request, None)
    request.data['activity_type'] = IOFOptionsEnum.BIN_COLLECTION_JOB
    request.data['schedule_activity_status'] = OptionsEnum.ACTIVE
    # request.data['modified_by'] = 1
    request.data['modified_by'] = h_utils.get_user_from_request(request,None).id
    if days_list:
        request.data['days_list'] = ",".join(str(bit) for bit in days_list)

    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: HTTP_ERROR_CODE, RESPONSE_DATA: []}
    http_status = HTTP_SUCCESS_CODE
    pk = request.data.get('id')
    if pk:
        ActivityQueue.objects.filter(activity_schedule_id=pk, customer=request.data.get('customer')).delete()
        queue_obj = ActivitySchedule.objects.get(pk=pk, customer_id=int(request.data.get('customer')))
        serializer = ActivityScheduleSerializer(queue_obj, data=request.data, partial=True, context={'request': request})
    else:
        serializer = ActivityScheduleSerializer(data=request.data, partial=True, context={'request': request})
    try:
        preferences = CustomerPreferences.objects.get(customer_id=h_utils.get_customer_from_request(request, None))
    except:
        response_body[RESPONSE_MESSAGE] = {'message': 'Customer invalid.'}
        http_status = 400
        response_body[RESPONSE_STATUS] = STATUS_ERROR

    # activity_date = str(request.data['start_date'])
    # activity_date = parse(activity_date)

    #TODO Check and Test for Days list scenarios.
    #Check serializer is_valid here
    if serializer.is_valid():
        from dateutil.parser import tz
        activity_datetime = str(serializer.validated_data.get('start_date')) + ' ' + str(serializer.validated_data.get('activity_start_time'))
        activity_datetime = parse(activity_datetime)
        activity_datetime = activity_datetime.replace(tzinfo=timezone.utc)
        # print(activity_datetime)
        now_time = timezone.now()

        if activity_datetime < now_time:
            response_body[RESPONSE_MESSAGE] = {'message':'Invalid Date Selected. You cannot select a past date.', 'time':False}
            http_status = 200
            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
            return generic_response(response_body=response_body, http_status=http_status)

        #TODO REMOVE
        if serializer.is_valid():
            if request.data.get('activity_type') == IOFOptionsEnum.BIN_COLLECTION_JOB:
                if days_list is None:
                    time_diff = now_time + timezone.timedelta(minutes=15)
                    if activity_datetime >= time_diff:
                        if pk:
                            if serializer.validated_data.get('end_date') is None:
                                conflict, activity_schedule = get_conflicts(preferences=preferences, data=serializer.validated_data, days_list=None)
                            else:
                                conflict, activity_schedule = get_conflicts(preferences=preferences, data=serializer.validated_data, days_list=None, start_date=timezone.now().date())

                        else:
                            conflict, activity_schedule = get_conflicts(preferences=preferences, data=serializer.validated_data, days_list=None)
                        if conflict:
                            user = h_utils.get_user_from_request(request, None)
                            if activity_schedule is None:
                                response_body[RESPONSE_MESSAGE] = {'message': 'Schedule Conflicts with an ongoing activity',
                                                                  'conflict': True,
                                                                  'suspend': False}
                            elif activity_schedule.modified_by == user:
                                response_body[RESPONSE_MESSAGE] = {'message': 'Schedule Conflicts with '+
                                                                      activity_schedule.get_name(), 'conflict': True,
                                                                   'suspend': True, 'id': activity_schedule.id}
                            else:
                                response_body[RESPONSE_MESSAGE] = {'message': 'Schedule Conflicts with ' +
                                                                      activity_schedule.get_name(), 'conflict': True,
                                                                   'suspend': False}
                            http_status = HTTP_SUCCESS_CODE
                        else:
                            ser = serializer.save()
                            if pk:
                                if serializer.data.get('end_date') is None:
                                    util_create_activity_queue(serializer=ser, days_list=None,
                                                               start_date=None)
                                else:
                                    util_create_activity_queue(serializer=ser, days_list=None, start_date=timezone.now().date())
                            else:
                                util_create_activity_queue(serializer=ser, days_list=None)

                            response_body[RESPONSE_MESSAGE] = {'message': TEXT_OPERATION_SUCCESSFUL, 'conflict': False}
                            http_status = HTTP_SUCCESS_CODE
                    else:
                        response_body[RESPONSE_MESSAGE] = {'message':'Schedules cannot be created within next 15 mins, \n NOTE: \n select time atleast 15 mins ahead.'}
                        http_status = HTTP_SUCCESS_CODE
                        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                        return generic_response(response_body=response_body, http_status=http_status)

                if days_list is not None:
                    if pk:
                        conflict, activity_schedule = get_conflicts(preferences=preferences, data=serializer.validated_data,
                                                                    days_list=days_list, start_date=timezone.now().date())
                    else:
                        conflict, activity_schedule = get_conflicts(preferences=preferences, data=serializer.validated_data,
                                                                    days_list=days_list)

                    if conflict:
                        user = h_utils.get_user_from_request(request, None)
                        if activity_schedule is None:
                            response_body[RESPONSE_MESSAGE] = {'message': 'Schedule Conflicts with Activity',
                                                              'conflict': True,
                                                              'suspend': False}
                        elif activity_schedule.modified_by == user:
                            response_body[RESPONSE_MESSAGE] = {'message': 'Schedule Conflicts with '+
                                                              activity_schedule.get_name(),
                                                               'conflict': True, 'suspend': True,
                                                               'id': activity_schedule.id}
                        else:
                            response_body[RESPONSE_MESSAGE] = {'message': 'Schedule Conflicts with ' +
                                                                                  activity_schedule.get_name(),
                                                               'conflict': True, 'suspend': False}

                        http_status = HTTP_SUCCESS_CODE
                    else:
                        ser = serializer.save()
                        if pk:
                            util_create_activity_queue(serializer=ser, days_list=days_list, start_date=timezone.now().date())
                        else:
                            util_create_activity_queue(serializer=ser, days_list=days_list)

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
def get_activity_schedules(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    customer_id = h_utils.get_customer_from_request(self, None)
    sch_id = h_utils.get_default_param(self, 'schedule_id', None)
    s_id = h_utils.get_default_param(self, 'status_id', None)
    t_id = h_utils.get_default_param(self, 'truck_id', None)
    d_id = h_utils.get_default_param(self, 'driver_id', None)
    a_id = h_utils.get_default_param(self, 'activity_id', None)
    start_date = h_utils.get_default_param(self, 'start_date', None)
    end_date = h_utils.get_default_param(self, 'end_date', None)
    http_status = HTTP_SUCCESS_CODE
    activities_list = []
    schedules_list = []

    result_list = {}
    # Adding a single schedule
    schedules = util_get_schedules(c_id=customer_id, t_id=t_id, d_id=d_id, sch_id=sch_id, s_id=s_id)
    for obj in schedules:
        schedules_data = ActivityScheduleSerializer(obj, context={'request': self})
        sch_dict = schedules_data.data.copy()
        sch_dict['action_items'] = util_get_bins_location(action_items=schedules_data.data['action_items'])
        sch_dict['completion_percentage'] = util_get_schedule_total_count(sch_id=obj.id)
        schedules_list.append(sch_dict)
    result_list['schedules'] = schedules_list

    activities = util_get_activities(c_id=customer_id, t_id=t_id, d_id=d_id, sch_id=sch_id, s_id=s_id,
                                     a_id=a_id, start_date=start_date, end_date=end_date)
    for obj in activities:
        activities_data = ActivitySerializer(obj, context={'request': self})
        act_dict = activities_data.data.copy()
        act_dict['action_items'] = util_get_bins_location(action_items=activities_data.data['action_items'])
        activities_list.append(act_dict)
    result_list['activities'] = activities_list

    upcoming_activity = util_upcoming_activities(c_id=customer_id, sch_id=sch_id, t_id=t_id, d_id=d_id, start_date=start_date, end_date=end_date)
    if upcoming_activity:
        upcoming_activity = upcoming_activity[0]
        result_list['upcoming_activity'] = upcoming_activity.as_queue_json()

    response_body[RESPONSE_DATA] = result_list
    response_body[RESPONSE_MESSAGE] = {'success':TEXT_OPERATION_SUCCESSFUL}
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
        if start_date and end_date:
            activities = util_get_activities(c_id=customer_id, t_id=t_id, d_id=d_id, sch_id=sch_id, s_id=s_id,
                                         a_id=a_id, start_date=start_date, end_date=end_date)

        elif a_id:
            activities = util_get_activities(c_id=customer_id, t_id=t_id, d_id=d_id, sch_id=sch_id, s_id=s_id,
                                         a_id=a_id, start_date=start_date, end_date=end_date)

            activity_data = util_get_activity_data(c_id=customer_id, t_id=t_id, d_id=d_id, a_id=a_id, s_id=s_id,
                                                   start_date=start_date, end_date=end_date)

        else:
            activities = util_get_activities(c_id=customer_id, t_id=t_id, d_id=d_id, sch_id=sch_id, s_id=s_id,
                                             a_id=a_id, start_date=start_date, end_date=end_date)



        for obj in activities:
            activities_data = ActivitySerializer(obj, context={'request': self})
            act_dict = activities_data.data.copy()
            invoices = util_get_bins_collection_data(c_id=customer_id, b_id=None, s_id=s_id, a_id=a_id, sup_id=None,
                                                          d_id=d_id, t_id=t_id, start_date=start_date, end_date=end_date).\
                                                          filter(status_id=IOFOptionsEnum.COLLECTED).values('invoice')\
                                                          .annotate(total_invoice=Sum('invoice'))

            #act_dict['total_invoice'] = invoices['invoice']0
            if act_dict['action_items']:
                act_dict['action_items'] = util_get_bins_location(action_items=activities_data.data['action_items'], activity_id=obj.id)
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
        response_body[RESPONSE_MESSAGE] = {'success':TEXT_OPERATION_SUCCESSFUL}
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
    response_body[RESPONSE_MESSAGE] = {'success':TEXT_OPERATION_SUCCESSFUL}

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
    upcoming_activity = util_upcoming_activities(c_id=customer_id, sch_id=None, t_id=None, d_id=None, start_date=start_date, end_date=end_date)
    for obj in upcoming_activity:
        upcoming_activities_dict['upcoming_activity'] = obj.as_queue_json()
        upcoming_activities_list.append(upcoming_activities_dict.copy())

    response_body[RESPONSE_DATA] = upcoming_activities_list
    response_body[RESPONSE_MESSAGE] = {'success':TEXT_OPERATION_SUCCESSFUL}

    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_bins_activities(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    customer_id = h_utils.get_customer_from_request(request, None)
    bin = h_utils.get_default_param(request, 'bin_id', None)
    status_id = h_utils.get_default_param(request, 'status_id', None)
    start_date = h_utils.get_default_param(request, 'start_date', None)
    end_date = h_utils.get_default_param(request, 'end_date', None)
    
    bin_collections_list = []

    upcoming_activities_dict = {}
    upcoming_activity = util_get_bins_action_data(c_id=customer_id, b_id=bin, s_id=status_id, start_date=start_date, end_date=end_date).order_by('-timestamp')
    for obj in upcoming_activity:
        bin_data = ActivityDataSerializer(obj, context={'request': request})
        bin_data = bin_data.data.copy()
        bin_collections_list.append(bin_data)
    upcoming_activities_dict['bins_collection_data'] = bin_collections_list
    response_body[RESPONSE_DATA] = bin_collections_list
    response_body[RESPONSE_MESSAGE] = {'success':TEXT_OPERATION_SUCCESSFUL}
    response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE

    return generic_response(response_body=response_body, http_status=200)