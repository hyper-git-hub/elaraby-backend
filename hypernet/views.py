from hypernet.notifications.utils import send_notification_violations
from iop.utils import update_online_status_iop_device
from rest_framework.permissions import (
    AllowAny,
)

from hypernet.utils import get_value_from_data
from iof.utils import update_collection_for_truck
from rest_framework.response import Response
from rest_framework.views import APIView
import dateutil.parser, traceback
import datetime as date_time
from django.core.mail import send_mail
from django.utils import timezone
import json
from backend import settings
from hypernet.serializers import BinSerializer
from .constants import email_list
from hypernet import constants
from hypernet.utils import get_request_param, \
    response_json, generic_response, get_param, get_data_param, get_data_param_list
from .models import Devices, HypernetPreData, Entity, HypernetPostData
from iof.models import LogisticAggregations
import pyrebase
from hypernet.enums import *
from user.models import *
from iop.models import IopAggregation
from customer.models import Customer


class GetEntity(APIView):
    """

    """
    """
            @api {get} /hypernet/entity/
            @apiName GetEntity
            @apiGroup Entity
            @apiDescription Return the entity of the id specified
            @apiParam {Integer} [id] device_id

    """

    def get(self, request, bin_id):
        try:
            entity = Entity.objects.get(id=bin_id)
        except Entity.DoesNotExist:
            return generic_response(response_json(False, None, constants.TEXT_OPERATION_UNSUCCESSFUL), 400)

        serializer = BinSerializer(entity)
        return generic_response(response_json(True, serializer.data))

    def put(self, request, bin_id):
        try:
            entity = Entity.objects.get(id=bin_id)
        except Entity.DoesNotExist:
            return generic_response(response_json(False, None, constants.TEXT_OPERATION_UNSUCCESSFUL), 400)
        data = get_data_param(request, 'data', None)
        serializer = BinSerializer(entity, data=json.loads(data))
        if serializer.is_valid():
            serializer.save()
            return generic_response(response_json(True, serializer.data))
        return generic_response(response_json(False, None, constants.TEXT_OPERATION_UNSUCCESSFUL), 400)

    def delete(self, request, bin_id):
        try:
            entity = Entity.objects.get(id=bin_id)
        except Entity.DoesNotExist:
            return generic_response(response_json(False, None, constants.TEXT_OPERATION_UNSUCCESSFUL), 400)
        entity.status = OptionsEnum.INACTIVE
        entity.end_datetime = timezone.now()
        serializer = BinSerializer(entity)
        if serializer.is_valid():
            serializer.save()
            return generic_response(response_json(True, serializer.data))
        return generic_response(response_json(False, None, constants.TEXT_OPERATION_UNSUCCESSFUL), 400)


class HypernetDataIngestion(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        successfully_saved_truck_counter = 0
        all_trucks_saved_successfully = True
        data = request.data
        firebase = pyrebase.initialize_app(settings.config_firebase)
        print(type(data))
        data = json.loads(data)
        print(type(data))
        try:
            if data is not None:
                db = firebase.database()
                if db and data.get('dID') in constants.iop_devices:
                    db.child(data.get('dID')).set(str(data))
                device_id = data.get('id') or data.get('dID')
                temperature = get_value_from_data('f_temperature', data, 'float', None)
                if temperature is None:
                    temperature = get_value_from_data('temp', data, 'float', 0)
                volume = get_value_from_data('f_volume', data, 'float', None)
                if volume is None:
                    volume = get_value_from_data('vol', data, 'float', 0)
                density = get_value_from_data('f_density', data, 'float', None)
                if density is None:
                    density = get_value_from_data('dens', data, 'float', 0)
                latitude = get_value_from_data('latitude', data, 'float', None)
                if latitude is None:
                    latitude = get_value_from_data('lat', data, 'float', None)
                longitude = get_value_from_data('longitude', data, 'float', None)
                if longitude is None:
                    longitude = get_value_from_data('lng', data, 'float', None) or get_value_from_data('lon', data,
                                                                                                       'float',
                                                                                                       None)
                speed = get_value_from_data('speed', data, 'float', None)
                if speed is None:
                    speed = get_value_from_data('spd', data, 'float', 0)
                trip = get_value_from_data('trip', data, 'int', 0)
                harsh_braking = get_value_from_data('h_br', data, 'int', 0)
                harsh_acceleration = get_value_from_data('h_acc', data, 'int', 0)
                nn_interval = data.get('nn_interval')
                accelerometer_1 = get_value_from_data('nw', data, 'float', 0)
                accelerometer_2 = get_value_from_data('gw', data, 'float', 0)
                validity = True  # data.get('valid')
                accelerometer_3 = data.get('az')
                gyro_1 = get_value_from_data('saf', data, 'int', 0)
                gyro_2 = get_value_from_data('sdf', data, 'int', 0)
                gyro_3 = get_value_from_data('stf', data, 'int', 0)
                hrv_value = data.get('hrv_value')
                breathingrate_avg = data.get('breathingrate_avg')
                breathingrate_min = data.get('breathingrate_min')
                breathingrate_max = data.get('breathingrate_max')
                duration = data.get('duration')
                heartrate_value = data.get('heartrate_value') or data.get('chs')  # chs = on and off status
                heartrate_recovery = data.get('heartrate_recovery')
                distance_by_sensor = data.get('distance_by_sensor')
                # type = data.get('type')
                customer = data.get('cust')
                module = data.get('mod')
                active_score = data.get('active_score') or data.get('cht')  # current heater temperature
                inactive_score = data.get('inactive_score') or data.get('err')  # error code.
                t_timestamp = data.get('t_timestamp') or data.get('ts')
                ctt = data.get('ctt')
                clm=data.get('clm')
                cdt=data.get('cdt')
                debug_key = data.get('d')

                try:
                    if t_timestamp:
                        t_timestamp = dateutil.parser.parse(t_timestamp)
                    else:
                        t_timestamp = dateutil.parser.parse(data.get('t'))
                    t_timestamp = timezone.make_aware(t_timestamp)
                    t_timestamp = t_timestamp.replace(microsecond=0)

                    # print(timezone.now() - t_timestamp)
                    if (
                        timezone.now() - t_timestamp).total_seconds() > 7200:  # The date sent is older than 2 hours - Fix it
                        t_timestamp = timezone.now()
                        t_timestamp = t_timestamp.replace(microsecond=0)
                    if (
                        t_timestamp - timezone.now()).total_seconds() > 7200:  # The date sent is in the future - Fix it
                        t_timestamp = timezone.now()
                        t_timestamp = t_timestamp.replace(microsecond=0)

                except:
                    # traceback.print_exc()
                    t_timestamp = timezone.now()
                    t_timestamp = t_timestamp.replace(microsecond=0)
                try:
                    if not latitude or not longitude:
                        latitude = None
                        longitude = None
                    else:
                        if float(latitude) == 0 or float(longitude) == 0:
                            latitude = None
                            longitude = None
                    en = Entity.objects.get(device_name__device_id=device_id, status__id=OptionsEnum.ACTIVE)
                    try:
                        device = Devices.objects.get(device=en)
                        if en.type_id == DeviceTypeEntityEnum.IOP_DEVICE:
                            device.timestamp = timezone.now()
                            device.save()
                    except Exception as e:
                        Devices.objects.create(device=en, timestamp=t_timestamp)
                        pass

                    if accelerometer_1 > 4000000:
                        accelerometer_1 = 2 ** 32 - accelerometer_1

                    if accelerometer_2 > 4000000:
                        accelerometer_2 = 2 ** 32 - accelerometer_1

                    if accelerometer_1 > accelerometer_2:
                        accelerometer_1 = accelerometer_2
                        accelerometer_2 = accelerometer_1

                    # Check for bin collection data and get the weight calculated here.
                    if en.type.id == DeviceTypeEntityEnum.TRUCK:
                        update_collection_for_truck(en, accelerometer_1, t_timestamp)

                    pre_data = HypernetPreData.objects.create(
                        device=en,
                        customer=en.customer,
                        module=en.module,
                        type=en.type,
                        temperature=temperature,
                        volume=volume,
                        density=density,
                        latitude=latitude,
                        longitude=longitude,
                        speed=speed,
                        trip=trip or False,
                        harsh_braking=harsh_braking or False,
                        harsh_acceleration=harsh_acceleration or False,
                        nn_interval=nn_interval,
                        accelerometer_1=accelerometer_1,
                        accelerometer_2=accelerometer_2,
                        accelerometer_3=accelerometer_3,
                        validity=validity,
                        gyro_1=gyro_1,
                        gyro_2=gyro_2,
                        gyro_3=gyro_3,
                        hrv_value=hrv_value,
                        breathingrate_avg=breathingrate_avg,
                        breathingrate_min=breathingrate_min,
                        breathingrate_max=breathingrate_max,
                        duration=duration,

                        # CHS
                        heartrate_value=heartrate_value,
                        heartrate_recovery=heartrate_recovery,
                        distance_by_sensor=distance_by_sensor,
                        timestamp=t_timestamp,

                        # Current Heater Temperature
                        active_score=active_score,

                        # Device Errors
                        inactive_score=inactive_score,

                        # Device Frimware Information
                        debug_key=debug_key,

                        # Heater Temperature Threshold
                        ctt=ctt,
                        cdt=cdt,
                        clm=clm,
                        )


                    if speed > 5:
                        users = User.objects.filter(role_id=RoleTypeEnum.ADMIN, customer_id=en.customer_id)
                        if data.get('gw') == 1 and data.get('nw') == 1:
                            if en.location is False or en.location is None:
                                en.location = True  # flag for checking whether notification has been sent to user or not
                                en.save()
                                # print('Location set to true' + en.name)
                                #  send_notification_violations(device=en.id, driver_id=None,
                                #                               customer_id = en.customer.id,
                                #                               module_id = en.module.id,
                                #                               title = str(en.name)+ ' is moving but weight module is not turned on',
                                #                               users_list = users)


                        else:
                            en.location = False
                    else:
                        en.location = False
                    en.save()

                    # Check violations with new version 6.2.4 or later
                    self.violation_notifications(en, pre_data)

                    try:
                        status = LogisticAggregations.objects.filter(device=en).last()
                        if status:
                            if status.online_status:
                                status.last_temperature = pre_data.active_score
                                status.last_volume = pre_data.heartrate_value
                                status.last_density = pre_data.ctt
                                status.timestamp = timezone.now()
                                status.last_updated = timezone.now()
                                status.save()
                            else:
                                status.online_status = True
                                status.timestamp = timezone.now()
                                status.last_updated = timezone.now()
                                status.save()
                                if en.type.id != DeviceTypeEntityEnum.IOP_DEVICE:
                                    send_mail('Hypernet Prod Device Online',
                                              'Device is back online id:' + en.name + ' time: ' + str(
                                                  t_timestamp),
                                              'support@hypernymbiz.com', email_list, fail_silently=False)
                        else:
                            customer = Customer.objects.get(id=en.customer_id)
                            module = Module.objects.get(id = en.module_id)
                            print("here")
                            dev_status = LogisticAggregations(device = en)
                            dev_status.online_status = True
                            dev_status.customer = customer
                            dev_status.module = module
                            dev_status.timestamp = timezone.now()
                            dev_status.last_updated = timezone.now()
                            dev_status.save()
                            print(dev_status)

                    except Exception as e:
                        print('logistic aggregaton execption  ', e)

                    successfully_saved_truck_counter += 1
                except Exception as e:
                    # traceback.print_exc()
                    pass
                if all_trucks_saved_successfully:
                    return generic_response((response_json(True, None, constants.TEXT_OPERATION_SUCCESSFUL)),
                                            http_status=200)
                else:
                    return generic_response(response_json(False, None, constants.TEXT_OPERATION_UNSUCCESSFUL),
                                            http_status=400)
            else:
                return generic_response(response_json(False, None, constants.TEXT_PARAMS_MISSING), http_status=400)

        except Exception as e:
            print(e)
            traceback.print_exc()
            return generic_response(response_json(False, None, constants.TEXT_OPERATION_UNSUCCESSFUL), http_status=500)

    def violation_notifications(self, entity, msg):
        users = User.objects.filter(role_id=RoleTypeEnum.ADMIN, customer_id=entity.customer_id)
        send = False
        message = None
        if msg.gyro_1:
            send = True
            message = "Sharp Acceleration alert! Vehicle: " + entity.name
        elif msg.gyro_2:
            send = True
            message = "Sharp Acceleration alert! Vehicle: " + entity.name
        elif msg.gyro_3:
            send = True
            message = "Sharp Acceleration alert! Vehicle: " + entity.name

        if send:
            send_notification_violations(entity,
                                         None,
                                         entity.customer_id,
                                         entity.module_id,
                                         message,
                                         users)


class HypernetQueuedDataIngestion(APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        successfully_saved_truck_counter = 0
        all_trucks_saved_successfully = True
        try:
            data_message = get_param(request, 'data', None)
            if data_message:
                data_message = json.loads(data_message)

                data = data_message
                device_id = data.get('id')

                temperature = data.get('f_temperature') or data.get('cht')  # current heater temperature
                if temperature is None:
                    temperature = data.get('temp')
                volume = data.get('f_volume')
                if volume is None:
                    volume = data.get('vol')
                density = data.get('f_density')
                if density is None:
                    density = data.get('dens')
                latitude = data.get('latitude')
                if latitude is None:
                    latitude = data.get('lat')
                longitude = data.get('longitude')
                if longitude is None:
                    longitude = data.get('lon')
                speed = data.get('speed')
                if speed is None:
                    speed = data.get('spd')

                trip = data.get('trip')
                harsh_braking = data.get('h_br')
                harsh_acceleration = data.get('h_acc')
                nn_interval = data.get('nn_interval')
                accelerometer_1 = data.get('nw')
                accelerometer_2 = data.get('gw')
                accelerometer_3 = data.get('az')
                gyro_1 = data.get('saf')
                gyro_2 = data.get('sdf')
                gyro_3 = data.get('stf')
                hrv_value = data.get('hrv_value')
                breathingrate_avg = data.get('breathingrate_avg')
                breathingrate_min = data.get('breathingrate_min')
                breathingrate_max = data.get('breathingrate_max')
                duration = data.get('duration')
                heartrate_value = data.get('heartrate_value')
                heartrate_recovery = data.get('heartrate_recovery')
                distance_by_sensor = data.get('distance_by_sensor')
                type = data.get('type')
                customer = data.get('cust')
                module = data.get('mod')

                t_timestamp = data.get('t_timestamp')
                if t_timestamp:
                    t_timestamp = dateutil.parser.parse(t_timestamp)
                else:
                    t_timestamp = dateutil.parser.parse(data.get('t'))
                t_timestamp = timezone.make_aware(t_timestamp)
                t_timestamp = t_timestamp.replace(microsecond=0)
                if (timezone.now() - t_timestamp).days > 2:  # The date sent is older than 2 days - Discard it
                    t_timestamp = None
                if (t_timestamp - timezone.now()).days > 2:  # The date sent is in the future - Discard it
                    t_timestamp = None
                try:
                    if not latitude or not longitude:
                        latitude = None
                        longitude = None
                    else:
                        if float(latitude) == 0 or float(longitude) == 0:
                            latitude = None
                            longitude = None
                    en = Entity.objects.get(device_name__device_id=device_id)
                    try:
                        Devices.objects.get(device=Entity.objects.get(device_name__device_id=device_id))
                    except Exception as e:
                        Devices.objects.create(device=Entity.objects.get(device_name__device_id=device_id),
                                               timestamp=t_timestamp)

                        pass

                    HypernetPostData.objects.create(
                        device=en,
                        customer=en.customer,
                        module=en.module,
                        type=en.type,
                        temperature=temperature,
                        volume=volume,
                        density=density,
                        latitude=latitude,
                        longitude=longitude,
                        speed=speed,
                        trip=trip or False,
                        harsh_braking=harsh_braking or False,
                        harsh_acceleration=harsh_acceleration or False,
                        nn_interval=nn_interval,
                        accelerometer_1=accelerometer_1,
                        accelerometer_2=accelerometer_2,
                        accelerometer_3=accelerometer_3,
                        gyro_1=gyro_1,
                        gyro_2=gyro_2,
                        gyro_3=gyro_3,
                        hrv_value=hrv_value,
                        breathingrate_avg=breathingrate_avg,
                        breathingrate_min=breathingrate_min,
                        breathingrate_max=breathingrate_max,
                        duration=duration,
                        heartrate_value=heartrate_value,
                        heartrate_recovery=heartrate_recovery,
                        distance_by_sensor=distance_by_sensor,
                        timestamp=t_timestamp,
                        processed=True,

                    )

                    successfully_saved_truck_counter += 1
                except Exception as e:
                    traceback.print_exc()
                    all_trucks_saved_successfully = False
                if all_trucks_saved_successfully:
                    return generic_response((response_json(True, None, constants.TEXT_OPERATION_SUCCESSFUL)),
                                            http_status=200)
                else:
                    # traceback.print_exc()
                    return generic_response(response_json(False, None, constants.TEXT_OPERATION_UNSUCCESSFUL),
                                            http_status=400)
            else:
                return generic_response(response_json(False, None, constants.TEXT_PARAMS_MISSING), http_status=403)
        except Exception as e:
            traceback.print_exc()
            return generic_response(response_json(False, None, constants.TEXT_OPERATION_UNSUCCESSFUL), http_status=500)
