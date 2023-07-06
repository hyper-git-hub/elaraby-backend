import calendar
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.views.decorators.csrf import csrf_exempt
# from geopy.distance import vincenty
import datetime as date_time
# For testing purposes
from hypernet.entity.job_V2.utils import check_conflicts_multi_days, suspend_overlapping_schedules
from rest_framework.decorators import api_view

from django.core.mail import send_mail, EmailMultiAlternatives
from twilio.rest import Client as client
# from backend import settings, local_settings
from ffp.cron_utils import get_geofence_violations, polygon_operations, check_employee_active_status
from ioa.tests.report_test import ReportViewInvoice
from user.enums import RoleTypeEnum
from .models import HypernetPreData, HypernetPostData, Entity, Module, DeviceType, Devices, HypernetNotification, \
    Assignment, DeviceCalibration, NotificationGroups, DeviceViolation
from iof.models import LogisticsDerived, TruckTrips, LogisticAggregations, ActivityQueue, Activity
from iof.generic_utils import get_generic_device_aggregations, get_generic_distance_travelled, \
    get_generic_volume_consumed, get_generic_jobs, get_generic_maintenances, get_generic_violations, \
    get_generic_fillups, get_generic_decantation, get_generic_trips, fillup_summary
from customer.models import Customer, CustomerClients
from .enums import DeviceTypeEntityEnum, IOFOptionsEnum, DeviceTypeAssignmentEnum, IopOptionsEnums,Enum
from hypernet.utils import *
from hypernet import constants
from hypernet.enums import OptionsEnum, FFPOptionsEnum
from iof.models import ActivityData, BinCollectionData
from datetime import datetime, timedelta, date
from django.utils import timezone
from user.models import User
from hypernet.notifications.utils import send_notification_to_user, util_save_activity_notification, \
    send_notification_to_admin, send_notification_violations, save_users_group
from options.models import Options
from hypernet.entity.utils import util_create_activity
from customer.models import CustomerPreferences
from iof.utils import create_activity_data, update_bin_statuses, create_bin_collection_data, RESPONSE_DATA, \
    HTTP_SUCCESS_CODE, check_activity_on_truck, check_shift_on_truck

email_list = constants.email_list
client_email_list = constants.client_email_list
from ffp.models import AttendanceRecord, Tasks
from ffp.reporting_utils import create_violation_data
from shapely.geometry import Point, Polygon
# from iop.models import IopDerived
from iop.models import IopDerived, ErrorLogs
from ioa.tests.report_test import ReportViewGeneric
from hypernet.enums import ModuleEnum
from user.models import ModuleAssignment
from iof.models import ActivitySchedule
from dateutil.parser import parse
from hypernet.entity.job_V2.utils import check_conflicts_days_after
import requests
import time

from iop.utils import *
from iop.crons.crons import *
from iop.crons.crons import retry_failure_cron,retry_failure_lock_mode_cron
from hypernet.entity.job_V2.utils import appliance_error,get_chs_value_from_hyperpredata_hyperpostdata
from iof.serializers import ActivityScheduleSerializer
enum=Enum()

@api_view(['GET'])
def process_pre_data(request):
    # def process_pre_data():
    try:
        # res = api.send_sms(body='I can haz txt', from_phone='+923465283576', to=['+923465283576'])
        twilio_client = client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        twilio_client.messages.create(body='i can do the texting', to='+923465283576',
                                      from_='+19844597474',
                                      # media_url=['https://demo.twilio.com/owl.png'])
                                      )
        return generic_response("Success", http_status=200)
    except Exception as e:
        traceback.print_exc()
        return generic_response("Failed", http_status=400)


# @api_view(['GET'])
# def process_logistics_truck_data(request):
def process_logistics_truck_data(request=None):
    try:
        # sleep(1)
        trucks = Devices.objects.filter(device__type_id__in=[DeviceTypeEntityEnum.TRUCK, DeviceTypeEntityEnum.VESSEL])
        for item in trucks:
            try:
                send_email = True
                last_lat = None
                last_lng = None
                last_vol = None
                last_temp = None
                try:
                    notification = DeviceViolation.objects.get(device=item.device,
                                                               violation_type=IOFOptionsEnum.FILLUPTHRESHOLD)
                except Exception as e:
                    notification = None
                    traceback.format_exc()
                try:
                    if item.device.volume_capacity:
                        volume_capacity = item.device.volume_capacity
                    else:
                        volume_capacity = None
                except Exception as e:
                    volume_capacity = None
                    traceback.format_exc()
                try:
                    aggregation = LogisticAggregations.objects.get(device=item.device)
                except Exception as e:
                    aggregation = None
                    pass
                try:
                    truck_trip = TruckTrips.objects.get(device=item.device, trip_end_timestamp__isnull=True)
                except Exception as e:
                    truck_trip = None
                    traceback.format_exc()
                try:
                    first_truck = HypernetPostData.objects.get(device=item.device, timestamp=item.timestamp)
                except Exception as e:
                    first_truck = None
                queryset = HypernetPreData.objects.filter(device=item.device).order_by('timestamp')
                for pre_data in queryset:
                    if HypernetPostData.objects.filter(device=pre_data.device, timestamp=pre_data.timestamp).exists():
                        pre_data.delete()
                        continue
                    else:
                        post = HypernetPostData()
                        post.device = pre_data.device
                        post.customer = pre_data.customer
                        post.module = pre_data.module
                        post.type = pre_data.type

                        post.temperature = pre_data.temperature
                        post.raw_temperature = pre_data.temperature
                        post.volume = pre_data.volume
                        post.raw_volume = pre_data.volume
                        post.density = pre_data.density
                        post.latitude = pre_data.latitude
                        post.longitude = pre_data.longitude
                        post.speed = pre_data.speed
                        post.trip = pre_data.trip
                        post.harsh_braking = pre_data.harsh_braking
                        post.harsh_acceleration = pre_data.harsh_acceleration
                        post.validity = pre_data.validity
                        post.accelerometer_1 = pre_data.accelerometer_1
                        post.accelerometer_2 = pre_data.accelerometer_2
                        post.volume_consumed = 0
                        post.distance_travelled = 0
                        post.gyro_1 = pre_data.gyro_1
                        post.gyro_2 = pre_data.gyro_2
                        post.gyro_3 = pre_data.gyro_3
                        post.timestamp = pre_data.timestamp

                        if pre_data.speed is None:
                            post.speed = 0
                        if pre_data.density is None:
                            post.density = 0
                        if truck_trip:
                            if post.trip == 0:
                                truck_trip.trip_end_timestamp = pre_data.timestamp
                                truck_trip.trip_end_lat_long = pre_data.latitude + "," + pre_data.longitude
                                truck_trip.trip_duration = truck_trip.trip_start_timestamp - truck_trip.trip_end_timestamp
                                truck_trip.save()
                        else:
                            if post.trip == 1:
                                truck_trip = TruckTrips()
                                truck_trip.customer = post.customer
                                truck_trip.module = post.module
                                truck_trip.on_job = Assignment.objects.filter(parent=post.device,
                                                                              child__type_id=DeviceTypeEntityEnum.JOB).exists()
                                if truck_trip.on_job == True:
                                    try:
                                        truck_trip.job = Assignment.objects.get(parent=post.device,
                                                                                status_id=OptionsEnum.ACTIVE,
                                                                                child__type_id=DeviceTypeEntityEnum.JOB).child
                                    except:
                                        truck_trip.job = None
                                        traceback.format_exc()
                                try:
                                    truck_trip.driver = Assignment.objects.get(parent=post.device,
                                                                               status_id=OptionsEnum.ACTIVE,
                                                                               child__type_id=DeviceTypeEntityEnum.DRIVER).child
                                except:
                                    truck_trip.driver = None
                                    traceback.format_exc()
                                truck_trip.trip_start_timestamp = post.timestamp
                                truck_trip.timestamp = post.timestamp
                                truck_trip.trip_start_lat_long = post.latitude + "," + post.longitude
                                truck_trip.save()
                        if last_lat is None and last_lng is None and last_vol is None:
                            if first_truck:
                                post, last_lat, last_lng = process_location_data(pre_data.latitude, pre_data.longitude,
                                                                                 first_truck.latitude,
                                                                                 first_truck.longitude, post)
                                if notification:
                                    last_vol, post = process_volume_data(notification.threshold_number, pre_data, post,
                                                                         first_truck.volume, first_truck.temperature,
                                                                         volume_capacity, aggregation)
                                else:
                                    last_vol, post = process_volume_data(5, pre_data, post, first_truck.volume,
                                                                         first_truck.temperature, volume_capacity,
                                                                         aggregation)
                                post.save()
                                pre_data.delete()
                            else:
                                post.save()
                                last_lat = pre_data.latitude
                                last_lng = pre_data.longitude
                                last_vol = pre_data.volume
                                last_temp = pre_data.temperature
                                pre_data.delete()
                        else:
                            post, last_lat, last_lng = process_location_data(pre_data.latitude, pre_data.longitude,
                                                                             last_lat,
                                                                             last_lng, post)

                            if notification:
                                last_vol, post = process_volume_data(notification.threshold_number, pre_data, post,
                                                                     last_vol, last_temp, volume_capacity, aggregation)
                            else:
                                last_vol, post = process_volume_data(5, pre_data, post, last_vol, last_temp,
                                                                     volume_capacity, aggregation)
                            post.save()
                            pre_data.delete()

                        # Check for trips on truck
                        update_trip_status_of_vehicle(item.device, pre_data.latitude, pre_data.longitude)
                        Devices.objects.update_or_create(device=pre_data.device,
                                                         defaults={'timestamp': pre_data.timestamp}, )
            except Exception as e:
                traceback.print_exc()
        print('Job completed at: ' + str(timezone.now()))
        # return generic_response("Success", http_status=200)
    except Exception as e:
        traceback.format_exc()
        traceback.print_exc()
        # return generic_response("Failed", http_status=400)


# @api_view(['GET'])
# def logistics_truck_aggregation(request):
def logistics_truck_aggregation(request=None):
    try:
        trucks = Devices.objects.filter(device__type_id__in=[DeviceTypeEntityEnum.TRUCK, DeviceTypeEntityEnum.VESSEL])
        for t in trucks:
            # sleep(1)
            date_now = timezone.now()
            if t.id in constants.demo_trucks:
                e_list = email_list
            else:
                e_list = constants.secondary_email_list
            try:
                aggregation = LogisticAggregations.objects.get(device=t.device)
                if (date_now - t.timestamp).total_seconds() / 60 > 20 and aggregation.online_status:
                    aggregation.online_status = False
                    # status.save()
                    send_mail('Staging Device Offline',
                              'Device is offline id: ' + t.device.name + ' since: ' + str(t.timestamp) + ' at: ' + str(
                                  date_now),
                              'support@hypernymbiz.com',
                              e_list, fail_silently=True)
            except Exception as e:
                aggregation = LogisticAggregations()
                if (date_now - t.timestamp).total_seconds() / 60 < 20:  # This will run only one time
                    aggregation.online_status = True
            try:
                date_from = date_now - date_time.timedelta(days=1)
                aggregation.tdist_last24Hrs = get_generic_distance_travelled(t.device.customer.id, t.device.id, None,
                                                                             None, date_from, date_now)
                aggregation.tvol_last24Hrs = get_generic_volume_consumed(t.device.customer.id, t.device.id, None, None,
                                                                         date_from, date_now)
                if aggregation.timestamp:
                    aggregation.total_distance += get_generic_distance_travelled(t.device.customer.id, t.device.id,
                                                                                 None, None, aggregation.timestamp,
                                                                                 date_now)
                    aggregation.total_volume_consumed += get_generic_volume_consumed(t.device.customer.id, t.device.id,
                                                                                     None, None, aggregation.timestamp,
                                                                                     date_now)
                    # To be fixed with migrations and review query calls - FIXED WALEED
                    aggregation.total_jobs_completed += get_generic_jobs(t.device.customer.id, t.device.id, None, None,
                                                                         None, IOFOptionsEnum.COMPLETED, None,
                                                                         aggregation.timestamp, date_now).count()
                    # aggregation.total_jobs_completed = 0
                    aggregation.total_fillups += len(
                        get_generic_fillups(t.device.customer.id, t.device.id, None, None, aggregation.timestamp,
                                            date_now))
                    aggregation.total_maintenances += get_generic_maintenances(t.device.customer.id, t.device.id, None,
                                                                               None, aggregation.timestamp,
                                                                               date_now).count()
                    aggregation.total_trips += get_generic_trips(t.device.customer.id, t.device.id, None, None,
                                                                 aggregation.timestamp, date_now).count()
                    aggregation.total_violations += get_generic_violations(t.device.customer.id, t.device.id, None,
                                                                           None, None, None, aggregation.timestamp,
                                                                           date_now).count()

                else:  # Only runs in case Aggregation object did not exist in the database
                    aggregation.device = t.device
                    aggregation.customer = t.device.customer
                    aggregation.module = t.device.module
                    aggregation.total_distance = get_generic_distance_travelled(t.device.customer.id, t.device.id, None,
                                                                                None, None, None)
                    aggregation.total_volume_consumed = get_generic_volume_consumed(t.device.customer.id, t.device.id,
                                                                                    None, None, None, None)
                    # To be fixed with migrations and review query calls - FIXED WALEED
                    aggregation.total_jobs_completed = get_generic_jobs(t.device.customer.id, t.device.id, None, None,
                                                                        None, IOFOptionsEnum.COMPLETED, None, None,
                                                                        None).count()
                    # aggregation.total_jobs_completed = 0
                    aggregation.total_fillups = len(
                        get_generic_fillups(t.device.customer.id, t.device.id, None, None, None, None))
                    aggregation.total_maintenances = get_generic_maintenances(t.device.customer.id, t.device.id, None,
                                                                              None, None, None).count()
                    aggregation.total_trips = get_generic_trips(t.device.customer.id, t.device.id, None, None, None,
                                                                None).count()
                    aggregation.total_violations = get_generic_violations(t.device.customer.id, t.device.id, None, None,
                                                                          None, None, None, None).count()
                aggregation.timestamp = date_now
                aggregation.last_updated = t.timestamp
                aggregation.save()
            except Exception as e:
                traceback.print_exc()
            try:
                last_message = HypernetPostData.objects.get(device=t.device, timestamp=t.timestamp)
                aggregation.last_volume = last_message.volume
                aggregation.last_density = last_message.density
                aggregation.last_temperature = last_message.temperature
                aggregation.last_latitude = last_message.latitude
                aggregation.last_longitude = last_message.longitude
                aggregation.last_speed = last_message.speed
                aggregation.save()
            except Exception as e:
                traceback.print_exc()
        print('Job completed at: ' + str(date_time.datetime.now()))

    except Exception as e:
        traceback.print_exc()


def process_queued_data_truck():
    try:
        trucks = Devices.objects.filter(device__type_id=DeviceTypeEntityEnum.TRUCK)
        for item in trucks:
            try:
                last_lat = None
                last_lng = None
                last_vol = None

                date_now = timezone.now()
                date_from = date_now - date_time.timedelta(days=1)
                try:
                    notification = DeviceViolation.objects.get(device=item.device,
                                                               violation_type=IOFOptionsEnum.FILLUPTHRESHOLD)
                except Exception as e:
                    notification = None
                    traceback.format_exc()
                try:
                    calibration = DeviceCalibration.objects.get(device=item.device)
                    calibration.calibration = json.loads(calibration.calibration)
                except Exception as e:
                    calibration = None
                    traceback.format_exc()
                try:
                    aggregation = LogisticAggregations.objects.get(device=item.device)
                except Exception as e:
                    aggregation = None
                    pass
                queryset = HypernetPostData.objects.filter(device=item.device,
                                                           timestamp__range=[date_from, date_now]).order_by('timestamp')
                for post in queryset:
                    if last_lat and last_lng:
                        post, last_lat, last_lng = process_location_data(post.latitude, post.longitude,
                                                                         last_lat,
                                                                         last_lng, post)
                    else:
                        last_lat = post.latitude
                        last_lng = post.longitude
                    if last_vol:
                        if notification:
                            last_vol, post = process_volume_data(notification.threshold_number, post, post, last_vol,
                                                                 calibration, aggregation)
                        else:
                            last_vol, post = process_volume_data(5, post, post, last_vol, calibration, aggregation)
                    else:
                        last_vol = post.volume
                    post.save()


            except Exception as e:
                traceback.format_exc()
                traceback.print_exc()
        print('Job completed at: ' + str(date_time.datetime.now()))
        # return generic_response("Success", http_status=200)
    except Exception as e:
        traceback.format_exc()
        traceback.print_exc()
        # return generic_response("Failed", http_status=400)


# @api_view(['GET'])
# def process_logistics_bin_data(request):
def process_logistics_bin_data():
    try:
        bins = Devices.objects.filter(device__type_id=DeviceTypeEntityEnum.BIN)
        for item in bins:
            last_vol = None
            try:
                notification = DeviceViolation.objects.get(device=item.device,
                                                           violation_type=IOFOptionsEnum.FILLUPTHRESHOLD)
            except Exception as e:
                notification = None
                pass
            try:
                first_bin = HypernetPostData.objects.get(device=item.device, timestamp=item.timestamp)
            except Exception as e:
                first_bin = None
                pass
            try:
                aggregation = LogisticAggregations.objects.get(device=item.device)
            except Exception as e:
                aggregation = None
                pass
            queryset = HypernetPreData.objects.filter(device=item.device).order_by('timestamp')
            for pre_data in queryset:
                post = HypernetPostData()
                post.device = pre_data.device
                post.customer = pre_data.customer
                post.module = pre_data.module
                post.type = pre_data.type
                post.volume = pre_data.volume
                post.latitude = pre_data.latitude
                post.longitude = pre_data.longitude
                post.timestamp = pre_data.timestamp

                if last_vol is None:
                    if first_bin:
                        if notification:
                            if first_bin.volume - pre_data.volume >= notification.threshold_number:
                                fill = LogisticsDerived()
                                fill.device = pre_data.device
                                fill.customer = pre_data.customer
                                fill.module = pre_data.module
                                fill.latitude = pre_data.latitude
                                fill.longitude = pre_data.longitude
                                fill.pre_dec_vol = first_bin.volume
                                fill.post_dec_vol = pre_data.volume
                                fill.timestamp = pre_data.timestamp
                                fill.save()
                                if aggregation:
                                    aggregation.last_decantation = pre_data.timestamp
                                    aggregation.save()
                        else:
                            if first_bin.volume - pre_data.volume >= 50:
                                fill = LogisticsDerived()
                                fill.device = pre_data.device
                                fill.customer = pre_data.customer
                                fill.module = pre_data.module
                                fill.latitude = pre_data.latitude
                                fill.longitude = pre_data.longitude
                                fill.pre_dec_vol = first_bin.volume
                                fill.post_dec_vol = pre_data.volume
                                fill.timestamp = pre_data.timestamp
                                fill.save()
                                if aggregation:
                                    aggregation.last_decantation = pre_data.timestamp
                                    aggregation.save()
                        post.save()
                        last_vol = pre_data.volume
                        pre_data.delete()
                    else:
                        post.save()
                        last_vol = pre_data.volume
                        pre_data.delete()
                else:
                    if notification:
                        if last_vol - pre_data.volume >= notification.threshold_number:
                            fill = LogisticsDerived()
                            fill.device = pre_data.device
                            fill.customer = pre_data.customer
                            fill.module = pre_data.module
                            fill.latitude = pre_data.latitude
                            fill.longitude = pre_data.longitude
                            fill.pre_dec_vol = last_vol
                            fill.post_dec_vol = pre_data.volume
                            fill.timestamp = pre_data.timestamp
                            fill.save()
                            if aggregation:
                                aggregation.last_decantation = pre_data.timestamp
                                aggregation.save()
                    else:
                        if last_vol - pre_data.volume >= 50:
                            fill = LogisticsDerived()
                            fill.device = pre_data.device
                            fill.customer = pre_data.customer
                            fill.module = pre_data.module
                            fill.latitude = pre_data.latitude
                            fill.longitude = pre_data.longitude
                            fill.pre_dec_vol = last_vol
                            fill.post_dec_vol = pre_data.volume
                            fill.timestamp = pre_data.timestamp
                            fill.save()
                            if aggregation:
                                aggregation.last_decantation = pre_data.timestamp
                                aggregation.save()
                    post.save()
                    last_vol = pre_data.volume
                    pre_data.delete()
                Devices.objects.update_or_create(device=pre_data.device, defaults={'timestamp': pre_data.timestamp}, )
        print('Job completed at: ' + str(date_time.datetime.now()))
        # return generic_response("Success", http_status=200)
    except Exception as e:
        traceback.format_exc()


# @api_view(['GET'])
# def logistics_bin_aggregation(request):
def logistics_bin_aggregation():
    try:
        bins = Devices.objects.filter(device__type_id=DeviceTypeEntityEnum.BIN)
        for b in bins:
            date_now = timezone.now()
            try:
                aggregation = LogisticAggregations.objects.get(device=b.device)
                if (date_now - b.timestamp).total_seconds() / 60 > 35 and aggregation.online_status:
                    send_mail('Staging Device Offline',
                              'Device is offline id: ' + b.device.name + ' since: ' + str(b.timestamp),
                              'support@hypernymbiz.com',
                              email_list, fail_silently=True)
                    aggregation.online_status = False
                if (date_now - b.timestamp).total_seconds() / 60 < 35 and not aggregation.online_status:
                    aggregation.online_status = True
            except Exception as e:
                aggregation = LogisticAggregations()
                if (date_now - b.timestamp).total_seconds() / 60 < 35:
                    aggregation.online_status = True
                else:
                    aggregation.online_status = False

            # No tdist_last24Hrs in case of bins
            try:

                if aggregation.timestamp:
                    # To be fixed with migrations and review query calls - FIXED WALEED
                    aggregation.total_jobs_completed += get_generic_jobs(b.device.customer.id, b.device.id, None, None,
                                                                         None, None, None,
                                                                         aggregation.timestamp, date_now).count()
                    # aggregation.total_jobs_completed = 0
                    aggregation.total_decantations += len(
                        get_generic_decantation(b.device.customer.id, b.device.id, None, None, aggregation.timestamp,
                                                date_now))
                    aggregation.total_maintenances += get_generic_maintenances(b.device.customer.id, b.device.id, None,
                                                                               None,
                                                                               aggregation.timestamp, date_now).count()

                    aggregation.total_violations += get_generic_violations(b.device.customer.id, b.device.id, None,
                                                                           None, None, None,
                                                                           aggregation.timestamp, date_now).count()

                else:
                    aggregation.device = b.device
                    aggregation.customer = b.device.customer
                    aggregation.module = b.device.module
                    # To be fixed with migrations and review query calls - FIXED WALEED
                    aggregation.total_jobs_completed = get_generic_jobs(b.device.customer.id, b.device.id, None, None,
                                                                        None, None,
                                                                        None, None, None).count()
                    # aggregation.total_jobs_completed = 0
                    aggregation.total_decantations = len(
                        get_generic_decantation(b.device.customer.id, b.device.id, None, None, None, None))
                    aggregation.total_maintenances = get_generic_maintenances(b.device.customer.id, b.device.id, None,
                                                                              None, None,
                                                                              None).count()
                    aggregation.total_violations = get_generic_violations(b.device.customer.id, b.device.id, None, None,
                                                                          None,
                                                                          None, None, None).count()
                aggregation.timestamp = date_now
                aggregation.last_updated = b.timestamp
                aggregation.save()
            except Exception as e:
                traceback.print_exc()

            try:
                last_message = HypernetPostData.objects.get(device=b.device, timestamp=b.timestamp)
                aggregation.last_volume = last_message.volume
                aggregation.last_latitude = last_message.latitude
                aggregation.last_longitude = last_message.longitude
                aggregation.last_speed = last_message.speed
                aggregation.last_temperature = last_message.temperature
                aggregation.save()
            except Exception as e:
                traceback.print_exc()
        print('Job completed at: ' + str(date_time.datetime.now()))
    except Exception as e:
        traceback.print_exc()



        # return generic_response("Failed", http_status=400)


# @api_view(['GET'])
# def process_logistics_bin_data(request):
# FIXME
# def process_logistics_vessel_data():
#     try:
#         vessels = Devices.objects.filter(device__type_id=DeviceTypeEntityEnum.VESSEL)
#         for item in vessels:
#             queryset = HypernetPreData.objects.filter(device=item.device).order_by('timestamp')
#             for pre_data in queryset:
#                 post = HypernetPostData()
#                 post.device = pre_data.device
#                 post.customer = pre_data.customer
#                 post.module = pre_data.module
#                 post.type = pre_data.type
#                 post.volume = pre_data.volume
#                 post.timestamp = pre_data.timestamp
#                 post.save()
#                 pre_data.delete()
#                 Devices.objects.update_or_create(device=pre_data.device, defaults={'timestamp': pre_data.timestamp}, )
#         print('Job completed at: ' + str(date_time.datetime.now()))
#         # return generic_response("Success", http_status=200)
#     except Exception as e:
#         traceback.format_exc()



def process_volume_data(threshold, pre_data, post, last_vol, last_temp, volume_capacity, aggregation):
    try:
        send_email = False
        if pre_data.volume:
            if (pre_data.volume == 1 and pre_data.temperature == 1) or pre_data.volume > 100 or pre_data.volume < 0:
                post.volume = last_vol
                post.temperature = last_temp
                return last_vol, post
            # if pre_data.volume - last_vol <= threshold and pre_data.volume - last_vol >= 0 and \
            #                 pre_data.type.id == DeviceTypeEntityEnum.TRUCK:  #TODO: To be fixed later
            #     post.volume = last_vol
            #     post.volume_consumed = 0
            #     pre_data.volume = last_vol
            if pre_data.volume - last_vol >= threshold and post.speed <= 1:
                try:
                    fill = LogisticsDerived.objects.get(device=pre_data.device, timestamp=pre_data.timestamp)
                except:
                    fill = LogisticsDerived()
                    send_email = False
                fill.device = pre_data.device
                fill.customer = pre_data.customer
                fill.module = pre_data.module
                fill.latitude = pre_data.latitude
                fill.longitude = pre_data.longitude
                fill.pre_fill_vol = last_vol
                fill.post_fill_vol = pre_data.volume
                fill.temperature = pre_data.temperature
                fill.timestamp = pre_data.timestamp
                if volume_capacity:
                    fill.pre_fill_vol = float(last_vol / 100) * volume_capacity
                    fill.post_fill_vol = float(pre_data.volume / 100) * volume_capacity
                    # fill.fuel_consumed = float(fill.fuel_consumed/100) * volume_capacity

                # fillup_data = fillup_summary(fill.device, aggregation, fill.timestamp, fill.fuel_consumed)
                # if fillup_data:
                #     fill.distance_travelled = fillup_data['distance']
                #     fill.fuel_avg = fillup_data['fuel_avg']
                fill.save()
                if send_email:
                    if volume_capacity:  # Temporary Fix. To be fixed later
                        send_mail('Staging Truck Fillup',
                                  'Truck: ' + pre_data.device.name + ' filled at: ' + str(
                                      pre_data.timestamp) + '. Location: https://www.google.com/maps/search/?api=1&query=' + str(
                                      pre_data.latitude) + ',' + str(pre_data.longitude) +
                                  '. Volume filled: ' + str(
                                      float((pre_data.volume - last_vol / 100)) * volume_capacity),
                                  'support@hypernymbiz.com',
                                  email_list, fail_silently=True)
                        # else:
                        #     send_mail('Staging Truck Fillup',
                        #               'Truck: ' + pre_data.device.name + ' filled at: ' + str(
                        #                   pre_data.timestamp) + '. Location: https://www.google.com/maps/search/?api=1&query=' + str(
                        #                   pre_data.latitude) + ',' + str(pre_data.longitude) +
                        #               '. Volume filled: ' + str(pre_data.volume-last_vol),
                        #               'support@hypernymbiz.com',
                        #               email_list, fail_silently=True)
                if aggregation:
                    aggregation.last_fillup = pre_data.timestamp
                    aggregation.save()
                last_vol = pre_data.volume
            elif last_vol - pre_data.volume >= threshold and pre_data.type.id == DeviceTypeEntityEnum.TRUCK:  # TODO: To be fixed later
                if volume_capacity:
                    post.volume_consumed = float((last_vol - pre_data.volume / 100)) * volume_capacity
                else:
                    post.volume_consumed = last_vol - pre_data.volume
                last_vol = pre_data.volume

            elif pre_data.volume - last_vol <= threshold:
                post.volume = last_vol
                post.volume_consumed = 0

            if pre_data.type.id == DeviceTypeEntityEnum.VESSEL:
                # Conversion to liters for better accuracy and decant detection.
                # pre_vol_vessel = float(last_vol/100) * volume_capacity
                # post_vol_vessel = float(pre_data.volume/100) * volume_capacity
                if last_vol - pre_data.volume >= 0.007:  # TODO: To be fixed later. Only for vessel
                    create_decant_derived_data(pre_data, last_vol, pre_data.volume)
                    post.volume_consumed = last_vol - pre_data.volume
                    if aggregation:
                        aggregation.last_decantation = pre_data.timestamp
                        aggregation.save()
                    last_vol = pre_data.volume
        else:
            post.volume = last_vol
            post.temperature = last_temp
            post.volume_consumed = 0
        return last_vol, post
    except Exception as e:
        traceback.print_exc()


# def process_location_data(current_lat, current_lng, last_lat, last_lng, post):
#     try:

#         if current_lat and current_lng:
#             post.latitude = current_lat
#             post.longitude = current_lng
#         else:
#             post.latitude = last_lat
#             post.longitude = last_lng
#             current_lat = last_lat
#             current_lng = last_lng

#         post.distance_travelled = vincenty((current_lat, current_lng), (last_lat, last_lng)).meters
#         if post.distance_travelled <= 200:
#             post.distance_travelled = 0
#             post.latitude = last_lat
#             post.longitude = last_lng
#         else:
#             last_lat = current_lat
#             last_lng = current_lng

#         return post, last_lat, last_lng
#     except Exception as e:
#         traceback.print_exc()


def process_location_data_ffp(current_lat, current_lng, last_lat, last_lng, post):
    try:

        if current_lat and current_lng:
            post.latitude = current_lat
            post.longitude = current_lng
        else:
            post.latitude = last_lat
            post.longitude = last_lng
            current_lat = last_lat
            current_lng = last_lng
        post.distance_travelled = vincenty((current_lat, current_lng), (last_lat, last_lng)).meters
        if post.distance_travelled <= 20:
            post.distance_travelled = 0
            post.latitude = last_lat
            post.longitude = last_lng
        else:
            last_lat = current_lat
            last_lng = current_lng
        return post, last_lat, last_lng
    except Exception as e:
        traceback.print_exc()


# @api_view(['GET'])
# def save_logistic_notification(request):
def save_logistic_notification():
    date_now = timezone.now()
    time_threshold_job = date_now + timezone.timedelta(minutes=constants.LAST_HOUR)
    time_threshold_maintenance = date_now + timezone.timedelta(minutes=constants.LAST_24_HOUR)
    try:
        ent = Entity.objects.filter(speed=False,
                                    type_id__in=[DeviceTypeEntityEnum.JOB, DeviceTypeEntityEnum.MAINTENANCE])
        for obj in ent:
            if obj.type.id == DeviceTypeEntityEnum.JOB and obj.job_status_id == IOFOptionsEnum.ACCEPTED and date_now <= obj.job_start_datetime <= time_threshold_job:

                try:
                    assigned_truck = Assignment.objects.get(child_id=obj.id,
                                                            child__type=DeviceTypeEntityEnum.JOB,
                                                            parent__type=DeviceTypeEntityEnum.TRUCK,
                                                            status=OptionsEnum.ACTIVE).parent_id

                    assigned_driver = Assignment.objects.get(parent_id=assigned_truck,
                                                             parent__type=DeviceTypeEntityEnum.TRUCK,
                                                             child__type=DeviceTypeEntityEnum.DRIVER,
                                                             status=OptionsEnum.ACTIVE).child_id

                    send_notification_to_user(assigned_truck, assigned_driver, obj,
                                              [User.objects.get(associated_entity=assigned_driver)],
                                              "There is an upcoming job")
                    obj.speed = True
                    obj.save()
                    print("Notification saved at" + str(date_time.datetime.now()))
                    # return generic_response("Success", http_status=200)
                except Exception as e:
                    pass

            elif obj.type.id == DeviceTypeEntityEnum.MAINTENANCE:
                td = obj.end_datetime.date() - date_now.date()
                tdd = td / timedelta(days=1)  # Checking difference of days b/w maintenance due date and current date.
                if tdd == 1.0:
                    try:
                        assigned_truck = Assignment.objects.get(child_id=obj.id,
                                                                child__type=DeviceTypeEntityEnum.MAINTENANCE,
                                                                parent__type=DeviceTypeEntityEnum.TRUCK,
                                                                status=OptionsEnum.ACTIVE).parent_id

                        assigned_driver = Assignment.objects.get(parent_id=assigned_truck,
                                                                 parent__type=DeviceTypeEntityEnum.TRUCK,
                                                                 child__type=DeviceTypeEntityEnum.DRIVER,
                                                                 status=OptionsEnum.ACTIVE).child_id
                        send_notification_to_user(assigned_truck, assigned_driver, obj,
                                                  [User.objects.get(associated_entity=assigned_driver)],
                                                  "Upcoming Maintenance")
                        obj.speed = True
                        obj.save()
                        print("Notification saved at" + str(date_time.datetime.now()))
                        # return generic_response("Success", http_status=200)
                    except Exception as e:
                        traceback.print_exc()
                        pass
                else:
                    print("Maitenance not in schedule")
                    # return generic_response("Success", http_status=200)
    except Exception as e:
        traceback.print_exc()


def process_logistics_ffp_data(request=None):
    try:
        last_lat = None
        last_lng = None

        workers = Devices.objects.filter(device__type_id=DeviceTypeEntityEnum.EMPLOYEE)

        for worker in workers:
            try:
                first_entity = HypernetPostData.objects.get(device=worker.device, timestamp=worker.timestamp)
            except Exception as e:
                first_entity = None
            queryset = HypernetPreData.objects.filter(device=worker.device).order_by('timestamp')
            chunk_size = queryset.count()
            steps = 0
            heart_rate = 0

            for pre_data in queryset:
                post = HypernetPostData()
                post.device = pre_data.device
                post.customer = pre_data.customer
                post.module = pre_data.module
                post.type = pre_data.type
                post.timestamp = pre_data.timestamp

                post.heartrate_value = pre_data.heartrate_value
                post.accelerometer_1 = pre_data.accelerometer_1
                post.accelerometer_2 = pre_data.accelerometer_2
                post.accelerometer_3 = pre_data.accelerometer_3
                post.gyro_1 = pre_data.gyro_1
                post.gyro_2 = pre_data.gyro_2
                post.gyro_3 = pre_data.gyro_3
                post.latitude = pre_data.latitude
                post.longitude = pre_data.longitude
                post.ambient_temperature = pre_data.ambient_temperature
                post.temperature = pre_data.temperature
                post.active_score = pre_data.active_score
                post.inactive_score = pre_data.inactive_score
                post.duration = pre_data.duration
                # post.trip = pre_data.trip
                if last_lat is None and last_lng is None:
                    if first_entity:
                        post, last_lat, last_lng = process_location_data_ffp(pre_data.latitude, pre_data.longitude,
                                                                             first_entity.latitude,
                                                                             first_entity.longitude,
                                                                             post)
                    else:
                        last_lat = pre_data.latitude
                        last_lng = pre_data.longitude
                else:
                    post, last_lat, last_lng = process_location_data_ffp(pre_data.latitude, pre_data.longitude,
                                                                         last_lat,
                                                                         last_lng, post)

                if not pre_data.duration:
                    pre_data.duration = 0
                if not pre_data.heartrate_value:
                    pre_data.heartrate_value = 0

                steps += pre_data.duration
                heart_rate += pre_data.heartrate_value

                if HypernetPreData.objects.filter(device=worker.device).count() == 1:
                    avg_heart_rate = heart_rate / chunk_size
                    if avg_heart_rate >= constants.AVERAGE_HEART_RATE:
                        post.trip = True
                    elif steps > 50:
                        post.trip = True
                    else:
                        post.trip = False
                else:
                    post.trip = None
                post.save()
                pre_data.delete()
        print('Job completed at: ' + str(date_time.datetime.now()))
    except Exception as e:
        print(e)
        traceback.print_exc()


# @api_view(['GET'])
# def check_maintenance_overdue(request):
def check_maintenance_overdue():
    try:
        maintenance = Entity.objects.filter(type_id=DeviceTypeEntityEnum.MAINTENANCE,
                                            job_status_id=IOFOptionsEnum.MAINTENANCE_DUE, status=OptionsEnum.ACTIVE)
        for obj in maintenance:
            threshold = timezone.now().date() - obj.end_datetime.date()  # Checking difference of days b/w current date and maintenance due date.
            buffer = threshold / timedelta(days=1)
            if buffer >= 1.0:
                obj.job_status = Options.objects.get(id=IOFOptionsEnum.MAINTENANCE_OVER_DUE)
                obj.save()
                try:
                    assigned_truck = Assignment.objects.get(child_id=obj.id,
                                                            child__type=DeviceTypeEntityEnum.MAINTENANCE,
                                                            parent__type=DeviceTypeEntityEnum.TRUCK).parent_id

                    assigned_driver = Assignment.objects.get(parent_id=assigned_truck,
                                                             child__type=DeviceTypeEntityEnum.DRIVER,
                                                             parent__type=DeviceTypeEntityEnum.TRUCK).child_id

                    over_due_maintenance = ActivityData(
                        device_id=obj.id,
                        customer_id=obj.customer_id,
                        module_id=obj.module_id,
                        entity_id=assigned_truck,
                        person_id=assigned_driver,
                        job_start_timestamp=obj.end_datetime,
                        job_end_timestamp=obj.end_datetime,
                        job_status=Options.objects.get(id=IOFOptionsEnum.MAINTENANCE_OVER_DUE),
                        maintenance_type=obj.maintenance_type
                    )
                    over_due_maintenance.save()

                    send_notification_to_user(assigned_truck, assigned_driver, obj,
                                              [User.objects.get(associated_entity=assigned_driver)],
                                              "Maintenance is now overdue")
                    obj.speed = True
                    obj.save()
                    print("Maintenance" + str(obj.name) + "is over-due")


                except Exception as e:
                    traceback.print_exc()
                    # return generic_response("Fail", http_status=500)
            else:
                print("maintenance not over-due")
                # return generic_response("Fail", http_status=500)
                # return generic_response("Success", http_status=200)
    except Exception as e:
        traceback.print_exc()
        # return generic_response("Fail", http_status=500)


@api_view(['GET'])
@csrf_exempt
def schedule_activity(request):
    activities = ActivityQueue.objects.filter(
        activity_datetime__date__range=[date.today(), date.today() + timedelta(days=1)])
    if activities:
        for obj in activities:
            try:
                Activity.objects.get(
                    activity_status_id__in=[IOFOptionsEnum.RUNNING, IOFOptionsEnum.PENDING, IOFOptionsEnum.ACCEPTED],
                    activity__primary_entity=obj.primary_entity)

                print("Activity already pending or running for truck" + str(obj.primary_entity.id))

            except:
                current_hour = timedelta(hours=timezone.now().hour)
                activity_hour = timedelta(hours=obj.activity.job_start_time.hour)

                t1 = timedelta(hours=timezone.now().hour, minutes=timezone.now().minute,
                               seconds=timezone.now().second)

                t2 = timedelta(hours=obj.activity.job_start_time.hour,
                               minutes=obj.activity.job_start_time.minute,
                               seconds=obj.activity.job_start_time.second)

                buffer = (t2 - t1).seconds
                # buffer = (obj.activity.job_start_time - dt)
                buffer = round(buffer / 60, 0)

                if buffer <= constants.LAST_THIRTY_MINUTES and buffer >= 0:  # this will be checked once User prefrences are added.
                    # Right now only checking if it lies in 30 minutes buffer

                    # Check from user prefrences if he has enabled accept or reject feature. If not then an Acitivity entry will be created
                    # with Accepted status and no notifcation will be sent. If enabled then the below scenario will follow.

                    if obj.activity.enable_accept_reject is True:

                        try:
                            assigned_driver = Assignment.objects.get(child__type_id=DeviceTypeEntityEnum.DRIVER,
                                                                     parent=obj.activity.primary_entity,
                                                                     status_id=OptionsEnum.ACTIVE).child
                            activity = util_create_activity(obj, assigned_driver, IOFOptionsEnum.PENDING,
                                                            obj.activity_datetime)
                            try:
                                activity.save()
                                util_save_activity_notification(obj, activity,
                                                                [User.objects.get(associated_entity=assigned_driver)],
                                                                "Accept or reject this activity")

                                ActivityQueue.objects.get(id=obj.id).delete()
                            except Exception as e:
                                traceback.print_exc()

                        except:
                            notification = HypernetNotification(
                                device=obj.activity.primary_entity,
                                driver=None,
                                activity=None,
                                customer_id=obj.activity.customer.id,
                                module_id=obj.activity.module.id,
                                status_id=OptionsEnum.ALERT_GENERATED,
                                timestamp=timezone.now(),
                                description="Activity",
                                title="No driver has been assigned to this truck."
                            )
                            notification.save()
                            for user in [User.objects.get(id=obj.activity.user.id)]:
                                gn = NotificationGroups(notification=notification,
                                                        user=user)
                                gn.save()
                            notification.save()

                    else:
                        try:
                            assigned_driver = Assignment.objects.get(child__type_id=DeviceTypeEntityEnum.DRIVER,
                                                                     parent=obj.activity.primary_entity,
                                                                     status_id=OptionsEnum.ACTIVE).child
                            activity = util_create_activity(obj, assigned_driver, IOFOptionsEnum.ACCEPTED,
                                                            obj.activity_datetime)
                            try:
                                activity.save()
                                ActivityQueue.objects.get(id=obj.id).delete()
                            except Exception as e:
                                traceback.print_exc()
                        except:
                            notification = HypernetNotification(
                                device=obj.activity.primary_entity,
                                driver=None,
                                activity=None,
                                customer_id=obj.activity.customer.id,
                                module_id=obj.activity.module.id,
                                status_id=OptionsEnum.ALERT_GENERATED,
                                timestamp=timezone.now(),
                                description="Activity",
                                title="No driver has been assigned to this truck."
                            )
                            notification.save()
                            for user in [User.objects.get(id=obj.activity.user.id)]:
                                gn = NotificationGroups(notification=notification,
                                                        user=user)
                                gn.save()
                            notification.save()
                            # else:
                            #    print("No activity in schedule")

        return generic_response("Success", http_status=200)
    else:
        print("No activity in schedule")


def send_notification(request=None):
    try:
        activity = Activity.objects.filter(activity_status_id=IOFOptionsEnum.ACCEPTED, notification_sent=False)

        for obj in activity:

            prefrences = CustomerPreferences.objects.get(customer=obj.activity_schedule.customer)
            buffer = (obj.activity_start_time - timezone.now()).total_seconds()

            buffer = round(buffer / 60, 0)

            if buffer <= prefrences.activity_start_buffer:
                notification = HypernetNotification(
                    device=obj.activity_schedule.primary_entity,
                    driver_id=obj.actor_id,
                    activity_id=obj.id,
                    customer_id=obj.activity_schedule.customer.id,
                    module_id=obj.activity_schedule.module.id,
                    status_id=OptionsEnum.ACTIVE,
                    timestamp=timezone.now(),
                    description="Activity",
                    title="You have an upcoming activity",
                    type_id=IOFOptionsEnum.NOTIFICATION_DRIVER_START_ACTIVITY,
                )
                notification.save()
                for user in [User.objects.get(associated_entity=obj.actor_id)]:
                    gn = NotificationGroups(notification=notification,
                                            user=user)
                    gn.save()
                notification.save()
                obj.notification_sent = True
                obj.save()
                print("Notification sent to user.")
            else:
                print("No activity in schedule")
        # print("Notification sent")
        print('Job completed at: ' + str(date_time.datetime.now()))
        # return generic_response("Success", http_status=200)
    except Exception as e:
        traceback.print_exc()
        # return generic_response("Failure", http_status=400)


def schedule_activity2(request=None):
    clean_activity = None
    end_time = (timezone.now() + timedelta(days=7))
    activities = ActivityQueue.objects.filter(activity_datetime__gte=timezone.now(), activity_datetime__lte=end_time,
                                              activity_schedule__schedule_activity_status_id=OptionsEnum.ACTIVE,
                                              activity_schedule__isnull=False, module=ModuleEnum.IOL)
    for obj in activities:
        preferences = CustomerPreferences.objects.get(customer_id=obj.activity_schedule.customer.id)
        buffer = (obj.activity_datetime - timezone.now()).total_seconds()
        buffer = round(buffer / 60, 0)
        print("Buffer:" + str(buffer) + " Schedule id:" + str(obj.activity_schedule.id))

        # Get current activity of Truck
        try:
            current_truck = Activity.objects.get(
                activity_status_id__in=[IOFOptionsEnum.SUSPENDED, IOFOptionsEnum.RUNNING, IOFOptionsEnum.PENDING,
                                        IOFOptionsEnum.ACCEPTED, IOFOptionsEnum.REJECTED, IOFOptionsEnum.FAILED,
                                        IOFOptionsEnum.CONFLICTING],
                primary_entity=obj.primary_entity)
        except:
            current_truck = None
        # Get current activity of Driver
        try:
            current_driver = Activity.objects.get(
                activity_status_id__in=[IOFOptionsEnum.SUSPENDED, IOFOptionsEnum.RUNNING,
                                        IOFOptionsEnum.PENDING, IOFOptionsEnum.ACCEPTED,
                                        IOFOptionsEnum.REJECTED,
                                        IOFOptionsEnum.FAILED, IOFOptionsEnum.CONFLICTING],
                actor=obj.actor)
        except:
            current_driver = None

        if preferences.enable_accept_reject:
            if buffer <= preferences.activity_accept_reject_buffer:
                try:  # Current activity of truck
                    activity = util_conflict_with_time(current_truck, preferences, obj,
                                                       "Activity already running for " + obj.primary_entity.name + ". Please Review.",
                                                       IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_TRUCK_CONFLICT)
                    if not activity:
                        activity = util_conflict_with_time(current_driver, preferences, obj,
                                                           "Activity already running for " + obj.actor.name + "Please Review. ",
                                                           IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_DRIVER_CONFLICT)
                    if not activity:
                        clean_activity = util_create_activity(obj, obj.actor, IOFOptionsEnum.PENDING,
                                                              obj.activity_datetime)
                        clean_activity.save()
                except:
                    traceback.print_exc()
                if clean_activity:
                    if preferences.activity_review is True:
                        send_notification_to_admin(obj.primary_entity.id, obj.actor.id, clean_activity.id, obj,
                                                   [obj.activity_schedule.modified_by_id],
                                                   "Please review the activity for driver " + obj.actor.name,
                                                   IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW)

                    else:
                        send_notification_to_admin(obj.primary_entity.id, obj.actor.id, clean_activity.id, obj,
                                                   [User.objects.get(associated_entity=obj.actor).id],
                                                   "Accept or reject this activity",
                                                   IOFOptionsEnum.NOTIFCIATION_DRIVER_ACCEPT_REJECT)
                        # Crete bin collection data here?
                obj.delete()

        else:
            if buffer <= preferences.activity_start_buffer:
                try:
                    activity = util_conflict_with_time(current_truck, preferences, obj,
                                                       "Activity already running for " + obj.primary_entity.name + ". Please Review.",
                                                       IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_TRUCK_CONFLICT)
                    if not activity:
                        activity = util_conflict_with_time(current_driver, preferences, obj,
                                                           "Activity already running for " + obj.actor.name + "Please Review. ",
                                                           IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_DRIVER_CONFLICT)
                    if not activity:
                        if not check_bins_validity(obj):
                            if (activity.activity_schedule.end_date is None) or (
                                        activity.activity_schedule.end_date <= timezone.now().date()):
                                activity.activity_schedule.schedule_activity_status = Options.objects.get(
                                    id=OptionsEnum.INACTIVE)
                                activity.activity_schedule.save()
                            obj.delete()
                            continue
                        if not check_bins_in_act(obj, "Bins already part of activity. Please Review. ",
                                                 IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_BIN_CONFLICT):
                            obj.delete()
                            continue
                        clean_activity = util_create_activity(obj, obj.actor, IOFOptionsEnum.PENDING,
                                                              obj.activity_datetime)
                        clean_activity.save()

                except Exception as e:
                    traceback.print_exc()

                if clean_activity:
                    if preferences.activity_review:
                        send_notification_to_admin(obj.primary_entity.id, obj.actor.id, clean_activity.id, obj,
                                                   [obj.activity_schedule.modified_by_id],
                                                   "Please review the activity for driver " + obj.actor.name,
                                                   IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW)
                    else:
                        clean_activity.activity_status = Options.objects.get(id=IOFOptionsEnum.ACCEPTED)
                        clean_activity.save()
                        # Create bin collection data for bins in activity?

                obj.delete()

    # print("Success")
    print('Job completed at: ' + str(date_time.datetime.now()))
    # return generic_response("Success", http_status=200)


def remove_notifications(request=None):
    # def remove_notifications():
    ###############################################################
    try:
        accept_reject_notifications = HypernetNotification.objects.filter(
            type_id=IOFOptionsEnum.NOTIFCIATION_DRIVER_ACCEPT_REJECT, status_id=OptionsEnum.ACTIVE)
        for obj in accept_reject_notifications:
            activity = Activity.objects.get(id=obj.activity.id)
            preference = CustomerPreferences.objects.get(customer=obj.customer)

            buffer = (timezone.now() - obj.created_datetime).total_seconds()

            buffer = round(buffer / 60, 0)
            if buffer >= preference.activity_accept_driver_buffer:
                if obj.type.id == IOFOptionsEnum.NOTIFCIATION_DRIVER_ACCEPT_REJECT and (
                                obj.activity.activity_status.id == IOFOptionsEnum.PENDING or obj.activity.activity_status.id == IOFOptionsEnum.REVIEWED):  # Driver has been sent a notification of ACCEPT/REJECT but driver doesnot take any action, hence
                    # notification is sent to admin to review it IF he has enabled Review flag in prefrence.
                    send_notification_to_user(obj, activity,
                                              [User.objects.get(id=obj.activity.activity_schedule.modified_by.id)],
                                              str(
                                                  obj.activity.actor.name) + " didn't take any action. Please review this activity",
                                              IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_NO_ACTION_ACCEPT_REJECT)

                    create_activity_data_alter_activity(obj, activity, IOFOptionsEnum.REJECTED)
            else:
                print(str(buffer - timezone.now().minute) + " Minutes left to review")
        ######################################################################################
        review_notifications = HypernetNotification.objects.filter(
            type_id__in=[IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW,
                         IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_DRIVER_REJECT,
                         IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_TRUCK_CONFLICT,
                         IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_DRIVER_CONFLICT,
                         IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_BIN_CONFLICT,
                         IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_NO_ACTION_ACCEPT_REJECT,
                         IOFOptionsEnum.NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_ABORT,
                         IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_NO_ACTION_START_FAIL],
            status_id=OptionsEnum.ACTIVE)
        for obj in review_notifications:
            activity = obj.activity
            preference = CustomerPreferences.objects.get(customer=obj.customer)

            buffer = (timezone.now() - obj.created_datetime).total_seconds()

            buffer = round(buffer / 60, 0)
            if buffer >= preference.activity_review_admin_buffer:
                if obj.type.id == IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW and obj.activity.activity_status.id == IOFOptionsEnum.PENDING:
                    if preference.enable_accept_reject:
                        send_notification_to_user(obj, activity,
                                                  [User.objects.get(associated_entity=obj.activity.actor)],
                                                  "Accept or reject this activity",
                                                  IOFOptionsEnum.NOTIFCIATION_DRIVER_ACCEPT_REJECT)
                        activity.activity_status = Options.objects.get(id=IOFOptionsEnum.REVIEWED)

                    else:
                        try:
                            driver = Activity.objects.get(actor=obj.driver,
                                                          activity_status_id__in=[IOFOptionsEnum.RUNNING,
                                                                                  IOFOptionsEnum.SUSPENDED,
                                                                                  IOFOptionsEnum.ACCEPTED])

                        except:
                            driver = None
                        try:
                            truck = Activity.objects.get(primary_entity=obj.device,
                                                         activity_status_id__in=[IOFOptionsEnum.RUNNING,
                                                                                 IOFOptionsEnum.SUSPENDED,
                                                                                 IOFOptionsEnum.ACCEPTED])
                        except:
                            truck = None

                        if driver or truck:
                            activity.activity_status = Options.objects.get(id=IOFOptionsEnum.ABORTED)

                            activity_data = create_activity_data(obj.activity.id, obj.activity.primary_entity.id,
                                                                 obj.activity.actor.id,
                                                                 timezone.now(),
                                                                 IOFOptionsEnum.ABORTED, None, None, obj.customer.id,
                                                                 obj.module.id)
                            activity_data.save()

                        else:
                            activity.activity_status = Options.objects.get(id=IOFOptionsEnum.ACCEPTED)
                            activity_data = create_activity_data(obj.activity.id, obj.activity.primary_entity.id,
                                                                 obj.activity.actor.id,
                                                                 timezone.now(),
                                                                 IOFOptionsEnum.REVIEWED, None, None, obj.customer.id,
                                                                 obj.module.id)
                            activity_data.save()

                            activity_data = create_activity_data(obj.activity.id, obj.activity.primary_entity.id,
                                                                 obj.activity.actor.id,
                                                                 timezone.now(),
                                                                 IOFOptionsEnum.ACCEPTED, None, None, obj.customer.id,
                                                                 obj.module.id)
                            activity_data.save()
                    activity.save()
                    obj.status = Options.objects.get(id=OptionsEnum.INACTIVE)
                    obj.save()

                elif obj.type.id == IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_DRIVER_REJECT and obj.activity.activity_status.id == IOFOptionsEnum.REJECTED:

                    process_activity(obj, activity, IOFOptionsEnum.ABORTED)

                elif obj.type.id == IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_NO_ACTION_ACCEPT_REJECT and obj.activity.activity_status.id == IOFOptionsEnum.REJECTED:  # Use Case: Accept reject notification sent to driver but driver doesnot take any action.
                    # Activity rejected as driver didnt take any action.
                    #  Review notification sent to admin but admin doesnot take any action
                    process_activity(obj, activity, IOFOptionsEnum.ABORTED)

                elif obj.type.id == IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_NO_ACTION_START_FAIL and obj.activity.activity_status.id == IOFOptionsEnum.FAILED:  # Use Case: Accept reject notification sent to driver but driver doesnot take any action.
                    # Activity rejected as driver didnt take any action.
                    #  Review notification sent to admin but admin doesnot take any action
                    process_activity(obj, activity, IOFOptionsEnum.ABORTED)

                elif (obj.type.id == IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_TRUCK_CONFLICT or \
                                  obj.type.id == IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_DRIVER_CONFLICT or \
                                  obj.type.id == IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_BIN_CONFLICT) \
                        and obj.activity.activity_status.id == IOFOptionsEnum.CONFLICTING:

                    process_activity(obj, activity, IOFOptionsEnum.ABORTED)

                elif (
                                obj.type.id == IOFOptionsEnum.NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_ABORT and obj.activity.activity_status.id == IOFOptionsEnum.FAILED):

                    process_activity(obj, activity, IOFOptionsEnum.ABORTED)
            else:
                print(str(buffer - timezone.now().minute) + " Minutes left to review")

        ###############################################################
        start_fail_notifications = HypernetNotification.objects.filter(
            type_id=IOFOptionsEnum.NOTIFICATION_DRIVER_START_ACTIVITY, status_id=OptionsEnum.ACTIVE)

        for obj in start_fail_notifications:
            activity = Activity.objects.get(id=obj.activity.id)
            preference = CustomerPreferences.objects.get(customer=obj.customer)

            # buffer=obj.created_datetime.minute + prefrence.activity_review_buffer

            buffer = (timezone.now() - obj.created_datetime).total_seconds()

            buffer = round(buffer / 60, 0)
            if buffer >= preference.activity_start_driver_buffer:
                if obj.type.id == IOFOptionsEnum.NOTIFICATION_DRIVER_START_ACTIVITY and obj.activity.activity_status.id == IOFOptionsEnum.ACCEPTED:
                    send_notification_to_user(obj, activity,
                                              [User.objects.get(id=obj.activity.activity_schedule.modified_by.id)],
                                              str(
                                                  obj.activity.actor.name) + " didn't take any action. Please review this activity",
                                              IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_NO_ACTION_START_FAIL)

                    create_activity_data_alter_activity(obj, activity, IOFOptionsEnum.FAILED)

                    bin_collection = BinCollectionData.objects.filter(activity=activity).update(
                        status_id=IOFOptionsEnum.ABORT_COLLECTION)
                    if not bin_collection:
                        for id in activity.action_items.split(','):
                            # try:
                            #     contract = Assignment.objects.get(parent_id = id, child__type_id = DeviceTypeEntityEnum.CONTRACT,
                            #                                       status_id = OptionsEnum.ACTIVE).child_id
                            #     try:
                            #         area = Assignment.objects.get(child_id = contract,
                            #                                       parent__type_id = DeviceTypeEntityEnum.AREA,
                            #                                       status_id = OptionsEnum.ACTIVE).parent_id
                            #     except:
                            #         area = None
                            # except:
                            #     contract = None
                            #     area = None
                            # try:
                            #     client = Entity.objects.get(id=id).client.id
                            # except:
                            #     client = None
                            bin_collection_data = create_bin_collection_data(activity.id, activity.primary_entity.id,
                                                                             activity.actor.id,
                                                                             timezone.now(),
                                                                             IOFOptionsEnum.ABORT_COLLECTION, id,
                                                                             activity.customer.id, activity.module_id)
                            bin_collection_data.save()
                            # obj.delete()
        # return generic_response("Success", http_status=200)
        print('Job completed at: ' + str(date_time.datetime.now()))

    except:
        traceback.print_exc()


###############################################################
def process_device_violations(query_set_pre):
    try:
        for pre_data in query_set_pre:
            send_email = False

            if pre_data.device.speed == True:
                send_email = speed_violations(pre_data=pre_data)

            if pre_data.device.location == True:
                pass

            if pre_data.device.temperature == True:
                pass

                if send_email:
                    pass

    except Exception as e:
        traceback.print_exc()


def speed_violations(pre_data):
    send_email = False
    try:
        device_thresholds = DeviceViolation.objects.get(customer_id=pre_data.customer_id,
                                                        device_id=pre_data.device_id, status_id=OptionsEnum.ACTIVE,
                                                        enabled=True,
                                                        violation_type_id=IOFOptionsEnum.SPEED).threshold_number

    except:
        traceback.print_exc()

        try:
            device_thresholds = CustomerPreferences.objects.get(customer_id=pre_data.customer_id).speed_violation_global
        except:
            device_thresholds = None

    if device_thresholds < pre_data.speed:
        activity = None
        try:
            activity = Activity.objects.get(primary_entity_id=pre_data.device_id, customer_id=pre_data.customer_id,
                                            activity_status_id=IOFOptionsEnum.RUNNING)
            # TODO Check Shifts of Truck/driver.

            driver = activity.actor_id
        except:
            traceback.print_exc()
            driver = None

        try:
            HypernetNotification.objects.get(timestamp__gt=pre_data.timestamp, timestamp__lt=timezone.now(),
                                             type_id=IOFOptionsEnum.SPEED, device_id=pre_data.device_id,
                                             driver_id=driver)
        except:
            traceback.print_exc()
            send_email = True
            users = User.objects.filter(role_id=RoleTypeEnum.ADMIN, customer_id=pre_data.customer_id)
            title = "Over speeding violation detected on" + " " + pre_data.device.name + " " + "at time" + " " + str(
                pre_data.timestamp)

            try:
                preferences = CustomerPreferences.objects.get(customer_id=pre_data.customer_id)
            except:
                preferences = None

            if preferences.speed_violations is True:
                notification_obj = send_notification_violations(device=pre_data.device_id, driver_id=driver,
                                                                customer_id=pre_data.customer_id,
                                                                module_id=pre_data.module_id,
                                                                title=title, users_list=users, threshold=None,
                                                                value=None)

    return send_email


def process_activity(obj, activity, status):
    activity_data = create_activity_data(obj.activity.id, obj.activity.primary_entity.id, obj.activity.actor.id,
                                         timezone.now(),
                                         status, None, None, obj.customer.id, obj.module.id)
    activity_data.save()

    activity.activity_status = Options.objects.get(id=status)
    activity.save()
    if (activity.activity_schedule.end_date is None) or (activity.activity_schedule.end_date <= timezone.now().date()):
        activity.activity_schedule.schedule_activity_status = Options.objects.get(id=OptionsEnum.INACTIVE)
        activity.activity_schedule.save()
    obj.status = Options.objects.get(id=OptionsEnum.INACTIVE)
    obj.save()
    bin_collection = BinCollectionData.objects.filter(activity=activity, status_id=IOFOptionsEnum.UNCOLLECTED).update(
        status=IOFOptionsEnum.ABORT_COLLECTION)
    if not bin_collection:
        for id in activity.action_items.split(','):
            # try:
            #     contract = Assignment.objects.get(parent_id=id, child__type_id=DeviceTypeEntityEnum.CONTRACT,
            #                                       status_id=OptionsEnum.ACTIVE).child_id
            #     try:
            #         area = Assignment.objects.get(child_id=contract,
            #                                       parent__type_id=DeviceTypeEntityEnum.AREA,
            #                                       status_id=OptionsEnum.ACTIVE).parent_id
            #     except:
            #         area = None
            # except:
            #     contract = None
            #     area = None
            # try:
            #     client = Entity.objects.get(id=id).client.id
            # except:
            #     client = None
            bin_collection_data = create_bin_collection_data(activity.id, activity.primary_entity.id, activity.actor.id,
                                                             timezone.now(), IOFOptionsEnum.ABORT_COLLECTION, id,
                                                             activity.customer.id, activity.module_id)
            bin_collection_data.save()


def create_activity_data_alter_activity(obj, activity, status):
    a_data = create_activity_data(obj.activity.id, obj.activity.primary_entity.id,
                                  obj.activity.actor.id, timezone.now(), status, None,
                                  None, obj.customer.id, obj.module.id)

    try:
        a_data.save()
        activity.activity_status = Options.objects.get(id=status)
        activity.save()
    except Exception as e:
        traceback.print_exc()

    obj.status = Options.objects.get(id=OptionsEnum.INACTIVE)
    obj.save()


def check_conflict_of_time(preferences, current, queue_time):
    end_datetime = (current + timedelta(minutes=preferences.average_activity_time))
    return current <= queue_time <= end_datetime


def util_conflict_with_time(current, preferences, obj, message, notification_type):
    if current:
        if current.start_datetime:
            conflict = check_conflict_of_time(preferences, current.start_datetime, obj.activity_datetime)
        else:
            conflict = check_conflict_of_time(preferences, current.activity_start_time,
                                              obj.activity_datetime)
        if conflict:
            activity = util_create_activity(obj, obj.actor, IOFOptionsEnum.CONFLICTING,
                                            obj.activity_datetime)
            activity.save()
            send_notification_to_admin(obj.primary_entity.id, obj.actor.id, activity.id, obj,
                                       [obj.activity_schedule.modified_by.id],
                                       message,
                                       notification_type)
            return activity
    return None


def check_bins_validity(obj):
    for id in obj.action_items.split(','):
        try:
            Entity.objects.get(id=id)
        except Entity.DoesNotExist:
            send_notification_to_admin(obj.primary_entity.id, obj.actor.id, None, obj,
                                       [obj.activity_schedule.modified_by.id],
                                       "Bin(s) that were part of the schedule have been deleted. Please try again.",
                                       None)
            return False
    return True


def check_bins_in_activity(activity_queue, message, notification_type):
    if activity_queue:
        bins = activity_queue.action_items.split(',')
        for obj in bins:
            try:
                BinCollectionData.objects.get(action_item_id=obj,
                                              activity__activity_status_id__in=[IOFOptionsEnum.RUNNING,
                                                                                IOFOptionsEnum.SUSPENDED,
                                                                                IOFOptionsEnum.ACCEPTED,
                                                                                IOFOptionsEnum.FAILED,
                                                                                IOFOptionsEnum.REJECTED])
                act = util_create_activity(activity_queue, activity_queue.actor, IOFOptionsEnum.CONFLICTING,
                                           activity_queue.activity_datetime)
                act.save()
                send_notification_to_admin(activity_queue.primary_entity.id, activity_queue.actor.id, act.id,
                                           activity_queue,
                                           [activity_queue.activity_schedule.modified_by.id],
                                           message,
                                           notification_type)
                return False
            except Exception as e:
                pass
        return True


def check_bins_in_act(activity_queue, message, notification_type):
    if activity_queue:
        occupied_bins = []
        activities = Activity.objects.filter(activity_status_id__in=[IOFOptionsEnum.RUNNING,
                                                                     IOFOptionsEnum.SUSPENDED,
                                                                     IOFOptionsEnum.ACCEPTED,
                                                                     IOFOptionsEnum.FAILED,
                                                                     IOFOptionsEnum.REJECTED])

        for obj in activities:
            for i in obj.action_items.split(','):
                occupied_bins.append(i)

        for queue in activity_queue.action_items.split(','):
            if queue in occupied_bins:
                act = util_create_activity(activity_queue, activity_queue.actor, IOFOptionsEnum.CONFLICTING,
                                           activity_queue.activity_datetime)
                act.save()
                send_notification_to_admin(activity_queue.primary_entity.id, activity_queue.actor.id, act.id,
                                           activity_queue,
                                           [activity_queue.activity_schedule.modified_by.id],
                                           message,
                                           notification_type)
                return False

        return True


def create_logistics_derived_data(pre_data, last_vol):
    try:
        fill = LogisticsDerived.objects.get(device=pre_data.device, timestamp=pre_data.timestamp)
    except:
        fill = LogisticsDerived()
        send_email = False
    fill.device = pre_data.device
    fill.customer = pre_data.customer
    fill.module = pre_data.module
    fill.latitude = pre_data.latitude
    fill.longitude = pre_data.longitude
    fill.pre_fill_vol = last_vol
    fill.post_fill_vol = pre_data.volume
    fill.temperature = pre_data.temperature
    fill.timestamp = pre_data.timestamp
    fill.save()


def create_decant_derived_data(pre_data, last_vol, vol):
    try:
        fill = LogisticsDerived.objects.get(device=pre_data.device, timestamp=pre_data.timestamp)
    except:
        fill = LogisticsDerived()
        send_email = False
    fill.device = pre_data.device
    fill.customer = pre_data.customer
    fill.module = pre_data.module
    fill.latitude = pre_data.latitude
    fill.longitude = pre_data.longitude
    fill.pre_dec_vol = last_vol
    fill.post_dec_vol = vol
    fill.temperature = pre_data.temperature
    fill.timestamp = pre_data.timestamp
    fill.save()


def check_site_zone_violation(request=None):
    present_employees = AttendanceRecord.objects.filter(
        site_checkin_dtm__date=timezone.now().date())  # querying on employees present today.
    if present_employees:
        for obj in present_employees:
            last_data = \
                HypernetPostData.objects.filter(device=obj.employee, timestamp__date=timezone.now().date()).order_by(
                    '-pk')[
                    0]

            s_flag = None
            z_flag = None

            if last_data:
                if last_data.latitude and last_data.longitude:
                    current_pt = Point(last_data.latitude,
                                       last_data.longitude)
                    zone_of_employee = Assignment.objects.get(child=last_data.device,
                                                              type_id=DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT,
                                                              status_id=OptionsEnum.ACTIVE)
                    site_of_zone = Assignment.objects.get(child=zone_of_employee.parent,
                                                          type_id=DeviceTypeAssignmentEnum.SITE_ZONE_ASSIGNMENT,
                                                          status_id=OptionsEnum.ACTIVE)
                    zones_of_site = Assignment.objects.filter(parent=site_of_zone.parent,
                                                              type_id=DeviceTypeAssignmentEnum.SITE_ZONE_ASSIGNMENT,
                                                              status_id=OptionsEnum.ACTIVE)

                    if zones_of_site:
                        s_flag = polygon_operations(zones=zones_of_site, curr_cordinates=current_pt)
                        z_flag = get_geofence_violations(last_data)
                        try:
                            if s_flag:  # flag true -> present in site    #if present in site
                                # Check if active or inactive -> site
                                # FIXME HERE IN SITE

                                if last_data.trip is not None and last_data.trip != obj.active_status:
                                    vltn = check_employee_active_status(last_data.trip, FFPOptionsEnum.IN_SITE, obj)
                                    vltn.save()
                                if obj.site_status is True:
                                    pass

                                if obj.site_checkout_dtm and obj.site_status is False:  # Just entered in site after going outside
                                    violation = create_violation_data(obj, FFPOptionsEnum.IN_SITE)
                                    violation.save()
                                    obj.zone_checkin_dtm = last_data.timestamp
                                obj.site_status = True
                                obj.save()

                            else:  # if not present in site
                                # FIXME No check for active/inactive while employee is out-of-site
                                if obj.site_status is True:  # Went outside of site.
                                    obj.site_checkout_dtm = last_data.timestamp
                                    # Adding in-site inactive row if employee is leaving site (TO DETECT ACCIRATE ACTIVE HRS)
                                    vltn = check_employee_active_status(False, FFPOptionsEnum.IN_SITE, obj)
                                    vltn.save()
                                    violation = create_violation_data(obj, FFPOptionsEnum.OUT_OF_SITE)
                                    violation.save()

                                    if z_flag is True:  # An employee went into the site but never went in zone and directly went out of zone without checking in
                                        if obj.zone_checkin_dtm is None:
                                            violation = create_violation_data(obj, FFPOptionsEnum.OUT_OF_ZONE)
                                            violation.save()
                                            obj.zone_checkout_dtm = last_data.timestamp
                                            obj.zone_status = False
                                if obj.site_status is False:
                                    pass
                                obj.site_status = False
                                obj.save()
                        except Exception as e:
                            print(traceback.print_exc())
                    try:
                        if z_flag:
                            # check for site flag
                            # if site flag false --> pass else check for active/inactive flag for zone
                            # if s_flag is True:
                            #     #FIXME This part is incorrect
                            #     if last_data.trip is not None and last_data.trip != obj.active_status:
                            #         vltn = check_employee_active_status(last_data.trip, FFPOptionsEnum.OUT_OF_ZONE, obj)
                            #         vltn.save()

                            if obj.zone_checkin_dtm:
                                if not obj.zone_checkout_dtm:
                                    # Adding in-zone inactive row if employee is leaving site (TO DETECT ACCIRATE ACTIVE HRS)
                                    vltn = check_employee_active_status(False, FFPOptionsEnum.IN_ZONE, obj)
                                    vltn.save()
                                    violation = create_violation_data(obj, FFPOptionsEnum.OUT_OF_ZONE)
                                    violation.save()
                                    obj.zone_checkout_dtm = last_data.timestamp
                                elif obj.zone_status:
                                    # Adding in-zone inactive row if employee is leaving site (TO DETECT ACCIRATE ACTIVE HRS)
                                    vltn = check_employee_active_status(False, FFPOptionsEnum.IN_ZONE, obj)
                                    vltn.save()
                                    violation = create_violation_data(obj, FFPOptionsEnum.OUT_OF_ZONE)
                                    violation.save()
                                    obj.zone_checkout_dtm = last_data.timestamp

                            obj.zone_status = False
                            obj.save()
                            print("Employee currently out of zone")
                        else:
                            if s_flag:
                                if last_data.trip is not None and last_data.trip != obj.active_status:
                                    vltn = check_employee_active_status(last_data.trip, FFPOptionsEnum.IN_ZONE, obj)
                                    vltn.save()
                            # check for active/inactive for zone
                            if obj.zone_checkin_dtm and obj.zone_status is True:
                                pass
                            if obj.zone_status is False and obj.zone_checkout_dtm:  # Coming inside zone from outside
                                violation = create_violation_data(obj, FFPOptionsEnum.IN_ZONE)
                                violation.save()
                                obj.zone_checkin_dtm = last_data.timestamp

                            if obj.zone_status is False and (
                                        obj.zone_checkin_dtm is None):  # Coming in zone for the first time.
                                violation = create_violation_data(obj, FFPOptionsEnum.IN_ZONE)
                                violation.save()
                                obj.zone_checkin_dtm = last_data.timestamp

                            obj.zone_status = True
                            obj.save()
                            print("Employee currently in-zone")

                        obj.active_status = last_data.trip
                        obj.save()
                    except Exception as e:
                        print(traceback.print_exc())
                else:
                    # FIXME ABSENT AND OUT OF ZONE IF NO LAT, LNG
                    print("No employee data available.")


@api_view(['GET'])
def generate_daily_invoices(request=None):
    customers = Customer.objects.all()
    year = date_time.datetime.now().year
    month = date_time.datetime.now().month
    day = date_time.datetime.now().day

    s_date = str(date_time.datetime(year, month, day, 0, 0, 0))
    e_date = str(date_time.datetime(year, month, day, 23, 59, 0))
    file_url = ''
    for customer in customers:
        email_body = '<body style="background:#b3dcf2;">' \
                     '<div style="max-width:600px; margin:auto; padding:30px; background:#ffffff; margin-top:30px; margin-bottom:30px; font-family:'"'Trebuchet MS'"',Arial;">' \
                     '<table style="width:100%; margin-bottom:0px; border-bottom:0px solid #808080; padding-bottom:30px;">' \
                     '<tr> ' \
                     '<td align="left"> ' \
                     '   <div style="font-size:36px; margin-bottom:20px; color:green"> <img src="http://design.hypernymbiz.com/zenath/icon-invoice.png" height="36" /> ' + customer.name + ' Invoice</div> ' \
                                                                                                                                                                                                                                                                                                 '<div style="font-size:14px; color:#808080;">To: <b style="color:#555;">' + e_date + '</b>  </div> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</td>' \
                                                                                                                                                                                                                                                                                                                                                                                          '<td style="text-align:right;"> <img src="http://design.hypernymbiz.com/zenath/zenath-logo.png" height="80" /> </td> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</tr> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</table> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<div style="margin-bottom:30px;"> <img src="http://design.hypernymbiz.com/zenath/bg-header.jpg" height="20" width="100%" /></div> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<table style="width:100%; font-size:14px; color:#555; border:0px solid #eee; background:#fefefe; padding:10px;" cellpadding="10"> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<tr> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<th style="border-bottom:2px solid #555; text-align:left; font-size:18px;" colspan="2">Invoice List</th> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</tr> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '{text} ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</table> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<div style="font-size:30px; margin-top:30px; margin-bottom:50px; color:#999; text-align:center;"> ' \
                                                                                                                                                                                                                                                                                                                                                                                          'Thanks for Your Business. ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</div> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<div style="font-size:10px; margin-top:20px; margin-bottom:20px; color:#999; text-align:center; border-top:2px dashed #eee; padding-top:20px;"> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<img src="http://design.hypernymbiz.com/zenath/logo-hypernym.png" height="50"   /> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<br /> Powered By HyperNym ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</div> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<div style="font-size:12px; margin-top:20px; margin-bottom:00px; color:#999; text-align:center;"> ' \
                                                                                                                                                                                                                                                                                                                                                                                          'Questions? Email <a href=""> support@hypernymbiz.com</a> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</div> </div> </body>'
        list_of_reports = ''
        pref = CustomerPreferences.objects.get(customer=customer)
        if pref.daily_invoice:
            users = User.objects.filter(customer=customer,
                                        role_id__in=[RoleTypeEnum.ADMIN, RoleTypeEnum.MANAGER]).values_list('email',
                                                                                                            flat=True)
            clients = CustomerClients.objects.filter(customer=customer)
            print('Job started at: ' + str(timezone.now()))
            print('clients count ' + str(clients.count()))
            print('customer ' + customer.name)
            for cl in clients:

                response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: 200, RESPONSE_DATA: {}}
                try:
                    print("going in...")
                    result = ReportViewInvoice.get_report(ReportViewInvoice(), cl.id, customer.id, s_date, e_date, None,
                                                          file_url, 1,
                                                          response_body)['response']['file']
                    print("invoice name:" + result)
                    list_of_reports += '<tr > ' \
                                       '<td style="border-bottom:1px solid #ccc;" > ' + cl.name + ' </td> ' \
                                                                                                  '<td style="border-bottom:1px solid #ccc;"> <a href="http://' + result + '"> <span style="display: inline-block; background: cadetblue;color: #fff; font-size: 12px; padding: 5px 10px; float: right; border-radius: 3px;">View  </span></a>  </td> ' \
                                                                                                                                                                           '</tr> '
                except:
                    traceback.print_exc()
                    pass
            try:
                # for user in users:
                email_body = email_body.replace('{text}', list_of_reports)
                msg = EmailMultiAlternatives('Daily Invoices for ' + (date_time.datetime.today()).strftime('%d %B, %Y'),
                                             email_body, 'support@hypernymbiz.com', to=users, cc=None, bcc=None)
                msg.content_subtype = "html"
                msg.send()
            except:
                traceback.print_exc()
    print('Job completed at: ' + str(timezone.now()))


# @api_view(['GET'])
def generate_weekly_invoices(request=None):
    customers = Customer.objects.all()
    e1_date = date_time.datetime.combine(date_time.date.today() - timedelta(1), date_time.time())
    s1_date = e1_date - timedelta(days=7)
    s_date = str(s1_date)
    e_date = str(e1_date)
    file_url = ''
    for customer in customers:
        email_body = '<body style="background:#b3dcf2;">' \
                     '<div style="max-width:600px; margin:auto; padding:30px; background:#ffffff; margin-top:30px; margin-bottom:30px; font-family:'"'Trebuchet MS'"',Arial;">' \
                     '<table style="width:100%; margin-bottom:0px; border-bottom:0px solid #808080; padding-bottom:30px;">' \
                     '<tr> ' \
                     '<td align="left"> ' \
                     '   <div style="font-size:36px; margin-bottom:20px; color:green"> <img src="http://design.hypernymbiz.com/zenath/icon-invoice.png" height="36" /> ' + customer.name + ' Invoice</div> ' \
                                                                                                                                                                                           '<div style="font-size:14px; color:#808080; margin-bottom:5px;">From: <b style="color:#555;">' + s_date + '</b>  </div> ' \
                                                                                                                                                                                                                                                                                                     '<div style="font-size:14px; color:#808080;">To: <b style="color:#555;">' + e_date + '</b>  </div> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</td>' \
                                                                                                                                                                                                                                                                                                                                                                                          '<td style="text-align:right;"> <img src="http://design.hypernymbiz.com/zenath/zenath-logo.png" height="80" /> </td> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</tr> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</table> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<div style="margin-bottom:30px;"> <img src="http://design.hypernymbiz.com/zenath/bg-header.jpg" height="20" width="100%" /></div> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<table style="width:100%; font-size:14px; color:#555; border:0px solid #eee; background:#fefefe; padding:10px;" cellpadding="10"> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<tr> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<th style="border-bottom:2px solid #555; text-align:left; font-size:18px;" colspan="2">Invoice List</th> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</tr> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '{text} ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</table> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<div style="font-size:30px; margin-top:30px; margin-bottom:50px; color:#999; text-align:center;"> ' \
                                                                                                                                                                                                                                                                                                                                                                                          'Thanks for Your Business. ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</div> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<div style="font-size:10px; margin-top:20px; margin-bottom:20px; color:#999; text-align:center; border-top:2px dashed #eee; padding-top:20px;"> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<img src="http://design.hypernymbiz.com/zenath/logo-hypernym.png" height="50"   /> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<br /> Powered By HyperNym ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</div> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<div style="font-size:12px; margin-top:20px; margin-bottom:00px; color:#999; text-align:center;"> ' \
                                                                                                                                                                                                                                                                                                                                                                                          'Questions? Email <a href=""> support@hypernymbiz.com</a> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</div> </div> </body>'
        list_of_reports = ''
        pref = CustomerPreferences.objects.get(customer=customer)
        if pref.weekly_invoice:
            users = User.objects.filter(customer=customer,
                                        role_id__in=[RoleTypeEnum.ADMIN, RoleTypeEnum.MANAGER]).values_list('email',
                                                                                                            flat=True)
            clients = CustomerClients.objects.filter(customer=customer)
            print('clients count ' + clients.count())
            print('customer ' + customer.name)
            for cl in clients:
                response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: 200, RESPONSE_DATA: {}}
                try:
                    result = ReportViewInvoice.get_report(ReportViewInvoice(), cl.id, customer.id, s_date, e_date, None,
                                                          file_url, 0,
                                                          response_body)['response']['file']
                    list_of_reports += '<tr > ' \
                                       '<td style="border-bottom:1px solid #ccc;" > ' + cl.name + ' </td> ' \
                                                                                                  '<td style="border-bottom:1px solid #ccc;"> <a href="http://' + result + '"> <span style="display: inline-block; background: cadetblue;color: #fff; font-size: 12px; padding: 5px 10px; float: right; border-radius: 3px;">View  </span></a>  </td> ' \
                                                                                                                                                                           '</tr> '
                except:
                    traceback.print_exc()
                    pass
            try:
                # for user in users:
                email_body = email_body.replace('{text}', list_of_reports)
                msg = EmailMultiAlternatives(
                    'Weekly Invoices from ' + (s1_date).strftime('%d %B, %Y') + ' to ' + (e1_date).strftime(
                        '%d %B, %Y'), email_body, 'support@hypernymbiz.com', to=users, cc=None, bcc=None)
                msg.content_subtype = "html"
                msg.send()
            except:
                traceback.print_exc()


# @api_view(['GET'])
def generate_monthly_invoices(request=None):
    return_data = []
    customers = Customer.objects.all()

    # Cron job runs at 1 st of each month, need to get date of last month for processing
    initial_date = date_time.date.today() - timedelta(1)
    year = initial_date.year
    month = initial_date.month
    date_ranges = calendar.monthrange(year, month)
    s_date = str(date_time.datetime(year, month, 1))
    e_date = str(date_time.datetime(year, month, date_ranges[1]))
    file_url = ''
    for customer in customers:
        email_body = '<body  style="background:#b3dcf2;">' \
                     '<div style="max-width:600px; margin:auto; padding:30px; background:#ffffff; margin-top:30px; margin-bottom:30px; font-family:'"'Trebuchet MS'"',Arial;">' \
                     '<table style="width:100%; margin-bottom:0px; border-bottom:0px solid #808080; padding-bottom:30px;">' \
                     '<tr> ' \
                     '<td align="left"> ' \
                     '   <div style="font-size:36px; margin-bottom:20px; color:green"> <img src="http://design.hypernymbiz.com/zenath/icon-invoice.png" height="36" /> ' + customer.name + ' Invoice</div> ' \
                                                                                                                                                                                           '                     <div style="font-size:14px; color:#808080; margin-bottom:5px;">From: <b style="color:#555;">' + s_date + '</b>  </div> ' \
                                                                                                                                                                                                                                                                                                                          '                         <div style="font-size:14px; color:#808080;">To: <b style="color:#555;">' + e_date + '</b>  </div> ' \
                                                                                                                                                                                                                                                                                                                                                                                                                                        '                       </td>' \
                                                                                                                                                                                                                                                                                                                                                                                                                                        '                       <td style="text-align:right;"> <img src="http://design.hypernymbiz.com/zenath/zenath-logo.png" height="80" /> </td> ' \
                                                                                                                                                                                                                                                                                                                                                                                                                                        '                     </tr> ' \
                                                                                                                                                                                                                                                                                                                                                                                                                                        '                   </table> ' \
                                                                                                                                                                                                                                                                                                                                                                                                                                        '                   <div style="margin-bottom:30px;"> <img src="http://design.hypernymbiz.com/zenath/bg-header.jpg" height="20" width="100%" /></div> ' \
                                                                                                                                                                                                                                                                                                                                                                                                                                        '                   <table style="width:100%; font-size:14px; color:#555; border:0px solid #eee; background:#fefefe; padding:10px;" cellpadding="10"> ' \
                                                                                                                                                                                                                                                                                                                                                                                                                                        '                     <tr> ' \
                                                                                                                                                                                                                                                                                                                                                                                                                                        '                       <th style="border-bottom:2px solid #555; text-align:left; font-size:18px;" colspan="2">Invoice List</th> ' \
                                                                                                                                                                                                                                                                                                                                                                                                                                        '                     </tr> ' \
                                                                                                                                                                                                                                                                                                                                                                                                                                        '                     {text} ' \
                                                                                                                                                                                                                                                                                                                                                                                                                                        '                   </table> ' \
                                                                                                                                                                                                                                                                                                                                                                                                                                        '                   <div style="font-size:30px; margin-top:30px; margin-bottom:50px; color:#999; text-align:center;"> ' \
                                                                                                                                                                                                                                                                                                                                                                                                                                        '                     Thanks for Your Business. ' \
                                                                                                                                                                                                                                                                                                                                                                                                                                        '                   </div> ' \
                                                                                                                                                                                                                                                                                                                                                                                                                                        '                   <div style="font-size:10px; margin-top:20px; margin-bottom:20px; color:#999; text-align:center; border-top:2px dashed #eee; padding-top:20px;"> ' \
                                                                                                                                                                                                                                                                                                                                                                                                                                        '                     <img src="http://design.hypernymbiz.com/zenath/logo-hypernym.png" height="50"   /> ' \
                                                                                                                                                                                                                                                                                                                                                                                                                                        '                    <br /> Powered By HyperNym ' \
                                                                                                                                                                                                                                                                                                                                                                                                                                        '                   </div> ' \
                                                                                                                                                                                                                                                                                                                                                                                                                                        '                   <div style="font-size:12px; margin-top:20px; margin-bottom:00px; color:#999; text-align:center;"> ' \
                                                                                                                                                                                                                                                                                                                                                                                                                                        '                     Questions? Email <a href=""> support@hypernymbiz.com</a> ' \
                                                                                                                                                                                                                                                                                                                                                                                                                                        '                   </div> </div> </body>'

        list_of_reports = ''
        pref = CustomerPreferences.objects.get(customer=customer)
        if pref.monthly_invoice:
            users = User.objects.filter(customer=customer,
                                        role_id__in=[RoleTypeEnum.ADMIN, RoleTypeEnum.MANAGER]).values_list('email',
                                                                                                            flat=True)
            clients = CustomerClients.objects.filter(customer=customer)

            for cl in clients:
                response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: 200, RESPONSE_DATA: {}}
                try:
                    result = ReportViewInvoice.get_report(ReportViewInvoice(), cl.id, customer.id, s_date, e_date, None,
                                                          file_url, 0,
                                                          response_body)['response']['file']
                    return_data.append(result)
                    # list_of_reports += '<a href="http://'+result+'">' +cl.name+'</a><br><br>'
                    list_of_reports += '<tr > ' \
                                       '<td style="border-bottom:1px solid #ccc;" > ' + cl.name + ' </td> ' \
                                                                                                  '<td style="border-bottom:1px solid #ccc;"> <a href="http://' + result + '"> <span style="display: inline-block; background: cadetblue;color: #fff; font-size: 12px; padding: 5px 10px; float: right; border-radius: 3px;">View  </span></a>  </td> ' \
                                                                                                                                                                           '</tr> '
                except:
                    traceback.print_exc()
                    pass
            try:
                # for user in users:
                email_body = email_body.replace('{text}', list_of_reports)
                msg = EmailMultiAlternatives('Monthly Invoices ' + initial_date.strftime('%B, %Y'), email_body,
                                             'support@hypernymbiz.com', to=users, cc=None, bcc=None)
                msg.content_subtype = "html"
                msg.send()
            except:
                traceback.print_exc()


def process_iop_data(request=None):
    try:
        print('-----------Start time '+  str(date_time.datetime.now()) + '------------')
        iop_devices = Devices.objects.filter(device__type_id=DeviceTypeEntityEnum.IOP_DEVICE)

        for iop_device in iop_devices:

            en = Entity.objects.get(engine_number=iop_device.device.engine_number)

            new_error_log = set()

            try:
                existing_error_logs = ErrorLogs.objects.filter(device=iop_device.device).values_list('inactive_score',
                                                                                                     flat=True)

                if iop_device.device_id == 115:
                    print('error logs  ', iop_device.device_id, ' - ', existing_error_logs)

            except Exception as e:
                print(e)
                existing_error_logs = []

            queryset = HypernetPreData.objects.filter(device=iop_device.device).order_by('timestamp')

            print("queryset count ", queryset.count())
            for pre_data in queryset:

                post = HypernetPostData()
                post.device = pre_data.device
                post.customer = pre_data.customer
                post.module = pre_data.module
                post.type = pre_data.type
                post.timestamp = pre_data.timestamp

                post.latitude = pre_data.latitude
                post.longitude = pre_data.longitude
                post.ambient_temperature = pre_data.ambient_temperature
                post.temperature = pre_data.temperature

                # ON/OFF STATUS.
                post.harsh_braking = pre_data.harsh_braking
                # ERROR CODE

                # Current temperature threshold
                post.debug_key = pre_data.debug_key
                post.ctt = pre_data.ctt
                post.active_score = pre_data.active_score
                post.heartrate_value = pre_data.heartrate_value
                post.inactive_score = pre_data.inactive_score
                post.cdt=pre_data.cdt
                post.clm=pre_data.clm
                post.save()

                en.registration = post.debug_key
                # if pre_data.inactive_score and pre_data.inactive_score > 0:

                if pre_data.inactive_score and pre_data.inactive_score > 0:
                    if pre_data.inactive_score not in existing_error_logs:
                        new_error_log.add(pre_data.inactive_score)
                        # new_error_log.append(ErrorLogs(device=pre_data.device, inactive_score=pre_data.inactive_score))
                try:
                    #\\ removed line 2084
                    # if pre_data.inactive_score>0:
                        #\\ adding lines 2085 to 2087
                    try:
                        error_log_recent = ErrorLogs.objects.filter(device=iop_device.device).latest('id')
                    except Exception as e:
                        error_log_recent = None
                    print("recent error log", error_log_recent)
                    if error_log_recent:
                        if error_log_recent.inactive_score != pre_data.inactive_score:
                            ErrorLogs.objects.create(device=iop_device.device, inactive_score=pre_data.inactive_score, err_datetime=pre_data.timestamp)
                    else:
                        ErrorLogs.objects.create(device=iop_device.device, inactive_score=pre_data.inactive_score,
                                                 err_datetime=pre_data.timestamp)
                except Exception as e:
                    print('error log execption', e)

                pre_data.delete()

            # try:
            #     for err in new_error_log:
            #         ErrorLogs.objects.create(device=iop_device.device, inactive_score=err)
            # except Exception as e:
            #     print('error log execption', e)

            en.save()

        print('-----------END time '+  str(date_time.datetime.now()) + '------------')

    except Exception as e:
        print(e)


def contracts_report_monthly(request=None):
    from django.db.models import F
    customers = Customer.objects.all()
    current_month = date_time.datetime.today().month

    current_year = date_time.datetime.today().year

    initial_date = date_time.date.today() - timedelta(1)
    year = initial_date.year
    month = initial_date.month
    date_ranges = calendar.monthrange(year, month)
    s_date = str(date_time.datetime(year, month, 1))
    e_date = str(date_time.datetime(year, month, date_ranges[1]))
    file_url = ''
    new_contracts = []
    renewed_contracts = []
    expired_contracts = []

    for customer in customers:
        #  users = User.objects.filter(customer=customer,
        #                             role_id__in=[RoleTypeEnum.ADMIN, RoleTypeEnum.MANAGER]).values_list(
        #     'email', flat=True)

        contracts = Entity.objects.filter(customer=customer, type_id=DeviceTypeEntityEnum.CONTRACT).exclude(
            status_id=OptionsEnum.DELETED).order_by(
            '-modified_datetime').distinct()

        new_contracts_qset = contracts.filter(date_commissioned__month=current_month,
                                              date_commissioned__year=current_year)  # .values('name','skip_rate',skip = F('skip_size__label'), party_code = F('client__party_code'),client_name=F('client__name')),
        for i in new_contracts_qset:
            new_contracts.append(i.name)

        expired_contracts_qset = contracts.filter(date_of_joining__month=current_month,
                                                  date_of_joining__year=current_year)  # .values('name','skip_rate',skip= F('skip_size__label'),party_code = F('client__party_code'),client_name=F('client__name'))

        for i in expired_contracts_qset:
            expired_contracts.append(i.name)

        renewed_contracts_qset = contracts.filter(
            speed=True)  # .values('name','skip_rate',skip= F('skip_size__label'),party_code = F('client__party_code'),client_name=F('client__name'))

        for i in renewed_contracts_qset:
            renewed_contracts.append(i.name)

        email_body = '<body style="background:#b3dcf2;">' \
                     '<div style="max-width:600px; margin:auto; padding:30px; background:#ffffff; margin-top:30px; margin-bottom:30px; font-family:'"'Trebuchet MS'"',Arial;">' \
                     '<table style="width:100%; margin-bottom:0px; border-bottom:0px solid #808080; padding-bottom:30px;">' \
                     '<tr> ' \
                     '<td align="left"> ' \
                     '   <div style="font-size:36px; margin-bottom:20px; color:green"> <img src="http://design.hypernymbiz.com/zenath/icon-invoice.png" height="36" /> ' + customer.name + ' Contracts Report</div> ' \
                                                                                                                                                                                           '<div style="font-size:14px; color:#808080; margin-bottom:5px;">From: <b style="color:#555;">' + s_date + '</b>  </div> ' \
                                                                                                                                                                                                                                                                                                     '<div style="font-size:14px; color:#808080;">To: <b style="color:#555;">' + e_date + '</b>  </div> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</td>' \
                                                                                                                                                                                                                                                                                                                                                                                          '<td style="text-align:right;"> <img src="http://design.hypernymbiz.com/zenath/zenath-logo.png" height="80" /> </td> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</tr> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</table> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<div style="margin-bottom:30px;"> <img src="http://design.hypernymbiz.com/zenath/bg-header.jpg" height="20" width="100%" /></div> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<table style="width:100%; font-size:14px; color:#555; border:0px solid #eee; background:#fefefe; padding:10px;" cellpadding="10"> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<tr> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<th style="border-bottom:2px solid #555; text-align:left; font-size:18px;" colspan="2">List of contracts</th> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</tr> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '{text} ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</table> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<div style="font-size:30px; margin-top:30px; margin-bottom:50px; color:#999; text-align:center;"> ' \
                                                                                                                                                                                                                                                                                                                                                                                          'Thanks for Your Business. ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</div> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<div style="font-size:10px; margin-top:20px; margin-bottom:20px; color:#999; text-align:center; border-top:2px dashed #eee; padding-top:20px;"> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<img src="http://design.hypernymbiz.com/zenath/logo-hypernym.png" height="50"   /> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<br /> Powered By HyperNym ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</div> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<div style="font-size:12px; margin-top:20px; margin-bottom:00px; color:#999; text-align:center;"> ' \
                                                                                                                                                                                                                                                                                                                                                                                          'Questions? Email <a href=""> support@hypernymbiz.com</a> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</div> </div> </body>'                                                                                                                                                                      '                     <div style="font-size:14px; color:#808080; margin-bottom:5px;">From: <b style="color:#555;">' + s_date + '</b>  </div> ' \
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      '                         <div style="font-size:14px; color:#808080;">To: <b style="color:#555;">' + e_date + '</b>  </div> ' \
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    '                   </div> </div> </body>'

        list_of_reports = ''
        pref = CustomerPreferences.objects.get(customer=customer)

        response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: 200, RESPONSE_DATA: {}}

        try:

            new_contracts_result = append_to_email_list(s_date, e_date, file_url, response_body,
                                                        'List of new contracts this month', new_contracts,
                                                        'New Contracts')

            list_of_reports += '<tr > ' \
                               '<td style="border-bottom:1px solid #ccc;" > New Contracts </td> ' \
                               '<td style="border-bottom:1px solid #ccc;"> <a href="http://' + new_contracts_result + '"> <span style="display: inline-block; background: cadetblue;color: #fff; font-size: 12px; padding: 5px 10px; float: right; border-radius: 3px;">View  </span></a>  </td> ' \
                                                                                                                      '</tr> '

            expired_contracts_result = append_to_email_list(s_date, e_date, file_url, response_body,
                                                            'List of contracts expiring this month', expired_contracts,
                                                            'Expiring contracts')

            list_of_reports += '<tr > ' \
                               '<td style="border-bottom:1px solid #ccc;" > Expired contracts </td> ' \
                               '<td style="border-bottom:1px solid #ccc;"> <a href="http://' + expired_contracts_result + '"> <span style="display: inline-block; background: cadetblue;color: #fff; font-size: 12px; padding: 5px 10px; float: right; border-radius: 3px;">View  </span></a>  </td> ' \
                                                                                                                          '</tr> '

            renewed_contracts_result = append_to_email_list(s_date, e_date, file_url, response_body,
                                                            'List of renewed contracts this month',
                                                            renewed_contracts_qset, 'Renewed contracts')

            list_of_reports += '<tr > ' \
                               '<td style="border-bottom:1px solid #ccc;" > Renewed Contracts </td> ' \
                               '<td style="border-bottom:1px solid #ccc;"> <a href="http://' + renewed_contracts_result + '"> <span style="display: inline-block; background: cadetblue;color: #fff; font-size: 12px; padding: 5px 10px; float: right; border-radius: 3px;">View  </span></a>  </td> ' \
                                                                                                                          '</tr> '

            # list_of_reports += '<a href="http://'+result+'">' +cl.name+'</a><br><br>'
        except:
            traceback.print_exc()
            pass
        try:
            # for user in users:
            email_body = email_body.replace('{text}', list_of_reports)
            msg = EmailMultiAlternatives('Monthly Contract Report' + initial_date.strftime('%B, %Y'), email_body,
                                         'support@hypernymbiz.com', to=['13bscsmbaig@seecs.edu.pk'], cc=None, bcc=None)
            msg.content_subtype = "html"
            msg.send()
        except:
            traceback.print_exc()


def iop_aggregation(request=None):
    today = timezone.now().date().today()
    yesterday = timezone.now().date().today() - timedelta(days=2)

    ents = Entity.objects.filter(type_id=DeviceTypeEntityEnum.IOP_DEVICE,
                                 entity_sub_type_id=IopOptionsEnums.WATER_HEATER)

    for e in ents:
        data = HypernetPostData.objects.filter(device=e, timestamp__date=yesterday).order_by('timestamp')
        try:
            aggregation_today = IopDerived.objects.get(timestamp__date=yesterday)
        except:
            aggregation_today = None
        if not aggregation_today:
            total_data_today = data.count()
            active_duration = 0
            result = []
            on_flag = off_flag = True
            on_obj = off_obj = None

            if len(data) >= 1:
                for d in data:
                    if d.harsh_braking is True and on_flag is True:
                        on_obj = d
                        on_flag = False
                        pass

                    if d.harsh_braking is False and off_flag is True:
                        off_obj = d
                        off_flag = False
                        pass

                    if on_obj and off_obj and off_obj.timestamp > on_obj.timestamp:
                        duration = (off_obj.timestamp - on_obj.timestamp).total_seconds()
                        duration = duration / 60
                        active_duration += duration
                        on_obj = off_obj = None
                        on_flag = off_flag = True

                    if on_obj and off_obj and off_obj.timestamp < on_obj.timestamp:
                        on_obj = off_obj = None
                        on_flag = off_flag = True

                if data[total_data_today - 1].harsh_braking is True:
                    # last_obj_time = data[total_data_today-1].timestamp
                    # duration = (last_obj_time - on_obj.timestamp).total_seconds()
                    # duration = duration / 60
                    # active_duration += duration
                    pass
                energy_consumed = (
                                      active_duration / 60) * 1.8  # 1.8 is fixed for now. The power consumption for a water heater will be stored in entity.
                if not aggregation_today:
                    obj = create_iop_aggregation(active_duration, energy_consumed, e)
                    obj.save()
                    # save object here


def create_iop_aggregation(active_duration, energy_consumed, device):
    obj = IopDerived(
        device=device,
        customer=device.customer,
        active_duration=active_duration,
        total_energy_consumed=energy_consumed,
        timestamp=timezone.now()
    )
    return obj


def non_active_bins(request=None):
    # Cron job runs at 1 st of each month, need to get date of last month for processing
    initial_date = date_time.date.today() - timedelta(1)
    year = initial_date.year
    month = initial_date.month
    date_ranges = calendar.monthrange(year, month)
    s_date = str(date_time.datetime(year, month, 1))
    e_date = str(date_time.datetime(year, month, date_ranges[1]))
    file_url = ''
    bin_list = []
    current_month = date_time.datetime.today().month
    current_year = date_time.datetime.today().year

    module_customers = ModuleAssignment.objects.filter(module=ModuleEnum.IOL).values('customer_id')
    customers = Customer.objects.filter(id__in=module_customers)

    for customer in customers:
        users = User.objects.filter(customer=customer,
                                    role_id__in=[RoleTypeEnum.ADMIN, RoleTypeEnum.MANAGER]).values_list(
            'email', flat=True)

        bins = BinCollectionData.objects.filter(customer=customer, timestamp__month=current_month,
                                                timestamp__year=current_year).distinct(
            'action_item').values_list('action_item', flat=True)
        return_data = []
        bins_list = []

        for b in bins:
            if BinCollectionData.objects.filter(action_item=b, timestamp__month=current_month,
                                                timestamp__year=current_year).count() <= 2:
                bins_list.append(b.name)

        email_body = '<body style="background:#b3dcf2;">' \
                     '<div style="max-width:600px; margin:auto; padding:30px; background:#ffffff; margin-top:30px; margin-bottom:30px; font-family:'"'Trebuchet MS'"',Arial;">' \
                     '<table style="width:100%; margin-bottom:0px; border-bottom:0px solid #808080; padding-bottom:30px;">' \
                     '<tr> ' \
                     '<td align="left"> ' \
                     '   <div style="font-size:36px; margin-bottom:20px; color:green"> <img src="http://design.hypernymbiz.com/zenath/icon-invoice.png" height="36" /> ' + customer.name + ' Inactive Bins</div> ' \
                                                                                                                                                                                           '<div style="font-size:14px; color:#808080; margin-bottom:5px;">From: <b style="color:#555;">' + s_date + '</b>  </div> ' \
                                                                                                                                                                                                                                                                                                     '<div style="font-size:14px; color:#808080;">To: <b style="color:#555;">' + e_date + '</b>  </div> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</td>' \
                                                                                                                                                                                                                                                                                                                                                                                          '<td style="text-align:right;"> <img src="http://design.hypernymbiz.com/zenath/zenath-logo.png" height="80" /> </td> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</tr> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</table> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<div style="margin-bottom:30px;"> <img src="http://design.hypernymbiz.com/zenath/bg-header.jpg" height="20" width="100%" /></div> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<table style="width:100%; font-size:14px; color:#555; border:0px solid #eee; background:#fefefe; padding:10px;" cellpadding="10"> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<tr> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<th style="border-bottom:2px solid #555; text-align:left; font-size:18px;" colspan="2">Click to view the inactive bins</th> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</tr> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '{text} ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</table> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<div style="font-size:30px; margin-top:30px; margin-bottom:50px; color:#999; text-align:center;"> ' \
                                                                                                                                                                                                                                                                                                                                                                                          'Thanks for Your Business. ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</div> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<div style="font-size:10px; margin-top:20px; margin-bottom:20px; color:#999; text-align:center; border-top:2px dashed #eee; padding-top:20px;"> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<img src="http://design.hypernymbiz.com/zenath/logo-hypernym.png" height="50"   /> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<br /> Powered By HyperNym ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</div> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '<div style="font-size:12px; margin-top:20px; margin-bottom:00px; color:#999; text-align:center;"> ' \
                                                                                                                                                                                                                                                                                                                                                                                          'Questions? Email <a href=""> support@hypernymbiz.com</a> ' \
                                                                                                                                                                                                                                                                                                                                                                                          '</div> </div> </body>'                                                                                                                                                                      '                     <div style="font-size:14px; color:#808080; margin-bottom:5px;">From: <b style="color:#555;">' + s_date + '</b>  </div> ' \
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      '                         <div style="font-size:14px; color:#808080;">To: <b style="color:#555;">' + e_date + '</b>  </div> ' \
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    '                   </div> </div> </body>'

        list_of_reports = ''
        pref = CustomerPreferences.objects.get(customer=customer)

        response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: 200, RESPONSE_DATA: {}}
        try:
            result = ReportViewGeneric.get_report(ReportViewGeneric(), s_date, e_date,
                                                  file_url, 0,
                                                  response_body, "List of inactive bins", bins_list, 'inactive_bins')[
                'response']['file']
            return_data.append(result)
            # list_of_reports += '<a href="http://'+result+'">' +cl.name+'</a><br><br>'
            list_of_reports = '<tr > ' \
                              '<td style="border-bottom:1px solid #ccc;" >  </td> ' \
                              '<td style="border-bottom:1px solid #ccc;"> <a href="http://' + result + '"> <span style="display: inline-block; background: cadetblue;color: #fff; font-size: 12px; padding: 5px 10px; float: right; border-radius: 3px;">View  </span></a>  </td> ' \
                                                                                                       '</tr> '
        except:
            traceback.print_exc()
            pass
        try:
            # for user in users:
            email_body = email_body.replace('{text}', list_of_reports)
            msg = EmailMultiAlternatives('Inactive bins ' + initial_date.strftime('%B, %Y'), email_body,
                                         'support@hypernymbiz.com', to=users, cc=None, bcc=None)
            msg.content_subtype = "html"
            msg.send()
        except:
            traceback.print_exc()

    print(bin_list)


def append_to_email_list(s_date, e_date, file_url, response_body, heading, table_data, report_title, table_cols=None):
    result_list = []
    result = ReportViewGeneric.get_report(ReportViewGeneric(), s_date, e_date,
                                          file_url, 0,
                                          response_body, heading, table_data, report_title)['response']['file']
    result_list.append(result)

    # list_of_reports += '<a href="http://'+result+'">' +cl.name+'</a><br><br>'
    return result


# @api_view(['GET'])
def calculate_fuel_averages_on_fillups(request=None):
    module_customers = ModuleAssignment.objects.filter(module=ModuleEnum.IOL).values('customer_id')
    customers = Customer.objects.filter(id__in=module_customers)
    for customer in customers:
        trucks = Entity.objects.filter(type_id=DeviceTypeEntityEnum.TRUCK, customer=customer)
        # trucks = Entity.objects.filter(id=10341)
        for truck in trucks:
            try:
                fillups = LogisticsDerived.objects.filter(customer=customer, device=truck,
                                                          fuel_avg__isnull=True).order_by('timestamp')
                # fillups = LogisticsDerived.objects.filter(customer_id=2, device_id=10341, fuel_avg__isnull=True).order_by('timestamp')
                try:
                    last_fillup = \
                        LogisticsDerived.objects.filter(customer=customer, device=truck,
                                                        fuel_avg__isnull=False).order_by(
                            '-timestamp')[0]
                    # last_fillup = LogisticsDerived.objects.filter(customer_id=2, device=10341, fuel_avg__isnull=False).order_by('-timestamp')[0]
                except:
                    last_fillup = None
                i = 0
                pre = 0
                post = 0
                first_timestamp = None
                timestamp = None
                fill_data = dict()
                fillup_data = []
                for f in fillups:
                    if f.pre_fill_vol and f.post_fill_vol:
                        if pre == 0:
                            pre = f.pre_fill_vol
                            first_timestamp = f.timestamp
                        else:
                            if post <= f.pre_fill_vol:
                                # To mark record as processed
                                if (f.timestamp - timestamp).total_seconds() > 600:
                                    if last_fillup:
                                        # Swap the start datetime if last fillup exists
                                        first_timestamp = last_fillup.timestamp

                                    # Get distance travelled from start and end datetime
                                    f.distance_travelled = (
                                                               get_generic_distance_travelled(customer.id, truck.id,
                                                                                              None, None,
                                                                                              str(first_timestamp),
                                                                                              str(timestamp))) / 1000
                                    f.fuel_consumed = float(post - pre) * 0.219
                                    f.fuel_avg = float(f.distance_travelled) / f.fuel_consumed
                                    f.save()
                                    pre = f.pre_fill_vol
                                    first_timestamp = timestamp
                                else:
                                    f.fuel_avg = 0
                                    f.save()
                            else:
                                if last_fillup:
                                    # Swap the start datetime if last fillup exists
                                    first_timestamp = last_fillup.timestamp

                                # Get distance travelled from start and end datetime
                                f.distance_travelled = (
                                                           get_generic_distance_travelled(customer.id, truck.id, None,
                                                                                          None,
                                                                                          str(first_timestamp),
                                                                                          str(timestamp))) / 1000
                                f.fuel_consumed = float(post - pre) * 0.219
                                f.fuel_avg = float(f.distance_travelled) / f.fuel_consumed
                                f.save()
                                pre = f.pre_fill_vol
                                first_timestamp = timestamp
                        post = f.post_fill_vol
                        timestamp = f.timestamp
                        i += 1
                        if fillups.count() == i:
                            if last_fillup:
                                # Swap the start datetime if last fillup exists
                                first_timestamp = last_fillup.timestamp

                            # Get distance travelled from start and end datetime
                            f.distance_travelled = (get_generic_distance_travelled(customer.id, truck.id, None, None,
                                                                                   str(first_timestamp),
                                                                                   str(timestamp))) / 1000
                            f.fuel_consumed = float(post - pre) * 0.219
                            f.fuel_avg = float(f.distance_travelled) / f.fuel_consumed
                            f.save()

            except:
                traceback.print_exc()
    print('Job completed at: ' + str(date_time.datetime.now()))

def appliance_aggregation():
    try:
        print('-----------Start time '+  str(date_time.datetime.now()) + '------------')
        # devices = Devices.objects.filter(device__type_id=DeviceTypeEntityEnum.IOP_DEVICE)
        # devices = Entity.objects.filter(type_id=DeviceTypeEntityEnum.IOP_DEVICE)
        aggregations = LogisticAggregations.objects.all()
        for aggregation in aggregations:
            date_now = timezone.now()
            print(date_now,'date Now')

            # Table for maintaining online/offline status of a device. Contains only one row for a device in it's entire lifetime. That row keeps getting updated
            print((date_now - aggregation.timestamp).total_seconds() / 60 > 2)
            if (date_now - aggregation.timestamp).total_seconds() / 60 > 2 and aggregation.online_status:
                print(aggregation)
                aggregation.online_status = False
                aggregation.save()
                print(aggregation)
                print("Exists ", aggregation.device_id, ' ', aggregation.last_updated)
            elif aggregation.online_status:
                pass

                # status.save()
                '''
                send_mail('Device Offline',
                          'Device is offline id: ' + d.device.name + ' since: ' + str(d.timestamp) + ' at: ' + str(
                              date_now),
                          'support@hypernymbiz.com',
                          constants.email_list_iop, fail_silently=True)
                 '''
    # except LogisticAggregations.DoesNotExist:
    #     print(d)
    #     aggregation = LogisticAggregations()
    #     aggregation.device = d.device
    #     if (date_now - d.timestamp).total_seconds() / 60 < 1:  # This will run only one time
    #         aggregation.online_status = True
    #     aggregation.timestamp = timezone.now()
    #     aggregation.customer = d.device.customer
    #     aggregation.module = d.device.module
    #     aggregation.last_updated = timezone.now()
    #     aggregation.save()
    #     print("Don't Exists ", aggregation.device_id, ' ', aggregation.last_updated)
    except Exception as e:
        print("Execption", e)

    print('-----------end time '+  str(date_time.datetime.now()) + '------------')  
def get_chs_device(device_id):
    try:
        querysets = HypernetPreData.objects.filter(device_id=device_id).latest('timestamp')
        return querysets
        
    except Exception as e:
        print(e)
        try:
            querysets = HypernetPostData.objects.filter(device_id=device_id).latest('timestamp')
            return querysets
        except Exception as e:
            print(e)
            return None 
def get_ctt_device(device_id):
    try:
        querysets = HypernetPreData.objects.filter(device_id=device_id).latest('timestamp')
        return querysets.ctt
        
    except Exception as e:
        print(e)
        try:
            querysets = HypernetPostData.objects.filter(device_id=device_id).latest('timestamp')
            return querysets.ctt
        except Exception as e:
            print(e)
            return None 
# change segment control according to current chs of device.
# this function excute every one minute and check current chs value and segment control value
# if segment control value and curent chs value not same and segment control set value according to current chs of device 
def change_segment_control_according_to_chs():
    try:
        entities=Entity.objects.filter(module_id=ModuleEnum.IOP,
                                    type_id=DeviceTypeEntityEnum.IOP_DEVICE,
                                    status_id=OptionsEnum.ACTIVE)
        for entity in entities:
            chs_value=get_chs_value_from_hyperpredata_hyperpostdata(entity)
            print(entity.standby_mode,'change segment_according to chs')
            print(chs_value,'current chs_value')
            if chs_value:
                if chs_value ==1:
                    entity.standby_mode=2
                    print('chs-1')
                elif chs_value ==2:
                    print('chs-2')
                    entity.standby_mode=3
                else:
                    entity.standby_mode=1
                    print('chs-3')
                entity.save()
    except Exception as e:
        print(e)
                
            
        
#this is use for get ctt value from activityQueue table  if ctt is null then ctt set 75 by default   
def get_ctt_value(activity_queue):
    if activity_queue.activity_schedule.current_ctt is None:
        ctt=constants.ACTIVITY_TEMP
        return int(ctt)
    ctt=activity_queue.activity_schedule.current_ctt
    return int(ctt)
    
#this function use for check retrying tag if activity is retrying tag and error=0 or chs =3 ,4 then retrying tag remove 
def change_retrying_state(activity_queue):
    try:
        current_chs=get_chs_device(activity_queue.primary_entity)
        # current_chs=HypernetPostData.objects.filter(device_id=activity_queue.primary_entity).latest('timestamp')
        if int(current_chs.heartrate_value) is 3 or int(current_chs.heartrate_value) is 4:
            print(activity_queue.activity_schedule.id,'schel')
            activity=Activity.objects.get(activity_schedule=activity_queue.activity_schedule.id,activity_status=IopOptionsEnums.IOP_SCHEDULE_RETRYING)
            if activity:
                activity.delete()
                HypernetNotification.objects.filter(value=activity_queue.id).delete()
                set_device_temperature(activity_queue, str(constants.ACTIVITY_TEMP))
    except Exception as e: 
        print(e)
#this function use for check ready tag in last event and if current activity change into in use or not used according to temperatur fall
def check_ready_tag(activity_queue):
    try:
        print('here for check ready tag')
        current_datetime = date_time.datetime.now()
        current_datetime = current_datetime.replace(tzinfo=None, second=0, microsecond=0)
        print("CURRENT DATE TIME", current_datetime.date())
        ready_tag=Options.objects.get(id=IopOptionsEnums.IOP_SCHEDULE_READY)
        activity = Activity.objects.get(activity_status=ready_tag,primary_entity=activity_queue.primary_entity)
        print("ready tag activity")
        flag = new_detect_drop_in_temperature(activity_queue.primary_entity)
        flag=False
        print('DROP IN TEMMPERATURE IN SCHEDULE READY ', flag)
        activity_time = activity.activity_schedule.new_end_dt.replace(tzinfo=None, second=0, microsecond=0)
        print("time left for ready tag",round((current_datetime - activity_time).total_seconds() / 60))                   
        if round((current_datetime - activity_time).total_seconds() / 60) >= 0:
            if flag is True:
                activity.activity_status = Options.objects.get(id=IopOptionsEnums.IOP_SCHEDULE_IN_USE)
                activity.save()
            else:
                activity.activity_status = Options.objects.get(id=IopOptionsEnums.IOP_SCHEDULE_CANCELLED)
                activity.save()
            activity.activity_schedule.schedule_activity_status=Options.objects.get(id=OptionsEnum.INACTIVE)
            activity.activity_schedule.save()
            ActivityQueue.objects.filter(activity_schedule=activity.activity_schedule).delete()
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return True
    
#this function is use for check retrying activity is already in event or not. 
#if retrying tag already in event and wait for event time,
#after the event time set tag not used or in use according to current temp of device 
def check_activity_retrying(activity_queue):
    try:
        current_datetime = date_time.datetime.now()
        current_datetime = current_datetime.replace(tzinfo=None, second=0, microsecond=0)
        print("CURRENT DATE TIME in retrying", current_datetime.date())
        activity_queue_time = activity_queue.activity_schedule.new_end_dt.replace(tzinfo=None, second=0, microsecond=0)
        current_activity_queue_time=round((activity_queue_time - current_datetime).total_seconds() / 60)
        print(current_activity_queue_time,'current activity time left')
        retrying=Options.objects.get(id=IopOptionsEnums.IOP_SCHEDULE_RETRYING)
        activity=Activity.objects.get(primary_entity=activity_queue.primary_entity,activity_status=retrying)
        if activity:
            activity_time =activity.activity_schedule.new_end_dt.replace(tzinfo=None, second=0, microsecond=0)
            last_activity_queue_time=round((activity_time - current_datetime).total_seconds() / 60)
            print(last_activity_queue_time,'last activity time left')
            if last_activity_queue_time >= current_activity_queue_time:
                activity.delete()
                return False
            else:
                return True
        return False
    except Exception as e:
        print(e)
        return False
    
#add schedule is use for when repeated event or sleep mode end.
#same value will be add in table but nxt datetime.
#add ActivitySchedule in table this table tigger the activityQueue and made the activity queue row 
def add_schedule(schedule,new_date):
    try:
        ActivitySchedule.objects.create(
            customer=schedule.customer,
            module=schedule.module,
            modified_by=schedule.modified_by,
            suspend_status=schedule.suspend_status,
            multi_days=schedule.multi_days,
            sleep_mode=schedule.sleep_mode,
            activity_route=schedule.activity_route,
            end_date=new_date,
            start_date=new_date,
            old_start_dt=parse(str(new_date) + '-' + str(schedule.activity_start_time)),
            new_start_dt=parse(str(new_date) + '-' + str(schedule.activity_start_time)),
            old_end_dt=parse(str(new_date) + '-' + str(schedule.activity_end_time)),
            new_end_dt=parse(str(new_date) + '-' + str(schedule.activity_end_time)),
            validity_date=schedule.validity_date,
            temp_after_usage=schedule.temp_after_usage,
            u_days_list=schedule.days_list,
            u_activity_start_time=schedule.activity_start_time,
            activity_start_time=schedule.activity_start_time,
            u_activity_end_time=schedule.activity_end_time,
            activity_end_time=schedule.activity_end_time,
            notes=schedule.notes,
            activity_check_point=schedule.activity_check_point,
            schedule_type=schedule.schedule_type,
            primary_entity=schedule.primary_entity,
            activity_type=schedule.activity_type,
            action_items=schedule.action_items,
            schedule_activity_status=schedule.schedule_activity_status,
            days_list=schedule.days_list,
            suggestion=schedule.suggestion,
            current_ctt=schedule.current_ctt


        )
    except Exception as e:
        print(e)
        
#this function check the repeated event and validity date
# if the validity date equal to current date return False.
# only check the validity date and repeated event 
def check_repeated_event(activity_queue):
    try:
        
        date_now=date_time.datetime.now()
    # current_datetime = date_now + datetime.timedelta(days=0)
        today=date_now.replace(second=0, microsecond=0)
        current_date=today.date()
        print(current_date)
        schedule=ActivitySchedule.objects.get(id=activity_queue.activity_schedule_id,activity_type_id=IopOptionsEnums.IOP_SCHEDULE_DAILY)

        if schedule.validity_date == current_date:
            return False
        return True
    except ActivitySchedule.DoesNotExist:
        return False
#this function add event next 7 day of week 
def add_new_schedule_event(activity_queue):
    try:
        schedule=ActivitySchedule.objects.get(id=activity_queue.activity_schedule_id,activity_type_id=IopOptionsEnums.IOP_SCHEDULE_DAILY)
        start_date=schedule.start_date
        new_date = start_date + date_time.timedelta(days=7)
        print(new_date)
        add_schedule(schedule,new_date)
    except Exception as e:
        print(e)


#cron job for manual mode check if the manual mode disable check ctt change without creating event after one minutes check ctt become 55 

def manual_mode_check_appliance(request=None):
    print('-----------Start time '+  str(date_time.datetime.now()) + '------------')
    try:
        change_segment_control_according_to_chs()
        current_datetime = date_time.datetime.now()
        entities=Entity.objects.filter(module_id=ModuleEnum.IOP,
                                 type_id=DeviceTypeEntityEnum.IOP_DEVICE,
                                 status_id=OptionsEnum.ACTIVE, temperature=False)
        today = str(current_datetime.weekday()) 
    
        for entity in entities:
            today_queues = ActivityQueue.objects.filter(day_of_week=today, activity_datetime__date=current_datetime.date(), module=ModuleEnum.IOP,
                                                    temp_set=True,primary_entity=entity.id,is_on=False).order_by('activity_datetime')
            
            try:
                print(entity.name)
                check_error=appliance_error(entity)
                print(check_error,'check error')
                error=check_error.get('error',False)
                if error is False:
                    if len(today_queues) == 0:
                            print(entity.name,entity.is_manual_mode)
                            current_ctt=get_ctt_device(entity)
                            if entity.is_manual_mode is False:
                                print(current_ctt,'ctt',entity.end_datetime)
                                if current_ctt is not constants.DEFAULT_TEMP:
                                    print('zone 1')
                                    if entity.end_datetime ==None:
                                        print('zone 2')
                                        Entity.objects.filter(id=entity.id).update(end_datetime=current_datetime)
                                    else:
                                        total_minutes = (current_datetime.replace(
                                        tzinfo=timezone.utc)- entity.end_datetime).total_seconds()  # Check how much time remaning for queue to execute
                                        print(total_minutes,'check time ')
                                        minutes_check = round(total_minutes / 60, 0)

                                        print(minutes_check)
                                        print('zone 3')
                                        if int(minutes_check) >60:
                                            print('zone 4')
                                            Entity.objects.filter(id=entity.id).update(end_datetime=None)
                                            set_device_temperature_for_manual_mode(entity, str(constants.DEFAULT_TEMP))
                            else:
                                if current_ctt is not constants.DEFAULT_TEMP:
                                    entity.end_datetime=None
                                    entity.save()
                                    set_device_temperature_for_manual_mode(entity, str(constants.DEFAULT_TEMP))
                    else:
                        for queue in today_queues:
                            event_ctt=queue.activity_schedule.current_ctt
                            print('event ctt')
                            print(event_ctt)
                            
                            device_ctt=get_ctt_device(entity)
                            print('device_ctt')
                            print(device_ctt)
                            if device_ctt:
                                if device_ctt is not event_ctt:
                                    set_device_temperature_for_manual_mode(entity, str(event_ctt))
                                    entity.end_datetime=None
                                    entity.save()
                                    
                            
            except Exception as e:
                print(e)       
        print('-----------End time '+  str(date_time.datetime.now()) + '------------')
    except Exception as e:
        print(e)

# this function used for when event is running add every minutes in table and after 15 minutes \
# save temperature in table 
# 
def add_minutes_and_temperature_in_queue(activity_queue):
    try:
        print(type(activity_queue.minutes))
        if activity_queue.minutes is None or activity_queue.minutes is 0:
            activity_queue.minutes=0
            activity_queue.minutes +=1
            current_temperature=HypernetPostData.objects.filter(device_id=activity_queue.primary_entity).latest('timestamp')
            activity_queue.temperature=current_temperature.active_score
            activity_queue.save()
        else:

            activity_queue.minutes +=1
            activity_queue.save()
    except Exception as e:
        print(e)

def temperature_moniter_after_15_min(activity_queue):
    current_time_temperature=HypernetPostData.objects.filter(device_id=activity_queue.primary_entity).latest('timestamp')
    minutes_mod=int(activity_queue.minutes) % 15
    if minutes_mod ==0:
        temperatue_after_15_min=int(current_time_temperature.active_score) - int(activity_queue.temperature)
        if int(activity_queue.temperature) is not 0:
            if temperatue_after_15_min <5:
                try:
                    queryset=HypernetNotification.objects.filter(value=4,description=str(activity_queue.id)).latest('timestamp')
                    queryset.delete()
                except:
                    
                    user = User.objects.get(id=activity_queue.activity_schedule.modified_by.id)
                    event_type=enum.get_event_type_mode(event_types=int(activity_queue.activity_schedule.action_items))

                    send_notification_violations(
                                    None, driver_id=None,value=4,
                                    customer_id=activity_queue.customer.id,
                                    module_id=activity_queue.module.id,description=str(activity_queue.id),
                                    title="Your {} is not properly heating up for {} {}".format(activity_queue.primary_entity.name,event_type,activity_queue.activity_schedule.activity_route),
                                    users_list=[user])
                return False # change True to False 
            else:
                activity_queue.temperature=current_time_temperature.active_score
                activity_queue.save()
                return False
        else:
            activity_queue.temperature=current_time_temperature.active_score
            activity_queue.save()
            return False

    else:
        return False    

def check_desired_temperature(activity_queue):
    try:
        print('zone 1')
        current_time_temperature=HypernetPostData.objects.filter(device_id=activity_queue.primary_entity).latest('timestamp')
        difference_in_temperature=int(current_time_temperature.ctt) - int(current_time_temperature.active_score)
        print(difference_in_temperature,'difference in temperature')
        if difference_in_temperature > 5:
            try:
                queryset=HypernetNotification.objects.filter(value=3,description=str(activity_queue.id)).latest('timestamp')
                activity = util_create_activity(activity_queue, None, IopOptionsEnums.IOP_SCHEDULE_FAILED, None)
                activity.save()
                repeated_event=check_repeated_event(activity_queue)
                if repeated_event:
                    add_new_schedule_event(activity_queue)
                activity_queue.activity_schedule.schedule_activity_status = Options.objects.get(id=OptionsEnum.INACTIVE)
                activity_queue.activity_schedule.save()
                activity_queue.delete()
                return True
            except Exception as e:
                user = User.objects.get(id=activity_queue.activity_schedule.modified_by.id)
                event_type=enum.get_event_type_mode(event_types=int(activity_queue.activity_schedule.action_items))
                send_notification_violations(
                            None, driver_id=None,value=3,
                            customer_id=activity_queue.customer.id,
                            module_id=activity_queue.module.id,description=str(activity_queue.id),
                            title="Your time of {} {} has arrived for {}  but the appliance is not ready yet.".format(event_type,activity_queue.activity_schedule.activity_route.lower(),activity_queue.primary_entity.name),
                            users_list=[user])
                activity = util_create_activity(activity_queue, None, IopOptionsEnums.IOP_SCHEDULE_FAILED, None)
                activity_queue.activity_schedule.schedule_activity_status = Options.objects.get(id=OptionsEnum.INACTIVE)
                activity_queue.activity_schedule.save()
                activity_queue.delete()
                activity.save()
                return True
                
    
        return False
    except Exception as e:
        print(e)


def check_offline_status(activiy_queue):
    try:     
        current_datetime = date_time.datetime.now()
        queryset=HypernetNotification.objects.filter(value=activiy_queue.id).latest('timestamp')
        print('zone 1 for check offline status')
        total_mintus = (activiy_queue.activity_datetime - current_datetime.replace(
                tzinfo=timezone.utc)).total_seconds()  # Check how much time remaning for queue to execute
        minutes_check = round(total_mintus / 60, 0)
        print(minutes_check)
        if minutes_check <= 1:
            activity = util_create_activity(activiy_queue, None, IopOptionsEnums.IOP_SCHEDULE_SKIPPED, None)
            activity.save()
            repeated_event=check_repeated_event(activiy_queue)
            if repeated_event:
                add_new_schedule_event(activiy_queue)
                
            activiy_queue.activity_schedule.schedule_activity_status = Options.objects.get(id=OptionsEnum.INACTIVE)  
            activiy_queue.activity_schedule.save()
            activiy_queue.delete()
        else:
            check_retry=check_activity_retrying(activiy_queue)
            print(check_retry)
            if check_retry is  False:
                activity = util_create_activity(activiy_queue, None, IopOptionsEnums.IOP_SCHEDULE_RETRYING, None)
                activity.save()

    except Exception as e:
        print(e)
        
        ready_tag=check_ready_tag(activiy_queue)
        if ready_tag:
            check_retry=check_activity_retrying(activiy_queue)
            ready_tag=check_ready_tag(activiy_queue)
            print(ready_tag,'ready tag for offline ')
            if check_retry is False:
                user = User.objects.get(id=activiy_queue.activity_schedule.modified_by.id)
                print('here in error notification ')
                event_type=""
                event_type=enum.get_event_type_mode(event_types=int(activiy_queue.activity_schedule.action_items))
                
                
                message = activiy_queue.activity_datetime
                send_notification_violations(
                            None, driver_id=None,value=activiy_queue.id,type_id=3,
                            customer_id=activiy_queue.customer.id,
                            module_id=activiy_queue.module.id,description=str(message),
                            title="Your {} will not execute {} {} at @time due to offline status.".format(activiy_queue.primary_entity.name,event_type,activiy_queue.activity_schedule.activity_route.lower()),
                            # title='Your "'+ activiy_queue.primary_entity.name +'" will not execute "'+ event_type +'" at @time due to fault mode.',
                            users_list=[user])
                
                activity = util_create_activity(activiy_queue, None, IopOptionsEnums.IOP_SCHEDULE_RETRYING, None)
                activity.save()
            
def error_execution_event(activiy_queue,temperature_chs,buffer,error_value):
    try:     
        queryset=HypernetNotification.objects.filter(value=activiy_queue.id).latest('timestamp')
        print(queryset,'hypernetnotification')
        print('here in error')
        print(buffer,'buffer value')
        if buffer <= 1:
            print('when buffer is less than 1')
            if  temperature_chs is 5 or error_value is not 0 :
                
                activity = util_create_activity(activiy_queue, None, IopOptionsEnums.IOP_SCHEDULE_FAILED, None)
                activity.save()
            else:
                activity = util_create_activity(activiy_queue, None, IopOptionsEnums.IOP_SCHEDULE_SKIPPED, None)
                activity.save()
            repeated_event=check_repeated_event(activiy_queue)
            if repeated_event:
                add_new_schedule_event(activiy_queue)
            activiy_queue.activity_schedule.schedule_activity_status = Options.objects.get(id=OptionsEnum.INACTIVE)
            activiy_queue.activity_schedule.save() 
            activiy_queue.delete()
        else:
            check_retry=check_activity_retrying(activiy_queue)
            print(check_retry)
            if check_retry is  False:
                activity = util_create_activity(activiy_queue, None, IopOptionsEnums.IOP_SCHEDULE_RETRYING, None)
                activity.save()


    except Exception as e:
        print(e)
        
        ready_tag=check_ready_tag(activiy_queue)
        if ready_tag:
            check_retry=check_activity_retrying(activiy_queue)
            print(ready_tag,'ready_tag for error')
            if check_retry is False:
                user = User.objects.get(id=activiy_queue.activity_schedule.modified_by.id)
                print('here in error notification ')
                event_type=enum.get_event_type_mode(event_types=int(activiy_queue.activity_schedule.action_items))
                print(event_type)        
                mode_value=enum.get_chs_mode(temperature_chs)
                message = activiy_queue.activity_datetime
                send_notification_violations(
                            None, driver_id=None,value=activiy_queue.id,type_id=3,
                            customer_id=activiy_queue.customer.id,
                            module_id=activiy_queue.module.id,description=str(message),
                            title="Your {} will not execute {} {} at @time due to {} mode.".format(activiy_queue.primary_entity.name,event_type,activiy_queue.activity_schedule.activity_route.lower(),mode_value),
                            # title="Your '"+ activiy_queue.primary_entity.name  +"' will not execute '"+ event_type + "' at @time due to fault mode.",
                            users_list=[user])
                
                
                activity = util_create_activity(activiy_queue, None, IopOptionsEnums.IOP_SCHEDULE_RETRYING, None)
                print(activity)
                activity.save()

'Sets temperature of water heater to desired temperature by calculating ttr. Sends notification to user and creates activity'
def create_appliance_activity(request=None):
    try:
        print('-----------Sactiviy_queuetart time '+  str(date_time.datetime.now()) + '------------')
        current_datetime = date_time.datetime.now()

        # Either we can do this, or t_q.activity_datetime.replace(tzinfo=None). To make append timezone info with datetimes or make them naive, both must be same
        current_datetime = current_datetime.replace(tzinfo=timezone.utc)
        today = str(current_datetime.weekday())  # Get weekday from current datetime

        # Fetch today queues, where activity_datetime is start_datetime of activity, queue should be off. For explaination, consult iof/models.py
        today_queues = ActivityQueue.objects.filter(day_of_week=today, activity_datetime__date=current_datetime.date(),
                                                    is_on=False, is_off=False, module=ModuleEnum.IOP,
                                                    temp_set=False, suspend=False).order_by('activity_datetime')

        # sort queues by their activity_datetime.

        if today_queues:

            for t_q in today_queues:


                # calculate ttr of water_heater(t_q.primary_entity), here t1 will be the current heater temperature and t2 will be caculated based on t_1 duration and desired temperature
                ttr, t2 = calculcate_ttr(t_q.primary_entity,
                                        t_q.activity_schedule.action_items,
                                        duration=t_q.activity_schedule.notes)
                print("TTR: ", ttr)
                # ttr >= 0 means that heater is already at the state where user wants it to be.
                if ttr >= 0:
                    print('in ttr>=0 If statement')
                    # subtract ttr from queue time (activity time).
                    ttr_time = t_q.activity_datetime - timedelta(minutes=ttr)

                    # print('activity start time:     ', t_q.activity_datetime)
                    # print('ttr time calculated:     ', ttr_time)
                    # print('difference;     ', t_q.activity_datetime - timedelta(minutes=ttr))
                    # print('current datetime;     ', current_datetime)
                    # There will always be one running queue. This whole process is to turn water heater to desired temperature
                    # and send notification for t_q. The query below checks if there are any already running queues/schedules

                    active_queues = ActivityQueue.objects.filter(primary_entity=t_q.primary_entity,
                                                                is_on=True, is_off=False).exclude(id=t_q.id)

                    # when ttr_time <= curent_datetime that means that it's now time to set heater to desired temperature.
                    # t_q.primary_entity. temperature is False: checks if sleep mode is not active. When sleep mode becomes active,
                    # the temperature field of entity is set to True.

                    if ttr_time <= current_datetime and t_q.primary_entity.temperature is False:

                        #device is in fault mode then notify user
                       
                        check_error=appliance_error(t_q.primary_entity)
                        print(check_error,'check error')
                        error=check_error.get('error',False)
                        try:
                            online_status_device = LogisticAggregations.objects.get(device=t_q.primary_entity).online_status
                        except Exception as e:
                            print(e)
                            online_status_device = False
                        if online_status_device:
                            buffer = (t_q.activity_datetime - current_datetime.replace(
                                tzinfo=timezone.utc)).total_seconds()  # change to timezone.now()
                            buffer = round(buffer / 60, 0)
                            print("BUFFER: ", buffer)
                            if error:
                                temperature_chs=check_error.get('chs',0)
                                error_value=check_error.get('error_score',0)
                                error_execution_event(t_q,temperature_chs,buffer,error_value)
                            else:
                                add_minutes_and_temperature_in_queue(t_q)
                                temperature_moniter=temperature_moniter_after_15_min(t_q)
                                if temperature_moniter is False:
                                    if active_queues:
                                        for queue in active_queues:
                                            queue.is_off = True  # Mark the already running queue off
                                            # repeated_event=check_repeated_event(queue)
                                            # if repeated_event:
                                            #     add_new_schedule_event(queue)
                                            #shift_schedule_to_next_day(queue, current_datetime)
                                            activities = Activity.objects.filter(activity_schedule_id=queue.activity_schedule.id)

                                            # If the already runnig schedule was in ready state --> Mark it cancelled
                                            activities.filter(activity_status_id=IopOptionsEnums.IOP_SCHEDULE_READY).update(
                                                activity_status_id=IopOptionsEnums.IOP_SCHEDULE_CANCELLED)
                                            # If the already runnig schedule was in in use state --> Mark it completed
                                            activities.filter(activity_status_id=IopOptionsEnums.IOP_SCHEDULE_IN_USE).update(
                                                activity_status_id=IopOptionsEnums.IOP_SCHEDULE_COMPLETED)
                                            activities.filter(activity_status_id=IopOptionsEnums.IOP_SCHEDULE_RETRYING).update(
                                                activity_status_id=IopOptionsEnums.IOP_SCHEDULE_SKIPPED)
                                            
                                        
                                            queue.delete()  # delete queue
                                    
                            
                                    t_q.temp_set = True  # This field is to mark that for this queue, we have set the heater to it's desired temperature
                                    ctt=get_ctt_value(t_q)
                                    set_device_temperature(t_q, str(ctt))
                                    # Cloud to device message for setting water heater temperature
                                    t_q.save()  # Save the queue

                        else:
                            check_offline_status(t_q)
                else:  # This else is executed if water heater is already at the desired state/temperature, for that we will directly send notification to user that their activity has started/heater is now ready

                    print('in ttr else statement')

                    

                    check_error=appliance_error(t_q.primary_entity)
                    error=check_error.get('error',False)
                    print(check_error,'check error')
                    try:
                        online_status_device = LogisticAggregations.objects.get(device=t_q.primary_entity).online_status
                    except Exception as e:
                        print(e)
                        online_status_device = False
                    if online_status_device:
                        # Check how much time remaning for queue to execute
                        buffer = (t_q.activity_datetime - current_datetime.replace(
                                tzinfo=timezone.utc)).total_seconds()  # change to timezone.now()
                        buffer = round(buffer / 60, 0)
                        print("BUFFER: ", buffer)
                        if error:
                            temperature_chs=check_error.get('chs',0)
                            error_value=check_error.get('error_score',0)
                            error_execution_event(t_q,temperature_chs,buffer,error_value)# check for error and chs state
                        else:
                            change_retrying_state(t_q)
                            add_minutes_and_temperature_in_queue(t_q)
                            temperature_moniter=temperature_moniter_after_15_min(t_q)
                            if temperature_moniter is False:
                                if buffer <= 1 and t_q.primary_entity.temperature is False:
                                    desired_temperature_check=check_desired_temperature(t_q)
                                    if desired_temperature_check is False:
                                        ctt=get_ctt_value(t_q)
                                        set_device_temperature(t_q, str(ctt)) if not t_q.temp_set else False
                                        try:
                                            user = User.objects.get(
                                                id=t_q.activity_schedule.modified_by.id)  # Query user who made schedule

                                            temp_name = 'Hot'
                                            for name, temp_range in constants.water_ranges.items():  # fetch label name agaisnt the tempeature saved in db
                                                if int(t_q.activity_schedule.action_items) in temp_range:
                                                    temp_name = name
                                            send_notification_violations(
                                                None, driver_id=None,
                                                customer_id=t_q.customer.id,
                                                module_id=t_q.module.id,
                                                title="Your {}  in {} is now ready.".format(temp_name, t_q.primary_entity.name),
                                                users_list=[user])
                                            repeated_event=check_repeated_event(t_q)
                                            if repeated_event:
                                                add_new_schedule_event(t_q)

                                        except User.DoesNotExist:
                                            pass

                                        t_q.is_on = True
                                        t_q.temp_set = True
                                        t_q.save()
                                        ActivitySchedule.objects.filter(id=int(t_q.activity_schedule.id)).update(suggestion=False)

                                        activity = util_create_activity(t_q, None, IopOptionsEnums.IOP_SCHEDULE_READY, None)
                                        activity.save()
                        
                    else:
                        check_offline_status(t_q)
        # This util is for querying queues whose temperature have been set (temp_set = True) and we now have to wait for their schedule time on which notification will be sent to user that their schedule has started
        ttr_set_queues = ActivityQueue.objects.filter(day_of_week=today, activity_datetime__date=current_datetime.date(),
                                                    is_on=False, is_off=False, module=ModuleEnum.IOP,
                                                    temp_set=True, suspend=False).order_by('activity_datetime')

        print('ttr_queue count    ', ttr_set_queues.count())

        if ttr_set_queues:

            for t_q in ttr_set_queues:
                check_error=appliance_error(t_q.primary_entity)
                print(check_error,'check error')
                error=check_error.get('error',False)
                try:
                    online_status_device = LogisticAggregations.objects.get(device=t_q.primary_entity).online_status
                except Exception as e:
                    print(e)
                    online_status_device = False
                if online_status_device:
                    print('ttr_queue    ', t_q)

                    buffer = (t_q.activity_datetime - current_datetime.replace(
                        tzinfo=timezone.utc)).total_seconds()  # Check how much time remaning for queue to execute
                    buffer = round(buffer / 60, 0)
                    print("BUFFER IN TTR SET QUEUES: ", buffer)
                   
                    if error:
                        temperature_chs=check_error.get('chs',0)
                        error_value=check_error.get('error_score',0)
                        error_execution_event(t_q,temperature_chs,buffer,error_value)# check for error and chs state
                    else:
                        change_retrying_state(t_q)
                        add_minutes_and_temperature_in_queue(t_q)
                        temperature_moniter=temperature_moniter_after_15_min(t_q)
                        if temperature_moniter is False:
                            if buffer <= 1 and t_q.primary_entity.temperature is False:  # <=1 can be <=0. Can be changed. Just keeping buffer of 1 minute
                                desired_temperature_check=check_desired_temperature(t_q)
                                if desired_temperature_check is False:    
                                    active_queues = ActivityQueue.objects.filter(primary_entity=t_q.primary_entity,
                                                                                is_on=True, is_off=False).exclude(
                                        id=t_q.id)  # Similar process repeated as above
                                    print("INSIDE BUFFER <=1 check")
                                    if active_queues:
                                        for queue in active_queues:
                                            queue.is_off = True
                                            # repeated_event=check_repeated_event(queue)
                                            # if repeated_event:
                                            #     add_new_schedule_event(queue)
                                            #shift_schedule_to_next_day(queue, current_datetime)
                                            
                                            activities = Activity.objects.filter(activity_schedule_id=queue.activity_schedule.id)

                                            activities.filter(activity_status_id=IopOptionsEnums.IOP_SCHEDULE_READY).update(
                                                activity_status_id=IopOptionsEnums.IOP_SCHEDULE_CANCELLED)

                                            activities.filter(activity_status_id=IopOptionsEnums.IOP_SCHEDULE_IN_USE).update(
                                                activity_status_id=IopOptionsEnums.IOP_SCHEDULE_COMPLETED)
                                            activities.filter(activity_status_id=IopOptionsEnums.IOP_SCHEDULE_RETRYING).update(
                                                activity_status_id=IopOptionsEnums.IOP_SCHEDULE_SKIPPED)
                                            
                                            queue.delete()
                                        
                                    t_q.is_on = True
                                    t_q.save()

                                    try:
                                        user = User.objects.get(id=t_q.activity_schedule.modified_by.id)
                                        temp_name = 'Hot'
                                        for name, temp_range in constants.water_ranges.items():
                                            if int(t_q.activity_schedule.action_items) in temp_range:
                                                temp_name = name
                                        send_notification_violations(None, driver_id=None,
                                                                    customer_id=t_q.customer.id, module_id=t_q.module.id,
                                                                    title="Your {} in {} is now ready.".format(
                                                                        temp_name, t_q.primary_entity.name,
                                                                    ), users_list=[user])
                                        repeated_event=check_repeated_event(t_q)
                                        if repeated_event:
                                            add_new_schedule_event(t_q)

                                    except User.DoesNotExist:
                                        pass
                                        # user = None
                                    print("Above setting it ready")
                                    # Creating Ready activity, this is created when notifiation is sent to the user
                                    ActivitySchedule.objects.filter(id=int(t_q.activity_schedule.id)).update(suggestion=False)
                                    activity = util_create_activity(t_q, None, IopOptionsEnums.IOP_SCHEDULE_READY, None)
                                    activity.save()

                else:
                    check_offline_status(t_q)
        print('-----------End time '+  str(date_time.datetime.now()) + '------------')
    except Exception as e:
        print(e)

'Cron for completing an activity. changes states of schedules i.e. Ready --> Cancelled, Ready --> In Use.  ' \
'In Use --> Completed. Also shifts the schedules to next weekday/ marks them inactive.'
def updated_complete_activity(request=None):
    print('-----------Start time '+  str(date_time.datetime.now()) + '------------')
    ents = Entity.objects.filter(module_id=ModuleEnum.IOP,
                                 type_id=DeviceTypeEntityEnum.IOP_DEVICE,
                                 status_id=OptionsEnum.ACTIVE, temperature=False)

    for ent in ents:
        print("ENT : ", ent.id)
        current_datetime = date_time.datetime.now()
        current_datetime = current_datetime.replace(tzinfo=None, second=0, microsecond=0)
        print("CURRENT DATE TIME", current_datetime.date())

        on_queues = ActivityQueue.objects.filter(is_on=True, temp_set=True,
                                                 is_off=False, module=ModuleEnum.IOP,
                                                 suspend=False, primary_entity=ent,
                                                 activity_datetime__date__lte=current_datetime.date()).order_by(
            'activity_datetime')
        # print("Queued devices found !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ")

        # print("SQL QUERY: ", on_queues.query)

        for o_q in on_queues:
            print("===================================================================================")
            print("entity:  ", ent.id)
            try:
                obj = Activity.objects.get(activity_schedule_id=o_q.activity_schedule.id)
                print("QUEUE ITEM: ", o_q)
                if obj.activity_status.id == IopOptionsEnums.IOP_SCHEDULE_READY:
                    flag = new_detect_drop_in_temperature(o_q.primary_entity)
                    print('DROP IN TEMMPERATURE IN SCHEDULE READY ', flag)
                    if flag is True:
                        obj.activity_status = Options.objects.get(id=IopOptionsEnums.IOP_SCHEDULE_IN_USE)
                        obj.save()
                    else:

                        activity_time = obj.activity_schedule.new_end_dt.replace(tzinfo=None, second=0, microsecond=0)
                        print('one hour check  ', (current_datetime - activity_time).total_seconds() / 60)

                        if round((current_datetime - activity_time).total_seconds() / 60) >= 60:
                            print('In ROUND Check')
                            obj.activity_status = Options.objects.get(id=IopOptionsEnums.IOP_SCHEDULE_CANCELLED)
                            obj.save()

                            # shift_schedule_to_next_day(o_q, current_datetime)
                            primary_entity = o_q.primary_entity
                            o_q.delete()
                            shift_to_normal_temp(entity=primary_entity, current_datetime=current_datetime)
                            print("DONE !!!!!!!!!!")
                        else:
                            pass

                elif obj.activity_status.id == IopOptionsEnums.IOP_SCHEDULE_IN_USE:
                    flag = new_detect_drop_in_temperature(o_q.primary_entity)
                    print('DROP IN TEMPERATURE: ', flag)

                    if flag is False:
                        activity_time = obj.activity_schedule.new_end_dt.replace(tzinfo=None, second=0, microsecond=0)
                        buffer = ((activity_time - current_datetime).total_seconds() / 60)
                        if round(buffer) <= 0:
                            print('In ROUND Check')
                            obj.activity_status = Options.objects.get(id=IopOptionsEnums.IOP_SCHEDULE_COMPLETED)
                            obj.save()
                            #shift_schedule_to_next_day(o_q, current_datetime)
                            primary_entity = o_q.primary_entity
                            o_q.delete()
                            shift_to_normal_temp(entity=primary_entity, current_datetime=current_datetime)
                    else:
                        pass
                
                
                print("===================================================================================")
            except Exception as e:
                print(e)
                pass
    check_if_any_abnormality()
    print('-----------Start time ' +  str(date_time.datetime.now()) + '------------')


# Trigger for creating queue of schedule. Whenever an object is saved in Activity Schedule, this trigger will create it's corresponding queue
@receiver(post_save, sender=ActivitySchedule)
def trigger_for_iop_queues(sender, instance, **kwargs):
    print('Receiver working')
    try:
        if time.tzname[0] == 'UTC':
            current_datetime = date_time.datetime.now()
        else:
            current_datetime = date_time.datetime.now()

        today = current_datetime.weekday()  # change to timezone.now()
        today = str(today)

        # Checking if schedule is active and it's type is any type other than sleep mode because for sleep mode no queue is created
        if instance.module.id == ModuleEnum.IOP and \
                        instance.schedule_activity_status.id == OptionsEnum.ACTIVE and \
                        instance.activity_type.id in [IopOptionsEnums.IOP_QUICK_SCHEDULE, IopOptionsEnums.IOP_USE_NOW,
                                                      IopOptionsEnums.IOP_SCHEDULE_ON_DEMAND,
                                                      IopOptionsEnums.IOP_SCHEDULE_DAILY]:
            # instance.u_days_list == today and \
            # instance.start_date == current_datetime.date() and \


            # This try block updates already created queue with the updated datetimes in activity schedule. For example if a schedule is shifted and
            # it's datetime have been updated
            try:
                q = ActivityQueue.objects.get(activity_schedule_id=instance.id)
                if q.is_on is False and q.is_off is False:
                    q.activity_datetime = parse(str(instance.start_date) + ' ' + str(instance.u_activity_start_time))
                    q.activity_end_datetime = parse(str(instance.end_date) + ' ' + str(instance.u_activity_end_time))
                    q.temp_set = False  # Setting this flag to False because if a queue that has set water heater to desired temperature can be modified. (It's time can be modified). It means it will now execute and set water heater tempeature at a differnt time
                    q.save()
            except:

                # Additional precautional check. The try block will work for one object, if due to any issue, multiple queues are created for
                # a single schedule, those multiple queues will be deleted.
                multiple_queues = ActivityQueue.objects.filter(activity_schedule_id=instance.id)

                if len(multiple_queues) > 1:
                    print('Multiple Queues with same schedule_id exist')
                    for m_q in multiple_queues:
                        print('Multiple queue being deleted')
                        if instance.u_activity_start_time != m_q.u_activity_start_time and instance.u_activity_end_time != m_q.u_activity_end_time:
                            m_q.delete()

                else:
                    # Creating queue if sleep mode is not active.
                    if instance.primary_entity.temperature is False:  # and instance.u_days_list == today and instance.start_date == current_datetime.date():
                        start_datetime = parse(str(instance.start_date) + ' ' + str(instance.u_activity_start_time))
                        end_datetime = parse(str(instance.end_date) + ' ' + str(instance.u_activity_end_time))

                        queue = ActivityQueue()
                        queue.activity_schedule_id = instance.id
                        queue.activity_datetime = start_datetime
                        queue.activity_end_datetime = end_datetime
                        queue.primary_entity_id = instance.primary_entity_id
                        queue.user = instance.modified_by
                        queue.customer_id = instance.customer_id
                        queue.module_id = instance.module_id
                        queue.action_items = instance.action_items
                        queue.day_of_week = instance.u_days_list
                        queue.save()

    except:
        pass


'''
This is the cronjob that will create queue for the next day provided that the queue doesnot exist. This cron will run at Midnight (0:00) every day and create queue for the next day.
This cron mainly create queues for Recurring and Quick Schedules when they will be executed for next weekday. The trigger works fine when
queue is created one time. For the next time, queue will be created by this cronjob
'''


def make_iop_queue():
    
    current_datetime = date_time.datetime.now()
    print('-----------Start time '+ str(current_datetime)+ '------------')

    today = str(current_datetime.weekday())  # change to timezone.now()
    print("today:   ", today)

    schedule = ActivitySchedule.objects.filter(u_days_list=today, module_id=ModuleEnum.IOP,
                                               schedule_activity_status_id=OptionsEnum.ACTIVE,
                                               activity_type_id__in=[
                                                   IopOptionsEnums.IOP_QUICK_SCHEDULE,
                                                   IopOptionsEnums.IOP_SCHEDULE_DAILY]
                                               )

    for s in schedule:
        try:
            q = ActivityQueue.objects.get(activity_schedule=s)
            if q.is_on is False and q.is_off is False:
                q.activity_datetime = parse(str(s.start_date) + ' ' + str(s.u_activity_start_time))
                q.activity_end_datetime = parse(str(s.end_date) + ' ' + str(s.u_activity_end_time))
                q.save()
            continue
        except Exception as e:
            print('make Iop Queue Execption\n')
            print(e)
            print("id   ", s.id)
            if s.u_days_list == today and s.start_date == current_datetime.date() and s.primary_entity.temperature is False:  # changed from current_datetime.date().today() to current_datetime.date(_
                print("in If Main")
                queue = ActivityQueue()
                queue.activity_schedule_id = s.id
                queue.activity_datetime = s.new_start_dt
                queue.activity_end_datetime = s.new_end_dt
                queue.primary_entity_id = s.primary_entity_id
                queue.user = s.modified_by
                queue.customer_id = s.customer_id
                queue.module_id = s.module_id
                queue.action_items = s.action_items
                queue.day_of_week = s.u_days_list
                queue.save()

    print('Job completed at: ' + str(date_time.datetime.now()))
    print('-----------End time '+ str(current_datetime)+ '------------')

def check_entity_temperature():
    try:
        entities=Entity.objects.filter(module_id=ModuleEnum.IOP,
                                    type_id=DeviceTypeEntityEnum.IOP_DEVICE,
                                    status_id=OptionsEnum.ACTIVE, temperature=True)
        
        for entity in entities:
            
            sleep_mode=ActivitySchedule.objects.filter(primary_entity=entity,schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                    activity_type_id__in=[IopOptionsEnums.IOP_SLEEP_MODE,
                                                                        IopOptionsEnums.RECURRING_SLEEP_MODE],
                                                    sleep_mode=True)
            if len(sleep_mode) == 0:
                print("check temp false")
                entity.temperature=False
                entity.save()
    except Exception as e:
        print(e)
            

def check_sleep_mode_in_schedule(activity_schedule):
    date_now=date_time.datetime.now()
    # current_datetime = date_now + datetime.timedelta(days=0)
    today=date_now.replace(second=0, microsecond=0)
    current_date=today.date()
    print(current_date)

    if activity_schedule.sleep_mode or activity_schedule.activity_type_id==IopOptionsEnums.RECURRING_SLEEP_MODE:
        if activity_schedule.validity_date:
            if activity_schedule.validity_date == current_date :
                return False
            return True 
        else:
            return False
    else:
        return False

def send_notification_sleep_mode_if_error(s_m,temperature_chs):
    try:
        queryset=HypernetNotification.objects.filter(value=s_m.id).latest('timestamp')
    except Exception as e:
        print(e)
        user = UserEntityAssignment.objects.filter(device=s_m.primary_entity,
                                                            # Query all users of the appliance
                                                            status_id=OptionsEnum.ACTIVE).values_list('user_id')

        mode_value=enum.get_chs_mode(temperature_chs)
        title = "Your {} will not execute sleep mode at @time due to {} mode".format(
                        s_m.primary_entity.name,mode_value)
        users = User.objects.filter(id__in=user)
        
        message = s_m.new_start_dt
        send_notification_violations(None, driver_id=None,type_id=3,description=str(message),
                                    customer_id=s_m.customer.id, module_id=s_m.module.id,
                                    title=title, users_list=users,value=s_m.id)

def add_sleep_mode_in_schedule(schedule):
    try:
        print(schedule.start_date,'sta')
        date_now=date_time.datetime.now()
  
        today=date_now.replace(second=0, microsecond=0)
        current_date=today.date()
        print(current_date)
        if schedule.start_date == current_date:
            new_date = schedule.start_date + date_time.timedelta(days=7)
        else:
            new_date=schedule.start_date
            
        print(new_date)
        print(new_date,'new date')
        add_schedule(schedule,new_date) 
    except Exception as e:
        print(e)

'''
Cron for running and ending sleep mode. Also shifts the sleep mode to next weekday/ marks it inactive depending on the type of schedule. 
'''


def check_sleep_mode(request=None):
    # Querying all active sleep modes.
    print('-----------Start time '+  str(date_time.datetime.now()) + '------------')
    sleep_mode = ActivitySchedule.objects.filter(schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                 activity_type_id__in=[IopOptionsEnums.IOP_SLEEP_MODE,
                                                                       IopOptionsEnums.RECURRING_SLEEP_MODE],
                                                 sleep_mode=False)

    current_datetime = date_time.datetime.now()

    print('sleep mode count:    ', sleep_mode.count())
    try:
        for s_m in sleep_mode:
            start_dt = s_m.new_start_dt.replace(tzinfo=None)
            buffer = (
                start_dt - current_datetime).total_seconds()  # Checking if datetime at which sleep mode will be executed is equal to current time
            
            check_error=appliance_error(s_m.primary_entity)
            error=check_error.get('error',False)
            print(check_error,'check error')
            if error:
                temperature_chs=check_error.get('chs',0)
                send_notification_sleep_mode_if_error(s_m,temperature_chs)
            else:
                
                if buffer <= 0:
                    print('active sleep mode:   ', s_m.primary_entity_id)
                    s_m.primary_entity.temperature = True  # Setting this flag in entity indicates that sleep mode against this appliance is now active.

                    s_m.primary_entity.weight = s_m.id  # weight to keep track of which sleep mode is currently active.
                    # Reason to use this field: Difficuilt to distignuish
                    # if there  are multiple sleep modes with same time ranges. Update: This check was set due to original requiremnets. Safe to remove since requiremnts were changed


                    s_m.primary_entity.save()
                    s_m.sleep_mode = True  # Redundant check. This was set when there were mutiple running sleep modes (original requirements). Can be removed after requirements were changed.
                    s_m.save()
                    suspend_overlapping_schedules(s_m)  # Shift/ mark schedule inactive

                    set_device_temperature(s_m, str(
                        constants.SLEEP_MODE_TEMP))  # Set temperature of device to Sleep mode temperature

                    user = UserEntityAssignment.objects.filter(device=s_m.primary_entity,
                                                            # Query all users of the appliance
                                                            status_id=OptionsEnum.ACTIVE).values_list('user_id')

                    name = s_m.modified_by.first_name + ' ' + s_m.modified_by.last_name if s_m.modified_by.last_name else s_m.modified_by.first_name

                    title = "Sleep mode scheduled by {} on appliance {} is now active. Schedules currently running have been stopped.".format(
                        name, s_m.primary_entity.name)
                    users = User.objects.filter(id__in=user)
                    send_notification_violations(None, driver_id=None,
                                                customer_id=s_m.customer.id, module_id=s_m.module.id,
                                                title=title, users_list=users)

            # Querying Active (Running) sleep modes
        sleep_mode = ActivitySchedule.objects.filter(schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                     activity_type_id__in=[IopOptionsEnums.IOP_SLEEP_MODE,
                                                                           IopOptionsEnums.RECURRING_SLEEP_MODE],
                                                     sleep_mode=True)

        print('running sleep mode count:    ', sleep_mode.count())
        for s_m in sleep_mode:
            end_dt = s_m.new_end_dt.replace(tzinfo=None)
            buffer = (end_dt - current_datetime).total_seconds()  # Check if sleep mode is about to end

            print("sleep mode buffer:   ", buffer)
            print('active sleep mode:   ', s_m.primary_entity_id)

            if buffer <= 0:
                
                if s_m.activity_type.id == IopOptionsEnums.IOP_SLEEP_MODE:  # if it's a simple sleep mode, it will be marked inactive
                    s_m.schedule_activity_status = Options.objects.get(id=OptionsEnum.INACTIVE)

                else:  # If it's a recurring sleep mode then it will be shifted to next weekday
                    today = current_datetime.date()  # changed from current_datetime.date().today() to current_datetime.date()

                    if today.weekday() == int(s_m.u_days_list):
                        upcoming_date = today + timedelta(days=7)  # Shifting sleep mode to the next weekday
                    else:
                        upcoming_date = today + date_time.timedelta((int(
                            s_m.u_days_list) - today.weekday()) % 7)  # redundant check, can be removed. In this case the if condition will always be execcuted

                    s_m.start_date = upcoming_date

                    if s_m.multi_days is True:  # Checking if sleep mode spans multiple days
                        s_m.end_date = upcoming_date + timedelta(days=1)

                    else:
                        s_m.end_date = upcoming_date

                    s_m.new_start_dt = parse(str(upcoming_date) + '-' + str(s_m.old_start_dt))
                    s_m.new_end_dt = parse(str(upcoming_date) + '-' + str(s_m.old_end_dt))

                    s_m.u_activity_start_time = s_m.new_start_dt.time()
                    s_m.u_activity_end_time = s_m.new_end_dt.time()
                
                check_sleep=check_sleep_mode_in_schedule(s_m)
                if check_sleep:
                    add_sleep_mode_in_schedule(s_m)
                s_m.sleep_mode = False  # Setting sleep mode flag to false indicating that sleep mode is now over. It was set when there were multiple active/running sleep modes. Can be removed. Redundant check.
                Entity.objects.filter(id=s_m.primary_entity.id).update(temperature= False)
                s_m.primary_entity.temperature = False
                s_m.primary_entity.save()
                s_m.save()
                check_error=appliance_error(s_m.primary_entity)
                error=check_error.get('error',False)
                print(check_error,'check error')
                if error is False:
                    result = set_device_temperature(s_m, str(constants.DEFAULT_TEMP))
                    print("status result:   ", result)
                

                user = UserEntityAssignment.objects.filter(device=s_m.primary_entity,
                                                           # Query all users of the appliance
                                                           status_id=OptionsEnum.ACTIVE).values_list('user_id')
                print("user ", user)

                users = User.objects.filter(id__in=user)
                send_notification_violations(None, driver_id=None,
                                             customer_id=s_m.customer.id, module_id=s_m.module.id,
                                             title="Sleep mode is now inactive."
                                             , users_list=users)


            else:
                s_m.sleep_mode = True  # Redundant check
                s_m.primary_entity.weight = s_m.id  # Redundant check
                s_m.save()
                s_m.primary_entity.save()
        check_entity_temperature() #check entity temperature
    except Exception as e:
        print(e)

    print('Job completed at: ' + str(date_time.datetime.now()))
    print('-----------end time '+  str(date_time.datetime.now()) + '------------')


# @api_view(['GET'])
# @csrf_exempt
def update_trip_status_of_vehicle(truck, lat, lng):
    check, act = check_activity_on_truck(truck)
    try:
        # If on activity then...
        if check:
            # get the territory and check if point lies within the territory or not
            dump = act.activity_end_point
            dump_territory = Assignment.objects.get(child=dump, type_id=DeviceTypeAssignmentEnum.DUMP_ASSIGNMENT).parent
            result = check_if_inside(lat, lng, dump_territory)
            # Is it inside?
            if result:
                # is the trip flag already set?
                if truck.temperature:
                    pass  # do nothing as it is still inside for now
                else:
                    # Set the flag and increment trip for the activity
                    truck.temperature = True
                    truck.save()
                    act.trips += 1
                    # Increment the trip flag for shift as well.
                    check, shift = check_shift_on_truck(truck)
                    if check:
                        shift.trips += 1
                        shift.save()
                        # If no shift then do nothing, can generate notification here however.
            # It is not inside, check flag n set it
            else:
                if truck.temperature:
                    # Set the flag as marked exited from territory
                    truck.temperature = False
                    truck.save()
                else:
                    pass

        # If not on activity then we still have to check em, check via shift.
        else:
            check, shift = check_shift_on_truck(truck)
            # Since khizer assigned the territory to all the trucks i ll fetch the territory from there
            if check:  # on shift then check territory breach
                dump_territory = Assignment.objects.get(parent=truck,
                                                        type_id=DeviceTypeAssignmentEnum.TERRITORY_ASSIGNMENT,
                                                        child__territory_type_id=IOFOptionsEnum.BLUE).child
                result = check_if_inside(lat, lng, dump_territory)
                if result:  # It is inside now check and set flags
                    if truck.temperature:
                        pass  # do nothing as it is still inside for now
                    else:
                        # Set the flag
                        truck.temperature = True
                        truck.save()
                        # Increment the trip flag for shift as well.
                        shift.trips += 1
                        shift.save()
                else:  # It aint inside, now set the flags accordingly
                    if truck.temperature:
                        truck.temperature = False
                        truck.save()
                    else:
                        pass
            else:
                # No shift just let it go
                pass
    except:
        traceback.print_exc()
        pass



def complete_appliance_activity(request=None):
    ents = Entity.objects.filter(module_id=ModuleEnum.IOP, type_id=DeviceTypeEntityEnum.IOP_DEVICE,
                                 status_id=OptionsEnum.ACTIVE, temperature=False)

    for ent in ents:
        on_queues = ActivityQueue.objects.filter(is_on=True, is_off=False, module=ModuleEnum.IOP, suspend=False,
                                                 primary_entity=ent).order_by('activity_datetime')
        users = {}
        if on_queues:
            if time.tzname[0] == 'UTC':
                current_datetime = date_time.datetime.now()
            else:
                current_datetime = date_time.datetime.now()

            for on_q in on_queues:

                off_q = ActivityQueue.objects.filter(is_on=False,
                                                     is_off=False, module=ModuleEnum.IOP, suspend=False,
                                                     primary_entity=on_q.primary_entity).order_by('activity_datetime')

                if off_q:
                    off_q = off_q[0]
                    # for off_q in off_queues:
                    ttr = calculcate_ttr(off_q.primary_entity, off_q.action_items)

                    print('ttr is: ', ttr)
                    ttr_time = off_q.activity_datetime - timedelta(minutes=ttr)

                    print('ttr time: ', ttr_time)
                    # checking if time of the next off_queue that will execute next lies (conflicts) with the time of running queue.
                    if ttr_time <= on_q.activity_datetime or ttr_time < on_q.activity_end_datetime:
                        st_time = off_q.activity_datetime + timedelta(minutes=ttr)  # shift that queue
                        end_time = st_time + timedelta(minutes=float(off_q.activity_schedule.notes))

                        off_q.activity_datetime = st_time
                        off_q.activity_end_datetime = end_time

                        off_q.save()
                        user = User.objects.get(id=off_q.activity_schedule.modified_by.id)

                        if user not in users.keys():  # sending notification only once to every user when there is a delay
                            users[user] = 0

                        if users[user] == 0:
                            # flag = False
                            users[user] = 1
                            check_shift_conflicts_in_queue(off_q, ttr)

                            data = get_latest_value(off_q.primary_entity)

                            temp_name = 'Hot'
                            for name, temp_range in constants.water_ranges.items():
                                if data.active_score in temp_range:
                                    temp_name = name

                            desired_temperature = off_q.activity_schedule.action_items

                            print('desired temp', desired_temperature)
                            print('current temp', data.active_score)

                            for name, temp_range in constants.water_ranges.items():
                                if int(desired_temperature) in temp_range:
                                    dest_temp_name = name

                            if int(desired_temperature) > data.active_score and temp_name != dest_temp_name:
                                text = "Water in {} is now {} due to recent usage. {} is being prepared for you. Open the app to see the delay.".format(
                                    off_q.primary_entity.name, temp_name, dest_temp_name)

                                # else:
                                #    text = "Water in {} is now {} due to recent usage. Water is being prepared for you according to your desired usage. Open the app to see the delay.".format(off_q.primary_entity.name, str(data.active_score))

                                send_notification_violations(None, driver_id=None,
                                                             customer_id=off_q.customer.id, module_id=off_q.module.id,
                                                             title=text, users_list=[user])

                    else:
                        pass

                        # check_shift_conflicts_in_queue(off_q, ttr)

            for o_q in on_queues:

                buffer = (o_q.activity_end_datetime - current_datetime.replace(
                    tzinfo=timezone.utc)).total_seconds()  # change to timezone.now()
                buffer = round(buffer / 60, 0)

                if buffer >= 60:

                    o_q.is_off = True
                    o_q.save()

                    if o_q.activity_schedule.activity_type.id in [IopOptionsEnums.IOP_QUICK_SCHEDULE,
                                                                  IopOptionsEnums.IOP_SCHEDULE_DAILY]:

                        orig_start_time = o_q.activity_schedule.activity_start_time
                        orig_end_time = o_q.activity_schedule.activity_end_time

                        u_start_time = o_q.activity_schedule.u_activity_start_time
                        u_end_time = o_q.activity_schedule.u_activity_end_time

                        days_list = o_q.activity_schedule.days_list
                        u_days_list = o_q.activity_schedule.u_days_list

                        if (u_start_time != orig_start_time) and (u_end_time != orig_end_time):

                            if orig_end_time > orig_start_time:
                                all_schedules = ActivitySchedule.objects.filter(primary_entity_id=o_q.primary_entity.id,
                                                                                u_days_list__in=[days_list],
                                                                                schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                                                suspend_status=False,
                                                                                u_activity_end_time__gt=orig_start_time,
                                                                                u_activity_start_time__lt=orig_end_time,
                                                                                activity_type_id__in=[
                                                                                    IopOptionsEnums.IOP_SCHEDULE_ON_DEMAND,
                                                                                    IopOptionsEnums.IOP_SCHEDULE_DAILY]).order_by(
                                    'u_activity_start_time')

                                all_schs = ActivitySchedule.objects.filter(primary_entity_id=o_q.primary_entity.id,
                                                                           multi_days=True,
                                                                           u_days_list__in=[str(int(days_list) - 1)],
                                                                           # conflict checking where an activity is made after midnight but conflicts to be checked at day before.
                                                                           schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                                           activity_type_id__in=[
                                                                               IopOptionsEnums.IOP_SCHEDULE_ON_DEMAND,
                                                                               IopOptionsEnums.IOP_SCHEDULE_DAILY]).order_by(
                                    'u_activity_start_time')
                                if all_schs:
                                    all_schs = check_conflicts_multi_days(all_schs,
                                                                          o_q.activity_schedule)  # check for conflicts that occur after midnight with the new schedule

                                    all_schedules = all_schedules.union(all_schs)


                            else:  # when end time falls after midnight (next day) and start time on previous day
                                all_schedules = ActivitySchedule.objects.filter(primary_entity_id=o_q.primary_entity.id,
                                                                                u_days_list__in=[days_list],
                                                                                schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                                                suspend_status=False,
                                                                                activity_type_id__in=[
                                                                                    IopOptionsEnums.IOP_SCHEDULE_ON_DEMAND,
                                                                                    IopOptionsEnums.IOP_SCHEDULE_DAILY]).order_by(
                                    'u_activity_start_time')

                                all_schedules = check_conflicts_multi_days(all_schedules, o_q.activity_schedule)

                                a_chs = check_conflicts_days_after(o_q.activity_schedule, days_list)

                                all_schedules = all_schedules.union(a_chs)

                            all_schedules = all_schedules.exclude(pk=o_q.activity_schedule.pk)

                            if len(all_schedules) == 0:
                                o_q.activity_schedule.u_activity_start_time = o_q.activity_schedule.activity_start_time
                                o_q.activity_schedule.u_activity_end_time = o_q.activity_schedule.activity_end_time
                                if o_q.activity_schedule.activity_end_time >= o_q.activity_schedule.activity_start_time:
                                    o_q.activity_schedule.multi_days = False
                                else:
                                    o_q.activity_schedule.multi_days = True

                                o_q.activity_schedule.u_days_list = o_q.activity_schedule.days_list
                                o_q.activity_schedule.save()

                        today = current_datetime.date()  # changed from current_datetime.date().today() to current_datetime.date()

                        if today.weekday() == int(o_q.activity_schedule.u_days_list):
                            upcoming_date = today + timedelta(days=7)
                        else:
                            upcoming_date = today + date_time.timedelta((int(u_days_list) - today.weekday()) % 7)

                        o_q.activity_schedule.start_date = upcoming_date

                        if o_q.activity_schedule.multi_days is True:
                            o_q.activity_schedule.end_date = upcoming_date + timedelta(days=1)

                        else:
                            o_q.activity_schedule.end_date = upcoming_date

                        o_q.save()
                        o_q.activity_schedule.save()


                    else:
                        o_q.activity_schedule.schedule_activity_status = Options.objects.get(id=OptionsEnum.INACTIVE)
                        o_q.activity_schedule.save()
                        ActivitySchedule.objects.filter(suspended_by=o_q.activity_schedule).update(suspended_by=None)

                    try:
                        user = User.objects.get(id=o_q.activity_schedule.modified_by.id)

                        send_notification_violations(None, driver_id=None,
                                                     customer_id=o_q.customer.id, module_id=o_q.module.id,
                                                     title="Your schedule is near completion.", users_list=[user])

                    except User.DoesNotExist:
                        user = None

                    try:
                        on_queue = ActivityQueue.objects.get(is_on=True, is_off=False,
                                                             module=ModuleEnum.IOP,
                                                             primary_entity=o_q.primary_entity)  # To be modified for sleep mode. check if primary_entity.temperature is false
                        set_device_temperature(on_queue, on_queue.activity_schedule.action_items)
                    except:
                        on_queue = None

                    o_q.delete()

                if on_queues.exclude(pk=o_q.pk).exists():
                    pass



def check_if_inside(lat, lng, dump_territory):
    location = (float(lat), float(lng))
    import ast
    from shapely import geometry
    parsed_shape = ast.literal_eval(dump_territory.territory)
    temp_shape = [tuple(d.values()) for d in parsed_shape]
    final_shape = geometry.Polygon(temp_shape)
    return final_shape.contains(Point(location))
