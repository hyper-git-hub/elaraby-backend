import datetime, traceback

from django.views.decorators.csrf import csrf_exempt
from geopy.distance import vincenty
import datetime as date_time
from django.utils import timezone
from dateutil import tz
#from sendsms import api
#For testing purposes
from rest_framework.decorators import api_view

from django.core.mail import send_mail
from twilio.rest import Client as client
from backend import settings
from user.enums import RoleTypeEnum
from .models import HypernetPreData, HypernetPostData, Entity, Module, DeviceType, Devices, HypernetNotification, \
    Assignment, DeviceCalibration, NotificationGroups, DeviceViolation
from iof.models import LogisticsDerived, TruckTrips, LogisticAggregations, ActivityQueue, Activity
from iof.generic_utils import get_generic_device_aggregations, get_generic_distance_travelled, get_generic_volume_consumed, get_generic_jobs, get_generic_maintenances, get_generic_violations, get_generic_fillups, get_generic_decantation , get_generic_trips
from customer.models import Customer
from .enums import DeviceTypeEntityEnum, IOFOptionsEnum
from hypernet.utils import *
from hypernet import constants
from hypernet.enums import OptionsEnum
from iof.models import ActivityData, BinCollectionData
from datetime import datetime, timedelta, date
from django.utils import timezone
from user.models import User
from hypernet.notifications.utils import send_notification_to_user, util_save_activity_notification, \
    send_notification_to_admin, send_notification_violations, save_users_group
from options.models import Options
from hypernet.entity.utils import util_create_activity
from customer.models import CustomerPreferences
from iof.utils import create_activity_data, update_bin_statuses, create_bin_collection_data
email_list = constants.email_list
client_email_list = constants.client_email_list

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
        print(e)
        return generic_response("Failed", http_status=400)


# @api_view(['GET'])
# def process_logistics_truck_data(request):
def process_logistics_truck_data(request=None):
    try:
        trucks = Devices.objects.filter(device__type_id=DeviceTypeEntityEnum.TRUCK)
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
                    if HypernetPostData.objects.filter(device=pre_data.device, timestamp = pre_data.timestamp).exists():
                        pre_data.delete()
                        continue
                    else:
                        post = HypernetPostData()
                        post.device = pre_data.device
                        post.customer = pre_data.customer
                        post.module = pre_data.module
                        post.type = pre_data.type

                        post.temperature = pre_data.temperature
                        post.volume = pre_data.volume
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
                                        truck_trip.job = Assignment.objects.get(parent=post.device, status_id=OptionsEnum.ACTIVE,
                                                                               child__type_id=DeviceTypeEntityEnum.JOB).child
                                    except:
                                        truck_trip.job = None
                                        traceback.format_exc()
                                try:
                                    truck_trip.driver = Assignment.objects.get(parent=post.device, status_id=OptionsEnum.ACTIVE,
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
                                post, last_lat, last_lng = process_location_data(pre_data.latitude, pre_data.longitude, first_truck.latitude, first_truck.longitude, post)
                                if notification:
                                    last_vol, post = process_volume_data(notification.threshold_number, pre_data, post, first_truck.volume, first_truck.temperature, calibration, aggregation)
                                else:
                                    last_vol, post = process_volume_data(7, pre_data, post, first_truck.volume, first_truck.temperature, calibration, aggregation)
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
                            post, last_lat, last_lng = process_location_data(pre_data.latitude, pre_data.longitude, last_lat,
                                                         last_lng, post)

                            if notification:
                                last_vol, post = process_volume_data(notification.threshold_number, pre_data, post, last_vol, last_temp, calibration, aggregation)
                            else:
                                last_vol, post = process_volume_data(7, pre_data, post, last_vol, last_temp, calibration, aggregation)
                            post.save()
                            pre_data.delete()

                        Devices.objects.update_or_create(device=pre_data.device, defaults={'timestamp': pre_data.timestamp}, )
            except Exception as e:
                traceback.print_exc()
        print('Job completed at: ' + str(date_time.datetime.now()))
        # return generic_response("Success", http_status=200)
    except Exception as e:
        print(e)
        traceback.format_exc()
        traceback.print_exc()
        # return generic_response("Failed", http_status=400)


# @api_view(['GET'])
# def logistics_truck_aggregation(request):
def logistics_truck_aggregation(request=None):
    try:
        trucks = Devices.objects.filter(device__type_id=DeviceTypeEntityEnum.TRUCK)
        for t in trucks:
            date_now = timezone.now()
            try:
                aggregation = LogisticAggregations.objects.get(device=t.device)
                if (date_now - t.timestamp).total_seconds() / 60 > 20 and aggregation.online_status:
                    aggregation.online_status = False
                    # status.save()
                    send_mail('Staging Device Offline', 'Device is offline id: ' + t.device.name + ' since: ' + str(t.timestamp)+' at: '+str(date_now),
                              'support@hypernymbiz.com',
                              email_list, fail_silently=True)
            except Exception as e:
                aggregation = LogisticAggregations()
                if (date_now - t.timestamp).total_seconds() / 60 < 20: # This will run only one time
                    aggregation.online_status = True
            try:
                date_from = date_now - date_time.timedelta(days=1)
                aggregation.tdist_last24Hrs = get_generic_distance_travelled(t.device.customer.id, t.device.id, None, None, date_from, date_now)
                aggregation.tvol_last24Hrs = get_generic_volume_consumed(t.device.customer.id, t.device.id, None, None, date_from, date_now)
                if aggregation.timestamp:
                    aggregation.total_distance += get_generic_distance_travelled(t.device.customer.id, t.device.id, None, None, aggregation.timestamp, date_now)
                    aggregation.total_volume_consumed += get_generic_volume_consumed(t.device.customer.id, t.device.id, None, None, aggregation.timestamp, date_now)
                    # To be fixed with migrations and review query calls - FIXED WALEED
                    aggregation.total_jobs_completed += get_generic_jobs(t.device.customer.id, t.device.id, None, None, None, IOFOptionsEnum.COMPLETED, None, aggregation.timestamp, date_now).count()
                    # aggregation.total_jobs_completed = 0
                    aggregation.total_fillups += len(get_generic_fillups(t.device.customer.id, t.device.id, None, None, aggregation.timestamp, date_now))
                    aggregation.total_maintenances += get_generic_maintenances(t.device.customer.id, t.device.id, None, None, aggregation.timestamp, date_now).count()
                    aggregation.total_trips += get_generic_trips(t.device.customer.id, t.device.id, None, None, aggregation.timestamp, date_now).count()
                    aggregation.total_violations += get_generic_violations(t.device.customer.id, t.device.id, None, None, None, None, aggregation.timestamp, date_now).count()
                    
                else: # Only runs in case Aggregation object did not exist in the database
                    aggregation.device = t.device
                    aggregation.customer = t.device.customer
                    aggregation.module = t.device.module
                    aggregation.total_distance = get_generic_distance_travelled(t.device.customer.id, t.device.id, None, None, None, None)
                    aggregation.total_volume_consumed = get_generic_volume_consumed(t.device.customer.id, t.device.id, None, None, None, None)
                    # To be fixed with migrations and review query calls - FIXED WALEED
                    aggregation.total_jobs_completed = get_generic_jobs(t.device.customer.id, t.device.id, None, None, None, IOFOptionsEnum.COMPLETED, None, None, None).count()
                    # aggregation.total_jobs_completed = 0
                    aggregation.total_fillups = len(get_generic_fillups(t.device.customer.id, t.device.id, None, None, None, None))
                    aggregation.total_maintenances = get_generic_maintenances(t.device.customer.id, t.device.id, None, None, None, None).count()
                    aggregation.total_trips = get_generic_trips(t.device.customer.id, t.device.id, None, None, None, None).count()
                    aggregation.total_violations = get_generic_violations(t.device.customer.id, t.device.id, None, None, None, None, None, None).count()
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
                queryset = HypernetPostData.objects.filter(device=item.device, timestamp__range=[date_from,date_now]).order_by('timestamp')
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
                            last_vol, post = process_volume_data(7, post, post, last_vol, calibration, aggregation)
                    else:
                        last_vol = post.volume
                    post.save()
                    
                    
            except Exception as e:
                print(e)
                traceback.format_exc()
                traceback.print_exc()
        print('Job completed at: ' + str(date_time.datetime.now()))
        # return generic_response("Success", http_status=200)
    except Exception as e:
        print(e)
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
                            if first_bin.volume - pre_data.volume>= 50:
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
                        if last_vol - pre_data.volume  >= notification.threshold_number:
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
                    aggregation.total_jobs_completed += get_generic_jobs(b.device.customer.id, b.device.id, None, None, None, None, None,
                                                                 aggregation.timestamp, date_now).count()
                    # aggregation.total_jobs_completed = 0
                    aggregation.total_decantations += len(
                        get_generic_decantation(b.device.customer.id, b.device.id, None, None, aggregation.timestamp, date_now))
                    aggregation.total_maintenances += get_generic_maintenances(b.device.customer.id, b.device.id, None, None,
                                                                       aggregation.timestamp, date_now).count()

                    aggregation.total_violations += get_generic_violations(b.device.customer.id, b.device.id, None, None, None, None,
                                                                   aggregation.timestamp, date_now).count()

                else:
                    aggregation.device = b.device
                    aggregation.customer = b.device.customer
                    aggregation.module = b.device.module
                    # To be fixed with migrations and review query calls - FIXED WALEED
                    aggregation.total_jobs_completed = get_generic_jobs(b.device.customer.id, b.device.id, None, None, None, None,
                                                                None, None, None).count()
                    # aggregation.total_jobs_completed = 0
                    aggregation.total_decantations = len(
                        get_generic_decantation(b.device.customer.id, b.device.id, None, None, None, None))
                    aggregation.total_maintenances = get_generic_maintenances(b.device.customer.id, b.device.id, None, None, None,
                                                                      None).count()
                    aggregation.total_violations = get_generic_violations(b.device.customer.id, b.device.id, None, None, None,
                                                                  None, None, None).count()
                aggregation.timestamp = date_now
                aggregation.last_updated = b.timestamp
                aggregation.save()
            except Exception as e:
                print(e)
                
            try:
                last_message = HypernetPostData.objects.get(device=b.device, timestamp=b.timestamp)
                aggregation.last_volume = last_message.volume
                aggregation.last_latitude = last_message.latitude
                aggregation.last_longitude = last_message.longitude
                aggregation.save()
            except Exception as e:
                print(e)
        print('Job completed at: ' + str(date_time.datetime.now()))
    except Exception as e:
        print(e)



                # return generic_response("Failed", http_status=400)


# @api_view(['GET'])
# def process_logistics_bin_data(request):
def process_logistics_vessel_data():
    try:
        vessels = Devices.objects.filter(device__type_id=DeviceTypeEntityEnum.VESSEL)
        for item in vessels:
            queryset = HypernetPreData.objects.filter(device=item.device).order_by('timestamp')
            for pre_data in queryset:
                post = HypernetPostData()
                post.device = pre_data.device
                post.customer = pre_data.customer
                post.module = pre_data.module
                post.type = pre_data.type
                post.volume = pre_data.volume
                post.timestamp = pre_data.timestamp
                post.save()
                pre_data.delete()
                Devices.objects.update_or_create(device=pre_data.device, defaults={'timestamp': pre_data.timestamp}, )
        print('Job completed at: ' + str(date_time.datetime.now()))
        # return generic_response("Success", http_status=200)
    except Exception as e:
        traceback.format_exc()


def process_volume_data(threshold, pre_data, post, last_vol, last_temp, calibration, aggregation):
    try:
        send_email = False
        if (pre_data.volume ==1 and pre_data.temperature ==1) or pre_data.volume >100 or pre_data.volume <0:
            post.volume = last_vol
            post.temperature = last_temp
            return last_vol, post
        if pre_data.volume:
            if pre_data.volume - last_vol <= 6:
                post.volume = last_vol
                post.volume_consumed = 0
                pre_data.volume = last_vol
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
                fill.save()
                if send_email:
                    if calibration:   #Temporary Fix. To be fixed later
                        send_mail('Staging Truck Fillup',
                              'Truck: ' + pre_data.device.name + ' filled at: ' + str(
                                  pre_data.timestamp) + '. Location: https://www.google.com/maps/search/?api=1&query='+str(pre_data.latitude)+','+str(pre_data.longitude)+
                                  '. Volume filled: '+calibration.calibration["{0:.2f}".format(float(pre_data.volume))] - \
                                               calibration.calibration["{0:.2f}".format(float(last_vol))],
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
            elif last_vol - pre_data.volume >= 6:
                if calibration:
                    post.volume_consumed = calibration.calibration["{0:.2f}".format(float(last_vol))] - \
                                           calibration.calibration[
                                               "{0:.2f}".format(float(pre_data.volume))]
                else:
                    post.volume_consumed = last_vol - pre_data.volume
                last_vol = pre_data.volume
                
            elif pre_data.volume - last_vol <= 6:
                post.volume = last_vol
                post.volume_consumed = 0
        else:
            post.volume = last_vol
            post.temperature = last_temp
            post.volume_consumed = 0
        return last_vol, post
    except Exception as e:
        traceback.print_exc()


def process_location_data(current_lat, current_lng, last_lat, last_lng, post):
    try:
        
        if current_lat and current_lng:
            post.latitude = current_lat
            post.longitude = current_lng
        else:
            post.latitude = last_lat
            post.longitude = last_lng
            current_lat = last_lat
            current_lng = last_lng
        
        post.distance_travelled = vincenty((current_lat, current_lng),(last_lat, last_lng)).meters
        if post.distance_travelled <= 200:
            post.distance_travelled = 0
            post.latitude = last_lat
            post.longitude = last_lng
        else:
            last_lat = current_lat
            last_lng = current_lng
        
        return post, last_lat, last_lng
    except Exception as e:
        traceback.print_exc()


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


#@api_view(['GET'])
#def save_logistic_notification(request):
def save_logistic_notification():
    date_now = timezone.now()
    time_threshold_job = date_now + timezone.timedelta(minutes=constants.LAST_HOUR)
    time_threshold_maintenance = date_now + timezone.timedelta(minutes = constants.LAST_24_HOUR)
    try:
        ent = Entity.objects.filter(speed = False, type_id__in = [DeviceTypeEntityEnum.JOB, DeviceTypeEntityEnum.MAINTENANCE]
                                    )
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

                    send_notification_to_user(assigned_truck, assigned_driver, obj, [User.objects.get(associated_entity=assigned_driver)], "There is an upcoming job")
                    obj.speed = True
                    obj.save()
                    print("Notification saved at" + str(date_time.datetime.now()))
                    #return generic_response("Success", http_status=200)
                except Exception as e:
                    pass

            elif obj.type.id == DeviceTypeEntityEnum.MAINTENANCE:
                td = obj.end_datetime.date() - date_now.date()
                tdd = td / timedelta(days = 1)  #Checking difference of days b/w maintenance due date and current date.
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
                        #return generic_response("Success", http_status=200)
                    except Exception as e:
                        print(e)
                        pass
                else:
                    print("Maitenance not in schedule")
            #return generic_response("Success", http_status=200)
    except Exception as e:
        print(e)


def process_logistics_ffp_data():
    try:
        last_lat = None
        last_lng = None
    
        workers = Devices.objects.filter(device__type_id=DeviceTypeEntityEnum.WORKFORCE)
        
        for worker in workers:
            try:
                first_truck = HypernetPostData.objects.get(device=worker.device, timestamp=worker.timestamp)
            except Exception as e:
                first_truck = None
            queryset = HypernetPreData.objects.filter(device=worker.device).order_by('timestamp')
            for pre_data in queryset:
                post = HypernetPostData()
                post.device = pre_data.device
                post.customer = pre_data.customer
                post.module = pre_data.module
                post.type = pre_data.type

                post.latitude = pre_data.latitude
                post.longitude = pre_data.longitude
                post.timestamp = pre_data.timestamp

                if last_lat is None and last_lng is None:
                    if first_truck:
                        post, last_lat, last_lng = process_location_data_ffp(pre_data.latitude, pre_data.longitude,
                                                                         first_truck.latitude, first_truck.longitude,
                                                                         post)
                    else:
                        last_lat = pre_data.latitude
                        last_lng = pre_data.longitude
                else:
                    post, last_lat, last_lng = process_location_data_ffp(pre_data.latitude, pre_data.longitude, last_lat,
                                                                     last_lng, post)
                post.save()
                pre_data.delete()
                
        print('Job completed at: ' + str(date_time.datetime.now()))
    except:
        traceback.print_exc()

#@api_view(['GET'])
#def check_maintenance_overdue(request):
def check_maintenance_overdue():
    try:
        maintenance = Entity.objects.filter(type_id = DeviceTypeEntityEnum.MAINTENANCE,
                                        job_status_id= IOFOptionsEnum.MAINTENANCE_DUE, status = OptionsEnum.ACTIVE)
        for obj in maintenance:
            threshold =  timezone.now().date() - obj.end_datetime.date()  #Checking difference of days b/w current date and maintenance due date.
            buffer = threshold / timedelta (days=1)
            if buffer >= 1.0:
                obj.job_status = Options.objects.get(id=IOFOptionsEnum.MAINTENANCE_OVER_DUE)
                obj.save()
                try:
                    assigned_truck = Assignment.objects.get(child_id=obj.id,
                                                    child__type=DeviceTypeEntityEnum.MAINTENANCE,
                                                    parent__type=DeviceTypeEntityEnum.TRUCK).parent_id

                    assigned_driver = Assignment.objects.get(parent_id =assigned_truck,
                                                     child__type=DeviceTypeEntityEnum.DRIVER,
                                                    parent__type=DeviceTypeEntityEnum.TRUCK).child_id

                    over_due_maintenance = ActivityData(
                        device_id=obj.id,
                        customer_id= obj.customer_id,
                        module_id=obj.module_id,
                        entity_id=assigned_truck,
                        person_id=assigned_driver,
                        job_start_timestamp=obj.end_datetime,
                        job_end_timestamp=obj.end_datetime,
                        job_status=Options.objects.get(id=IOFOptionsEnum.MAINTENANCE_OVER_DUE),
                        maintenance_type= obj.maintenance_type
                    )
                    over_due_maintenance.save()

                    send_notification_to_user(assigned_truck, assigned_driver, obj,
                                              [User.objects.get(associated_entity=assigned_driver)],
                                              "Maintenance is now overdue")
                    obj.speed = True
                    obj.save()
                    print("Maintenance" +str(obj.name) + "is over-due")


                except Exception as e:
                    print(e)
                    #return generic_response("Fail", http_status=500)
            else:
                print("maintenance not over-due")
                #return generic_response("Fail", http_status=500)
        #return generic_response("Success", http_status=200)
    except Exception as e:
        print(e)
        #return generic_response("Fail", http_status=500)

@api_view(['GET'])
@csrf_exempt
def schedule_activity(request):

    activities = ActivityQueue.objects.filter(activity_datetime__date__range = [date.today(), date.today()+timedelta(days=1)])
    if activities:
        for obj in activities:
            try:
                Activity.objects.get(activity_status_id__in = [IOFOptionsEnum.RUNNING, IOFOptionsEnum.PENDING, IOFOptionsEnum.ACCEPTED],
                                 activity__primary_entity = obj.primary_entity)

                print("Activity already pending or running for truck" + str(obj.primary_entity.id))

            except:
                        current_hour = timedelta(hours=timezone.now().hour)
                        activity_hour = timedelta(hours = obj.activity.job_start_time.hour)



                        t1 = timedelta(hours=timezone.now().hour, minutes=timezone.now().minute,
                                       seconds=timezone.now().second)

                        t2 = timedelta(hours=obj.activity.job_start_time.hour,
                                       minutes=obj.activity.job_start_time.minute,
                                       seconds=obj.activity.job_start_time.second)

                        buffer = (t2 - t1).seconds
                        #buffer = (obj.activity.job_start_time - dt)
                        buffer = round(buffer / 60,0)


                        if buffer <= constants.LAST_THIRTY_MINUTES and buffer >= 0: #this will be checked once User prefrences are added.
                                                                                    # Right now only checking if it lies in 30 minutes buffer

                        # Check from user prefrences if he has enabled accept or reject feature. If not then an Acitivity entry will be created
                        # with Accepted status and no notifcation will be sent. If enabled then the below scenario will follow.

                            if obj.activity.enable_accept_reject is True:

                                    try:
                                        assigned_driver = Assignment.objects.get(child__type_id = DeviceTypeEntityEnum.DRIVER,
                                                                                 parent = obj.activity.primary_entity,
                                                                                 status_id = OptionsEnum.ACTIVE).child
                                        activity = util_create_activity(obj, assigned_driver, IOFOptionsEnum.PENDING, obj.activity_datetime)
                                        try:
                                            activity.save()
                                            util_save_activity_notification(obj, activity,
                                                                            [User.objects.get(associated_entity=assigned_driver)],
                                                                            "Accept or reject this activity")

                                            ActivityQueue.objects.get(id=obj.id).delete()
                                        except Exception as e:
                                            print (e)

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
                                        for user in [User.objects.get(id = obj.activity.user.id)]:
                                            gn = NotificationGroups(notification=notification,
                                                                    user=user)
                                            gn.save()
                                        notification.save()

                            else:
                                try:
                                    assigned_driver = Assignment.objects.get(child__type_id=DeviceTypeEntityEnum.DRIVER,
                                                                             parent=obj.activity.primary_entity,
                                                                             status_id=OptionsEnum.ACTIVE).child
                                    activity= util_create_activity(obj, assigned_driver,  IOFOptionsEnum.ACCEPTED, obj.activity_datetime)
                                    try:
                                        activity.save()
                                        ActivityQueue.objects.get(id=obj.id).delete()
                                    except Exception as e:
                                        print(e)
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


# @api_view(['GET'])
def send_notification(request = None):
#def send_notification():
    try:
        activity = Activity.objects.filter(activity_status_id = IOFOptionsEnum.ACCEPTED, notification_sent = False)
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
                    type_id = IOFOptionsEnum.NOTIFICATION_DRIVER_START_ACTIVITY,
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
        #print("Notification sent")
        print('Job completed at: ' + str(date_time.datetime.now()))
        # return generic_response("Success", http_status=200)
    except Exception as e:
        traceback.print_exc()
        # return generic_response("Failure", http_status=400)


#@api_view(['GET'])
#def schedule_activity2(request):
def schedule_activity2(request=None):
    clean_activity = None
    end_time = (timezone.now() + timedelta(days=7))
    activities = ActivityQueue.objects.filter(activity_datetime__gte = timezone.now(), activity_datetime__lte= end_time, activity_schedule__schedule_activity_status_id = OptionsEnum.ACTIVE)
    for obj in activities:
        preferences = CustomerPreferences.objects.get(customer_id = obj.activity_schedule.customer.id)
        buffer = (obj.activity_datetime - timezone.now()).total_seconds()
        buffer = round(buffer / 60, 0)
        
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
            current_driver = Activity.objects.get(activity_status_id__in=[IOFOptionsEnum.SUSPENDED, IOFOptionsEnum.RUNNING,
                                                               IOFOptionsEnum.PENDING, IOFOptionsEnum.ACCEPTED,
                                                               IOFOptionsEnum.REJECTED,
                                                               IOFOptionsEnum.FAILED, IOFOptionsEnum.CONFLICTING],
                                              actor=obj.actor)
        except:
            current_driver = None
            
        if preferences.enable_accept_reject:
            if buffer <= preferences.activity_accept_reject_buffer:
                try:  # Current activity of truck
                    activity = bla(current_truck, preferences, obj,
                                   "Activity already running for " + obj.primary_entity.name + ". Please Review.",
                                   IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_TRUCK_CONFLICT)
                    if not activity:
                        activity = bla(current_driver, preferences, obj,
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
                                               [obj.actor.id],
                                               "Accept or reject this activity",
                                               IOFOptionsEnum.NOTIFCIATION_DRIVER_ACCEPT_REJECT)
                obj.delete()

        else:
            if buffer <= preferences.activity_start_buffer:
                try:
                    activity = bla(current_truck, preferences, obj,
                                   "Activity already running for " + obj.primary_entity.name + ". Please Review.",
                                   IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_TRUCK_CONFLICT)
                    if not activity:
                        activity = bla(current_driver, preferences, obj,
                                       "Activity already running for " + obj.actor.name + "Please Review. ",
                                       IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_DRIVER_CONFLICT)
                    if not activity:
                        if check_bins_validity(obj):
                            if (activity.activity_schedule.end_date is None) or (activity.activity_schedule.end_date <= timezone.now().date()):
                                activity.activity_schedule.schedule_activity_status = Options.objects.get(id=OptionsEnum.INACTIVE)
                                activity.activity_schedule.save()
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

                    
                obj.delete()

    
    # print("Success")
    print('Job completed at: ' + str(date_time.datetime.now()))
    #return generic_response("Success", http_status=200)
    
def remove_notifications(request=None):
#def remove_notifications():
###############################################################
    try:
        accept_reject_notifications = HypernetNotification.objects.filter(
            type_id=IOFOptionsEnum.NOTIFCIATION_DRIVER_ACCEPT_REJECT, status_id = OptionsEnum.ACTIVE)
        for obj in accept_reject_notifications:
            activity = Activity.objects.get(id=obj.activity.id)
            preference = CustomerPreferences.objects.get(customer=obj.customer)

            buffer = (timezone.now() - obj.created_datetime).total_seconds()
            
            buffer = round(buffer / 60, 0)
            if buffer >= preference.activity_accept_driver_buffer:
                if obj.type.id == IOFOptionsEnum.NOTIFCIATION_DRIVER_ACCEPT_REJECT and (obj.activity.activity_status.id == IOFOptionsEnum.PENDING or obj.activity.activity_status.id == IOFOptionsEnum.REVIEWED):  # Driver has been sent a notification of ACCEPT/REJECT but driver doesnot take any action, hence
                    # notification is sent to admin to review it IF he has enabled Review flag in prefrence.
                    send_notification_to_user(obj, activity,
                                                  [User.objects.get(id=obj.activity.activity_schedule.modified_by.id)],
                                                  str(obj.activity.actor.name)+ " didn't take any action. Please review this activity",
                                                  IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_NO_ACTION_ACCEPT_REJECT)
                        
                    create_activity_data_alter_activity(obj,activity, IOFOptionsEnum.REJECTED)
            else:
                print(str(buffer - timezone.now().minute) + " Minutes left to review")
        ######################################################################################
        review_notifications = HypernetNotification.objects.filter(type_id__in = [IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW,
                                                                   IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_DRIVER_REJECT,
                                                                                  IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_TRUCK_CONFLICT,
                                                                                  IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_DRIVER_CONFLICT,
                                                                                  IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_NO_ACTION_ACCEPT_REJECT,
                                                                                  IOFOptionsEnum.NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_ABORT,
                                                                                  IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_NO_ACTION_START_FAIL], status_id = OptionsEnum.ACTIVE)
        for obj in review_notifications:
            activity = obj.activity
            preference = CustomerPreferences.objects.get(customer=obj.customer)
    
            buffer = (timezone.now() - obj.created_datetime).total_seconds()
    
            buffer = round(buffer/60,0)
            if buffer >= preference.activity_review_admin_buffer:
                if obj.type.id == IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW and obj.activity.activity_status.id == IOFOptionsEnum.PENDING:
                    if preference.enable_accept_reject:
                        send_notification_to_user(obj,activity,
                                              [User.objects.get(associated_entity=obj.activity.actor)],
                                                "Accept or reject this activity",
                                              IOFOptionsEnum.NOTIFCIATION_DRIVER_ACCEPT_REJECT)
                        activity.activity_status = Options.objects.get(id=IOFOptionsEnum.REVIEWED)

                    else:
                        try:
                            driver = Activity.objects.get(actor=obj.driver, activity_status_id__in = [IOFOptionsEnum.RUNNING, IOFOptionsEnum.SUSPENDED, IOFOptionsEnum.ACCEPTED])

                        except:
                            driver = None
                        try:
                            truck = Activity.objects.get(primary_entity=obj.device, activity_status_id__in=[IOFOptionsEnum.RUNNING,
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
                                                                 IOFOptionsEnum.REVIEWED, None, None, obj.customer.id, obj.module.id)
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
    
                elif obj.type.id == IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_NO_ACTION_ACCEPT_REJECT and obj.activity.activity_status.id == IOFOptionsEnum.REJECTED: #Use Case: Accept reject notification sent to driver but driver doesnot take any action.
                                                                                                                                                                            #Activity rejected as driver didnt take any action.
                                                                                                                                                                            #  Review notification sent to admin but admin doesnot take any action
                    process_activity(obj, activity, IOFOptionsEnum.ABORTED)

                elif obj.type.id == IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_NO_ACTION_START_FAIL and obj.activity.activity_status.id == IOFOptionsEnum.FAILED:  # Use Case: Accept reject notification sent to driver but driver doesnot take any action.
                    # Activity rejected as driver didnt take any action.
                    #  Review notification sent to admin but admin doesnot take any action
                    process_activity(obj, activity, IOFOptionsEnum.ABORTED)
                
                elif (obj.type.id == IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_TRUCK_CONFLICT or \
                                obj.type.id == IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_DRIVER_CONFLICT) \
                        and obj.activity.activity_status.id == IOFOptionsEnum.CONFLICTING:
    
    
                    process_activity(obj, activity, IOFOptionsEnum.ABORTED)

                elif (obj.type.id == IOFOptionsEnum.NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_ABORT and obj.activity.activity_status.id == IOFOptionsEnum.FAILED):

                    process_activity(obj, activity, IOFOptionsEnum.ABORTED)
            else:
                print(str(buffer - timezone.now().minute) + " Minutes left to review")
    
    
    
        ###############################################################
        start_fail_notifications = HypernetNotification.objects.filter(type_id=IOFOptionsEnum.NOTIFICATION_DRIVER_START_ACTIVITY, status_id = OptionsEnum.ACTIVE)
        
        for obj in start_fail_notifications:
            activity = Activity.objects.get(id=obj.activity.id)
            preference = CustomerPreferences.objects.get(customer=obj.customer)
    
            #buffer=obj.created_datetime.minute + prefrence.activity_review_buffer
    
            buffer = (timezone.now() - obj.created_datetime).total_seconds()
    
            buffer = round(buffer/60,0)
            if buffer >= preference.activity_start_driver_buffer:
                if obj.type.id == IOFOptionsEnum.NOTIFICATION_DRIVER_START_ACTIVITY and obj.activity.activity_status.id == IOFOptionsEnum.ACCEPTED:
                    send_notification_to_user(obj, activity,
                                              [User.objects.get(id=obj.activity.activity_schedule.modified_by.id)],
                                              str(obj.activity.actor.name) +" didn't take any action. Please review this activity",
                                              IOFOptionsEnum.NOTIFICATION_ADMIN_ACTIVITY_REVIEW_NO_ACTION_START_FAIL)

                    create_activity_data_alter_activity(obj, activity, IOFOptionsEnum.FAILED)

                    bin_collection = BinCollectionData.objects.filter(activity=activity).update(status_id=IOFOptionsEnum.ABORT_COLLECTION)
                    if not bin_collection:
                        for id in activity.action_items.split(','):
                            try:
                                contract = Assignment.objects.get(parent_id = id, child__type_id = DeviceTypeEntityEnum.CONTRACT,
                                                                  status_id = OptionsEnum.ACTIVE).child_id
                                try:
                                    area = Assignment.objects.get(child_id = contract,
                                                                  parent__type_id = DeviceTypeEntityEnum.AREA,
                                                                  status_id = OptionsEnum.ACTIVE).parent_id
                                except:
                                    area = None
                            except:
                                contract = None
                                area = None
                            try:
                                client = Entity.objects.get(id=id).client.id
                            except:
                                client = None
                            bin_collection_data = create_bin_collection_data(activity.id, activity.primary_entity.id,
                                                                             activity.actor.id,
                                                                             timezone.now(),
                                                                             IOFOptionsEnum.ABORT_COLLECTION, id,
                                                                             activity.customer.id, activity.module_id, contract, client, area)
                            bin_collection_data.save()
            #obj.delete()
        #return generic_response("Success", http_status=200)
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
                                                           enabled=True, violation_type_id=IOFOptionsEnum.SPEED).threshold_number

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
            #TODO Check Shifts of Truck/driver.

            driver = activity.actor_id
        except:
            traceback.print_exc()
            driver = None

        try:
            HypernetNotification.objects.get(timestamp__gt=pre_data.timestamp, timestamp__lt=timezone.now(),
                                                type_id=IOFOptionsEnum.SPEED, device_id=pre_data.device_id, driver_id=driver)
        except:
            traceback.print_exc()
            send_email = True
            users = User.objects.filter(role_id=RoleTypeEnum.ADMIN, customer_id=pre_data.customer_id)
            title = "Over speeding violation detected on"+" "+pre_data.device.name+" "+ "at time"+" "+str(pre_data.timestamp)

            try:
                preferences = CustomerPreferences.objects.get(customer_id=pre_data.customer_id)
            except:
                preferences = None

            if preferences.speed_violations is True:
                notification_obj = send_notification_violations(device=pre_data.device_id, driver_id=driver, customer_id=pre_data.customer_id, module_id=pre_data.module_id,
                                  title=title, users_list=users, threshold=None, value=None)

    return send_email

def process_activity(obj,activity, status):
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
    bin_collection = BinCollectionData.objects.filter(activity=activity, status_id = IOFOptionsEnum.UNCOLLECTED).update(status = IOFOptionsEnum.ABORT_COLLECTION)
    if not bin_collection:
        for id in activity.action_items.split(','):
            try:
                contract = Assignment.objects.get(parent_id=id, child__type_id=DeviceTypeEntityEnum.CONTRACT,
                                                  status_id=OptionsEnum.ACTIVE).child_id
                try:
                    area = Assignment.objects.get(child_id=contract,
                                                  parent__type_id=DeviceTypeEntityEnum.AREA,
                                                  status_id=OptionsEnum.ACTIVE).parent_id
                except:
                    area = None
            except:
                contract = None
                area = None
            try:
                client = Entity.objects.get(id=id).client.id
            except:
                client = None
            bin_collection_data = create_bin_collection_data(activity.id, activity.primary_entity.id, activity.actor.id,
                                                             timezone.now(), IOFOptionsEnum.ABORT_COLLECTION, id,
                                                             activity.customer.id, activity.module_id, contract, client, area)
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
    

def bla(current, preferences, obj, message, notification_type):
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
        except:
            send_notification_to_admin(obj.primary_entity.id, obj.actor.id, None, obj,
                                       [obj.activity_schedule.modified_by.id],
                                       "Bin(s) that were part of the schedule have been deleted. Please try again.",
                                       None)
            return True