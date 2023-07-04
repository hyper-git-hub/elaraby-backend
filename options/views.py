from django.db.models import F
from django.http import JsonResponse
from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import AllowAny

from hypernet.constants import RESPONSE_MESSAGE, RESPONSE_STATUS, STATUS_OK, RESPONSE_DATA, HTTP_SUCCESS_CODE, \
    HTTP_ERROR_CODE, ERROR_RESPONSE_BODY
from .models import Options
from rest_framework.views import *
from hypernet.utils import generic_response, get_default_param, get_user_from_request



class OptionsAll(APIView):
    permission_classes = (AllowAny,)
    
    def get(self, request):
        option_key = get_default_param(request, 'option_key', None)
        response_body = {RESPONSE_MESSAGE: "options", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: {}}
        queryset = Options.objects.filter(key=option_key).values('id', 'label')
        response_body[RESPONSE_DATA]['option_values'] = list(queryset)
        return generic_response(response_body=response_body, http_status=200)


class OptionsKeys(APIView):
    
    def get(self, request):
        user = get_user_from_request(request, None)
        response_body = {RESPONSE_MESSAGE: "options", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: {}}
        data = Options.objects.filter(module=user.preferred_module).values('key', ).distinct()
        response_body[RESPONSE_DATA]['option_keys'] = list(data)
        return generic_response(response_body=response_body, http_status=200)
