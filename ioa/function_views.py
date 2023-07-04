import datetime as dt
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
import hypernet.utils as h_utils
from hypernet.utils import generic_response, get_user_from_request, get_default_param, \
    verify_request_params, get_customer_from_request, get_module_from_request
from ioa.utils import *



@csrf_exempt
@api_view(['GET'])
# @verify_request_params(params=["customer"])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_alerts_count(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    user = get_user_from_request(request, None)
    # c_id = get_default_param(request, "customer", None)
    c_id = get_customer_from_request(request, None)
    animal = get_default_param(request, "animal", None)
    time = dt.date.today() - timedelta(days=float(get_default_param(request, "days", LAST_WEEK)))
    response_body[RESPONSE_DATA] = get_alerts(c_id=c_id, days=time, a_id=animal)
    # response_body[RESPONSE_DATA]['User'] = str(user)
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_recent_alerts_pi(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    time = dt.date.today() - timedelta(days=float(self.query_params.get("days", LAST_WEEK)))
    # q_customer_id = self.query_params["customer"]
    q_customer_id = get_customer_from_request(self, None)
    response_body[RESPONSE_DATA] = list(get_alerts_recent(customer_id=q_customer_id, date_range=time))
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_recent_alerts_detail(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    # user = get_user_from_request(self, None)
    # module_id = get_module_from_request(self, None)
    animal_id = self.query_params.get('animal')
    customer_id = get_customer_from_request(self, None)
    herd_id = self.query_params.get('herd')
    alert_status = self.query_params.get('status')
    limit = int(self.query_params.get('limit', RECENT_DATA))
    recent_alerts = util_get_recent_alerts(customer_id=customer_id, animal_id=animal_id, herd_id=herd_id,
                                           no_alerts=limit, status=alert_status)

    activity_type = Options.objects.get(key=ACTIVITY_TYPE, value=INSPECTION)
    alert_action = {'activity_type': activity_type.label,
                    'activity_type_id': activity_type.id}

    for alert in recent_alerts:
        alert_dict = alert.animal_alert_to_dict()
        if alert_dict:
            alert_dict.update(alert_action)
            response_body[RESPONSE_DATA].append(alert_dict)
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_alert_graph_data(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    # customer_id = self.query_params['customer']
    customer_id = get_customer_from_request(self, None)
    days = self.query_params.get('days', LAST_WEEK)
    group_by = self.query_params.get('group_by')
    group_by, days = ("%H", days) if group_by == "hour" else (GRAPH_DATE_FORMAT, days)
    from_date = dt.date.today() - timedelta(int(days))
    response_body[RESPONSE_DATA] = util_get_alerts_data_modified(customer_id, from_date, group_by)
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_herds_list(self):
    from random import randint
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    customer = self.query_params["customer"]
    for i in range(5, 11):
        response_body[RESPONSE_DATA].append(
            {
                "id": i,
                "name": "Name "+str(i),
                "cows": i*10,
                "heifers": randint(10, 15),
                "calves": randint(10, 15),
                "in lactation": randint(10, 15)
            }
        )
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@verify_request_params(params=['customer'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_scheduling_form_data(self):
    from hypernet.entity.utils import util_get_entity_dropdown
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: {}}
    customer = self.query_params["customer"]
    herd = self.query_params.get("herd")
    response_body[RESPONSE_DATA]['herd'] = (
        list(util_get_entity_dropdown(c_id=customer, entity_type=DeviceTypeEntityEnum.HERD)))
    response_body[RESPONSE_DATA]['animals'] = (list(get_herd_animal_ids(herd_id=herd)))
    response_body[RESPONSE_DATA]['staff'] = (list(get_all_staff(c_id=customer)))
    # REFACTOR THE option_key according to constants
    response_body[RESPONSE_DATA]['activity_type'] = (list(options_data(options_key='ioa_activity_type')))
    response_body[RESPONSE_DATA]['activity_routine_type'] = (list(options_data(options_key='ioa_routine_type')))
    response_body[RESPONSE_DATA]['activity_priority'] = (list(options_data(options_key='ioa_activity_priority')))
    return generic_response(response_body=response_body, http_status=200)


# @csrf_exempt
# @api_view(['GET'])
# @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
# def ignore_alert(self):
#     response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
#     pk = self.query_params['pk']
#     customer_id = self.query_params['customer']
#     response_body[RESPONSE_DATA] = update_alert_status(id=pk, c_id=customer_id, flag_is_viewed=False, status=None)
#     return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_alert_count_by_type(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    time = dt.date.today() - timedelta(days=float(self.query_params.get("days")))
    alert_name = self.query_params.get("alert")
    # c_id = self.query_params["customer"]
    c_id = get_customer_from_request(self, None)
    response_body[RESPONSE_DATA] = list(get_alerts_by_type(customer_id=c_id, s_date=time, alert_type=alert_name))
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['PATCH'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def update_alert_flag(request):
    from hypernet.notifications.utils import update_alert_flag_status
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    user = get_user_from_request(request, None).id
    customer = get_customer_from_request(request, None)
    module_id = get_module_from_request(request, None)
    update_status = update_alert_flag_status(u_id=user, c_id=customer, m_id=module_id)
    if update_status:
        response_body[RESPONSE_DATA] = TEXT_OPERATION_SUCCESSFUL
    else:
        response_body[RESPONSE_DATA] = DEFAULT_ERROR_MESSAGE
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_user_notifications(request):
    from hypernet.notifications.utils import util_user_notifications
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    user = get_user_from_request(request, None)
    customer = get_customer_from_request(request, None)
    module_id = get_module_from_request(request, None)
    response_body[RESPONSE_DATA] = util_user_notifications(u_id=user, c_id=customer, m_id=int(module_id))
    return generic_response(response_body=response_body, http_status=200)


# TODO Remove this API (Use from Hypernet Instead)
@csrf_exempt
@api_view(['PATCH'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def update_alerts_status(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    pk = request.data["pk"]
    customer = get_customer_from_request(request, None)
    module_id = get_module_from_request(request, None)
    status = request.data["status"]
    update_status = update_alert_status(id=pk, c_id=customer, status=status, m_id=module_id)
    print(update_status)
    if update_status:
        response_body[RESPONSE_DATA] = TEXT_OPERATION_SUCCESSFUL
    else:
        response_body[RESPONSE_DATA] = DEFAULT_ERROR_MESSAGE
    return generic_response(response_body=response_body, http_status=200)
