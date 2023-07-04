from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from hypernet.utils import generic_response, get_customer_from_request
from ioa.utils import *
from ioa.serializer import *

class UserViews(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
        serializer = IoaCaretakerSerializer(data=request.data)  # , partial=True)
        if serializer.is_valid():
            serializer.save()
            user_obj = User.objects.filter(email=serializer.data['email'])[0]
            resp_serializer = UserDataSerializer(user_obj, partial=True, context={'request': request})
            response_body[RESPONSE_DATA] = resp_serializer.data
            response_body[RESPONSE_STATUS] = STATUS_OK
            return generic_response(response_body=response_body, http_status=200)
        elif serializer.errors:
            error_list = []
            for errors in serializer.errors:
                error_list.append("invalid  " + errors + "  given.")
            response_body[RESPONSE_MESSAGE] = error_list
            response_body[RESPONSE_STATUS] = STATUS_ERROR
        return generic_response(response_body=response_body, http_status=400)

    def patch(self, request):
        response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
        pk = get_data_param(request, 'pk', None)
        user_obj = User.objects.filter(pk=pk)[0]
        if user_obj:
            serializer = IoaCaretakerSerializer(user_obj, data=request.data, partial=True, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                resp_serializer = UserDataSerializer(user_obj, partial=True, context={'request': request})
                response_body[RESPONSE_DATA] = resp_serializer.data
                response_body[RESPONSE_STATUS] = STATUS_OK
                return generic_response(response_body=response_body, http_status=200)
            elif serializer.errors:
                error_list = []
                for errors in serializer.errors:
                    error_list.append("invalid  " + errors + "  given.")
                response_body[RESPONSE_MESSAGE] = error_list
                response_body[RESPONSE_STATUS] = STATUS_ERROR
            return generic_response(response_body=response_body, http_status=403)

class CaretakerLogin(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
        email = request.POST.get('email')
        password = request.POST.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if user:
                token = Token.objects.get_or_create(user=user)
                user_details = CaretakerLoginSerializer(user)
                user_data = user_details.data
                token_key = token[0].key
                response_body[RESPONSE_DATA] = {"Login Successful": user_data,
                                                "Token": token_key}
                return generic_response(response_body=response_body, http_status=200)
        return generic_response(response_body="Error Invalid Credentials were provided", http_status=400)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_staff_list(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: {}}
    # customer = self.query_params["customer"]
    customer = get_customer_from_request(self, None)
    animal_id = self.query_params.get('animal')
    staff_id = self.query_params.get('staff')
    response_body[RESPONSE_DATA]['staff_list'] = get_staff_detail(c_id=customer, staff=staff_id)
    response_body[RESPONSE_DATA]['staff_recent_activites'] = get_complete_activities(customer, animal_id, staff_id)
    response_body[RESPONSE_DATA].update(util_staff_total(c_id=customer))
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_staff_dropdown(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    customer = self.query_params["customer"]
    response_body[RESPONSE_DATA] = util_get_caretakers(c_id=customer)
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_staff_roles(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    response_body[RESPONSE_DATA] = util_get_roles()
    return generic_response(response_body=response_body, http_status=200)
