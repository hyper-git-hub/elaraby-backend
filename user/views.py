import datetime
import json
import os
import random
import string
import invitations
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password
from rest_framework.decorators import api_view, permission_classes

from email_manager.email_util import extended_email_with_title
from hypernet.constants import ERROR_RESPONSE_BODY, HTTP_ERROR_CODE, RESPONSE_MESSAGE, TEXT_PARAMS_MISSING, \
    RESPONSE_STATUS, STATUS_ERROR, RESPONSE_DATA, STATUS_OK, HTTP_SUCCESS_CODE, TEXT_OPERATION_SUCCESSFUL, \
    EMAIL_FORGOT_PASSWORD_MESSAGE
from hypernet.enums import OptionsEnum
from hypernet.utils import get_data_param, response_json, exception_handler, generic_response, \
    get_customer_from_request, get_user_from_request, get_default_param, get_module_from_request
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import IntegrityError
from django.http import HttpResponse
from django.http import QueryDict
from django.shortcuts import get_object_or_404
from django.template import loader
from django.views.generic import View
from rest_framework.authtoken.models import Token
from rest_framework.generics import (
    CreateAPIView
)
from rest_framework.permissions import (
    AllowAny,
    IsAdminUser,
    IsAuthenticated)
from rest_framework.response import Response
from rest_framework.status import HTTP_409_CONFLICT
from rest_framework.views import APIView
from customer.serializers import CustomerListSerializer
from hypernet import constants
from user.enums import RoleTypeEnum
from user.utils import user_reset_verify, reset_user_token_reset
from .models import User, ModuleAssignment
from .permissions import IsAdminOrReadOnly
# Create your views here.

# from posts.api.permissions import IsOwnerOrReadOnly
# from posts.api.pagination import PostLimitOffsetPagination, PostPageNumberPagination


User = get_user_model()

from .serializers import (
    UserCreateSerializer,
    UserLoginSerializer,
    InvitationCreateSerializer,
    UserSerializer)


class UserInviteAPIView(CreateAPIView):
    serializer_class = InvitationCreateSerializer
    queryset = invitations.models.Invitation.objects.all()
    permission_classes = [IsAdminUser]

    def send(self, request):
        invite = invitations.model.Invitation.create(request.data.email, inviter=request.data.user)
        invite.send_invitation(request)


class UserCreateAPIView(CreateAPIView):
    """
    Registers a User. Requires Username, Password and Email.
    """
    serializer_class = UserCreateSerializer
    queryset = User.objects.all()
    permission_classes = [AllowAny]


# class UserLoginAPIView(APIView):
#     """
#     Logs a User in provided correct credentials including Username, Password and Email.
#     """
#     permission_classes = [AllowAny]
#     serializer_class = UserLoginSerializer
#
#     def post(self, request, *args, **kwargs):
#         data = request.data
#         serializer = UserLoginSerializer(data=data)
#         if serializer.is_valid(raise_exception=True):
#             # pdb.set_trace()
#             # new_data = serializer.data
#             user_obj = User.objects.get(email=data['email'])
#             user = authenticate(username = user_obj.email, password = data['password'])
#             new_data = dict()
#             new_data["email"] = user_obj.email
#             new_data["customer"] = user_obj.customer.name
#             try:
#                 new_data["fleet_count"] = user_obj.customer.fleet_set.count()
#             except AttributeError as e:
#                 new_data["fleet_count"] = None
#             try:
#                 new_data["depot_count"] = user_obj.customer.depot_set.count()
#             except AttributeError as e:
#                 new_data["depot_count"] = None
#             print(new_data)
#             if user is not None:
#                 login(request, user)
#             return Response(new_data, status=HTTP_200_OK)
#         return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class UserLoginAPIView(APIView):
    # soban
    permission_classes = [AllowAny]

    """
    @api {post} /api/users/login/ User login
    @apiName Login User
    @apiGroup User
    @apiDescription Return user and token

    @apiParam {String} email 
    @apiParam {String} password
    """

    def post(self, request):
        email = get_data_param(request, 'email', None)
        password = get_data_param(request, 'password', None)
        push_key = get_data_param(request, 'push_key', None)
        if email and password:
            user = authenticate(username=email, password=password)
            if user:
                token = Token.objects.get_or_create(user=user)
                user_serializer = UserLoginSerializer(user)
                user_modules = ModuleAssignment.objects.filter(customer=user.customer)
                customer_serializer = CustomerListSerializer(user.customer)
                data = user_serializer.data
                data['customer'] = customer_serializer.data
                data['token'] = token[0].key
                data['user_role_id'] = None if not user.role else user.role.id
                data['user_role_name'] = None if not user.role else user.role.name
                data['avatar'] = None if not user.avatar else request.build_absolute_uri(user.avatar.url)
                data['module'] = [user_module.module.as_json_module() for user_module in user_modules]
                if push_key:
                    user.one_signal_device_id = push_key
                    user.save()
                return Response(response_json(200, data, None))     #TODO: Will be removed later.
            return Response(response_json(500, None, 'Wrong username or password'))
        return Response(response_json(500, None, constants.TEXT_PARAMS_MISSING))


class UsersAPIView(View):
    def get(self, request):
        # ========================================
        # add generic filter instead of 'trucks'
        # ========================================
        try:
            user = request.user
            team = []
            team_dict = dict()
            queryset = user.info.customer.info_set.all()
            for q in queryset:
                t = dict()
                t["email"] = q.user.email
                t["id"] = q.user.id
                t["username"] = q.user.username
                team.append(json.dumps(t))
            team_dict["team"] = team
        except Exception as e:
            print(e, type(e))

        return HttpResponse(json.dumps(team_dict), content_type="application/json")

    def post(self, request):

        user_id = None
        try:
            user = User.objects.create_user(username=request.POST["username"],
                                            email=request.POST["email"],
                                            password=request.POST["password"])
            user.info = User()
            user.info.customer = request.user.info.customer
            user.info.designation = 'Manager'
            user.info.save()
            user_id = user.id
        except IntegrityError:
            return HttpResponse(content="User with name already exists", status=HTTP_409_CONFLICT)
        except Exception as e:
            print(e, type(e))

        return HttpResponse(content="User created successfully with id " + str(user_id), status=201)


class UserAPIView(View):
    def get(self, request, user_id):
        # ========================================
        # add generic filter instead of 'trucks'
        # ========================================
        user = get_object_or_404(User, pk=user_id)
        try:
            request_user = request.user
            u = dict()
            if user.info.customer == request_user.info.customer:
                u["email"] = user.email
                u["id"] = user.id
                u["username"] = user.username
        except Exception as e:
            print(e, type(e))

        return HttpResponse(json.dumps(u), content_type="application/json")

    def put(self, request, user_id):

        user = get_object_or_404(User, pk=user_id)
        try:
            request_user = request.user
            data = QueryDict(request.body)
            if "username" in data:
                user.username = data["username"]
            if "email" in data:
                user.email = data["email"]
            if "password" in data:
                user.password = data["password"]
            user.save()
            return HttpResponse(content="User updated with id " + user.id, status=200)
        except Exception as e:
            print(e, type(e))

    def delete(self, request, user_id):

        user = get_object_or_404(User, pk=user_id)
        try:
            request_user = request.user
            if user.info.customer == request_user.info.customer:
                user.delete()
        except Exception as e:
            print(e, type(e))

        return HttpResponse(content="Deleted successfully user with id " + str(user_id), status=200)


class UserPasswordResetRequest(View):
    def post(self, request):
        email = request.POST["user_email"]
        try:
            user = User.objects.get(email=email)
            chars = string.ascii_letters + string.digits + '!@$*()'
            random.seed = (os.urandom(1024))
            token = ''.join(random.choice(chars) for i in range(6))
            html_message = loader.render_to_string(
                'reset_password_email.html',
                {
                    'email': email,
                    'token': token,
                }
            )
            send_mail(
                'Reset Password',
                '',
                'from@example.com',
                [email],
                fail_silently=False,
                html_message=html_message,
            )
            user.reset_token = token
            user.reset_token_datetime = datetime.datetime.now()
            user.save()
        except User.DoesNotExist:
            user = None

        return HttpResponse(200)


class UserResetTokenVerify(View):
    def post(self, request):
        email = request.POST["user"]
        token = request.POST["token"]
        try:
            user = User.objects.get(email=email)
            now = datetime.datetime.now()
            token_time = user.reset_token_datetime.replace(tzinfo=None)
            if (token == user.reset_token) and (user.reset_token != "") and (
                (now - token_time).total_seconds() < 86400):
                return HttpResponse(status=200)
        except User.DoesNotExist:
            user = None

        return HttpResponse(status=401)


class UserChangePassword(View):
    def post(self, request):
        new_password = request.POST["new_password"]
        re_new_password = request.POST["re_new_password"]
        email = request.POST["email"]
        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            user.reset_token = ""
            user.save()
            return HttpResponse(status=200)
        except User.DoesNotExist:
            user = None

        return HttpResponse(status=401)



@api_view(['GET'])
@permission_classes((AllowAny,))
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def get_user_profile(request):
    user_id = get_user_from_request(request,0)
    token = get_default_param(request, 'reset_token', None)

    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: HTTP_ERROR_CODE, RESPONSE_DATA: []}
    http_status = HTTP_SUCCESS_CODE

    resp_dict = {}
    resp_list = []
    if user_id.id is not None:
        user_id = int(user_id.id)
        try:
            user_obj = User.objects.get(pk=user_id)
            serializer = UserSerializer(user_obj, partial=True, context={'request': request})
            resp_dict = serializer.data
            resp_list.append(resp_dict)

            response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
            response_body[RESPONSE_DATA] = resp_list
        except User.DoesNotExist:
            response_body[RESPONSE_MESSAGE] = "The profile you are using is not valid. Please login again with valid credentials."
            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
            return generic_response(response_body=response_body, http_status=http_status)
    elif token:
        user_obj = User.objects.get(reset_token=token)
        serializer = UserSerializer(user_obj, partial=True, context={'request': request})
        resp_dict = serializer.data
        resp_list.append(resp_dict)

        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
        response_body[RESPONSE_DATA] = resp_list

    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['PATCH'])
@permission_classes((AllowAny,))
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def modify_user_details(request):
    user_id = get_user_from_request(request, 0)
    token = get_data_param(request, 'reset_token', None)
    old_password = get_data_param(request, 'old_password', None)

    if request.data.get('password'):
        request.POST._mutable = True
        request.data['password'] = make_password(request.data.get('password'))
        request.POST._mutable = False

    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    http_status = HTTP_SUCCESS_CODE

    if user_id.id is not None and old_password is None:
        user_id = int(user_id.id)
        user_obj = User.objects.get(pk=user_id)
        serializer = UserSerializer(user_obj, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            data_dict = {}
            data_dict['avatar'] = serializer.data.get('avatar')
            data_dict['first_name'] = serializer.data.get('first_name')
            data_dict['last_name'] = serializer.data.get('last_name')
            data_dict['preferred_module'] = serializer.data.get('preferred_module')
            response_body[RESPONSE_MESSAGE] = {'success_message': TEXT_OPERATION_SUCCESSFUL}
            
            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
            response_body[RESPONSE_DATA] = data_dict

        else:
            error_list = []
            response_body[RESPONSE_MESSAGE] = "Following Fields have invalid values: \n"
            for errors in serializer.errors:
                print(serializer.errors)
                error_list.append(errors)
                response_body[RESPONSE_MESSAGE] += errors +'\n'
            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE

    # elif token:
    #     try:
    #         email = User.objects.get(reset_token=token)
    #         verified_user = user_reset_verify(user_email=email.email, token=token)
    #
    #     except:
    #         return generic_response(response_body=response_body, http_status=http_status)
    #     if verified_user:# and verified_user.password is None:
    #         verified_user.reset_token = ""
    #         verified_user.reset_token_datetime = None
    #         verified_user.save()
    #         serializer = UserSerializer(verified_user, data=request.data, partial=True, context={'request': request})
    #         if serializer.is_valid():
    #             serializer.save()
    #
    #             response_body[RESPONSE_MESSAGE] = {'success_message': TEXT_OPERATION_SUCCESSFUL}
    #             http_status = HTTP_SUCCESS_CODE
    #             response_body[RESPONSE_STATUS] = http_status

    elif old_password and user_id:
        try:
            user_id = int(user_id.id)
            user_obj = User.objects.get(pk=user_id)

            if check_password(old_password, user_obj.password):
                user_obj.password = request.data['password']
                user_obj.save()

                response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
                response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
            else:
                response_body[RESPONSE_MESSAGE] = "Incorrect Password Entered"
                response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE

        except User.DoesNotExist:
            response_body[RESPONSE_MESSAGE] = "User profile does not exist. Please contact your administrator."
            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
            
    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['PATCH'])
@permission_classes((AllowAny,))
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def regenerate_reset_token(request):
    email = get_data_param(request, 'email', None)

    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    http_status = HTTP_SUCCESS_CODE
    if email:
        add_user = reset_user_token_reset(user_email=email)
        if add_user:
            url = add_user.reset_token
            msg = EMAIL_FORGOT_PASSWORD_MESSAGE
            extended_email_with_title(title="create_user", to_list=[email], email_words_dict={'{0}': url, '{text}':msg})

            response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        else:
            response_body[RESPONSE_MESSAGE] = "User does not exist or incorrect credentials provided"
            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE

    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['PATCH'])
@permission_classes((AllowAny,))
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def verfiy_user_token(request):
    token = get_default_param(request, 'reset_token', None)

    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    http_status = HTTP_ERROR_CODE

    if token is not None:
        try:
            email = User.objects.get(reset_token=token)
            verified_user = user_reset_verify(user_email=email.email, token=token)
            if verified_user:
                response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
                http_status = HTTP_SUCCESS_CODE
                response_body[RESPONSE_STATUS] = STATUS_OK
        except:
            response_body[RESPONSE_MESSAGE] = 'Link Expired ! Please Contact your system Admin'
            http_status = HTTP_SUCCESS_CODE
            response_body[RESPONSE_STATUS] = STATUS_ERROR
            # return generic_response(response_body=response_body, http_status=http_status)
    else:
        response_body[RESPONSE_MESSAGE] = 'Link Expired ! Please Contact your system Admin'
        return generic_response(response_body=response_body, http_status=http_status)

    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['PATCH'])
@permission_classes((AllowAny,))
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def reset_user_password_token(request):
    token = get_data_param(request, 'reset_token', None)

    if request.data.get('password'):
        request.POST._mutable = True
        request.data['password'] = make_password(request.data.get('password'))
        request.POST._mutable = False

    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    http_status = HTTP_ERROR_CODE

    if token:
        try:
            email = User.objects.get(reset_token=token)
            verified_user = user_reset_verify(user_email=email.email, token=token)

        except:
            return generic_response(response_body=response_body, http_status=http_status)
        if verified_user:# and verified_user.password is None:
            verified_user.reset_token = ""
            verified_user.reset_token_datetime = None
            verified_user.save()
            serializer = UserSerializer(verified_user, data=request.data, partial=True, context={'request': request})
            if serializer.is_valid():
                serializer.save()

                response_body[RESPONSE_MESSAGE] = {'success_message': TEXT_OPERATION_SUCCESSFUL}
                http_status = HTTP_SUCCESS_CODE
                response_body[RESPONSE_STATUS] = http_status
        else:
            response_body[RESPONSE_MESSAGE] = {'Error_Message': 'Link Expired ! Please Contact your system Admin'}
            return generic_response(response_body=response_body, http_status=http_status)

    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['POST'])
# @permission_classes((IsAdminOrReadOnly,))
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def user_sign_up_invitation_manager(request):
    email = get_data_param(request, 'email', None)
    request.POST._mutable = True
    request.data['status'] = OptionsEnum.ACTIVE
    request.data['customer'] = get_customer_from_request(request, None)
    request.data['module'] = get_module_from_request(request, None)
    request.data['modified_by'] = get_user_from_request(request,None).id
    request.POST._mutable = False
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}


    if email:

        try:
            user = User.objects.get(email=email)
            if user:
                response_body[RESPONSE_MESSAGE] = {'error_message': 'User Already Exists'}
                http_status = HTTP_SUCCESS_CODE
                response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                return generic_response(response_body=response_body, http_status=http_status)
        except:
            serializer = UserSerializer(data=request.data, partial=True, context={'request': request})
            if serializer.is_valid():
                user = serializer.save()
                email = user.email
                add_user = reset_user_token_reset(user_email=email)
                if add_user:
                    url = add_user.reset_token
                    msg = EMAIL_FORGOT_PASSWORD_MESSAGE
                    extended_email_with_title(title="create_user", to_list=[email], email_words_dict={'{0}':url, '{text}':msg})

                response_body[RESPONSE_MESSAGE] = {'success_message': TEXT_OPERATION_SUCCESSFUL}
                http_status = HTTP_SUCCESS_CODE
                response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE

            else:
                error_list = []
                for errors in serializer.errors:
                    error_list.append("invalid  " + errors + "  given.")
                print(error_list)

                response_body[RESPONSE_MESSAGE] = {'error_message': 'Validation Error'}
                http_status = HTTP_SUCCESS_CODE
                response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                response_body[RESPONSE_DATA] = error_list

        else:
            response_body[RESPONSE_MESSAGE] = {'error_message': 'Enter a Valid Email Addresse'}
            http_status = HTTP_SUCCESS_CODE
            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
            return generic_response(response_body=response_body, http_status=http_status)

        return generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def users_details_list(request):
    customer = get_customer_from_request(request,None)
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    if get_user_from_request(request,None):
        if get_user_from_request(request, None).role_id != RoleTypeEnum.ADMIN:
            response_body[RESPONSE_MESSAGE] = 'You do not have sufficient privleges to perform this action.'
            http_status = HTTP_SUCCESS_CODE
            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
            return generic_response(response_body=response_body, http_status=http_status)
    if customer:
        users_list = []
        user = User.objects.filter(customer_id = customer)
        for obj in user:
            serializer = UserSerializer(obj, partial=True, context={'request': request})
            serializer_data = serializer.data.copy()
            users_list.append(serializer_data)

        response_body[RESPONSE_MESSAGE] = {'success_message': TEXT_OPERATION_SUCCESSFUL}
        http_status = HTTP_SUCCESS_CODE
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        response_body[RESPONSE_DATA] = users_list

        return generic_response(response_body=response_body, http_status=http_status)