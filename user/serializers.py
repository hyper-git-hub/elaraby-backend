import traceback

from django.contrib.auth.hashers import make_password
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import User
import invitations
import sys
from django.contrib.auth import authenticate, login
import pdb

from rest_framework.serializers import (
    CharField,
    EmailField,
    HyperlinkedIdentityField,
    ModelSerializer,
    SerializerMethodField,
    ValidationError,
    ImageField
    )


User = get_user_model()


class InfoDetailSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = [
            'admin',
            'customer'
        ]



class InvitationCreateSerializer(ModelSerializer):
    class Meta:
        model = invitations.models.Invitation
        fields = [
            'email',
            'inviter',
        ]


class UserDetailSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
        ]



class UserCreateSerializer(ModelSerializer):
    email = EmailField(label='Email Address')
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
        ]
        extra_kwargs = {"password":
                            {"write_only": True}
                            }
    def validate(self, data):
        # email = data['email']
        # user_qs = User.objects.filter(email=email)
        # if user_qs.exists():
        #     raise ValidationError("This user has already registered.")
        return data


    def validate_email(self, value):
        data = self.get_initial()
        email1 = data.get("email2")
        email2 = value

        user_qs = User.objects.filter(email=email2)
        if user_qs.exists():
            raise ValidationError("This user has already registered.")

        return value

    # def validate_email2(self, value):
    #     data = self.get_initial()
    #     email1 = data.get("email")
    #     email2 = value
    #     if email1 != email2:
    #         raise ValidationError("Emails must match.")
    #     return value



    def create(self, validated_data):
        username = validated_data['username']
        email = validated_data['email']
        password = validated_data['password']
        try:
            invite = invitations.models.Invitation.objects.filter(email=email)
            customer = invite.order_by('id')[0].inviter.info.customer
        except:
            print("Unexpected error:", sys.exec_info()[0])
        user_obj = User(
                username = username,
                email = email
            )
        user_obj.set_password(password)
        user = user_obj.save()
        user_obj.info = User(
            customer = customer
        )
        user_obj.info.save()
        return validated_data


# class UserLoginSerializer(ModelSerializer):
#     # token = CharField(allow_blank=True, read_only=True)
#     # info = InfoDetailSerializer(read_only=True)
#     email = EmailField(label='Email Address')
#     class Meta:
#         model = User
#         fields = [
#             'email',
#             'password',
#             # 'info'
#             # 'token',
#         ]
#         extra_kwargs = {"password":
#                             {"write_only": True}
#                             }
#     def validate(self, data):
#         # pdb.set_trace()
#         user_obj = None
#         email = data.get("email", None)
#         password = data["password"]
#         if not email:
#             raise ValidationError("An email is required to login.")
# 
#         user = User.objects.filter(
#                 Q(email=email)
#         ).distinct()
#         user = user.exclude(email__isnull=True)
#         if user.exists():
#             user_obj = user.first()
#         else:
#             raise ValidationError("This email is not valid.")
# 
#         if user_obj:
#             if not user_obj.check_password(password):
#                 raise ValidationError("Incorrect credentials please try again.")
# 
# 
#         # if user_obj.info:
#         #     company = user_obj.info.customer
#         #     things = user_obj.info.customer.thing_set.all()
#         #     data['company'] = company
#         #     data['things'] = things
#         # email = data['email']
#         # user_qs = User.objects.filter(email=email)
#         # if user_qs.exists():
#         #     raise ValidationError("This user has already registered.")
#         return data

class UserLoginSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'preferred_module',
            'associated_entity'
        ]


class UserSerializer(ModelSerializer):
    # avatar = ImageField(allow_empty_file=True, allow_null=True, required=False)
    avatar_method = SerializerMethodField('img_url', required=False)
    full_name = SerializerMethodField('full_name_method', allow_null=True, required=False, read_only=True)
    gender_label = SerializerMethodField('gender_method', required=False, allow_null=True)
    status_label = SerializerMethodField('status_method', required=False, allow_null=True)
    customer_name = SerializerMethodField('customer_name_method', required=False, allow_null=True)
    language_label = SerializerMethodField('language_method', required=False, allow_null=True)
    role_name = SerializerMethodField('role_method', required=False, allow_null=True)
    associated_entity_name = SerializerMethodField('associated_entity_name_method', required=False, allow_null=True)
    last_user_login = SerializerMethodField('last_user_login_method', required=False, allow_null=True)
    date_joined_date = SerializerMethodField('date_joined_method', required=False, allow_null=True)
    # password = SerializerMethodField('password_method', required=False, read_only=False)


    # def password_method(self, obj):
    #     if self.context['request'].method == 'POST' or self.context['request'].method == 'PATCH':
    #         request = self.context['request']
    #         obj.password = make_password(request.data.get('password'))
    #         obj.save()
    #     else:
    #         return obj.password


    def associated_entity_name_method(self, obj):
        if obj.associated_entity:
            entity_name = obj.associated_entity.name
            return entity_name
        else:
            return None

    def last_user_login_method(self, obj):
        if obj.last_login:
            return obj.last_login
        else:
            return None

    def role_method(self, obj):
        if obj.role:
            role_name = obj.role.name
            return role_name
        else:
            return None

    def status_method(self, obj):
        if obj.status:
            return obj.status.label
        else:
            return None
        
    def customer_name_method(self, obj):
        if obj.customer:
            return obj.customer.name
        else:
            return None

    def date_joined_method(self, obj):
        if obj.created_datetime:
            return str(obj.created_datetime.date())
        else:
            return None

    def language_method(self, obj):
        if obj.language:
            return obj.language.label
        else:
            return None

    def gender_method(self, obj):
        if obj.gender:
            return obj.gender.label
        else:
            return None

    def full_name_method(self, obj):
        if [obj.first_name, obj.last_name] is not None:
            full_name = obj.first_name + " " + obj.last_name
            return full_name
        else:
            return None

    def img_url(self, obj):
        if self.context['request'].method == 'POST' or self.context['request'].method == 'PATCH':
            req = self.context['request']
            obj.avatar = req.data.get('avatar')
            obj.save()
        elif self.context['request'].method == 'GET':
            try:
                photo_url = obj.avatar.url
                return self.context['request'].build_absolute_uri(photo_url)
            except:
                traceback.print_exc()
                return None




    # password = make_password()
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'password',

            'first_name',
            'last_name',
            'full_name',

            'customer',
            'customer_name',

            'gender',
            'gender_label',
            'status',
            'status_label',
            'language',
            'language_label',

            'modified_by',
            'role',
            'role_name',


            'contact_number',
            'date_joined_date',
            'preferred_module',

            'avatar',
            'avatar_method',

            'associated_entity',
            'associated_entity_name',

            'last_user_login',

        ]

        # def create(self, validated_data):
        #     user = User(password=make_password(validated_data['password']),
        #                 email=validated_data['email'],
        #                 first_name=validated_data['first_name'],
        #                 last_name=validated_data['last_name'],
        #                 customer=validated_data['customer'],
        #                 status=validated_data['status'],
        #                 modified_by=validated_data['modified_by'],
        #                 role=validated_data['role'],
        #                 gender=validated_data['gender'],
        #                 language=validated_data['language'],
        #                 contact_number=validated_data['contact_number'],
        #                 preferred_module=validated_data['preferred_module'],
        #                 avatar=validated_data['avatar'],
        #                 )
        #     user.save()
        #     return user
