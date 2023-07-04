from dateutil.parser import parse
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer
from .models import *


class ActivityScheduleSerializer(ModelSerializer):
    customer_name = SerializerMethodField('customer_method', allow_null=True, required=False, read_only=True)
    modified_by_name = SerializerMethodField('modified_name', allow_null=True, required=False, read_only=True)
    module_name = SerializerMethodField('module_method', required=False, allow_null=True)
    activity_type_label = SerializerMethodField('status_method', required=False, allow_null=True)
    primary_entity_name = SerializerMethodField('entity_method', allow_null=True, required=False, read_only=True)
    actor_name = SerializerMethodField('actor_method', allow_null=True, required=False, read_only=True)
    activity_end_point_name = SerializerMethodField('activity_end_point_method', allow_null=True, required=False, read_only=True)
    activity_check_point_name = SerializerMethodField('activity_check_point_method', allow_null=True, required=False, read_only=True)
    activity_end_point_latlong = SerializerMethodField('activity_end_point_latlong_method', allow_null=True, required=False, read_only=True)
    activity_check_point_latlong = SerializerMethodField('activity_check_point_latlong_method', allow_null=True, required=False, read_only=True)
    schedule_activity_status_label = SerializerMethodField('schedule_activity_status_method', allow_null=True, required=False, read_only=True)
    days_list_get = SerializerMethodField('days_list_method', allow_null=True, required=False, read_only=True)


    def entity_method(self, obj):
        if obj.primary_entity:
            return obj.primary_entity.name
        else:
            return None

    def days_list_method(self, obj):
        if obj.days_list:
            days = list(obj.days_list.split(','))
            # if len(days) > 0:
            return days
        else:
            days = str(str(obj.start_date)+' '+str(obj.activity_start_time))
            days = parse(days)
            return str(days.weekday())

    def activity_end_point_method(self, obj):
        if obj.activity_end_point:
            return obj.activity_end_point.name
        else:
            return None

    def activity_end_point_latlong_method(self, obj):
        if obj.activity_end_point:
            return obj.activity_end_point.source_latlong
        else:
            return None

    def activity_check_point_method(self, obj):
        if obj.activity_check_point:
            return obj.activity_check_point.name
        else:
            return None
        
    def activity_check_point_latlong_method(self, obj):
        if obj.activity_check_point:
            return obj.activity_check_point.source_latlong
        else:
            return None

    def actor_method(self, obj):
        if obj.actor:
            return obj.actor.name
        else:
            return None

    def customer_method(self, obj):
        if obj.customer:
            return obj.customer.name
        else:
            return None

    def modified_name(self, obj):
        if obj.modified_by:
            if obj.modified_by.last_name and obj.modified_by.last_name:
                email = obj.modified_by.first_name + ' ' + obj.modified_by.last_name
            else:
                email = obj.modified_by.email
            return email
        else:
            return None

    def status_method(self, obj):
        if obj.activity_type:
            stat = obj.activity_type.label
            return stat
        else:
            return None

    def schedule_activity_status_method(self, obj):
        if obj.schedule_activity_status:
            stat = obj.schedule_activity_status.label
            return stat
        else:
            return None

    def module_method(self, obj):
        if obj.module:
            mod = obj.module.name
            return mod
        else:
            return None


    class Meta:
        model = ActivitySchedule
        fields = \
            [
                'id',
                'customer',
                'customer_name',

                'module',
                'module_name',

                'activity_type',
                'activity_type_label',

                'primary_entity',
                'primary_entity_name',
                # 'schedule_type',
                'start_date',
                'end_date',
                'activity_start_time',
                'action_items',
                # 'activity_route',
                # 'activity_priority',
                # 'is_active',
                'modified_by',
                'modified_by_name',

                'schedule_activity_status_label',
                'schedule_activity_status',

                'actor',
                'actor_name',
                'activity_end_point',
                'activity_end_point_name',
                'activity_end_point_latlong',
                'activity_check_point',
                'activity_check_point_name',
                'activity_check_point_latlong',
                'days_list',
                'days_list_get',
                'notes',
            ]



class ActivitySerializer(ModelSerializer):
    customer_name = SerializerMethodField('customer_method', allow_null=True, required=False, read_only=True)
    module_name = SerializerMethodField('module_method', required=False, allow_null=True)
    activity_status_label = SerializerMethodField('status_method', required=False, allow_null=True)
    primary_entity_name = SerializerMethodField('entity_method', allow_null=True, required=False, read_only=True)
    actor_name = SerializerMethodField('actor_method', allow_null=True, required=False, read_only=True)
    activity_end_point_name = SerializerMethodField('activity_end_point_method', allow_null=True, required=False,
                                                    read_only=True)
    activity_end_point_latlong = SerializerMethodField('activity_end_point_latlong_method', allow_null=True,
                                                       required=False, read_only=True)
    activity_check_point_name = SerializerMethodField('activity_check_point_method', allow_null=True, required=False,
                                                    read_only=True)
    activity_check_point_latlong = SerializerMethodField('activity_check_point_latlong_method', allow_null=True,
                                                       required=False, read_only=True)

    def entity_method(self, obj):
        if obj.primary_entity:
            return obj.primary_entity.name
        else:
            return None

    def activity_end_point_latlong_method(self, obj):
        if obj.activity_end_point:
            return obj.activity_end_point.source_latlong
        else:
            return None

    def activity_end_point_method(self, obj):
        if obj.activity_end_point:
            return obj.activity_end_point.name
        else:
            return None

    def activity_check_point_latlong_method(self, obj):
        if obj.activity_check_point:
            return obj.activity_check_point.source_latlong
        else:
            return None

    def activity_check_point_method(self, obj):
        if obj.activity_check_point:
            return obj.activity_check_point.name
        else:
            return None

    
    def actor_method(self, obj):
        if obj.actor:
            return obj.actor.name
        else:
            return None

    def customer_method(self, obj):
        if obj.customer:
            return obj.customer.name
        else:
            return None


    def status_method(self, obj):
        if obj.activity_status:
            stat = obj.activity_status.label
            return stat
        else:
            return None

    def module_method(self, obj):
        if obj.module:
            mod = obj.module.name
            return mod
        else:
            return None


    class Meta:
        model = Activity
        fields = \
            [
                'id',
                'activity_schedule',
                'action_items',

                'customer',
                'customer_name',

                'module',
                'module_name',

                'activity_status',
                'activity_status_label',

                'created_datetime',
                'start_datetime',
                'end_datetime',
                'notification_sent',
                'start_lat_long',
                'end_lat_long',

                'actor',
                'actor_name',

                'primary_entity',
                'primary_entity_name',

                'activity_end_point',
                'activity_end_point_name',
                'activity_end_point_latlong',
    
                'activity_check_point',
                'activity_check_point_name',
                'activity_check_point_latlong',
                
                'activity_start_time',
                'distance',
                'duration',
                'volume_consumed',
                'violations',
                'notes',

            ]



class ActivityDataSerializer(ModelSerializer):
    customer_name = SerializerMethodField('customer_method', allow_null=True, required=False, read_only=True)
    module_name = SerializerMethodField('module_method', required=False, allow_null=True)
    activity_status_label = SerializerMethodField('status_method', required=False, allow_null=True)
    primary_entity_name = SerializerMethodField('entity_method', allow_null=True, required=False, read_only=True)
    supervisor_name = SerializerMethodField('supervisor_method', allow_null=True, required=False, read_only=True)
    actor_name = SerializerMethodField('actor_method', allow_null=True, required=False, read_only=True)
    activity_end_point_name = SerializerMethodField('activity_end_point_method', allow_null=True, required=False, read_only=True)
    activity_check_point_name = SerializerMethodField('activity_check_point_method', allow_null=True, required=False, read_only=True)


    def entity_method(self, obj):
        if obj.primary_entity:
            return obj.primary_entity.name
        else:
            return None
    
    def supervisor_method(self, obj):
        if obj.supervisor:
            return obj.supervisor.name
        else:
            return None
    
    def activity_end_point_method(self, obj):
        if obj.activity_end_point:
            return obj.activity_end_point.name
        else:
            return None
    
    def activity_check_point_method(self, obj):
        if obj.activity_check_point:
            return obj.activity_check_point.name
        else:
            return None

    def actor_method(self, obj):
        if obj.actor:
            return obj.actor.name
        else:
            return None

    def customer_method(self, obj):
        if obj.customer:
            return obj.customer.name
        else:
            return None


    def status_method(self, obj):
        if obj.activity_status:
            stat = obj.activity_status.label
            return stat
        else:
            return None

    def module_method(self, obj):
        if obj.module:
            mod = obj.module.name
            return mod
        else:
            return None


    class Meta:
        model = ActivityData
        fields = \
            [
                'id',
                'scheduled_activity',
                'action_items',

                'customer',
                'customer_name',

                'module',
                'module_name',

                'activity_status',
                'activity_status_label',

                'lat_long',

                'actor',
                'actor_name',

                'primary_entity',
                'primary_entity_name',

                'activity_end_point',
                'activity_end_point_name',
    
                'activity_check_point',
                'activity_check_point_name',

                'created_datetime',
                'timestamp',
                'supervisor',
                'supervisor_name',
            ]

class ActivityQueueSerializer(ModelSerializer):

    class Meta:
        model = ActivityQueue
        fields = \
            [
                'id',
                'activity_schedule',
                'action_items',
                'activity_datetime',
                'primary_entity',
                'customer',
                'module',
                'actor',
                'activity_end_point',
                'activity_end_datetime',

            ]