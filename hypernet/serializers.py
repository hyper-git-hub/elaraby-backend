import traceback

from django.core.exceptions import ObjectDoesNotExist
from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
    Field
    )

from customer.models import CustomerClients
from hypernet.enums import DeviceTypeEntityEnum, OptionsEnum, IOFOptionsEnum, DeviceTypeAssignmentEnum
from hypernet.models import HypernetNotification, DeviceViolation
from options.models import Options
from user.models import User
from .models import Entity, \
    Assignment, CustomerDevice
from rest_framework.serializers import ValidationError
from django.db.models import  F

class BinSerializer(ModelSerializer):
    device_name_method = SerializerMethodField('customer_devices')
    modified_by_name = SerializerMethodField('modified_name', allow_null=True, required=False, read_only=True)
    modified_by_email = SerializerMethodField('modified_email', allow_null=True, required=False, read_only=True)
    module_name = SerializerMethodField('module_method', required=False, allow_null=True)
    status_label = SerializerMethodField('status_method', required=False, allow_null=True)
    entity_sub_type_name = SerializerMethodField('entity_sub_type_name_method', required=False, allow_null=True)
    bin_contract_label = SerializerMethodField('bin_contract_label_method', required=False, allow_null=True, read_only=True)
    bin_contract = SerializerMethodField('bin_contract_method', required=False, allow_null=True, read_only=True)
    client_label = SerializerMethodField('client_label_method', allow_null=True, required=False, read_only=True)
    
    def status_method(self, obj):
        if obj.status:
            stat = obj.status.label
            return stat
        else:
            return None
        
    def entity_sub_type_name_method(self, obj):
        if obj.entity_sub_type:
            type = obj.entity_sub_type.label
            return type
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
    
    def customer_devices(self, obj):
        if self.context['request'] is not None:
            if self.context['request'].method == 'PATCH' or self.context['request'].method == 'POST':
                if self.context['request'].method == 'PATCH':
                    try:
                        device = CustomerDevice.objects.get(pk=obj.device_name_id)
                        device.assigned=False
                        device.save()
                    except:
                        pass
                req = self.context['request']
                try:
                    device = CustomerDevice.objects.get(pk=req.data['device_name'])
                    device.assigned = False
                    device.save()

                    obj.device_name_id = req.data['device_name']
                    obj.save()
                except:
                    pass
            return None if not obj.device_name else obj.device_name.device_id
    
    
    def bin_contract_label_method(self, obj):
        if self.context['request'] is not None:
            if self.context['request'].method == 'GET':
                try:
                    contract = Assignment.objects.get(child__type_id=DeviceTypeEntityEnum.CONTRACT, parent_id=obj.id, status_id=OptionsEnum.ACTIVE).child
                    return contract.name
                except:
                    return None
            else:
                return None
    
    def bin_contract_method(self, obj):
        if self.context['request'] is not None:
            if self.context['request'].method == 'GET':
                try:
                    contract = Assignment.objects.get(child__type_id=DeviceTypeEntityEnum.CONTRACT, parent_id=obj.id, status_id=OptionsEnum.ACTIVE).child
                    return contract.id
                except:
                    return None
            else:
                return None
    
    def client_label_method(self, obj):
        if obj.client:
            client = obj.client.name
            return client
        else:
            return None
    
    class Meta:
        model = Entity
        fields = (
            # Common fields to be included in every Entity serializer
            'id',
            'name',
            'type',
            'customer',
        
            'status',
            'status_label',
            'module',
            'module_name',
        
            'modified_by',
            'modified_by_name',
            'modified_by_email',
        
            'created_datetime',
            'modified_datetime',
            'end_datetime',
            'assignments',
            # Truck specific fields
            'device_name',
            'device_name_method',
            'volume',
            'source_latlong',
            'description',
            # Skip size
            'weight',

            'entity_sub_type',
            'entity_sub_type_name',
            'client',
            'client_label',
            'bin_contract',
            'bin_contract_label',
        
            # Operational Status
            'obd2_compliant'
        )


class TruckSerializer(ModelSerializer):
    photo = SerializerMethodField('img_url', required=False)
    # customer_devices = SerializerMethodField()
    module_name = SerializerMethodField('module_method', required=False, allow_null=True)
    status_label = SerializerMethodField('status_method', required=False, allow_null=True)
    modified_by_name = SerializerMethodField('modified_name', allow_null=True, required=False, read_only=True)
    modified_by_email = SerializerMethodField('modified_email', allow_null=True, required=False, read_only=True)
    entity_sub_type_name = SerializerMethodField('entity_sub_type_name_method', required=False, allow_null=True)
    threshold_value = SerializerMethodField('threshold_method', required=False, allow_null=True)



    def threshold_method(self, obj):
        if obj.speed:
            try:
                type = DeviceViolation.objects.get(violation_type_id=IOFOptionsEnum.SPEED, device_id=obj.id,
                                                      status_id=OptionsEnum.ACTIVE)
                return type.threshold_number

            except:
                return None
        else:
            return None

    def entity_sub_type_name_method(self, obj):
        if obj.entity_sub_type:
            type = obj.entity_sub_type.label
            return type
        else:
            return None

    def img_url(self, obj):
        if self.context['request'].method == 'POST' or self.context['request'].method == 'PATCH':
            req = self.context['request']
            obj.photo = req.data.get('photo')
            obj.save()
        elif self.context['request'].method == 'GET':
            try:
                photo_url = obj.photo.url
                return self.context['request'].build_absolute_uri(photo_url)
            except Exception as e:
                print(str(e))
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

    # TODO Testing of this method.
    def get_customer_devices(self, obj):
        if self.context['request'].method == 'PATCH' or self.context['request'].method == 'POST':
            if self.context['request'].method == 'PATCH':
                try:
                    device = CustomerDevice.objects.get(pk=obj.device_name.id)
                    device.assigned = False
                    device.save()
                    print('old device: ' + device.device_id)
                except:
                    traceback.print_exc()
                    pass
            req = self.context['request']
            try:
                device = CustomerDevice.objects.get(pk=req.data.get('device_name'))
                device.assigned = True
                device.save()
                print('device name: '+device.device_id)

                obj.device_name.id = req.data.get('device_name')
                obj.save()
                print('name of latest device: '+obj.device_name.device_id)
            except:
                traceback.print_exc()
                pass

        return None if not obj.device_name else obj.device_name.device_id

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
        model = Entity
        fields = [
            # Common fields to be included in every Entity serializer
            'id',
            'name',
            'type',
            'customer',
            'module',
            'module_name',

            'status',
            'status_label',
            'modified_by',
            'modified_by_name',
            'modified_by_email',

            'created_datetime',
            'modified_datetime',
            'end_datetime',
            'assignments',
            # Truck specific fields
            
            'device_name',
            # 'customer_devices',

            #Speed Check and Threshold Value
            'speed',
            'volume',
            'density',
            'temperature',
            'location',


            'registration',
            'engine_number',
            'chassis_number',
            'make',
            'model',
            'color',
            'year',
            'odo_reading',
            'engine_capacity',
            'wheels',
            'volume_capacity',
            'date_commissioned',
            'obd2_compliant',
            'leased_owned',
            'photo',
            'entity_sub_type',
            'entity_sub_type_name',
            'threshold_value',
        ]


class DriverSerializer(ModelSerializer):
    photo_method = SerializerMethodField('img_url', required=False)
    gender_label = SerializerMethodField('gender_method', required=False, allow_null=True)
    module_name = SerializerMethodField('module_method', required=False, allow_null=True)
    marital_status_label = SerializerMethodField('marital_method', required=False, allow_null=True)
    status_label = SerializerMethodField('status_method', required=False, allow_null=True)
    age = SerializerMethodField('age_cal', required=False, allow_null=True)
    modified_by_name = SerializerMethodField('modified_name', allow_null=True, required=False, read_only=True)
    modified_by_email = SerializerMethodField('modified_email', allow_null=True, required=False, read_only=True)
    driver_email = SerializerMethodField('email_method', allow_null=True, required=False, read_only=True)


    def email_method(self, obj):
        if obj:
            try:
                email = User.objects.get(associated_entity_id=obj.id).email
            except:
                email = None
            return email


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

    def gender_method(self, obj):
        if obj.gender:
            gender = obj.gender.label
            return gender
        else:
            return None

    def age_cal(self, obj):
        if obj.dob:
            import datetime
            age = datetime.date.today().year - obj.dob.year
            return age
        else:
            return None

    def module_method(self, obj):
        if obj.module:
            mod = obj.module.name
            return mod
        else:
            return None

    def status_method(self, obj):
        if obj.status:
            stat = obj.status.label
            return stat
        else:
            return None

    def marital_method(self, obj):
        if obj.marital_status:
            m_status = obj.marital_status.label
            return m_status
        else:
            return None

    def img_url(self, obj):
        if self.context['request'].method == 'POST' or self.context['request'].method == 'PATCH':
            req = self.context['request']
            obj.photo = req.data.get('photo')
            obj.save()
        elif self.context['request'].method == 'GET':
            try:
                photo_url = obj.photo.url
                return self.context['request'].build_absolute_uri(photo_url)
            except Exception as e:
                # print(str(e))
                return None

    class Meta:
        model = Entity
        fields = [
            # Common fields to be included in every Entity serializer
            'id',
            'name',
            'type',
            'customer',
            'assignments',

            'module',
            'module_name',

            'status',
            'status_label',

            'modified_by',
            'modified_by_name',
            'modified_by_email',

            'created_datetime',
            'modified_datetime',
            'end_datetime',
            # Driver specific fields
            'cnic',
            'dob',
            'date_of_joining',
            'salary',

            'marital_status',
            'marital_status_label',
            'gender',
            'gender_label',
            'photo',
            'photo_method',
            'age',
            
            'driver_email',

        ]


class TerritorySerializer(ModelSerializer):
    status_label = SerializerMethodField('status_method', required=False, allow_null=True)
    module_name = SerializerMethodField('module_method', required=False, allow_null=True)
    modified_by_name = SerializerMethodField('modified_name', allow_null=True, required=False, read_only=True)
    modified_by_email = SerializerMethodField('modified_email', allow_null=True, required=False, read_only=True)

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


    class Meta:
        model = Entity
        fields = [
            'id',
            'name',
            'type',
            'customer',

            'module',
            'module_name',

            'status',
            'status_label',

            'modified_by',
            'modified_by_name',
            'modified_by_email',

            'created_datetime',
            'modified_datetime',
            'end_datetime',
            'assignments',
            'territory_type',
            'territory',
            'description',
        ]


class JobSerializer(ModelSerializer):

    class Meta:
        model = Entity
        fields = [
            'id',
            'name',
            'type',
            'customer',
            'module',
            'status',
            'modified_by',
            'created_datetime',
            'modified_datetime',
            'end_datetime',
            'assignments',
            'description',
            'job_start_datetime',
            'job_end_datetime',
            'job_status',
            'source_latlong',
            'destination_latlong',
        ]


class MaintenanceSerializer(ModelSerializer):
    name = SerializerMethodField('maintenance_name', required=False, allow_null=True)

    def maintenance_name(self, obj):
        req = self.context['request']
        if self.context['request'].method == 'POST' or self.context['request'].method == 'PATCH':
            try:
                opt = str(Options.objects.get(pk=req.data.get('maintenance_type')).label)
                truck = str(Entity.objects.get(pk=req.data.get('truck')).name)
                obj.name = opt + " : " + truck
                obj.save()
            except Exception as e:
                print(str(e))

    class Meta:
        model = Entity
        fields = [
            'id',
            'name',
            'type',
            'customer',
            'module',
            'status',
            'modified_by',
            'created_datetime',
            'modified_datetime',
            'end_datetime',
            'description',
            # Using similar columns for maintenance
            # 'job_start_datetime',
            'job_status',
            # 'job_type',
            # 'routine_type',
            'maintenance_type',
        ]


class CustomerClientsSerializer(ModelSerializer):
    modified_by_name = SerializerMethodField('modified_name', allow_null=True, required=False, read_only=True)
    modified_by_email = SerializerMethodField('modified_email', allow_null=True, required=False, read_only=True)
    status_label = SerializerMethodField('status_method', required=False, allow_null=True)

    def status_method(self, obj):
        if obj.status:
            stat = obj.status.label
            return stat
        else:
            return None

    def modified_name(self, obj):
        if obj.modified_by:
            if obj.modified_by.last_name and obj.modified_by.last_name:
                email = obj.modified_by.first_name + ' ' + obj.modified_by.last_name
            else:
                email = None
            return email
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


    class Meta:
        model = CustomerClients
        fields = [
            'id',
            'name',
            'customer',
            'address',
            'contact_number',
            'email',
            'status',
            'status_label',
            'description',

            'modified_by',
            'modified_by_name',
            'modified_by_email',

            'created_datetime',
            'modified_datetime',
            'end_datetime',
            'party_code',

        ]


class DumpingSiteSerializer(ModelSerializer):
    status_label = SerializerMethodField('status_method', required=False, allow_null=True)
    module_name = SerializerMethodField('module_method', required=False, allow_null=True)
    modified_by_name = SerializerMethodField('modified_name', allow_null=True, required=False, read_only=True)
    modified_by_email = SerializerMethodField('modified_email', allow_null=True, required=False, read_only=True)
    customer_name = SerializerMethodField('customer_method', allow_null=True, required=False, read_only=True)


    def customer_method(self, obj):
        if obj.customer:
            return obj.customer.name
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
        model = Entity

        fields = [
        'id',
        'name',
        'type',
        'customer',
        'customer_name',
        'module',
        'status',
        'modified_by',
        'status_label',
        'module_name',
        'modified_by_name',
        'modified_by_email',
        # 'created_datetime',
        # 'modified_datetime',
        # 'end_datetime',
        'description',
        'source_latlong',
        'created_datetime',
        'modified_datetime',

    ]


class RfidScannerSerializer(ModelSerializer):
    status_label = SerializerMethodField('status_method', required=False, allow_null=True)
    module_name = SerializerMethodField('module_method', required=False, allow_null=True)
    modified_by_name = SerializerMethodField('modified_name', allow_null=True, required=False, read_only=True)
    modified_by_email = SerializerMethodField('modified_email', allow_null=True, required=False, read_only=True)
    customer_name = SerializerMethodField('customer_method', allow_null=True, required=False, read_only=True)

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
                email = None
            return email
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
        model = Entity

        fields = [
            'id',
            'name',
            'type',
            'customer',
            'customer_name',
    
            'module',
            'module_name',
    
            'status',
            'status_label',
    
            'modified_by',
            'modified_by_name',
            'modified_by_email',
    
            'created_datetime',
            'modified_datetime',
            # 'end_datetime',
            'description',
            # 'source_latlong',

        ]

    def validate(self, data):
        if self.context['request'].method == 'POST':
            try:
                Entity.objects.get(name=data['name'], type_id=data['type'])
                raise ValidationError(detail='RFID scanner is already registered in the system. Please contact your administrator.')
            except ObjectDoesNotExist:
                pass
        return data


class RfidCardTagSerializer(ModelSerializer):

    class Meta:
        model = Entity

        fields = [
        'id',
        'name',
        'type',
        'customer',
        'module',
        'status',
        'modified_by',
        'created_datetime',
        'modified_datetime',
        # 'end_datetime',
        # 'source_latlong',
        'obd2_compliant',

    ]


class ClientContractSerializer(ModelSerializer):
    status_label = SerializerMethodField('status_method', required=False, allow_null=True)
    module_name = SerializerMethodField('module_method', required=False, allow_null=True)
    entity_sub_type_name = SerializerMethodField('entity_sub_type_method', required=False, allow_null=True)
    modified_by_name = SerializerMethodField('modified_name', allow_null=True, required=False, read_only=True)
    modified_by_email = SerializerMethodField('modified_email', allow_null=True, required=False, read_only=True)
    customer_name = SerializerMethodField('customer_method', allow_null=True, required=False, read_only=True)
    client_name = SerializerMethodField('client_method', allow_null=True, required=False, read_only=True)
    # name = SerializerMethodField('name_method', allow_null=True, required=False, read_only=True)
    party_code = SerializerMethodField('party_code_name', allow_null=True, required=False, read_only=True)
    leased_owned_name = SerializerMethodField('leased_owned_method', allow_null=True, required=False, read_only=True)

    def modified_email(self, obj):
            if obj.modified_by:
                if obj.modified_by.email:
                    email = obj.modified_by.email
                else:
                    email = None
                return email
            else:
                return None

    # def name_method(self, obj):
    #     req = self.context['request']
    #     if self.context['request'].method == 'POST' or self.context['request'].method == 'PATCH':
    #         obj.name = obj.client.name + ' ' + obj.type.name + ' '+ str(obj.job_start_datetime.date()) + '|'+ str(obj.job_end_datetime.date())
    #         obj.save()
    #     else:
    #         return obj.name

    def customer_method(self, obj):
        if obj.customer:
            return obj.customer.name
        else:
            return None

    def client_method(self, obj):
        if obj.client:
            return obj.client.__str__()
        else:
            return None

    def party_code_name(self, obj):
        if obj.client:
            return obj.client.party_code
        else:
            return None

    def modified_name(self, obj):
        if obj.modified_by:
            if obj.modified_by.last_name and obj.modified_by.last_name:
                email = obj.modified_by.first_name + ' ' + obj.modified_by.last_name
            else:
                email = None
            return email
        else:
            return None

    def status_method(self, obj):
        if obj.status:
            stat = obj.status.label
            return stat
        else:
            return None

    def leased_owned_method(self, obj):
        if obj.leased_owned:
            return obj.leased_owned.label
        else:
            return None

    def entity_sub_type_method(self, obj):
        if obj.entity_sub_type:
            stat = obj.entity_sub_type.label
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
        model = Entity

        fields = [
        'id',
        'type',
        'name',
        'customer',
        'customer_name',
        'module',
        'module_name',
        'status',
        'status_label',
        'modified_by',
        'modified_by_name',
        'modified_by_email',
        'created_datetime',
        'modified_datetime',
        'description',
        'entity_sub_type',
        'entity_sub_type_name',

        #Contract start/end dates respectively
        'date_commissioned',
        'date_of_joining',

        #Unit Price
        'weight',
        'client',
        'client_name',
        'skip_rate',
        'party_code',

        #Contract Invoice Type
        'leased_owned',
        'leased_owned_name',
        #Rate(Fixed rate) for calculations of Invoice, for Trip and Weight based.
        'squad_number',

        # 'dob',
        # 'date_of_joining',



    ]


class ClientSupervisorSerializer(ModelSerializer):
    status_label = SerializerMethodField('status_method', required=False, allow_null=True)
    module_name = SerializerMethodField('module_method', required=False, allow_null=True)
    modified_by_name = SerializerMethodField('modified_name', allow_null=True, required=False, read_only=True)
    modified_by_email = SerializerMethodField('modified_email', allow_null=True, required=False, read_only=True)
    customer_name = SerializerMethodField('customer_method', allow_null=True, required=False, read_only=True)
    client_name = SerializerMethodField('client_method', allow_null=True, required=False, read_only=True)
    area_name = SerializerMethodField('supervisor_area_label_method', allow_null=True, required=False, read_only=True)
    contract_name = SerializerMethodField('supervisor_contract_label_method', allow_null=True, required=False, read_only=True)
    area_id = SerializerMethodField('supervisor_area_method', allow_null=True, required=False, read_only=True)
    contract_id = SerializerMethodField('supervisor_contract_method', allow_null=True, required=False, read_only=True)
    party_code = SerializerMethodField('party_code_name', allow_null=True, required=False, read_only=True)

    def customer_method(self, obj):
        if obj.customer:
            return obj.customer.name
        else:
            return None

    def client_method(self, obj):
        if obj.client:
            return obj.client.__str__()
        else:
            return None

    def modified_name(self, obj):
        if obj.modified_by:
            if obj.modified_by.last_name and obj.modified_by.last_name:
                email = obj.modified_by.first_name + ' ' + obj.modified_by.last_name
            else:
                email = None
            return email
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

    def supervisor_area_label_method(self, obj):
        if self.context['request'] is not None:
            if self.context['request'].method == 'GET':
                try:
                    contract = Assignment.objects.get(child_id=obj.id,
                                                      type_id=DeviceTypeAssignmentEnum.SUPERVISOR_CONTRACT_ASSIGNMENT,
                                                      status_id=OptionsEnum.ACTIVE).parent
                    area = Assignment.objects.get(parent__type_id=DeviceTypeEntityEnum.AREA, child_id=contract.id,
                                                      status_id=OptionsEnum.ACTIVE).parent
                    return area.name
                except:
                    return None
            else:
                return None

    def supervisor_area_method(self, obj):
        if self.context['request'] is not None:
            if self.context['request'].method == 'GET':
                try:
                    contract = Assignment.objects.get(child_id=obj.id,
                                                      type_id=DeviceTypeAssignmentEnum.SUPERVISOR_CONTRACT_ASSIGNMENT,
                                                      status_id=OptionsEnum.ACTIVE).parent
                    area = Assignment.objects.get(parent__type_id=DeviceTypeEntityEnum.AREA, child_id=contract.id,
                                                      status_id=OptionsEnum.ACTIVE).parent
                    return area.id
                except:
                    return None
            else:
                return None

    def party_code_name(self, obj):
        if obj.client:
            return obj.client.party_code
        else:
            return None

    def supervisor_contract_method(self, obj):
        if self.context['request'] is not None:
            if self.context['request'].method == 'GET':
                try:
                    return Assignment.objects.get(child_id=obj.id,
                                                      type_id=DeviceTypeAssignmentEnum.SUPERVISOR_CONTRACT_ASSIGNMENT,
                                                      status_id=OptionsEnum.ACTIVE).parent.id
                except:
                    return None
            else:
                return None

    def supervisor_contract_label_method(self, obj):
        if self.context['request'] is not None:
            if self.context['request'].method == 'GET':
                try:
                    return Assignment.objects.get(child_id=obj.id,
                                                      type_id=DeviceTypeAssignmentEnum.SUPERVISOR_CONTRACT_ASSIGNMENT,
                                                      status_id=OptionsEnum.ACTIVE).parent.name
                except:
                    return None
            else:
                return None
    class Meta:
        model = Entity

        fields = [
        'id',
        'type',
        'name',
        'customer',
        'customer_name',

        'module',
        'module_name',
        'status',
        'status_label',

        'modified_by',
        'modified_by_name',
        'modified_by_email',

        'created_datetime',
        'modified_datetime',


        #SHIFT START TIME END TIME
        # 'start_time',
        # 'end_time',

        #Email
        # 'destination_address',
        #Addresse
        # 'source_latlong',
        #Contact_no
       'destination_latlong',
        #No of Bins
        # 'ethnicity',

        # 'age',
        'client',
        'client_name',
        
        'area_id',
        'area_name',
        'contract_id',
        'contract_name',
        'party_code'
    ]


class SortingFacilitySerializer(ModelSerializer):
    status_label = SerializerMethodField('status_method', required=False, allow_null=True)
    module_name = SerializerMethodField('module_method', required=False, allow_null=True)
    modified_by_name = SerializerMethodField('modified_name', allow_null=True, required=False, read_only=True)
    modified_by_email = SerializerMethodField('modified_email', allow_null=True, required=False, read_only=True)
    customer_name = SerializerMethodField('customer_method', allow_null=True, required=False, read_only=True)


    def customer_method(self, obj):
        if obj.customer:
            return obj.customer.name
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
        model = Entity

        fields = [
        'id',
        'name',
        'type',
        'customer',
        'customer_name',
        'module',
        'status',
        'modified_by',
        'status_label',
        'module_name',
        'modified_by_name',
        'modified_by_email',
        # 'created_datetime',
        # 'modified_datetime',
        # 'end_datetime',
        'description',
        'source_latlong',
        'created_datetime',
        'modified_datetime',

    ]


class NotificationSerializer(ModelSerializer):

    assigned_device = SerializerMethodField('device_name', required=False, allow_null=True)
    assigned_device_id = SerializerMethodField('device_id', required=False, allow_null=True)
    notification_id = SerializerMethodField('notification_id_method', required=False, allow_null=True)
    activity_type = SerializerMethodField('activity_type_method', required=False, allow_null=True)
    activity_status = SerializerMethodField('activity_status_method', required=False, allow_null=True)
    status = SerializerMethodField('status_method', required=False, allow_null=True)
    status_id = SerializerMethodField('status_id_method', required=False, allow_null=True)
    customer_name = SerializerMethodField('customer_name_method', required=False, allow_null=True)
    customer_id = SerializerMethodField('customer_id_method', required=False, allow_null=True)
    created_time = SerializerMethodField('created_time_method', required=False, allow_null=True)
    #is_viewed = SerializerMethodField('is_viewed_method', required=False, allow_null=True)
    notification_type = SerializerMethodField('notification_type_method', required=False, allow_null=True)


    def device_name(self, obj):
        if obj.device:
            device = obj.device.name
            return device
        else:
            return None

    def device_id(self, obj):
        if obj.device:
            device = obj.device.id
            return device
        else:
            return None

    def notification_id_method(self, obj):
        if obj:
            notification = obj.id
            return notification
        else:
            return None

    def activity_type_method(self, obj):
        if obj.activity:
            activity = obj.activity.activity_schedule.activity_type.label
            return activity
        else:
            return None

    def activity_status_method(self, obj):
        if obj.activity:
            activity = obj.activity.activity_status.label
            return activity
        else:
            return None

    def status_method(self, obj):
        if obj:
            status = obj.status.label
            return status
        else:
            return None

    def status_id_method(self, obj):
        if obj:
            status = obj.status.id
            return status
        else:
            return None

    def customer_name_method(self, obj):
        if obj:
            customer = obj.customer.name
            return customer
        else:
            return None

    def customer_id_method(self, obj):
        if obj:
            customer_id = obj.customer.id
            return customer_id
        else:
            return None

    def created_time_method(self, obj):
        if obj:
            created_time = obj.created_datetime.time()
            return created_time
        else:
            return None



    def notification_type_method(self, obj):
        if obj:
            type = obj.type.id
            return type
        else:
            return None

    class Meta:
        model = HypernetNotification
        fields = [
            'assigned_device',
            'assigned_device_id',
            'notification_id',
            'activity_id',
            'activity_type',
            'activity_status',
            'status',
            'status_id',
            'customer_name',
            'customer_id',
            'created_datetime',
            'created_time',
            'title',
            'notification_type'

        ]