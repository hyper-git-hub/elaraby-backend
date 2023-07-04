import traceback

import pyrebase
from django.db.models.signals import post_save
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from rest_framework.decorators import api_view, APIView, permission_classes
from rest_framework.permissions import AllowAny

from iof.models import ActivityData, Activity, IofShifts
from ioa.serializer import *
from hypernet.constants import *
from hypernet.models import Assignment, HypernetNotification, Entity, HypernetPostData
from hypernet.notifications.utils import update_alert_flag_status, util_user_notifications
from hypernet.enums import *

from backend import settings
from customer.models import CustomerPreferences
from hypernet.enums import DeviceTypeEntityEnum, OptionsEnum
from iof.generic_utils import get_generic_jobs, \
    get_generic_distance_travelled, \
    get_generic_volume_consumed, get_generic_device_aggregations
from iof.serializers import BinCollectionDataSerializer
from iof.utils import get_entity, get_activites, create_activity_data, get_time_info, \
    create_bin_collection_data, waste_collection_management, driver_shift_management, \
    util_create_incident_reporting, create_child_parent_assigment, \
    bin_collection_management, verification_management, \
    incident_reporting_list, update_bin_statuses, check_entity_on_current_shift, \
    check_entity_on_activity, driver_shift_management_simplified, update_skip_weight, check_shift_on_truck, \
    get_shift_truck_of_driver, waste_collection_management_withou_rfid, driver_shift_management_revised, \
    report_bin_maintenance, calculate_fuel_cost, calculate_labour_cost, calculate_trip_revenue, \
    calculate_trip_waste_collected, collect_package, start_e2e_collection

from hypernet.notifications.utils import send_action_notification, send_notification_to_admin, save_users_group
from hypernet.utils import *
from options.models import Options
# Create your views here.
from django.utils import timezone
from hypernet.entity.job_V2.utils import util_upcoming_activities, util_get_bins_collection_data
from iof.utils import append_activity, get_schedule_type
from django.db.models import F, Sum
from hypernet.entity.job_V2.utils import util_get_bins_location
from hypernet.serializers import DriverSerializer, TruckSerializer
from django.dispatch import receiver
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from user.serializers import UserLoginSerializer
from user.models import User, ModuleAssignment
from customer.serializers import CustomerListSerializer
from rest_framework.response import Response



@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def get_app_jobs(request):
    c_id = get_customer_from_request(request, None)
    user = get_user_from_request(request, None)
    d_id = user.associated_entity.id
    j_id = get_default_param(request, 'job_id', None)
    response = {RESPONSE_STATUS: STATUS_OK, RESPONSE_MESSAGE: "", RESPONSE_DATA: []}
    result = dict()
    temp_list = []
    completed = []
    failed = []
    if c_id and user:
        if j_id:
            try:
                obj = get_activites(j_id, None, c_id, [IOFOptionsEnum.PENDING, IOFOptionsEnum.REVIEWED,
                                                   IOFOptionsEnum.ACCEPTED, IOFOptionsEnum.RUNNING, IOFOptionsEnum.SUSPENDED,
                                                   IOFOptionsEnum.RESUMED, IOFOptionsEnum.COMPLETED, IOFOptionsEnum.ABORTED, IOFOptionsEnum.REJECTED]) #redundant checks because this util is being used in other places.
            except:
                http_status = HTTP_SUCCESS_CODE
                response[RESPONSE_STATUS] = HTTP_ERROR_CODE
                response[RESPONSE_MESSAGE] = TEXT_OPERATION_UNSUCCESSFUL
                response[RESPONSE_MESSAGE] = "Activity not valid"
                return generic_response(response_body=response, http_status=http_status)
            
            if obj.activity_status_id not in [IOFOptionsEnum.REJECTED, IOFOptionsEnum.FAILED]:
                result['activity_type'] = obj.activity_schedule.activity_type.label if obj.activity_schedule.activity_type else None
                result['activity_status'] = obj.activity_status.label if obj.activity_status else None
                result['assigned_truck'] = obj.primary_entity.name if obj.primary_entity else None
                result['schedule_type'] = get_schedule_type(obj)
                result['activity_time'] = obj.activity_start_time
                result['activity_date'] = obj.created_datetime.date()
                # result['activity_date'] = obj.activity_schedule.start_date
                result['check_point_name'] = obj.activity_check_point.name if obj.activity_check_point else None
                result['check_point_lat_long'] = obj.activity_check_point.source_latlong if obj.activity_check_point else None
                result['end_point_name'] = obj.activity_end_point.name if obj.activity_end_point else None
                result['end_point_lat_long'] = obj.activity_end_point.source_latlong if obj.activity_end_point else None
                result['duration'] = int(obj.duration) if obj.duration else None
                result['action_items'] = util_get_bins_location(None, obj.id)
                response[RESPONSE_DATA] = result
                http_status = HTTP_SUCCESS_CODE
                response[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
                response[RESPONSE_STATUS] = http_status
            else:
                http_status = HTTP_SUCCESS_CODE
                response[RESPONSE_STATUS] = HTTP_ERROR_CODE
                # response[RESPONSE_MESSAGE] = TEXT_OPERATION_UNSUCCESSFUL
                response[RESPONSE_MESSAGE] = "Activity not valid"
        else:
            c_activity = get_activites(None, d_id, c_id, [IOFOptionsEnum.COMPLETED])
            for obj in c_activity:
                completed = append_activity(obj,temp_list)
            result['completed'] = completed
            temp_list = []

            f_activity = get_activites(None, d_id, c_id, [IOFOptionsEnum.ABORTED])
            for obj in f_activity:
                failed = append_activity(obj, temp_list)

            result['failed'] = failed

            upcoming = util_upcoming_activities(c_id, None, None, d_id, None, None)
            if upcoming:
                upcoming = upcoming[0]
                result['upcoming'] = upcoming.as_queue_json()
            else:
                result['upcoming'] = {}
            response[RESPONSE_DATA] = result
            http_status = HTTP_SUCCESS_CODE
            response[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
            response[RESPONSE_STATUS] = http_status
        return generic_response(response_body=response, http_status=http_status)
    else:
        http_status = HTTP_SUCCESS_CODE
        response[RESPONSE_STATUS] = HTTP_ERROR_CODE
        response[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        return generic_response(response_body=response, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def get_driver_info(request):
    response = {RESPONSE_STATUS: STATUS_OK, RESPONSE_MESSAGE: "", RESPONSE_DATA: []}
    user = get_user_from_request(request, None)
    d_id = user.associated_entity.id
    http_status = HTTP_ERROR_CODE
    if d_id and user.associated_entity.type.id == DeviceTypeEntityEnum.DRIVER:
        try:
            obj = Entity.objects.get(id=d_id)
            driver_data = DriverSerializer(obj, context={'request': request})
            response[RESPONSE_DATA] = driver_data.data
            http_status = HTTP_SUCCESS_CODE
            response[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
            response[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
            return generic_response(response_body=response, http_status=http_status)
        except:
            response[RESPONSE_MESSAGE] = USER_DOES_NOT_EXIST
            response[RESPONSE_STATUS] = HTTP_ERROR_CODE
            return generic_response(response_body=response, http_status=http_status)

    else:
        response[RESPONSE_MESSAGE] = NOT_ALLOWED
        response[RESPONSE_STATUS] = HTTP_ERROR_CODE
        return generic_response(response_body=response, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_SUCCESS_CODE))
def get_notifications(request):
    response = {RESPONSE_STATUS: STATUS_OK, RESPONSE_MESSAGE: "", RESPONSE_DATA: []}
    c_id = get_customer_from_request(request, None)
    m_id = get_module_from_request(request, None)
    u_id = get_user_from_request(request, None).id
    type = get_list_param(request, 'type', None)
    #print(len(type))
    start_datetime = get_default_param(request, 'start_datetime', None)
    end_datetime = get_default_param(request, 'end_datetime', None)
    list = []

    http_status = HTTP_SUCCESS_CODE
    if u_id:
        try:
            user = User.objects.get(pk=u_id)
        except:
            response[RESPONSE_MESSAGE] = USER_DOES_NOT_EXIST
            response[RESPONSE_STATUS] = HTTP_ERROR_CODE
            return generic_response(response_body=response, http_status=http_status)
        violations = HypernetNotification.objects.filter(user=user, customer_id = c_id).order_by('-created_datetime')

        if type:
            violations = violations.filter(type_id__in=type)
        #alert_status = update_alert_flag_status(u_id, c_id, m_id)

        if start_datetime and end_datetime:
            violations = violations.filter(timestamp__range=[start_datetime,end_datetime])

        if not start_datetime and not end_datetime and not type:
            violations = violations.filter(timestamp__date = timezone.now().date())
        for obj in violations:
            noti_dic = obj.as_job_notification_json()
            noti_dic['minutes_ago'] = get_time_info(obj.created_datetime)
            list.append(noti_dic)

        http_status = HTTP_SUCCESS_CODE
        response[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
        response[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        response[RESPONSE_DATA] = list
    else:
        response[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
        response[RESPONSE_STATUS] = HTTP_ERROR_CODE
    return generic_response(response_body=response, http_status=http_status)



class MaintenanceUpdate(APIView):
    @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
    def put(self, request):
        response = {RESPONSE_STATUS: STATUS_OK, RESPONSE_MESSAGE: ""}
        response[RESPONSE_DATA] = {}
        customer_id = get_customer_from_request(request, None)
        m_id = get_data_param(request, 'm_id', None)
        driver_id = get_data_param(request, 'driver_id', None)
        module = get_module_from_request(request, None)
        flag = get_data_param(request, 'flag', None)
        if not m_id:
            response[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
            http_status = 400
            response[RESPONSE_STATUS] = STATUS_ERROR
            return generic_response(response_body=response, http_status=http_status)
        try:
            ent = Entity.objects.get(id=m_id)
            assigned_truck = Assignment.objects.get(child_id=ent.id, child__type=DeviceTypeEntityEnum.MAINTENANCE,
                                                parent__type=DeviceTypeEntityEnum.TRUCK).parent_id
            if m_id and driver_id:
                if int(flag) == IOFOptionsEnum.MAINTENANCE_COMPLETED:
                    ent.job_status = Options.objects.get(id=IOFOptionsEnum.MAINTENANCE_COMPLETED)
                    ent.save()
                    maintenance = ActivityData (
                        device_id=m_id,
                        customer_id=customer_id,
                        module_id=module,
                        entity_id=assigned_truck,
                        person_id=driver_id,
                        job_start_timestamp= ent.end_datetime,
                        job_end_timestamp=ent.end_datetime,
                        job_status=ent.job_status,
                        maintenance_type = ent.maintenance_type
                    )

                    maintenance.save()
                    http_status = 200
                    response[RESPONSE_STATUS] = STATUS_OK
        except Exception as e:
            http_status = 400
            response[RESPONSE_STATUS] = STATUS_ERROR

        response[RESPONSE_MESSAGE] = {"OperationSuccessful": True}
        return generic_response(response_body=response, http_status=http_status)

@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def get_app_maintenances(request):
    response = {RESPONSE_STATUS: STATUS_OK, RESPONSE_MESSAGE: ""}
    response[RESPONSE_DATA] = {}
    c_id = get_customer_from_request(request, None)
    d_id = get_default_param(request, 'driver_id', None)
    m_id = get_default_param(request, 'm_id', None)
    s_id = get_default_param(request, 's_id', None)
    result = dict()
    temp_list = []
    if d_id:
        if m_id:
            try:
                maintenance = Entity.objects.get(id = m_id, customer_id = c_id)
                assinged_truck = Assignment.objects.get(child_id=m_id, status_id = OptionsEnum.ACTIVE,
                                                        parent__type_id = DeviceTypeEntityEnum.TRUCK)
                result['maintenance_name'] = maintenance.name
                result['due_date'] = maintenance.end_datetime
                result['maintenance_type'] = maintenance.maintenance_type.label
                result['status'] = maintenance.job_status.label
                result['assigned_truck'] = assinged_truck.parent.name
                http_status = 200
            except:
                http_status = 400
                response[RESPONSE_STATUS] = STATUS_ERROR
            response[RESPONSE_DATA] = result
            http_status = http_status
            response[RESPONSE_STATUS] = STATUS_OK

        else:
            if int(s_id) in [IOFOptionsEnum.MAINTENANCE_COMPLETED, IOFOptionsEnum.MAINTENANCE_OVER_DUE]:
                maintenances = get_generic_jobs(c_id, None, d_id, None, None, s_id, None, None, None)


                for obj in maintenances:
                    temp_list.append({'maintenance_name': obj.device.name,
                                  'status': obj.job_status.label,
                                  'due_date': obj.job_end_timestamp,
                                  'maintenance_type': obj.maintenance_type.label if obj.maintenance_type else None,
                                  'assigned_truck': obj.entity.name})

            else:
                maintenances = Entity.objects.filter(type = DeviceTypeEntityEnum.MAINTENANCE, status_id = OptionsEnum.ACTIVE,
                                                     job_status__id = IOFOptionsEnum.MAINTENANCE_DUE )


                for obj in maintenances:
                    try:
                       truck = Assignment.objects.get(parent__type=DeviceTypeEntityEnum.TRUCK,
                                               status_id=OptionsEnum.ACTIVE,
                                               child_id=obj.id).parent.name



                    except:
                        truck = None

                    temp_list.append({'maintenance_name': obj.name,
                                  'status': obj.job_status.label,
                                  'due_date': obj.end_datetime,
                                  'maintenance_type': obj.maintenance_type.label if obj.maintenance_type else None,
                                  'assigned_truck': truck})

            http_status = 200
            response[RESPONSE_DATA] = temp_list
            http_status = http_status
            response[RESPONSE_STATUS] = STATUS_OK
    else:
        response[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        http_status = 400
        response[RESPONSE_STATUS] = STATUS_ERROR
    return generic_response(response_body=response, http_status=http_status)


class DriverJobUpdate(APIView):
    @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
    def put(self, request):
        response = {RESPONSE_STATUS: STATUS_OK, RESPONSE_MESSAGE: ""}
        response[RESPONSE_DATA] = {}
        customer_id = get_customer_from_request(request, None)
        job_id = get_data_param(request, 'job_id', None)
        user = get_user_from_request(request, None)
        module =  get_module_from_request(request, None)
        timestamp = timezone.now()
        lat_long = get_data_param(request, 'lat_long', None)
        flag = get_data_param(request, 'flag', None)
        remarks = get_data_param(request, 'remarks', None)
        http_status = 200
        result = dict()
        # print(job_id)
        if not job_id:
            response[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
            http_status = 400
            response[RESPONSE_STATUS] = STATUS_ERROR
            return generic_response(response_body=response, http_status=http_status)
        try:
            driver_id = user.associated_entity.id
        except:
            driver_id = None
        activity = Activity.objects.get(id=job_id)

        if flag and driver_id:
            try:
                preferences = CustomerPreferences.objects.get(customer_id=customer_id)
                check, assigned_truck = get_shift_truck_of_driver(None, driver_id)

                if int(flag) == IOFOptionsEnum.FAILED:
                   try:
                        if activity.activity_status.id == IOFOptionsEnum.RUNNING or activity.activity_status.id == IOFOptionsEnum.ACCEPTED:
                            activity.activity_status = Options.objects.get(id=IOFOptionsEnum.FAILED)
                            activity.end_lat_long = lat_long
                            activity_data = create_activity_data(job_id, assigned_truck.id, driver_id, timestamp,
                                                                 IOFOptionsEnum.FAILED, lat_long, None,
                                                                 customer_id, module)

                            activity_data.save()
                            update_bin_statuses(activity.id)
                            if remarks:
                                activity.notes = remarks
                                activity_data.notes = remarks
                                activity_data.save()

                            send_notification_to_admin(assigned_truck.id, activity.actor.id, activity.id, activity,
                                                       [activity.activity_schedule.modified_by.id],
                                                           user.associated_entity.name + " Failed the activity " +
                                                           activity.activity_schedule.activity_type.label + " Please review.",
                                                            IOFOptionsEnum.NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_ABORT, None,
                                                       )
                            HypernetNotification.objects.filter(activity_id=activity.id, driver_id = activity.actor.id,
                                                                    type_id__in=[IOFOptionsEnum.NOTIFCIATION_DRIVER_ACCEPT_REJECT,
                                                                                 IOFOptionsEnum.NOTIFICATION_DRIVER_START_ACTIVITY]).update(status_id = OptionsEnum.INACTIVE)


                           # if (activity.activity_schedule.end_date is None) or (activity.activity_schedule.end_date <= timezone.now().date()):
                            #    activity.activity_schedule.schedule_activity_status = Options.objects.get(id=OptionsEnum.INACTIVE)
                             #   activity.activity_schedule.save()
                            activity.notification_sent = False
                        else:
                            http_status = 200
                            response[RESPONSE_STATUS] = 400
                            response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
                            response[RESPONSE_MESSAGE] = "Activity no longer exists"
                            return generic_response(response_body=response, http_status=http_status)
                   except Exception as e:
                       traceback.print_exc()
                       http_status = 400
                       response[RESPONSE_STATUS] = STATUS_ERROR

                elif int(flag) == IOFOptionsEnum.ACCEPTED:
                    try:
                        if activity.activity_status.id == IOFOptionsEnum.REVIEWED or activity.activity_status.id == IOFOptionsEnum.PENDING:
                            activity.activity_status = Options.objects.get(id=IOFOptionsEnum.ACCEPTED)
                            # activity.lat_long = lat_long
                            activity_data = create_activity_data(job_id, assigned_truck.id, driver_id, timestamp,
                                                             IOFOptionsEnum.ACCEPTED, lat_long, None, customer_id, module)
                            activity_data.save()

                            if remarks:
                                activity.notes = remarks
                                activity_data.notes = remarks
                                activity_data.save()

                            if preferences.activity_accept is True:
                                send_notification_to_admin(assigned_truck.id,driver_id,activity.id,activity,[activity.activity_schedule.modified_by.id],
                                                           user.associated_entity.name + " Accepted the activity " + str(
                                                           activity.activity_schedule.activity_type.label),
                                                            IOFOptionsEnum.NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_ACCEPT,None)


                            else:
                                pass
                            HypernetNotification.objects.filter(activity_id=activity.id, driver_id = activity.actor.id,
                                                             type_id=IOFOptionsEnum.NOTIFCIATION_DRIVER_ACCEPT_REJECT).update(status_id = OptionsEnum.INACTIVE)
                        else:
                            http_status = 200
                            response[RESPONSE_STATUS] = 400
                            response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
                            response[RESPONSE_MESSAGE] = "Activity no longer exists"
                            return generic_response(response_body=response, http_status=http_status)
                    except:
                        traceback.print_exc()
                        http_status = 400
                        response[RESPONSE_STATUS] = STATUS_ERROR

                elif int(flag) == IOFOptionsEnum.REJECTED:
                    try:
                        if activity.activity_status.id in [IOFOptionsEnum.REVIEWED, IOFOptionsEnum.ACCEPTED]:
                            activity.activity_status = Options.objects.get(id=IOFOptionsEnum.REJECTED)

                            activity_data = create_activity_data(job_id, assigned_truck.id, driver_id, timestamp,
                                                             IOFOptionsEnum.REJECTED, lat_long, None, customer_id, module)
                            activity_data.save()
                            if remarks:
                                activity.notes = remarks
                                activity_data.notes = remarks
                                activity_data.save()

                            send_notification_to_admin(assigned_truck.id, driver_id, activity.id, activity,
                                                        [activity.activity_schedule.modified_by.id],
                                                        user.associated_entity.name + " Rejected the activity " + activity.activity_schedule.activity_type.label,
                                                        IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_DRIVER_REJECT, None)
                            activity.notification_sent = False
                            HypernetNotification.objects.filter(activity_id=activity.id, driver_id = activity.actor.id,
                                                                type_id=IOFOptionsEnum.NOTIFCIATION_DRIVER_ACCEPT_REJECT).update(status_id = OptionsEnum.INACTIVE)

                        else:
                            http_status = 200
                            response[RESPONSE_STATUS] = 400
                            response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
                            response[RESPONSE_MESSAGE] = "Activity no longer exists"
                            return generic_response(response_body=response, http_status=http_status)
                    except:
                        traceback.print_exc()
                        http_status = 400
                        response[RESPONSE_STATUS] = STATUS_ERROR

                elif int(flag) == IOFOptionsEnum.SUSPENDED:
                    try:
                        try:
                            shift = IofShifts.objects.get(child_id=driver_id, shift_end_time__isnull=True)
                        except:
                            # traceback.print_exc()
                            response[RESPONSE_MESSAGE] = START_SHIFT
                            http_status = 200
                            response[RESPONSE_STATUS] = 500
                            response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
                            return generic_response(response_body=response, http_status=http_status)

                        activity.activity_status = Options.objects.get(id=IOFOptionsEnum.SUSPENDED)
                        activity_data = create_activity_data(job_id, shift.parent.id, shift.child.id, timestamp,
                                                         IOFOptionsEnum.SUSPENDED, lat_long, None, customer_id, module)
                        activity_data.save()

                        if remarks:
                            activity.notes = remarks
                            activity_data.notes = remarks
                            activity_data.save()

                        if preferences.activity_suspend:
                            send_notification_to_admin(shift.parent.id, shift.child.id, activity.id, activity,
                                                   [activity.activity_schedule.modified_by.id],
                                                       shift.child.name + " Suspended the activity " +
                                                       activity.activity_schedule.activity_type.label,
                                                       IOFOptionsEnum.NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_SUSPEND,None
                                                   )

                    except Exception as e:
                        traceback.print_exc()
                        http_status = HTTP_ERROR_CODE
                        response[RESPONSE_STATUS] = STATUS_ERROR

                elif int(flag) == IOFOptionsEnum.RESUMED:
                    try:
                        try:
                            shift = IofShifts.objects.get(child_id=driver_id, shift_end_time__isnull=True)
                        except:
                            # traceback.print_exc()
                            response[RESPONSE_MESSAGE] = START_SHIFT
                            http_status = 200
                            response[RESPONSE_STATUS] = 500
                            response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
                            return generic_response(response_body=response, http_status=http_status)
                        activity.activity_status = Options.objects.get(id=IOFOptionsEnum.RUNNING)
                        # activity.lat_long = lat_long
                        activity_data = create_activity_data(job_id, shift.parent.id, shift.child.id, timestamp,
                                                         IOFOptionsEnum.RESUMED, lat_long, None, customer_id, module)
                        activity_data.save()
                        if remarks:
                            activity.notes = remarks
                            activity_data.notes = remarks
                            activity_data.save()

                        if preferences.activity_resume:
                            send_notification_to_admin(shift.parent.id, shift.child.id, activity.id, activity,
                                                   [activity.activity_schedule.modified_by.id],
                                                       shift.child.name+ " Resumed the activity " +
                                                       activity.activity_schedule.activity_type.label,
                                                       IOFOptionsEnum.NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_RESUME,None
                                                   )

                    except Exception as e:
                        # traceback.print_exc()
                        http_status = HTTP_ERROR_CODE
                        response[RESPONSE_STATUS] = STATUS_ERROR

                elif int(flag) == IOFOptionsEnum.STARTED:
                    if activity.activity_status_id == IOFOptionsEnum.ABORTED or activity.activity_status_id == IOFOptionsEnum.FAILED:
                        response[RESPONSE_MESSAGE] = ACTIVITY_EXPIRED
                        http_status = 200
                        response[RESPONSE_STATUS] = 500
                        response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
                        return generic_response(response_body=response, http_status=http_status)
                    try:
                        shift = IofShifts.objects.get(child_id = driver_id, shift_end_time__isnull=True)
                    except:
                        # traceback.print_exc()
                        response[RESPONSE_MESSAGE] = START_SHIFT
                        http_status = 200
                        response[RESPONSE_STATUS] = 500
                        response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
                        return generic_response(response_body=response, http_status=http_status)

                    try:
                        try:
                            status = get_generic_device_aggregations(customer_id, assigned_truck.id, None, None)
                        except:
                            response[RESPONSE_MESSAGE] = TRUCK_DATA_DOES_NOT_EXIST
                            http_status = 200
                            response[RESPONSE_STATUS] = 500
                            response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
                            return generic_response(response_body=response, http_status=http_status)
                        if not status.online_status:
                            response[RESPONSE_MESSAGE] = TRUCK_OFFLINE_ACTIVITY
                            http_status = 200
                            response[RESPONSE_STATUS] = 500
                            response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
                            return generic_response(response_body=response, http_status=http_status)
                    except:
                        response[RESPONSE_MESSAGE] = DEFAULT_ERROR_MESSAGE
                        http_status = 200
                        response[RESPONSE_STATUS] = 500
                        response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
                        return generic_response(response_body=response, http_status=http_status)

                    if activity.activity_status.id == IOFOptionsEnum.ACCEPTED:
                        try:
                            HypernetNotification.objects.filter(activity_id=job_id,
                                                             type=IOFOptionsEnum.NOTIFICATION_DRIVER_START_ACTIVITY).update(status_id = OptionsEnum.INACTIVE)
                        except:
                            pass
                        activity.activity_status = Options.objects.get(id=IOFOptionsEnum.RUNNING)
                        activity.start_datetime = timestamp
                        activity.start_lat_long = lat_long
                        activity.save()
                        activity_data = create_activity_data(job_id, shift.parent.id, shift.child_id, timestamp,
                                                             IOFOptionsEnum.STARTED, lat_long, None,
                                                             customer_id, module)

                        if remarks:
                            activity.notes = remarks
                            activity_data.notes = remarks
                        activity_data.save()

                        result = dict()
                        for id in activity.action_items.split(','):    #TODO. Check if this bin has already an uncollected row. (Place under try catch)
                            # try:
                            #     contract = Assignment.objects.get(parent_id = id, child__type_id = DeviceTypeEntityEnum.CONTRACT,
                            #                                       status_id = OptionsEnum.ACTIVE).child_id
                            #     try:
                            #         area = Assignment.objects.get(child_id = contract,
                            #                                       parent__type_id = DeviceTypeEntityEnum.AREA,
                            #                                       status_id = OptionsEnum.ACTIVE).parent_id
                            #     except:
                            #         area = None
                            # except:
                            #     contract = None
                            #     area = None
                            # try:
                            #     client = Entity.objects.get(id=id).client.id
                            # except:
                            #     client = None
                            bin_collection_data = create_bin_collection_data(job_id, shift.parent.id, shift.child.id,
                                                                             timestamp, IOFOptionsEnum.UNCOLLECTED, id,
                                                                             customer_id, module)
                            bin_collection_data.save()
                        if activity.activity_schedule.action_items:
                            result['bins_list'] = activity.activity_schedule.action_items
                        result['activity_start_time'] = activity.start_datetime

                        response[RESPONSE_MESSAGE] = "Activity has started."
                        if preferences.activity_start is True:
                            send_notification_to_admin(shift.parent.id, shift.child.id, activity.id, activity,
                                                       [activity.activity_schedule.modified_by.id],
                                                       shift.child.name + " Started the activity " +
                                                           activity.activity_schedule.activity_type.label,
                                                       IOFOptionsEnum.NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_START, None
                                                       )
                        else:
                            pass
                        response[RESPONSE_DATA] = result
                        http_status = 200
                        response[RESPONSE_STATUS] = http_status
                    else:
                        http_status = 200
                        response[RESPONSE_STATUS] = 400
                        response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
                        response[RESPONSE_MESSAGE] = "Activity no longer exists"
                        return generic_response(response_body=response, http_status=http_status)
                    
                elif int(flag) == IOFOptionsEnum.COMPLETED:
                    try:
                        try:
                            shift = IofShifts.objects.get(child_id=driver_id, shift_end_time__isnull=True)
                        except:
                            # traceback.print_exc()
                            response[RESPONSE_MESSAGE] = START_SHIFT
                            http_status = 200
                            response[RESPONSE_STATUS] = 500
                            response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
                            return generic_response(response_body=response, http_status=http_status)

                        activity.activity_status = Options.objects.get(id=IOFOptionsEnum.COMPLETED)
                        activity.end_datetime = timestamp
                        activity.end_lat_long = lat_long
                        activity.save()
                        a_data = create_activity_data(job_id, shift.parent.id, shift.child.id, timestamp,
                                                      IOFOptionsEnum.COMPLETED, lat_long, None, customer_id, module)
                        update_bin_statuses(activity.id)
                        if remarks:
                            activity.notes = remarks
                            a_data.notes = remarks
                            a_data.save()
                        job_distance = get_generic_distance_travelled(customer_id, shift.parent.id, None, None,
                                                                      activity.start_datetime,
                                                                      timestamp)
                        if job_distance is None:
                            job_distance = 0
                        else:
                            job_distance = job_distance/1000

                        job_volume_consumed = get_generic_volume_consumed(customer_id, shift.parent.id, None, None,
                                                                          activity.start_datetime,
                                                                          timestamp)

                        #Costs being calculated


                        if job_volume_consumed is None:
                            job_volume_consumed = 0

                        duration = (timestamp - activity.start_datetime).total_seconds()
                        duration = round(duration/60)
                        activity.duration = duration
                        activity.distance = job_distance
                        activity.volume_consumed = job_volume_consumed
                        activity.save()
                        a_data.save()

                        fuel_cost = calculate_fuel_cost(shift.parent, job_volume_consumed)
                        labour_cost = calculate_labour_cost(shift.child, duration)

                        a_data_fuel_cost = create_activity_data(job_id, shift.parent.id, shift.child.id, timestamp,
                                                      IOFOptionsEnum.FUEL_COST, lat_long, None, customer_id, module, cost = fuel_cost)


                        a_data_labour_cost = create_activity_data(job_id, shift.parent.id, shift.child.id, timestamp,
                                                      IOFOptionsEnum.LABOUR_COST, lat_long, None, customer_id, module, cost = labour_cost)

                        a_data_fuel_cost.save()
                        a_data_labour_cost.save()


                        activity.trip_cost = a_data_fuel_cost.cost + a_data_labour_cost.cost

                        activity.trip_revenue = calculate_trip_revenue(job_id)

                        activity.waste_collected = calculate_trip_waste_collected(job_id)

                        activity.diesel_price = preferences.diesel_price

                        if job_distance == 0  or job_volume_consumed == 0:
                            activity.fuel_avg = 0
                        else:
                            activity.fuel_avg = job_distance/job_volume_consumed

                        activity.save()

                        result[
                            'job_name'] = activity.activity_schedule.activity_type.label if activity.activity_schedule.activity_type else None
                        if activity.start_datetime:
                            result['activity_start_time'] = activity.start_datetime
                        if activity.end_datetime:
                            result['activity_end_time'] = activity.end_datetime
                        # if job.job_volume_consumed:
                        result['activity_volume_consumed'] = activity.volume_consumed
                        # if job.job_distance:
                        result['activity_distance'] = activity.distance
                        if activity.start_lat_long:
                            job_start_lat, job_start_lng = activity.start_lat_long.split(",")
                            result['activity_start_lat'], result['activity_start_lng'] = float(
                                job_start_lat), float(job_start_lng)

                        if activity.end_lat_long:
                            job_end_lat, job_end_lng = activity.end_lat_long.split(",")
                            result['activity_end_lat'], result['activity_end_lng'] = float(job_end_lat), float(
                                job_end_lng)
                        response[RESPONSE_MESSAGE] = "Job has ended"

                        if preferences.activity_end:
                            send_notification_to_admin(shift.parent.id, shift.child.id, activity.id, activity,
                                                       [activity.activity_schedule.modified_by.id],
                                                       shift.child.name+ " Completed the activity " +
                                                       activity.activity_schedule.activity_type.label,
                                                       IOFOptionsEnum.NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_COMPLETE,None
                                                       )
                        if (activity.activity_schedule.end_date is None) or (activity.activity_schedule.end_date <= timezone.now().date()):
                            activity.activity_schedule.schedule_activity_status = Options.objects.get(id=OptionsEnum.INACTIVE)
                            activity.activity_schedule.save()
                        else:
                            pass
                    except Exception as e:
                        traceback.print_exc()
                        http_status = HTTP_ERROR_CODE
                        response[RESPONSE_STATUS] = STATUS_ERROR

                elif int(flag) == IOFOptionsEnum.TRIP_INCREMENT:
                    try:
                        try:
                            shift = IofShifts.objects.get(child_id=driver_id, shift_end_time__isnull=True)
                        except:
                            # traceback.print_exc()
                            response[RESPONSE_MESSAGE] = START_SHIFT
                            http_status = 200
                            response[RESPONSE_STATUS] = 500
                            response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
                            return generic_response(response_body=response, http_status=http_status)

                        activity.trips += 1
                        activity_data = create_activity_data(job_id, shift.parent.id, shift.child.id, timestamp,
                                                         IOFOptionsEnum.TRIP_INCREMENT, lat_long, None, customer_id, module)
                        activity_data.save()

                        if remarks:
                            activity.notes = remarks
                            activity_data.notes = remarks
                            activity_data.save()

                        # Activate notification when adding this type as notification for trips.
                        # if preferences.activity_suspend:
                        #     send_notification_to_admin(shift.parent.id, shift.child.id, activity.id, activity,
                        #                            [activity.activity_schedule.modified_by.id],
                        #                                shift.child.name + " Suspended the activity " +
                        #                                activity.activity_schedule.activity_type.label,
                        #                                IOFOptionsEnum.NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_SUSPEND,None
                        #                            )

                    except Exception as e:
                        traceback.print_exc()
                        http_status = HTTP_ERROR_CODE
                        response[RESPONSE_STATUS] = STATUS_ERROR
                
                elif int(flag) == IOFOptionsEnum.TRIP_DECREMENT:
                    try:
                        try:
                            shift = IofShifts.objects.get(child_id=driver_id, shift_end_time__isnull=True)
                        except:
                            # traceback.print_exc()
                            response[RESPONSE_MESSAGE] = START_SHIFT
                            http_status = 200
                            response[RESPONSE_STATUS] = 500
                            response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
                            return generic_response(response_body=response, http_status=http_status)

                        activity.trips -= 1
                        activity_data = create_activity_data(job_id, shift.parent.id, shift.child.id, timestamp,
                                                         IOFOptionsEnum.TRIP_DECREMENT, lat_long, None, customer_id, module)
                        activity_data.save()

                        if remarks:
                            activity.notes = remarks
                            activity_data.notes = remarks
                            activity_data.save()

                        # Activate notification when adding this type as notification for trips.
                        # if preferences.activity_suspend:
                        #     send_notification_to_admin(shift.parent.id, shift.child.id, activity.id, activity,
                        #                            [activity.activity_schedule.modified_by.id],
                        #                                shift.child.name + " Suspended the activity " +
                        #                                activity.activity_schedule.activity_type.label,
                        #                                IOFOptionsEnum.NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_SUSPEND,None
                        #                            )

                    except Exception as e:
                        traceback.print_exc()
                        http_status = HTTP_ERROR_CODE
                        response[RESPONSE_STATUS] = STATUS_ERROR
                        
                activity.save()
                http_status = 200
                response[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
                response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: True}
            except Exception as e:
                traceback.print_exc()
                http_status = 400
                response[RESPONSE_STATUS] = STATUS_ERROR
                pass
        return generic_response(response_body=response, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def get_rfid_scan_admin(request):
    customer = get_customer_from_request(request, None)
    
    response_body = {RESPONSE_STATUS: STATUS_OK, RESPONSE_MESSAGE: ""}
    response_body[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: True}
    http_status = HTTP_SUCCESS_CODE
    response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    
    rfid_id = get_param(request, 'rfid', None)
    if rfid_id:
        try:
            entity = Assignment.objects.get(child__name=rfid_id, status_id=OptionsEnum.ACTIVE)
            if entity.customer.id == customer:
                response_body[
                RESPONSE_MESSAGE] = "You are trying to add an existing RFID. Please choose different RFID card/tag." \
                                    " Assigned Asset: "+entity.parent.name+\
                                    " Type: "+entity.parent.type.name
            else:
                response_body[
                    RESPONSE_MESSAGE] = "Scanned Tag/Card does not belong to your Customer. Please contact your administrator"
            response_body[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
            http_status = HTTP_SUCCESS_CODE
            
            return generic_response(response_body=response_body, http_status=http_status)
        except:
            # traceback.print_exc()
            try:
                Entity.objects.get(name=rfid_id, type_id__in=[DeviceTypeEntityEnum.RFID_TAG,DeviceTypeEntityEnum.RFID_CARD])
            except MultipleObjectsReturned:
                ent = Entity.objects.filter(name=rfid_id, type_id__in=[DeviceTypeEntityEnum.RFID_TAG,DeviceTypeEntityEnum.RFID_CARD]).first()
                Entity.objects.filter(name=rfid_id, type_id__in=[DeviceTypeEntityEnum.RFID_TAG,DeviceTypeEntityEnum.RFID_CARD]).delete()
                ent.save()
                traceback.print_exc()
                pass
            except ObjectDoesNotExist:
                response_body[
                    RESPONSE_MESSAGE] = "Scanned Tag/Card Does not exist. Please register it first."
                response_body[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
                response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                http_status = HTTP_SUCCESS_CODE
                # traceback.print_exc()
                return generic_response(response_body=response_body, http_status=http_status)
            try:
                Entity.objects.get(name=rfid_id, type_id__in=[DeviceTypeEntityEnum.RFID_TAG,DeviceTypeEntityEnum.RFID_CARD], customer_id=customer)
            except ObjectDoesNotExist:
                # traceback.print_exc()
                response_body[
                    RESPONSE_MESSAGE] = "Scanned Tag/Card does not belong to your Customer. Please contact your administrator"
                response_body[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
                response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                http_status = HTTP_SUCCESS_CODE
                return generic_response(response_body=response_body, http_status=http_status)
    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def get_rfid_card_tag_scan_admin(request):
    response_body = {RESPONSE_STATUS: STATUS_OK, RESPONSE_MESSAGE: ""}
    response_body[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: True}
    http_status = HTTP_SUCCESS_CODE
    response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    
    rfid_id = get_param(request, 'rfid', None)
    if rfid_id:
        try:
            Entity.objects.get(name=rfid_id, type_id__in=[DeviceTypeEntityEnum.RFID_TAG,DeviceTypeEntityEnum.RFID_CARD])
            # "You are trying to add an existing RFID. Please choose different RFID card/tag."
            response_body[RESPONSE_MESSAGE] = ADD_EXISTING_RFID
            response_body[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
            http_status = HTTP_SUCCESS_CODE
            return generic_response(response_body=response_body, http_status=http_status)
        except MultipleObjectsReturned:
            ent = Entity.objects.filter(name=rfid_id, type_id__in=[DeviceTypeEntityEnum.RFID_TAG,DeviceTypeEntityEnum.RFID_CARD]).first()
            Entity.objects.filter(name=rfid_id, type_id__in=[DeviceTypeEntityEnum.RFID_TAG,DeviceTypeEntityEnum.RFID_CARD]).delete()
            ent.save()
            pass
        except ObjectDoesNotExist:
            pass
            
    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@permission_classes((AllowAny,))
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def get_rfid_scan_driver(request):
    response = {RESPONSE_STATUS: STATUS_OK, RESPONSE_MESSAGE: ""}
    response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
    response[RESPONSE_STATUS] = HTTP_ERROR_CODE
    http_status = HTTP_SUCCESS_CODE
    
    rfid_scanner_id = get_param(request, 'id', None)
    scanned_id = get_param(request, 'rfid', None)
    second_scanned_id = get_param(request, 'rfid_2', None)
    action = get_param(request, 'action', None)
    location = get_param(request, 'location', None)
    
    try:
        rfid = Entity.objects.get(name=rfid_scanner_id, type_id=DeviceTypeEntityEnum.RFID_SCANNER, status_id=OptionsEnum.ACTIVE)
    except:
        # "RFID Scanner does not exist. Please contact your administrator"
        response[RESPONSE_MESSAGE] = SCANNER_DOES_NOT_EXIST
        return generic_response(response_body=response, http_status=http_status)
    try:
        truck = Assignment.objects.get(child=rfid, parent__type_id=DeviceTypeEntityEnum.TRUCK, status_id=OptionsEnum.ACTIVE).parent
    except:
        # "RFID Scanner is not associated with a Truck. Please contact your administrator"
        response[RESPONSE_MESSAGE] = SCANNER_NOT_WITH_TRUCK
        return generic_response(response_body=response, http_status=http_status)
    if scanned_id:
        try:
            scanned_rfid = Entity.objects.get(name=scanned_id, type_id__in=[DeviceTypeEntityEnum.RFID_TAG,DeviceTypeEntityEnum.RFID_CARD], status_id=OptionsEnum.ACTIVE, customer=rfid.customer)
        except MultipleObjectsReturned:
            rfid_valid = Entity.objects.filter(name=scanned_id, type_id__in=[DeviceTypeEntityEnum.RFID_TAG,DeviceTypeEntityEnum.RFID_CARD]).first()
            Entity.objects.filter(name=scanned_id, type_id__in=[DeviceTypeEntityEnum.RFID_TAG,DeviceTypeEntityEnum.RFID_CARD]).exclude(id=rfid_valid.id).delete()
            scanned_rfid = rfid_valid
            pass
        except ObjectDoesNotExist:
            # "RFID Tag/Card does not exist. Please contact your administrator"
            response[RESPONSE_MESSAGE] = RFID_TAG_CARD_DOES_NOT_EXIST
            return generic_response(response_body=response, http_status=http_status)
        try:
            ent = Assignment.objects.get(child=scanned_rfid, status=OptionsEnum.ACTIVE).parent
            # ent is the asset that the scanned asset is associated with. It can be a bin, driver or a client rep
        except:
            # "RFID is not associated with any asset. Please contact your administrator"
            response[
                RESPONSE_MESSAGE] = RFID_NOT_WITH_ASSET
            return generic_response(response_body=response, http_status=http_status)
            
        if action:# check actions against options
            
            action = int(action)
            result = None
            if action == IOFOptionsEnum.START_SHIFT:
                # Start shift logic here
                # result, response[RESPONSE_MESSAGE] = driver_shift_management(truck, ent, True)
                result, response[RESPONSE_MESSAGE] = driver_shift_management_simplified(truck, ent, response)
            
            elif action == IOFOptionsEnum.END_SHIFT:
                # End shift logic here
                result, response[RESPONSE_MESSAGE] = driver_shift_management(truck, ent, False)
    
            elif action == IOFOptionsEnum.COLLECT_WASTE or action == IOFOptionsEnum.WASTE_COLLECTED:
                on_shift, response[RESPONSE_MESSAGE] = check_shift_on_truck(truck)
                # Collect, waste collected logic here
                if on_shift:
                    result, response[RESPONSE_MESSAGE] = waste_collection_management(ent, truck, action, location)
            
            elif action == IOFOptionsEnum.PICKUP_BIN \
                    or action == IOFOptionsEnum.BIN_PICKED_UP \
                    or action == IOFOptionsEnum.CONTRACT_TERMINATION \
                    or action == IOFOptionsEnum.MAINTENANCE_PICKUP \
                    or action == IOFOptionsEnum.UPDATE_SKIP_DETAILS \
                    or action == IOFOptionsEnum.SPARE_SKIP_DEPOSIT \
                    or action == IOFOptionsEnum.WORKSHOP_DROP \
                    or action == IOFOptionsEnum.DROPOFF_BIN:
                # Dropoff and Pick up Bin Logice here
                result, response[RESPONSE_MESSAGE] = bin_collection_management(ent, truck, action, location)
            
            elif action == IOFOptionsEnum.VERIFY_COLLECTION or action == IOFOptionsEnum.SKIP_VERIFITCATION:
                # Supervisor verify/abort  collection logic here
                on_shift, response[RESPONSE_MESSAGE] = check_shift_on_truck(truck)
                if on_shift:
                    result, response[RESPONSE_MESSAGE] = verification_management(ent, response[RESPONSE_MESSAGE],second_scanned_id, action)
            
            elif action == IOFOptionsEnum.UPDATE_SKIP_WEIGHT:
                result, response[RESPONSE_MESSAGE] = update_skip_weight(truck, ent)
            elif action == IOFOptionsEnum.REPORT_MAINTENANCE:
                result, response[RESPONSE_MESSAGE] = report_bin_maintenance(truck, ent)
            
            if result:
                response[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
                response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: True}
        else:  # Send true as no action has been set yet.
            response[RESPONSE_MESSAGE] = ent.name + ', '+','+ent.type.name
            if ent.photo:
                response[RESPONSE_MESSAGE] = ent.name + ',' + request.build_absolute_uri(ent.photo.url)+','+ent.type.name
            response[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
            response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: True}
    return generic_response(response_body=response, http_status=http_status)


@api_view(['POST'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def update_rfid_scan_driver(request):
    response = {RESPONSE_STATUS: STATUS_OK, RESPONSE_MESSAGE: ""}
    response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
    response[RESPONSE_STATUS] = HTTP_ERROR_CODE
    http_status = HTTP_SUCCESS_CODE

    scanned_id = get_data_param(request, 'rfid', None)
    rfid_type = get_data_param(request, 'type', None)
    entity_id = get_data_param(request, 'entity_id', None)
    user = get_user_from_request(request, None)

    if scanned_id:
        try:
            scanned_entity = Entity.objects.get(name=scanned_id)
        except:
            response[RESPONSE_MESSAGE] = RFID_TAG_CARD_DOES_NOT_EXIST
            response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
            response[RESPONSE_STATUS] = HTTP_ERROR_CODE
            http_status = HTTP_SUCCESS_CODE
            return generic_response(response_body=response, http_status=http_status)
        try:
            Assignment.objects.get(child=scanned_entity, child__type_id=rfid_type, status=OptionsEnum.ACTIVE)
            # "Scanned RFID/Tag is already assigned to an existing asset. Please choose different RFID Card/Tag"
            response[RESPONSE_MESSAGE] = RFID_ALREADY_WITH_ASSET
            response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
            response[RESPONSE_STATUS] = HTTP_ERROR_CODE
            http_status = HTTP_SUCCESS_CODE
            return generic_response(response_body=response, http_status=http_status)


        except:
            try:
                assignment = Assignment.objects.get(parent_id=entity_id, parent__type_id=rfid_type, status=OptionsEnum.ACTIVE)
                assignment.status_id = OptionsEnum.INACTIVE
                assignment.save()
                assignment.child.obd2_compliant = False
                assignment.child.save()
            except:
                pass
            truck = Entity.objects.get(id=entity_id, status_id = OptionsEnum.ACTIVE)
            if truck.type_id == DeviceTypeEntityEnum.DRIVER or truck.type_id == DeviceTypeEntityEnum.SUPERVISOR:
                t = DeviceTypeAssignmentEnum.RFID_CARD_ASSIGMENT
            elif truck.type_id == DeviceTypeEntityEnum.BIN:
                t = DeviceTypeAssignmentEnum.RFID_TAG_ASSIGMENT
            
            create_child_parent_assigment(child=scanned_entity.id,
                                          parent=entity_id,
                                          type=t,
                                          customer=scanned_entity.customer_id,
                                          module=scanned_entity.module_id,
                                          modified_by=user.id
                                          )

            
            scanned_entity.obd2_compliant = True
            response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: True}
            http_status = HTTP_SUCCESS_CODE
            response[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
            response[
                RESPONSE_MESSAGE] = "Asset: " + scanned_entity.name + " Type: " + scanned_entity.type.name + " RFID has been updated successfully"
    return generic_response(response_body=response, http_status=http_status)


@api_view(['GET'])
@permission_classes((AllowAny,))
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def get_rfid_scanner_truck(request):
    response = {RESPONSE_STATUS: STATUS_OK, RESPONSE_MESSAGE: ""}
    response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
    response[RESPONSE_STATUS] = HTTP_ERROR_CODE
    http_status = HTTP_SUCCESS_CODE
    rfid_scanner_id = get_param(request, 'id', None)
    try:
        rfid = Entity.objects.get(name=rfid_scanner_id, type_id=DeviceTypeEntityEnum.RFID_SCANNER, status=OptionsEnum.ACTIVE)
    except:
        response[RESPONSE_MESSAGE] = "RFID Scanner does not exist. Please contact your administrator"
        return generic_response(response_body=response, http_status=http_status)
    try:
        truck = Assignment.objects.get(child=rfid, parent__type_id=DeviceTypeEntityEnum.TRUCK, status=OptionsEnum.ACTIVE).parent
    except:
        response[RESPONSE_MESSAGE] = "RFID Scanner is not associated with a Truck. Please contact your administrator"
        return generic_response(response_body=response, http_status=http_status)
    response[RESPONSE_MESSAGE] = 'Truck: '+truck.name+'\nCustomer: '+truck.customer.name
    obj = TruckSerializer(truck, context={'request': request})
    response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: True, 'data': obj.data}
    response[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    return generic_response(response_body=response, http_status=http_status)


@api_view(['POST'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def report_incident(request):
    response = {RESPONSE_STATUS: STATUS_OK, RESPONSE_MESSAGE: "", RESPONSE_DATA: []}
    response[RESPONSE_STATUS] = HTTP_ERROR_CODE
    c_id = get_customer_from_request(request, None)
    user = get_user_from_request(request, None)
    m_id = get_module_from_request(request,None)
    d_id = user.associated_entity.id
    timestamp =  get_data_param(request, 'timestamp', None)
    notes = get_data_param(request, 'notes', None)
    type = get_data_param(request, 'type', None)
    if c_id and user:
        if d_id and user.associated_entity.type.id == DeviceTypeEntityEnum.DRIVER:
            try:
                running_activity = Activity.objects.get(actor_id = d_id, activity_status_id__in =
                                                                    [IOFOptionsEnum.RUNNING, IOFOptionsEnum.SUSPENDED])

                report = util_create_incident_reporting(d_id,running_activity.primary_entity.id,
                                                        running_activity.action_items,
                                                        timestamp,running_activity.id,type,notes, c_id, m_id)


                response[RESPONSE_MESSAGE]= {TEXT_OPERATION_SUCCESSFUL: True}
                http_status = HTTP_SUCCESS_CODE
                response[RESPONSE_STATUS] = http_status

            except:
                truck = Entity.get_truck.__get__(user.associated_entity)
                if truck:
                    report = util_create_incident_reporting(d_id, truck.id,
                                                        None, timestamp, None, type, notes, c_id, m_id)

                else:
                    report = util_create_incident_reporting(d_id, None,
                                                                None, timestamp, None, type, notes, c_id, m_id)
                response[RESPONSE_MESSAGE] = {TEXT_OPERATION_SUCCESSFUL: True}
                http_status = HTTP_SUCCESS_CODE
                response[RESPONSE_STATUS] = http_status

            report.save()
        else:
            response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
            http_status = HTTP_ERROR_CODE
            response[RESPONSE_STATUS] = http_status
    else:
        response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
        http_status = HTTP_ERROR_CODE
        response[RESPONSE_STATUS] = http_status
    return generic_response(response_body=response, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_SUCCESS_CODE))
def incident_report_list(request):
    response = {RESPONSE_STATUS: STATUS_OK, RESPONSE_MESSAGE: "", RESPONSE_DATA: []}
    c_id = get_customer_from_request(request, None)
    user = get_user_from_request(request, None)
    m_id = get_module_from_request(request,None)
    d_id = user.associated_entity.id
    t_id = get_default_param(request, 'truck_id', None)
    http_status = HTTP_SUCCESS_CODE

    result = {}
    if c_id and user:
        if user.associated_entity.type.id != DeviceTypeEntityEnum.DRIVER:
            response[RESPONSE_MESSAGE] = NOT_ALLOWED
            response[RESPONSE_STATUS] = HTTP_ERROR_CODE
        elif d_id and user.associated_entity.type.id == DeviceTypeEntityEnum.DRIVER:
            reports = incident_reporting_list(d_id,c_id,None).values('notes','timestamp',driver=F('actor__name'),truck=F('primary_entity__name'),
                                                                 incident=F('incident_type__label'),
                                                                activity = F('scheduled_activity__activity_schedule__activity_type__label'))

        elif t_id:
            reports = incident_reporting_list(None, c_id, t_id).values('notes', 'timestamp', driver=F('driver__name'), truck=F('primary_entity__name'),
                                                                       incident=F('incident_type__label'),
                                                                       activity=F(
                                                                           'scheduled_activity__activity_schedule__activity_type__label'))
        result['data'] = list(reports)
        response[RESPONSE_DATA] = result
        response[RESPONSE_STATUS] = http_status
        response[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
    else:
        response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
        http_status = HTTP_SUCCESS_CODE
        response[RESPONSE_STATUS] = HTTP_ERROR_CODE
    return generic_response(response_body=response, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_SUCCESS_CODE))
def get_last_job(request):
    response = {RESPONSE_STATUS: STATUS_OK, RESPONSE_MESSAGE: "", RESPONSE_DATA: []}
    c_id = get_customer_from_request(request, None)
    user = get_user_from_request(request, None)
    d_id = user.associated_entity.id
    http_status = HTTP_SUCCESS_CODE
    result = dict()
    if user.associated_entity.type.id == DeviceTypeEntityEnum.DRIVER:
        obj = get_activites(None, d_id, c_id, [IOFOptionsEnum.COMPLETED,
                                               IOFOptionsEnum.ABORTED]).order_by('-created_datetime')
        if obj:
            obj = obj[0]
            result['activity_type'] = obj.activity_schedule.activity_type.label if obj.activity_schedule.activity_type else None
            result['activity_status'] = obj.activity_status.label if obj.activity_status else None
            result['assigned_truck'] = obj.primary_entity.name if obj.primary_entity else None
            result['driver'] = obj.actor.name if obj.actor else None
            result['schedule_type'] = get_schedule_type(obj)
            result['activity_time'] = obj.activity_schedule.activity_start_time
            result['end_point_name'] = obj.activity_end_point.name if obj.activity_end_point else None
            result['end_point_lat_long'] = obj.activity_end_point.source_latlong if obj.activity_end_point else None
            result['check_point_name'] = obj.activity_check_point.name if obj.activity_check_point else None
            result['check_point_lat_long'] = obj.activity_check_point.source_latlong if obj.activity_check_point else None
            result['duration'] = int(obj.duration) if obj.duration else None
            result['action_items'] = util_get_bins_location(obj.action_items, obj.id)
            response[RESPONSE_DATA] = result
            response[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
            response[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
        else:
            response[RESPONSE_DATA] = {}
            response[RESPONSE_STATUS] = 400
            response[RESPONSE_MESSAGE] = NO_LAST_ACTIVITY
    else:
        response[RESPONSE_STATUS] = HTTP_ERROR_CODE
        response[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
    return generic_response(response_body=response, http_status=http_status)


# Removing interceptor because of trips
# @receiver(post_save, sender=IofShifts)
# def intercept_shifts(sender, instance, **kwargs):
#     result = []
#     driver_user = User.objects.get(associated_entity=instance.child).id
#     result.append(driver_user)
#     admin = User.objects.filter(customer=instance.customer, role_id=1)
#     for obj in admin:
#         result.append(obj.id)
#
#     if not instance.shift_end_time:
#         notification = send_action_notification(instance.parent.id, instance.child.id, None, instance,
#                                  instance.child.name + " started the shift ",
#                                 IOFOptionsEnum.NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_SHIFT_START)
#         notification.save()
#         save_users_group(notification,result)
#
#
#     else:
#         notification = send_action_notification(instance.parent.id, instance.child.id, None, instance,
#                                  instance.child.name + " ended the shift",
#                                 IOFOptionsEnum.NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_SHIFT_COMPLETE)
#         notification.save()
#         save_users_group(notification, result)



@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_SUCCESS_CODE))
def driver_shift_activity_status(request):
    response = {RESPONSE_STATUS: STATUS_OK, RESPONSE_MESSAGE: "", RESPONSE_DATA: []}
    c_id = get_customer_from_request(request, None)
    user = get_user_from_request(request, None)
    d_id = user.associated_entity.id
    http_status = HTTP_SUCCESS_CODE
    result = {}
    if user.associated_entity.type.id == DeviceTypeEntityEnum.DRIVER:
        result['shift_status'], shift_obj = check_entity_on_current_shift(d_id, None, c_id)
        if result['shift_status']:
            result['assigned_truck'] = shift_obj.parent.name
        else:
            result['assigned_truck'] = None
        result['on_activity'], activity = check_entity_on_activity(d_id=d_id, t_id=None, c_id=c_id)
        if result['on_activity']:
            result['activity_name'] = activity.activity_schedule.activity_type.label
        else:
            result['activity_name'] = None
            
        response[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        response[RESPONSE_DATA] = result
        response[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
    else:
        response[RESPONSE_STATUS] = HTTP_ERROR_CODE
        response[RESPONSE_MESSAGE] = NOT_ALLOWED
    return generic_response(response_body=response, http_status=http_status)

@api_view(['POST'])
@permission_classes([AllowAny])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def shift_login(request):
    email = get_data_param(request, 'email', None)
    password = get_data_param(request, 'password', None)
    action = get_data_param(request, 'action', None)
    rfid_scanner_id = get_data_param(request, 'rfid_scanner_id', None)
    logged_in_user = get_user_from_request(request, None)

    try:
        rfid = Entity.objects.get(name=rfid_scanner_id, type_id=DeviceTypeEntityEnum.RFID_SCANNER, status_id=OptionsEnum.ACTIVE)
    except:
        return Response(response_json(500, None, 'RFID Scanner doesnot exist'))
        rfid = None
    try:
        truck = Assignment.objects.get(child=rfid, parent__type_id=DeviceTypeEntityEnum.TRUCK, status_id=OptionsEnum.ACTIVE).parent
    except:
        # "RFID Scanner is not associated with a Truck. Please contact your administrator"
        truck = None
        return Response(response_json(500, None, 'No assigned truck with this scanner'))
    if email and password:
        user = authenticate(username=email, password=password)
        if user:
            token = Token.objects.get_or_create(user=user)
            user_serializer = UserLoginSerializer(user)
            user_modules = ModuleAssignment.objects.filter(customer=user.customer)
            customer_serializer = CustomerListSerializer(user.customer)
            data = user_serializer.data
            data['customer'] = customer_serializer.data
            data['token'] = token[0].key
            data['user_role_id'] = None if not user.role else user.role.id
            data['user_role_name'] = None if not user.role else user.role.name
            data['avatar'] = None if not user.avatar else request.build_absolute_uri(user.avatar.url)
            data['module'] = [user_module.module.as_json_module() for user_module in user_modules]
            data['user_entity_type'] = user.associated_entity.entity_sub_type_id if user.associated_entity else None

            user.last_login = timezone.now()
            user.save()

            #result, resp = driver_shift_management_simplified(truck, user.associated_entity, None)

            result, resp = driver_shift_management_revised(truck, user.associated_entity, True)
            #response = Response(response_json(200, data, None))  # TODO: Will be removed later.
            #data['shift_status'] = resp

            data['message'] = resp
            if result is True:
                response = Response(response_json(200, data, None))  # TODO: Will be removed later.
            else:
                response = Response(response_json(500, None, resp))  # TODO: Will be removed later
            return response
        return Response(response_json(500, None, 'Wrong username or password'))

    if int(action) == IOFOptionsEnum.END_SHIFT:
        # End shift logic here
        result, resp = driver_shift_management_revised(truck, logged_in_user.associated_entity, None)
        data = {}
        data['message'] = resp

        if result is True:
            response = Response(response_json(200, data, None))  # TODO: Will be removed later.
        else:
            response = Response(response_json(500, None, resp))  # TODO: Will be removed later
        return response
    return Response(response_json(500, None, TEXT_PARAMS_MISSING))



@api_view(['GET'])
@permission_classes((AllowAny,))
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def manual_waste_collection(request):
    response = {RESPONSE_STATUS: STATUS_OK, RESPONSE_MESSAGE: ""}
    response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
    response[RESPONSE_STATUS] = HTTP_ERROR_CODE
    http_status = HTTP_SUCCESS_CODE

    rfid_scanner_id = get_param(request, 'rfid_scanner_id', None)
    #action = get_param(request, 'action', None)
    location = get_param(request, 'location', None)
    user = get_user_from_request(request, None)
    bin_id = get_param(request, 'bin_id', None)
    invoice = get_param(request, 'invoice', 0)
    weight = get_param(request, 'weight', 0)
    try:
        rfid = Entity.objects.get(name=rfid_scanner_id, type_id=DeviceTypeEntityEnum.RFID_SCANNER,
                                  status_id=OptionsEnum.ACTIVE)
    except:
        # "RFID Scanner does not exist. Please contact your administrator"
        response[RESPONSE_MESSAGE] = SCANNER_DOES_NOT_EXIST
        return generic_response(response_body=response, http_status=http_status)
    try:
        truck = Assignment.objects.get(child=rfid, parent__type_id=DeviceTypeEntityEnum.TRUCK,
                                       status_id=OptionsEnum.ACTIVE).parent
    except:
        # "RFID Scanner is not associated with a Truck. Please contact your administrator"
        response[RESPONSE_MESSAGE] = SCANNER_NOT_WITH_TRUCK
        return generic_response(response_body=response, http_status=http_status)

    try:
        ent = Entity.objects.get(id=bin_id)
        print(ent.name)
        # ent is the asset that the scanned asset is associated with. It can be a bin, driver or a client rep
    except:
        # "RFID is not associated with any asset. Please contact your administrator"
        response[
            RESPONSE_MESSAGE] = RFID_NOT_WITH_ASSET
        return generic_response(response_body=response, http_status=http_status)


    #action = int(action)
    result = None

    #if action == IOFOptionsEnum.COLLECT_WASTE or action == IOFOptionsEnum.WASTE_COLLECTED:
    on_shift, response[RESPONSE_MESSAGE] = check_shift_on_truck(truck)
    # Collect, waste collected logic here
    if on_shift:
        result, response[RESPONSE_MESSAGE] = waste_collection_management_withou_rfid(ent, truck, None, location, invoice, weight)

    if result:
        response[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: True}
    else:  # Send true as no action has been set yet.
        response[RESPONSE_MESSAGE] = ent.name + ', ' + ',' + ent.type.name
        if ent.photo:
            response[RESPONSE_MESSAGE] = ent.name + ',' + request.build_absolute_uri(
                ent.photo.url) + ',' + ent.type.name
        response[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: True}
    return generic_response(response_body=response, http_status=http_status)


########## For E2E: TODO: Remove this in the future or turn this generic
@api_view(['GET'])
@permission_classes((AllowAny,))
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def e2e_actions(request):
    response = {RESPONSE_STATUS: STATUS_OK, RESPONSE_MESSAGE: ""}
    response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
    response[RESPONSE_STATUS] = HTTP_ERROR_CODE
    http_status = HTTP_SUCCESS_CODE
    user = User.objects.get(email='driver_e2e@hypernymbiz.com')
    bin_id = get_param(request, 'id', None)
    location = get_param(request, 'location', None)
    
    if bin_id:
        try:
            bin = Entity.objects.get(name=bin_id, type_id=DeviceTypeEntityEnum.BIN,
                                      status_id=OptionsEnum.ACTIVE)
        except:
            # "RFID Scanner does not exist. Please contact your administrator"
            response[RESPONSE_MESSAGE] = "Scanned Package does not exist"
            return generic_response(response_body=response, http_status=http_status)
        try:
            check, response[RESPONSE_MESSAGE] = collect_package(bin, location, user)
            if check:
                response[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        except:
            traceback.print_exc()
            response[RESPONSE_MESSAGE] = "An error occurred. Please try again later."
    else:
        try:
            check, response[RESPONSE_MESSAGE] = start_e2e_collection(location, user)
            if check:
                response[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        except:
            traceback.print_exc()
            response[RESPONSE_MESSAGE] = "An error occurred. Please try again later."
    return generic_response(response_body=response, http_status=http_status)


@api_view(['GET'])
@permission_classes((AllowAny,))
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def get_e2e_packages(request):
    response = {RESPONSE_STATUS: STATUS_OK, RESPONSE_MESSAGE: ""}
    response[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
    response[RESPONSE_STATUS] = HTTP_ERROR_CODE
    http_status = HTTP_SUCCESS_CODE
    user = User.objects.get(email='driver_e2e@hypernymbiz.com')
    result = dict()
    bin_collections_list = []
    b_data = util_get_bins_collection_data(None, None, None, None, None, user.associated_entity.id, None, None, None)
    try:
        for obj in b_data:
            collection_data = BinCollectionDataSerializer(obj, context={'request': request})
            collection_data = collection_data.data.copy()
            collection_data['entity_location'] = obj.action_item.source_latlong
            bin_collections_list.append(collection_data)
        result['assets'] = bin_collections_list
        response[RESPONSE_DATA] = result
    except:
        traceback.print_exc()
        # "RFID Scanner does not exist. Please contact your administrator"
        response[RESPONSE_MESSAGE] = "Some error occurred. Please try again later."
        return generic_response(response_body=response, http_status=http_status)
    response[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    return generic_response(response_body=response, http_status=http_status)