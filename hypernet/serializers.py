import traceback

from datetime import timedelta
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
    Field,
    CharField
    )
from customer.models import CustomerClients
from hypernet.constants import LAST_WEEK
from hypernet.enums import DeviceTypeEntityEnum, OptionsEnum, IOFOptionsEnum, DeviceTypeAssignmentEnum, FFPOptionsEnum, \
    ModuleEnum
from hypernet.models import HypernetNotification, DeviceViolation, HypernetPostData, InvoiceData, UserEntityAssignment, \
    EntityDocument,HypernetPreData
from iof.models import BinCollectionData
from options.models import Options
from user.models import User

from .models import Entity, \
    Assignment, CustomerDevice
from ffp.models import AttendanceRecord, EmployeeViolations
from rest_framework.serializers import ValidationError
from django.db.models import F, Avg
from django.utils import timezone
import itertools
from iop.models import *
from iof.models import LogisticAggregations

from .enums import Enum
enum=Enum()

class BinSerializer(ModelSerializer):
    device_name_method = SerializerMethodField('customer_devices')
    modified_by_name = SerializerMethodField('modified_name', allow_null=True, required=False, read_only=True)
    modified_by_email = SerializerMethodField('modified_email', allow_null=True, required=False, read_only=True)
    module_name = SerializerMethodField('module_method', required=False, allow_null=True)
    status_label = SerializerMethodField('status_method', required=False, allow_null=True)
    entity_sub_type_name = SerializerMethodField('entity_sub_type_name_method', required=False, allow_null=True)
    skip_size_name = SerializerMethodField('skip_size_name_method', required=False, allow_null=True)
    leased_owned_name = SerializerMethodField('leased_owned_name_method', required=False, allow_null=True)
    # bin_contract = SerializerMethodField('bin_contract_method', required=False, allow_null=True, read_only=True)
    client_name = SerializerMethodField('client_label_method', allow_null=True, required=False, read_only=True)
    maintenance_status = SerializerMethodField('maintenance_status_method', allow_null=True, required=False, read_only=True)

    assigned_contract = SerializerMethodField('bin_contract_label_method', required=False, allow_null=True, read_only=True)
    assigned_contract_id = SerializerMethodField('bin_contract_id_method', required=False, allow_null=True, read_only=True)
    assigned_contract_type = SerializerMethodField('assigned_contract_type_method', required=False, allow_null=True, read_only=True)
    assigned_area = SerializerMethodField('assigned_area_method', allow_null=True, required=False, read_only=True)
    assigned_area_id = SerializerMethodField('assigned_area_id_method', allow_null=True, required=False, read_only=True)
    assigned_location = SerializerMethodField('assigned_location_method', allow_null=True, required=False, read_only=True)
    assigned_location_id = SerializerMethodField('assigned_location_id_method', allow_null=True, required=False, read_only=True)
    last_collection = SerializerMethodField('last_collection_method', allow_null=True, required=False, read_only=True)
    activity_status = SerializerMethodField('activity_status_method', allow_null=True, required=False, read_only=True)
    current_activity = SerializerMethodField('current_activity_method', allow_null=True, required=False, read_only=True)
    skip_rate = SerializerMethodField('skip_rate_method', allow_null=True, required=False, read_only=True)
    party_code = SerializerMethodField('party_code_method', allow_null=True, required=False, read_only=True)

    old_area = SerializerMethodField('old_area_method', allow_null=True, required=False, read_only=True)
    old_contract = SerializerMethodField('old_contract_method', allow_null=True, required=False, read_only=True)
    old_contract_type = SerializerMethodField('old_contract_type_method', required=False, allow_null=True,
                                                   read_only=True)
    old_location = SerializerMethodField('old_location_method', allow_null=True, required=False, read_only=True)

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

    def skip_size_name_method(self, obj):
        if obj.skip_size:
            type = obj.skip_size.label
            return type
        else:
            return None

    def leased_owned_name_method(self, obj):
        if obj.leased_owned:
            type = obj.leased_owned.label
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
                    if contract:
                        try:
                            assigned_area = Assignment.objects.get(child__id=contract.id,
                                                                   parent__type_id=DeviceTypeEntityEnum.AREA,
                                                                   status_id=OptionsEnum.ACTIVE).parent

                            if assigned_area:
                                try:
                                    assigned_location = Assignment.objects.get(child__id=contract.id,
                                                                           parent__type_id=DeviceTypeEntityEnum.LOCATION,
                                                                           status_id=OptionsEnum.ACTIVE).parent

                                    return contract.name + " - " + assigned_area.name + " - " + assigned_location.name
                                except:
                                    assigned_location = None


                            return contract.name+" - "+assigned_area.name
                        except:
                            try:
                                assigned_location = Assignment.objects.get(child__id=contract.id,
                                                                       parent__type_id=DeviceTypeEntityEnum.LOCATION,
                                                                       status_id=OptionsEnum.ACTIVE).parent
                                return contract.name + " - " + assigned_area.name + " - " + assigned_location.name
                            except:
                                return contract.name
                except:
                    return None
            else:
                return None

    def bin_contract_id_method(self, obj):
        if self.context['request'] is not None:
            if self.context['request'].method == 'GET':
                try:
                    return Assignment.objects.get(child__type_id=DeviceTypeEntityEnum.CONTRACT, parent_id=obj.id, status_id=OptionsEnum.ACTIVE).child.id
                except:
                    return None
            else:
                return None

    def assigned_contract_type_method(self, obj):
        if self.context['request'] is not None:
            if self.context['request'].method == 'GET':
                try:
                    return Assignment.objects.get(child__type_id=DeviceTypeEntityEnum.CONTRACT, parent=obj, type_id=DeviceTypeAssignmentEnum.CONTRACT_ASSIGNMENT, status_id=OptionsEnum.ACTIVE).child.leased_owned.label

                except:
                    # traceback.print_exc()
                    return None

    def client_label_method(self, obj):
        if obj.client:
            return obj.client.party_code+" - ( "+obj.client.name+" )"
        else:
            return None

    def maintenance_status_method(self, obj):
        from iof.models import LogisticMaintenance
        try:
            data = LogisticMaintenance.objects.filter(truck=obj).order_by('-issued_datetime')
            if data:
                data = data[0]
                return data.status.label
            else:
                return "-"
        except:
            traceback.print_exc()
            return "-"

    def assigned_area_method(self, obj):
        if self.context.get('request') is not None:
            if self.context['request'].method == 'GET':
                try:
                    return Assignment.objects.get(child__type_id=DeviceTypeEntityEnum.AREA, parent_id=obj.id, status_id=OptionsEnum.ACTIVE).child.name
                except:
                    # traceback.print_exc()
                    return None
            else:
                req = self.context['request']
                contract_id = Entity.objects.get(id=req.data.get('contract'))
                current_ass = None
                old_ass = None
                try:
                    area = Assignment.objects.get(type_id=DeviceTypeAssignmentEnum.AREA_CONTRACT_ASSIGNMENT,
                                                  child_id=contract_id, status_id=OptionsEnum.ACTIVE).parent
                    old_ass = Assignment.objects.get(type_id=DeviceTypeAssignmentEnum.AREA_ASSIGNMENT, parent=obj,
                                                     status_id=OptionsEnum.ACTIVE)
                    current_ass = Assignment.objects.get(child_id=area.id, parent=obj,
                                                         status_id=OptionsEnum.ACTIVE,
                                                         type_id=DeviceTypeAssignmentEnum.AREA_ASSIGNMENT)
                except:
                    if old_ass:
                        if current_ass:
                            pass
                        else:
                            # If code reaches here then old ass exists but current is diff so create new assignment.
                            old_ass.status_id = OptionsEnum.INACTIVE
                            old_ass.save()
                            bin_area_assignment = Assignment(
                                name=area.name + " Assigned to " + obj.name,
                                child_id=area.id,
                                parent_id=obj.id,
                                customer_id=obj.customer.id,
                                module_id=ModuleEnum.IOL,
                                type_id=DeviceTypeAssignmentEnum.AREA_ASSIGNMENT,
                                status_id=OptionsEnum.ACTIVE,
                                modified_by_id=obj.modified_by_id, )
                            bin_area_assignment.save()
                    else:  # No assignment at all, fresh item create assignment
                        bin_area_assignment = Assignment(
                            name=area.name + " Assigned to " + obj.name,
                            child_id=area.id,
                            parent_id=obj.id,
                            customer_id=obj.customer.id,
                            module_id=ModuleEnum.IOL,
                            type_id=DeviceTypeAssignmentEnum.AREA_ASSIGNMENT,
                            status_id=OptionsEnum.ACTIVE,
                            modified_by_id=obj.modified_by_id, )
                        bin_area_assignment.save()

    def assigned_area_id_method(self, obj):
        if self.context.get('request') is not None:
            if self.context['request'].method == 'GET':
                try:
                    return Assignment.objects.get(child__type_id=DeviceTypeEntityEnum.AREA, parent_id=obj.id, status_id=OptionsEnum.ACTIVE).child.id
                except:
                    # traceback.print_exc()
                    return None
            else:
                return None

    def assigned_location_method(self, obj):
        if self.context.get('request') is not None:
            if self.context['request'].method == 'GET':
                try:
                    return Assignment.objects.get(child__type_id=DeviceTypeEntityEnum.AREA, parent_id=obj.id, status_id=OptionsEnum.ACTIVE).child.name
                except:
                    # traceback.print_exc()
                    return None
            else:
                req = self.context['request']
                contract_id = Entity.objects.get(id=req.data.get('contract'))
                current_ass = None
                old_ass = None
                try:
                    location = Assignment.objects.get(type_id=DeviceTypeAssignmentEnum.LOCATION_CONTRACT_ASSIGNMENT,
                                                  child_id=contract_id, status_id=OptionsEnum.ACTIVE).parent
                    old_ass = Assignment.objects.get(type_id=DeviceTypeAssignmentEnum.LOCATION_ASSIGNMENT, parent=obj,
                                                     status_id=OptionsEnum.ACTIVE)
                    current_ass = Assignment.objects.get(child_id=location.id, parent=obj,
                                                         status_id=OptionsEnum.ACTIVE,
                                                         type_id=DeviceTypeAssignmentEnum.LOCATION_ASSIGNMENT)
                except:
                    if old_ass:
                        if current_ass:
                            pass
                        else:
                            # If code reaches here then old ass exists but current is diff so create new assignment.
                            old_ass.status_id = OptionsEnum.INACTIVE
                            old_ass.save()
                            bin_area_assignment = Assignment(
                                name=location.name + " Assigned to " + obj.name,
                                child_id=location.id,
                                parent_id=obj.id,
                                customer_id=obj.customer.id,
                                module_id=ModuleEnum.IOL,
                                type_id=DeviceTypeAssignmentEnum.LOCATION_ASSIGNMENT,
                                status_id=OptionsEnum.ACTIVE,
                                modified_by_id=obj.modified_by_id, )
                            bin_area_assignment.save()
                    else:  # No assignment at all, fresh item create assignment
                        bin_area_assignment = Assignment(
                            name=location.name + " Assigned to " + obj.name,
                            child_id=location.id,
                            parent_id=obj.id,
                            customer_id=obj.customer.id,
                            module_id=ModuleEnum.IOL,
                            type_id=DeviceTypeAssignmentEnum.LOCATION_ASSIGNMENT,
                            status_id=OptionsEnum.ACTIVE,
                            modified_by_id=obj.modified_by_id, )
                        bin_area_assignment.save()

    def assigned_location_id_method(self, obj):
        if self.context.get('request') is not None:
            if self.context['request'].method == 'GET':
                try:
                    return Assignment.objects.get(child__type_id=DeviceTypeEntityEnum.AREA, parent_id=obj.id, status_id=OptionsEnum.ACTIVE).child.id
                except:
                    # traceback.print_exc()
                    return None
            else:
                return None

    def last_collection_method(self, obj):
        if self.context['request'] is not None:
            if self.context['request'].method == 'GET':
                try:
                    data = BinCollectionData.objects.filter(action_item=obj).order_by('-timestamp').first()
                    if data:
                        return data.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
                    else:
                        return None
                except:
                    return None
            else:
                return None

    def activity_status_method(self, obj):
        try:
            return BinCollectionData.objects.get(action_item=obj, status_id=IOFOptionsEnum.UNCOLLECTED).activity.activity_status.id
        except:
            return None

    def current_activity_method(self, obj):
        try:
            return BinCollectionData.objects.get(action_item=obj, status_id=IOFOptionsEnum.UNCOLLECTED).activity.id
        except:
            return None

    def skip_rate_method(self, obj):
        if self.context['request'] is not None:
            if self.context['request'].method == 'GET':
                try:
                    return Assignment.objects.get(child__type_id=DeviceTypeEntityEnum.CONTRACT, parent_id=obj.id,
                                       status_id=OptionsEnum.ACTIVE).child.skip_rate
                except:
                    return None
            # else:
            #     try:
            #         obj.skip_rate = Assignment.objects.get(child__type_id=DeviceTypeEntityEnum.CONTRACT, parent_id=obj.id,
            #                            status_id=OptionsEnum.ACTIVE).child.skip_rate
            #         obj.save()
            #     except:
            #         return None

    def party_code_method(self, obj):
        if self.context['request'] is not None:
            if self.context['request'].method == 'GET':
                try:
                    return obj.client.party_code
                except:
                    # traceback.print_exc()
                    return None

    def old_area_method(self, obj):
        if self.context['request'] is not None:
            if self.context['request'].method == 'GET':
                try:

                    return Assignment.objects.filter(parent=obj,
                                                         type_id=DeviceTypeAssignmentEnum.AREA_ASSIGNMENT,
                                                         child__type_id=DeviceTypeEntityEnum.AREA,
                                                         status_id=OptionsEnum.INACTIVE).order_by('-created_datetime')[0].name
                except:
                    # traceback.print_exc()
                    return None

    def old_contract_method(self, obj):
        if self.context['request'] is not None:
            if self.context['request'].method == 'GET':
                try:

                    return Assignment.objects.filter(parent=obj,
                                                         type_id=DeviceTypeAssignmentEnum.CONTRACT_ASSIGNMENT,
                                                         child__type_id=DeviceTypeEntityEnum.CONTRACT,
                                                         status_id=OptionsEnum.INACTIVE).order_by('-created_datetime')[0].name
                except:
                    # traceback.print_exc()
                    return None

    def old_contract_type_method(self, obj):
        if self.context['request'] is not None:
            if self.context['request'].method == 'GET':
                try:
                    return Assignment.objects.filter(child__type_id=DeviceTypeEntityEnum.CONTRACT, parent_id=obj.id, type_id=DeviceTypeAssignmentEnum.CONTRACT_ASSIGNMENT, status_id=OptionsEnum.INACTIVE).order_by('-created_datetime')[0].child.leased_owned.label
                except:
                    return None

    def old_location_method(self, obj):
        if self.context['request'] is not None:
            if self.context['request'].method == 'GET':
                try:

                    return Assignment.objects.filter(parent=obj,
                                                         type_id=DeviceTypeAssignmentEnum.LOCATION_ASSIGNMENT,
                                                         child__type_id=DeviceTypeEntityEnum.LOCATION,
                                                         status_id=OptionsEnum.INACTIVE).order_by('-created_datetime')[0].name
                except:
                    # traceback.print_exc()
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
            # 'description',

            # SHypernetPreDatakip size
            'skip_size',
            'skip_size_name',

            'entity_sub_type',
            'entity_sub_type_name',
            'client_name',
            'client',
            # 'bin_contract', Removing this as this is NOT required at all for now, additional join removed


            # Operational Status
            'obd2_compliant',

            #Ownership of skip
            'leased_owned',
            'leased_owned_name',
            'maintenance_status',


            # Extra columns to be added for listing
            'activity_status',
            'assigned_area',
            'assigned_area_id',
            'assigned_location',
            'assigned_location_id',
            'assigned_contract',
            'assigned_contract_id',
            'assigned_contract_type',
            'last_collection',
            'activity_status',
            'current_activity',

            'old_contract',
            'old_contract_type',
            'old_area',
            'old_location',

            'skip_rate',
            'party_code',
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
                # traceback.print_exc()
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

            # Flag for administrative rights
            'speed'

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
    dump_territory = SerializerMethodField('dump_method', allow_null=True, required=False, read_only=True)

    def dump_method(self, obj):
        req = self.context['request']
        if req.method == 'POST' or req.method == 'PATCH':
            # add a new assignment or overwrite old one
            try:
                # If i can get it dont do anything just let is go...
                Assignment.objects.get(child=obj, parent_id=req.data.get('territory',type=DeviceTypeAssignmentEnum.DUMP_ASSIGNMENT))
            except:
                #uh oh, dint get the assignment better make one now
                try:
                    Assignment.objects.filter(child=obj).delete()
                    Assignment.objects.create(
                        name=obj.name + ' is assigned to ' + Entity.objects.get(id=req.data.get('territory')).name,
                        comments="",
                        child_id=obj.id,
                        parent_id=req.data.get('territory'),
                        customer_id=req.data.get('customer'),
                        module_id=req.data.get('module'),
                        type_id=DeviceTypeAssignmentEnum.DUMP_ASSIGNMENT,
                        status_id=OptionsEnum.ACTIVE,
                        modified_by_id=req.data.get('modified_by')
                    )
                except:
                    traceback.print_exc()
                    pass
        else:
            try:
                ass = Assignment.objects.get(child=obj, type=DeviceTypeAssignmentEnum.DUMP_ASSIGNMENT)
                return {'value': ass.parent.id, 'label': ass.parent.name}
            except:
                return None

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
            'dump_territory'

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
                Entity.objects.get(name=data['name'], type_id=data['type'], status_id=OptionsEnum.ACTIVE)
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
    photo_method = SerializerMethodField('img_url', required=False)
    module_name = SerializerMethodField('module_method', required=False, allow_null=True)
    entity_sub_type_name = SerializerMethodField('entity_sub_type_method', required=False, allow_null=True)
    skip_size_name = SerializerMethodField('skip_size_name_method', required=False, allow_null=True)
    modified_by_name = SerializerMethodField('modified_name', allow_null=True, required=False, read_only=True)
    modified_by_email = SerializerMethodField('modified_email', allow_null=True, required=False, read_only=True)
    customer_name = SerializerMethodField('customer_method', allow_null=True, required=False, read_only=True)
    client_name = SerializerMethodField('client_method', allow_null=True, required=False, read_only=True)
    # name = SerializerMethodField('name_method', allow_null=True, required=False, read_only=True)
    party_code = SerializerMethodField('party_code_name', allow_null=True, required=False, read_only=True)
    leased_owned_name = SerializerMethodField('leased_owned_method', allow_null=True, required=False, read_only=True)
    files_name = SerializerMethodField('files_method', required=False, allow_null=True)

    def files_method(self, obj):
        if self.context['request'].method == 'POST' or self.context['request'].method == 'PATCH':
            req = self.context['request']
            files = req.FILES.getlist('files')
            # Delete all relationships cause they will be recreated
            EntityDocument.objects.filter(entity=obj).delete()
            for f in files:
                b = EntityDocument()
                filename = 'documents/' + f.name
                import os
                from django.conf import settings
                file_to_check = os.path.join(settings.BASE_DIR, 'media/documents/' + f.name).replace(' ', '_')
                try:
                    # if it exists in the system
                    if b.file.storage.exists(file_to_check):
                        # File exists/ and we want the relationship (Make it!)
                        EntityDocument.objects.create(entity=obj, file=filename.replace(' ', '_'))
                    else:
                        # File does not exist. Lets put it in the system and on our server.
                        EntityDocument.objects.create(entity=obj, file=f)
                except:
                    traceback.print_exc()
                    return None
        elif self.context['request'].method == 'GET':
            try:
                result = []
                files = EntityDocument.objects.filter(entity=obj)
                for f in files:
                    result.append(self.context['request'].build_absolute_uri(f.file.url))
                return result
            except Exception as e:
                traceback.print_exc()
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

    # def name_method(self, obj):
    #     req = self.context['request']
    #     if self.context['request'].method == 'POST' or self.context['request'].method == 'PATCH':
    #         obj.name = obj.client.name + ' ' + obj.type.name + ' '+ str(obj.job_start_datetime.date()) + '|'+ str(obj.job_end_datetime.date())
    #         obj.save()
    #     else:
    #         return obj.name

    def skip_size_name_method(self, obj):
        if obj.skip_size:
            type = obj.skip_size.label
            return type
        else:
            return None

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

    def img_url(self, obj):
        if self.context:
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
            'skip_size',
            'skip_size_name',
            'client',
            'client_name',
            'skip_rate',
            'party_code',

            #Contract Invoice Type
            'leased_owned',
            'leased_owned_name',

            #Renewed this month
            'speed',

            'photo',
            'photo_method',
            'files_name',

            'volume',
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

       'destination_latlong',
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


class ZoneSerializer(ModelSerializer):
    status_label = SerializerMethodField('status_method', required=False, allow_null=True)
    module_name = SerializerMethodField('module_method', required=False, allow_null=True)
    modified_by_name = SerializerMethodField('modified_name', allow_null=True, required=False, read_only=True)
    modified_by_email = SerializerMethodField('modified_email', allow_null=True, required=False, read_only=True)
    employees = SerializerMethodField('zone_employees', allow_null=True, required=False, read_only=True)
    assigned_supervisor = SerializerMethodField('zone_supervisor_method', allow_null=True, required=False, read_only=True)
    assigned_supervisor_id = SerializerMethodField('zone_supervisor_id_method', allow_null=True, required=False, read_only=True)
    zone_productivity = SerializerMethodField('zone_productivity_method', allow_null=True, required=False, read_only=True)
    violations_last_day = SerializerMethodField('zone_violations_method', allow_null=True, required=False, read_only=True)

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

    def zone_employees(self, obj):
        if obj:
            employees = Assignment.objects.filter(parent=obj, type= DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT,
                                                  status_id=OptionsEnum.ACTIVE).count()
            return employees
        else:
            return None


    def zone_supervisor_method(self, obj):
        if obj:
            try:
                supervisor = Assignment.objects.get(parent=obj, type_id=DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT,status_id=OptionsEnum.ACTIVE,
                                                    child__entity_sub_type_id = FFPOptionsEnum.ZONE_SUPERVISOR).child.name
            except:
                supervisor = None
            return supervisor
        else:
            return None


    def zone_supervisor_id_method(self, obj):
        if obj:
            try:
                supervisor = Assignment.objects.get(parent=obj, type_id=DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT,status_id=OptionsEnum.ACTIVE,
                                                    child__entity_sub_type_id = FFPOptionsEnum.ZONE_SUPERVISOR).child.id
            except:
                supervisor = None
            return supervisor
        else:
            return None

    def zone_productivity_method(self, obj):
        from ffp.models import FFPDataDailyAverage
        try:
            yesterday_avg = FFPDataDailyAverage.objects.get(timestamp__date=(timezone.now()- timedelta(days=1)).date(), zone=obj, employee=None).zone_productivity_avg
        except:
            yesterday_avg = 0
        return yesterday_avg

    def zone_violations_method(self, obj):
        if obj:
            violations_last_day = EmployeeViolations.objects.filter(zone=obj, violations_type_id__in=[FFPOptionsEnum.OUT_OF_ZONE, FFPOptionsEnum.OUT_OF_SITE],
                                                                    violations_dtm__date=(timezone.now() - timedelta(days=1)).date()).order_by('violations_type_id')
            return violations_last_day.count()
        else:
            return 0

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
            'territory',
            'description',
            'employees',
            'assigned_supervisor',
            'assigned_supervisor_id',
            'zone_productivity',
            #Man Hours Allocated
            'squad_number',
            'violations_last_day',
        ]


class EmployeeSerializer(ModelSerializer):
    photo_method = SerializerMethodField('img_url', required=False)
    gender_label = SerializerMethodField('gender_method', required=False, allow_null=True)
    module_name = SerializerMethodField('module_method', required=False, allow_null=True)
    marital_status_label = SerializerMethodField('marital_method', required=False, allow_null=True)
    status_label = SerializerMethodField('status_method', required=False, allow_null=True)
    age = SerializerMethodField('age_cal', required=False, allow_null=True)
    modified_by_name = SerializerMethodField('modified_name', allow_null=True, required=False, read_only=True)
    modified_by_email = SerializerMethodField('modified_email', allow_null=True, required=False, read_only=True)
    entity_sub_type_name = SerializerMethodField('entity_sub_type_name_method', required=False, allow_null=True)
    employee_email = SerializerMethodField('email_method', allow_null=True, required=False, read_only=True)
    assigned = SerializerMethodField('assigned_region_name_method', allow_null=True, required=False, read_only=True)
    assigned_id = SerializerMethodField('assigned_region_id_method', allow_null=True, required=False, read_only=True)
    employee_role = SerializerMethodField('employee_role_method', allow_null=True, required=False, read_only=True)
    employee_present_absent = SerializerMethodField('employee_present_absent_method_field', allow_null=True, required=False, read_only=True)
    violations_data = SerializerMethodField('employee_violations_method', allow_null=True, required=False, read_only=True)
    duration_now_in_site = SerializerMethodField('calculate_emp_durations_site', allow_null=True, required=False, read_only=True)
    duration_now_in_zone = SerializerMethodField('calculate_emp_durations_zone', allow_null=True, required=False, read_only=True)
    duration_now_in_site_active = SerializerMethodField('calculate_emp_durations_site_active', allow_null=True, required=False, read_only=True)
    duration_now_in_zone_active = SerializerMethodField('calculate_emp_durations_zone_active', allow_null=True, required=False, read_only=True)
    duration_in_site_last_day = SerializerMethodField('calculate_emp_durations_site_last_day', allow_null=True, required=False, read_only=True)
    duration_in_zone_last_day = SerializerMethodField('calculate_emp_durations_zone_last_day', allow_null=True, required=False, read_only=True)
    duration_in_site_last_day_active = SerializerMethodField('calculate_emp_durations_site_last_day_active', allow_null=True, required=False, read_only=True)
    duration_in_zone_last_day_active = SerializerMethodField('calculate_emp_durations_zone_last_day_active', allow_null=True, required=False, read_only=True)
    productivity_today = SerializerMethodField('calculate_productivity_today', allow_null=True, required=False, read_only=True)
    violations_last_day = SerializerMethodField('employee_last_day_violations', allow_null=True, required=False, read_only=True)
    violations_this_day = SerializerMethodField('employee_this_day_violations', allow_null=True, required=False, read_only=True)
    assigned_zone_territory = SerializerMethodField('employee_zone_shape', allow_null=True, required=False, read_only=True)
    productivity_this_day = SerializerMethodField('employee_productivity_this_day', allow_null=True, required=False, read_only=True)
    productivity_last_day = SerializerMethodField('employee_productivity_last_day', allow_null=True, required=False, read_only=True)
    employee_location = SerializerMethodField('location_of_employee', allow_null=True, required=False, read_only=True)
    in_zone = SerializerMethodField('employee_in_zone', allow_null=True, required=False, read_only=True)
    in_site = SerializerMethodField('employee_in_site', allow_null=True, required=False, read_only=True)
    device_name_method = SerializerMethodField('customer_device_name_method', allow_null=True, required=False, read_only=True)
    last_updated = SerializerMethodField('last_updated_method', allow_null=True, required=False, read_only=True)
    monthly_working_hours = SerializerMethodField('employee_monthly_working_hours', allow_null=True, required=False, read_only=True)
    employee_status = SerializerMethodField('employee_status_method', allow_null=True, required=False, read_only=True)
    emp_clock_in_time = SerializerMethodField('emp_clock_in_time_method', allow_null=True, required=False, read_only=True)
    emp_clock_out_time = SerializerMethodField('emp_clock_out_time_method', allow_null=True, required=False, read_only=True)


    def email_method(self, obj):
        if obj:
            try:
                email = User.objects.get(associated_entity_id=obj.id).email
            except:
                email = None
            return email

    def customer_device_name_method(self, obj):
        if obj and obj.device_name:
            return obj.device_name.device_id
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

    def last_updated_method(self, obj):
        from ffp.reporting_utils import get_ffp_last_data
        if obj:
            last_updated_dtm = get_ffp_last_data(c_id=obj.customer_id, e_id=obj.id)
            if last_updated_dtm:
                return last_updated_dtm.timestamp
            else:
                return None
        else:
            return None

    def marital_method(self, obj):
        if obj.marital_status:
            m_status = obj.marital_status.label
            return m_status
        else:
            return None

    def img_url(self, obj):
        if self.context:
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
        else:
            return None

    def entity_sub_type_name_method(self, obj):
        if obj.entity_sub_type:
            type = obj.entity_sub_type.label
            return type
        else:
            return None

    def assigned_region_name_method(self, obj):
        if obj:
            if obj.entity_sub_type.id == FFPOptionsEnum.ZONE_SUPERVISOR:
                region= check_employee_assigned_region(obj, FFPOptionsEnum.ZONE_SUPERVISOR,
                                                       DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT)
                if region:
                    return region.name
                else:
                    return None

            if obj.entity_sub_type.id == FFPOptionsEnum.LABOUR:
                region= check_employee_assigned_region(obj, FFPOptionsEnum.LABOUR, DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT)
                if region:
                    return region.name
                else:
                    return None

            if obj.entity_sub_type.id == FFPOptionsEnum.SITE_SUPERVISOR:
                region= check_employee_assigned_region(obj, FFPOptionsEnum.SITE_SUPERVISOR,
                                                       DeviceTypeAssignmentEnum.SITE_EMPLOYEE_ASSIGNMENT)
                if region:
                    return region.name
                else:
                    return None

            if obj.entity_sub_type.id == FFPOptionsEnum.TEAM_SUPERVISOR:
                region= check_employee_assigned_region(obj, FFPOptionsEnum.TEAM_SUPERVISOR, DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT)
                if region:
                    return region.name
                else:
                    return None

        else:
            return None

    def assigned_region_id_method(self, obj):
        if obj:
            if obj.entity_sub_type.id == FFPOptionsEnum.ZONE_SUPERVISOR:
                region = check_employee_assigned_region(obj, FFPOptionsEnum.ZONE_SUPERVISOR,
                                                        DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT)
                if region:
                    return region.id
                else:
                    return None

            if obj.entity_sub_type.id == FFPOptionsEnum.LABOUR:
                region= check_employee_assigned_region(obj, FFPOptionsEnum.LABOUR,
                                                       DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT)
                if region:
                    return region.id
                else:
                    return None

            if obj.entity_sub_type.id == FFPOptionsEnum.TEAM_SUPERVISOR:
                region= check_employee_assigned_region(obj, FFPOptionsEnum.TEAM_SUPERVISOR,
                                                       DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT)
                if region:
                    return region.id
                else:
                    return None

            if obj.entity_sub_type.id == FFPOptionsEnum.SITE_SUPERVISOR:
                region = check_employee_assigned_region(obj, FFPOptionsEnum.SITE_SUPERVISOR,
                                                        DeviceTypeAssignmentEnum.SITE_EMPLOYEE_ASSIGNMENT)
                if region:
                    return region.id
                else:
                    return None
        else:
            return None

    def employee_role_method(self, obj):
        if obj:
            role = obj.entity_sub_type.label
        else:
            role = None
        return role

    def employee_present_absent_method_field(self, obj):
        if obj:
            try:
                present_employee = AttendanceRecord.objects.get(employee=obj, present=True,
                                                               site_checkin_dtm__date = timezone.now().date())
                date = present_employee.site_checkin_dtm
            except:
                date = None
            return date
        else:
            return None

    def employee_violations_method(self, obj):
        if obj:
            violations = EmployeeViolations.objects.filter(employee=obj, violations_type_id__in=[FFPOptionsEnum.OUT_OF_ZONE,FFPOptionsEnum.OUT_OF_SITE],
                                                           violations_dtm__date=timezone.now() - timedelta(days=LAST_WEEK)).order_by('violations_type_id')
            violations_of_emp = [{k: len(list(g))} for k, g in itertools.groupby(violations, lambda viol: viol.violations_type.label)]
            return violations_of_emp
        else:
            return None

    def employee_last_day_violations(self, obj):
        if obj:
            last_day = timezone.now() - timedelta(days=1)
            violations = EmployeeViolations.objects.filter(employee=obj, violations_type_id__in=[FFPOptionsEnum.OUT_OF_ZONE,
                                                                                   FFPOptionsEnum.OUT_OF_SITE], violations_dtm__date=last_day).order_by('violations_type_id')
            return violations.count()
        else:
            return None

    def employee_this_day_violations(self, obj):
        if obj:
            violations = EmployeeViolations.objects.filter(employee=obj, violations_type_id__in=[FFPOptionsEnum.OUT_OF_ZONE,
                                                                                   FFPOptionsEnum.OUT_OF_SITE], violations_dtm__date=timezone.now().date()).order_by('violations_type_id')
            return violations.count()
        else:
            return None

    def calculate_emp_durations_site(self, obj):
        from ffp.cron_utils import get_durations_site
        violations_now = EmployeeViolations.objects.filter(violations_dtm__date=timezone.now().today().date(), employee=obj)
        duration_in_site = get_durations_site(emp_id=obj.id, date=timezone.now().date(), viol_q_set_site=violations_now)
        return duration_in_site

    def calculate_emp_durations_zone(self, obj):
        from ffp.cron_utils import get_durations_zone
        violations_now = EmployeeViolations.objects.filter(violations_dtm__date=timezone.now().today().date(), employee=obj)
        duration_in_zone = get_durations_zone(emp_id=obj.id, date=timezone.now().date(), viol_q_set_zone=violations_now)
        return duration_in_zone

    def calculate_emp_durations_site_active(self, obj):
        from ffp.cron_utils import get_active_hours_site
        violations_now = EmployeeViolations.objects.filter(violations_dtm__date=timezone.now().today().date(), employee=obj)
        duration_in_site = get_active_hours_site(emp_id=obj.id, date=timezone.now().date(), viol_q_set_site=violations_now)
        return duration_in_site

    def calculate_productivity_today(self, obj):
        from ffp.cron_utils import get_productivity
        duration_in_site = self.calculate_emp_durations_site_active(obj)
        try:
            zone = Assignment.objects.get(child=obj, status_id=OptionsEnum.ACTIVE, type_id=DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT).parent
        except:
            zone = None
        try:
            site = Assignment.objects.get(child=zone, status_id=OptionsEnum.ACTIVE, type_id=DeviceTypeAssignmentEnum.SITE_ZONE_ASSIGNMENT).parent
        except:
            site = None

        productivity = get_productivity(c_id=obj.customer_id, dur_active=duration_in_site, site=site, zone=None)
        return productivity

    def calculate_emp_durations_zone_active(self, obj):
        from ffp.cron_utils import get_active_hours_zone
        violations_now = EmployeeViolations.objects.filter(violations_dtm__date=timezone.now().today().date(), employee=obj)
        duration_in_zone = get_active_hours_zone(emp_id=obj.id, date=timezone.now().date(), viol_q_set_zone=violations_now)
        return duration_in_zone

    def calculate_emp_durations_zone_last_day(self, obj):
        from ffp.cron_utils import get_durations_zone
        last_day = timezone.now() - timedelta(days=1)
        try:
            duration_in_zone = AttendanceRecord.objects.get(site_checkin_dtm__date=last_day.date(), present=True)
            duration_in_zone = duration_in_zone.duration_in_site
        except:
            violations_now = EmployeeViolations.objects.filter(violations_dtm__date=last_day.date(), employee=obj)
            duration_in_zone = get_durations_zone(emp_id=obj.id, date=last_day.date(), viol_q_set_zone=violations_now)

        return duration_in_zone

    def calculate_emp_durations_site_last_day(self, obj):
        from ffp.cron_utils import get_durations_site
        last_day = timezone.now() - timedelta(days=1)
        try:
            duration_in_site = AttendanceRecord.objects.get(site_checkin_dtm__date=last_day.date(), present=True)
            duration_in_site = duration_in_site.duration_in_site
        except:
            violations_now = EmployeeViolations.objects.filter(violations_dtm__date=last_day.date(), employee=obj)
            duration_in_site = get_durations_site(emp_id=obj.id, date=last_day.date(), viol_q_set_site=violations_now)

        return duration_in_site

    def calculate_emp_durations_site_last_day_active(self, obj):
        from ffp.cron_utils import get_active_hours_site
        last_day = timezone.now() - timedelta(days=1)
        try:
            duration_in_site = AttendanceRecord.objects.get(site_checkin_dtm__date=last_day.date(), present=True)
            duration_in_site = duration_in_site.duration_in_site_active if duration_in_site.duration_in_site_active else 0
        except:
            violations_now = EmployeeViolations.objects.filter(violations_dtm__date=last_day.date(), employee=obj)
            duration_in_site = get_active_hours_site(emp_id=obj.id, date=last_day.date(), viol_q_set_site=violations_now)

        return duration_in_site

    def calculate_emp_durations_zone_last_day_active(self, obj):
        from ffp.cron_utils import get_active_hours_zone
        last_day = timezone.now() - timedelta(days=1)
        try:
            duration_in_zone = AttendanceRecord.objects.get(site_checkin_dtm__date=last_day.date(), present=True)
            duration_in_zone = duration_in_zone.duration_in_zone_active if duration_in_zone.duration_in_zone_active else 0
        except:
            violations_now = EmployeeViolations.objects.filter(violations_dtm__date=last_day.date(), employee=obj)
            duration_in_zone = get_active_hours_zone(emp_id=obj.id, date=last_day.date(), viol_q_set_zone=violations_now)

        return duration_in_zone

    def employee_zone_shape(self, obj):
        try:
            zone = Assignment.objects.get(child=obj, status_id=OptionsEnum.ACTIVE, type_id=DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT)
        except:
            zone = None
        if zone:
            return zone.parent.territory
        else:
            return None

    def employee_productivity_last_day(self, obj):
        # from ffp.reporting_utils import calculate_entity_productivty
        if obj:
            try:
                attendance_last_day = AttendanceRecord.objects.get(employee=obj, attendance_dtm__date=(timezone.now() - timedelta(days=1)).date())
            except:
                attendance_last_day = None
            # productivity = calculate_entity_productivty(e_id=obj.id, day=timezone.now() - timedelta(days=1))
            if attendance_last_day:
                return attendance_last_day.productive_hours
            else:
                return 0
        else:
            return 0

    def employee_productivity_this_day(self, obj):
        from ffp.reporting_utils import calculate_entity_productivty
        if obj:
            productivity = calculate_entity_productivty(e_id=obj.id, day=timezone.now())
            return productivity
        else:
            return None

    def location_of_employee(self, obj):
        if obj:
            location = HypernetPostData.objects.filter(device=obj, timestamp__date=timezone.now().date()).order_by('-timestamp')
            if location.__len__()>0:
                location = location[0]
                return location.latitude, location.longitude
        else:
            return None, None

    def employee_in_zone(self, obj):
        if obj:
            try:
                in_zone = AttendanceRecord.objects.get(employee=obj, zone_checkin_dtm__date = timezone.now().date(), zone_status=True)
                status = in_zone.zone_status
            except:
                status = False
            return status
        else:
            return False

    def employee_in_site(self, obj):
        if obj:
            try:
                in_site = AttendanceRecord.objects.get(employee=obj, site_checkin_dtm__date = timezone.now().date(), site_status=True)
                status = in_site.site_status
            except:
                status = False
            return status
        else:
            return False

    def employee_monthly_working_hours(self, obj):
        if obj:
            monthly_q_set = AttendanceRecord.objects.filter(employee=obj, attendance_dtm__gte=(timezone.now() - timedelta(days=30)))
            working_hrs = monthly_q_set.values('employee').annotate(monthly_work_avg=Avg('duration_in_site')).values('monthly_work_avg')
            if working_hrs.__len__() > 0:
                return working_hrs[0]['monthly_work_avg']
            else:
                return 0

    def employee_status_method(self, obj):
        if obj:
            active_stauts = HypernetPostData.objects.filter(device=obj, timestamp__gte=(timezone.now() - timedelta(minutes=3))).order_by('-timestamp').first()
            if active_stauts:
                return active_stauts.trip
            else:
                return False

    def emp_clock_in_time_method(self, obj):
        if obj:
            check_in_time = None
            try:
                attn = AttendanceRecord.objects.get(employee=obj, site_checkin_dtm__date=timezone.now().date(),
                                                   present=True)
            except:
                attn = None
            if attn:
                if attn.site_checkin_dtm:
                    check_in_time= attn.site_checkin_dtm
                else:
                    check_in_time=None

            return check_in_time

    def emp_clock_out_time_method(self, obj):
        if obj:
            check_out_time = None
            try:
                attn = AttendanceRecord.objects.get(employee=obj, site_checkin_dtm__date=timezone.now().date(),
                                                present=True)
            except:
                attn = None
            if attn:
                if attn.site_checkout_dtm:
                    check_out_time = attn.site_checkout_dtm
                else:
                    check_out_time = None

            return check_out_time

    class Meta:
        model = Entity
        fields = [
            # Common fields to be included in every Entity serializer
            'id',
            'name',
            'type',
            'customer',
            'assignments',
            'device_name',
            'device_name_method',

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
            'entity_sub_type',
            'entity_sub_type_name',

            'employee_email',

            'assigned',
            'assigned_id',

            'employee_role',
            'employee_present_absent',
            'violations_data',
            'duration_now_in_site',
            'duration_now_in_zone',
            'violations_last_day',
            'violations_this_day',
            'assigned_zone_territory',
            'productivity_this_day',
            'productivity_last_day',
            'employee_location',
            'in_site',
            'in_zone',
            'duration_in_site_last_day',
            'duration_in_zone_last_day',
            'duration_now_in_site_active',
            'duration_now_in_zone_active',
            'duration_in_site_last_day_active',
            'duration_in_zone_last_day_active',
            'last_updated',
            'productivity_today',
            'monthly_working_hours',
            'employee_status',
            'emp_clock_in_time',
            'emp_clock_out_time'
        ]


class SiteSerializer(ModelSerializer):
    status_label = SerializerMethodField('status_method', required=False, allow_null=True)
    module_name = SerializerMethodField('module_method', required=False, allow_null=True)
    modified_by_name = SerializerMethodField('modified_name', allow_null=True, required=False, read_only=True)
    modified_by_email = SerializerMethodField('modified_email', allow_null=True, required=False, read_only=True)
    site_productivity = SerializerMethodField('site_productivity_method', allow_null=True, required=False, read_only=True)

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

    def site_productivity_method(self, obj):
        from ffp.models import FFPDataDailyAverage
        try:
            yesterday_data = FFPDataDailyAverage.objects.get(timestamp__date = (timezone.now()-timedelta(days=1)).date(), site=obj, employee = None, zone=None).site_productivity_avg
        except Exception as e:
            print(e)
            yesterday_data = 0

        return yesterday_data


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
            'territory',
            'description',
            'site_productivity',
            'squad_number',
        ]


def check_employee_assigned_region(obj, sub_type, type_id):
    try:
        assigned = Assignment.objects.get(child=obj, child__entity_sub_type = sub_type, type_id=type_id,
                                          status_id=OptionsEnum.ACTIVE).parent
    except:
        assigned = None
    return assigned


class VesselSerializer(ModelSerializer):
    #photo = SerializerMethodField('img_url', required=False)
    # customer_devices = SerializerMethodField()
    module_name = SerializerMethodField('module_method', required=False, allow_null=True)
    status_label = SerializerMethodField('status_method', required=False, allow_null=True)
    modified_by_name = SerializerMethodField('modified_name', allow_null=True, required=False, read_only=True)
    modified_by_email = SerializerMethodField('modified_email', allow_null=True, required=False, read_only=True)
    entity_sub_type_name = SerializerMethodField('entity_sub_type_name_method', required=False, allow_null=True)
    threshold_value = SerializerMethodField('threshold_method', required=False, allow_null=True)
    device = SerializerMethodField('customer_device_name', required=False, allow_null=True)

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

    def customer_device_name(self, obj):
        if obj.device_name:
            name = obj.device_name.device_id
            return name
        else:
            return None
    '''
    def img_url(self, obj):
        print(self.context['request'].method)
        if self.context['request'].method == 'POST' or self.context['request'].method == 'PATCH':
            req = self.context['request']
            obj.photo = req.data.get('photo')
            obj.save()
        elif self.context['request'].method == 'GET':
            try:
                photo_url = obj.photo.url
                return self.context['request'].build_absolute_uri(photo_url)
            except Exception as e:
                traceback.print_exc()
                return None
    '''

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
                print('device name: ' + device.device_id)

                obj.device_name.id = req.data.get('device_name')
                obj.save()
                print('name of latest device: ' + obj.device_name.device_id)
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
            'device',
            # 'customer_devices',

            # Speed Check and Threshold Value
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
            #'photo',
            'entity_sub_type',
            'entity_sub_type_name',
            'threshold_value',
        ]


class EmployeeListingSerializer(ModelSerializer):
    photo_method = SerializerMethodField('img_url', required=False)
    gender_label = SerializerMethodField('gender_method', required=False, allow_null=True)
    module_name = SerializerMethodField('module_method', required=False, allow_null=True)
    marital_status_label = SerializerMethodField('marital_method', required=False, allow_null=True)
    status_label = SerializerMethodField('status_method', required=False, allow_null=True)
    age = SerializerMethodField('age_cal', required=False, allow_null=True)
    modified_by_name = SerializerMethodField('modified_name', allow_null=True, required=False, read_only=True)
    modified_by_email = SerializerMethodField('modified_email', allow_null=True, required=False, read_only=True)
    entity_sub_type_name = SerializerMethodField('entity_sub_type_name_method', required=False, allow_null=True)
    employee_email = SerializerMethodField('email_method', allow_null=True, required=False, read_only=True)
    assigned = SerializerMethodField('assigned_region_name_method', allow_null=True, required=False, read_only=True)
    assigned_id = SerializerMethodField('assigned_region_id_method', allow_null=True, required=False, read_only=True)
    employee_role = SerializerMethodField('employee_role_method', allow_null=True, required=False, read_only=True)
    device_name_method = SerializerMethodField('customer_device_name_method', allow_null=True, required=False,read_only=True)
    #FIXME
    employee_present_absent = SerializerMethodField('employee_present_absent_method_field', allow_null=True, required=False, read_only=True)
    in_zone = SerializerMethodField('employee_in_zone', allow_null=True, required=False, read_only=True)
    in_site = SerializerMethodField('employee_in_site', allow_null=True, required=False, read_only=True)
    violations_data = SerializerMethodField('employee_violations_method', allow_null=True, required=False, read_only=True)
    employee_status = SerializerMethodField('employee_status_method', allow_null=True, required=False, read_only=True)
    employee_location = SerializerMethodField('location_of_employee', allow_null=True, required=False, read_only=True)
    productivity_last_day = SerializerMethodField('employee_productivity_last_day', allow_null=True, required=False, read_only=True)

    def email_method(self, obj):
        if obj:
            try:
                email = User.objects.get(associated_entity_id=obj.id).email
            except:
                email = None
            return email

    def customer_device_name_method(self, obj):
        if obj and obj.device_name:
            return obj.device_name.device_id
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
        if self.context:
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
        else:
            return None

    def entity_sub_type_name_method(self, obj):
        if obj.entity_sub_type:
            type = obj.entity_sub_type.label
            return type
        else:
            return None

    def assigned_region_name_method(self, obj):
        if obj:
            if obj.entity_sub_type.id == FFPOptionsEnum.ZONE_SUPERVISOR:
                region= check_employee_assigned_region(obj, FFPOptionsEnum.ZONE_SUPERVISOR,
                                                       DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT)
                if region:
                    return region.name
                else:
                    return None

            if obj.entity_sub_type.id == FFPOptionsEnum.LABOUR:
                region= check_employee_assigned_region(obj, FFPOptionsEnum.LABOUR, DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT)
                if region:
                    return region.name
                else:
                    return None

            if obj.entity_sub_type.id == FFPOptionsEnum.SITE_SUPERVISOR:
                region= check_employee_assigned_region(obj, FFPOptionsEnum.SITE_SUPERVISOR,
                                                       DeviceTypeAssignmentEnum.SITE_EMPLOYEE_ASSIGNMENT)
                if region:
                    return region.name
                else:
                    return None

            if obj.entity_sub_type.id == FFPOptionsEnum.TEAM_SUPERVISOR:
                region= check_employee_assigned_region(obj, FFPOptionsEnum.TEAM_SUPERVISOR, DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT)
                if region:
                    return region.name
                else:
                    return None

        else:
            return None

    def assigned_region_id_method(self, obj):
        if obj:
            if obj.entity_sub_type.id == FFPOptionsEnum.ZONE_SUPERVISOR:
                region = check_employee_assigned_region(obj, FFPOptionsEnum.ZONE_SUPERVISOR,
                                                        DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT)
                if region:
                    return region.id
                else:
                    return None

            if obj.entity_sub_type.id == FFPOptionsEnum.LABOUR:
                region= check_employee_assigned_region(obj, FFPOptionsEnum.LABOUR,
                                                       DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT)
                if region:
                    return region.id
                else:
                    return None

            if obj.entity_sub_type.id == FFPOptionsEnum.TEAM_SUPERVISOR:
                region= check_employee_assigned_region(obj, FFPOptionsEnum.TEAM_SUPERVISOR,
                                                       DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT)
                if region:
                    return region.id
                else:
                    return None

            if obj.entity_sub_type.id == FFPOptionsEnum.SITE_SUPERVISOR:
                region = check_employee_assigned_region(obj, FFPOptionsEnum.SITE_SUPERVISOR,
                                                        DeviceTypeAssignmentEnum.SITE_EMPLOYEE_ASSIGNMENT)
                if region:
                    return region.id
                else:
                    return None
        else:
            return None

    def employee_role_method(self, obj):
        if obj:
            role = obj.entity_sub_type.label
        else:
            role = None
        return role

    def employee_present_absent_method_field(self, obj):
        if obj:
            try:
                present_employee = AttendanceRecord.objects.get(employee=obj, present=True,
                                                               site_checkin_dtm__date = timezone.now().date())
                date = present_employee.site_checkin_dtm
            except:
                date = None
            return date
        else:
            return None

    def employee_violations_method(self, obj):
        if obj:

            violations = EmployeeViolations.objects.filter(employee=obj, violations_type_id__in=[FFPOptionsEnum.OUT_OF_ZONE,
                                                                                   FFPOptionsEnum.OUT_OF_SITE], active_status=None, violations_dtm__date=(timezone.now() - timedelta(days=1)).date()).order_by('violations_type_id')
            violations_of_emp = [{k: len(list(g))} for k, g in itertools.groupby(violations, lambda viol: viol.violations_type.label)]
            return violations_of_emp
        else:
            return None

    def employee_in_zone(self, obj):
        if obj:
            try:
                in_zone = AttendanceRecord.objects.get(employee=obj, zone_checkin_dtm__date = timezone.now().date(), zone_status=True)
                status = in_zone.zone_status
            except:
                status = False
            return status
        else:
            return False

    def employee_in_site(self, obj):
        if obj:
            try:
                in_site = AttendanceRecord.objects.get(employee=obj, site_checkin_dtm__date = timezone.now().date(), site_status=True)
                status = in_site.site_status
            except:
                status = False
            return status
        else:
            return False

    def employee_status_method(self, obj):
        if obj:
            active_stauts = HypernetPostData.objects.filter(device=obj, timestamp__gte=(timezone.now() - timedelta(minutes=3))).order_by('-timestamp').first()
            if active_stauts:
                return active_stauts.trip
            else:
                return False

    def location_of_employee(self, obj):
        if obj:
            location = HypernetPostData.objects.filter(device=obj, timestamp__date=timezone.now().date()).order_by('-timestamp')
            if location.__len__()>0:
                location = location[0]
                return location.latitude, location.longitude
        else:
            return None, None

    def employee_productivity_last_day(self, obj):
        # from ffp.reporting_utils import calculate_entity_productivty
        if obj:
            try:
                attendance_last_day = AttendanceRecord.objects.get(employee=obj, attendance_dtm__date=(timezone.now() - timedelta(days=1)).date())
            except:
                attendance_last_day = None
            # productivity = calculate_entity_productivty(e_id=obj.id, day=timezone.now() - timedelta(days=1))
            if attendance_last_day:
                return attendance_last_day.productive_hours
            else:
                return 0
        else:
            return 0

    class Meta:
        model = Entity
        fields = [
            # Common fields to be included in every Entity serializer
            'id',
            'name',
            'type',
            'customer',
            'assignments',
            'device_name',
            'device_name_method',
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
            # Employee specific fields
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
            'entity_sub_type',
            'entity_sub_type_name',
            'employee_email',
            'assigned',
            'assigned_id',
            'employee_role',
            'employee_present_absent',
            'in_zone',
            'in_site',
            'violations_data',
            'employee_status',
            'employee_location',
            'productivity_last_day',
        ]


class HomeAppliancesSerializer(ModelSerializer):
    module_name = SerializerMethodField('module_method', required=False, allow_null=True)
    status_label = SerializerMethodField('status_method', required=False, allow_null=True)
    modified_by_name = SerializerMethodField('modified_name', allow_null=True, required=False, read_only=True)
    modified_by_email = SerializerMethodField('modified_email', allow_null=True, required=False, read_only=True)
    entity_sub_type_name = SerializerMethodField('entity_sub_type_name_method', required=False, allow_null=True)
    device_name_method = SerializerMethodField('customer_device_name_method', allow_null=True, required=False,read_only=True)
    energy_consumed_yesterday = SerializerMethodField('energy_consumed_last_24_hrs', allow_null=True, required=False,read_only=True)
    active_hrs_yesterday = SerializerMethodField('active_hrs_last_24_hrs', allow_null=True, required=False,read_only=True)
    errors_yesterday = SerializerMethodField('errors_last_24_hrs', allow_null=True, required=False,read_only=True)
    leased_owned_name = SerializerMethodField('leased_owned_name_method', required=False, allow_null=True)
    standby = SerializerMethodField('validate_standby', required=False, allow_null=True)
    ctt = SerializerMethodField('validate_ctt', required=False, allow_null=True)
    cdt=SerializerMethodField('validate_cdt', required=False, allow_null=True)
    clm=SerializerMethodField('validate_clm', required=False, allow_null=True)
    cht=SerializerMethodField('validate_cht', required=False, allow_null=True)
    types=SerializerMethodField('validate_types', required=False, allow_null=True)
    
    
    def validate_types(self,obj):
        if obj:
            if 'wh' in str(obj.device_name.device_id):
                return 'Vertical Tank'
            else:
                return None
                
    def validate_cht(self, obj):
        if obj:
            print(obj.id)
            try:
                data = HypernetPreData.objects.filter(device_id=obj.id).latest('timestamp')
                print(data)
                return data.active_score

            except Exception as e:
                print(e)
                try:
                    data=HypernetPostData.objects.filter(device_id=obj.id).latest('timestamp')
                    return data.active_score
                except Exception as e:
                    return None
    def validate_clm(self, obj):
        if obj:
            print(obj.id)
            try:
                data = HypernetPreData.objects.filter(device_id=obj.id).latest('timestamp')
                print(data)
                return data.clm

            except Exception as e:
                print(e)
                try:
                    data=HypernetPostData.objects.filter(device_id=obj.id).latest('timestamp')
                    return data.clm
                except Exception as e:
                    return None
    def validate_cdt(self, obj):
        if obj:
            print(obj.id)
            try:
                data = HypernetPreData.objects.filter(device_id=obj.id).latest('timestamp')
                print(data)
                return data.cdt

            except Exception as e:
                print(e)
                try:
                    data=HypernetPostData.objects.filter(device_id=obj.id).latest('timestamp')
                    return data.cdt
                except Exception as e:
                    return None
                
    def validate_ctt(self, obj):
        if obj:
            print(obj.id)
            try:
                data = HypernetPreData.objects.filter(device_id=obj.id).latest('timestamp')
                print(data)
                return data.ctt

            except Exception as e:
                print(e)
                try:
                    data=HypernetPostData.objects.filter(device_id=obj.id).latest('timestamp')
                    return data.ctt
                except Exception as e:
                    return None
    def validate_standby(self, obj):
        standby=obj.standby_mode
        print('check here', standby)
        standby_value = enum.get_standby_mode(standby=standby)
        return standby_value

    def customer_device_name_method(self, obj):
        if obj and obj.device_name:
            return obj.device_name.device_id
        else:
            return None

    def client_label_method(self, obj):
        if obj.client:
            client = obj.client.name
            return client
        else:
            return None

    def leased_owned_name_method(self, obj):
        if obj.leased_owned:
            type = obj.leased_owned.label
            return type
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

    def module_method(self, obj):
        if obj.module:
            mod = obj.module.name
            return mod
        else:
            return None

    def status_method(self, obj):
        if obj.status:
            stat = obj.status.label
            # stat = "Active"
            return stat
        else:
            return None

    def energy_consumed_last_24_hrs(self, obj):
        if obj:
            yesterday = timezone.now() - timedelta(days=1)
            try:
                data = IopDerived.objects.get(device=obj, timestamp__date = yesterday.date())
                return data.total_energy_consumed
            except:
                return None

    def active_hrs_last_24_hrs(self, obj):
        if obj:
            yesterday = timezone.now() - timedelta(days=1)
            try:
                data = IopDerived.objects.get(device=obj, timestamp__date = yesterday.date())
                return data.active_duration
            except:
                return None

    def errors_last_24_hrs(self, obj):
        if obj:
            yesterday = timezone.now() - timedelta(days=1)
            try:
                data = IopDerived.objects.get(device=obj, timestamp__date = yesterday.date())
                return data.total_errors
            except:
                return None

    def entity_sub_type_name_method(self, obj):
        if obj.entity_sub_type:
            type = obj.entity_sub_type.label
            return type
        else:
            return None


    class Meta:
        model = Entity
        fields = [
            # Common fields to be included in every Entity serializer
            'id',
            'name',
            'type',
            'types',
            'customer',
            'assignments',
            'device_name',
            'device_name_method',
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
            'ctt',
            'cdt',
            'clm',
            'cht',
            

            #SSID and PASSWORD.
            'engine_number',
            'chassis_number',

            'model',
            'make',
            'weight',

            # Sold Status
            'obd2_compliant',
            #Model Type of Device.
            'leased_owned',
            'leased_owned_name',
            #capacity of device if any
            'volume_capacity',
            #Frequency
            'cnic',
            #Energy
            'age',
            #Device type i.e. (Water heater, refrigirator, AC)
            'entity_sub_type',
            'entity_sub_type_name',
            #Sub Type of Device. i.e. (Water heater: Vertical Tank etc)
            'breed',
            #Dimensions
            'ethnicity',
            #Classification
            'past_club',
            #Heated up Temperature
            'player_position',

            #Method Fields
            'energy_consumed_yesterday',
            'active_hrs_yesterday',
            'errors_yesterday',
            'is_enabled',
            'source_latlong',
            'registration',
            'is_manual_mode',
            'standby_mode',
            'standby',
            'is_washing_machine'
        ]

class IOPApplianceFrontendsSerializer(ModelSerializer):
    status_label = SerializerMethodField('status_method', required=False, allow_null=True)
    entity_sub_type_name = SerializerMethodField('entity_sub_type_name_method', required=False, allow_null=True)
    device_name_method = SerializerMethodField('customer_device_name_method', allow_null=True, required=False,read_only=True)
    leased_owned_name = SerializerMethodField('leased_owned_name_method', required=False, allow_null=True)
    standby = SerializerMethodField('validate_standby', required=False, allow_null=True)
    type=SerializerMethodField('validate_type', required=False, allow_null=True)

    def validate_standby(self, obj):
        standby=obj.standby_mode
        standby_value = enum.get_standby_mode(standby=standby)
        return standby_value
    def validate_type(self,obj):
        if obj:
            if 'wh' in str(obj.device_name.device_id):
                return 'Vertical Tank'
            else:
                return None
    def leased_owned_name_method(self, obj):
        if obj.leased_owned:
            type = obj.leased_owned.label
            return type
        else:
            return None
    def customer_device_name_method(self, obj):
        if obj and obj.device_name:
            return obj.device_name.device_id
        else:
            return None
    def entity_sub_type_name_method(self, obj):
        if obj.entity_sub_type:
            type = obj.entity_sub_type.label
            return type
        else:
            return None

    def status_method(self, obj):
        if obj.status:
            stat = obj.status.label
            # stat = "Active"
            return stat
        else:
            return None
    class Meta:
        model=Entity
        fields='__all__'

class HomeApplianceFrontendsSerializer(ModelSerializer):
    module_name = SerializerMethodField('module_method', required=False, allow_null=True)
    status_label = SerializerMethodField('status_method', required=False, allow_null=True)
    modified_by_name = SerializerMethodField('modified_name', allow_null=True, required=False, read_only=True)
    modified_by_email = SerializerMethodField('modified_email', allow_null=True, required=False, read_only=True)
    entity_sub_type_name = SerializerMethodField('entity_sub_type_name_method', required=False, allow_null=True)
    device_name_method = SerializerMethodField('customer_device_name_method', allow_null=True, required=False,read_only=True)
    energy_consumed_yesterday = SerializerMethodField('energy_consumed_last_24_hrs', allow_null=True, required=False,read_only=True)
    active_hrs_yesterday = SerializerMethodField('active_hrs_last_24_hrs', allow_null=True, required=False,read_only=True)
    errors_yesterday = SerializerMethodField('errors_last_24_hrs', allow_null=True, required=False,read_only=True)
    leased_owned_name = SerializerMethodField('leased_owned_name_method', required=False, allow_null=True)
    standby = SerializerMethodField('validate_standby', required=False, allow_null=True)
    ctt = SerializerMethodField('validate_ctt', required=False, allow_null=True)
    cdt=SerializerMethodField('validate_cdt', required=False, allow_null=True)
    clm=SerializerMethodField('validate_clm', required=False, allow_null=True)
    cht=SerializerMethodField('validate_cht', required=False, allow_null=True)
    type=SerializerMethodField('validate_type', required=False, allow_null=True)
    online_status=SerializerMethodField()
    last_updated=SerializerMethodField()
    device_model=SerializerMethodField()

    def get_online_status(self,obj):
        try:
            query=LogisticAggregations.objects.get(device_id=obj.id)

            return query.online_status
        except:
            return None
    

    def get_last_updated(self,obj):
        try:
            query=LogisticAggregations.objects.get(device_id=obj.id)

            return query.last_updated
        except:
            return None

    def get_device_model(self,obj):
        try:
            query=LogisticAggregations.objects.get(device_id=obj.id)

            return query.device.leased_owned.label
        except:
            return None
    
    def validate_type(self,obj):
        if obj:
            if 'wh' in str(obj.device_name.device_id):
                return 'Vertical Tank'
            else:
                return None
                
    def validate_cht(self, obj):
        if obj:
            print(obj.id)
            try:
                data = HypernetPostData.objects.filter(device_id=obj.id).latest('timestamp')
                print(data)
                return data.active_score

            except Exception as e:
                return None
    def validate_clm(self, obj):
        if obj:
            print(obj.id)
            try:
                data = HypernetPostData.objects.filter(device_id=obj.id).latest('timestamp')
                print(data)
                return data.clm

            except Exception as e:
                
                return None
    def validate_cdt(self, obj):
        if obj:
            try:
                data = HypernetPostData.objects.filter(device_id=obj.id).latest('timestamp')
                print(data)
                return data.cdt

            except Exception as e:
               
                return None
                
    def validate_ctt(self, obj):
        if obj:
            print(obj.id)
            try:
                data = HypernetPostData.objects.filter(device_id=obj.id).latest('timestamp')
                print(data)
                return data.ctt

            except Exception as e:
               
                return None
    def validate_standby(self, obj):
        standby=obj.standby_mode
        print('check here', standby)
        standby_value = enum.get_standby_mode(standby=standby)
        return standby_value

    def customer_device_name_method(self, obj):
        if obj and obj.device_name:
            return obj.device_name.device_id
        else:
            return None

    def client_label_method(self, obj):
        if obj.client:
            client = obj.client.name
            return client
        else:
            return None

    def leased_owned_name_method(self, obj):
        if obj.leased_owned:
            type = obj.leased_owned.label
            return type
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

    def module_method(self, obj):
        if obj.module:
            mod = obj.module.name
            return mod
        else:
            return None

    def status_method(self, obj):
        if obj.status:
            stat = obj.status.label
            # stat = "Active"
            return stat
        else:
            return None

    def energy_consumed_last_24_hrs(self, obj):
        if obj:
            yesterday = timezone.now() - timedelta(days=1)
            try:
                data = IopDerived.objects.get(device=obj, timestamp__date = yesterday.date())
                return data.total_energy_consumed
            except:
                return None

    def active_hrs_last_24_hrs(self, obj):
        if obj:
            yesterday = timezone.now() - timedelta(days=1)
            try:
                data = IopDerived.objects.get(device=obj, timestamp__date = yesterday.date())
                return data.active_duration
            except:
                return None

    def errors_last_24_hrs(self, obj):
        if obj:
            yesterday = timezone.now() - timedelta(days=1)
            try:
                data = IopDerived.objects.get(device=obj, timestamp__date = yesterday.date())
                return data.total_errors
            except:
                return None

    def entity_sub_type_name_method(self, obj):
        if obj.entity_sub_type:
            type = obj.entity_sub_type.label
            return type
        else:
            return None


    class Meta:
        model = Entity
        fields = [
            # Common fields to be included in every Entity serializer
            'id',
            'name',
            'online_status',
            'last_updated',
            'device_model',
            'type',
            'customer',
            'assignments',
            'device_name',
            'device_name_method',
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
            'ctt',
            'cdt',
            'clm',
            'cht',
            

            #SSID and PASSWORD.
            'engine_number',
            'chassis_number',

            'model',
            'make',
            'weight',

            # Sold Status
            'obd2_compliant',
            #Model Type of Device.
            'leased_owned',
            'leased_owned_name',
            #capacity of device if any
            'volume_capacity',
            #Frequency
            'cnic',
            #Energy
            'age',
            #Device type i.e. (Water heater, refrigirator, AC)
            'entity_sub_type',
            'entity_sub_type_name',
            #Sub Type of Device. i.e. (Water heater: Vertical Tank etc)
            'breed',
            #Dimensions
            'ethnicity',
            #Classification
            'past_club',
            #Heated up Temperature
            'player_position',

            #Method Fields
            'energy_consumed_yesterday',
            'active_hrs_yesterday',
            'errors_yesterday',
            'is_enabled',
            'source_latlong',
            'registration',
            'is_manual_mode',
            'standby_mode',
            'standby',
            'is_washing_machine'
        ]


class InvoiceDataSerializer(ModelSerializer):
    customer_name = SerializerMethodField('customer_method', allow_null=True, required=False, read_only=True)
    module_name = SerializerMethodField('module_method', required=False, allow_null=True)
    client_name = SerializerMethodField('client_method', allow_null=True, required=False, read_only=True)
    contract_name = SerializerMethodField('contract_method', allow_null=True, required=False,read_only=True)
    contract_type_label = SerializerMethodField('contract_type_method', required=False, allow_null=True)
    area_name = SerializerMethodField('area_method', allow_null=True, required=False, read_only=True)
    payment_status_label = SerializerMethodField('payment_status_method', required=False, allow_null=True)

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

    def area_method(self, obj):
        if obj.area:
            return obj.area.__str__()
        else:
            return None

    def contract_method(self, obj):
        if obj.area:
            return obj.area.__str__()
        else:
            return None

    def contract_type_method(self, obj):
        if obj.contract_type:
            stat = obj.contract_type.label
            return stat
        else:
            return None

    def module_method(self, obj):
        if obj.module:
            mod = obj.module.name
            return mod
        else:
            return None

    def payment_status_method(self, obj):
        if obj.payment_status:
            return "Paid"
        else:
            return "Un Paid"

    class Meta:
        model = InvoiceData

        fields = [
            'id',
            'invoice_number',
            'customer',
            'customer_name',
            'module',
            'module_name',
            'created_datetime',

            'client',
            'client_name',
            'contract',
            'contract_name',
            'contract_type',
            'contract_type_label',
            'area',
            'area_name',

            'start_datetime',
            'end_datetime',

            'payment_status',
            'payment_status_label',
            'total_sum',
            'invoice_path'

        ]


class ApplianceQRSerializer(ModelSerializer):
    password = SerializerMethodField('password_method', allow_null=True, required=False, read_only=True)
    
    def password_method(self, obj):
        import base64
        if obj.password:
            message=obj.password
            encodedBytes = base64.b64encode(message.encode("utf-8"))
            encodedStr = str(encodedBytes, "utf-8")
            print(encodedStr)
            return str(encodedStr)     
        else:
            return None
    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super(ApplianceQRSerializer, self).__init__(many=many, *args, **kwargs)

    class Meta:
        model = ApplianceQR

        fields = [
            'ssid',
            'password',
            'created_datetime',
            # 'device_id'
        ]


class UpdateEntitySettingSerializer(ModelSerializer):
    class Meta:
        model=Entity
        fields = ['id', 'is_manual_mode', 'standby_mode', 'is_washing_machine']

