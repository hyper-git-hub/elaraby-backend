import traceback

from dateutil.parser import parse
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer

from hypernet.enums import DeviceTypeAssignmentEnum, OptionsEnum
from hypernet.models import Assignment
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
    schedule_clients = SerializerMethodField('schedule_clients_method', allow_null=True, required=False, read_only=True)
    schedule_contracts = SerializerMethodField('schedule_contracts_method', allow_null=True, required=False, read_only=True)


    def schedule_contracts_method(self, obj):
        try:
            contracts_list = ""
            all_bins = obj.action_items.split(',')
            for b in all_bins:
                try:
                    contracts_list += Assignment.objects.get(parent_id=b,
                                                             type_id=DeviceTypeAssignmentEnum.CONTRACT_ASSIGNMENT,
                                                             status_id=OptionsEnum.ACTIVE).child.name+", "
                except:
                    traceback.print_exc()
                    pass
            return contracts_list
        except:
            traceback.print_exc()
            return None


    def schedule_clients_method(self, obj):
        try:
            clients_list = ""
            all_bins = obj.action_items.split(',')
            for b in all_bins:
                try:
                    client = Entity.objects.get(id=b).client.name
                    if client not in clients_list:
                        clients_list += client+", "
                except:
                    traceback.print_exc()
                    pass
            return clients_list
        except:
            traceback.print_exc()
            return None


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
                'created_datetime',
                'module',
                'module_name',
                'current_ctt',
                'activity_type',
                'activity_type_label',

                'primary_entity',
                'primary_entity_name',
                # 'schedule_type',
                'start_date',
                'end_date',
                'activity_start_time',
                'activity_end_time',
                'u_activity_start_time',
                'u_activity_end_time',
                'action_items',
                'activity_route',
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
                'u_days_list',
                'multi_days',
                'days_list_get',
                'notes',
                'schedule_clients',
                'schedule_contracts',
                'temp_after_usage',
                'old_start_dt',
                'old_end_dt',
                'new_start_dt',
                'new_end_dt',
                'validity_date',
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
                'trips',
                'trip_cost',
                'trip_revenue',
                'fuel_avg',
                'waste_collected',
                'diesel_price'
            ]



class ActivityDataSerializer(ModelSerializer):
    customer_name = SerializerMethodField('customer_method', allow_null=True, required=False, read_only=True)
    module_name = SerializerMethodField('module_method', required=False, allow_null=True)
    activity_status_label = SerializerMethodField('status_method', required=False, allow_null=True)
    primary_entity_name = SerializerMethodField('entity_method', allow_null=True, required=False, read_only=True)
    action_items_name = SerializerMethodField('action_item_method', allow_null=True, required=False, read_only=True)
    supervisor_name = SerializerMethodField('supervisor_method', allow_null=True, required=False, read_only=True)
    actor_name = SerializerMethodField('actor_method', allow_null=True, required=False, read_only=True)
    activity_end_point_name = SerializerMethodField('activity_end_point_method', allow_null=True, required=False, read_only=True)
    activity_check_point_name = SerializerMethodField('activity_check_point_method', allow_null=True, required=False, read_only=True)


    def entity_method(self, obj):
        if obj.primary_entity:
            return obj.primary_entity.name
        else:
            return None
        
    def action_item_method(self, obj):
        if obj.action_items:
            return obj.action_items.name
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
                'action_items_name',

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
                'notes',
                'cost'
            ]


class BinCollectionDataSerializer(ModelSerializer):
    customer_name = SerializerMethodField('customer_method', allow_null=True, required=False, read_only=True)
    module_name = SerializerMethodField('module_method', required=False, allow_null=True)
    status_label = SerializerMethodField('status_method', required=False, allow_null=True)
    entity_name = SerializerMethodField('entity_method', allow_null=True, required=False, read_only=True)
    contract_name = SerializerMethodField('contract_method', allow_null=True, required=False, read_only=True)
    client_name = SerializerMethodField('client_method', allow_null=True, required=False,read_only=True)
    area_name = SerializerMethodField('area_method', allow_null=True, required=False,read_only=True)
    action_item_name = SerializerMethodField('action_item_method', allow_null=True, required=False,read_only=True)
    actor_name = SerializerMethodField('actor_method', allow_null=True, required=False, read_only=True)
    supervisor_name = SerializerMethodField('supervisor_method', allow_null=True, required=False, read_only=True)
    
    
    
    def entity_method(self, obj):
        if obj.entity:
            return obj.entity.name
        else:
            return None
    
    def supervisor_method(self, obj):
        if obj.supervisor:
            return obj.supervisor.name
        else:
            return None
    
    def contract_method(self, obj):
        if obj.contract:
            return obj.contract.name
        else:
            return None
    
    def client_method(self, obj):
        if obj.client:
            return obj.client.name
        else:
            return None

    def area_method(self, obj):
        if obj.client:
            return obj.area.name
        else:
            return None
        
    def action_item_method(self, obj):
        if obj.action_item:
            return obj.action_item.name
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
        if obj.status:
            stat = obj.status.label
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
        model = BinCollectionData
        fields = \
            [
                'id',
                
                'customer',
                'customer_name',
                'module',
                'module_name',
                'status',
                'status_label',
                
                'entity',
                'entity_name',
                
                'contract',
                'contract_name',
    
                'client',
                'client_name',
                
                'area',
                'area_name',
                
                'activity',
    
                'action_item',
                'action_item_name',
                
                'actor',
                'actor_name',
                
                'pre_weight',
                'post_weight',
                'weight',

                'timestamp',
                'invoice',
                'verified',
                
                'supervisor',
                'supervisor_name'
                
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


class LogisticMaintenanceSerializer(ModelSerializer):
    customer_name = SerializerMethodField('customer_method', allow_null=True, required=False, read_only=True)
    module_name = SerializerMethodField('module_method', required=False, allow_null=True)
    status_label = SerializerMethodField('status_method', required=False, allow_null=True)
    driver_name = SerializerMethodField('driver_method', allow_null=True, required=False, read_only=True)
    truck_name = SerializerMethodField('truck_method', allow_null=True, required=False, read_only=True)
    maintenance_type_name = SerializerMethodField('maintenance_method', allow_null=True, required=False, read_only=True)
    modified_by_name = SerializerMethodField('modified_name', allow_null=True, required=False, read_only=True)
    modified_by_email = SerializerMethodField('modified_email', allow_null=True, required=False, read_only=True)
    cost = SerializerMethodField('cost_method', allow_null=True, required=False, read_only=True)
    
    def driver_method(self, obj):
        if obj.driver:
            return obj.driver.name
        else:
            return None
        
    def truck_method(self, obj):
        if obj.truck:
            return obj.truck.name
        else:
            return None
        
    def maintenance_method(self, obj):
        if obj.maintenance_type:
            return obj.maintenance_type.label
        else:
            return None
    
    def customer_method(self, obj):
        if obj.customer:
            return obj.customer.name
        else:
            return None
    
    def status_method(self, obj):
        if obj.status:
            stat = obj.status.label
            return stat
        else:
            return None
    
    def module_method(self, obj):
        if obj.module:
            mod = obj.module.name
            return mod
        else:
            return None

    def modified_email(self, obj):
        if obj.modified_by:
            if obj.modified_by.email:
                email = obj.modified_by.email
            else:
                email = None
            return email
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
    
    def cost_method(self, obj):
        data = LogisticMaintenanceData.objects.filter(maintenance=obj)
        total = 0
        for o in data:
            if o.cost:
                total += o.cost
        return total
        
    class Meta:
        model = LogisticMaintenance
        fields = \
            [
                'id',
                
                'customer',
                'customer_name',
                'module',
                'module_name',
                'status',
                'status_label',
                
                'driver',
                'driver_name',
    
                'truck',
                'truck_name',
                
                'maintenance_type',
                'maintenance_type_name',
    
                'issued_datetime',
                'start_datetime',
                'end_datetime',

                'modified_by',
                'modified_by_name',
                'modified_by_email',
                'cost',
                
                
            ]


class LogisticMaintenanceDataSerializer(ModelSerializer):
    customer_name = SerializerMethodField('customer_method', allow_null=True, required=False, read_only=True)
    module_name = SerializerMethodField('module_method', required=False, allow_null=True)
    action_label = SerializerMethodField('action_method', required=False, allow_null=True)
    driver_name = SerializerMethodField('driver_method', allow_null=True, required=False, read_only=True)
    truck_name = SerializerMethodField('truck_method', allow_null=True, required=False, read_only=True)
    cost_type_label = SerializerMethodField('cost_type_method', required=False, allow_null=True)
    modified_by_name = SerializerMethodField('modified_name', allow_null=True, required=False, read_only=True)
    modified_by_email = SerializerMethodField('modified_email', allow_null=True, required=False, read_only=True)

    def driver_method(self, obj):
        if obj.driver:
            return obj.driver.name
        else:
            return None

    def truck_method(self, obj):
        if obj.truck:
            return obj.truck.name
        else:
            return None

    def customer_method(self, obj):
        if obj.customer:
            return obj.customer.name
        else:
            return None
    
    def action_method(self, obj):
        if obj.action:
            stat = obj.action.label
            return stat
        else:
            return None
        
    def cost_type_method(self, obj):
        if obj.cost_type:
            stat = obj.cost_type.label
            return stat
        else:
            return None
    
    def module_method(self, obj):
        if obj.module:
            mod = obj.module.name
            return mod
        else:
            return None
        
    def modified_email(self, obj):
        if obj.modified_by:
            if obj.modified_by.email:
                email = obj.modified_by.email
            else:
                email = None
            return email
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
    
    class Meta:
        model = LogisticMaintenanceData
        fields = \
            [
                'id',
                
                'maintenance',
                
                'driver',
                'driver_name',
    
                'truck',
                'truck_name',
                
                'customer',
                'customer_name',
                'module',
                'module_name',
                
                'action',
                'action_label',
                
                'cost',
                
                'cost_type',
                'cost_type_label',
                
                'timestamp',
                'notes',
    
                'modified_by',
                'modified_by_name',
                'modified_by_email'
            
            ]


class CMSVehicleReportingSerializer(ModelSerializer):
    vehicle_wheels = SerializerMethodField('vehicle_wheels_name_method', required=False, allow_null=True)
    vehicle_status_name = SerializerMethodField('vehicle_status_name_method', required=False, allow_null=True)
    driver_name = SerializerMethodField('driver_name_method', allow_null=True, required=False, read_only=True)
    vehicle_name = SerializerMethodField('vehicle_name_method', allow_null=True, required=False, read_only=True)

    client_name = SerializerMethodField('client_name_method', allow_null=True, required=False, read_only=True)
    destination_name = SerializerMethodField('destination_name_method', allow_null=True, required=False, read_only=True)
    loading_location_name = SerializerMethodField('loading_location_name_method', allow_null=True, required=False, read_only=True)
    loading_city_name = SerializerMethodField('loading_city_name_method', allow_null=True, required=False, read_only=True)
    supervisor_name = SerializerMethodField('supervisor_name_method', allow_null=True, required=False, read_only=True)

    def vehicle_status_name_method(self, obj):
        if obj.vehicle_status:
            return obj.vehicle_status.label
        else:
            return None

    def vehicle_wheels_name_method(self, obj):
        if obj.vehicle.wheels:
            return str(obj.vehicle.wheels)
        else:
            return None

    def driver_name_method(self, obj):
        if obj.driver:
            return obj.driver.name
        else:
            return None

    def vehicle_name_method(self, obj):
        if obj.vehicle:
            return obj.vehicle.name
        else:
            return None

    def client_name_method(self, obj):
        if obj.client:
            return obj.client.name
        else:
            return None

    def destination_name_method(self, obj):
        if obj.destination:
            return obj.destination.name
        else:
            return None

    def loading_location_name_method(self, obj):
        if obj.loading_location:
            return obj.loading_location.name
        else:
            return None

    def loading_city_name_method(self, obj):
        if obj.loading_city:
            return obj.loading_city.name
        else:
            return None

    def supervisor_name_method(self, obj):
        if obj.supervisor:
            return obj.supervisor.name
        else:
            return None

    class Meta:
        model = CMSVehicleReporting
        fields = \
        [
            'id',
            'customer',
            'vehicle',
            'vehicle_name',
            'driver',
            'driver_name',
            'vehicle_wheels',
            'vehicle_status',
            'vehicle_status_name',
            'timestamp',

            # Data from Excel
            'loading_location',
            'loading_location_name',
            'loading_city',
            'loading_city_name',
            'destination',
            'destination_name',
            'vms',
            'trip_number',
            'order_number',

            'client',
            'client_name',
            # Timestamps for different events in the trip
            'trip_start_datetime',
            'loaded_datetime',

            'stops_loaded_duration',

            'arrival_datetime',
            'unloaded_datetime',

            'halting',
            'stops_unloading_duration',

            'loaded_workshop_in',
            'loaded_workshop_out',
            'loaded_work_order_number',
            'loaded_workshop_remarks',
            'loaded_workshop_duration',

            'unloaded_workshop_in',
            'unloaded_workshop_out',
            'unloaded_work_order_number',
            'unloaded_workshop_remarks',
            'unloaded_workshop_duration',


            'km_loaded',
            'km_unloaded',

            'office',

            'supervisor',
            'supervisor_name',



        ]