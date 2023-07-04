import itertools

from datetime import timedelta
from django.db import transaction
from rest_framework.decorators import api_view
from django.utils import timezone

import hypernet.utils as h_utils
from ffp.cron_utils import get_durations_site, daily_averages_ffp, get_active_hours_site
from ffp.models import Tasks, EmployeeViolations
from ffp.reporting_utils import util_get_tasks_employees, util_get_tasks, get_zones_of_site, \
    get_site_or_zone_of_supervisor, get_zones_list, util_get_task_rate, util_get_task_line_graph_data_site, \
    util_get_task_line_graph_data_zone, util_get_productivity_data_site
from ffp.serializers import TaskSerializer
from hypernet.constants import ERROR_RESPONSE_BODY, HTTP_ERROR_CODE, HTTP_SUCCESS_CODE, RESPONSE_MESSAGE, \
    RESPONSE_STATUS, RESPONSE_DATA, TEXT_SUCCESSFUL, TEXT_PARAMS_MISSING, GRAPH_DATE_FORMAT, \
    TEXT_OPERATION_UNSUCCESSFUL, TEXT_OPERATION_SUCCESSFUL
from hypernet.cron_task import process_logistics_ffp_data
from hypernet.enums import OptionsEnum, IOFOptionsEnum, FFPOptionsEnum
from hypernet.models import Assignment
from hypernet.notifications.utils import send_notification_violations
from user.models import User


@transaction.atomic()
@api_view(['POST', 'PATCH'])
@h_utils.exception_handler(h_utils.generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def add_tasks(request):
    response_body = {RESPONSE_MESSAGE: TEXT_SUCCESSFUL, RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: {}}
    http_status = HTTP_SUCCESS_CODE
    # user = h_utils.get_user_from_request(request, None)
    user_ent = h_utils.get_user_from_request(request, None).associated_entity
    if user_ent:
        site = get_site_or_zone_of_supervisor(s_sup_id=user_ent).id
    else:
        site = None

    request.POST._mutable = True
    request.data['customer'] = h_utils.get_customer_from_request(request, None)
    request.data['module'] = h_utils.get_module_from_request(request, None)
    request.data['responsible'] = h_utils.get_user_from_request(request, None).associated_entity_id
    request.data['task_status'] = IOFOptionsEnum.PENDING
    request.data['site'] = site if site else request.data.get('site')
    request.data['modified_by'] = h_utils.get_user_from_request(request,None).id
    request.POST._mutable = False

    serializer = TaskSerializer(data=request.data, partial=True, context={'request': request})

    if serializer.is_valid():
        serializer.save()
        title = "You have been assigned: \n"+ str(serializer.data.get('title')) if serializer.data.get('title') else None
        try:
            user = User.objects.get(associated_entity=serializer.data.get('assignee'))
        except:
            user = None

        if user:
            send_notification_violations(device=serializer.data.get('assignee'),driver_id=None,
                                         customer_id=serializer.data.get('customer'), module_id=serializer.data.get('module'),
                                         title=title, users_list=[user])

        return h_utils.generic_response(response_body=response_body, http_status=http_status)

    else:
        response_body[RESPONSE_MESSAGE] = h_utils.error_message_serializers(serializer.errors)
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
        return h_utils.generic_response(response_body=response_body, http_status=http_status)


@transaction.atomic()
@api_view(['POST', 'PATCH'])
@h_utils.exception_handler(h_utils.generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def edit_tasks(request):
    response_body = {RESPONSE_MESSAGE: TEXT_SUCCESSFUL, RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: {}}
    http_status = HTTP_SUCCESS_CODE
    task_id = int(h_utils.get_data_param(request, 'task_id', 0))
    try:
        task = Tasks.objects.get(pk=task_id)
    except:
        task = None

    if task:
        serializer = TaskSerializer(task, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            title = "You have been assigned or your previous task is modified by the supervisor: \n"+serializer.data.get('title')
            try:
                user = User.objects.get(associated_entity=serializer.data.get('assignee'))
            except:
                user = None

            if user:
                send_notification_violations(device=serializer.data.get('assignee'),driver_id=None,
                                             customer_id=serializer.data.get('customer'), module_id=serializer.data.get('module'),
                                             title=title, users_list=[user])

            return h_utils.generic_response(response_body=response_body, http_status=http_status)
        else:
            response_body[RESPONSE_MESSAGE] = h_utils.error_message_serializers(serializer.errors)
            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
            return h_utils.generic_response(response_body=response_body, http_status=http_status)
    else:
        response_body[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
        return h_utils.generic_response(response_body=response_body, http_status=http_status)


@transaction.atomic()
@api_view(['POST', 'PATCH'])
@h_utils.exception_handler(h_utils.generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def delete_tasks(request):
    response_body = {RESPONSE_MESSAGE: TEXT_SUCCESSFUL, RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: {}}
    http_status = HTTP_SUCCESS_CODE
    task_id_list = h_utils.get_data_param(request, 'id_list', None)

    if task_id_list:
        for task_id in task_id_list:
            try:
                task = Tasks.objects.get(pk=task_id)
                task.delete()
            except:
                response_body[RESPONSE_MESSAGE] = "The record you're trying delete is invalid or no longer exists"
                response_body[RESPONSE_DATA] = task_id
                response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                return h_utils.generic_response(response_body=response_body, http_status=http_status)

        return h_utils.generic_response(response_body=response_body, http_status=http_status)

    else:
        response_body[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
        return h_utils.generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@h_utils.exception_handler(h_utils.generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def get_tasks(request):
    response_body = {RESPONSE_MESSAGE: TEXT_SUCCESSFUL, RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: {}}
    http_status = HTTP_SUCCESS_CODE
    user = h_utils.get_user_from_request(request, None)
    site = h_utils.get_default_param(request, 'site_id', None)
    zone = h_utils.get_default_param(request, 'zone_id', None)
    employee = h_utils.get_default_param(request, 'employee_id', None)

    if user or employee:
        response_body[RESPONSE_MESSAGE] = TEXT_SUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        response_body[RESPONSE_DATA] = util_get_tasks(loged_user=user, employee=employee)
        return h_utils.generic_response(response_body=response_body, http_status=http_status)

    else:
        response_body[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
        response_body[RESPONSE_DATA] = None
        return h_utils.generic_response(response_body=response_body, http_status=http_status)


@transaction.atomic()
@api_view(['POST', 'PATCH'])
@h_utils.exception_handler(h_utils.generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def update_task_status(request):
    response_body = {RESPONSE_MESSAGE: TEXT_SUCCESSFUL, RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: {}}
    http_status = HTTP_SUCCESS_CODE
    task_id = h_utils.get_data_param(request, 'task_id', None)
    logged_in_user = h_utils.get_user_from_request(request, None)
    task_status = h_utils.get_data_param(request, 'type', None)

    if task_id:
        try:
            task = Tasks.objects.get(pk=task_id)
            if task_status == FFPOptionsEnum.TASK_APPROVED and task.responsible == logged_in_user.associated_entity:
                task.task_status_id = FFPOptionsEnum.TASK_COMPLETED
                task.approved = True
                task.save()
                response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE

            elif task_status == FFPOptionsEnum.TASK_COMPLETED and task.assignee == logged_in_user.associated_entity:
                task.task_status_id = FFPOptionsEnum.TASK_COMPLETED
                task.save()
                response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE

            else:
                response_body[RESPONSE_MESSAGE] = "You don't have previliges to modify this record."
                response_body[RESPONSE_DATA] = task_id
                response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                return h_utils.generic_response(response_body=response_body, http_status=http_status)

            response_body[RESPONSE_MESSAGE] = "Your Task is updated succesfully"
            return h_utils.generic_response(response_body=response_body, http_status=http_status)

        except:
            response_body[RESPONSE_MESSAGE] = "The record you're trying delete is invalid or no longer exists"
            response_body[RESPONSE_DATA] = task_id
            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
            return h_utils.generic_response(response_body=response_body, http_status=http_status)

    else:
        response_body[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
        return h_utils.generic_response(response_body=response_body, http_status=http_status)



@api_view(['GET'])
@h_utils.exception_handler(h_utils.generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def employee_dropdown(request):
    response_body = {RESPONSE_MESSAGE: TEXT_SUCCESSFUL, RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
    http_status = HTTP_SUCCESS_CODE
    user = h_utils.get_user_from_request(request, None)

    if user:
        response_body[RESPONSE_DATA] = util_get_tasks_employees(loged_user=user)
        response_body[RESPONSE_MESSAGE] = TEXT_SUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE

    else:
        response_body[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
    return h_utils.generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@h_utils.exception_handler(h_utils.generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def zone_dropdown(request):
    response_body = {RESPONSE_MESSAGE: TEXT_SUCCESSFUL, RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
    http_status = HTTP_SUCCESS_CODE
    user = h_utils.get_user_from_request(request, None)

    if user.associated_entity:
        response_body[RESPONSE_DATA] = list(get_zones_of_site(s_sup_id=user.associated_entity_id))
        response_body[RESPONSE_MESSAGE] = TEXT_SUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    else:
        response_body[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
    return h_utils.generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@h_utils.exception_handler(h_utils.generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def assigned_zone_dropdown(request):
    response_body = {RESPONSE_MESSAGE: TEXT_SUCCESSFUL, RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
    http_status = HTTP_SUCCESS_CODE
    user = h_utils.get_user_from_request(request, None)
    c_id = h_utils.get_customer_from_request(request, None)
    ent_id = h_utils.get_default_param(request, 'entity_id', None)

    if user.associated_entity:
        response_body[RESPONSE_DATA] = get_zones_list(customer=c_id, entity_id=ent_id)
        response_body[RESPONSE_MESSAGE] = TEXT_SUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    else:
        response_body[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
    return h_utils.generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@h_utils.exception_handler(h_utils.generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def get_task_rate(request):
    response_body = {RESPONSE_MESSAGE: TEXT_SUCCESSFUL, RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: {}}
    http_status = HTTP_SUCCESS_CODE
    user = h_utils.get_user_from_request(request, None)
    site = h_utils.get_default_param(request, 'site', None)
    zone = h_utils.get_default_param(request, 'zone', None)
    employee = h_utils.get_default_param(request, 'employee_id', None)
    s_date = h_utils.get_default_param(request, 'start_date', None)
    e_date = h_utils.get_default_param(request, 'end_date', None)
    group_by = h_utils.get_default_param(request, 'group_by', None)
    task_status = h_utils.get_default_param(request, 'status', None)
    group_by = "%H" if group_by == "hour" else GRAPH_DATE_FORMAT

    tasks_total = util_get_task_rate(loged_user=user, site=site, zone=zone, employee=employee, s_date=s_date, e_date=e_date, st_id=None)
    completed_tasks = util_get_task_rate(loged_user=user, site=site, zone=zone, employee=employee, s_date=s_date,
                                     e_date=e_date, st_id=IOFOptionsEnum.COMPLETED)
    if site:
        graphical_tasks = util_get_task_line_graph_data_zone(group_by=group_by, q_set=tasks_total)
    else:
        graphical_tasks = util_get_task_line_graph_data_site(group_by=group_by, q_set=tasks_total)

    if site:
        graphical_tasks_completed = util_get_task_line_graph_data_zone(group_by=group_by, q_set=completed_tasks)
    else:
        graphical_tasks_completed = util_get_task_line_graph_data_site(group_by=group_by, q_set=completed_tasks)

    response_body[RESPONSE_DATA]['total_tasks'] = graphical_tasks
    response_body[RESPONSE_DATA]['completed_tasks'] = graphical_tasks_completed
    response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
    response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE

    # daily_averages_ffp()

    return h_utils.generic_response(response_body=response_body, http_status=http_status)



@api_view(['GET'])
@h_utils.exception_handler(h_utils.generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def get_productivity_percentage(request):
    response_body = {RESPONSE_MESSAGE: TEXT_SUCCESSFUL, RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: {}}
    http_status = HTTP_SUCCESS_CODE
    user = h_utils.get_user_from_request(request, None)
    site = h_utils.get_default_param(request, 'site', None)
    zone = h_utils.get_default_param(request, 'zone', None)
    group_by = h_utils.get_default_param(request, 'group_by', None)
    group_by = "%H" if group_by == "hour" else GRAPH_DATE_FORMAT

    last_week = timezone.now() - timedelta(days=7)

    if site:
        productivity = util_get_productivity_data_site(group_by=group_by, site_id=site, last_week=last_week)
        response_body[RESPONSE_DATA] = productivity
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE

    else:
        response_body[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE

    return h_utils.generic_response(response_body=response_body, http_status=http_status)
