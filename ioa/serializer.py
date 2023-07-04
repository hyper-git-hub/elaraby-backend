from rest_framework import serializers
from hypernet.models import Entity
from ioa.models import Scheduling, ActivityList
from user.models import User
from django.contrib.auth.hashers import make_password


class SchedulingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scheduling
        fields = ('animal', 'scheduled_start_time', 'scheduled_end_time', 'scheduled_start_date',
                  'scheduled_end_date', 'comments')

class AnimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
        fields = ('name', 'lactation_days', 'last_breeding', 'age', 'weight', 'type', 'customer',
                  'module', 'status', 'modified_by', 'breed', 'lactation_status', 'group')

class ActivityListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityList
        fields = ('animal', 'customer', 'derived_alerts', 'activity_type', 'action_status',
                  'group', 'group_value', 'perform_individually', 'individual_value',
                  'scheduled_start_time', 'scheduled_end_time', 'scheduling_comments',
                  'performed_start_time', 'performed_end_time', 'performed_comments',
                  'is_on_time', 'created_by', 'modified_by', 'activity_priority',
                  )


class IoaCaretakerSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(allow_empty_file=True, allow_null=True, required=False)

    # password = make_password()
    class Meta:
        model = User
        fields = [
            'email',
            'password',
            'first_name',
            'last_name',
            'customer',
            'gender',
            'status',
            'modified_by',
            'role',
            'language',
            'contact_number',
            'date_joined',
            'preferred_module',
            'avatar',
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


class UserDataSerializer(serializers.ModelSerializer):
    role = serializers.SlugRelatedField(read_only=True, slug_field='name')
    status = serializers.SlugRelatedField(read_only=True, slug_field='label')
    customer = serializers.SlugRelatedField(slug_field='name', read_only=True)
    gender = serializers.SlugRelatedField(slug_field='label', read_only=True)
    avatar_url = serializers.SerializerMethodField('img_url')

    def img_url(self, obj):
        if obj.avatar:
            photo_url = obj.avatar.url
            return self.context['request'].build_absolute_uri(photo_url)
        else:
            return None

    class Meta:
        model = User
        fields = [
            'email',
            'first_name',
            'last_name',
            'customer',
            'gender',
            'status',
            'modified_by',
            'role',
            'language',
            'contact_number',
            'date_joined',
            'preferred_module',
            'avatar_url',
        ]



class CaretakerLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
        ]
