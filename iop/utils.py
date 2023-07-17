import os
import random
import string
import traceback
from _decimal import Decimal
from datetime import timedelta, datetime

import requests
from dateutil.parser import parse
from django.core.mail import send_mail
from django.db.models import Q, Avg, Count,Sum
from django.utils import timezone
from rest_framework.pagination import LimitOffsetPagination

import hypernet.constants as constants
import hypernet.entity.utils as ent_utils
# from hypernet.entity.job_V2.utils import updated_conflicts
from hypernet.enums import ModuleEnum, DeviceTypeEntityEnum, DeviceTypeAssignmentEnum, OptionsEnum, IopOptionsEnums
from hypernet.models import Entity, HypernetPostData, HypernetPreData, UserEntityAssignment, Devices
from hypernet.serializers import HomeAppliancesSerializer,HomeApplianceFrontendsSerializer,IOPApplianceFrontendsSerializer
from iof.models import ActivityQueue, ActivitySchedule, Activity, LogisticAggregations
from iop.models import IopAggregation, ErrorLogs, ReconfigurationTable
from iop.models import IopDerived, EnergyConsumption
from options.models import Options
from django.db import connection


def get_iop_devices_count(c_id):
    devices = Entity.objects.filter(customer_id=c_id, module_id=ModuleEnum.IOP)

    data = devices.values('entity_sub_type_id').annotate(device_count=Count('entity_sub_type_id')). \
        values('device_count', 'entity_sub_type__label', 'entity_sub_type_id')

    return (data)


def get_iop_devices(c_id, t_id, mod_id, s_date=None, e_date=None):
    if mod_id:
        ent = Entity.objects.filter(leased_owned_id=mod_id)
    elif t_id:
        ent = Entity.objects.filter(entity_sub_type_id=t_id)
    else:
        ent = Entity.objects.filter(customer_id=c_id)

    if s_date and e_date:
        ent = ent.filter(created_datetime__range=[s_date, e_date])

    return ent
    # return Entity.objects.filter(Q(entity_sub_type_id=t_id) | Q(leased_owned_id=mod_id),
    #                              customer_id=c_id, type_id=DeviceTypeEntityEnum.IOP_DEVICE, module_id=ModuleEnum.IOP,
    #                              created_datetime__range=[s_date, e_date])


def sold_devices_iop(c_id, s_date, e_date):
    print(c_id)
    sold_device = Entity.objects.filter(customer_id=c_id, module_id=ModuleEnum.IOP, obd2_compliant=True)
    if s_date and e_date:
        sold_device = sold_device.filter(created_datetime__date__range=[s_date, e_date])
    return sold_device


def get_sold_stats(c_id):
    this_week = timezone.now() - timedelta(days=7)
    last_week = this_week - timedelta(days=7)

    this_month = timezone.now() - timedelta(days=30)
    last_month = this_month - timedelta(days=30)

    this_year = timezone.now() - timedelta(days=365)
    last_year = this_year - timedelta(days=365)

    sold_device_this_week = sold_devices_iop(c_id=c_id, s_date=this_week, e_date=timezone.now())
    sold_device_this_month = sold_devices_iop(c_id=c_id, s_date=this_month, e_date=timezone.now())
    sold_device_this_year = sold_devices_iop(c_id=c_id, s_date=this_year, e_date=timezone.now())

    sold_device_last_week = sold_devices_iop(c_id=c_id, s_date=last_week, e_date=this_week)
    sold_device_last_month = sold_devices_iop(c_id=c_id, s_date=last_month, e_date=this_month)
    sold_device_last_year = sold_devices_iop(c_id=c_id, s_date=last_year, e_date=this_year)

    result_dict = {}
    result_lst = []

    result_dict['sold_this_week'] = sold_device_this_week.count()
    result_dict['sold_this_month'] = sold_device_this_month.count()
    result_dict['sold_this_year'] = sold_device_this_year.count()

    result_dict['sold_last_week'] = sold_device_last_week.count()
    result_dict['sold_last_month'] = sold_device_last_month.count()
    result_dict['sold_last_year'] = sold_device_last_year.count()

    result_lst.append(result_dict)

    return result_lst


def util_get_error_logs(c_id, e_id, mod_id, dev_type_id, err_code=None, s_date=None, e_date=None):
    if e_id:
        errs = HypernetPostData.objects.filter(
            Q(inactive_score__gt=0),
            device_id=e_id
        )

    elif dev_type_id:
        errs = HypernetPostData.objects.filter(Q(inactive_score__gt=0), device__entity_sub_type_id=dev_type_id)
    elif mod_id:
        errs = HypernetPostData.objects.filter(Q(inactive_score__gt=0), device__breed_id=mod_id)
    elif err_code:
        # TODO refactor to Options field .
        errs = HypernetPostData.objects.filter(Q(inactive_score__gt=0), inactive_score=err_code)
    else:
        # errs = HypernetPostData.objects.filter(Q(inactive_score__isnull=False) | Q(inactive_score__gt=0), customer_id=c_id)
        errs = HypernetPostData.objects.filter(Q(inactive_score__gt=0), customer_id=c_id)

    if s_date and e_date:
        errs = errs.filter(timestamp__range=[s_date, e_date])

    return errs


def new_get_error_logs(c_id, e_id, mod_id, dev_type_id, err_code=None, s_date=None, e_date=None):
    if e_id:
        errs = ErrorLogs.objects.filter(
            Q(inactive_score__gt=0),
            device_id=e_id
        )

    elif dev_type_id:
        errs = ErrorLogs.objects.filter(Q(inactive_score__gt=0), device__entity_sub_type_id=dev_type_id)
    elif mod_id:
        errs = ErrorLogs.objects.filter(Q(inactive_score__gt=0), device__breed_id=mod_id)
    elif err_code:
        # TODO refactor to Options field .
        errs = ErrorLogs.objects.filter(Q(inactive_score__gt=0), inactive_score=err_code)
    else:
        # errs = HypernetPostData.objects.filter(Q(inactive_score__isnull=False) | Q(inactive_score__gt=0), customer_id=c_id)
        errs = ErrorLogs.objects.filter(Q(inactive_score__gt=0), device__customer_id=c_id)

    if s_date and e_date:
        errs = errs.filter(datetime__range=[s_date, e_date])

    return errs


def util_get_usage_stats(c_id, e_id, mod_id=None, dev_type_id=None, s_date=None, e_date=None):
    if e_id:
        # device_derived_data = IopDerived.objects.filter(device_id=e_id)
        device_derived_data = EnergyConsumption.objects.filter(device_id=e_id)
        if len(device_derived_data)== 0:
            return []

        # elif mod_id:
        #     device_derived_data = IopDerived.objects.filter(device__breed_id=mod_id)
        # elif dev_type_id:
        #     device_derived_data = EnergyConsumption.objects.filter(device_id=e_id)

        # device_derived_data = IopDerived.objects.filter(device__entity_sub_type_id=dev_type_id)
    else:
        # device_derived_data = IopDerived.objects.filter(customer_id=c_id)
        device_derived_data = EnergyConsumption.objects.filter(device_id__customer_id=c_id)

    if s_date and e_date:
        # device_derived_data = device_derived_data.filter(timestamp__range=[s_date, e_date])
        device_derived_data = device_derived_data.filter(datetime__date__range=[s_date, e_date])

    return device_derived_data


def new_util_get_usage_stats(c_id, e_id, mod_id=None, dev_type_id=None, s_date=None, e_date=None):
    if e_id:
        usage_data = IopDerived.objects.filter(device_id=e_id)
    else:
        usage_data = IopDerived.objects.filter(customer_id=c_id)
    if s_date and e_date:
        usage_data = usage_data.filter(timestamp__date__range=[s_date, e_date])

    return usage_data.order_by('timestamp')


def util_get_device_usage_stats_average(c_id, e_id):
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)

    this_week = today - timedelta(days=7)
    last_week = this_week - timedelta(days=7)

    this_month = today - timedelta(days=30)
    last_month = this_month - timedelta(days=30)
    #
    # this_year = today - timedelta(days=365)
    # last_year = this_year - timedelta(days=365)


    this_day_average = util_get_usage_stats(c_id=c_id, e_id=e_id, s_date=yesterday, e_date=timezone.now())
    this_week_average = util_get_usage_stats(c_id=c_id, e_id=e_id, s_date=this_week, e_date=timezone.now())
    this_month_average = util_get_usage_stats(c_id=c_id, e_id=e_id, s_date=this_month, e_date=timezone.now())
    # this_year_average = util_get_usage_stats(c_id=c_id, e_id=e_id, s_date=this_year, e_date=timezone.now())
    data_dict = {}
    data_list = []
    last_day_average = util_get_usage_stats(c_id=c_id, e_id=e_id, s_date=yesterday, e_date=today)
    last_week_average = util_get_usage_stats(c_id=c_id, e_id=e_id, s_date=last_week, e_date=this_week)
    last_month_average = util_get_usage_stats(c_id=c_id, e_id=e_id, s_date=last_month, e_date=this_month)
    # last_year_average = util_get_usage_stats(c_id=c_id, e_id=e_id, s_date=last_year, e_date=this_year)
    if len(this_day_average)is not 0 and len(this_week_average)is not 0 and len(this_month_average) : #
        this_day_average = this_day_average.aggregate(this_day=Avg('energy_consumed'))
        this_week_average = this_week_average.aggregate(this_week=Avg('energy_consumed'))
        this_month_average = this_month_average.aggregate(this_month=Avg('energy_consumed'))
        # this_year_average = this_year_average.aggregate(this_year=Avg('energy_consumed'))
        data_dict['this_day_average'] = this_day_average['this_day']
        data_dict['this_week_average'] = this_week_average['this_week']
        data_dict['this_month_average'] = this_month_average['this_month']
    if len(last_day_average)is not 0 and len(last_week_average)is not 0 and len(last_month_average) :
        last_day_average = last_day_average.aggregate(last_day=Avg('energy_consumed'))
        last_week_average = last_week_average.aggregate(last_week=Avg('energy_consumed'))
        last_month_average = last_month_average.aggregate(last_month=Avg('energy_consumed'))
        # last_year_average = last_year_average.aggregate(last_year=Avg('energy_consumed'))
        data_dict['last_day_average'] = last_day_average['last_day']
        data_dict['last_week_average'] = last_week_average['last_week']
        data_dict['last_month_average'] = last_month_average['last_month']

    
    if data_dict:
        data_list.append(data_dict)
    
    return data_list


def util_usage_graph_data(c_id, e_id, data_type, mod_id=None, dev_type_id=None, s_date=None, e_date=None):
    result = []
    if e_id:
        data = util_get_usage_stats(c_id, e_id, mod_id=None, dev_type_id=None, s_date=s_date, e_date=e_date).order_by(
            'timestamp')
    elif mod_id:
        data = util_get_usage_stats(c_id, None, mod_id=mod_id, dev_type_id=None, s_date=s_date, e_date=e_date).order_by(
            'timestamp')
    elif dev_type_id:
        data = util_get_usage_stats(c_id, None, mod_id=None, dev_type_id=dev_type_id, s_date=s_date,
                                    e_date=e_date).order_by('timestamp')

    if data_type == 'energy':
        for d in data:
            dict = {}
            dict['energy_consumed'] = d.total_energy_consumed
            dict['timestamp'] = d.timestamp
            result.append(dict)

    if data_type == 'usage hours':

        if e_id:
            usage_data = IopDerived.objects.filter(device_id=e_id)
        else:
            usage_data = IopDerived.objects.filter(customer_id=c_id)
        if s_date and e_date:
            usage_data = usage_data.filter(timestamp__date__range=[s_date, e_date])

        usage_data = usage_data.order_by('-timestamp')

        for d in usage_data:
            dict = {}
            dict['active_duration'] = d.active_duration
            dict['timestamp'] = d.timestamp
            result.append(dict)

    if data_type == 'temperature':
        for d in data:
            dict = {}
            dict['average_temperature'] = d.average_temperature
            dict['timestamp'] = d.timestamp
            result.append(dict)
    return result


def new_energy_usage_data(c_id, e_id, breakdown, data_type, mod_id=None, dev_type_id=None, s_date=None, e_date=None):
    result = []
    saving_factor = 0

    if data_type == 'energy':
        saving_factor = list()
        if e_id:
            energy_data = EnergyConsumption.objects.filter(device_id=e_id)
        else:
            energy_data = EnergyConsumption.objects.filter(device_id__customer_id=c_id)
        if s_date and e_date:
            if s_date == e_date:
                print('here 12234aw')
                energy_data = energy_data.filter(datetime__date__gte=s_date) \
                    .extra(select={'date': 'datetime'}) \
                    .values('date') \
                    .annotate(smart_energy=Sum('energy_consumed'), regular_energy=Sum('ec_regular_appliance')) \
                    .order_by('date')
            else:
                print('here 12234')
                energy_data = energy_data.filter(datetime__date__range=[s_date, e_date]) \
                    .extra(select={'date': 'datetime::date'}) \
                    .values('date') \
                    .annotate(smart_energy=Sum('energy_consumed'), regular_energy=Sum('ec_regular_appliance')) \
                    .order_by('date')
               
        print(len(energy_data))
        for d in energy_data:
            dict = {}
            dict['smart_energy'] = d['smart_energy']
            dict['regular_energy'] = d['regular_energy']
            dict['timestamp'] = d['date']
            dict['total_saving']=d['regular_energy'] - d['smart_energy']
            saving_factor.append(d['regular_energy'] - d['smart_energy'])
            result.append(dict)

        if len(saving_factor) > 1:
            result.append({'saving_factor': sum(saving_factor)})
        else:
            result.append({'saving_factor': 0})

    if data_type == 'temperature':
        if e_id:
            energy_data = EnergyConsumption.objects.filter(device_id=e_id)
        else:
            energy_data = EnergyConsumption.objects.filter(device_id__customer_id=c_id)
        if s_date and e_date:
            if s_date == e_date:
                print("SAME START AND END DATE !!!!!!!!!!!!!!!!!!!")
                energy_data = energy_data.filter(datetime__date__gte=datetime.strptime(s_date, '%Y-%m-%d').date()) \
                    .extra(select={'date': 'datetime'}) \
                    .values('date') \
                    .annotate(average_temperature=Avg('average_temperature'), average_ctt=Avg('average_ctt')) \
                    .order_by('date')
            else:
                energy_data = energy_data.filter(datetime__date__range=[s_date, e_date]) \
                    .extra(select={'date': 'datetime::date'}) \
                    .values('date') \
                    .annotate(average_temperature=Avg('average_temperature'), average_ctt=Avg('average_ctt')) \
                    .order_by('date')
                

        for d in energy_data:
            dict = {}
            dict['average_temperature'] = d['average_temperature']
            dict['average_ctt'] = d['average_ctt']
            dict['timestamp'] = d['date']
            result.append(dict)

    if data_type == 'usage_hours':
        if e_id:
            energy_data = IopDerived.objects.filter(device_id=e_id)
        else:
            energy_data = IopDerived.objects.filter(device_id__customer_id=c_id)
        if s_date and e_date:
            if s_date == e_date:
                energy_data = energy_data.filter(
                    timestamp__date__gte=datetime.strptime(s_date, '%Y-%m-%d').date()) \
                    .extra(select={'date': 'timestamp'}) \
                    .values('date') \
                    .annotate(energy_avg=Sum('active_duration')) \
                    .order_by('date')
            else:
                energy_data = energy_data.filter(timestamp__date__range=[s_date, e_date]) \
                    .extra(select={'date': 'timestamp::date'}) \
                    .values('date') \
                    .annotate(energy_avg=Sum('active_duration')) \
                    .order_by('date')
                

        for d in energy_data:
            dict = {}
            dict['average_usage'] = d['energy_avg']
            dict['timestamp'] = d['date']
            result.append(dict)

    return result

def get_latest_value_from_pre_post(device):
    try:
        data = HypernetPreData.objects.get(device_id=device.id)
        return data

    except Exception as e:
        print(e)
        try:
            data=HypernetPostData.objects.get(device_id=device.id)
            return data
        except Exception as e:
            print(e)
def get_device_online_count(devices):
    try:
        
        
        logisticAggregations = LogisticAggregations.objects.filter(online_status=True)
              
        return logisticAggregations.count()
                
            
    except Exception as e:
        print(e)

def util_get_device_sub_type_listing(c_id, sub_type_id, mod_id,search, index_a=None, index_b=None,request=None):
    try:
        if sub_type_id:

            devices = Entity.objects.filter(type_id=DeviceTypeEntityEnum.IOP_DEVICE, entity_sub_type_id=sub_type_id,
                                            customer_id=c_id)
            if search:
                query=Q(name__icontains=search) | Q(device_name__device_id__icontains=search)
                devices=devices.filter(query)
        elif mod_id:
            devices = Entity.objects.filter(leased_owned_id=mod_id, type_id=DeviceTypeEntityEnum.IOP_DEVICE,
                                            customer_id=c_id)
                                        
        else:
            devices = Entity.objects.filter(customer_id=c_id)

        if request.query_params.get('limit') and request.query_params.get('offset'):
            paginator = LimitOffsetPagination()
            devices = paginator.paginate_queryset(devices,request)

        online_device_count=get_device_online_count(devices)

        if index_a >= 0 and index_b > 0:
            devices_list=[]
            device_ser=IOPApplianceFrontendsSerializer(devices,many=True).data

            for device in device_ser:
                try:
                    logisticAggregations = LogisticAggregations.objects.get(device_id=device['id'])
                    device['online_status'] = logisticAggregations.online_status
                    device['last_updated'] = logisticAggregations.last_updated
                    device['device_model'] = logisticAggregations.device.leased_owned.label
                except:
                    device['online_status'] = ''
                    device['last_updated'] = ''
                try:

                    query = ('''SELECT * FROM hypernet_hypernetpostdata WHERE "device_id" = {} ORDER BY timestamp DESC LIMIT 1''').format(device['id'])
                    cursor = connection.cursor()
                    cursor.execute(query)
                    columns = [col[0] for col in cursor.description]
                    row = cursor.fetchone()
                    object = dict(zip(columns, row))
                    # data = HypernetPostData.objects.filter(device_id=device['id']).latest('timestamp')
                    device['ctt']=object.get('ctt')
                    device['cdt']=object.get("cdt")
                    device['clm']=object.get("clm")
                    device['cht']=object.get("active_score")

                except:
                    device['ctt']=None

                    device['cdt']=None
                    device['clm']=None
                    device['cht']=None
                devices_list.append(device)

            return devices_list, len(devices),online_device_count
        else:
            return devices, 0,0
    except Exception as e:
        print(e)

def util_get_device_latest_data(c_id, d_id):
    entity_list = []
    last_data_dict = {}

    if d_id:
        latest_data = HypernetPreData.objects.filter(device_id=d_id, customer_id=c_id)
        if latest_data.count() == 0:
            latest_data = HypernetPostData.objects.filter(device_id=d_id, customer_id=c_id)

        if latest_data.count() > 0:
            latest_data = latest_data.latest('timestamp')
            last_data_dict['error_code'] = latest_data.inactive_score
            last_data_dict['on_off_status'] = latest_data.harsh_braking
            last_data_dict['temperature'] = latest_data.temperature
            last_data_dict['temperature_threshold'] = latest_data.active_score
            last_data_dict['amb_temperature'] = latest_data.ambient_temperature
            last_data_dict['timestamp'] = latest_data.timestamp
        else:
            latest_data_dict = None

        entity_list.append(last_data_dict)

    return entity_list


def util_generate_sharing_code(d_id):
    if d_id:
        chars = string.ascii_lowercase + string.digits
        random.seed = (os.urandom(1024))
        sharing_code = ''.join(random.choice(chars) for i in range(7))

        try:
            device = Entity.objects.get(pk=d_id)

        except:
            device = None

        if device:
            device.source_address = sharing_code
            device.save()

            return device.source_address

        else:
            return None
    else:
        return None


def util_use_sharing_code(sh_code, usr):
    if sh_code:
        try:
            device = Entity.objects.get(source_address=sh_code)
        except:
            device = None

        if device:
            dev_flag = ent_utils.save_user_device_assignment(dev=device, user=usr)
            device.source_address = None
            device.save()
        else:
            dev_flag = False

        return dev_flag


def manage_user_device_previliges(js_data):
    un_updated_users_lst = []
    updated_users_lst = []

    # for data in js_data['user_data']:
    for data in js_data:
        user_id = data['user_id']
        device_id = data['device_id']
        can_edit = data['can_edit']
        can_read = data['can_read']
        can_remove = data['can_remove']
        can_share = data['can_share']
        status = data['status']

        try:
            dev = UserEntityAssignment.objects.get(device_id=device_id, user_id=user_id,
                                                   type_id=DeviceTypeAssignmentEnum.IOP_DEVICE_USER_ASSIGNMENT,
                                                   status_id=OptionsEnum.ACTIVE)
        except UserEntityAssignment.DoesNotExist:
            dev = None

        if dev:
            '''
            if status is True:
                dev.status_id = OptionsEnum.INACTIVE
                dev.save()
            '''
            dev.can_edit = can_edit
            dev.can_read = can_read
            dev.can_remove = can_remove
            dev.can_share = can_share
            dev.save()
            updated_users_lst.append(user_id)

        else:
            un_updated_users_lst.append(user_id)

    return updated_users_lst, un_updated_users_lst


# Schedule related utils.


def check_overlapping_schedules(sleepmode, end_time, start_time, days_of_week):
    from hypernet.entity.job_V2.utils import check_conflicts_multi_days, check_conflicts_days_after
    if end_time > start_time:
        all_schedules = ActivitySchedule.objects.filter(primary_entity_id=sleepmode.primary_entity.id,
                                                        u_days_list__in=[days_of_week],
                                                        schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                        suspend_status=False, u_activity_end_time__gt=start_time,
                                                        u_activity_start_time__lt=end_time,
                                                        activity_type_id__in=[IopOptionsEnums.IOP_SCHEDULE_ON_DEMAND,
                                                                              IopOptionsEnums.IOP_SCHEDULE_DAILY,
                                                                              IopOptionsEnums.IOP_QUICK_SCHEDULE]).order_by(
            'u_activity_start_time')


    else:
        all_schedules = ActivitySchedule.objects.filter(primary_entity_id=sleepmode.primary_entity.id,
                                                        u_days_list__in=[days_of_week],
                                                        schedule_activity_status_id=OptionsEnum.ACTIVE,
                                                        suspend_status=False,
                                                        activity_type_id__in=[IopOptionsEnums.IOP_SCHEDULE_ON_DEMAND,
                                                                              IopOptionsEnums.IOP_SCHEDULE_DAILY,
                                                                              IopOptionsEnums.IOP_QUICK_SCHEDULE]).order_by(
            'u_activity_start_time')

        all_schedules = check_conflicts_multi_days(all_schedules, sleepmode)

        a_chs = check_conflicts_days_after(sleepmode, days_of_week)

        all_schedules = all_schedules.union(a_chs)

    return all_schedules


# def calculcate_ttr(ent, desired_temp, duration=None, t2=None, t1=None):
#     ttr = 0
#     model = ent.model
#
#     if model:
#         tpd = constants.tpd[model]
#         tpd = float(tpd)
#     else:
#         tpd = 1.0
#
#     data = get_latest_value(ent)
#     if data:
#         # t1 = float(data.active_score)
#         if not t2:
#             try:
#                 t2 = caculate_t2(des_temp=int(desired_temp), capacity=model, duration=float(duration))
#                 print('t2 is', t2)
#             except Exception as e:
#                 print(e)
#
#         if not t1:
#             t1 = 35
#         ttr = (t2 - t1) * tpd * 1.1  # float(data.active_score)
#
#     # else:
#     #     ttr = None
#     # if ttr and ttr > 0:
#     #     ttr = float(int(ttr))
#     # else:
#     #     ttr = 0
#     #
#     print(ttr)
#     return ttr, t2


def calculcate_ttr(ent, desired_temp, duration=None, t2=None, t1=None):
    model = ent.model
    if model:
        tpd = constants.tpd[model]
        tpd = float(tpd)
    else:
        tpd = 1.0

    data = get_latest_value(ent)
    if data:
        if t1 is None:
            t1 = float(data.active_score)
        if not t2:
            t2 = caculate_t2(des_temp=int(desired_temp), capacity=float(ent.model), duration=float(duration))

        # Hardcodding Desired temperature to 75
        t2= constants.DEFAULT_EVENT_DESIRED_TEMPERATURE
        ttr = (t2 - t1) * tpd * 1.1  # float(data.active_score)
        print('ttr in if    ', ttr)
    else:
        ttr = None

    if ttr > 0:
        ttr = float(int(ttr))
    else:
        ttr = 0

    #print('capacity:  ', float(ent.model))
    # print('entity post value:  ', data)
    # print('t1   /   device temperature:  ', float(data.active_score))
    #print('tpd  ', tpd)
    # print('duration:     ', duration)
    # print('desired temp:     ', desired_temp)
    print('ttr:     ', ttr)
    print('t2:     ', t2)
    return ttr, t2


# def caculate_t2(des_temp, capacity, duration):
#     t2 = 0
#     tm = constants.temp_mixed_water[des_temp]
#     ft = constants.ft
#
#     tc = 0
#     try:
#         tc = calcuate_temp_cairo_city()
#     except Exception as e:
#         print(e)
#
#     if duration and duration > 0:
#         fh = (float(capacity) * 0.6) / duration
#     else:
#         fh = 1
#
#     try:
#         t2 = ((1 / fh) * ((tm - tc) * ft)) + tc
#     except Exception as e:
#         print(e)
#
#     return t2 if t2 else 0

def caculate_t2(des_temp, capacity, duration):
    tm = constants.temp_mixed_water[des_temp]
    ft = constants.ft
    tc = calcuate_temp_cairo_city()
    fh = (capacity * 0.6) / duration
    t2 = ((1 / fh) * ((tm - tc) * ft)) + tc

    print('tm:  ', tm)
    print('ft:  ', ft)
    print('tc:  ', tc)
    print('fh:  ', fh)
    return t2


def get_latest_value(device):
    data = HypernetPreData.objects.filter(device_id=device.id).order_by('-timestamp')
    print(data)
    if data:
        data = data[0]
    else:
        
        data = HypernetPostData.objects.filter(device_id=device.id).last()

    return data


        

def check_shift_conflicts_in_queue(obj,
                                   ttr):  # util when there is a queue running and ttr of next queue (Q2) is calculated.
    # ttr time is subtracted from the Q2's start time to determine it's new time. Now if this resultant
    # subtracted time conflicts with running queue, this start time of Q2 is shifted as: (dt)Q2 + timedelta(minutes=ttr)

    flag = True
    current_obj = obj
    while flag == True:

        off_queues = ActivityQueue.objects.filter(is_on=False,
                                                  is_off=False, module=ModuleEnum.IOP,
                                                  primary_entity=current_obj.primary_entity,
                                                  ).order_by('activity_datetime')

        off_queues = off_queues.filter(Q(activity_datetime__lte=current_obj.activity_datetime) &
                                       Q(activity_end_datetime__gt=current_obj.activity_datetime) |
                                       Q(activity_datetime__lte=current_obj.activity_end_datetime) &
                                       Q(activity_end_datetime__gte=current_obj.activity_end_datetime))

        off_queues = off_queues.exclude(id=current_obj.id)
        if off_queues:
            for off_q in off_queues:
                start_datetime = off_q.activity_datetime

                start_datetime = start_datetime.replace(second=0, microsecond=0)
                current_start_time = current_obj.activity_datetime
                current_end_time = current_obj.activity_end_datetime
                current_start_time = current_start_time.replace(second=0, microsecond=0)
                current_end_time = current_end_time.replace(second=0, microsecond=0)
                end_datetime = off_q.activity_end_datetime
                end_datetime = end_datetime.replace(second=0, microsecond=0)

                if start_datetime <= current_start_time <= end_datetime or start_datetime <= current_end_time <= end_datetime:
                    off_q.activity_datetime = current_obj.activity_end_datetime
                    off_q.activity_end_datetime = off_q.activity_datetime + timedelta(
                        minutes=float(off_q.activity_schedule.notes))
                    off_q.save()

                    current_obj = off_q
                else:
                    flag = False
        else:
            flag = False

    return
def set_device_temperature_for_manual_mode(obj, temp):  # util for setting stt of device to desired temperature


    try:
        print(obj.device_name.device_id,'get obj name')
        url = 'https://IoTHWLabs.azure-devices.net/twins/{}/methods?api-version=2018-06-30'.format(obj.device_name.device_id)

        print("URL : ", url)
        res = requests.post(url=url,
                            json={'methodName': 'stt', 'payload': {'t': '{}'.format(temp),
                                                                    },
                                'responseTimeoutInSeconds': 30},
                            headers={
                                'Authorization': 'SharedAccessSignature sr=IoTHWLabs.azure-devices.net&sig=5EeO2kvTkr0OgO8tS9OKFT9%2Bbam%2B8MIyABNYXZqKpwg%3D&se=1721152990&skn=iothubowner'}

                            )
        print("RESPONSE disable mode is true: ", res.status_code)
        signal_r_failure(res, obj, temp)

        print("BELOW SIGNALR FAILURE CALL AT THE END")
        return res.status_code
    except Exception as f:
        print(f)
        print("INSIDE ELSE IN SET TEMP !!!!!!!!!!!!!!!")
        url = 'https://IoTHWLabs.azure-devices.net/twins/{}/methods?api-version=2018-06-30'.format(
            obj.device_name.device_id)

        print("URL : ", url)
        res = requests.post(url=url,
                            json={'methodName': 'stt', 'payload': {'t': '{}'.format(temp),
                                                                    },
                                    'responseTimeoutInSeconds': 30},
                            headers={
                                'Authorization': 'SharedAccessSignature sr=IoTHWLabs.azure-devices.net&sig=5EeO2kvTkr0OgO8tS9OKFT9%2Bbam%2B8MIyABNYXZqKpwg%3D&se=1721152990&skn=iothubowner'}

                            )
        print("RESPONSE CODE FROM SIGNALR HIT: ", res.status_code)
        signal_r_failure(res, obj, temp)

        print("BELOW SIGNALR FAILURE CALL AT THE END")
        return res.status_code

        return res.status_code
    
def set_device_temperature_for_quick_sch(obj, temp):  # util for setting stt of device to desired temperature
    try:
        url = 'https://IoTHWLabs.azure-devices.net/twins/{}/methods?api-version=2018-06-30'.format(obj.device_name.device_id)

        print("URL : ", url)
        res = requests.post(url=url,
                            json={'methodName': 'stt',
                                'payload': {'t': '{}'.format(temp), },
                                'responseTimeoutInSeconds': 30},
                            headers={
                                'Authorization': 'SharedAccessSignature sr=IoTHWLabs.azure-devices.net&sig=5EeO2kvTkr0OgO8tS9OKFT9%2Bbam%2B8MIyABNYXZqKpwg%3D&se=1721152990&skn=iothubowner'}

                            )
        print("RESPONSE CODE FROM SIGNALR HIT: ", res.status_code)

        # signal_r_failure(res, obj.device_name.device_id, temp)
        print("BELOW SIGNALR FAILURE CALL AT THE END")
        return res.status_code
    except Exception as e:
        print(e)
    
def set_device_temperature(obj, temp, ent=None):  # util for setting stt of device to desired temperature

    if not ent:
        if obj.primary_entity:
            print('obj primary_entity   ', obj.primary_entity)
            if obj.primary_entity.device_name:
                appliance_id = obj.primary_entity.device_name.device_id
            else:
                appliance_id = None
        else:
            appliance_id = None

        url = 'https://IoTHWLabs.azure-devices.net/twins/{}/methods?api-version=2018-06-30'.format(appliance_id)

        print("URL : ", url)
        res = requests.post(url=url,
                          json={'methodName': 'stt',
                                'payload': {'t': '{}'.format(temp), },
                                'responseTimeoutInSeconds': 30},
                          headers={
                              'Authorization': 'SharedAccessSignature sr=IoTHWLabs.azure-devices.net&sig=5EeO2kvTkr0OgO8tS9OKFT9%2Bbam%2B8MIyABNYXZqKpwg%3D&se=1721152990&skn=iothubowner'}

                          )
        print("RESPONSE CODE FROM SIGNALR HIT: ", res.status_code)

        signal_r_failure(res, obj.primary_entity, temp)
        print("BELOW SIGNALR FAILURE CALL AT THE END")
        return res.status_code
    else:
        try:
            print("INSIDE ELSE IN SET TEMP !!!!!!!!!!!!!!!")
            print('ent device:  ', ent)
            url = 'https://IoTHWLabs.azure-devices.net/twins/{}/methods?api-version=2018-06-30'.format(ent.device.device_name.device_id)

            print("URL : ", url)
            res = requests.post(url=url,
                              json={'methodName': 'stt', 'payload': {'t': '{}'.format(temp),
                                                                     },
                                    'responseTimeoutInSeconds': 30},
                              headers={
                                  'Authorization': 'SharedAccessSignature sr=IoTHWLabs.azure-devices.net&sig=5EeO2kvTkr0OgO8tS9OKFT9%2Bbam%2B8MIyABNYXZqKpwg%3D&se=1721152990&skn=iothubowner'}

                              )
            print("RESPONSE CODE FROM SIGNALR HIT: ", res.status_code)
            signal_r_failure(res, ent, temp)

            print("BELOW SIGNALR FAILURE CALL AT THE END")
            return res.status_code
        except Exception as f:
            print(f)
            print("INSIDE ELSE IN SET TEMP !!!!!!!!!!!!!!!")
            print('ent device:  ', ent)
            url = 'https://IoTHWLabs.azure-devices.net/twins/{}/methods?api-version=2018-06-30'.format(
                ent.device_name.device_id)

            print("URL : ", url)
            res = requests.post(url=url,
                                json={'methodName': 'stt', 'payload': {'t': '{}'.format(temp),
                                                                       },
                                      'responseTimeoutInSeconds': 30},
                                headers={
                                    'Authorization': 'SharedAccessSignature sr=IoTHWLabs.azure-devices.net&sig=5EeO2kvTkr0OgO8tS9OKFT9%2Bbam%2B8MIyABNYXZqKpwg%3D&se=1721152990&skn=iothubowner'}

                                )
            print("RESPONSE CODE FROM SIGNALR HIT: ", res.status_code)
            signal_r_failure(res, ent, temp)

            print("BELOW SIGNALR FAILURE CALL AT THE END")
            return res.status_code

            return res.status_code


def retry_mechanism_set_device_temperature(obj, temp, ent=None):  # util for setting stt of device to desired temperature

    if not ent:
        if obj.primary_entity:
            print('obj primary_entity   ', obj.primary_entity)
            if obj.primary_entity.device_name:
                appliance_id = obj.primary_entity.device_name.device_id
            else:
                appliance_id = None
        else:
            appliance_id = None

        url = 'https://IoTHWLabs.azure-devices.net/twins/{}/methods?api-version=2018-06-30'.format(appliance_id)

        print("URL : ", url)
        res = requests.post(url=url,
                          json={'methodName': 'stt',
                                'payload': {'t': '{}'.format(temp), },
                                'responseTimeoutInSeconds': 30},
                          headers={
                              'Authorization': 'SharedAccessSignature sr=IoTHWLabs.azure-devices.net&sig=5EeO2kvTkr0OgO8tS9OKFT9%2Bbam%2B8MIyABNYXZqKpwg%3D&se=1721152990&skn=iothubowner'}

                          )
        print("RESPONSE CODE FROM SIGNALR HIT: ", res.status_code)

        retry_mechanism_signal_r_failure(res, obj.primary_entity, temp)
        print("BELOW SIGNALR FAILURE CALL AT THE END")
        return res.status_code
    else:
        try:
            print("INSIDE ELSE IN SET TEMP !!!!!!!!!!!!!!!")
            print('ent device:  ', ent)
            url = 'https://IoTHWLabs.azure-devices.net/twins/{}/methods?api-version=2018-06-30'.format(ent.device.device_name.device_id)

            print("URL : ", url)
            res = requests.post(url=url,
                              json={'methodName': 'stt', 'payload': {'t': '{}'.format(temp),
                                                                     },
                                    'responseTimeoutInSeconds': 30},
                              headers={
                                  'Authorization': 'SharedAccessSignature sr=IoTHWLabs.azure-devices.net&sig=5EeO2kvTkr0OgO8tS9OKFT9%2Bbam%2B8MIyABNYXZqKpwg%3D&se=1721152990&skn=iothubowner'}

                              )
            print("RESPONSE CODE FROM SIGNALR HIT: ", res.status_code)
            retry_mechanism_signal_r_failure(res, ent, temp)

            print("BELOW SIGNALR FAILURE CALL AT THE END")
            return res.status_code
        except Exception as f:
            print(f)
            traceback.print_exc()
            return res.status_code


def retry_mechanism_signal_r_failure(signal_r_response, device, temperature):
    try:
        print('INSIDE SIGNALR FAILURE EXCEPTION !!!!  ', device)
        row_to_update = ReconfigurationTable.objects.get(device=device.device)
        row_to_update.failure_code = signal_r_response.status_code
        row_to_update.temperature_set = temperature
        row_to_update.datetime = datetime.now()
        print("Updating Reconfiguration table")
        row_to_update.save()
        print("Updated RECONFIGURATION TABLE !!!!")
    except Exception as e:
        print("INSIDE EXCEPTION in retry mechanism signalr failure")
        traceback.print_exc()


def signal_r_failure(signal_r_response, device, temperature):
    try:
        print('device in try cash   ', device)
        row_to_update = ReconfigurationTable.objects.get(device=device)
        row_to_update.failure_code = signal_r_response.status_code
        row_to_update.temperature_set = temperature
        row_to_update.datetime = datetime.now()
        print("Updating Reconfiguration table")
        row_to_update.save()
        print("Updated RECONFIGURATION TABLE !!!!")
    except Exception as e:
        print("ReconfigurationTable Execption:      ", e)
        row_to_save = ReconfigurationTable(device=device, temperature_set=temperature, failure_code=signal_r_response.status_code)
        row_to_save.save()


def get_user_privelages_info(user, appliance_id):
    try:
        user_appliance_assignment = UserEntityAssignment.objects.get(user=user, device_id=appliance_id,
                                                                     status_id=OptionsEnum.ACTIVE)
    except:
        user_appliance_assignment = None

    return user_appliance_assignment


def shift_queues(sleep_mode,
                 queue):  # This util is called when a sleep mode is over(becomes) inactive and ttr is recalculated.
    # Shifting will occur if this ttr is added into the queue's time to make a new time. If this new
    # time conflicts with queues, those queues will be shifted accordingly.

    calculcate_ttr(sleep_mode.primary_entity, )


def overlapping_queues_revised(queue):
    all_schedules = ActivityQueue.objects.filter((Q(activity_datetime__gt=queue.activity_datetime) &
                                                  Q(activity_end_datetime__lte=queue.activity_datetime)) |
                                                 (Q(activity_datetime__gt=queue.activity_end_datetime) &
                                                  Q(activity_end_datetime__lte=queue.activity_end_datetime))
                                                 , primary_entity=queue.primary_entity)

    all_schedules = all_schedules.exclude(id=queue.id).order_by('activity_datetime')

    current_obj = queue
    for o in all_schedules:
        old_time = o.activity_datetime
        o.activity_datetime = current_obj.activity_end_datetime

        buffer = (o.activity_datetime - old_time).min

        o.activity_end_datetime = buffer + o.activity_end_datetime

        o.save()

    return


def update_online_status_iop_device(en, t_timestamp):
    try:
        email_list = constants.email_list_iop
        status = IopAggregation.objects.get(device=en)
        if status.online_status:
            print('Online Entity: ' + status.device.name + ' Status: ' + str(status.online_status))
            try:
                device = Devices.objects.get(device=en)
                device.timestamp = timezone.now()
                device.save()
            except:
                pass

        else:
            status.online_status = True
            print('{} now online'.format(en.name))
            # status.last_updated = t_timestamp
            status.save()
            send_mail('Hypernet Prod Device Online', 'Device is back online id:' + en.name + ' time: ' + str(
                t_timestamp),
                      'support@hypernymbiz.com', email_list, fail_silently=False)
            # print('Offline Entity: ' + status.device.name + ' Status: ' + str(status.online_status))
        return True
    except:
        return False


def calcuate_temp_cairo_city():
    try:
        response = requests.get(constants.open_weather_api_url)
        # print(response.json())
        x = response.json()

        temp = x['main']['temp']
        return temp

    except Exception as e:
        print(e)
        return 27

        # json method of response object
        # convert json format data into
        # python format data


# def calculate_tau(t2, des_temp, duration, ent):
#     tm = constants.temp_mixed_water[des_temp]
#     tc = 27.0  # calcuate_temp_cairo_city()
#     q = constants.q
#     fh = ((tm - tc) / (t2 - tc)) * q
#     duration = float(duration)
#     model = float(ent.model)
#     tau = ((tc * duration * fh) + (t2 * (model - (fh * duration)))) / model
#     return tau

def get_t1_temp(ent):
    t1 = get_latest_value(ent).active_score
    if t1<55:
        t1=55
    while t1 %5 is not 0:
        t1 -=1
    return t1

def TTR_calculation_use_now_events(des_temp, duration, ent):
    print('in new function =============')

    tm = constants.temp_mixed_water[int(des_temp)]

    tc = calcuate_temp_cairo_city()

    Q = constants.q

    duration = float(duration)
    print('duration  :', duration)
    print('des_temp ', des_temp)
    print('duration ', duration)
    print('ent  ', ent)
    print('q  :', Q)
    print('tc  :', tc)
    print('tm  :', tm)

    model = ent.model
    if model:
        tpd = constants.tpd[model]
        tpd = float(tpd)
    else:
        tpd = 1.0

    capacity = int(ent.model)

    t1 = get_latest_value(ent).active_score
    print('t1  :', t1)
    print('cap  :', capacity)
    print('tpd ', tpd)
    th = get_t1_temp(ent)
    print('all good')
    # for loop from 30 to 75 with increment by 5
    for x in range(int(th), 80, 5):
        th = x
        fh = (tm - tc) * (Q / (th - tc))
        print('fh in For Loop:  ', fh)
        if (fh * duration) <= (0.6 * capacity):
            print('th value in foor loop:  ', th)
            break

    if (th > 75):
        th = 75
    print('th   ', th)
    ttr = (th - t1) * 1.1 * tpd

    if ttr < 0:
        ttr = 3
    return int(ttr),th


def calculate_tau(t2, des_temp, duration, ent):
    tm = constants.temp_mixed_water[des_temp]
    tc = calcuate_temp_cairo_city()
    q = constants.q
    # 𝐹ℎ = (𝑇𝑚−𝑇𝑐) / (𝑇ℎ−𝑇𝑐) *Q
    fh = ((tm - tc) / (t2 - tc)) * q
    duration = float(duration)
    model = float(ent.model)
    # tau = ((tc * duration * fh) + (t2 * (model - (fh * duration)))) / model
    tau = (tc * fh * duration + t2 * (model - (fh * duration))) / (model) + (1.8 * (duration - 5) * 60 * 0.9) / (
    4.18 * model)

    print('tau:     ', tau)
    print('tc:     ', tc)
    print('fh:     ', fh)
    print('dur:     ', duration)
    print('t2:     ', t2)
    print('model:     ', model)
    print('tm:     ', tm)
    print('Q:     ', q)
    return tau


def detect_drop_in_temperature(ent):
    first_obj = HypernetPreData.objects.filter(device=ent).last()
    if first_obj:
        scnd_obj = HypernetPreData.objects.filter(device=ent,
                                                  timestamp__hour=first_obj.timestamp.hour,
                                                  timestamp__minute=(
                                                      first_obj.timestamp - timedelta(minutes=1)).minute).last()
        if scnd_obj:
            if first_obj.active_score - scnd_obj.active_score < 0:
                return True
            else:
                return False
        else:
            scnd_obj = HypernetPostData.objects.filter(device=ent).last()
            if scnd_obj:
                if first_obj.active_score - scnd_obj.active_score < 0:
                    return True
                else:
                    return False
            else:
                return False

    else:
        first_obj = HypernetPostData.objects.filter(device=ent).last()

        if first_obj:
            scnd_obj = HypernetPreData.objects.filter(device=ent,
                                                      timestamp__hour=first_obj.timestamp.hour,
                                                      timestamp__minute=(first_obj.timestamp - timedelta(
                                                          minutes=1)).minute).last()
            if scnd_obj:
                if first_obj.active_score - scnd_obj.active_score < 0:
                    return True
                else:
                    return False
            else:
                scnd_obj = HypernetPostData.objects.filter(device=ent,
                                                           timestamp__hour=first_obj.timestamp.hour,
                                                           timestamp__minute=(first_obj.timestamp - timedelta(
                                                               minutes=1)).minute).last()
                if scnd_obj:
                    if first_obj.active_score - scnd_obj.active_score < 0:
                        return True
                    else:
                        return False
                else:
                    return False
        else:
            return False


def new_detect_drop_in_temperature(ent):
    try:
        import datetime as date_time

        #   get latest data from HypernetPreData
        latest_data = HypernetPreData.objects.filter(device=ent).latest('timestamp')
        print('latest data active score %d' % latest_data.active_score)
        #   get last 5 min data from HypernetPreData
        #/// adding line 1137
        print("previous data timestamp calculation",(latest_data.timestamp - timedelta(minutes=5)))
        #/// adding lines 1139 to 1143
        previous_data = HypernetPostData.objects.filter(device=ent, timestamp__gte=(latest_data.timestamp - timedelta(minutes=5))).order_by('timestamp')
        if previous_data.count() == 0:
            #   get last 5 min data from HypernetPostData
            previous_data = HypernetPreData.objects.filter(device=ent, timestamp__gte=(
                latest_data.timestamp - timedelta(minutes=5))).order_by('timestamp')

        #/// previous_data = HypernetPreData.objects.filter(device=ent, timestamp__gte=(
        #///     latest_data.timestamp - timedelta(minutes=5))).order_by('timestamp')
        #///
        #/// if previous_data.count() == 0:
        #///     #   get last 5 min data from HypernetPostData
        #///     previous_data = HypernetPostData.objects.filter(device=ent, timestamp__gte=(
        #///         latest_data.timestamp - timedelta(minutes=5))).order_by('timestamp')

        #/// adding lines 1154 and 1155
        print("previous data first time stamp", previous_data.first().timestamp)
        print("previous data last time stamp", previous_data.last().timestamp)
        # find difference between theoretical tpd and actual tpd between two latest temperature differences
        if latest_data.heartrate_value == 4:
            try:
                print('chs === ', latest_data.heartrate_value)

                #/// theoretical_tpd = constants.tpd[ent.model]
                #///adding line 1163
                theoretical_tpd= constants.degree_drop_per_minute_in_sec[ent.model]
                # this one is correct for chs 4

                #/// data2 = previous_data.filter(active_score__lt=latest_data.active_score).latest('timestamp')
                # selecting last minute data from pre / post data
                #  added line 1169 to 1170
                print("date time calculation ",(latest_data.timestamp - timedelta(seconds=theoretical_tpd)))
                data2 = previous_data.filter(timestamp__gte=(latest_data.timestamp - timedelta(seconds=theoretical_tpd))).earliest('timestamp')
                print('previous temperature ', data2.active_score, ' ', data2.timestamp.time())
                print('current temperature ', latest_data.active_score, ' ', latest_data.timestamp.time())

                #/// if latest_data.active_score > data2.active_score:
                #/// adding line 1176
                if latest_data.active_score <= data2.active_score:
                    #/// measured_tpd = (latest_data.timestamp - data2.timestamp).seconds / 60
                    #/// adding lines from 1179 to 1185
                    tempurate_difference =float(data2.active_score - latest_data.active_score)
                    print('temperature difference ',tempurate_difference)
                    if tempurate_difference > 0.0:
                        print("debug:", "usage found")
                        return True
                    else:
                        return False

                    #/// print('measured tpd  ', measured_tpd)
                    #/// if measured_tpd > theoretical_tpd:
                    #///     return True
                    #/// else:
                    #///     return False

                else:
                    print("debug:", "usage found before differnce  direct usage ")
                    return False
            except Exception as e:
                print(e)
                return False

        # find temperature difference in last 5 minutes
        elif latest_data.heartrate_value == 3:
            print('chs === ', latest_data.heartrate_value)

            print('latest_data temperature ', latest_data.active_score, ' ', latest_data.timestamp)
            print('previous_data temperature ', (previous_data.first()).active_score, ' ',
                  (previous_data.first()).timestamp)
            if float((previous_data.first()).active_score - latest_data.active_score) > 5.0:
                return True
            else:
                return False
        else:
            return False
    except Exception as e:
        print(e)
        return False


def shift_schedule_to_next_day(queue, current_datetime):
    # Check if for queue, the related schedule is of type recurring or daily
    if queue.activity_schedule.activity_type.id in [IopOptionsEnums.IOP_QUICK_SCHEDULE,
                                                    IopOptionsEnums.IOP_SCHEDULE_DAILY]:

        # This mechanism is to shift the schedule to next weekday by changing it's datetime fields

        old_start_dt = queue.activity_schedule.old_start_dt
        new_start_dt = queue.activity_schedule.new_start_dt
        old_end_dt = queue.activity_schedule.old_end_dt
        new_end_dt = queue.activity_schedule.new_end_dt

        days_list = queue.activity_schedule.days_list
        u_days_list = queue.activity_schedule.u_days_list

        today = current_datetime.date()

        if today.weekday() == int(queue.activity_schedule.u_days_list):  # Shifting schedule's date to next weekday
            upcoming_date = today + timedelta(days=7)
        else:  # Redundant statement, can be removed, the if statement will always be executed
            upcoming_date = today + timedelta((int(u_days_list) - today.weekday()) % 7)

        queue.activity_schedule.start_date = upcoming_date
        queue.activity_schedule.new_start_dt = parse(str(upcoming_date) + '-' + str(old_start_dt.time()))
        queue.activity_schedule.new_end_dt = parse(str(upcoming_date) + '-' + str(
            old_start_dt.time()))  # new_start_dt and new_end_dt will be same at this step
        queue.activity_schedule.u_days_list = queue.activity_schedule.new_start_dt.weekday()
        queue.activity_schedule.end_date = queue.activity_schedule.new_end_dt.date()
        queue.activity_schedule.u_start_time = queue.activity_schedule.new_start_dt.time()

        if old_start_dt.date() != old_end_dt.date():  # Checking if schedule spans multiple days
            queue.activity_schedule.multi_days = True

            queue.activity_schedule.new_end_dt = queue.activity_schedule.new_end_dt + timedelta(
                days=1)  # new_start_dt and new_end dt which were same are now different by checking if schedule spanned multple days. So the ending date of schedule will be greated
            queue.activity_schedule.end_date = queue.activity_schedule.new_end_dt.date()
        else:
            queue.activity_schedule.multi_days = False

        queue.activity_schedule.u_end_time = queue.activity_schedule.new_end_dt.time()
        queue.save()
        queue.activity_schedule.save()

    else:  # If schedule is of type use_now or once, then mark is at inative as it's lifecyce will be completed here.
        queue.activity_schedule.schedule_activity_status = Options.objects.get(id=OptionsEnum.INACTIVE)
        queue.activity_schedule.save()

    ActivitySchedule.objects.filter(suspended_by=queue.activity_schedule).update(
        suspended_by=None)  # Updating suspended_by to None so that when queue that supends it will be deleted, doesnot affects other schedules
    return


def util_get_device_users(entity_id, type_id=DeviceTypeAssignmentEnum.IOP_DEVICE_USER_ASSIGNMENT):
    user_assignments = UserEntityAssignment.objects.filter(device_id=entity_id,
                                                           type_id=type_id,
                                                           status_id=OptionsEnum.ACTIVE)

    return user_assignments


def util_get_saving_factor_per_day(date):
    A = (ActivitySchedule.objects.filter(created_datetime__date=date)).count()
    print("activitySchedule count", A)
    import math
    saving_factor = 0.1 + (0.8 * (math.e ** (-0.17 * A)))

    return saving_factor


def util_get_energy_saving_percentage(saving_factor_per_day, ec_regular_applaince_per_day):
    if ec_regular_applaince_per_day > 0:

        percentage_es = Decimal(saving_factor_per_day) / (ec_regular_applaince_per_day)

    else:
        percentage_es = 0

    return percentage_es


# Returns number of records in Hypernetpost data uptil now
def get_energy_consumed_from_hypernet_post(device, one_hour_before, now_time):
    post_data = HypernetPostData.objects.filter(device=device.device, heartrate_value=4, timestamp__gte=one_hour_before,
                                                timestamp__lte=now_time).count()
    print('Post data count   ', post_data)
    return (post_data) * 0.005000004


def get_number_of_events(entity_id, start_date, end_date, eventsToExclude=(IopOptionsEnums.RECURRING_SLEEP_MODE,)):
    # query = ActivitySchedule.objects \
    #     .filter(primary_entity_id=entity_id,
    #             schedule_activity_status_id=OptionsEnum.ACTIVE)
    query = ActivitySchedule.objects.filter(primary_entity_id=entity_id)
    if end_date:
        query = query.filter(start_date__date__gte=start_date, end_date__date__lte=end_date) \
            .exclude(activity_type_id__in=eventsToExclude) \
            .values('activity_type_id') \
            .annotate(num_events=Count('activity_type_id')) \
            .order_by('-num_events')

    else:
        query = query.filter(start_date__date=start_date) \
            .values('created_datetime', 'notes', 'activity_type_id', 'modified_by', 'modified_by__first_name',
                    'activity_start_time', 'start_date') \
            .order_by('activity_start_time')

    return query


def util_get_entity_events_count(entity_id, start_date, end_date, eventsToExclude=[]):
    try:
                
        time='19:00:00'
            
        start_date_data = datetime.strptime(start_date, '%Y-%m-%d').date() - timedelta(1)
        start_time = datetime.strptime(time, "%H:%M:%S").time()
        
        start_date=datetime.combine(start_date_data, start_time)
        
       
        
        
        time='18:59:59'
            
        end_date_data = datetime.strptime(end_date, '%Y-%m-%d').date()
        end_time = datetime.strptime(time, "%H:%M:%S").time()
        
        end_date=datetime.combine(end_date_data, end_time)
        
        # start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
        # end_date=datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
        
        schs = ActivitySchedule.objects.filter(new_start_dt__date__range=[start_date, end_date], primary_entity_id=entity_id)

        schs = schs \
            .exclude(activity_type_id__in=eventsToExclude) \
            .values('activity_type_id', 'primary_entity_id','new_start_dt') \
            .annotate(num_events=Count('activity_type_id')) \
            .order_by('-num_events')
        print(schs)
        return schs
    except Exception as e:
        print(e)
        return []


def select_rand_qs_duration(start_dt, capacity):
    index = random.randint(0, 2)
    rand_temp = constants.temperatures[index]
    duration = constants.rand_durations[capacity][rand_temp]
    return duration, rand_temp


def shift_to_normal_temp(entity, current_datetime):
    queues = ActivityQueue.objects.filter(primary_entity=entity,
                                          is_on=False, is_off=False).order_by('activity_datetime')
    if queues:
        queue = queues[0]

        print("=-=-=-=-=-queue:    ", queue)

        ttr, _ = calculcate_ttr(ent=entity, desired_temp=queue.activity_schedule.action_items,
                                duration=queue.activity_schedule.notes)

        queue.activity_datetime = queue.activity_datetime.replace(tzinfo=None)
        time_diff = ((queue.activity_datetime - current_datetime).total_seconds() / 60)

        print("time_difference:     ", time_diff)
        print("ttr:     ", ttr)

        if time_diff > ttr:
            print("set temperature in IF")
            set_device_temperature(obj=queue, temp=str(constants.DEFAULT_TEMP))
    else:
        print("set temperature in ELSE")
        set_device_temperature(obj=None, temp=str(constants.DEFAULT_TEMP), ent=entity)


def create_iop_activity(a_s, state):
    activity = Activity(
        module=a_s.module,
        customer=a_s.customer,
        activity_schedule=a_s,
        primary_entity=a_s.primary_entity,
        activity_status=Options.objects.get(id=state)
    )

    return activity

def calculate_overlapping(temp_usage,duration,des_temp,volume_capacity):
    try:
        fh_duration=0.1
        uf_whcap=2
        whcap=volume_capacity
        if whcap is None:
            whcap=45
        th=temp_usage
        while fh_duration <= uf_whcap:
            if th is None:
                th=55
            else:
                th +=5
            tc=calcuate_temp_cairo_city()
            tm = calculate_mixed_water_temp(des_temp)
            UF=constants.UF
            
            print(th,'check th')
            print(tc,'cairo_city')
            Q=constants.Q
            
            fh=(float(tm)- float(tc)) / (float(th) - float(tc)) * float(Q)
            print(fh,'use now fh')
            fh_duration=fh * float(duration)
            print(fh_duration,'fh duration')
        
            uf_whcap=UF * whcap
            print(uf_whcap,'uf_whcap')
            if th==75:
                break
        return th

    except Exception as e:
        print(e)
    
def calculate_temperature_time_to_ready(duration,ttr,des_temp):
    try:
        tc=calcuate_temp_cairo_city()
        tm=float(des_temp)

        wh_cap=45
        Q=constants.Q
        uf=constants.UF
        th=(float(duration) * (float(tm)-float(tc))) / (uf * wh_cap) + tc
        print(th,'print th in time_to_Ready')

        fh=(float(tm)- float(tc)) / (float(th) - float(tc)) * float(Q)
        print(fh,'print fh in time_to_Ready')

        tf=(tc * fh * float(duration) + th * (wh_cap - (fh * float(duration)))) / (wh_cap + 1.8 * (float(duration) -5) *60 * 0.9) / (4.18 * wh_cap)
        print(tf,'temperatur check tf')


    except Exception as e:
        print(e)

def calculate_mixed_water_temp(des_temp):
    if des_temp ==constants.warm_water:
        return 37
    elif des_temp == constants.hot_water:
        return 40
    else:
        return 43