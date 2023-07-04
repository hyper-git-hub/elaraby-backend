import calendar
import json
import datetime
from datetime import timedelta, datetime, time, timezone
from pathlib import Path

from django.db.models import F, Count, Max, Q, TimeField
from django.db.models.functions import TruncDay, TruncMinute
from django.utils import timezone
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER

from backend import settings
from hypernet.models import UserEntityAssignment, Devices, HypernetPostData, Assignment
from hypernet.notifications.utils import send_notification_violations
from iof.models import ActivitySchedule, ActivityQueue, Activity
from rest_framework.decorators import api_view, permission_classes, authentication_classes
import hypernet.constants as const
import hypernet.utils as h_utils
import iop.utils as iop_utils
from hypernet.enums import OptionsEnum, IopOptionsEnums, DeviceTypeEntityEnum, DeviceTypeAssignmentEnum
from django.db.models import Avg
from dateutil.parser import parse
import traceback
from hypernet.models import CustomerDevice, Entity
from hypernet.serializers import HomeAppliancesSerializer
from options.models import Options
from hypernet.serializers import HomeAppliancesSerializer, ApplianceQRSerializer
from iop.models import ApplianceQR, IopAggregation, EnergyConsumption, ErrorLogs
from iof.models import LogisticAggregations
from hypernet.enums import ModuleEnum
from rest_framework.permissions import AllowAny
from user.models import User
import os
from django.db.models import F


@api_view(['GET'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def get_iop_devices_count_cards(request):
    customer = h_utils.get_customer_from_request(request, None)
    dev_type_id = h_utils.get_default_param(request, 'device_type', None)
    model_id = h_utils.get_default_param(request, 'model_id', None)

    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.STATUS_ERROR,
                     const.RESPONSE_DATA: []}
    http_status = const.HTTP_SUCCESS_CODE

    if customer:
        data = iop_utils.get_iop_devices_count(c_id=customer)

        response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
        response_body[const.RESPONSE_DATA] = list(data)

    else:
        response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_PARAMS_MISSING

    return h_utils.generic_response(response_body, http_status)


@api_view(['GET'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def get_iop_devices_count(request):
    customer = h_utils.get_customer_from_request(request, None)
    dev_type_id = h_utils.get_default_param(request, 'device_type', None)
    model_id = h_utils.get_default_param(request, 'model_id', None)

    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.STATUS_ERROR,
                     const.RESPONSE_DATA: []}
    http_status = const.HTTP_SUCCESS_CODE

    if customer:
        data = iop_utils.get_iop_devices(c_id=customer, mod_id=model_id, t_id=dev_type_id)

        data = data.values(
            'id',
            'name',
            sold=F('obd2_compliant'),
            model_name=F('leased_owned__label'),
            model_id=F('leased_owned'),
            device_type_id=F('entity_sub_type_id'),
            device_type_name=F('entity_sub_type__label'),
        )

        response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
        response_body[const.RESPONSE_DATA] = list(data)

    else:
        response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_PARAMS_MISSING

    return h_utils.generic_response(response_body, http_status)


@api_view(['GET'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def get_iop_devices_sold_stats(request):
    customer = h_utils.get_customer_from_request(request, None)
    dev_type_id = h_utils.get_default_param(request, 'device_type', None)
    model_id = h_utils.get_default_param(request, 'model_id', None)

    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.STATUS_ERROR,
                     const.RESPONSE_DATA: []}
    http_status = const.HTTP_SUCCESS_CODE

    if customer:
        data = iop_utils.get_sold_stats(c_id=customer)

        response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
        response_body[const.RESPONSE_DATA] = data

    else:
        response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_PARAMS_MISSING

    return h_utils.generic_response(response_body, http_status)


@api_view(['GET'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def get_device_error_logs(request):
    customer = h_utils.get_customer_from_request(request, None)
    dev_type_id = h_utils.get_default_param(request, 'device_type', None)
    entity_id = h_utils.get_default_param(request, 'entity_id', None)
    model_id = h_utils.get_default_param(request, 'model_id', None)
    start_date = h_utils.get_default_param(request, 'start_date', None)
    end_date = h_utils.get_default_param(request, 'end_date', None)
    err_type = h_utils.get_default_param(request, 'err_id', None)
    days = int(h_utils.get_default_param(request, 'days', 0))

    if days > 0:
        this_start_date = timezone.now() - timedelta(days=days)

    else:
        this_start_date = start_date

    print(this_start_date, 'error logs')

    data = []

    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.STATUS_ERROR,
                     const.RESPONSE_DATA: []}
    http_status = const.HTTP_SUCCESS_CODE

    if customer:
        err_data = iop_utils.new_get_error_logs(c_id=customer, e_id=entity_id,
                                                mod_id=model_id, dev_type_id=dev_type_id,
                                                err_code=err_type, s_date=this_start_date, e_date=timezone.now())

        if err_data:
            data = err_data.values('id', 'datetime','err_datetime' ,'date', 'inactive_score', 'device_id', 'device__name',
                                   'device__leased_owned__label', 'device__device_name__device_id')

        response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
        response_body[const.RESPONSE_DATA] = list(data)

    else:
        response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_PARAMS_MISSING

    return h_utils.generic_response(response_body, http_status)


@api_view(['GET'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def get_device_sold_stats_graph(request):
    customer = h_utils.get_customer_from_request(request, None)
    dev_type_id = h_utils.get_default_param(request, 'device_type', None)
    entity_id = h_utils.get_default_param(request, 'entity_id', None)
    model_id = h_utils.get_default_param(request, 'model_id', None)
    start_date = h_utils.get_default_param(request, 'start_date', None)
    end_date = h_utils.get_default_param(request, 'end_date', None)
    err_type = h_utils.get_default_param(request, 'err_id', None)

    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.STATUS_ERROR,
                     const.RESPONSE_DATA: []}
    http_status = const.HTTP_SUCCESS_CODE

    if customer:
        sold_data = iop_utils.sold_devices_iop(c_id=customer, s_date=start_date, e_date=end_date)
        data = sold_data.values('entity_sub_type__label', 'entity_sub_type_id', device_count=Count('entity_sub_type'))
        response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
        response_body[const.RESPONSE_DATA] = list(data)

    else:
        response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_PARAMS_MISSING

    return h_utils.generic_response(response_body, http_status)


@api_view(['GET'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def graph_data_energy_active_duration(request):
    customer = h_utils.get_customer_from_request(request, None)
    dev_type_id = h_utils.get_default_param(request, 'device_type', None)
    entity_id = h_utils.get_default_param(request, 'entity_id', None)
    model_id = h_utils.get_default_param(request, 'model_id', None)
    start_date = h_utils.get_default_param(request, 'start_date', None)
    end_date = h_utils.get_default_param(request, 'end_date', None)
    data_type = h_utils.get_default_param(request, 'data_type', None)

    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.STATUS_ERROR,
                     const.RESPONSE_DATA: []}
    http_status = const.HTTP_SUCCESS_CODE

    if customer:
        graph_data = iop_utils.util_usage_graph_data(customer, entity_id, data_type, s_date=start_date, e_date=end_date)

        response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
        response_body[const.RESPONSE_DATA] = graph_data

    else:
        response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_PARAMS_MISSING

    return h_utils.generic_response(response_body, http_status)


@api_view(['GET'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def new_graph_data_energy_active_duration(request):
    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.STATUS_ERROR,
                        const.RESPONSE_DATA: []}
    http_status = const.HTTP_SUCCESS_CODE
    try:
        customer = h_utils.get_customer_from_request(request, None)
        dev_type_id = h_utils.get_default_param(request, 'device_type', None)
        entity_id = h_utils.get_default_param(request, 'entity_id', None)
        model_id = h_utils.get_default_param(request, 'model_id', None)
        start_date = h_utils.get_default_param(request, 'start_date', None)
        end_date = h_utils.get_default_param(request, 'end_date', None)

        
            
        # time='19:00:00'
            
        # start_date_data = datetime.strptime(start_date, '%Y-%m-%d').date() - timedelta(1)
        # start_time = datetime.strptime(time, "%H:%M:%S").time()
        
        # start_date=datetime.combine(start_date_data, start_time)
        
       
        
        
        # time='18:59:59'
            
        # end_date_data = datetime.strptime(end_date, '%Y-%m-%d').date()
        # end_time = datetime.strptime(time, "%H:%M:%S").time()
        
        # end_date=datetime.combine(end_date_data, end_time)
        # print(start_date,'time jasndjk',end_date)
        
        data_type = h_utils.get_default_param(request, 'data_type', None)
        breakdown = request.GET.get("breakdown", None)
        print("BREAKDOWN = ", breakdown)
        response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.STATUS_ERROR,
                        const.RESPONSE_DATA: []}
        http_status = const.HTTP_SUCCESS_CODE

        if customer:
            graph_data = iop_utils.new_energy_usage_data(customer, entity_id, breakdown, data_type, s_date=start_date, e_date=end_date)

            # print(graph_data[len(graph_data) -1])

            response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
            response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
            response_body[const.RESPONSE_DATA] = graph_data

        else:
            response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
            response_body[const.RESPONSE_MESSAGE] = const.TEXT_PARAMS_MISSING

        return h_utils.generic_response(response_body, http_status)
    except Exception as e:
        print(e)
        return h_utils.generic_response(response_body, http_status)

@api_view(['GET'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def get_device_listing_by_type(request):
    customer = h_utils.get_customer_from_request(request, None)
    dev_type_id = h_utils.get_default_param(request, 'device_type', None)
    entity_id = h_utils.get_default_param(request, 'entity_id', None)
    model_id = h_utils.get_default_param(request, 'model_id', None)
    start_date = h_utils.get_default_param(request, 'start_date', None)
    end_date = h_utils.get_default_param(request, 'end_date', None)
    err_type = h_utils.get_default_param(request, 'err_id', None)
    ind_a = int(h_utils.get_default_param(request, 'index_a', 0))
    ind_b = int(h_utils.get_default_param(request, 'index_b', 10))
    search = h_utils.get_default_param(request, 'searchText', None)

    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.STATUS_ERROR,
                     const.RESPONSE_DATA: []}
    http_status = const.HTTP_SUCCESS_CODE

    if customer:
        devices_list, count, online_device_count = iop_utils.util_get_device_sub_type_listing(c_id=customer, sub_type_id=dev_type_id,
                                                                         mod_id=model_id, index_a=ind_a, index_b=ind_b,search=search,request=request)

        response_body['count'] = count
        print(online_device_count,'online count device')
        response_body['online_device_count'] = online_device_count
        response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
        response_body[const.RESPONSE_DATA] = devices_list

    else:
        response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_PARAMS_MISSING
    print("here for response")
    return h_utils.generic_response(response_body, http_status)


@api_view(['GET'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def get_device_usage_stats(request):
    customer = h_utils.get_customer_from_request(request, None)
    dev_type_id = h_utils.get_default_param(request, 'device_type', None)
    entity_id = h_utils.get_default_param(request, 'entity_id', None)
    model_id = h_utils.get_default_param(request, 'model_id', None)
    start_date = h_utils.get_default_param(request, 'start_date', None)
    end_date = h_utils.get_default_param(request, 'end_date', None)
    err_type = h_utils.get_default_param(request, 'err_id', None)

    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.STATUS_ERROR,
                     const.RESPONSE_DATA: []}
    http_status = const.HTTP_SUCCESS_CODE

    if customer:
        device_usage_data = iop_utils.util_get_device_usage_stats_average(c_id=customer, e_id=entity_id)
        print(device_usage_data,'asdasdasd')
        if len(device_usage_data)==0:
            print('hasjdjasdjnasjndj')
            response_body[const.RESPONSE_STATUS] = const.HTTP_ERROR_CODE
            response_body[const.RESPONSE_MESSAGE] = const.TEXT_PARAMS_MISSING
            response_body[const.RESPONSE_DATA] = device_usage_data
            return h_utils.generic_response(response_body, http_status)
            
        response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
        response_body[const.RESPONSE_DATA] = device_usage_data

    else:
        response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_PARAMS_MISSING

    return h_utils.generic_response(response_body, http_status)


@api_view(['GET'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def error_occuring_model(request):
    customer = h_utils.get_customer_from_request(request, None)
    sub_type = h_utils.get_default_param(request, 'sub_type', None)
    days = int(h_utils.get_default_param(request, 'days', 0))
    start_date = h_utils.get_default_param(request, 'start_date', None)
    end_date = h_utils.get_default_param(request, 'end_date', None)

    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.STATUS_ERROR,
                     const.RESPONSE_DATA: []}
    http_status = const.HTTP_SUCCESS_CODE

    if days > 0:
        this_start_date = timezone.now() - timedelta(days=days)
        last_start_date = this_start_date - timedelta(days=days)

    else:
        this_start_date = timezone.now().date()
        last_start_date = timezone.now().replace(hour=0, minute=0, second=0)

    # if days > 0:
    #     this_start_date = timezone.now() - timedelta(days=days)
    #     last_start_date = this_start_date - timedelta(days=days)
    #
    # else:
    #     this_start_date = start_date
    #     last_start_date = end_date
    result = {}
    if customer:
        devices = iop_utils.get_iop_devices(customer, t_id=None, mod_id=None)

        result['total_devices'] = devices.count()
        result['active_devices'] = devices.filter(status_id=OptionsEnum.ACTIVE).count()
        result['inactive_devices'] = devices.filter(status_id=OptionsEnum.INACTIVE).count()

        device_errors = iop_utils.util_get_error_logs(c_id=customer, e_id=None, mod_id=None, dev_type_id=sub_type,
                                                      s_date=this_start_date, e_date=timezone.now())
        error_prone_device = device_errors.values('device__name').annotate(count=Count('inactive_score')).values(
            'count', 'device__leased_owned__label').order_by('-count')

        last_error_prone_devices = iop_utils.util_get_error_logs(c_id=customer, e_id=None, mod_id=None,
                                                                 dev_type_id=sub_type, s_date=last_start_date,
                                                                 e_date=this_start_date)
        last_error_prone_devices = last_error_prone_devices.values('device__name').annotate(
            count=Count('inactive_score')).values('count', 'device__leased_owned__label').order_by('-count')

        error_prone_device = error_prone_device.first()
        result['error_prone_device'] = error_prone_device.get(
            'device__leased_owned__label') if error_prone_device else None
        result['error_prone_device_errors'] = error_prone_device.get('count') if error_prone_device else 0

        last_error_prone_devices = last_error_prone_devices.first()
        result['last_error_prone_device'] = last_error_prone_devices.get(
            'device__leased_owned__label') if last_error_prone_devices else None
        result['last_error_prone_device_errors'] = last_error_prone_devices.get(
            'count') if last_error_prone_devices else 0

        response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
        response_body[const.RESPONSE_DATA] = result

        # elif last_error_prone_devices.count() == 0 and error_prone_device.count() == 0:
        #     response_body[const.RESPONSE_MESSAGE] = 'No data to display'
        #     response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
        #     response_body[const.RESPONSE_DATA] = ''

    return h_utils.generic_response(response_body, http_status)


@api_view(['GET'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def most_sold_model(request):
    customer = h_utils.get_customer_from_request(request, None)
    sub_type = h_utils.get_default_param(request, 'sub_type', None)

    days = int(h_utils.get_default_param(request, 'days', 0))
    start_date = h_utils.get_default_param(request, 'start_date', None)
    end_date = h_utils.get_default_param(request, 'end_date', None)

    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.STATUS_ERROR,
                     const.RESPONSE_DATA: []}
    http_status = const.HTTP_SUCCESS_CODE

    if days > 0:
        this_start_date = timezone.now() - timedelta(days=days)
        last_start_date = this_start_date - timedelta(days=days)

    else:
        this_start_date = timezone.now().date()
        last_start_date = timezone.now().replace(hour=0, minute=0, second=0)

    result = {}
    if customer:
        devices = iop_utils.get_iop_devices(customer, t_id=None, mod_id=None, s_date=this_start_date,
                                            e_date=timezone.now())
        sold_models = devices.filter(obd2_compliant=True).values('leased_owned').annotate(
            count=Count('leased_owned')).values('leased_owned__label', 'count').order_by('-count')

        last_sold_models = iop_utils.get_iop_devices(customer, t_id=None, mod_id=None, s_date=last_start_date,
                                                     e_date=this_start_date)
        last_sold_models = last_sold_models.filter(obd2_compliant=True).values('leased_owned').annotate(
            count=Count('leased_owned')).values('leased_owned__label', 'count').order_by('-count')

        sold_models = sold_models.first()
        result['most_sold_model'] = sold_models['leased_owned__label'] if sold_models else None
        result['sold_model_count'] = sold_models['count'] if sold_models else None
        # response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
        # response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
        # response_body[const.RESPONSE_DATA] = result

        last_sold_models = last_sold_models.first()
        result['last_most_sold_model'] = last_sold_models['leased_owned__label'] if last_sold_models else None
        result['last_sold_model_count'] = last_sold_models['count'] if last_sold_models else None
        response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
        response_body[const.RESPONSE_DATA] = result

    else:
        response_body[const.RESPONSE_STATUS] = const.HTTP_ERROR_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_UNSUCCESSFUL

    return h_utils.generic_response(response_body, http_status)


@api_view(['GET'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def avg_errors_all_devices(request):
    customer = h_utils.get_customer_from_request(request, None)
    sub_type = h_utils.get_default_param(request, 'sub_type', None)
    days = int(h_utils.get_default_param(request, 'days', 0))
    start_date = h_utils.get_default_param(request, 'start_date', None)
    end_date = h_utils.get_default_param(request, 'end_date', None)

    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.STATUS_ERROR,
                     const.RESPONSE_DATA: []}
    http_status = const.HTTP_SUCCESS_CODE

    if days > 0:
        this_start_date = timezone.now() - timedelta(days=days)
        last_start_date = this_start_date - timedelta(days=days)

    else:
        this_start_date = timezone.now().date()
        last_start_date = timezone.now().replace(hour=0, minute=0, second=0)
    #
    # if days > 0:
    #     this_start_date = timezone.now() - timedelta(days=days)
    #     last_start_date = this_start_date - timedelta(days=days)
    #
    # else:
    #     this_start_date = start_date
    #     last_start_date = end_date

    result = {}
    if customer:
        device_errors = iop_utils.util_get_error_logs(c_id=customer, e_id=None, mod_id=None, dev_type_id=sub_type,
                                                      s_date=this_start_date, e_date=timezone.now())
        last_device_errors = iop_utils.util_get_error_logs(c_id=customer, e_id=None, mod_id=None, dev_type_id=sub_type,
                                                           s_date=last_start_date, e_date=this_start_date)

        total_errors = device_errors.count()
        total_devices_with_error = device_errors.values('device').annotate(count=Count('device'))
        total_devices_with_error = total_devices_with_error[0]['count'] if total_devices_with_error.count() > 0 else 0
        if total_devices_with_error > 0 and total_errors > 0:
            this_date_avg = total_errors / total_devices_with_error
        else:
            this_date_avg = 0

        last_total_errors = last_device_errors.count()
        last_total_devices_with_error = last_device_errors.values('device').annotate(count=Count('device'))
        last_total_devices_with_error = last_total_devices_with_error[0][
            'count'] if last_total_devices_with_error.count() > 0 else 0
        if last_total_devices_with_error > 0 or last_total_errors > 0:
            last_date_avg = last_total_errors / last_total_devices_with_error
        else:
            last_date_avg = 0

        result['this_date'] = round(this_date_avg)
        result['last_date'] = round(last_date_avg)

        # print('avg: ', this_date_avg)
        # print('last avg: ', last_date_avg)
        # print('this date count: ', device_errors.count())
        # print('last date count: ', last_device_errors.count())

        response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
        response_body[const.RESPONSE_DATA] = result

    else:
        response_body[const.RESPONSE_STATUS] = const.HTTP_ERROR_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_UNSUCCESSFUL
    return h_utils.generic_response(response_body, http_status)


@api_view(['GET'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def avg_energy_all_devices(request):
    customer = h_utils.get_customer_from_request(request, None)
    sub_type = h_utils.get_default_param(request, 'sub_type', None)
    ent_id = h_utils.get_default_param(request, 'entity_id', None)

    days = int(h_utils.get_default_param(request, 'days', 0))
    start_date = h_utils.get_default_param(request, 'start_date', None)
    end_date = h_utils.get_default_param(request, 'end_date', None)

    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.STATUS_ERROR,
                     const.RESPONSE_DATA: {}}
    http_status = const.HTTP_SUCCESS_CODE

    if days > 0:
        this_start_date = timezone.now() - timedelta(days=days)
        last_start_date = this_start_date - timedelta(days=days)

    else:
        this_start_date = timezone.now().date()
        last_start_date = timezone.now().replace(hour=0, minute=0, second=0)

    # if days > 0:
    #     this_start_date = timezone.now() - timedelta(days=days)
    #     last_start_date = this_start_date - timedelta(days=days)
    #
    # else:
    #     this_start_date = start_date
    #     last_start_date = end_date

    if customer:
        avg_stats = iop_utils.new_util_get_usage_stats(c_id=customer, e_id=ent_id, s_date=this_start_date,
                                                       e_date=timezone.now())
        last_avg_stats = iop_utils.new_util_get_usage_stats(c_id=customer, e_id=ent_id, s_date=last_start_date,
                                                            e_date=this_start_date)

        avg_energy_consumed = avg_stats.aggregate(avg=Avg('active_duration'))
        last_avg_energy_consumed = last_avg_stats.aggregate(avg=Avg('active_duration'))

        response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
        response_body[const.RESPONSE_DATA]['current_value'] = avg_energy_consumed['avg']
        response_body[const.RESPONSE_DATA]['last_value'] = last_avg_energy_consumed['avg']

    else:
        response_body[const.RESPONSE_STATUS] = const.HTTP_ERROR_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_UNSUCCESSFUL

    return h_utils.generic_response(response_body, http_status)


@api_view(['GET'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def latest_data_iop_device(request):
    customer = h_utils.get_customer_from_request(request, None)
    device_id = h_utils.get_default_param(request, 'device', None)

    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.STATUS_ERROR,
                     const.RESPONSE_DATA: {}}
    http_status = const.HTTP_SUCCESS_CODE

    if customer:
        latest_data = iop_utils.util_get_device_latest_data(c_id=customer, d_id=device_id)

        response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
        response_body[const.RESPONSE_DATA] = latest_data

    else:
        response_body[const.RESPONSE_STATUS] = const.HTTP_ERROR_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_UNSUCCESSFUL

    return h_utils.generic_response(response_body, http_status)


@api_view(['GET'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def get_sharing_code(request):
    customer = h_utils.get_customer_from_request(request, None)
    device_id = int(h_utils.get_default_param(request, 'device', 0))

    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.STATUS_ERROR,
                     const.RESPONSE_DATA: {}}
    http_status = const.HTTP_SUCCESS_CODE

    if customer:
        sharing_code = iop_utils.util_generate_sharing_code(d_id=device_id)
        if sharing_code:
            response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
            response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
            response_body[const.RESPONSE_DATA] = sharing_code
        else:
            response_body[const.RESPONSE_STATUS] = const.HTTP_ERROR_CODE
            response_body[const.RESPONSE_MESSAGE] = const.TEXT_DOES_NOT_EXISTS
    else:
        response_body[const.RESPONSE_STATUS] = const.HTTP_ERROR_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_PARAMS_MISSING

    return h_utils.generic_response(response_body, http_status)


@api_view(['GET'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def assigne_device_with_sharing_code(request):
    customer = h_utils.get_customer_from_request(request, None)
    usr = h_utils.get_user_from_request(request, None)
    sharing_code = h_utils.get_default_param(request, 'code', None)

    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.STATUS_ERROR,
                     const.RESPONSE_DATA: {}}
    http_status = const.HTTP_SUCCESS_CODE

    if customer:
        flag = iop_utils.util_use_sharing_code(sh_code=sharing_code, usr=usr)
        if flag:
            response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
            response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
            response_body[const.RESPONSE_DATA] = flag
        else:
            response_body[const.RESPONSE_STATUS] = const.HTTP_ERROR_CODE
            response_body[const.RESPONSE_MESSAGE] = const.TEXT_DOES_NOT_EXISTS
    else:
        response_body[const.RESPONSE_STATUS] = const.HTTP_ERROR_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_PARAMS_MISSING

    return h_utils.generic_response(response_body, http_status)


@api_view(['POST'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def manage_device_user_previliges(request):
    customer = h_utils.get_customer_from_request(request, None)
    # usr = h_utils.get_user_from_request(request, None)
    privilege_data = h_utils.get_data_param(request, 'data', None)

    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.STATUS_ERROR,
                     const.RESPONSE_DATA: {}}
    http_status = const.HTTP_SUCCESS_CODE
    # json_data = json.loads(privilege_data)

    if customer:
        updated_usrs, un_updated_usrs = iop_utils.manage_user_device_previliges(js_data=privilege_data)

        response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
        response_body[const.RESPONSE_DATA]['updated_devices'] = updated_usrs
        response_body[const.RESPONSE_DATA]['un_updated_devices'] = un_updated_usrs
    else:
        response_body[const.RESPONSE_STATUS] = const.HTTP_ERROR_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_PARAMS_MISSING

    return h_utils.generic_response(response_body, http_status)


@api_view(['POST'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def generate_qr_code(request):
    customer = h_utils.get_customer_from_request(request, None)
    # ssids = h_utils.get_data_param(request, 'ssid', None)
    # passwords = h_utils.get_data_param(request, 'password', None)
    # device_ids = h_utils.get_data_param(request, 'device_id', None)
    appliances = h_utils.get_data_param(request, 'appliances', None)
    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.STATUS_ERROR,
                     const.RESPONSE_DATA: {}}
    http_status = const.HTTP_SUCCESS_CODE

    if customer:
        response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL

        # if len(ssids) > 1:
        if len(appliances) > 1:
            now = datetime.now()
            file_name = "QR Codes " + str(now.date())
        else:
            # file_name = ssids[0] + "-QR Code"
            file_name = appliances[0]['ssid'] + "-QR Code"

        data_folder = Path(settings.MEDIA_ROOT + "/reports/")
        print(data_folder,'path')
        if not data_folder.exists():
            os.mkdir(data_folder)
        file_loc = "./media/reports/" + file_name + '.pdf'
        file_loc_server = "/media/reports/" + file_name + '.pdf'

        if os.path.exists(file_loc):
            os.remove(file_loc)

        generate_pdf(file_name=file_loc, appliances=appliances)
        file_url = (request.get_host() + file_loc_server)
        response_body[const.RESPONSE_DATA] = {'file': file_url}
        response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
        response_body[const.RESPONSE_MESSAGE] = "Report generated successfully"
    else:
        response_body[const.RESPONSE_STATUS] = const.HTTP_ERROR_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_PARAMS_MISSING

    return h_utils.generic_response(response_body, http_status)


from reportlab.lib.units import inch
from reportlab.platypus import TableStyle, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image
from reportlab.graphics.shapes import Drawing
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import colors
from reportlab.graphics.barcode import eanbc, qr, usps
from reportlab.lib.units import mm


def generate_pdf(file_name, appliances):
    HEIGHT = 23 * mm
    catalog = []
    table_row = []
    spacer = Spacer(5 * inch, 0.1 * inch)  # (widht, height)
    spacer1 = Spacer(5 * inch, 0.08 * inch)  # (widht, height)

    image_tornado_logo = Image('media/tornado_logo_qr.png')

    image_tornado_logo.drawHeight = 0.6 * inch * image_tornado_logo.drawHeight / image_tornado_logo.drawWidth
    image_tornado_logo.drawWidth = 0.7 * inch
    image_tornado_logo.hAlign = 'RIGHT'

    pdfmetrics.registerFont(TTFont("Mont-Bold", "./media/Mont-Bold.ttf"))
    pdfmetrics.registerFont(TTFont("Mont-Semibold", "./media/Mont-SemiBold.ttf"))
    pdfmetrics.registerFont(TTFont("Mont-Regular", "./media/Mont-Regular.ttf"))

    # styling objects for table row


    style_bold = ParagraphStyle(
        name='Normal',
        fontName='Mont-Bold',
        fontSize=7,
        leftIndent=10,
        rightIndent=10

    )

    # styles for table cell
    styles = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'CENTER'),
        # ('BACKGROUND', (0, 0), (0, -1), '#a7a5a5'),
        ('BOX', (0, 0), (-1, -1), 1, colors.black, 1, (15, 12, 0, 0)),  # outer border
        ('LINEBELOW', (0, 0), (-1, -2), 1, colors.black, 1, (15, 12, 0, 0)),
        # (dashes size, join, linecount, linespacing)
    ])

    p_scan_me = Paragraph("Scan Me", style=style_bold)

    for appliance in appliances:
        qr_code = qr.QrCodeWidget(appliance['ssid'] + ',' + appliance['password'])
        bounds = qr_code.getBounds()
        qr_width = (bounds[2] - bounds[0]) - 15
        qr_height = (bounds[3] - bounds[1]) - 17
        d = Drawing(HEIGHT, HEIGHT, transform=[HEIGHT / qr_width, 0, 0, HEIGHT / qr_height, -10, -5])
        d.add(qr_code)

        p_wifi_id_label = Paragraph("<b>WIFI ID</b> ",
                                    ParagraphStyle(name='Normal', fontName='Mont-Semibold', fontSize=5, leftIndent=5,
                                                   spaceBefore=1))
        p_wifi_id_value = Paragraph(appliance['ssid'],
                                    ParagraphStyle(name='Normal', fontName='Mont-Bold', fontSize=5, leftIndent=5))
        p_password_label = Paragraph("PASS.",
                                     ParagraphStyle(name='Normal', fontName='Mont-Semibold', fontSize=5,
                                                    leftIndent=5, ))
        p_password_value = Paragraph(appliance['password'],
                                     ParagraphStyle(name='Normal', fontName='Mont-Bold', fontSize=5, leftIndent=5))

        table_row.append(
            [[spacer1, d], [spacer, image_tornado_logo, p_scan_me, p_wifi_id_label, p_wifi_id_value, p_password_label,
                            p_password_value]]
        )
    catalog.append(Table(table_row,
                         # colWidths=[1.9 * inch, 2.3 * inch],
                         # colWidths=[2 * inch, 2.3 * inch],
                         # rowHeights=[2 * inch] * len(table_row), style=styles)
                         colWidths=[23 * mm, 27 * mm],
                         rowHeights=[25 * mm] * len(table_row), style=styles)

                   )
    doc = SimpleDocTemplate(file_name, pagesize=A4)
    doc.build(catalog)


'''
returns listing for schedules both active/inactive.
'''


@api_view(['GET'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def get_schedules_list(request):
    customer = h_utils.get_customer_from_request(request, None)
    # usr = h_utils.get_user_from_request(request, None)
    user = h_utils.get_user_from_request(request, None)
    day = h_utils.get_default_param(request, 'day', None)
    start_date = h_utils.get_default_param(request, 'start_date', None)
    appliance_id = h_utils.get_default_param(request, 'appliance_id', None)
    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.STATUS_ERROR,
                     const.RESPONSE_DATA: {}}
    http_status = const.HTTP_SUCCESS_CODE
    assignment_info = iop_utils.get_user_privelages_info(user, appliance_id)
    # print('token', request.auth)

    if assignment_info:
        start_date = parse(start_date)
        result_list = []

        # u_days_list = day,
        if customer and user:
            schedules = ActivitySchedule.objects \
                .filter(primary_entity_id=appliance_id,
                        schedule_activity_status_id__in=[OptionsEnum.ACTIVE, OptionsEnum.INACTIVE],
                        activity_type__in=[
                            IopOptionsEnums.IOP_SCHEDULE_DAILY,
                            IopOptionsEnums.IOP_USE_NOW,
                            IopOptionsEnums.IOP_QUICK_SCHEDULE,
                            IopOptionsEnums.IOP_SCHEDULE_ON_DEMAND,
                            IopOptionsEnums.IOP_SLEEP_MODE]) \
                .order_by('new_start_dt')


            if start_date:
                # query previous day, current day and next day
                start_date = start_date - timedelta(days=1)
                schedules = schedules.filter(start_date__gte=start_date)

            print("schedules count:     ", schedules.count())
            if schedules:
                for o in schedules:
                    # print("schedule:   ", o.start_date, '    ', o.u_activity_start_time)
                    result = {}
                    result['scheduled_by'] = o.modified_by.first_name + ' ' + o.modified_by.last_name
                    result['scheduled_by_email'] = o.modified_by.email
                    result['duration'] = o.notes
                    result['start_date'] = o.start_date
                    result['end_date'] = o.end_date
                    result['usage'] = o.activity_route if o.activity_route else None
                    result['temperature'] = o.action_items
                    result['type'] = o.activity_type.id
                    result['sch_id'] = o.id
                    result['status'] = o.schedule_activity_status.label
                    result['current_ctt']=o.current_ctt
                    # try:
                    #     q = ActivityQueue.objects.get(activity_schedule=o)
                    #
                    #     result['start_time'] = q.activity_datetime.time().replace(second=0)
                    #     result['end_time'] = q.activity_end_datetime.time().replace(second=0)
                    #
                    # except:
                    #     result['start_time'] = o.new_start_dt.time().replace(second=0)
                    #     result['end_time'] = o.new_end_dt.time().replace(second=0)

                    result['start_time'] = o.activity_start_time.replace(second=0)
                    result['end_time'] = o.activity_end_time.replace(second=0)
                    try:
                        act = Activity.objects.get(activity_schedule_id=o.id)
                        result['state'] = act.activity_status.label
                    except:
                        pass
                    # if there's no shifting then u_activity_start_time and activity_start_time will be same and there won't be any delay
                    # delay occurs incase of shifting where u_activity_start_time is changed.

                    if o.u_activity_start_time != o.activity_start_time:
                        delay = ((o.new_start_dt - o.old_start_dt).total_seconds() / 60)
                        result['delay'] = round(delay)
                    else:
                        result['delay'] = 0

                    result_list.append(result)

            response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
            response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
            response_body[const.RESPONSE_DATA] = result_list


        else:
            response_body[const.RESPONSE_STATUS] = const.HTTP_ERROR_CODE
            response_body[const.RESPONSE_MESSAGE] = const.TEXT_PARAMS_MISSING

    else:
        response_body[const.RESPONSE_STATUS] = const.HTTP_ERROR_CODE
        response_body[const.RESPONSE_MESSAGE] = "You don't have privileges to view the schedules"

    return h_utils.generic_response(response_body, http_status)


@api_view(['GET'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def energy_consumed_stats(request):
    from dateutil.parser import parse
    customer = h_utils.get_customer_from_request(request, None)
    sub_type = h_utils.get_default_param(request, 'sub_type', None)
    ent_id = h_utils.get_default_param(request, 'entity_id', None)

    start_date = h_utils.get_default_param(request, 'start_date', None)
    end_date = h_utils.get_default_param(request, 'end_date', None)

    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.STATUS_ERROR,
                     const.RESPONSE_DATA: {}}
    http_status = const.HTTP_SUCCESS_CODE
    result = []

    if customer:
        start_date = parse(start_date)
        end_date = parse(end_date)
        avg_stats = iop_utils.util_get_usage_stats(c_id=customer, e_id=ent_id, s_date=start_date, e_date=end_date)

        for av in avg_stats:
            result.append({'timestamp': av.timestamp, 'total_energy_consumed': av.total_energy_consumed})
        response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
        response_body[const.RESPONSE_DATA] = result

    else:
        response_body[const.RESPONSE_STATUS] = const.HTTP_ERROR_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_UNSUCCESSFUL

    return h_utils.generic_response(response_body, http_status)


'''
Deletes the appliance. Also deletes it's associated customer device.
'''


@api_view(['POST', 'PATCH'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def delete_appliance(request):
    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.HTTP_ERROR_CODE,
                     const.RESPONSE_DATA: []}
    user = h_utils.get_user_from_request(request, None)
    module_id = h_utils.get_module_from_request(request, None)
    appliance_id = h_utils.get_data_param(request, 'appliance_id', None)
    status = h_utils.get_data_param(request, 'status', None)
    print("STATUS in DELETE ENTITY : ", status)
    print("APPLIACE ID LSIT in DELETE ENTITY : ", appliance_id)

    try:
        for dev_id in appliance_id:
            user_assignment = iop_utils.get_user_privelages_info(user, dev_id)
            if user_assignment:
                if user_assignment.is_admin:
                    schedules = ActivitySchedule.objects.filter(primary_entity_id=dev_id)
                    if schedules:
                        schedules.delete()
                    try:
                        ent = Entity.objects.get(id=dev_id)
                    except Exception as e:
                        print("entity error", e)
                        ent = None
                    if ent:
                        try:
                            agg = IopAggregation.objects.get(device_id=dev_id)
                            agg.delete()
                        except Exception as e:
                            print("Aggregation error", e)
                            agg = None

                        try:
                            c_device = CustomerDevice.objects.get(device_id=ent.device_name.device_id)
                            ent.delete()
                            c_device.delete()
                        except Exception as e:
                            print("customer devices error", e)
                            c_device = None

                    response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
                    response_body[const.RESPONSE_MESSAGE] = "Successfully deleted appliance"
                    return h_utils.generic_response(response_body=response_body, http_status=200)

                else:
                    response_body[const.RESPONSE_STATUS] = const.HTTP_ERROR_CODE
                    response_body[
                        const.RESPONSE_MESSAGE] = "You don't have enough permissions to delete this appliance."
                    return h_utils.generic_response(response_body=response_body, http_status=200)
            else:
                response_body[const.RESPONSE_STATUS] = const.HTTP_ERROR_CODE
                response_body[const.RESPONSE_MESSAGE] = "You are not assigned to this device."
                return h_utils.generic_response(response_body=response_body, http_status=200)

    except Exception as L:
        print(L)


@api_view(['POST', 'PATCH'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def delete_appliance_frontend(request):
    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.HTTP_ERROR_CODE,
                     const.RESPONSE_DATA: []}
    user = h_utils.get_user_from_request(request, None)
    module_id = h_utils.get_module_from_request(request, None)
    appliance_id = h_utils.get_data_param(request, 'appliance_id', None)
    status = h_utils.get_data_param(request, 'status', None)
    print("STATUS in FRONTEND DELETE ENTITY : ", status)
    print("APPLIACE ID LSIT in FRONTEND DELETE ENTITY : ", appliance_id)

    try:
        # status = 12 means delete
        if status == 12:
            for dev_id in appliance_id:
                schedules = ActivitySchedule.objects.filter(primary_entity_id=dev_id)
                if schedules:
                    schedules.delete()
                try:
                    ent = Entity.objects.get(id=dev_id)
                except Exception as e:
                    print("entity error", e)
                    ent = None
                if ent:
                    try:
                        agg = IopAggregation.objects.get(device_id=dev_id)
                        agg.delete()
                    except Exception as e:
                        print("Aggregation error", e)
                        agg = None

                    try:
                        c_device = CustomerDevice.objects.get(device_id=ent.device_name.device_id)
                        ent.delete()
                        c_device.delete()
                    except Exception as e:
                        print("customer devices error", e)
                        c_device = None

                response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
                response_body[const.RESPONSE_MESSAGE] = "Successfully deleted appliance"
                return h_utils.generic_response(response_body=response_body, http_status=200)

        # status =2 means just mark it as inactive
        elif status == 2:
            for dev_id in appliance_id:
                ent = Entity.objects.get(id=dev_id)
                # type_id = int(ent.type_id)
                ent.status_id = status
                ent.description = ""
                ent.save()

                # CHECK IF PARENT
                Assignment.objects.filter(parent=ent, status_id=OptionsEnum.ACTIVE).update(
                    status_id=OptionsEnum.INACTIVE)
                # CHECK IF CHILD
                Assignment.objects.filter(child=ent, status_id=OptionsEnum.ACTIVE).update(
                                status_id=OptionsEnum.INACTIVE)

                response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
                response_body[const.RESPONSE_MESSAGE] = "Appliance Inactive successful"
                return h_utils.generic_response(response_body=response_body, http_status=200)

        elif status == 1:
            for dev_id in appliance_id:
                ent = Entity.objects.get(id=dev_id)
                # type_id = int(ent.type_id)
                ent.status_id = status
                ent.description = ""
                ent.save()

                # CHECK IF PARENT
                Assignment.objects.filter(parent=ent, status_id=OptionsEnum.INACTIVE).update(
                    status_id=OptionsEnum.ACTIVE)
                # CHECK IF CHILD
                Assignment.objects.filter(child=ent, status_id=OptionsEnum.INACTIVE).update(
                                status_id=OptionsEnum.ACTIVE)

                response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
                response_body[const.RESPONSE_MESSAGE] = "Appliance Activated Successfully"
                return h_utils.generic_response(response_body=response_body, http_status=200)

    except Exception as L:
        print(L)
        response_body[const.RESPONSE_STATUS] = const.HTTP_ERROR_CODE
        response_body[
            const.RESPONSE_MESSAGE] = "An Error occured while performing the desired operation on the selected device."
        return h_utils.generic_response(response_body=response_body, http_status=200)


@api_view(['GET'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def check_appliance_data(request):
    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.HTTP_ERROR_CODE,
                     const.RESPONSE_DATA: []}
    user = h_utils.get_user_from_request(request, None)
    module_id = h_utils.get_module_from_request(request, None)
    appliance_id = h_utils.get_default_param(request, 'appliance_id', None)

    if appliance_id:
        schedules = ActivitySchedule.objects.filter(primary_entity_id=appliance_id,
                                                    schedule_activity_status_id=OptionsEnum.ACTIVE)

        if schedules:
            response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
            response_body[
                const.RESPONSE_MESSAGE] = "Warning! You are about to delete a device that has upcoming/running schedules. Do you want to delete it?"
        else:
            response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
            response_body[const.RESPONSE_MESSAGE] = "Safe to remove device. No related schedules exist."


    else:
        response_body[const.RESPONSE_STATUS] = const.HTTP_ERROR_CODE
        response_body[const.RESPONSE_MESSAGE] = "Appliance doesnot exist"

    return h_utils.generic_response(response_body=response_body, http_status=200)


@api_view(['POST'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def edit_appliance(request):
    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.HTTP_ERROR_CODE,
                     const.RESPONSE_DATA: []}
    user = h_utils.get_user_from_request(request, None)
    module_id = h_utils.get_module_from_request(request, None)
    appliance_id = h_utils.get_default_param(request, 'appliance_id', None)

    if appliance_id:
        try:
            ent = Entity.objects.get(id=appliance_id)
        except:
            ent = None

        if ent:
            ent.name = request.data['name']
            ent.save()
            response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
            response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
    return h_utils.generic_response(response_body=response_body, http_status=200)


@api_view(['GET'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def get_single_appliance_details(request):
    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.HTTP_ERROR_CODE,
                     const.RESPONSE_DATA: []}
    user = h_utils.get_user_from_request(request, None)
    module_id = h_utils.get_module_from_request(request, None)
    appliance_id = h_utils.get_default_param(request, 'appliance_id', None)
    inner_result = []
    if appliance_id:
        try:
            ent = Entity.objects.get(id=appliance_id)
        except:
            ent = None

        if ent:
            ser = HomeAppliancesSerializer(ent)
            result = ser.data

            shared_with = UserEntityAssignment.objects.filter(device=ent, status_id=OptionsEnum.ACTIVE, is_admin=False)
            for s_w in shared_with:
                inner_result['name'] = s_w.user.first_name + ' ' + s_w.user.last_name

            result['shared_with'] = inner_result
            response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
            response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
            response_body[const.RESPONSE_DATA] = result
    return h_utils.generic_response(response_body=response_body, http_status=200)


'''
This API dis-associates user with the appliance.
'''


@api_view(['POST'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def delete_user(request):
    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.HTTP_ERROR_CODE,
                     const.RESPONSE_DATA: []}
    user = h_utils.get_user_from_request(request, None)

    tbd_user = h_utils.get_data_param(request, 'tbd_user', None)
    appliance_id = h_utils.get_data_param(request, 'appliance_id', None)

    user_assignment = iop_utils.get_user_privelages_info(user, appliance_id)

    if user_assignment:
        if user_assignment.is_admin:  # Only admin has the privelage to perform this action
            user = User.objects.get(id=tbd_user)
            try:
                assignment = UserEntityAssignment.objects.get(user=user, device_id=appliance_id,
                                                              # Get the assignment of user with applinace
                                                              status_id=OptionsEnum.ACTIVE)
            except:
                assignment = None

            if assignment:
                assignment.status = Options.objects.get(id=OptionsEnum.INACTIVE)  # Mark this assignment inactive.
                assignment.save()

                send_notification_violations(None, driver_id=None,  # Send notification to the user.
                                             customer_id=user.customer.id, module_id=ModuleEnum.IOP,
                                             title="You have been removed from device: {}.".format(
                                                 assignment.device.name)
                                             , users_list=[user])
            else:
                response_body[const.RESPONSE_STATUS] = const.HTTP_ERROR_CODE
                response_body[const.RESPONSE_MESSAGE] = "User not assigned to this appliance."
                return h_utils.generic_response(response_body=response_body, http_status=200)

            schs = ActivitySchedule.objects.filter(modified_by=user,
                                                   primary_entity_id=appliance_id)  # Also deletes schedules set by that user on the appliance

            if schs:
                for sch in schs:
                    ActivitySchedule.objects.filter(suspended_by=sch).update(suspended_by=None)
                    sch.delete()

            response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
            response_body[
                const.RESPONSE_MESSAGE] = "Succesfully removed user"


        else:
            response_body[const.RESPONSE_STATUS] = const.HTTP_ERROR_CODE
            response_body[
                const.RESPONSE_MESSAGE] = "Warning! You don't have enough privelages to perform that operation."

    return h_utils.generic_response(response_body=response_body, http_status=200)


@api_view(['POST'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def add_appliance_details_for_qr(request):
    response_body = {const.RESPONSE_MESSAGE: const.TEXT_SUCCESSFUL, const.RESPONSE_STATUS: const.HTTP_SUCCESS_CODE,
                     const.RESPONSE_DATA: []}
    http_status = const.HTTP_SUCCESS_CODE

    devices_list = h_utils.get_default_param(request, 'devices_list', None)
    num_of_rows_created = 0

    for device in reversed(devices_list):
        p, created = ApplianceQR.objects.get_or_create(
            ssid=device['ssid'],
            password=device['password']
        )
        print(p, created)

        if created:
            num_of_rows_created = num_of_rows_created + 1

        if num_of_rows_created >= 1:
            response_body[const.RESPONSE_MESSAGE] = str(num_of_rows_created) + ' ' + const.TEXT_SUCCESSFUL

        else:
            response_body[const.RESPONSE_MESSAGE] = 'Report has been generated Successfully'

  


    return h_utils.generic_response(response_body=response_body, http_status=http_status)


@api_view((['GET']))
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def get_appliance_details_for_qr(request):
    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.HTTP_ERROR_CODE,
                     const.RESPONSE_DATA: []}
    http_status = const.HTTP_SUCCESS_CODE
    c_id = h_utils.get_customer_from_request(request, None)
    start_date = h_utils.get_default_param(request, 'start_date', None)
    end_date = h_utils.get_default_param(request, 'end_date', None)

    result = {'devices': []}
    if c_id:
        try:
            devices = ApplianceQR.objects.all().order_by('-created_datetime','ssid')

            if start_date and end_date:
                devices = devices.filter(created_datetime__gte=start_date, created_datetime__lte=end_date)

            if devices:
                ser = ApplianceQRSerializer(devices, many=True)
                query_result = ser.data

                for q_res in query_result:
                    result['devices'].append(q_res)

            response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
            response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
            response_body[const.RESPONSE_DATA] = result


        except:
            traceback.print_exc()
            pass

    return h_utils.generic_response(response_body=response_body, http_status=http_status)


@api_view((['PATCH']))
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def deletion_qr_code(request):
    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.HTTP_ERROR_CODE,
                     const.RESPONSE_DATA: []}
    http_status = const.HTTP_SUCCESS_CODE
    list_id = h_utils.get_data_param(request, 'ssid_list', None)

    if list_id:
        for id in list_id:
            try:
                device = ApplianceQR.objects.filter(ssid=id)
                if device:
                    device.delete()
            except Exception as e:
                traceback.print_exc()

        response_body[const.RESPONSE_DATA] = {const.TEXT_OPERATION_SUCCESSFUL: True}
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
        response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE

    else:
        response_body = const.ERROR_PARAMS_MISSING_BODY
        http_status = const.TEXT_OPERATION_UNSUCCESSFUL
    return h_utils.generic_response(response_body=response_body, http_status=http_status)


@api_view((['GET']))
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def get_online_status_iop_device(request):
    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.HTTP_SUCCESS_CODE,
                     const.RESPONSE_DATA: []}
    http_status = const.HTTP_SUCCESS_CODE
    c_id = h_utils.get_customer_from_request(request, None)
    user = h_utils.get_user_from_request(request, None)
    device_id = h_utils.get_default_param(request, 'device_id', None)

    if device_id:
        try:
            status = LogisticAggregations.objects.get(device_id=device_id)
            response_body[const.RESPONSE_DATA] = {'status': status.online_status}
            response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
        except:
            response_body[const.RESPONSE_DATA] = {'status': False}
            response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL

    else:
        response_body[const.RESPONSE_DATA] = 'Device doesnot exist'
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_UNSUCCESSFUL
        response_body[const.RESPONSE_STATUS] = const.HTTP_ERROR_CODE

    return h_utils.generic_response(response_body=response_body, http_status=http_status)


'''
@api_view((['GET']))
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def get_online_status_iop_device(request):
    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.HTTP_SUCCESS_CODE,
                     const.RESPONSE_DATA: []}
    http_status = const.HTTP_SUCCESS_CODE
    customer = h_utils.get_customer_from_request(request, None)
    user = h_utils.get_user_from_request(request, None)
    day = h_utils.get_default_param(request, 'day', None)
    start_date = h_utils.get_default_param(request, 'start_date', None)
    appliance_id = h_utils.get_default_param(request, 'appliance_id', None)
    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.STATUS_ERROR,
                     const.RESPONSE_DATA: {}}
    http_status = const.HTTP_SUCCESS_CODE
    assignment_info = iop_utils.get_user_privelages_info(user, appliance_id)

    if assignment_info:
        start_date = parse(start_date)
        result_list = []

        if customer and user:
            schedules = ActivitySchedule.objects.filter(primary_entity_id=appliance_id,
                                                        u_days_list=day,
                                                        schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                        activity_type_id=IopOptionsEnums.IOP_QUICK_SCHEDULE).order_by('u_activity_start_time')

            if start_date:
                schedules = schedules.filter(start_date=start_date)

            if schedules:
                for o in schedules:
                    result = {}
                    result['scheduled_by'] = o.modified_by.first_name + ' ' + o.modified_by.last_name
                    result['duration'] = o.notes
                    result['start_date'] = o.start_date
                    result['end_date'] = o.end_date
                    result['usage'] = o.activity_route
                    result['temperature'] = o.action_items
                    result['type'] = o.activity_type.id
                    result['sch_id'] = o.id
                    try:
                        q = ActivityQueue.objects.get(activity_schedule=o)
                        result['start_time'] = q.activity_datetime.time().replace(second=0)
                        result['end_time'] = q.activity_end_datetime.time().replace(second=0)
                        if q.is_on is True and q.suspend is False:
                            result['state'] = 'In use'

                        elif q.is_on is False and q.suspend is True:
                            result['state'] = 'Suspended'
                        else:
                            result['state'] = 'Not In use'
                    except:
                        result['state'] = 'Not in use'
                        result['start_time'] = o.u_activity_start_time.replace(second=0)
                        result['end_time'] = o.u_activity_end_time.replace(second=0)

                    if o.u_activity_start_time != o.activity_start_time:
                        start_datetime = parse(str(o.start_date) + ' ' + str(o.activity_start_time))
                        u_start_datetime = parse(str(o.start_date) + ' ' + str(o.u_activity_start_time))

                        delay = ((u_start_datetime - start_datetime).total_seconds() / 60)
                        delay = round(delay, 0)
                        result['delay'] = delay
                    else:
                        result['delay'] = 0
                    result_list.append(result)

            response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
            response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
            response_body[const.RESPONSE_DATA] = result_list
        else:
            response_body[const.RESPONSE_STATUS] = const.HTTP_ERROR_CODE
            response_body[const.RESPONSE_MESSAGE] = const.TEXT_PARAMS_MISSING

    else:
        response_body[const.RESPONSE_STATUS] = const.HTTP_ERROR_CODE
        response_body[const.RESPONSE_MESSAGE] = "You don't have privileges to view the schedules"

    return h_utils.generic_response(response_body, http_status)

'''


@api_view(['GET'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def get_quick_schedules(request):
    customer = h_utils.get_customer_from_request(request, None)
    # usr = h_utils.get_user_from_request(request, None)
    user = h_utils.get_user_from_request(request, None)
    day = h_utils.get_default_param(request, 'day', 0)
    appliance_id = h_utils.get_default_param(request, 'appliance_id', None)
    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.STATUS_ERROR,
                     const.RESPONSE_DATA: {}}
    http_status = const.HTTP_SUCCESS_CODE
    assignment_info = iop_utils.get_user_privelages_info(user, appliance_id)

    if assignment_info:
        dict = {'Shower': {'start_times': [], 'end_times': []}, 'Laundary': {'start_times': [], 'end_times': []},
                'Dishes': {'start_times': [], 'end_times': []}, 'Throughout': {'start_times': [], 'end_times': []}}

        if customer and user:
            schedules = ActivitySchedule.objects.filter(primary_entity_id=appliance_id, u_days_list=day,
                                                        schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                        activity_type__id=IopOptionsEnums.IOP_QUICK_SCHEDULE).order_by(
                'u_activity_start_time')

            if schedules:
                for o in schedules:
                    usages = o.activity_route.split(',')
                    for u in usages:
                        dict[u]['start_times'].append(o.u_activity_start_time)
                        dict[u]['end_times'].append(o.u_activity_end_time)

            response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
            response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
            response_body[const.RESPONSE_DATA] = dict
        else:
            response_body[const.RESPONSE_STATUS] = const.HTTP_ERROR_CODE
            response_body[const.RESPONSE_MESSAGE] = const.TEXT_PARAMS_MISSING

    else:
        response_body[const.RESPONSE_STATUS] = const.HTTP_ERROR_CODE
        response_body[const.RESPONSE_MESSAGE] = "You don't have privileges to view the schedules"

    return h_utils.generic_response(response_body, http_status)


@api_view(['POST'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def delete_schedule(request):
    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.STATUS_ERROR,
                     const.RESPONSE_DATA: {}}
    http_status = const.HTTP_SUCCESS_CODE
    pk = h_utils.get_data_param(request, 'pk', 0)
    filter = request.data.get("single")
    print(request.data)

    print(filter)
    try:
        sch = ActivitySchedule.objects.get(id=pk)
        try:
            if filter == False or filter == "False":
                all_sch = ActivitySchedule.objects.filter(primary_entity_id=sch.primary_entity_id , activity_start_time = sch.activity_start_time , activity_end_time = sch.activity_end_time ).delete()

        except Exception as e:
            print(e)
            pass
        # queue = ActivityQueue.objects.filter(activity_schedule=sch).delete()
        # activity = Activity.objects.filter(activity_schedule=sch).delete()

        # ActivitySchedule.objects.filter(suspended_by_id=sch).update(suspended_by=None)
        ttr, _ = iop_utils.calculcate_ttr(ent=sch.primary_entity, desired_temp=sch.action_items,
                                          duration=sch.notes)
        # iop_utils.set_device_temperature(obj=None, ent=sch.primary_entity, temp=const.DEFAULT_TEMP)
        print("ttr in delete API:   ", ttr)
        try:
            print("In try of delete try")
            import time
            current_time = datetime.now(timezone.utc).replace(microsecond=0)
            event_time = sch.new_start_dt.replace(microsecond=0)
            time_difference = event_time - current_time
            difference_in_minutes = time_difference.total_seconds() / 60.0
            print("TIME DIFFERENCE IN MINUTES: ", difference_in_minutes)
            # iop_utils.set_device_temperature(obj=None, ent=sch.primary_entity, temp=const.DEFAULT_TEMP)
            if difference_in_minutes <= ttr:
                pass
                # iop_utils.set_device_temperature(obj=None, ent=sch.primary_entity, temp=const.DEFAULT_TEMP) #change not set set temperature
            # a_q = ActivityQueue.objects.get(activity_schedule__id=sch.id)
            # print(a_q.temp_set)
            # print("below Activity Queue Check")
            # if a_q.temp_set:
            #     print("INSIDE IF OF TEMP SET IN ACTIVITY QUEUE CHECK !!!!")
            #     iop_utils.set_device_temperature(obj=None, ent=sch.primary_entity, temp=const.DEFAULT_TEMP)
            #     print("DELETED !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! TEMP SET TO DEFAULT !!!!!!!!!!!!!")

        except Exception as excep:
            print(str(excep))

        # iop_utils.set_device_temperature(obj=None, ent=sch.primary_entity, temp=const.DEFAULT_TEMP)
        sch.delete()
        response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
        response_body[const.RESPONSE_MESSAGE] = 'Successfully deleted Schedule'
    except Exception as e:
        print(e)
        sch = None
        response_body[const.RESPONSE_STATUS] = const.HTTP_ERROR_CODE
        response_body[const.RESPONSE_MESSAGE] = "There is some issue. Please try again after few minutes."
    return h_utils.generic_response(response_body, http_status)


from rest_framework.authtoken.models import Token


@api_view((['GET']))
@permission_classes([AllowAny, ])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def get_energy_consumed_graph(request):
    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.HTTP_ERROR_CODE,
                     const.RESPONSE_DATA: []}
    http_status = const.HTTP_SUCCESS_CODE
    device_id = h_utils.get_default_param(request, 'device_id', None)
    tz_difference = h_utils.get_default_param(request, 'tz_difference', 0)  # utc to PST by default
    customer = h_utils.get_customer_from_request(request, None)
    today_date = timezone.now().today().date()
    user = h_utils.get_user_from_request(request, None)
    key = h_utils.get_default_param(request, 'key', None)

    if key:
        try:
            token = Token.objects.get(key=key)
            request.user = token.user
            request.auth = token
        except:
            pass

    if request.user:
        # result = {'today': {'regular_appliance': [{'hr': 1, 'energy': 4}], 'smart_appliance': [{'hr': 1, 'energy': 4}]},
        #           'week': {'regular_appliance': [{'date': 10, 'energy': 8, 'month_name': 'June'}],
        #                    'smart_appliance': [{'date': 15, 'energy': 10, 'month_name': 'June'}]},
        #           'month': {'regular_appliance': [{'date': 1, 'energy': 12, 'month_name': 'June'}],
        #                     'smart_appliance': [{'date': 2, 'energy': 15, 'month_name': 'June'}]},
        #           }

        myresult = {'today': {'regular_appliance': [], 'smart_appliance': []},
                    'week': {'regular_appliance': [], 'smart_appliance': []},
                    'month': {'regular_appliance': [], 'smart_appliance': []}
                    }
        if device_id:
            try:

                myresult['today'] = get_day_ec(device_id, today_date, tz_difference)
                myresult['week'] = get_ec_duration(device_id, today_date - timedelta(days=7), today_date)
                myresult['month'] = get_ec_duration(device_id, today_date - timedelta(days=30), today_date)

                response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
                response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
                response_body[const.RESPONSE_DATA] = myresult


            except:
                traceback.print_exc()
                pass
    else:
        response_body[const.RESPONSE_STATUS] = 401
        response_body[const.RESPONSE_MESSAGE] = 'Unauthorized'
    return h_utils.generic_response(response_body=response_body, http_status=http_status)


def get_day_ec(device_id, date, tz_difference):
    tempObj = {'smart_appliance': [], 'regular_appliance': []}
    query = EnergyConsumption.objects.filter(device_id=device_id, datetime__date=date).order_by('datetime')
    print('query date time     ', query[0].datetime)
    max = query.aggregate(max=Max('energy_consumed'))

    count = query.count()
    tempObj['max'] = max['max'] or 0

    saving_factor = 0
    if query.exists():
        for obj in query:
            # hour = TruncHour('datetime', output_field=TimeField())
            # split_timezone1 = int(tz_difference)
            # converted_time = obj.datetime + timedelta(hours=split_timezone1)
            # time = datetime.strftime(converted_time, '%I %p')
            tempObj['smart_appliance'].append({'hr': obj.datetime, 'date': obj.datetime, 'energy': obj.energy_consumed})
            tempObj['regular_appliance'].append(
                {'hr': obj.datetime, 'date': obj.datetime, 'energy': obj.ec_regular_appliance})

            saving_factor = saving_factor + iop_utils.util_get_energy_saving_percentage(
                iop_utils.util_get_saving_factor_per_day(obj.datetime),
                obj.ec_regular_appliance)

    tempObj['saving'] = round(saving_factor, 2)
    return tempObj


def get_ec_duration(device_id, start_date, end_date):
    tmpObj = {'smart_appliance': [], 'regular_appliance': []}

    try:
        # query = EnergyConsumption.objects.filter(device_id=device_id, datetime__lte= end_date, datetime__gte= start_date)
        '''
        query = EnergyConsumption.objects\
            .extra(select={'the_date': 'date(datetime)'})\
            .filter(device_id=device_id, datetime__date__lte= end_date, datetime__date__gte= start_date) \
            .values('the_date', 'device_id', 'energy_consumed', 'ec_regular_appliance') \
            .annotate(max_date=Max('datetime'))
        '''
        query = EnergyConsumption.objects.filter(datetime__range=[start_date, end_date + timedelta(days=1)],
                                                 device_id=device_id)

        from itertools import chain
        my_obj_list = list()
        days = (end_date - start_date).days

        for i in range(days + 1):
            temp_date = start_date + timedelta(days=i)
            i += 1
            # obj = query.filter(datetime__date=temp_date).values('datetime', 'energy_consumed', 'ec_regular_appliance',
            #                                                     'device_id').last()
            print("day count  %d" % i)
            obj = query.filter(datetime__date=temp_date).values('datetime', 'energy_consumed', 'ec_regular_appliance',
                                                                'device_id').order_by('-datetime').first()
            print("obj  ", obj)

            if obj:
                my_obj_list.append(obj)

        saving_factor = 0
        max = 0
        max_rc = 0
        if query.exists():
            for obj in my_obj_list:
                saving_factor = saving_factor + iop_utils.util_get_energy_saving_percentage(
                    iop_utils.util_get_saving_factor_per_day(obj['datetime']),
                    obj['ec_regular_appliance'])
                month_name = calendar.month_name[obj['datetime'].month]
                tmpObj['smart_appliance'].append(
                    {'date': obj['datetime'].day, 'date2': obj['datetime'], 'energy': obj['energy_consumed'],
                     'month_name': month_name})
                tmpObj['regular_appliance'].append(
                    {'date': obj['datetime'].day, 'date2': obj['datetime'], 'energy': obj['ec_regular_appliance'],
                     'month_name': month_name})

        newlist = sorted(my_obj_list, key=lambda k: k['energy_consumed'])
        newlist2 = sorted(my_obj_list, key=lambda k: k['ec_regular_appliance'])
        if len(newlist):
            max = newlist[-1]['energy_consumed']
        if len(newlist2):
            max_rc = newlist2[-1]['ec_regular_appliance']

        tmpObj['max'] = max
        tmpObj['saving'] = round(saving_factor / days, 2) * 100
        print('saving', saving_factor, days, saving_factor / days, tmpObj['saving'])

        if max_rc > max:
            tmpObj['max'] = max_rc

        return tmpObj


    except Exception as e:
        print(e)
        pass


@api_view((['GET']))
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def get_density_reporting_graph(request):
    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.HTTP_ERROR_CODE,
                        const.RESPONSE_DATA: []}
    http_status = const.HTTP_SUCCESS_CODE
    try:
        response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.HTTP_ERROR_CODE,
                        const.RESPONSE_DATA: []}
        http_status = const.HTTP_SUCCESS_CODE
        entity_id = h_utils.get_default_param(request, 'entity_id', None)
        start_date = h_utils.get_default_param(request, 'start_date', None)

        end_date = h_utils.get_default_param(request, 'end_date', None)
        start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
        end_date=datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
        print(start_date, end_date,'a=asdhnasndjkasndknaskdnkas')
        today_date = timezone.now().date()

        # type_id = h_utils.get_default_param(request,'type_id',None)
        type_id = h_utils.get_list_param(request, 'type_id', None)

        user_id = h_utils.get_list_param(request, 'user_id', None)

        show_density_reporting = h_utils.get_default_param(request, 'show_density_reporting', None)

        tempArr = []

        tempObj = {'today': [], 'week': [], 'month': []}

        print('===========  type id in density reporting ===============')
        print(type_id)
    
        schs = ActivitySchedule.objects.filter(new_start_dt__date__range=[start_date, end_date], primary_entity_id=entity_id).values('created_datetime', 'notes', 'activity_type_id', 'modified_by', 'modified_by__first_name',
                    'activity_start_time', 'start_date', 'u_activity_start_time', 'new_start_dt').order_by('new_start_dt')

        print('schedule count  %d  ' % schs.count())
        if show_density_reporting:
            if user_id:
                schs = schs.filter(modified_by__in=user_id).order_by('new_start_dt ')
            if type_id:
                schs = schs.filter(activity_type_id__in=type_id).order_by('new_start_dt ')
            if schs.exists():
                for obj in schs:
                    tempArr.append(obj)

            response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
            response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
            response_body[const.RESPONSE_DATA] = tempArr

        else:
            num_of_events_today = schs \
                .values('activity_type_id') \
                .annotate(num_events=Count('activity_type_id')).order_by('-num_events')

            print('number of events today  %d  ' % num_of_events_today)

            for obj in num_of_events_today:
                tempObj['today'].append(obj)

            num_of_events_week = iop_utils.get_number_of_events(entity_id=entity_id,
                                                                start_date=today_date - timedelta(days=7),
                                                                end_date=today_date, eventsToExclude=None)
            for obj in num_of_events_week:
                tempObj['week'].append(obj)

            num_of_events_month = iop_utils.get_number_of_events(start_date=today_date - timedelta(days=30),
                                                                end_date=today_date, entity_id=entity_id)
            for obj in num_of_events_month:
                tempObj['month'].append(obj)

            response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
            response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
            response_body[const.RESPONSE_DATA] = tempObj

        return h_utils.generic_response(response_body=response_body, http_status=http_status)
    except Exception as e:
        print(e)
        return h_utils.generic_response(response_body=response_body, http_status=http_status)

@api_view((['GET']))
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def get_events_created_graph(request):
    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.HTTP_ERROR_CODE,
                     const.RESPONSE_DATA: []}
    http_status = const.HTTP_SUCCESS_CODE
    entity_id = h_utils.get_default_param(request, 'entity_id', None)
    start_date = h_utils.get_default_param(request, 'start_date', None)
    end_date = h_utils.get_default_param(request, 'end_date', None)
    tempObj = {'data':[]}

    # eventsToExclude = [IopOptionsEnums.RECURRING_SLEEP_MODE]
    
    eventsToExclude=[]
    start_date_data = iop_utils.util_get_entity_events_count(entity_id=entity_id, start_date=start_date,
                                                                 end_date=end_date, eventsToExclude=eventsToExclude)
    

    for obj in start_date_data:
        tempObj['data'].append(obj)

    response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
    response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
    response_body[const.RESPONSE_DATA] = tempObj

    return h_utils.generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def get_device_day_stats(request):
    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.HTTP_ERROR_CODE,
                     const.RESPONSE_DATA: []}
    http_status = const.HTTP_SUCCESS_CODE
    entity_id = h_utils.get_default_param(request, 'entity_id', None)
    today_date = timezone.now().date()

    energy_consumed = 0
    stats = {}

    if entity_id:
        energy_consumed_query = EnergyConsumption.objects.filter(device_id=entity_id, datetime=today_date)
        if energy_consumed_query:
            energy_consumed_query = energy_consumed_query.latest('datetime')
            energy_consumed = energy_consumed_query.energy_consumed

        num_events_query = ActivitySchedule.objects.filter(start_date=today_date, primary_entity_id=entity_id).count()

        # num_events_query = ActivitySchedule.objects.filter(start_date=today_date, primary_entity_id=entity_id,
        #                                                    schedule_activity_status_id=OptionsEnum.ACTIVE).count()

        # errors_count = iop_utils.util_get_error_logs(c_id=None, e_id=entity_id,
        #                                              mod_id=None, dev_type_id=None,
        #                                              err_code=None, s_date=today_date, e_date=today_date).count()

        errors_count = ErrorLogs.objects.filter(Q(inactive_score__gt=0), Q(device_id=entity_id), Q(date__gte=today_date), Q(date__lte=today_date)).count()
        stats['energy_consumed'] = energy_consumed
        stats['events_created'] = num_events_query
        stats['err_data'] = errors_count
        stats['users'] = []

        users_assignments = iop_utils.util_get_device_users(entity_id,
                                                            DeviceTypeAssignmentEnum.IOP_DEVICE_USER_ASSIGNMENT)

        for user in users_assignments:
            stats['users'].append(user.users_assignments_as_json())

        response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
        response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
        response_body[const.RESPONSE_DATA] = stats

    else:
        response_body[const.RESPONSE_STATUS] = const.HTTP_ERROR_CODE
        response_body[const.RESPONSE_MESSAGE] = "You don't have privileges to view the schedules"

    return h_utils.generic_response(response_body, http_status)


@api_view(['GET'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def get_temperature_graph(request):
    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.HTTP_ERROR_CODE,
                     const.RESPONSE_DATA: []}
    http_status = const.HTTP_SUCCESS_CODE
    entity_id = h_utils.get_default_param(request, 'entity_id', None)
    start_date = h_utils.get_default_param(request, 'start_date', None)
    end_date = h_utils.get_default_param(request, 'end_date', None)

    tempArr = []
    if end_date:
        # hypernet_post_data_query = HypernetPostData.objects.filter(device=entity_id, timestamp__date__lte=end_date, timestamp__date__gte=start_date).aggregate(Avg('active_score'))

        # qs1 = HypernetPostData.objects \
        #         .extra({'created':"date(timestamp)"})\
        #         .filter(device=entity_id, timestamp__date__lte=end_date, timestamp__date__gte=start_date) \
        #         .values('created').annotate(created_count=Count('id'))

        hypernet_post_data_query = HypernetPostData.objects \
            .filter(device=entity_id, timestamp__lte=end_date, timestamp__gte=start_date) \
            .extra({'day': "timestamp::date"}) \
            .values('day') \
            .annotate(avg_temperature=Avg('active_score')) \
            .order_by('day')
    else:
        from django.db.models.functions import TruncHour
        hypernet_post_data_query = HypernetPostData.objects \
            .filter(device=entity_id, timestamp__date=start_date) \
            .annotate(day=TruncHour('timestamp')) \
            .values('day') \
            .annotate(avg_temperature=Avg('active_score')).order_by('day')

    for obj in hypernet_post_data_query:
        print(obj['day'])
        tempArr.append({
            'day': obj['day'],
            'avg_temperature': obj['avg_temperature'],
            # 'ctt': obj['ctt']
        })

    # latest_data = HypernetPostData.objects.filter(device=entity_id).latest('timestamp')
    # res_data = {
    #     'array': tempArr,
    #     'ctt': latest_data.ctt or None
    # }

    response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
    response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
    response_body[const.RESPONSE_DATA] = tempArr

    return h_utils.generic_response(response_body=response_body, http_status=http_status)


import calendar

'''
Returns sleep mode ist
'''


@api_view(['GET'])
@h_utils.exception_handler(
    h_utils.generic_response(response_body=const.ERROR_RESPONSE_BODY, http_status=const.HTTP_ERROR_CODE))
def sleep_mode_listing(request):
    response_body = {const.RESPONSE_MESSAGE: const.TEXT_PARAMS_MISSING, const.RESPONSE_STATUS: const.HTTP_ERROR_CODE,
                     const.RESPONSE_DATA: []}
    http_status = const.HTTP_SUCCESS_CODE

    appliance_id = h_utils.get_default_param(request, 'primary_entity', None)
    schedules = ActivitySchedule.objects.filter(primary_entity_id=appliance_id,
                                                schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                activity_type__in=[IopOptionsEnums.RECURRING_SLEEP_MODE,
                                                                   IopOptionsEnums.IOP_SLEEP_MODE]).order_by(
        'new_start_dt')

    result = []

    for sch in schedules:

        day = calendar.day_name[int(sch.u_days_list)]
        if not any(d['day'] == day for d in result):
            result.append({'day': day,
                           'events': list(schedules.filter(u_days_list=sch.u_days_list).values('id', start_time=F(
                               'u_activity_start_time'), end_time=F('u_activity_end_time')))})

    response_body[const.RESPONSE_STATUS] = const.HTTP_SUCCESS_CODE
    response_body[const.RESPONSE_MESSAGE] = const.TEXT_OPERATION_SUCCESSFUL
    response_body[const.RESPONSE_DATA] = result

    return h_utils.generic_response(response_body, http_status)
