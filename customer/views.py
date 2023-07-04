from rest_framework.decorators import api_view
from customer.serializers import CustomerPreferencesSerializer
from hypernet.constants import ERROR_RESPONSE_BODY, HTTP_ERROR_CODE, RESPONSE_DATA, STATUS_ERROR, RESPONSE_STATUS, \
    TEXT_PARAMS_MISSING, RESPONSE_MESSAGE, HTTP_SUCCESS_CODE, STATUS_OK, TEXT_OPERATION_SUCCESSFUL, \
    TEXT_OPERATION_UNSUCCESSFUL
from hypernet.utils import exception_handler, generic_response, get_customer_from_request, get_default_param, \
    get_data_param
from iof.utils import check_activities_to_be_performed
from .models import CustomerPreferences

# Create your views here.

@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def get_preferences(request):
    customer = int(get_customer_from_request(request, 0))

    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: HTTP_ERROR_CODE, RESPONSE_DATA: []}
    http_status = HTTP_ERROR_CODE

    resp_dict = {}
    resp_list = []
    if customer:
        c_pref = CustomerPreferences.objects.filter(customer_id=customer)

        for obj in c_pref:
            serializer = CustomerPreferencesSerializer(obj, partial=True, context={'request': request})
            resp_dict = serializer.data
            resp_list.append(resp_dict)

        response_body[RESPONSE_MESSAGE] = {'success_message': TEXT_OPERATION_SUCCESSFUL}
        http_status = HTTP_SUCCESS_CODE
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        response_body[RESPONSE_DATA] = resp_list

    else:
        response_body[RESPONSE_MESSAGE] = {'error_message': TEXT_PARAMS_MISSING}
        http_status = HTTP_SUCCESS_CODE
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
        response_body[RESPONSE_DATA] = resp_list

    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['PATCH'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def modify_preferences(request):
    customer = int(get_customer_from_request(request, 0))
    pref_id = get_data_param(request, 'id', None)
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: HTTP_ERROR_CODE, RESPONSE_DATA: []}
    http_status = HTTP_SUCCESS_CODE

    resp_dict = {}
    resp_list = []
    if pref_id:
        if not check_activities_to_be_performed(customer):
            c_pref = CustomerPreferences.objects.filter(customer_id=customer, id=int(pref_id))
    
            for obj in c_pref:
                serializer = CustomerPreferencesSerializer(obj,data= request.data, partial=True, context={'request': request})
                if serializer.is_valid():
                    serializer.save()
                    resp_dict = serializer.data
                    resp_list.append(resp_dict)
    
                    response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
                    http_status = HTTP_SUCCESS_CODE
                    response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
                    response_body[RESPONSE_DATA] = resp_list
    
                else:
                    error_list = []
                    for errors in serializer.errors:
                        error_list.append("invalid  " + errors + "  given.")
                    # response_body[RESPONSE_MESSAGE] = error_list
                    print(error_list)
    
                    response_body[RESPONSE_MESSAGE] =  error_list
                    response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                    response_body[RESPONSE_DATA] = resp_list
        else:
            response_body[RESPONSE_MESSAGE] = "Cannot Update preferences when there are activities to be performed." \
                                              "\nNote: This is a fail-safe feature in order to avoid un-wanted behavior in schedules and activities."
            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
            response_body[RESPONSE_DATA] = resp_list
    else:
        response_body[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
        response_body[RESPONSE_DATA] = resp_list

    return generic_response(response_body=response_body, http_status=http_status)
