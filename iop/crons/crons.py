from datetime import timedelta, datetime
from decimal import Decimal
import datetime as date_time
from django.db.models import Avg, Q, F
from django.http import HttpResponseNotFound
from django.utils import timezone

from customer.models import Customer
from hypernet.entity.utils import util_create_activity, abornamlity_removal_util_create_activity,retry_mechanism_signal_shs_mode_device,retry_mechanism_signal_clm_mode_device
from hypernet.enums import DeviceTypeEntityEnum, ModuleEnum, OptionsEnum, IopOptionsEnums
from hypernet.models import Devices, HypernetPostData, Entity
from iof.models import LogisticAggregations, ActivitySchedule, ActivityQueue, Activity
from iop.models import EnergyConsumption, IopDerived, ReconfigurationTable,ReconfigurationLockMode

'''
cronjob to check online/offline status of device. This cron monitors if device is offline and after a certain
threshold of time, data stops coming, sets the device status to offline
'''


def appliance_aggregation(request=None):
    try:
        print('-----------Start time '+  str(date_time.datetime.now()) + '------------')
        retry_failure_cron(request=None)
        retry_failure_lock_mode_cron(request=None)
        devices = Devices.objects.filter(device__type_id=DeviceTypeEntityEnum.IOP_DEVICE)
        for d in devices:
            date_now = timezone.now()
            print(date_now,'date Now')
            
        
            # Table for maintaining online/offline status of a device. Contains only one row for a device in it's entire lifetime. That row keeps getting updated
            aggregation = LogisticAggregations.objects.get(device=d.device)
            print((date_now - aggregation.timestamp).total_seconds() / 60 > 1)
            if (date_now - aggregation.timestamp).total_seconds() / 60 > 1 and aggregation.online_status:
                print(aggregation)
                aggregation.online_status = False
                aggregation.save()
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
    except LogisticAggregations.DoesNotExist:
        print(d)
        aggregation = LogisticAggregations()
        aggregation.device = d.device
        if (date_now - d.timestamp).total_seconds() / 60 < 1:  # This will run only one time
            aggregation.online_status = True
        aggregation.timestamp = timezone.now()
        aggregation.customer = d.device.customer
        aggregation.module = d.device.module
        aggregation.last_updated = timezone.now()
        aggregation.save()
        print("Don't Exists ", aggregation.device_id, ' ', aggregation.last_updated)
    except Exception as e:
        print("Execption", e)

    print('-----------end time '+  str(date_time.datetime.now()) + '------------')

class HttpResponse(object):
    pass


import iop.utils as iop_utils


def energy_consumption(request=None):
    print('-----------Start time '+  str(date_time.datetime.now()) + '------------')
    appliance_aggregation(request=None)
    customer = Customer.objects.get(id=1)
    devices = Devices.objects.filter(device__type_id=DeviceTypeEntityEnum.IOP_DEVICE)
    now = timezone.datetime.now()
    one_hour_before = timezone.datetime.now() - timedelta(hours=1)

    for device in devices:

        avg_temperature = 0
        avg_ctt = 0
        try:
            post_data = HypernetPostData.objects.filter(device_id=device.device,
                                                        timestamp__gte=one_hour_before,
                                                        timestamp__lte=now)

            avg_temperature = post_data.aggregate(avg_temp=Avg('active_score'))

            # current temperature threshold
            avg_ctt = post_data.aggregate(avg_ctt=Avg('ctt'))

            try:
                avg = post_data.aggregate(avg_temp=Avg('active_score'))['avg_temp']
                print('avg   ', avg)
            except Exception as e:
                print('print execption -=- = -= ', e)

            print('avg ctt ===', avg_ctt['avg_ctt'])
            print('avg temperature ===', avg_temperature['avg_temp'])

            total = post_data.count()
            active_time = post_data.filter(heartrate_value=4).count()
            average = 0

            if total > 0:
                average = active_time / total
            # avg_active_duration = post_data.aggregate(Avg("heartrate_value"))

            avg_active_duration = 1

            print('average- %d:   active_time- %d:   total- %d:' % (average, active_time, total))
            try:
                iopDerived = IopDerived(device=device.device, customer=customer, active_duration=average, timestamp=now)
                iopDerived.save()
            except Exception as e:
                print("New execption", e)

        except Exception as e:
            print("execption", e)

        try:
            saving_factor_per_day = Decimal(iop_utils.util_get_saving_factor_per_day(now))
            smart_energy_consumed = Decimal(
                iop_utils.get_energy_consumed_from_hypernet_post(device, one_hour_before, now))
            regular_energy_consumed = 0
            latest_obj = EnergyConsumption.objects.filter(device_id=device.device).last()

            if latest_obj:
                regular_energy_consumed = (smart_energy_consumed) + (saving_factor_per_day)
                smart_energy_consumed = (smart_energy_consumed) + (latest_obj.energy_consumed)  # Adds t

                print('regular_energy_consumed %d' % regular_energy_consumed)
                print('smart_energy_consumed %d' % smart_energy_consumed)
                print('saving_factor_per_day %d' % saving_factor_per_day)
                # print('latest_obj_energy_consumed' % latest_obj.energy_consumed)

            row_to_save = EnergyConsumption(device_id=device.device, datetime=now,
                                            energy_consumed=smart_energy_consumed,
                                            ec_regular_appliance=regular_energy_consumed,
                                            average_temperature=avg_temperature['avg_temp'],
                                            average_ctt=avg_ctt['avg_ctt'])

            print('device id  ', row_to_save.device_id)
            print('row to save  ', row_to_save.energy_consumed)
            print('avg temperature  ', row_to_save.average_temperature)

            row_to_save.save()
            print('Chron completed for device: ', device, ' at ', now, row_to_save)

        except Exception as e:
            print(e.args[0], 'at', now)
            pass
    print('-----------END time '+  str(date_time.datetime.now()) + '------------')          
    return HttpResponseNotFound('<h1>Chron successfull!</h1>')


def check_if_any_abnormality(request=None):
    try:
        print("ABONORMALITY REMOVAL CRON JOB STARTED !!!")
        ents = Entity.objects.filter(module_id=ModuleEnum.IOP,
                                     type_id=DeviceTypeEntityEnum.IOP_DEVICE,
                                     status_id=OptionsEnum.ACTIVE, temperature=False)
        for ent in ents:
            print("ENT : ", ent.id)
            calculated_datetime = datetime.now() + timedelta(minutes=120)
            # check_time = calculated_datetime
            # print("Calculated Date time after 2 hrs gap", calculated_datetime)

            Activity.objects.filter(activity_schedule__new_start_dt__gt=calculated_datetime, primary_entity=ent).delete()
            abnormal_schedules = ActivitySchedule.objects.filter(primary_entity=ent, new_start_dt__date__gt=F('old_start_dt'))
            print("ACTIVITY SCHEDULES FOUND ABNORMAL: ", abnormal_schedules)
            abnormal_schedules.delete() #for testing check
            # abnormal_activities = Activity.objects.filter(activity_status_id=2023)
            current_datetime = datetime.now()

            # Either we can do this, or t_q.activity_datetime.replace(tzinfo=None). To make append timezone info with datetimes or make them naive, both must be same
            current_datetime = current_datetime.replace(tzinfo=timezone.utc)
            print("Current Date: ", current_datetime)

            # Fetch today queues, where activity_datetime is start_datetime of activity, queue should be off. For explaination, consult iof/models.py
            today_queues = ActivityQueue.objects.filter(activity_datetime__date=current_datetime.date(),
                                                        is_on=False, is_off=False, module=ModuleEnum.IOP,
                                                        temp_set=False, suspend=False, primary_entity=ent,
                                                        activity_datetime__lt=datetime.now()).order_by('activity_datetime')

            print("TODAY QUEUES IN ABNORMAL ACTIVITY", today_queues)
            for t_q in today_queues:
                activity = abornamlity_removal_util_create_activity(t_q, None, IopOptionsEnums.IOP_SCHEDULE_READY, None)
                activity.save()
            # for act in abnormal_activities:
            #     print("ACTIVITY ID TO BE DELETED : ", act.id)
            #     print("SCHEDULE ID TO BE DELETED : ", act.activity_schedule.id)
            #     # print("ACTIVITY_QUEUE_TO BE DELETED: ", ac)
            #     ActivityQueue.objects.filter(activity_schedule_id=act.activity_schedule.id).delete()
            #     ActivitySchedule.objects.filter(id=act.activity_schedule.id).delete()
            #     act.delete()
                if not t_q.is_on and not t_q.temp_set:
                    t_q.is_on = True
                    t_q.temp_set = True
                    t_q.save()
                    print("setting is_on and temp_set")
            # current_time = datetime.now()
            # missed_check = current_time - timedelta(minutes=5)
            # current_date = current_time.date()
            #
            # result = Activity.objects.filter(Q(activity_schedule__new_start_dt_lt=missed_check), Q(activity_schedule__new_start_dt__date=current_date),
            #                         ~Q(activity_status_id=2018), ~Q(activity_status_id=2019), ~Q(activity_status_id=2020),
            #                         ~Q(activity_status_id=2021)).update(activity_status_id=2018)
            # print("result: ", result)
            print("Updated abnormal schedule")

        print("ABONORMALITY REMOVED !!!!!!!!!!!!!!!!!!")

    except Exception as e:
        print(e)


def new_energy_consumption(request=None):
    customer = Customer.objects.get(id=1)
    devices = Devices.objects.filter(device__type_id=DeviceTypeEntityEnum.IOP_DEVICE)
    now = timezone.datetime.now()
    one_hour_before = timezone.datetime.now() - timedelta(hours=1)

    for device in devices:
        try:
            post_data = HypernetPostData.objects.filter(device_id=device.device,
                                                        timestamp__gte=one_hour_before,
                                                        timestamp__lte=now)

            try:
                aggregation = post_data.aggregate(avg_temp=Avg('active_score'), avg_ctt=Avg('ctt'))
                print('aggregation result   ', aggregation)
            except Exception as e:
                print('aggregation execption  ', e)

            total = post_data.count()
            active_time = post_data.filter(heartrate_value=4).count() * 10
            # average = 0
            #
            # if total > 0:
            #     average = active_time / total
            # avg_active_duration = post_data.aggregate(Avg("heartrate_value"))

            avg_active_duration = 1

            try:
                iopDerived = IopDerived(device=device.device, customer=customer, active_duration=active_time,
                                        timestamp=now)
                iopDerived.save()
            except Exception as e:
                print("New execption", e)

        except Exception as e:
            print("execption", e)

        try:
            saving_factor_per_day = Decimal(iop_utils.util_get_saving_factor_per_day(now))
            smart_energy_consumed = Decimal(
                iop_utils.get_energy_consumed_from_hypernet_post(device, one_hour_before, now))

            regular_energy_consumed = (smart_energy_consumed) + (saving_factor_per_day)

            if float(smart_energy_consumed) == 0:
                regular_energy_consumed = 0

            row_to_save = EnergyConsumption(device_id=device.device, datetime=now,
                                            energy_consumed=smart_energy_consumed,
                                            ec_regular_appliance=regular_energy_consumed,
                                            average_temperature=aggregation['avg_temp'] or 0,
                                            average_ctt=aggregation['avg_ctt'] or 0)

            row_to_save.save()
            print('device: ', row_to_save)
            print('Chron completed for device: ', device, ' at ', now)

        except Exception as e:
            print(e.args[0], 'at', now)
            pass

    print(' === Chron completed at: ', now)

    return HttpResponseNotFound('<h1>Chron successfull!</h1>')


def retry_failure_cron(request=None):
    try:
        print('retry_failure_cron')
        print('-----------Start time '+  str(timezone.datetime.now()) + '------------')
        devices = Devices.objects.filter(device__type_id=DeviceTypeEntityEnum.IOP_DEVICE)
        now = timezone.datetime.now()
        for device in devices:
            try:
                print('retry crons start')
                print(device.device.device_name.device_id,'device_name')
                failure_status = ReconfigurationTable.objects.get(device=device.device.id)
                print('device_device:   ', failure_status.device, '  status: ', failure_status.failure_code)
                if failure_status.failure_code != 200:
                    print("Inside error check of retry failure")
                    iop_utils.retry_mechanism_set_device_temperature(obj=None, ent=device, temp=failure_status.temperature_set)
                    retry_mechanism_signal_shs_mode_device(device.device,failure_status.shs)
                    print("after setting the temperature")
            except Exception as e:
                pass
        print('-----------END time '+  str(timezone.datetime.now()) + '------------')
    except Exception as e:
        print(e)

def retry_failure_lock_mode_cron(request=None):
    try:
        print('-----------Start time '+  str(timezone.datetime.now()) + '------------')
        devices = Devices.objects.filter(device__type_id=DeviceTypeEntityEnum.IOP_DEVICE)
        now = timezone.datetime.now()
        for device in devices:
            try:
                print('retry crons start')
                print(device.device.device_name.device_id,'device_name')
                failure_status = ReconfigurationLockMode.objects.get(device=device.device.id)
                print('device_device:   ', failure_status.device, '  status: ', failure_status.failure_code)
                if failure_status.failure_code != 200:
                    print("Inside error check of retry failure for lock mode")
                    retry_mechanism_signal_clm_mode_device(device.device,failure_status.lock_mode,)
                    print("after setting the lock mode")
            except Exception as e:
                pass
        print('-----------END time '+  str(timezone.datetime.now()) + '------------')
    except Exception as e:
        print(e)

'''
def set_normal_temperature(request=None):

    ents = Entity.objects.filter(type_id = DeviceTypeEntityEnum.IOP_DEVICE,
                                 status_id = OptionsEnum.ACTIVE)

    for ent in ents:
        if ent.temperature is True:
            continue

        else:
            queues = ActivityQueue.objects.filter(primary_entity = ent, is_on=True)
            if len(queues) > 0:
                continue
            else:
                set_device_temperature(, str(constants.SLEEP_MODE_TEMP))
'''
