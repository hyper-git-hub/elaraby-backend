'''
import random
import sys
import time

from django.views.decorators.csrf import csrf_exempt
from iothub_service_client import IoTHubMessaging, IoTHubMessage, IoTHubError
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny

from hypernet.constants import ERROR_RESPONSE_BODY, RESPONSE_STATUS, HTTP_SUCCESS_CODE, RESPONSE_DATA, RESPONSE_MESSAGE, \
    HTTP_ERROR_CODE
from hypernet.utils import exception_handler, generic_response, get_data_param

OPEN_CONTEXT = 0
FEEDBACK_CONTEXT = 1
MESSAGE_COUNT = 1
AVG_WIND_SPEED = 10.0
# MSG_TXT = "{\"service client sent a message\": %.2f}"


CONNECTION_STRING = "HostName=Askar-output.azure-devices.net;SharedAccessKeyName=iothubowner;SharedAccessKey=wNQXeNiUg9NgN/xx9B1qaSm9IHqcgYTN9Ao2mlKInzs="
# DEVICE_ID = "homeAppliances-testDevice1"



def open_complete_callback(context):
    print ( 'open_complete_callback called with context: {0}'.format(context) )


def send_complete_callback(context, messaging_result):
    context = 0
    print ( 'send_complete_callback called with context : {0}'.format(context))
    print ( 'messagingResult : {0}'.format(messaging_result))


def iothub_cloud_to_device_messaging(MSG_TXT=None, DEVICE_ID=None):
    try:
        iothub_messaging = IoTHubMessaging(CONNECTION_STRING)
        iothub_messaging.open(open_complete_callback, OPEN_CONTEXT)

        message = IoTHubMessage(bytearray(MSG_TXT, 'utf8'))
        iothub_messaging.send_async(DEVICE_ID, message, send_complete_callback, None)
        time.sleep(4)
        iothub_messaging.close()

        return True

    except IoTHubError as iothub_error:
        print ("Unexpected error {0}" % iothub_error)
        return False
    except KeyboardInterrupt:
        print ("IoTHubMessaging sample stopped")



@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny,])
@authentication_classes(())
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def send_message_to_device_api(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
    device_id = get_data_param(request, 'device_id', None)
    message = get_data_param(request, 'message', None)

    if device_id:
        status = iothub_cloud_to_device_messaging(MSG_TXT=message, DEVICE_ID=device_id)
        if status:
            response_body[RESPONSE_MESSAGE] = "message sent to device."
            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        else:
            response_body[RESPONSE_MESSAGE] = "connection to device device failed, try again."
            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE

    return generic_response(response_body=response_body, http_status=HTTP_SUCCESS_CODE)
'''