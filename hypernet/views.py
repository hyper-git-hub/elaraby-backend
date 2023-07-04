from django.http import JsonResponse
from rest_framework.permissions import (
    AllowAny,
)
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from hypernet.utils import generic_response, verify_request_params, exception_handler, get_value_from_data
from rest_framework.response import Response
from rest_framework.views import APIView
import dateutil.parser, traceback
import datetime as date_time
from django.core.mail import send_mail
from django.utils import timezone
import json
from backend import settings
from .constants import email_list
from hypernet.serializers import BinSerializer
from .constants import email_list, ERROR_RESPONSE_BODY, RESPONSE_MESSAGE, RESPONSE_STATUS, STATUS_OK, RESPONSE_DATA
from hypernet import constants
from hypernet.enums import OptionsEnum
from hypernet.utils import get_request_param, \
    response_json, generic_response, get_param, get_data_param
from .models import Devices, HypernetPreData, Entity, HypernetPostData
from iof.models import LogisticAggregations


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
        data_list = request.data
        try:
            if data_list is not None:
                for data in data_list:
                    # print(data)
                    device_id = data.get('id')
                    
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
                        longitude = get_value_from_data('lon', data, 'float', None)
                    speed = get_value_from_data('speed', data, 'float', None)
                    if speed is None:
                        speed = get_value_from_data('spd', data, 'float', 0)
                    trip = get_value_from_data('trip', data, 'int', 0)
                    harsh_braking = get_value_from_data('h_br', data, 'int', 0)
                    harsh_acceleration = get_value_from_data('h_acc', data, 'int', 0)
                    nn_interval= data.get('nn_interval')
                    accelerometer_1= get_value_from_data('nw', data, 'float', 0)
                    accelerometer_2= get_value_from_data('gw', data, 'float', 0)
                    validity= True#data.get('valid')
                    accelerometer_3= data.get('az')
                    gyro_1 = data.get('gx')
                    gyro_2 = data.get('gy')
                    gyro_3 = data.get('gz')
                    hrv_value= data.get('hrv_value')
                    breathingrate_avg= data.get('breathingrate_avg')
                    breathingrate_min= data.get('breathingrate_min')
                    breathingrate_max= data.get('breathingrate_max')
                    duration= data.get('duration')
                    heartrate_value= data.get('heartrate_value')
                    heartrate_recovery= data.get('heartrate_recovery')
                    distance_by_sensor= data.get('distance_by_sensor')
                    type = data.get('type')
                    customer = data.get('cust')
                    module = data.get('mod')
                    
                    t_timestamp = data.get('t_timestamp')
                    try:
                        if t_timestamp:
                            t_timestamp = dateutil.parser.parse(t_timestamp)
                        else:
                            t_timestamp = dateutil.parser.parse(data.get('t'))
                        t_timestamp = timezone.make_aware(t_timestamp)
                        if (timezone.now() - t_timestamp).days > 2:  # The date sent is older than 2 days - Fix it
                            t_timestamp = timezone.now()
                        if (t_timestamp - timezone.now()).days > 2:  # The date sent is in the future - Fix it
                            t_timestamp = timezone.now()
                    except:
                        t_timestamp = timezone.now()
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
                            Devices.objects.get(device=en)
                        except Exception as e:
                            Devices.objects.create(device=en, timestamp=t_timestamp)
                            pass
                        HypernetPreData.objects.create(
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
                            harsh_acceleration = harsh_acceleration or False,
                            nn_interval = nn_interval,
                            accelerometer_1 = accelerometer_1,
                            accelerometer_2 = accelerometer_2,
                            accelerometer_3 = accelerometer_3,
                            validity = validity,
                            gyro_1=gyro_1,
                            gyro_2=gyro_2,
                            gyro_3=gyro_3,
                            hrv_value = hrv_value,
                            breathingrate_avg = breathingrate_avg,
                            breathingrate_min = breathingrate_min,
                            breathingrate_max = breathingrate_max,
                            duration = duration,
                            heartrate_value = heartrate_value,
                            heartrate_recovery = heartrate_recovery,
                            distance_by_sensor = distance_by_sensor,
                            timestamp=t_timestamp,
                                           
                                           )
                        try:
                            status = LogisticAggregations.objects.get(device=en)
                            if status.online_status:
                                pass
                            else:
                                status.online_status = True
                                status.save()
                                send_mail('Hypernet Device Online', 'Device is back online id:' + en.name + ' time: ' + str(
                                    t_timestamp),
                                          'support@hypernymbiz.com', email_list, fail_silently=False)
                        except Exception as e:
                            continue
                        successfully_saved_truck_counter += 1
                    except Exception as e:
                        # traceback.print_exc()
                        continue
                if all_trucks_saved_successfully:
                    return generic_response((response_json(True,None, constants.TEXT_OPERATION_SUCCESSFUL)), http_status=200)
                else:
                    return generic_response(response_json(False, None, constants.TEXT_OPERATION_UNSUCCESSFUL),
                                         http_status=400)
            else:
                return generic_response(response_json(False, None, constants.TEXT_PARAMS_MISSING),http_status=400)
        except Exception as e:
            traceback.print_exc()
            return generic_response(response_json(False, None, constants.TEXT_OPERATION_UNSUCCESSFUL),http_status=500)

    
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
                
                temperature = data.get('f_temperature')
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
                accelerometer_1 = data.get('w_n')
                accelerometer_2 = data.get('w_grs')
                accelerometer_3 = data.get('az')
                gyro_1 = data.get('gx')
                gyro_2 = data.get('gy')
                gyro_3 = data.get('gz')
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
                if (timezone.now() - t_timestamp).days > 2:  # The date sent is older than 2 days - Discard it
                    t_timestamp = None
                if (t_timestamp - timezone.now()).days > 2:  # The date sent is in the future - Discard it
                    t_timestamp = None
                try:
                    if not latitude or not longitude:
                        latitude = None
                        longitude = None
                    else:
                        if int(latitude) == 0 or int(longitude) == 0:
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

                    )

                    successfully_saved_truck_counter += 1
                except Exception as e:
                    # traceback.print_exc()
                    all_trucks_saved_successfully = False
                if all_trucks_saved_successfully:
                    return generic_response((response_json(True, None, constants.TEXT_OPERATION_SUCCESSFUL)),
                                            http_status=200)
                else:
                    # traceback.print_exc()
                    return generic_response(response_json(False, None, constants.TEXT_OPERATION_UNSUCCESSFUL),
                                            http_status=400)
            else:
                return generic_response(response_json(False, None, constants.TEXT_PARAMS_MISSING),http_status=403)
        except Exception as e:
            traceback.print_exc()
            return generic_response(response_json(False, None, constants.TEXT_OPERATION_UNSUCCESSFUL), http_status=500)



