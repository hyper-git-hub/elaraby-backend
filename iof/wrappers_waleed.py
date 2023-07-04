from __future__ import unicode_literals

import traceback

from django.db.models import F, Q, Sum
from rest_framework.decorators import api_view, permission_classes
import pytz
from django.utils import timezone
from dateutil.parser import parse
import datetime
import datetime as date_time


from rest_framework.permissions import AllowAny

from hypernet import constants
from hypernet.entity.job_V2.utils import util_get_activities
from hypernet.entity.utils import util_create_activity
from hypernet.enums import DimensionEnum, OptionsEnum, DeviceTypeAssignmentEnum, DeviceTypeEntityEnum, IOFOptionsEnum
from hypernet.models import Assignment, Entity, HypernetNotification, NotificationGroups
from hypernet.serializers import BinSerializer
from hypernet.utils import *
from hypernet.constants import *
from iof.generic_utils import get_generic_fillups, get_generic_violations, get_generic_maintenances, \
    get_generic_maintenances_snapshot, get_generic_territories, get_maintenance_details, get_generic_decantation
from iof.utils import update_or_delete_activity, check_activity_conflicts_review, get_shift_data, \
    create_bin_collection_data, check_bin_in_activity, get_bins_collected
from iof.models import ActivityData
from .report_utils import compute_data_day, compute_data_month, compute_data_year, create_queryset_drill_report, \
    create_queryset_post_data, compute_data_hour, compute_data_minute, compute_data_second, territories_of_truck, \
    get_assigned_drivers_datetime, get_jobs_of_trucks_datetime, create_queryset_pre_data, \
    create_queryset_maintenance_data, create_queryset_maintenance, create_queryset_cms_truck_data, calculate_stops

from iof.models import Activity, ActivityQueue, BinCollectionData

###Wrappers for Truck and Fleet###
from options.models import *
from iof.utils import create_activity_data
from customer.models import CustomerPreferences
from iof.serializers import ActivitySerializer, LogisticMaintenanceSerializer, LogisticMaintenanceDataSerializer, \
    CMSVehicleReportingSerializer
from hypernet.notifications.utils import send_notification_to_admin
from user.models import User
import hypernet.utils as h_utils
from iof.utils import maintain_excel
from iof.utils import parent_child_assignment

'''
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_jobs_of_entity(request):
    c_id = get_default_param(request, 'customer_id', None)
    f_id = get_default_param(request, 'truck_id', None)
    t_id = get_default_param(request, 'fleet_id', None)
    d_id = get_default_param(request, 'driver_id', None)
    start_datetime = get_default_param(request, 'start_datetime', None)
    end_datetime = get_default_param(request, 'end_datetime', None)
    
    data = dict()
    accomplished_count = 0
    failed_count = 0
    if c_id:
        result = get_jobs(c_id, f_id, t_id, d_id, start_datetime, end_datetime)
        for obj in result:
            if obj.job_status == IOFOptionsEnum.ACCOMPLISHED:
                accomplished_count += 0
            elif obj.job_status == IOFOptionsEnum.FAILED:
                failed_count += 0
            
        data["job_list"] = result
        data["accomplished_count"] = accomplished_count
        data["failed_count"] = failed_count
        
        result = get_pending_jobs(c_id, f_id, t_id, d_id, start_datetime, end_datetime)
        data["pending_jobs"] = result
        data["pending_count"] = result.count()
        result = get_unassigned_jobs(c_id, f_id, t_id, d_id, start_datetime, end_datetime)
        data["unassigned_jobs"] = result
        data["unassigned_count"] = result.count()
    else:
        return generic_response(response_json(False, None, constants.TEXT_PARAMS_MISSING),
                                         http_status=500)
    return generic_response(data, http_status=200)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_drivers_data(request):
    result = dict()
    c_id = get_default_param(request, 'customer_id', None)
    d_id = get_default_param(request, 'driver_id', None)
    if c_id:
        result["driver_details"] = get_driver_details(c_id, d_id)
        if d_id:
            result["driver_job_details"] = get_jobs(c_id, None, None, d_id, None, None).last()
            result["driver_info"] = get_entity(d_id, c_id)
    else:
        return generic_response(response_json(False, None, constants.TEXT_PARAMS_MISSING),
                                         http_status=500)
    return generic_response(result, http_status=200)

'''

@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def drill_down_report(request):
    customer_id = get_customer_from_request(request, None)
    module_id = get_default_param(request, 'module_id', None)
    group_id = get_default_param(request, 'group_id', None)
    type_id = get_default_param(request, 'type_id', None)
    entity_id = get_default_param(request, 'entity_id', None)
    tzinfo = get_default_param(request, 'tzinfo', None)
    person_id = get_default_param(request, 'person_id', None)
    dimension = int(get_default_param(request, 'dimension', None))
    variable = get_list_param(request, 'variable', None)
    drill_date = get_default_param(request, 'time', None)
    if tzinfo:
        tzinfo = pytz.timezone(tzinfo)
    final_result = None
    
    if dimension and variable:
        if dimension == DimensionEnum.YEAR:
            for var in variable:
                val = json.loads(var)
                final_result = compute_data_year(val['variable'], val['aggregation'],
                             create_queryset_drill_report(val['source'], customer_id, group_id, entity_id, type_id,
                                                          None, None), final_result, tzinfo)
            return generic_response(response_json(True, final_result))
        elif dimension == DimensionEnum.MONTH:
            for var in variable:
                val = json.loads(var)
                final_result = compute_data_month(val['variable'], val['aggregation'],
                                                      create_queryset_drill_report(val['source'], customer_id,
                                         group_id, entity_id, type_id, None, None), final_result, drill_date, tzinfo)
            return generic_response(response_json(True, final_result))
        elif dimension == DimensionEnum.DAY:
            for var in variable:
                val = json.loads(var)
                final_result = compute_data_day(val['variable'], val['aggregation'],
                                                    create_queryset_drill_report(val['source'], customer_id,
                                         group_id, entity_id, type_id, None, None), final_result, drill_date, tzinfo)
            return generic_response(response_json(True, final_result))
        elif dimension == DimensionEnum.HOUR:
            for var in variable:
                val = json.loads(var)
                final_result = compute_data_hour(val['variable'], val['aggregation'],
                                                    create_queryset_drill_report(val['source'], customer_id,
                                         group_id, entity_id, type_id, None, None), final_result, drill_date, tzinfo)
            return generic_response(response_json(True, final_result))
        elif dimension == DimensionEnum.MINUTE:
            for var in variable:
                val = json.loads(var)
                final_result = compute_data_minute(val['variable'], val['aggregation'],
                                                    create_queryset_drill_report(val['source'], customer_id,
                                         group_id, entity_id, type_id, None, None), final_result, drill_date, tzinfo)
            return generic_response(response_json(True, final_result))
        elif dimension == DimensionEnum.SECOND:
            for var in variable:
                val = json.loads(var)
                final_result = compute_data_second(val['variable'], val['aggregation'],
                                                    create_queryset_drill_report(val['source'], customer_id,
                                         group_id, entity_id, type_id, None, None), final_result, drill_date, tzinfo)
            return generic_response(response_json(True, final_result))
    else:
        return generic_response(response_json(False, None, constants.TEXT_PARAMS_MISSING),
                                             http_status=500)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def zooming_report_bins(request):
    result = []
    dataset = dict()
    temp_result = {}
    dataset['data'] = []
    data_points = []
    customer_id = get_customer_from_request(request, None)
    module_id = get_default_param(request, 'module_id', None)
    type_id = get_default_param(request, 'type_id', None)
    start_datetime = get_default_param(request, 'start_datetime', None)
    end_datetime =get_default_param(request, 'end_datetime', None)
    variable = get_default_param(request, 'variable', None)
    bin_id = get_default_param(request, 'bin_id', None)
    
    if customer_id:
        queryset = create_queryset_post_data(customer_id, None, bin_id, type_id, start_datetime, end_datetime).order_by('timestamp').values('volume', 'timestamp')
        dataset['name'] = variable
        for obj in queryset:
            if obj['volume']:
                data_points.append(obj['timestamp'].timestamp()*1000)
                data_points.append(float(obj['volume']))
                dataset['data'].append(data_points)
                data_points = []
        result.append(dataset)
        temp_result['data_set'] = result
    else:
        return generic_response(response_json(False, None, constants.TEXT_PARAMS_MISSING),
                                         http_status=500)
    return generic_response(response_json(True, temp_result))


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def zooming_report_bins_new(request):
    result = []
    temp_result = {}
    dataset = []
    data_points = dict()
    customer_id = get_customer_from_request(request, None)
    module_id = get_default_param(request, 'module_id', None)
    type_id = get_default_param(request, 'type_id', None)
    start_datetime = get_default_param(request, 'start_datetime', None)
    end_datetime = get_default_param(request, 'end_datetime', None)
    bin_id = get_default_param(request, 'bin_id', None)
    
    if customer_id:
        queryset = create_queryset_post_data(customer_id, None, bin_id, type_id, start_datetime, end_datetime).order_by(
            'timestamp').values('device_id','volume', 'timestamp')
        for obj in queryset:
            if obj['volume']:
                if type_id:
                    data_points['time'] = obj['timestamp']
                    data_points['value'] = float(obj['volume'])
                    if str(obj['device_id']) in temp_result:
                        temp_result[str(obj['device_id'])].append(data_points)
                    else:
                        temp_result[str(obj['device_id'])] = []
                        temp_result[str(obj['device_id'])].append(data_points)
                else:
                    data_points['time'] = obj['timestamp']
                    data_points['value'] = float(obj['volume'])
                    dataset.append(data_points)

                data_points = dict()
        if temp_result:
            result.append(temp_result)
        elif dataset:
            result=dataset
    else:
        return generic_response(response_json(False, None, constants.TEXT_PARAMS_MISSING),
                                http_status=400)
    return generic_response(response_json(True, result))



@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def zooming_report_trucks(request):
    result = []
    dataset = dict()
    temp_result = {}
    dataset['data'] = []
    data_points = []
    customer_id = get_customer_from_request(request, None)
    module_id = get_default_param(request, 'module_id', None)
    type_id = get_default_param(request, 'type_id', None)
    start_datetime = get_default_param(request, 'start_datetime', None)
    end_datetime = get_default_param(request, 'end_datetime', None)
    variable = get_default_param(request, 'variable', None)
    bin_id = get_default_param(request, 'bin_id', None)
    
    if customer_id:
        queryset = create_queryset_post_data(customer_id, None, bin_id, type_id, start_datetime, end_datetime).order_by(
            'timestamp').values('volume', 'timestamp')
        dataset['name'] = variable
        for obj in queryset:
            if obj['volume']:
                data_points.append(obj['timestamp'].timestamp() * 1000)
                data_points.append(float(obj['volume']))
                dataset['data'].append(data_points)
                data_points = []
        result.append(dataset)
        temp_result['data_set'] = result
    else:
        return generic_response(response_json(False, None, constants.TEXT_PARAMS_MISSING),
                                http_status=400)
    return generic_response(response_json(True, temp_result))


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def map_trail(request):
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    dataset = []
    data_points = dict()
    customer_id = get_customer_from_request(request, None)
    start_datetime = get_default_param(request, 'start_datetime', None)
    end_datetime = get_default_param(request, 'end_datetime', None)
    truck_id = get_default_param(request, 'truck_id', None)
    stops = get_default_param(request, 'stops', None)
    #FIXME LATER.
    #flag = int(get_default_param(request, 'flag', 0))

    http_status = HTTP_SUCCESS_CODE
    if customer_id:
        if start_datetime and end_datetime:
            start_datetime = parse(start_datetime)
            end_datetime = parse(end_datetime)

        queryset = create_queryset_post_data(customer_id, None, truck_id, None, start_datetime, end_datetime).order_by(
        'timestamp').values('speed','latitude', 'longitude', 'timestamp', 'volume')

        for obj in queryset:
            if obj['latitude'] and obj['longitude']:
                data_points['lat'] = (float(obj['latitude']))
                data_points['long'] = (float(obj['longitude']))
                if obj.get('speed'):
                    data_points['speed'] = (float(obj['speed']))
                data_points['timestamp'] = str(obj['timestamp'])
                if obj.get('volume'):
                    data_points['volume'] = (float(obj['volume']))
                dataset.append(data_points)
                data_points = dict()
        if stops:
            dataset.append({'stop_times': calculate_stops(queryset)})
        response_body[RESPONSE_DATA] = dataset
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
    else:
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_UNSUCCESSFUL
    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def snapshot(request):
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    dataset = []
    data_points = {}
    customer_id = get_customer_from_request(request, None)
    start_datetime = get_default_param(request, 'start_datetime', None)
    end_datetime = get_default_param(request, 'end_datetime', None)
    truck_id = get_default_param(request, 'truck_id', None)
    driver_id = get_default_param(request, 'driver_id', None)
    http_status = HTTP_SUCCESS_CODE
    if driver_id:
        driver_curr_truck = Assignment.objects.get(status_id=OptionsEnum.ACTIVE, child_id=driver_id).parent_id
        truck_id = driver_curr_truck
    else:
        truck_id = truck_id

    if customer_id:
        obj = create_queryset_post_data(customer_id, None, truck_id, None, start_datetime, None).order_by(
            'timestamp').first()
        if obj:
            data_points['long'] = obj.longitude if obj else None
            data_points['lat'] = obj.latitude if obj else None
            data_points['speed'] = obj.speed if obj else None
            data_points['weight'] = obj.accelerometer_1 if obj else None
            data_points['timestamp'] = obj.timestamp if obj else None
            data_points['temperature'] = obj.temperature if obj else None
            data_points['volume'] = obj.volume if obj else None
            data_points['truck_name'] = obj.device.name if obj else None
            data_points['territory'] = list(territories_of_truck(truck_id, start_datetime))
            driver_ass_truck = get_assigned_drivers_datetime(truck_id, start_datetime, end_datetime)
            data_points['assigned_driver'] = driver_ass_truck
            # None if not driver_ass_truck else driver_ass_truck.child.as_entity_json()
            if obj.device.volume_capacity:
                data_points['volume'] = float((obj.volume / 100)) * obj.device.volume_capacity
            
            jobs_of_truck = get_jobs_of_trucks_datetime(truck_id, start_datetime)
            if jobs_of_truck:
                jobs_of_truck = ActivitySerializer(jobs_of_truck, partial=True)
                data_points['details_of_job'] = jobs_of_truck.data
        else:
            response_body[RESPONSE_MESSAGE] = NO_DATA_TO_DISPLAY
            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
            return generic_response(response_body=response_body, http_status=http_status)
        # if jobs_of_truck:
        #     jobs_of_truck = jobs_of_truck.order_by('created_datetime') \
        #     .values('id', job_name=F('activity_schedule__schedule_type__label'), job_start_loc=F('start_lat_long'),
        #             job_dest_loc=F('end_lat_long')
        #             , volume=F('volume_consumed'),
        #             status_job=F('activity_status__label'), starttime_job=F('activity_start_time'))

        # else:
        #     data_points['details_of_job'] = None
        dataset.append(data_points)
        response_body[RESPONSE_DATA] = dataset
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    else:
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_UNSUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def maintenance_details(request):
    customer_id = get_customer_from_request(request, None)
    start_datetime = get_default_param(request, 'start_datetime', None)
    end_datetime = get_default_param(request, 'end_datetime', None)
    truck_id = get_default_param(request, 'truck_id', None)
    driver_id = get_default_param(request, 'driver_id', None)
    status = get_default_param(request, 'status', None)

    dataset = []
    data_points = {}

    if customer_id:
        if truck_id:
            maintenances_of_truck = get_generic_maintenances_snapshot(customer_id, truck_id, None, status, None, start_datetime,
                                                                      end_datetime)
        elif driver_id:
            maintenances_of_truck = get_generic_maintenances_snapshot(customer_id, None, driver_id, status, None, start_datetime,
                                                                      end_datetime)
        else:
            maintenances_of_truck = get_generic_maintenances_snapshot(customer_id, None, None, status, None, start_datetime,
                                                                      end_datetime)

        maintenances = maintenances_of_truck.values(type=F('scheduled_activity__activity_schedule__activity_type__label'), driver=F('actor__name'),
                                                    driver_id=F('actor_id'), truck = F('primary_entity__name'), truck_id = F('primary_entity_id'),
                   date_time=F('end_date'), m_status = F('schedule_activity_status__label'))

        data_points['maintenance'] = list(maintenances)
        dataset.append(data_points)
    else:
        return generic_response(response_json(False, None, constants.TEXT_PARAMS_MISSING),
                                http_status=404)
    return generic_response(response_json(True, dataset))


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_fillups_list(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    customer_id = get_customer_from_request(request, None)
    start_datetime = get_default_param(request, 'start_datetime', None)
    end_datetime = get_default_param(request, 'end_datetime', None)
    truck_id = get_default_param(request, 'truck_id', None)
    http_status = HTTP_SUCCESS_CODE
    dataset = []
    data_points = {}

    if customer_id:
        data_points['fillups'] = get_generic_fillups(customer_id, truck_id, None, None, start_datetime, end_datetime)
        dataset.append(data_points)
        response_body[RESPONSE_DATA] = dataset
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
    else:
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
        response_body[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_decantations_list(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    customer_id = get_customer_from_request(request, None)
    start_datetime = get_default_param(request, 'start_datetime', None)
    end_datetime = get_default_param(request, 'end_datetime', None)
    truck_id = get_default_param(request, 'truck_id', None)
    http_status = HTTP_SUCCESS_CODE
    dataset = []
    data_points = {}

    if customer_id:
        decatations_of_asset = get_generic_decantation(customer_id, truck_id, None, None, start_datetime, end_datetime)
        data_points['decantations'] = decatations_of_asset
        dataset.append(data_points)
        response_body[RESPONSE_DATA] = dataset
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
    else:
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
        response_body[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_violations_list(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    customer_id = get_customer_from_request(request, None)
    start_datetime = get_default_param(request, 'start_datetime', None)
    end_datetime = get_default_param(request, 'end_datetime', None)
    entity_id = get_default_param(request, 'entity_id', None)
    driver_id = get_default_param(request, 'driver_id', None)
    type_id = get_default_param(request, 'type_id', None)
    http_status = HTTP_SUCCESS_CODE
    dataset = []
    data_points = {}

    if customer_id:
        if driver_id:
            violations = get_generic_violations(customer_id, None, None, driver_id, None, type_id, start_datetime,
                                                end_datetime).filter(violation_type__isnull=False)
        elif entity_id:
            violations = get_generic_violations(customer_id, entity_id, None, None, None, type_id, start_datetime,
                                                end_datetime).filter(violation_type__isnull=False)
        else:
            violations = get_generic_violations(customer_id, None, None, None, None, type_id, start_datetime,
                                                end_datetime).filter(violation_type__isnull=False)

        violations_detail = violations.values('violation_type__label',
                   assigned_activity=F('activity_id'),
                   driver_assigned=F('driver__name'),
                   threshold_violation=F('threshold'),
                   violation_value=F('value'), lat=F('latitude'), long=F('longitude'),
                   date=F('timestamp'),
                   entity_id=F('device_id'),
                   violation_id=F('id'))

        data_points['violations'] = list(violations_detail)
        dataset.append(data_points)
        response_body[RESPONSE_DATA] = dataset
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE

    else:
        response_body[RESPONSE_DATA] = dataset
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_maintenance_summary(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    customer_id = get_customer_from_request(request, None)
    start_datetime = get_default_param(request, 'start_datetime', None)
    end_datetime = get_default_param(request, 'end_datetime', None)
    http_status = HTTP_SUCCESS_CODE
    result = dict()
    if customer_id:
       result['due_maintenance'] = Entity.objects.filter(type = DeviceTypeEntityEnum.MAINTENANCE,
                                                             job_status_id = IOFOptionsEnum.MAINTENANCE_DUE,
                                                             status = OptionsEnum.ACTIVE).count()

       result['over_due'] = Entity.objects.filter(type = DeviceTypeEntityEnum.MAINTENANCE,
                                                             job_status_id = IOFOptionsEnum.MAINTENANCE_OVER_DUE,
                                                             status = OptionsEnum.ACTIVE).count()


       result['completed'] = Entity.objects.filter(type = DeviceTypeEntityEnum.MAINTENANCE,
                                                             job_status_id = IOFOptionsEnum.MAINTENANCE_COMPLETED,
                                                             status = OptionsEnum.ACTIVE).count()

       result['service_maintenance'] = get_maintenance_details(customer_id, None,
                                                               IOFOptionsEnum.SERVICE_MAINTENANCE,
                                                               start_datetime, end_datetime).count()

       result['tyre_replacement'] =  get_maintenance_details(customer_id, None,
                                                             IOFOptionsEnum.TYRE_REPLACEMENT_MAINTENANCE,
                                                             start_datetime, end_datetime).count()

       result['suspension_repair_replacement'] = get_maintenance_details(customer_id, None,
                                                                         IOFOptionsEnum.SUSPENSION_REPAIR_MAINTENANCE,
                                                                         start_datetime, end_datetime).count()

       result['engine_tuning'] = get_maintenance_details(customer_id, None,
                                                         IOFOptionsEnum.ENGINE_TUNING_MAINTENANCE,
                                                         start_datetime, end_datetime).count()
       response_body[RESPONSE_DATA] = result
       response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
       response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    else:
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_UNSUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_territory_info(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    customer_id = get_customer_from_request(request, None)
    http_status = HTTP_SUCCESS_CODE
    territories = dict()
    if customer_id:
        territories['total'] = get_generic_territories(customer_id, None, None).count()
        territories['red'] = get_generic_territories(customer_id, None, IOFOptionsEnum.RED).count()
        territories['blue'] = get_generic_territories(customer_id, None, IOFOptionsEnum.BLUE).count()
        territories['green'] = get_generic_territories(customer_id, None, IOFOptionsEnum.GREEN).count()
        response_body[RESPONSE_DATA] = territories
        response_body[RESPONSE_MESSAGE] =TEXT_OPERATION_SUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    else:
        response_body[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_review_form_data(request):
    customer_id = get_customer_from_request(request, None)
    result = dict()
    http_status = HTTP_SUCCESS_CODE
    activity_id = get_default_param(request, 'a_id', None)
    temp_list = []
    if activity_id and customer_id:
        try:
            obj = Activity.objects.get(id=activity_id)
            result['truck_name'] = obj.activity_schedule.primary_entity.name
            result['truck_id'] = obj.activity_schedule.primary_entity.id
            result['driver_name'] = obj.activity_schedule.actor.name
            result['driver_id'] = obj.activity_schedule.actor.id
            result['bins_list'] = obj.activity_schedule.action_items
            result['start_time'] = obj.activity_start_time
            result['dump_id'] = obj.activity_end_point.id
            result['dump_name'] = obj.activity_end_point.name
            result['dump_lat_long'] = obj.activity_end_point.source_latlong
            result['sorting_id'] = obj.activity_check_point.id if obj.activity_check_point else None
            result['sorting_name'] = obj.activity_check_point.name if obj.activity_check_point else None
            if obj.activity_status.id == IOFOptionsEnum.PENDING:
                result['message'] = 'No conflict, review this activity'
                result['flag'] = True
            elif obj.activity_status.id == IOFOptionsEnum.CONFLICTING:
                result['message'] = 'The truck, driver or bin' + ENTITY_OCCUPIED
                result['flag'] = False
            elif obj.activity_status.id == IOFOptionsEnum.REJECTED:
                result['message'] = 'Activity rejected. Please review.'
                result['flag'] = False
            elif obj.activity_status.id == IOFOptionsEnum.ABORTED:
                result['message'] = 'Activity no longer valid.'
                result['flag'] = False
    
            if obj.activity_status.id == IOFOptionsEnum.FAILED:
                result['message'] = 'Activity failed by driver. Please review'
                result['flag'] = False
                bin = BinCollectionData.objects.filter(activity=obj, status_id=IOFOptionsEnum.ABORT_COLLECTION)
                if bin.count() >0:
                    for b in bin:
                        temp_list.append({'bin_name': b.action_item.name,
                                          'bin_id': b.action_item.id,
                                          'bin_lat_long': b.action_item.source_latlong,
                                          'bin_weight': b.action_item.weight})
                    result['action_items'] = temp_list
                else:
                    for id in obj.activity_schedule.action_items.split(','):
                        bin = Entity.objects.get(id=id)
                        temp_list.append({'bin_name': bin.name,
                                          'bin_id': bin.id,
                                          'bin_lat_long': bin.source_latlong,
                                          'bin_weight': bin.weight})
                    result['action_items'] = temp_list
    
            else:
                for id in obj.activity_schedule.action_items.split(','):
                    bin = Entity.objects.get(id=id)
                    temp_list.append({'bin_name': bin.name,
                                      'bin_id': bin.id,
                                      'bin_lat_long':bin.source_latlong,
                                      'bin_weight': bin.weight})
                result['action_items'] = temp_list
            

        except:
            traceback.print_exc()
            # obj = ActivityQueue.objects.get(id=activity_id)
            # result['truck_name'] = obj.activity_schedule.primary_entity.name
            # result['truck_id'] = obj.activity_schedule.primary_entity.id
            # result['driver_name'] = obj.activity_schedule.actor.name
            # result['driver_id'] = obj.activity_schedule.actor.id
            # result['bins_list'] = obj.activity_schedule.action_items
            # result['start_time'] = obj.activity_datetime
            # result['dump_id'] = obj.activity_end_point.id
            # result['dump_name'] = obj.activity_end_point.name
            # result['sorting_id'] = obj.activity_check_point.id
            # result['sorting_name'] = obj.activity_check_point.name
            # for id in obj.activity_schedule.action_items.split(','):
            #     bin = Entity.objects.get(id=id)
            #     temp_list.append({'bin_name': bin.name,
            #                       'bin_id': bin.id,
            #                       'bin_lat_long': bin.source_latlong,
            #                       'bin_weight': bin.weight})
            # result['action_items'] = temp_list
            # http_status = HTTP_SUCCESS_CODE

        # notification = HypernetNotification.objects.get(queue_id = obj.id)
        # if notification.type.id == IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_DRIVER_CONFLICT:
        #     result['message'] = str(obj.actor) + ENTITY_OCCUPIED
        # if notification.type.id == IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_TRUCK_CONFLICT:
        #     result['message'] = str(obj.primary_entity) + ENTITY_OCCUPIED
    else:
        return generic_response(response_json(False, None, constants.TEXT_PARAMS_MISSING),
                                http_status=500)
    return generic_response(response_json(http_status, result))


@api_view(['POST'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def edit_activity(request):
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    pk = h_utils.get_data_param(request, 'id', None)
    request.POST._mutable = True
    request.data['customer'] = h_utils.get_customer_from_request(request, None)
    request.data['module'] = h_utils.get_module_from_request(request, None)
    request.data['user'] = h_utils.get_user_from_request(request, None).id
    request.POST._mutable = False
    http_status = HTTP_SUCCESS_CODE
    try:
        if pk and request.data.get('customer'):
            preferences = CustomerPreferences.objects.get(customer_id=request.data.get('customer'))
            activity = Activity.objects.get(id=pk)
            flag = request.data.get('flag')
            if activity.activity_status.id in [IOFOptionsEnum.PENDING, IOFOptionsEnum.REJECTED, IOFOptionsEnum.CONFLICTING, IOFOptionsEnum.FAILED, IOFOptionsEnum.ACCEPTED, IOFOptionsEnum.REVIEWED]:
                serializer = ActivitySerializer(activity, data=request.data, partial=True)
                if serializer.is_valid():

                    serializer = serializer.validated_data

                    serializer.get('actor')
                    if int(flag) == IOFOptionsEnum.ABORTED:
                        activity.activity_status = Options.objects.get(id=IOFOptionsEnum.ABORTED)
                        activity.save()
                        a_data = create_activity_data(activity.id, activity.primary_entity.id,
                                                      activity.actor.id, timezone.now(),
                                                      IOFOptionsEnum.ABORTED, None, None, activity.customer_id,
                                                      activity.module_id)
                        a_data.save()
                        BinCollectionData.objects.filter(activity=activity, status_id = IOFOptionsEnum.UNCOLLECTED).update(status_id=IOFOptionsEnum.ABORT_COLLECTION)
                        if (activity.activity_schedule.end_date is None) or (activity.activity_schedule.end_date <= timezone.now().date()):
                            activity.activity_schedule.schedule_activity_status = Options.objects.get(id=OptionsEnum.INACTIVE)
                            activity.activity_schedule.save()
                        try:
                            HypernetNotification.objects.filter(
                                type_id__in=[IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW,
                                             IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_NO_ACTION_ACCEPT_REJECT,
                                             IOFOptionsEnum.NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_ABORT,
                                             IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_DRIVER_REJECT],
                                activity_id=activity.id,
                                ).update(status_id = OptionsEnum.INACTIVE)
                        except:
                            pass
                        response_body[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: True}
                        http_status = HTTP_SUCCESS_CODE
                        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
                        return generic_response(response_body=response_body, http_status=http_status)
                    
                    elif int(flag) == IOFOptionsEnum.REVIEWED:
                    # Check conflicts
                        act = None
                        try:
                            conflict, current_activity = check_activity_conflicts_review(serializer=serializer,preferences=preferences)
                            if conflict:
                                response_body[RESPONSE_DATA] = TEXT_OPERATION_UNSUCCESSFUL
                                response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                                response_body[RESPONSE_MESSAGE] = ENTITY_OCCUPIED
                                return generic_response(response_body=response_body, http_status=http_status)
                            else:
                                new_timestamp = serializer.get('activity_start_time')
                                if new_timestamp <= (timezone.now() + datetime.timedelta(minutes=preferences.average_activity_time)):
                                    #update activity and send notification to driver
                                    act = update_or_delete_activity(activity, serializer, preferences)
                                else:
                                    #delete activity and create activity queue and leave it at that, cron job will bring it back into cycle when the time comes.
                                    act = update_or_delete_activity(activity, serializer, preferences)
                                if activity.activity_status.id == IOFOptionsEnum.FAILED or activity.activity_status.id == IOFOptionsEnum.CONFLICTING :  # If driver aborts activity, need to change status of bins that werent collected to uncollected.

                                    for obj in serializer.get('action_items').split(','):
                                        bin_data = BinCollectionData.objects.filter(action_item_id=obj)
                                        flag = check_bin_in_activity(activity, bin_data, response_body)
                                        if not flag:
                                            return generic_response(response_body=response_body,
                                                                    http_status=http_status)
                                    # Two for loops, one to check and one to update
                                    for obj in serializer.get('action_items').split(','):
                                        BinCollectionData.objects.filter(activity=activity,
                                                                         status_id=IOFOptionsEnum.ABORT_COLLECTION,
                                                                         action_item_id=obj).update(
                                            status_id=IOFOptionsEnum.UNCOLLECTED, entity=activity.primary_entity,
                                            actor=activity.actor)

                                        if BinCollectionData.objects.filter(action_item_id=obj, activity=activity,
                                                                            status_id=IOFOptionsEnum.UNCOLLECTED).exists():
                                            pass
                                        else:

                                            collection_data = create_bin_collection_data(activity.id,
                                                                                         activity.primary_entity.id,
                                                                                         activity.actor.id,
                                                                                         timezone.now(),
                                                                                         IOFOptionsEnum.UNCOLLECTED,
                                                                                         obj, activity.customer_id,
                                                                                         activity.module_id
                                                                                         )
                                            collection_data.save()


                                    # BinCollectionData.objects.filter(activity=activity, status_id = IOFOptionsEnum.ABORT_COLLECTION).update(status_id=IOFOptionsEnum.FAILED)

                                if act:
                                    act.action_items = serializer.get('action_items')
                                    act.save()
                                    if preferences.enable_accept_reject:
                                        send_notification_to_admin(act.primary_entity.id, act.actor.id,
                                                                   act.id, act,
                                                                   [User.objects.get(
                                                                       associated_entity=act.actor).id],
                                                                   "Accept or reject this activity",
                                                                   IOFOptionsEnum.NOTIFCIATION_DRIVER_ACCEPT_REJECT)

                            # Do not save serializer. NEVER.
                            # serializer.save()
                        except Exception as e:
                            traceback.print_exc()
                            response_body[RESPONSE_DATA] = ENTITY_OCCUPIED
                            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                            return generic_response(response_body=response_body, http_status=http_status)

                    # Handle activity notifications and statuses
                        if activity.activity_status.id in [IOFOptionsEnum.PENDING, IOFOptionsEnum.FAILED, IOFOptionsEnum.REJECTED, IOFOptionsEnum.CONFLICTING] and preferences.enable_accept_reject is False:
                            activity.activity_status_id = IOFOptionsEnum.ACCEPTED
                            activity.notification_sent = False
                            activity.save()
                            a_data = create_activity_data(activity.id, serializer.get('primary_entity').id,
                                                          serializer.get('actor').id, timezone.now(),
                                                          IOFOptionsEnum.REVIEWED, None, None, activity.customer_id,
                                                          activity.module_id)
                            a_data.save()
                        else:
                            activity.activity_status_id = IOFOptionsEnum.REVIEWED
                            activity.save()
                            a_data = create_activity_data(activity.id, serializer.get('primary_entity').id,
                                                          serializer.get('actor').id, timezone.now(),
                                                          IOFOptionsEnum.REVIEWED, None, None, activity.customer_id,
                                                          activity.module_id)
                            a_data.save()

                else:
                    error_list = []
                    for errors in serializer.errors:
                        error_list.append("invalid  " + errors + "  given.")
                    response_body[RESPONSE_MESSAGE] = error_list
                    # print(error_list)
                #TODO: check for type_id in ADMIN_ACTIVITY_REVIEW and ADMIN_ACTIVITY_REVIEW_DRIVER_REJECTS,

                try:
                    HypernetNotification.objects.filter(type_id__in = [IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW,
                                                                    IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_NO_ACTION_ACCEPT_REJECT,
                                                                    IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_DRIVER_REJECT, IOFOptionsEnum.NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_ABORT,
                                                                       IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_NO_ACTION_START_FAIL],
                                                     activity_id = activity.id,
                                                    ).update(status_id = OptionsEnum.INACTIVE)
                except:
                    pass
                response_body[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: True}
                http_status = HTTP_SUCCESS_CODE
                response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE

            else:
                response_body[RESPONSE_DATA] = {TEXT_OPERATION_UNSUCCESSFUL: True}
                response_body[RESPONSE_MESSAGE] = "Activity no longer valid"
                http_status = HTTP_SUCCESS_CODE
                response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
    except:
        traceback.print_exc()
        response_body[RESPONSE_DATA] = {TEXT_OPERATION_UNSUCCESSFUL: True}
        http_status = HTTP_ERROR_CODE
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def shift_reporting(request):
    http_status = HTTP_SUCCESS_CODE
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    customer_id = get_customer_from_request(request, None)
    driver_id = get_default_param(request, 'd_id', None)
    truck_id = get_default_param(request, 't_id', None)
    start_datetime = get_default_param(request, 'start_datetime', None)
    end_datetime = get_default_param(request, 'end_datetime', None)
    
    final_result = []
    if customer_id:
        result = get_shift_data(driver_id, truck_id, customer_id, start_datetime, end_datetime)
        for obj in result:
            final_result.append(obj.as_json(driver_id=driver_id, truck_id=truck_id))
        response_body[RESPONSE_DATA] = final_result
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    else:
        response_body[RESPONSE_DATA] = final_result
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    return generic_response(response_body=response_body, http_status=http_status)



@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def check_invalid_assignments(request):
    http_status = HTTP_SUCCESS_CODE
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    customer_id = get_customer_from_request(request, None)
    result = []
    inner_list = []
    count = 0
    bin_count = 0
    tags = Entity.objects.filter(type_id=DeviceTypeEntityEnum.RFID_TAG, customer_id=customer_id)
    print(tags.count())
    for t in tags:
        dict = {}

        try:
            tag = Assignment.objects.get(child_id=t.id, type_id = DeviceTypeAssignmentEnum.RFID_TAG_ASSIGMENT
                                         , customer_id=customer_id)
            # dict['assigned_tag'] = tag.child.name
            # dict['assigned_bin'] = tag.parent.name
            # dict['single_assignment'] = True
        except Assignment.MultipleObjectsReturned:
            assignments = Assignment.objects.filter(child_id=t.id, type_id = DeviceTypeAssignmentEnum.RFID_TAG_ASSIGMENT
                                                    , customer_id=customer_id)
            # for a in assignments:
            #     if a.child.name != a.parent.name:
            #         try:
            #             a.child = Entity.objects.get(name=a.parent.name, type_id=DeviceTypeEntityEnum.RFID_TAG)
            #             a.save()
            #         except Entity.MultipleObjectsReturned:
            #             print(a.id+ ' ' +a.parent.name)
            #             pass
            #         except:
            #             pass
            dict['assigned_bins'] = list(assignments.values_list('parent__name', 'parent__source_latlong'))
            dict['assigned_tag'] = t.name
            dict['tag_id'] = t.id
            count+=1
            result.append(dict)
        except Assignment.DoesNotExist:
            pass



    bins = Entity.objects.filter(type_id=DeviceTypeEntityEnum.BIN, customer_id=customer_id, status_id=OptionsEnum.ACTIVE)
    print(bins.count())
    for t in bins:
        dict = {}

        try:
            tag = Assignment.objects.get(parent__name=t.name, type_id=DeviceTypeAssignmentEnum.RFID_TAG_ASSIGMENT, status_id=OptionsEnum.ACTIVE)
            # dict['assigned_tag'] = tag.child.name
            # dict['assigned_bin'] = tag.parent.name
            # dict['single_assignment'] = True
        except Assignment.MultipleObjectsReturned:
            assignments = Assignment.objects.filter(parent__name=t.name, type_id=DeviceTypeAssignmentEnum.RFID_TAG_ASSIGMENT)
            # keep_one = assignments[0]
            # assignments.delete()
            # keep_one.save()
            if assignments:
                dict['single_assignment'] = False
            else:
                dict['single_assignment'] = None
            dict['assigned_tags'] = list(assignments.values_list('child__name'))
            dict['assigned_bin'] = t.name +' '+ t.source_latlong
            dict['bin_id'] = t.id

            if dict['assigned_bin']:
                bin_count += 1
            result.append(dict)
        except Assignment.DoesNotExist:
            pass
    result.append({'garbage_assignments': count})
    result.append({'garbage_bin_assignments': bin_count})
    response_body[RESPONSE_DATA] = result
    response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
    response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    return generic_response(response_body=response_body, http_status=http_status)



@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def delete_invalid_assignment(request):
    http_status = HTTP_SUCCESS_CODE
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    #bin_name = get_default_param(request, 'bin_name', None)
    excel_data = []
    ents = Entity.objects.filter(id=8698, type_id=DeviceTypeEntityEnum.BIN)

    for obj in ents:
        if obj.name not in constants.duplicate_bins:
            try:
                tag = Entity.objects.get(name=obj.name, type_id=DeviceTypeEntityEnum.RFID_TAG)
                try:
                    valid_assignment = Assignment.objects.get(child=tag, type_id=DeviceTypeAssignmentEnum.RFID_TAG_ASSIGMENT, parent = obj)
                except:
                    traceback.print_exc()
                    print("Bin not assgined to same tag. Bin name: " + str(obj.name))
                    excel_data.append(obj.name)
                    assgns = Assignment.objects.filter(child=tag, type_id = DeviceTypeAssignmentEnum.RFID_TAG_ASSIGMENT)

                    print("Assignment is:" + str(assgns.values_list('name')))
                    if assgns.count() > 1:
                        continue

                    else:
                        print("Assignment count greater than 1.")
                        assignment = Assignment(
                            name=tag.name + " Assigned to "
                                 + obj.name,
                            child=tag,
                            parent=obj,
                            customer_id=1,
                            module_id=1,
                            type_id=50,
                            status_id=OptionsEnum.ACTIVE,
                            modified_by_id=1,
                        )
                        assignment.save()

                        objs = Assignment.objects.filter(type_id=DeviceTypeAssignmentEnum.RFID_TAG_ASSIGMENT, parent = obj)

                        for i in objs:
                            if i.parent.name != i.child.name:
                                i.delete()

                        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
                        response_body[RESPONSE_STATUS] = "Assignment Added"
            except:
                traceback.print_exc()
                response_body[RESPONSE_MESSAGE] = "Failed"
                response_body[RESPONSE_STATUS] = "Tag doesnot exist"
        else:
            continue

    maintain_excel(excel_data)
    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def migrate_skip_size(request):
    http_status = HTTP_SUCCESS_CODE
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    #bin_name = get_default_param(request, 'bin_name', None)
    duplicates = []
    ents = Entity.objects.filter(type_id=DeviceTypeEntityEnum.BIN)
    try:
        
        for obj in ents:
            if obj.weight == 1.1:
                obj.skip_size = Options.objects.get(id=IOFOptionsEnum.SKIP_SIZE_1)
            elif obj.weight == 2.5:
                obj.skip_size = Options.objects.get(id=IOFOptionsEnum.SKIP_SIZE_2)
            elif obj.weight == 5:
                obj.skip_size = Options.objects.get(id=IOFOptionsEnum.SKIP_SIZE_3)
            elif obj.weight == 8:
                obj.skip_size = Options.objects.get(id=IOFOptionsEnum.SKIP_SIZE_4)
            elif obj.weight == 10:
                obj.skip_size = Options.objects.get(id=IOFOptionsEnum.SKIP_SIZE_5)
            elif obj.weight == 12:
                obj.skip_size = Options.objects.get(id=IOFOptionsEnum.SKIP_SIZE_6)
            elif obj.weight == 14:
                obj.skip_size = Options.objects.get(id=IOFOptionsEnum.SKIP_SIZE_7)
            elif obj.weight == 18:
                obj.skip_size = Options.objects.get(id=IOFOptionsEnum.SKIP_SIZE_8)
            elif obj.weight == 20:
                obj.skip_size = Options.objects.get(id=IOFOptionsEnum.SKIP_SIZE_9)
            elif obj.weight == 26:
                obj.skip_size = Options.objects.get(id=IOFOptionsEnum.SKIP_SIZE_10)
            elif obj.weight == 30:
                obj.skip_size = Options.objects.get(id=IOFOptionsEnum.SKIP_SIZE_11)
            obj.leased_owned = Options.objects.get(id=IOFOptionsEnum.OWNED)
            obj.save()
    except:
        traceback.print_exc()

    ents = Entity.objects.filter(type_id=DeviceTypeEntityEnum.CONTRACT)
    try:
        for obj in ents:
            if obj.weight == 1.1:
                obj.skip_size = Options.objects.get(id=IOFOptionsEnum.SKIP_SIZE_1)
            elif obj.weight == 2.5:
                obj.skip_size = Options.objects.get(id=IOFOptionsEnum.SKIP_SIZE_2)
            elif obj.weight == 5:
                obj.skip_size = Options.objects.get(id=IOFOptionsEnum.SKIP_SIZE_3)
            elif obj.weight == 8:
                obj.skip_size = Options.objects.get(id=IOFOptionsEnum.SKIP_SIZE_4)
            elif obj.weight == 10:
                obj.skip_size = Options.objects.get(id=IOFOptionsEnum.SKIP_SIZE_5)
            elif obj.weight == 12:
                obj.skip_size = Options.objects.get(id=IOFOptionsEnum.SKIP_SIZE_6)
            elif obj.weight == 14:
                obj.skip_size = Options.objects.get(id=IOFOptionsEnum.SKIP_SIZE_7)
            elif obj.weight == 18:
                obj.skip_size = Options.objects.get(id=IOFOptionsEnum.SKIP_SIZE_8)
            elif obj.weight == 20:
                obj.skip_size = Options.objects.get(id=IOFOptionsEnum.SKIP_SIZE_9)
            elif obj.weight == 26:
                obj.skip_size = Options.objects.get(id=IOFOptionsEnum.SKIP_SIZE_10)
            elif obj.weight == 30:
                obj.skip_size = Options.objects.get(id=IOFOptionsEnum.SKIP_SIZE_11)
            obj.save()
    except:
        traceback.print_exc()
    return generic_response(response_body=response_body, http_status=http_status)



@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def delete_invalid_assignments_by_tag(request):
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    tag_name = get_default_param(request, 'tag_name', None)

    try:
        tag = Entity.objects.get(type_id=DeviceTypeEntityEnum.RFID_TAG, name=tag_name)
        try:
            bin = Entity.objects.get(name=tag.name, type_id=DeviceTypeEntityEnum.BIN)
            try:
                valid_assignment = Assignment.objects.get(child__name=tag.name, parent__name= bin.name, type_id=50)
                if valid_assignment:
                    all_assignments = Assignment.objects.filter(child__name = tag.name, type_id=50)
                    for obj in all_assignments:
                        if obj.child.name != obj.parent.name:
                            obj.delete()
            except:
                valid_assignment=None
        except:
            bin = None
    except:
        tag=None


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def check_tags_without_bins(request):
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    tags = 0
    free = 0

    tags = Entity.objects.filter(type_id=47)
    bins = Entity.objects.filter(type_id=21).count()

    for t in tags:
        assignment = Assignment.objects.filter(child=t,type_id=DeviceTypeAssignmentEnum.RFID_TAG_ASSIGMENT)
        if not assignment:
            free+=1

    print('Free tags', free)
    print('Total Tags: ',tags.count())

    
@api_view(['GET'])
@permission_classes((AllowAny,))
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_tag_from_name(request):
    response_body = {RESPONSE_MESSAGE: TEXT_OPERATION_SUCCESSFUL, RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
    tag_name = get_default_param(request, 'tag_name', None)
    http_status = HTTP_SUCCESS_CODE
    try:
        tag = Entity.objects.get(type_id=DeviceTypeEntityEnum.RFID_TAG, name=tag_name)
        try:
            bin = Assignment.objects.get(child=tag, status_id=OptionsEnum.ACTIVE, type_id=DeviceTypeAssignmentEnum.RFID_TAG_ASSIGMENT).parent
            try:
                obj = BinSerializer(bin, context={'request': request})
                response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
                response_body[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: True, 'data': obj.data}
                
            except:
                response_body[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
                response_body[RESPONSE_MESSAGE] = DEFAULT_ERROR_MESSAGE
                response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
        except:
            response_body[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
            response_body[RESPONSE_MESSAGE] = RFID_NOT_WITH_ASSET
            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
    except:
        response_body[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
        response_body[RESPONSE_MESSAGE] = RFID_TAG_CARD_DOES_NOT_EXIST
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def construct_clean_assignments(request):
    #response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}

    bins = Entity.objects.filter(type_id=DeviceTypeEntityEnum.BIN)
    for b in bins:
        try:
            bin = Entity.objects.get(name=b.name, type_id=DeviceTypeEntityEnum.BIN)
            try:
                tag = Entity.objects.get(name=bin.name, type_id=DeviceTypeEntityEnum.RFID_TAG)
                try:
                    Assignment.objects.get(parent=bin, child=tag,
                                           type_id=DeviceTypeAssignmentEnum.RFID_TAG_ASSIGMENT)
                except:
                    assignment = parent_child_assignment(bin, tag,
                                                         DeviceTypeAssignmentEnum.RFID_TAG_ASSIGMENT)
                    assignment.save()
            except:
                print (traceback.print_exc())
                pass
        except:
            bins = Entity.objects.filter(name=b.name, type_id=DeviceTypeEntityEnum.BIN)
            if bins.count() > 1:
                bins = bins.order_by('created_datetime')
                clean_bin = bins[0]

                bins = bins.exclude(id=clean_bin.id)

                bins.delete()
                try:
                    tag = Entity.objects.get(name=clean_bin.name, type_id=DeviceTypeEntityEnum.RFID_TAG)
                    try:
                        Assignment.objects.get(parent=clean_bin, child=tag,
                                               type_id=DeviceTypeAssignmentEnum.RFID_TAG_ASSIGMENT)
                    except:
                        assignment = parent_child_assignment(clean_bin, tag,
                                                             DeviceTypeAssignmentEnum.RFID_TAG_ASSIGMENT)
                        assignment.save()
                except:
                    print(traceback.print_exc())
                    pass
            else:
                pass


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def vehicle_summary(request):
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    data_points = dict()
    customer_id = get_customer_from_request(request, None)
    start_datetime = get_default_param(request, 'start_datetime', None)
    end_datetime = get_default_param(request, 'end_datetime', None)
    truck_id = get_default_param(request, 'truck_id', None)

    http_status = HTTP_SUCCESS_CODE
    if customer_id:
        if start_datetime and end_datetime:
            start_datetime = parse(start_datetime)
            end_datetime = parse(end_datetime)

        queryset = create_queryset_post_data(customer_id, None, truck_id, None, start_datetime, end_datetime).order_by(
            'timestamp').aggregate(Sum('volume_consumed'), Sum('distance_travelled'))
        data_points['volume_consumed'] = 0
        data_points['distance_travelled'] = 0

        if queryset['volume_consumed__sum'] is None:
            queryset['volume_consumed__sum'] = 0
        data_points['volume_consumed'] = float(queryset['volume_consumed__sum'])

        if queryset['distance_travelled__sum'] is None:
            queryset['distance_travelled__sum'] = 0
        data_points['distance_travelled'] = float(queryset['distance_travelled__sum'])
        
        activities = util_get_activities(customer_id, truck_id, None, None, None, None, start_datetime, end_datetime)
        data_points['activities_completed'] = activities.count()
        
        response_body[RESPONSE_DATA] = data_points
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
    else:
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_UNSUCCESSFUL
    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def maintenance_of_entity(request):
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    final_result = []
    customer_id = get_customer_from_request(request, None)
    start_datetime = get_default_param(request, 'start_datetime', None)
    end_datetime = get_default_param(request, 'end_datetime', None)
    truck_id = get_default_param(request, 'truck_id', None)
    driver_id = get_default_param(request, 'driver_id', None)
    maintenance_id = get_default_param(request, 'maintenance_id', None)
    type_id = get_default_param(request, 'type_id', None)

    http_status = HTTP_SUCCESS_CODE
    if customer_id:
        if start_datetime and end_datetime:
            start_datetime = parse(start_datetime)
            end_datetime = parse(end_datetime)

        queryset = create_queryset_maintenance(customer_id, maintenance_id, truck_id, driver_id, type_id, start_datetime, end_datetime)
        for obj in queryset:
            final_result.append(LogisticMaintenanceSerializer(obj, context={'request': request}).data)
        response_body[RESPONSE_DATA] = final_result
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
    else:
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_UNSUCCESSFUL
    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def maintenance_data_of_entity(request):
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    final_result = []
    customer_id = get_customer_from_request(request, None)
    start_datetime = get_default_param(request, 'start_datetime', None)
    end_datetime = get_default_param(request, 'end_datetime', None)
    truck_id = get_default_param(request, 'truck_id', None)
    driver_id = get_default_param(request, 'driver_id', None)
    maintenance_id = get_default_param(request, 'maintenance_id', None)
    type_id = get_default_param(request, 'type_id', None)

    http_status = HTTP_SUCCESS_CODE
    if customer_id:
        if start_datetime and end_datetime:
            start_datetime = parse(start_datetime)
            end_datetime = parse(end_datetime)

        queryset = create_queryset_maintenance_data(customer_id, maintenance_id, truck_id, driver_id, type_id, start_datetime, end_datetime)
        for obj in queryset:
            final_result.append(LogisticMaintenanceDataSerializer(obj, context={'request': request}).data)
        response_body[RESPONSE_DATA] = final_result
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
    else:
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_UNSUCCESSFUL
    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def truck_reporting_cms(request):
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    final_result = []
    customer_id = get_customer_from_request(request, None)
    start_datetime = get_default_param(request, 'start_datetime', None)
    end_datetime = get_default_param(request, 'end_datetime', None)
    truck_id = get_default_param(request, 'truck_id', None)
    supervisor_id = get_default_param(request, 'supervisor', None)
    office = get_default_param(request, 'office', None)
    destination_location = get_default_param(request, 'destination_location', None)
    source_location = get_default_param(request, 'source_location', None)
    wheels = get_default_param(request, 'wheels', None)
    summary = int(get_default_param(request, 'summary', 0))


    http_status = HTTP_SUCCESS_CODE
    if customer_id:
        if start_datetime and end_datetime:
            start_datetime = parse(start_datetime)
            end_datetime = parse(end_datetime)

        queryset = create_queryset_cms_truck_data(customer_id, truck_id, destination_location, source_location, wheels, office,
                                                  supervisor_id, start_datetime, end_datetime)
        if summary == 0:
            for obj in queryset:
                final_result.append(CMSVehicleReportingSerializer(obj, context={'request': request}).data)
        else:
            trucks = queryset.values_list("vehicle_id", flat=True).distinct()
            for t in trucks:
                result = dict()
                data = create_queryset_cms_truck_data(customer_id, t, destination_location, source_location, wheels, office,
                                           supervisor_id, start_datetime, end_datetime)
                result['vehicle'] = Entity.objects.get(id=t).name
                result['distance_loaded'] = data.aggregate(Sum('km_loaded'))['km_loaded__sum'] or 0
                result['distance_unloaded'] = data.aggregate(Sum('km_unloaded'))['km_unloaded__sum'] or 0
                result['total_distance'] = result['distance_unloaded'] + result['distance_loaded']
                result['workshop_duration'] = data.filter(loading_location__name='Workshop').count()

                result['stops_loaded_duration'] = data.aggregate(Sum('stops_loaded_duration'))['stops_loaded_duration__sum'] or 0
                result['stops_unloaded_duration'] = data.aggregate(Sum('stops_unloading_duration'))['stops_unloading_duration__sum'] or 0
                result['stops_duration'] = result['stops_unloaded_duration'] + result['stops_loaded_duration']

                # unique_load_times = data.distinct('trip_start_datetime', 'loaded_datetime')
                final_result.append(result)
            pass
        response_body[RESPONSE_DATA] = final_result
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
    else:
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_UNSUCCESSFUL
    return generic_response(response_body=response_body, http_status=http_status)