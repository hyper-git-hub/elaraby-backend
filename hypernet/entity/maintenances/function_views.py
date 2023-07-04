from django.db.models import Sum
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
from hypernet.entity.job_V2.utils import get_dates, util_create_activity_queue, util_get_schedules, util_get_activities, \
    util_get_bins_location, util_get_activity_data, util_get_bin_with_location, util_upcoming_activities, \
    get_conflicts, suspend_activity_schedule, util_get_bins_activities, util_get_bins_action_data, \
    util_get_schedule_total_count, util_get_bins_collection_data, check_suspend, check_bin_in_activity, \
    get_activity_bins, delete_bincollection_data
from hypernet.constants import *
from hypernet.enums import OptionsEnum, DeviceTypeEntityEnum, DeviceTypeAssignmentEnum, IOFOptionsEnum
from hypernet.models import HypernetNotification
from hypernet.utils import generic_response, exception_handler, get_default_param
import hypernet.utils as h_utils
from customer.models import CustomerPreferences
from iof.models import ActivitySchedule, ActivityQueue, BinCollectionData, LogisticMaintenance
from iof.serializers import ActivityScheduleSerializer, ActivityDataSerializer, BinCollectionDataSerializer, \
    LogisticMaintenanceSerializer, LogisticMaintenanceDataSerializer
from iof.serializers import ActivitySerializer
from iof.utils import create_bin_collection_data, create_activity_data
from hypernet.notifications.utils import send_action_notification, save_users_group
from user.models import User
# ---------------------------------------------------------------------------------------------------------
from options.models import Options


@transaction.atomic()
@api_view(['POST', 'PATCH'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def add_update_maintenance(request):
    request.POST._mutable = True
    request.data['customer'] = h_utils.get_customer_from_request(request, None)
    request.data['module'] = h_utils.get_module_from_request(request, None)
    request.data['modified_by'] = h_utils.get_user_from_request(request, None).id
    request.data['timestamp'] = timezone.now()
    request.POST._mutable = False
    
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
    http_status = HTTP_SUCCESS_CODE
    pk = request.data.get('id')
    if pk:
        maintenance = LogisticMaintenance.objects.get(id=pk, customer=request.data.get('customer'))
        serializer = LogisticMaintenanceSerializer(maintenance, data=request.data, partial=True, context={'request': request})
    else:
        serializer = LogisticMaintenanceSerializer(data=request.data, partial=True, context={'request': request})

    if serializer.is_valid():
        entity = serializer.save()
        request.POST._mutable = True
        request.data['maintenance'] = entity.id
        request.POST._mutable = False
        serializer = LogisticMaintenanceDataSerializer(data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
        else:
            error_list = []
            for errors in serializer.errors:
                error_list.append("invalid  " + errors + "  given.")
            response_body[RESPONSE_MESSAGE] = error_list
            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
            return generic_response(response_body=response_body, http_status=http_status)
    else:
        for errors in serializer.errors:
            if errors == 'non_field_errors':
                response_body[RESPONSE_MESSAGE] = serializer.errors[errors][0]
            else:
                response_body[RESPONSE_MESSAGE] = h_utils.error_message_serializers(serializer.errors)
                response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
    return generic_response(response_body=response_body, http_status=http_status)


@transaction.atomic()
@api_view(['POST'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def add_maintenance_data(request):
    request.POST._mutable = True
    request.data['status'] = OptionsEnum.ACTIVE
    request.data['customer'] = h_utils.get_customer_from_request(request, None)
    request.data['module'] = h_utils.get_module_from_request(request, None)
    request.data['modified_by'] = h_utils.get_user_from_request(request, None).id
    request.data['timestamp'] = timezone.now()
    request.POST._mutable = False

    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
    http_status = HTTP_SUCCESS_CODE
    serializer = LogisticMaintenanceDataSerializer(data=request.data, partial=True, context={'request': request})
    if serializer.is_valid():
        entity = serializer.save()
    else:
        for errors in serializer.errors:
            if errors == 'non_field_errors':
                response_body[RESPONSE_MESSAGE] = serializer.errors[errors][0]
            else:
                response_body[RESPONSE_MESSAGE] = h_utils.error_message_serializers(serializer.errors)
                response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
    return generic_response(response_body=response_body, http_status=http_status)


# @api_view(['PATCH'])
# # @append_request_params
# @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
# def mark_activity_inactive(request):
#     status = int(h_utils.get_data_param(request, 'status', None))
#     # activity_id = h_utils.get_data_param(request, 'activity_id', None)
#     list_id = h_utils.get_data_param(request, 'id_list', None)
#
#     response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
#     http_status = HTTP_ERROR_CODE
#
#     for id in list_id:
#         if status in [OptionsEnum.INACTIVE]:
#             activity_schedule = ActivitySchedule.objects.get(id=id)
#             activity_schedule.schedule_activity_status = OptionsEnum.INACTIVE
#             activity_schedule.save()
#
#             response_body[RESPONSE_MESSAGE] = {'success_message': TEXT_OPERATION_SUCCESSFUL}
#             http_status = HTTP_SUCCESS_CODE
#             response_body[RESPONSE_STATUS] = STATUS_OK
#
#         else:
#             response_body[RESPONSE_MESSAGE] = {'success_message': TEXT_OPERATION_UNSUCCESSFUL}
#             http_status = HTTP_ERROR_CODE
#             response_body[RESPONSE_STATUS] = STATUS_ERROR
#
#     return generic_response(response_body=response_body, http_status=http_status)
#
#
# @api_view(['PATCH'])
# # @append_request_params
# @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
# def edit_activity_scehdule(request):
#     response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
#     try:
#
#         return add_activity_scehdule(request=request)
#
#     except:
#         response_body[RESPONSE_MESSAGE] = {'error_message': TEXT_OPERATION_UNSUCCESSFUL}
#         http_status = HTTP_ERROR_CODE
#         response_body[RESPONSE_STATUS] = STATUS_ERROR
#         return generic_response(response_body=response_body, http_status=http_status)
#
#
# @csrf_exempt
# @api_view(['GET'])
# @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
# def get_activity_schedules(request):
#     response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
#     customer_id = h_utils.get_customer_from_request(request, None)
#     sch_id = h_utils.get_default_param(request, 'schedule_id', None)
#     s_id = h_utils.get_default_param(request, 'status_id', None)
#     t_id = h_utils.get_default_param(request, 'truck_id', None)
#     d_id = h_utils.get_default_param(request, 'driver_id', None)
#     a_id = h_utils.get_default_param(request, 'activity_id', None)
#     start_date = h_utils.get_default_param(request, 'start_date', None)
#     end_date = h_utils.get_default_param(request, 'end_date', None)
#     http_status = HTTP_SUCCESS_CODE
#     activities_list = []
#     schedules_list = []
#
#     result_list = {}
#     # Adding a single schedule
#     schedules = util_get_schedules(c_id=customer_id, t_id=t_id, d_id=d_id, sch_id=sch_id, s_id=s_id)
#     for obj in schedules:
#         schedules_data = ActivityScheduleSerializer(obj, context={'request': request})
#         sch_dict = schedules_data.data.copy()
#         sch_dict['action_items'] = util_get_bins_location(action_items=schedules_data.data['action_items'])
#         sch_dict['completion_percentage'] = util_get_schedule_total_count(sch_id=obj.id)
#         schedules_list.append(sch_dict)
#     result_list['schedules'] = schedules_list
#
#     activities = util_get_activities(c_id=customer_id, t_id=t_id, d_id=d_id, sch_id=sch_id, s_id=s_id,
#                                      a_id=a_id, start_date=start_date, end_date=end_date)
#     for obj in activities:
#         activities_data = ActivitySerializer(obj, context={'request': request})
#         act_dict = activities_data.data.copy()
#         act_dict['action_items'] = util_get_bins_location(action_items=activities_data.data['action_items'])
#         activities_list.append(act_dict)
#     result_list['activities'] = activities_list
#
#     upcoming_activity = util_upcoming_activities(c_id=customer_id, sch_id=sch_id, t_id=t_id, d_id=d_id, start_date=start_date, end_date=end_date)
#     if upcoming_activity:
#         upcoming_activity = upcoming_activity[0]
#         result_list['upcoming_activity'] = upcoming_activity.as_queue_json()
#
#     response_body[RESPONSE_DATA] = result_list
#     response_body[RESPONSE_MESSAGE] = {'success':TEXT_OPERATION_SUCCESSFUL}
#     response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
#     return generic_response(response_body=response_body, http_status=http_status)
#
#
# @csrf_exempt
# @api_view(['GET'])
# @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
# def get_activities_data(self):
#     response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
#     customer_id = h_utils.get_customer_from_request(self, None)
#     sch_id = h_utils.get_default_param(self, 'schedule_id', None)
#     s_id = h_utils.get_default_param(self, 'status_id', None)
#     t_id = h_utils.get_default_param(self, 'truck_id', None)
#     d_id = h_utils.get_default_param(self, 'driver_id', None)
#     a_id = h_utils.get_default_param(self, 'activity_id', None)
#     start_date = h_utils.get_default_param(self, 'start_date', None)
#     end_date = h_utils.get_default_param(self, 'end_date', None)
#
#     activities_list = []
#     schedules_list = []
#
#     result_dict = {}
#     activity_data = []
#     # Adding a single schedule
#     if customer_id:
#
#         if a_id:
#             activity_data = util_get_activity_data(c_id=customer_id, t_id=t_id, d_id=d_id, a_id=a_id, s_id=s_id,
#                                                    start_date=start_date, end_date=end_date)
#
#         activities = util_get_activities(c_id=customer_id, t_id=t_id, d_id=d_id, sch_id=sch_id, s_id=s_id,
#                                          a_id=a_id, start_date=start_date, end_date=end_date)
#
#
#         for obj in activities:
#             activities_data = ActivitySerializer(obj, context={'request': self})
#             act_dict = activities_data.data.copy()
#             if obj.activity_status.id not in [IOFOptionsEnum.COMPLETED, IOFOptionsEnum.ABORTED]:
#                 act_dict['truck_device_id'] = obj.primary_entity.device_name.device_id if obj.primary_entity.device_name.device_id else None
#                 act_dict['truck_type'] = obj.primary_entity.entity_sub_type.id if obj.primary_entity.entity_sub_type else None
#                 act_dict['truck_type_label'] = obj.primary_entity.entity_sub_type.label if obj.primary_entity.entity_sub_type else None
#
#             invoices = util_get_bins_collection_data(c_id=customer_id, b_id=None, s_id=s_id, a_id=a_id, sup_id=None,
#                                                           d_id=d_id, t_id=t_id, start_date=start_date, end_date=end_date).\
#                                                           filter(status_id=IOFOptionsEnum.COLLECTED).values('invoice')\
#                                                           .annotate(total_invoice=Sum('invoice'))
#
#             #act_dict['total_invoice'] = invoices['invoice']0
#             if act_dict['action_items']:
#                 act_dict['action_items'] = util_get_bins_location(action_items=None, activity_id=obj.id)
#
#             activities_list.append(act_dict)
#         result_dict['activity'] = activities_list
#
#         for obj in activity_data:
#             schedules_data = ActivityDataSerializer(obj, context={'request': self})
#             sch_dict = schedules_data.data.copy()
#             if sch_dict['action_items']:
#                 sch_dict['action_items'] = util_get_bin_with_location(bin=sch_dict['action_items'])
#
#             if sch_dict['supervisor']:
#                 sch_dict['supervisor'] = util_get_bin_with_location(bin=sch_dict['supervisor'])
#
#             schedules_list.append(sch_dict)
#         result_dict['activity_data'] = schedules_list
#
#         response_body[RESPONSE_DATA] = result_dict
#         response_body[RESPONSE_MESSAGE] = {'success':TEXT_OPERATION_SUCCESSFUL}
#         response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
#     else:
#         response_body[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
#         response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
#     return generic_response(response_body=response_body, http_status=200)
#
#
# @csrf_exempt
# @api_view(['GET'])
# @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
# def get_activities_details(self):
#     response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
#     customer_id = h_utils.get_customer_from_request(self, None)
#     sch_id = h_utils.get_default_param(self, 'schedule_id', None)
#     s_id = h_utils.get_default_param(self, 'status_id', None)
#     t_id = h_utils.get_default_param(self, 'truck_id', None)
#     d_id = h_utils.get_default_param(self, 'driver_id', None)
#     a_id = h_utils.get_default_param(self, 'activity_id', None)
#     start_date = h_utils.get_default_param(self, 'start_date', None)
#     end_date = h_utils.get_default_param(self, 'end_date', None)
#
#     activities_list = []
#     schedules_list = []
#     result_list = {}
#
#     activities = util_get_activities(c_id=customer_id, t_id=t_id, d_id=d_id, sch_id=sch_id, s_id=s_id,
#                                      a_id=a_id, start_date=start_date, end_date=end_date)
#     for obj in activities:
#         activities_data = ActivitySerializer(obj, context={'request': self})
#         act_dict = activities_data.data.copy()
#         act_dict['action_items'] = util_get_bins_location(action_items=activities_data.data['action_items'])
#         activities_list.append(act_dict)
#     result_list['activity'] = activities_list
#
#     response_body[RESPONSE_DATA] = result_list
#     response_body[RESPONSE_MESSAGE] = {'success':TEXT_OPERATION_SUCCESSFUL}
#
#     return generic_response(response_body=response_body, http_status=200)
#
#
# @csrf_exempt
# @api_view(['GET'])
# @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
# def get_upcoming_activities(self):
#     response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
#     customer_id = h_utils.get_customer_from_request(self, None)
#     start_date = h_utils.get_default_param(self, 'start_date', None)
#     end_date = h_utils.get_default_param(self, 'end_date', None)
#
#     upcoming_activities_list = []
#
#     upcoming_activities_dict = {}
#     upcoming_activity = util_upcoming_activities(c_id=customer_id, sch_id=None, t_id=None, d_id=None, start_date=start_date, end_date=end_date)
#     for obj in upcoming_activity:
#         upcoming_activities_dict['upcoming_activity'] = obj.as_queue_json()
#         upcoming_activities_list.append(upcoming_activities_dict.copy())
#
#     response_body[RESPONSE_DATA] = upcoming_activities_list
#     response_body[RESPONSE_MESSAGE] = {'success':TEXT_OPERATION_SUCCESSFUL}
#
#     return generic_response(response_body=response_body, http_status=200)
#
#
# @csrf_exempt
# @api_view(['GET'])
# @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
# def get_bins_activities(request):
#     response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
#     customer_id = h_utils.get_customer_from_request(request, None)
#     bin = h_utils.get_default_param(request, 'bin_id', None)
#     status_id = h_utils.get_default_param(request, 'status_id', None)
#     start_date = h_utils.get_default_param(request, 'start_datetime', None)
#     end_date = h_utils.get_default_param(request, 'end_datetime', None)
#
#     bin_collections_list = []
#
#     upcoming_activities_dict = {}
#     upcoming_activity = util_get_bins_action_data(c_id=customer_id, b_id=bin, s_id=status_id, start_date=start_date, end_date=end_date).order_by('-timestamp')
#     for obj in upcoming_activity:
#         bin_data = ActivityDataSerializer(obj, context={'request': request})
#         bin_data = bin_data.data.copy()
#         bin_collections_list.append(bin_data)
#     upcoming_activities_dict['bins_collection_data'] = bin_collections_list
#     response_body[RESPONSE_DATA] = bin_collections_list
#     response_body[RESPONSE_MESSAGE] = {'success':TEXT_OPERATION_SUCCESSFUL}
#     response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
#
#     return generic_response(response_body=response_body, http_status=200)
#
#
# @csrf_exempt
# @api_view(['POST'])
# @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
# def update_running_activity(request):
#     response_body = {RESPONSE_MESSAGE: "Updated Successfully!", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
#     http_status = HTTP_SUCCESS_CODE
#     customer_id = h_utils.get_customer_from_request(request, None)
#     activity_id = h_utils.get_default_param(request, 'activity_id', None)
#     bins_list = h_utils.get_default_param(request, 'bins', None)
#     action = h_utils.get_default_param(request, 'action', None)
#
#     activity = util_get_activities(customer_id, None, None, None, None, activity_id, None, None).first()
#
#     if activity.activity_status.id not in [IOFOptionsEnum.COMPLETED, IOFOptionsEnum.ABORTED]:
#         logistic_job = create_activity_data(activity_id, activity.primary_entity.id, activity.actor.id, timezone.now(), IOFOptionsEnum.ACTIVITY_UPDATED, None, None, customer_id, activity.module_id,
#                              supervisor=None)
#         logistic_job.save()
#         if action:
#             activity.activity_status = Options.objects.get(id=IOFOptionsEnum.ABORTED)
#             activity.save()
#             a_data = create_activity_data(activity.id, activity.primary_entity.id,
#                                           activity.actor.id, timezone.now(),
#                                           IOFOptionsEnum.ABORTED, None, None, activity.customer_id,
#                                           activity.module_id)
#             a_data.save()
#             BinCollectionData.objects.filter(activity=activity, status_id=IOFOptionsEnum.UNCOLLECTED).update(
#                 status_id=IOFOptionsEnum.ABORT_COLLECTION)
#             if (activity.activity_schedule.end_date is None) or (
#                 activity.activity_schedule.end_date <= timezone.now().date()):
#                 activity.activity_schedule.schedule_activity_status = Options.objects.get(id=OptionsEnum.INACTIVE)
#                 activity.activity_schedule.save()
#             try:
#                 HypernetNotification.objects.filter(
#                     type_id__in=[IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW,
#                                  IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_NO_ACTION_ACCEPT_REJECT,
#                                  IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_DRIVER_REJECT],
#                     activity_id=activity.id,
#                 ).update(status_id=OptionsEnum.INACTIVE)
#             except:
#                 pass
#             notification = send_action_notification(activity.primary_entity.id, activity.actor.id, activity.id,
#                                      activity, "This Activity has been aborted by your administrator. It is no longer valid.",
#                                      IOFOptionsEnum.NOTIFICATION_DRIVER_ACKNOWLEDGE_ACTIVITY_ABORT)
#             notification.save()
#             save_users_group(notification, [User.objects.get(associated_entity=activity.actor).id])
#
#             response_body[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: True}
#             response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
#             return generic_response(response_body=response_body, http_status=http_status)
#         else:
#             if not bins_list:
#                 response_body[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: True}
#                 response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
#                 response_body[
#                     RESPONSE_MESSAGE] = "Bin list cannot be empty. Please select at least one bin."
#                 return generic_response(response_body=response_body, http_status=http_status)
#             bins_in_activity = get_activity_bins(activity_id)
#
#             for b1 in bins_in_activity:
#                 if b1 in bins_list:
#                     pass
#                 else:
#                     check, message = delete_bincollection_data(b1, activity_id)
#                     if not check:
#                         response_body[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: True}
#                         response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
#                         response_body[
#                             RESPONSE_MESSAGE] = message
#                         return generic_response(response_body=response_body, http_status=http_status)
#             for b2 in bins_list:
#                 if b2 in bins_in_activity:
#                     pass
#                 else:
#                     data = create_bin_collection_data(activity_id, activity.primary_entity.id, activity.actor.id, timezone.now(),
#                                                       IOFOptionsEnum.UNCOLLECTED, b2, customer_id, activity.module.id)
#                     if data.activity_id != activity_id:
#                         response_body[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: True}
#                         response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
#                         response_body[
#                             RESPONSE_MESSAGE] = "Bin is already part of another running activity. Bin: " + data.action_item.name
#                         return generic_response(response_body=response_body, http_status=http_status)
#                     if data.status_id == IOFOptionsEnum.UNCOLLECTED:
#                         data.save()
#                     else:
#                         response_body[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: True}
#                         response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
#                         response_body[RESPONSE_MESSAGE] = "Bin is already collected in an ongoing activity and cannot be collected again. Bin: "+ data.action_item.name
#                         return generic_response(response_body=response_body, http_status=http_status)
#
#             activity.action_items = ','.join(map(str, bins_list))
#             activity.save()
#             notification = send_action_notification(activity.primary_entity.id, activity.actor.id, activity.id,
#                                      activity, "Bins have been updated by your administrator.",
#                                      IOFOptionsEnum.NOTIFICATION_DRIVER_ACKNOWLEDGE_BINS_UPDATE)
#             notification.save()
#             save_users_group(notification, [User.objects.get(associated_entity=activity.actor).id])
#             return generic_response(response_body=response_body, http_status=http_status)
#
#     else:
#         response_body[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: True}
#         response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
#         response_body[
#             RESPONSE_MESSAGE] = "Activity can no longer be updated. It may have been completed already."
#         return generic_response(response_body=response_body, http_status=http_status)
#
#
# @csrf_exempt
# @api_view(['GET'])
# @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
# def get_collection_events(request):
#     response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
#     customer_id = h_utils.get_customer_from_request(request, None)
#     truck = h_utils.get_default_param(request, 'truck_id', None)
#     driver = h_utils.get_default_param(request, 'driver_id', None)
#     start_date = h_utils.get_default_param(request, 'start_date', None)
#     end_date = h_utils.get_default_param(request, 'end_date', None)
#
#     bin_collections_list = []
#
#     collection_events = util_get_bins_collection_data(customer_id, None, None, None, None, driver, truck, start_date, end_date)
#     for obj in collection_events:
#         collection_data = BinCollectionDataSerializer(obj, context={'request': request})
#         collection_data = collection_data.data.copy()
#         bin_collections_list.append(collection_data)
#
#     response_body[RESPONSE_DATA] = bin_collections_list
#     response_body[RESPONSE_MESSAGE] = {'success': TEXT_OPERATION_SUCCESSFUL}
#     response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
#
#     return generic_response(response_body=response_body, http_status=200)