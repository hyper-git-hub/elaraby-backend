from .utils import *
import hypernet.utils as h_utils
from hypernet.constants import *
from hypernet.utils import exception_handler, generic_response
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view


@csrf_exempt
@api_view(['PATCH'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def update_alert_flag(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    user = h_utils.get_user_from_request(request, None).id
    print(user)
    customer = h_utils.get_customer_from_request(request, None)
    module_id =  h_utils.get_module_from_request(request, None)
    update_status = update_alert_flag_status(u_id=user, c_id=customer, m_id=module_id)
    if update_status is True:
        response_body[RESPONSE_DATA] = TEXT_OPERATION_SUCCESSFUL
    else:
        response_body[RESPONSE_DATA] = DEFAULT_ERROR_MESSAGE
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_user_notifications(request):
    import hypernet.utils as h_utils
    #response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    user = h_utils.get_user_from_request(request, None)
    customer = h_utils.get_customer_from_request(request, None)
    module_id = h_utils.get_module_from_request(request, None)
    result = util_user_notifications(u_id=user, c_id=customer, m_id=int(module_id))
    http_status = 200
    return generic_response(h_utils.response_json(http_status, result))





@csrf_exempt
@api_view(['PATCH'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def update_alert_status(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    alert_id = request.data["alert_id"]
    c_id = request.data["customer"]
    status_id = request.data["status"]
    is_viewed = request.data["is_viewed"]
    if status_id:
        update_status = update_alert_status(id=alert_id, c_id=c_id, status=status_id, flag_is_viewed=is_viewed)
        if update_status:
            response_body[RESPONSE_DATA] = TEXT_OPERATION_SUCCESSFUL
        else:
            response_body[RESPONSE_DATA] = DEFAULT_ERROR_MESSAGE
    else:
        response_body[RESPONSE_DATA] = TEXT_PARAMS_INCORRECT
    return generic_response(response_body=response_body, http_status=200)
