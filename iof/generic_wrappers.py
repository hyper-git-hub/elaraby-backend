from __future__ import unicode_literals

import traceback
from datetime import timedelta
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.forms.models import model_to_dict
import datetime as date_time

from hypernet.serializers import InvoiceDataSerializer
from iof.models import BinCollectionData, IofShifts, LogisticMaintenanceData
from hypernet import constants
from hypernet.enums import IOFOptionsEnum, DeviceTypeEntityEnum, OptionsEnum, DeviceTypeAssignmentEnum
from hypernet.models import Entity, Assignment
from hypernet.utils import *
from rest_framework.decorators import api_view, APIView
from django.db.models import Sum, Value, FloatField, Count
from hypernet.utils import generic_response, get_data_param, get_default_param, exception_handler
from hypernet.constants import *
from iof.serializers import LogisticMaintenanceDataSerializer
from iop.models import ErrorLogs
from .generic_utils import \
    get_generic_device_aggregations, \
    get_generic_distance_travelled, \
    get_generic_fillups, \
    get_generic_jobs, \
    get_generic_maintenances, \
    get_generic_volume_consumed, \
    get_generic_violations, \
    get_generic_devices, \
    entity_calibration, \
    create_fillup_data, \
    calculate_fuel_avgs, \
    get_generic_entity_jobs, get_uassigned_jobs, util_get_jobs_chart, util_get_jobs_chart_twice
from .utils import \
    get_entity, get_entity_brief, check_entity_on_current_shift, get_activites, \
    check_entity_on_activity, get_assets_list, get_clients_invoice, get_contract_listing, renew_contract, \
    get_invoice_listing, update_invoice_payment_status, get_bins_collected, vehicle_type_reporting,get_device_lastest_data

from hypernet.entity.utils import util_get_entity_dropdown
from hypernet.entity.job_V2.utils import util_get_activities, util_get_schedules
from customer.models import CustomerPreferences
from django.db.models import F
from user.models import User
from django.contrib.auth import authenticate



@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_generic_entities_summary(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    c_id = get_customer_from_request(request, None)
    t_id = get_default_param(request, 'type_id', None)
    e_id = get_default_param(request, 'entity_id', None)
    truck_ids = get_list_param(request, 'truck_ids', None)
    fillups = 0
    start_datetime = get_default_param(request, 'start_datetime', None)
    end_datetime = get_default_param(request, 'end_datetime', None)
    result = {}
    if t_id or e_id:
        entity_violation = get_generic_violations(c_id,e_id, None, None, None, t_id, start_datetime, end_datetime)
        # To be fixed with migrations and review query calls - FIXED WALEED
        entity_maintenances = get_generic_maintenances(c_id,e_id, None, t_id, start_datetime, end_datetime)
        # entity_maintenances = None
        if t_id:
            entity_list = get_generic_devices(c_id,e_id,t_id).count()
        if e_id:
            entity_list = get_generic_devices(c_id,e_id,t_id)

        # To be fixed with migrations and review query calls - FIXED WALEED
        entity_jobs = get_generic_jobs(c_id,e_id, None, None, t_id, None, None, start_datetime, end_datetime)
        # entity_jobs = None
        entity_distance_travelled = get_generic_distance_travelled(c_id, e_id, None, t_id, start_datetime, end_datetime)
        entity_volume_consumed = get_generic_volume_consumed(c_id, e_id, None, t_id, start_datetime, end_datetime)
        entity_fillups = get_generic_fillups(c_id, e_id, None, t_id, start_datetime, end_datetime)
        entity_online = get_generic_device_aggregations(c_id, e_id, None, t_id, truck_ids)
        online_count = 0

        if truck_ids:
            entity_list = entity_online.count()
        if entity_online and t_id:
            for obj in entity_online:
                if obj.online_status:
                    online_count+=1
            result['total_online'] = online_count
        elif entity_online and e_id:
            result['online_status'] = entity_online.online_status

        if entity_violation is not None:
            result['total_violations'] = entity_violation.count()
        if entity_maintenances is not None:
            result['total_maintenances'] = entity_maintenances.count()
        if entity_jobs is not None:
            result['total_jobs'] = entity_jobs.count()
        if entity_distance_travelled:
            result['total_distance_travelled'] = round(entity_distance_travelled, 2)
        if entity_list is not None and t_id:
            result['entity_count'] = entity_list
        if entity_list is not None and e_id:
            result['entity'] = get_entity(e_id, None, c_id)
        if entity_volume_consumed is not None:
            result['total_volume_consumed'] = round(entity_volume_consumed, 2)
        if entity_fillups is not None:
            result['total_fillups'] = len(entity_fillups)
        response_body[RESPONSE_DATA] = result
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
    else:
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
        response_body[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
    return generic_response(response_body=response_body, http_status=200)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_generic_entities_list(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
    c_id = get_customer_from_request(request, None)
    t_id = get_default_param(request, 'type_id', None)
    client_id = get_default_param(request, 'client_id', None)
    truck_ids = get_list_param(request, 'truck_ids', None)
    index_a = int(get_default_param(request, 'index_a', 0))
    index_b = int(get_default_param(request, 'index_b', 0))
    temp_list = []
    if t_id:
        devices = get_generic_devices(c_id, None, t_id, client_id, truck_ids)

        # for dev in devices:
        for i in range(index_a, index_b):
            try:
                device = devices[i]
            except:
                response_body["remaining"] = False
                return generic_response(response_body=response_body, http_status=200)
            try:
                d = get_generic_device_aggregations(c_id, device.id, None, None)
            except:
                d = None

            try:
                result = get_entity(None, device, c_id, context={'request': request})
            except:
                traceback.print_exc()
            if result:
                if d:
                    try:
                        error_log = ErrorLogs.objects.filter(device_id=d.device_id).latest('datetime')
                        result['error_log'] = error_log.inactive_score
                    except Exception as e:
                        print(e)

                    result['online_status'] = d.online_status
                    result['last_updated'] = str(d.last_updated)

                    if d.total_distance:
                        result['total_distance'] = d.total_distance
                    if d.total_trips:
                        result['total_trips'] = d.total_trips
                    if d.total_jobs_completed:
                        result['total_jobs_completed'] = d.total_jobs_completed
                    if d.total_maintenances:
                        result['total_maintenances'] = d.total_maintenances
                    if d.total_violations:
                        result['total_violations'] = d.total_violations
                    if d.total_fillups:
                        result['total_fillups'] = d.total_fillups
                    if d.total_decantations:
                        result['total_decantations'] = d.total_decantations
                    if d.tdist_last24Hrs:
                        result['tdist_last24Hrs'] = d.tdist_last24Hrs
                    if d.tvol_last24Hrs:
                        result['tvol_last24Hrs'] = d.tvol_last24Hrs
                    if d.performance_rating:
                        result['performance_rating'] = d.performance_rating

                    if d.last_density is not None:
                        result['last_density'] = float(d.last_density)
                    if d.last_longitude and d.last_latitude is not None:
                        result['last_latitude'] = float(d.last_latitude)
                        result['last_longitude'] = float(d.last_longitude)
                    if d.last_speed is not None:
                        result['last_speed'] = float(d.last_speed)
                    if d.last_temperature is not None:
                        result['last_temperature'] = float(d.last_temperature)
                    if d.last_volume is not None:
                        result['last_volume'] = float(d.last_volume)
                    if d.last_decantation is not None:
                        result['last_decantation'] = str(d.last_decantation)
                    if d.last_fillup is not None:
                        result['last_fillup'] = str(d.last_fillup)
                temp_list.append(result)
                response_body[RESPONSE_DATA] = temp_list
                response_body["remaining"] = True
                response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
                response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
    else:
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
        response_body[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
    return generic_response(response_body=response_body, http_status=200)



@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_generic_entity_info(request, entity_id):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    c_id = get_customer_from_request(request, None)

    print('Device Info API')
    if entity_id:
        lastest_data=get_device_lastest_data(entity_id)
        try:
            d = get_generic_device_aggregations(c_id, entity_id, None, None)
        except:
            d = None

        result = get_entity(entity_id, None, c_id, context={'request': request})
        if result:
            if result.get('image'):
                result['image'] = request.build_absolute_uri(result.get('image'))
            if d:
                result['online_status'] = d.online_status
                result['last_updated'] = str(d.last_updated)

                try:
                    error_log = ErrorLogs.objects.filter(device_id=d.device_id).latest('datetime')
                    result['error_log'] = error_log.inactive_score
                except Exception as e:
                    print(e)

                if d.total_distance:
                    result['total_distance'] = d.total_distance
                if d.total_trips:
                    result['total_trips'] = d.total_trips
                if d.total_jobs_completed:
                    result['total_jobs_completed'] = d.total_jobs_completed
                if d.total_maintenances:
                    result['total_maintenances'] = d.total_maintenances
                if d.total_violations:
                    result['total_violations'] = d.total_violations
                if d.total_fillups:
                    result['total_fillups'] = d.total_fillups
                if d.total_decantations:
                    result['total_decantations'] = d.total_decantations
                if d.tdist_last24Hrs:
                    result['tdist_last24Hrs'] = d.tdist_last24Hrs
                if d.tvol_last24Hrs:
                    result['tvol_last24Hrs'] = d.tvol_last24Hrs
                if d.performance_rating:
                    result['performance_rating'] = d.performance_rating

                if d.last_density is not None:
                    result['last_density'] = float(d.last_density)
                if d.last_longitude and d.last_latitude is not None:
                    result['last_latitude'] = float(d.last_latitude)
                    result['last_longitude'] = float(d.last_longitude)
                if d.last_speed is not None:
                    result['last_speed'] = float(d.last_speed)
                if d.last_volume is not None:
                    result['last_volume'] = float(d.last_volume)
                if d.last_decantation is not None:
                    result['last_decantation'] = str(d.last_decantation)
                if d.last_fillup is not None:
                    result['last_fillup'] = str(d.last_fillup)
                if lastest_data.active_score is not None:
                    result['last_temperature'] = float(lastest_data.active_score)
                if lastest_data.cdt is not None:
                    result['cdt'] = float(lastest_data.cdt)
                if lastest_data.clm is not None:
                    result['clm'] = lastest_data.clm
            response_body[RESPONSE_DATA] = result
            response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        else:
            response_body[RESPONSE_MESSAGE] = NO_DATA_TO_DISPLAY
            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    else:
        response_body[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
    return generic_response(response_body=response_body, http_status=200)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=200))
def get_entity_calibration(request, entity_id):
    c_id = get_customer_from_request(request, None)
    if entity_id:
        result = entity_calibration(c_id, entity_id)
        return generic_response(response_json(True, result))
    else:
        return generic_response(response_json(False, None, constants.TEXT_PARAMS_MISSING), http_status=500)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_entities_list(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    c_id = get_customer_from_request(request, None)
    user = get_user_from_request(request, None)
    t_id = get_default_param(request, 'type_id', None)
    index_a = int(get_default_param(request, 'index_a', 0))
    index_b = int(get_default_param(request, 'index_b', 0))
    m_id = get_module_from_request(request, None)

    if not c_id:
        response_body[RESPONSE_MESSAGE] = NOT_ALLOWED
        response_body[RESPONSE_STATUS] = 500

    elif not m_id:
        response_body[RESPONSE_MESSAGE] = INVALID_MODULE
        response_body[RESPONSE_STATUS] = 500
    else:
        response_body[RESPONSE_DATA], response_body["remaining"] = get_entity_brief(c_id=c_id, m_id=int(m_id), t_id=int(t_id), e_id=None,
                                                    context={'request': request}, index_a=index_a, index_b=index_b, u_id=user)
        response_body[RESPONSE_STATUS] = 200
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_assets_details(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
    c_id = get_customer_from_request(request, None)
    m_id = get_module_from_request(request, None)
    index_a = int(get_default_param(request, 'index_a', 0))
    index_b = int(get_default_param(request, 'index_b', 0))
    t_id = get_default_param(request, 't_id', None)
    if not c_id:
        response_body[RESPONSE_MESSAGE] = NOT_ALLOWED
        response_body[RESPONSE_STATUS] = 500

    elif not m_id:
        response_body[RESPONSE_MESSAGE] = INVALID_MODULE
        response_body[RESPONSE_STATUS] = 500
    else:
        response_body[RESPONSE_DATA] , response_body["remaining"] = get_assets_list(c_id=c_id, m_id=int(m_id), index_a=index_a, index_b=index_b, t_id=t_id)
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_job_details(request):
    c_id = get_customer_from_request(request, None)
    m_id = get_module_from_request(request, None)
    j_id = get_default_param(request, 'job_id', None)
    s_id = get_default_param(request, 'status_id', None)
    index_a = int(get_default_param(request, 'index_a', 0))
    index_b = int(get_default_param(request, 'index_b', 0))
    if j_id:
        job = get_entity(j_id, None, c_id)
        if int(s_id) != IOFOptionsEnum.PENDING:
            job["job_details"] = model_to_dict(get_generic_jobs(c_id, None, None, None, None, s_id, j_id, None, None))
            job["job_details"]["entity"] = get_entity_brief(c_id, m_id, None,{'request': request}, job["job_details"]["entity"], index_a, index_b)
            job["job_details"]["person"] = get_entity_brief(c_id, m_id, None,{'request': request}, job["job_details"]["person"],index_a, index_b)
            job["job_violations"]= list(get_generic_violations(c_id, None, None, None, j_id, None, None, None).values(
                'id', 'timestamp', 'violation_type_id', 'violation_type__value', 'threshold', 'value', 'latitude', 'longitude', 'title',
                'description', 'threshold_string'
            ))
            job["job_fillups"] = get_generic_fillups(c_id, job["id"], None, None, job["job_details"]["actual_job_start_timestamp"], job["job_details"]["actual_job_end_timestamp"])
        else:
            job["job_details"] = None

        return generic_response(response_json(True, job))
    else:
        return generic_response(response_json(False, None, constants.TEXT_PARAMS_MISSING), http_status=500)


# TODO Refactor .values() method to return only job
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=200))
def get_generic_person_info(request, person_id):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    c_id = get_customer_from_request(request, None)
    http_status = HTTP_SUCCESS_CODE
    if person_id:
        try:
            result = get_entity(person_id, None, c_id)
            response_body[RESPONSE_DATA] = result
            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE

        except:
            result = None

        response_body[RESPONSE_DATA] = result
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    else:
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_UNSUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=200))
def get_jobs_details_list(request):
    import datetime as dt
    c_id = get_customer_from_request(request, None)
    # start_datetime = get_default_param(request, 'start_datetime', None)
    # end_datetime = get_default_param(request, 'end_datetime', None)
    days = request.query_params.get('days', LAST_WEEK)
    group_by = request.query_params.get('group_by')
    group_by, days = ("%H", days) if group_by == "hour" else (GRAPH_DATE_FORMAT, days)
    from_date = dt.date.today() - timedelta(int(days))

    result = {}
    if c_id:
        failed_jobs = get_generic_jobs(c_id, None, None, None, DeviceTypeEntityEnum.TRUCK, IOFOptionsEnum.ABORTED, None,
                                       None, None)
        completed_jobs = get_generic_jobs(c_id, None, None, None, DeviceTypeEntityEnum.TRUCK, IOFOptionsEnum.COMPLETED,
                                          None, None, None)
        running_jobs = get_generic_jobs(c_id, None, None, None, DeviceTypeEntityEnum.TRUCK, IOFOptionsEnum.RUNNING,
                                        None, None, None)
        accepted_jobs = get_generic_jobs(c_id, None, None, None, DeviceTypeEntityEnum.TRUCK, IOFOptionsEnum.ACCEPTED,
                                         None, None, None)
        rejected_jobs = get_generic_entity_jobs(c_id, None, None, IOFOptionsEnum.REJECTED, None, None)
        pending_jobs = get_generic_entity_jobs(c_id, None, None, IOFOptionsEnum.PENDING, None, None)
        un_assigned_jobs = get_uassigned_jobs(c_id, None, None)

        if failed_jobs:
            result["failed_jobs"] = list(failed_jobs.values('entity__name', 'entity_id', 'device__name', 'device_id',
                                                            'person_id', 'person__name', 'job_status__label',
                                                            'job_status_id', 'job_start_timestamp',
                                                            'job_end_timestamp', 'job_start_lat_long',
                                                            'job_end_lat_long'))
            result["failed_jobs_count"] = failed_jobs.count()

        if completed_jobs:
            result["completed_jobs"] = list(
                completed_jobs.values('entity__name', 'entity_id', 'device__name', 'device_id',
                                      'person_id', 'person__name', 'job_status__label', 'job_status_id',
                                      'job_start_timestamp',
                                      'job_end_timestamp', 'job_start_lat_long', 'job_end_lat_long').order_by(
                    '-timestamp'))
            result["completed_jobs_count"] = completed_jobs.count()

        if running_jobs:
            result["running_jobs"] = list(running_jobs.values('entity__name', 'entity_id', 'device__name', 'device_id',
                                                              'person_id', 'person__name', 'job_status__label',
                                                              'job_status_id', 'job_start_timestamp',
                                                              'job_end_timestamp', 'job_start_lat_long',
                                                              'job_end_lat_long').order_by('-timestamp'))
            result["running_jobs_count"] = running_jobs.count()

        if accepted_jobs:
            result["accepted_jobs"] = list(
                accepted_jobs.values('entity__name', 'entity_id', 'device__name', 'device_id',
                                     'person_id', 'person__name', 'job_status__label', 'job_status_id',
                                     'job_start_timestamp',
                                     'job_end_timestamp', 'job_start_lat_long', 'job_end_lat_long').order_by(
                    '-timestamp'))
            result["accepted_jobs_count"] = accepted_jobs.count()

        if rejected_jobs:
            result["rejected_jobs"] = list(rejected_jobs.values(
                'job_start_datetime', 'job_end_datetime', 'description',
                'name', 'id', 'destination_latlong', 'source_latlong', 'job_status_id', 'job_status__label'))
            result["rejected_jobs"] = rejected_jobs.count()

        if pending_jobs:
            result["pending_jobs"] = list(pending_jobs.values(
                'job_start_datetime', 'job_end_datetime', 'description',
                'name', 'id', 'destination_latlong', 'source_latlong', 'job_status_id', 'job_status__label'))
            result["pending_jobs_count"] = pending_jobs.count()

        if un_assigned_jobs:
            result["unassigned_jobs"] = list(un_assigned_jobs.values(
                'job_start_datetime', 'job_end_datetime', 'description',
                'name', 'id', 'destination_latlong', 'source_latlong', 'job_status_id', 'job_status__label'))
            result["unassigned_jobs_count"] = un_assigned_jobs.count()

        result.update(util_get_jobs_chart(pending_jobs, from_date, group_by, "pending"))
        result.update(util_get_jobs_chart(un_assigned_jobs, from_date, group_by, "unassigned"))
        result.update(util_get_jobs_chart(rejected_jobs, from_date, group_by, "rejected"))
        result.update(util_get_jobs_chart_twice(accepted_jobs, from_date, group_by, "accepted"))
        result.update(util_get_jobs_chart_twice(failed_jobs, from_date, group_by, "failed"))
        result.update(util_get_jobs_chart_twice(completed_jobs, from_date, group_by, "completed"))
        result.update(util_get_jobs_chart_twice(running_jobs, from_date, group_by, "running"))

        return generic_response(response_json(True, result))

    else:
        return generic_response(response_json(False, None, constants.TEXT_PARAMS_MISSING), http_status=500)
    return generic_response(response_json(True, result))


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_drivers_list(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    c_id = get_customer_from_request(request,None)
    m_id = get_module_from_request(request,None)
    index_a = int(get_default_param(request, 'index_a', 0))
    index_b = int(get_default_param(request, 'index_b', 0))

    list = []
    final_result = {}
    drivers = util_get_entity_dropdown(c_id, DeviceTypeEntityEnum.DRIVER, m_id)
    http_status = HTTP_SUCCESS_CODE
    if not c_id:
        response_body[RESPONSE_MESSAGE] = NOT_ALLOWED
        response_body[RESPONSE_STATUS] = 500
    elif not m_id:
        response_body[RESPONSE_MESSAGE] = INVALID_MODULE
        response_body[RESPONSE_STATUS] = 500
    else:
        # for obj in drivers:
        for i in range(index_a, index_b):
            try:
                obj = drivers[i]
            except:
                final_result['result'] = list
                response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
                response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
                response_body[RESPONSE_DATA] = final_result
                response_body['remaining'] = False
                return generic_response(response_body=response_body, http_status=http_status)
            result = {}
            result['id'] = obj['id']
            flag, activity = check_entity_on_activity(obj['id'],None,c_id)
            if flag is True:
                result['on_activity'] = True
                result['on_activity_id'] = activity.id
            else:
                result['on_activity'] = None
                result['on_activity_id'] = None
            result['name'] = obj['label']
            result['on_shift'], shift_obj= check_entity_on_current_shift(obj['id'], None, c_id)
            if result['on_shift']:
                result['associated_truck'] = shift_obj.parent.name
                result['associated_truck_id'] = shift_obj.parent.id
            else:
                truck = Entity.get_truck.__get__(Entity.objects.get(id=obj['id']))
                result['associated_truck'] = truck.name if truck else None
                result['associated_truck_id'] = truck.id if truck else None
            if result.get('on_activity'):
                activity= get_activites(None, obj['id'], c_id, [IOFOptionsEnum.RUNNING, IOFOptionsEnum.SUSPENDED])
                for act in activity:
                    result['activity'] = act.activity_schedule.activity_type.label
                    result['activity_id'] = act.id

            result['completed_activities'] = get_activites(None, obj['id'], c_id, [IOFOptionsEnum.COMPLETED]).count()
            result['failed_activities'] = get_activites(None, obj['id'], c_id,
                                                                      [IOFOptionsEnum.ABORTED]).count()
            initial_date = date_time.date.today()
            year = initial_date.year
            month = initial_date.month
            import calendar
            date_ranges = calendar.monthrange(year, month)
            s_date = str(date_time.datetime(year, month, 1))
            e_date = str(date_time.datetime(year, month, date_ranges[1]))
            result['bins_collected'] = get_bins_collected(None, obj['id'], None, c_id, s_date, e_date, [IOFOptionsEnum.WASTE_COLLECTED, IOFOptionsEnum.BIN_PICKED_UP]).count()
            result['status'] = obj['rec_status']
            list.append(result)
        final_result['result'] = list
        response_body['remaining'] = True
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        response_body[RESPONSE_DATA] = final_result
    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def customer_dashboard(request):
    http_status = HTTP_SUCCESS_CODE
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    customer_id = get_customer_from_request(request, None)
    entity = {}
    count = 0
    driver_activity_count = 0
    driver_shift_count =0
    operational_bins_count = 0
    truck_activity_count = 0
    if customer_id:
        entity['total_drivers'] = get_generic_devices(customer_id, None, DeviceTypeEntityEnum.DRIVER).count()
        entity['total_bins'] = get_generic_devices(customer_id, None, DeviceTypeEntityEnum.BIN).count()
        entity['total_trucks'] = get_generic_devices(customer_id, None, DeviceTypeEntityEnum.TRUCK).count()

        drivers = get_generic_devices(customer_id,None,DeviceTypeEntityEnum.DRIVER)
        for obj in drivers:
            flag, activity = check_entity_on_activity(d_id=obj.id, t_id=None, c_id=customer_id)
            if flag:
                driver_activity_count+=1
            flag, shift_obj = check_entity_on_current_shift(d_id=obj.id, t_id=None, c_id=customer_id)
            if flag:
                driver_shift_count +=1

        entity['drivers_on_activity'] = driver_activity_count
        entity['drivers_shift_count'] = driver_shift_count

        bins = get_generic_devices(customer_id, None, DeviceTypeEntityEnum.BIN)
        for obj in bins:
            if obj.obd2_compliant:
                operational_bins_count+=1
        entity['operational_bins'] = operational_bins_count

        trucks = get_generic_devices(customer_id, None, DeviceTypeEntityEnum.TRUCK)
        for obj in trucks:
            flag, activity = check_entity_on_activity(d_id=None, t_id=obj.id, c_id=customer_id)
            if not flag:
                truck_activity_count+=1
        entity['available_trucks'] = truck_activity_count

        activities = util_get_activities(customer_id,None,None,None,None,None,None,None)
        entity['total_activites'] = activities.count()
        for obj in activities:
            if obj.activity_status.id in [IOFOptionsEnum.ACCEPTED, IOFOptionsEnum.REJECTED, IOFOptionsEnum.RUNNING, IOFOptionsEnum.SUSPENDED, IOFOptionsEnum.RESUMED]:
                count +=1
        entity['current_activities'] = count
        count = 0
        schedules = util_get_schedules(customer_id, None, None, None, None)
        entity['total_schedules'] = schedules.count()
        for obj in schedules:
            if obj.schedule_activity_status.id == OptionsEnum.ACTIVE:
                count +=1
        entity['current_schedules'] = count
        count =0
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        response_body[RESPONSE_DATA] = entity
    return generic_response(response_body=response_body, http_status=http_status)



@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def trip_sheet_reporting(request):
    http_status = HTTP_SUCCESS_CODE
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    customer_id = get_customer_from_request(request, None)
    client = get_default_param(request, 'client', None)
    contract = get_list_param(request, 'contracts', None)
    start_datetime = get_default_param(request, 'start_datetime', None)
    end_datetime = get_default_param(request, 'end_datetime', None)
    result_list = []
    if customer_id:
        if client:
            trip_sheet = get_clients_invoice(client,customer_id,
                                [IOFOptionsEnum.WASTE_COLLECTED,IOFOptionsEnum.BIN_PICKED_UP, IOFOptionsEnum.DROPOFF_BIN],
                                start_datetime,end_datetime)
            if contract:
                trip_sheet = trip_sheet.filter(contract_id__in=contract)

            for obj in trip_sheet:
                result_dict = {}
                result_dict['contract'] = obj.contract.name if obj.contract else None
                result_dict['client'] = obj.client.name if obj.client else None
                result_dict['area'] = obj.area.name if obj.area else None
                result_dict['client_party_code'] = obj.client.party_code if obj.client else None
                result_dict['bin'] = obj.action_item.name if obj.action_item else None
                result_dict['supervisor'] = obj.supervisor.name if obj.supervisor else None
                result_dict['verified'] = "No" if not obj.verified else "Yes"
                # result_dict['skip'] = obj.contract.skip_rate if obj.contract else None
                result_dict['skip'] = obj.invoice
                result_dict['time'] = obj.timestamp
                result_dict['contract_type'] = obj.contract.leased_owned.label if obj.contract.leased_owned else None
                result_dict['truck'] = obj.entity.name if obj.entity.name else None
                result_dict['driver'] = obj.actor.name if obj.actor.name else None
                result_list.append(result_dict)

        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        response_body[RESPONSE_DATA] = result_list
    else:
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_UNSUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def invoice_reporting(request):
    http_status = HTTP_SUCCESS_CODE
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    customer_id = get_customer_from_request(request, None)
    contracts = get_list_param(request, 'contracts', None)
    overall_net_amount=0
    overall_total_sum=0
    client = get_default_param(request, 'client', None)
    start_datetime = get_default_param(request, 'start_datetime', None)
    end_datetime = get_default_param(request, 'end_datetime', None)
    result = []
    final_result = {}
    if customer_id:
        preferences = CustomerPreferences.objects.get(customer_id = customer_id)
        if client:
            invoice = get_clients_invoice(client,customer_id,[IOFOptionsEnum.WASTE_COLLECTED,
                                                              IOFOptionsEnum.BIN_PICKED_UP],
                                                            start_datetime,end_datetime)

            if contracts:
                invoice = invoice.filter(contract_id__in = contracts).values('contract__name').annotate(invoice_sum = Sum('invoice'),
                                                                                                        trips= Count('contract_id')).order_by('invoice_sum')

            else:
                invoice = invoice.values('contract__name').annotate(
                    invoice_sum=Sum('invoice'), trips=Count('contract_id')).order_by('invoice_sum')

            invoice = invoice.values('trips', contract=F('contract__name'),
                                     client=F('client__name'), area=F('area__name'),
                                    contract_type=F('contract__leased_owned__label'),
                                     net_amount=F('invoice_sum')).annotate(
                                    vat=Value(preferences.value_added_tax, output_field=FloatField()))

            for obj in invoice:
                obj['total_sum'] = obj['net_amount'] + (obj['net_amount'] * preferences.get_vat_percentage())
                result.append(obj)

            for val in invoice:
                overall_net_amount = overall_net_amount + val['net_amount']
                overall_total_sum = overall_total_sum + val['total_sum']
            final_result['result'] = result
            final_result['overall_net_amount'] = overall_net_amount
            final_result['overall_total_sum'] = overall_total_sum

            response_body[RESPONSE_DATA] = final_result
            response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE

        else:
            response_body[RESPONSE_MESSAGE] = NO_ENTITY_SELECTED + "client"
            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
    else:
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_UNSUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def check_count(request):
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    http_status = HTTP_SUCCESS_CODE
    count = 0
    ents = Entity.objects.filter(type_id=DeviceTypeEntityEnum.BIN)
    result = []
    duplicate = []
    for e in ents:
        if e.name in result:
            count+=1
            duplicate.append(e.name)
        else:
            result.append(e.name)

    print(count)
    response_body[RESPONSE_DATA] = duplicate
    response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_UNSUCCESSFUL
    response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
    return generic_response(response_body=response_body, http_status=http_status)



def delete_bulk_corrupt_assignments(request):
    http_status = HTTP_SUCCESS_CODE
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    bin_name = get_default_param(request, 'bin_name', None)
    customer = get_customer_from_request(request,None)
    result = []
    duplicates = []
    count = 0

    bins = Entity.objects.filter(type_id=DeviceTypeEntityEnum.BIN, customer_id=customer)[:10]

    for b in bins:
        if b.name not in duplicates:
            try:
                tag = Entity.objects.get(name=b.name)
                try:
                    Assignment.objects.get(child__name=tag.name, type_id=DeviceTypeAssignmentEnum.RFID_TAG_ASSIGMENT
                                           )
                except:
                    pass
            except:
                tag = None
        else:
            duplicates.append(b.name)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def manual_fillup(request):
    http_status = HTTP_SUCCESS_CODE
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    customer = get_customer_from_request(request,None)
    module = get_module_from_request(request,None)
    user = get_user_from_request(request,None)
    latitude = get_default_param(request, 'latitude', None)
    longitude = get_default_param(request, 'longitude', None)
    fuel_consumed = get_default_param(request, 'fuel_consumed', None)
    timestamp = get_default_param(request,'timestamp',None)
    try:
        driver = user.associated_entity
        print(driver.id)
        try:
            assigned_truck = IofShifts.objects.get(child_id = driver.id, shift_end_time__isnull=True)
        except:
            print(traceback.print_exc())
            assigned_truck = None
    except:
        driver = None


    if assigned_truck:
        result, flag = calculate_fuel_avgs(assigned_truck.parent, fuel_consumed,timestamp)

        create_fillup_data(result,assigned_truck.parent,customer,module,latitude, longitude, flag,timestamp)
    response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
    response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    return generic_response(response_body=response_body, http_status=http_status)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_contracts_list(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    c_id = get_customer_from_request(request, None)
    t_id = get_default_param(request, 'type_id', None)
    index_a = int(get_default_param(request, 'index_a', 0))
    index_b = int(get_default_param(request, 'index_b', 0))
    m_id = get_module_from_request(request, None)


    if not c_id:
        response_body[RESPONSE_MESSAGE] = NOT_ALLOWED
        response_body[RESPONSE_STATUS] = 500

    elif not m_id:
        response_body[RESPONSE_MESSAGE] = INVALID_MODULE
        response_body[RESPONSE_STATUS] = 500
    else:
        response_body[RESPONSE_DATA], response_body["remaining"] = get_contract_listing(c_id=c_id, m_id=int(m_id), t_id=t_id, e_id=None,
                                                    context={'request': request}, index_a=index_a, index_b=index_b)
        response_body[RESPONSE_STATUS] = 200
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def post_renew_contract(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    c_id = get_customer_from_request(request, None)
    contract_id = get_default_param(request, 'contract_id', None)
    new_date = get_default_param(request, 'date', None)
    
    if not c_id:
        response_body[RESPONSE_MESSAGE] = NOT_ALLOWED
        response_body[RESPONSE_STATUS] = 500
    else:
        response_body[RESPONSE_DATA] = renew_contract(customer_id=c_id, contract_id=contract_id, new_date=new_date,)
        response_body[RESPONSE_STATUS] = 200
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
    return generic_response(response_body=response_body, http_status=200)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def invoice_listing(request):
    http_status = HTTP_SUCCESS_CODE
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    customer_id = get_customer_from_request(request, None)
    start_datetime = get_default_param(request, 'start_datetime', None)
    end_datetime = get_default_param(request, 'end_datetime', None)
    final_result = []
    if customer_id:
        # preferences = CustomerPreferences.objects.get(customer_id = customer_id)
        invoices = get_invoice_listing(None, customer_id,start_datetime,end_datetime)
        for obj in invoices:
            final_result.append(InvoiceDataSerializer(obj, context={'request': request}).data)

        response_body[RESPONSE_DATA] = final_result
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE

    else:
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_UNSUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def update_payment_status(request):
    http_status = HTTP_SUCCESS_CODE
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    customer_id = get_customer_from_request(request, None)
    invoice_id = get_default_param(request, 'invoice_id', None)
    payment_status = get_default_param(request, 'payment_status', None)
    final_result = []
    if customer_id:
        invoice = update_invoice_payment_status(invoice_id, payment_status, customer_id)
        if invoice:
            response_body[RESPONSE_DATA] = final_result
            response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE

        else:
            response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_UNSUCCESSFUL
            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
    return generic_response(response_body=response_body, http_status=http_status)


@transaction.atomic()
@api_view(['POST'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def add_fine(request):
    request.POST._mutable = True
    request.data['status'] = OptionsEnum.ACTIVE
    request.data['customer'] = get_customer_from_request(request, None)
    request.data['module'] = get_module_from_request(request, None)
    request.data['modified_by'] = get_user_from_request(request, None).id
    request.data['cost_type'] = IOFOptionsEnum.MAINTENANCE_DATA_COST_FINE
    request.POST._mutable = False

    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
    http_status = HTTP_SUCCESS_CODE
    serializer = LogisticMaintenanceDataSerializer(data=request.data, partial=True, context={'request': request})
    if serializer.is_valid():
        serializer.save()
    else:
        for errors in serializer.errors:
            if errors == 'non_field_errors':
                response_body[RESPONSE_MESSAGE] = serializer.errors[errors][0]
            else:
                response_body[RESPONSE_MESSAGE] = error_message_serializers(serializer.errors)
                response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
    return generic_response(response_body=response_body, http_status=http_status)



@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def last_shift_data(request):
    http_status = HTTP_SUCCESS_CODE
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    c_id = get_customer_from_request(request, None)
    parent_id = get_default_param(request, 'parent_id', None)
    child_id = get_default_param(request, 'child_id', None)

    shift_data = None
    if parent_id:
        shift_data = IofShifts.objects.filter(parent_id=parent_id,
                                                  shift_end_time__isnull=False,
                                                 customer_id=c_id).order_by('-shift_end_time').first()
    elif child_id:
        shift_data = IofShifts.objects.filter(child_id=child_id,
                                                  shift_end_time__isnull=False,
                                                 customer_id=c_id).order_by('-shift_end_time').first()
    if shift_data:
        response_body[RESPONSE_DATA] = {'d_travelled': shift_data.distance_travelled,
                                        'vol_consumed': shift_data.volume_consumed,
                                        'fuel_avg': shift_data.fuel_avg}

    else:
        response_body[RESPONSE_DATA] = {'d_travelled': None,
                                        'vol_consumed': None,
                                        'fuel_avg': None}

    response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
    response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def vehicles_dashboard_reporting(request):
    http_status = HTTP_SUCCESS_CODE
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    customer_id = get_customer_from_request(request, None)
    vehicle_type = get_default_param(request, 'type', None)
    truck_ids = get_list_param(request, 'truck_ids', None)
    drivers = int(get_default_param(request, 'drivers', 0))
    start_datetime = get_default_param(request, 'start_datetime', None)
    end_datetime = get_default_param(request, 'end_datetime', None)
    final_result = []
    if customer_id:
        # preferences = CustomerPreferences.objects.get(customer_id = customer_id)
        final_result = vehicle_type_reporting(vehicle_type, drivers, customer_id, start_datetime, end_datetime, truck_ids)
        response_body[RESPONSE_DATA] = final_result
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE

    else:
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_UNSUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
    return generic_response(response_body=response_body, http_status=http_status)
