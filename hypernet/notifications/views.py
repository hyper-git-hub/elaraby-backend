from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view

from .utils import *
import hypernet.utils as h_utils
from hypernet.constants import *
from hypernet.utils import exception_handler, generic_response

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


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def update_notifications_count(request):
    response = {RESPONSE_STATUS: STATUS_OK, RESPONSE_MESSAGE: "", RESPONSE_DATA: []}
    user = h_utils.get_user_from_request(request, None)
    c_id = h_utils.get_customer_from_request(request, None)
    m_id = h_utils.get_module_from_request(request, None)
    u_id = h_utils.get_user_from_request(request, None).id
    http_status = HTTP_SUCCESS_CODE
    if user:
        try:
            firebase = pyrebase.initialize_app(settings.config_firebase)
            db = firebase.database()

        except:  # TODO Find Exception sets of FireBase Connections.
            traceback.print_exc()
            db = None

        if db:
            try:
                db.child(str(user.email).replace('.', '-')).set(0)
                alert_status = update_alert_flag_status(u_id, c_id, m_id)
                response[RESPONSE_MESSAGE] = TEXT_SUCCESSFUL
                response[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
                return generic_response(response_body=response, http_status=http_status)

            except:
                traceback.print_exc()
                response[RESPONSE_MESSAGE] = USER_DOES_NOT_EXIST
                response[RESPONSE_STATUS] = HTTP_ERROR_CODE
                return generic_response(response_body=response, http_status=http_status)

    else:
        response[RESPONSE_MESSAGE] = NOT_ALLOWED
        response[RESPONSE_STATUS] = HTTP_ERROR_CODE
        return generic_response(response_body=response, http_status=http_status)
