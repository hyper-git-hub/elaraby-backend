from __future__ import unicode_literals

import traceback

from django.core.exceptions import ObjectDoesNotExist
from rest_framework.authtoken.models import Token
from django.db.models import F
import datetime
from dateutil import parser
from hypernet.constants import *
from customer.models import CustomerClients
from hypernet.entity.job_V2.utils import util_get_activities
from hypernet.entity.utils import util_create_activity
from hypernet.models import Entity, \
    Assignment, HypernetPostData, Devices, HypernetPreData, CustomerDevice

from hypernet.serializers import CustomerClientsSerializer, DumpingSiteSerializer, RfidScannerSerializer, \
    ClientContractSerializer, ClientSupervisorSerializer, SortingFacilitySerializer, DriverSerializer, BinSerializer
from iof.models import ActivityData, ActivitySchedule, IofShifts, IncidentReporting
from hypernet.enums import *
from iof.models import Activity, BinCollectionData, ActivityQueue, LogisticAggregations
from user.models import User
from customer.models import CustomerPreferences
from iof.serializers import ActivityScheduleSerializer, ActivityDataSerializer
from django.utils import timezone
import pytz
from hypernet.notifications.utils import send_action_notification, save_users_group, send_notification_to_admin


def get_entity(e_id, c_id):
    if e_id:
        try:
            ent = Entity.objects.get(id=e_id, customer_id=c_id, status_id__in=[OptionsEnum.ACTIVE,OptionsEnum.INACTIVE])
        except:
            return None
        if ent.type.id == DeviceTypeEntityEnum.TRUCK:
            entity = ent.as_truck_json()
            try:
                driver = Assignment.objects.get(parent_id=e_id,  type_id=DeviceTypeAssignmentEnum.DRIVER_ASSIGNMENT, status_id=OptionsEnum.ACTIVE)
                entity['assigned_driver'] = driver.child.as_driver_json()
            except Exception as e:
                #print(str(e))
                pass
            territory = Assignment.objects.filter(parent_id=e_id, type_id=DeviceTypeAssignmentEnum.TERRITORY_ASSIGNMENT,
                                                  status_id=OptionsEnum.ACTIVE)
            # print(job)
            if territory:
                ter_list = []
                for ter in territory:
                    ter_list.append(ter.child.as_territory_json())
                if len(ter_list) == 1:
                    entity['assigned_territory'] = ter.child.as_territory_json()
                else:
                    entity['assigned_territory'] = ter_list

            # job = Assignment.objects.filter(parent_id=e_id, type_id=DeviceTypeAssignmentEnum.JOB_ASSIGNMENT,
            #                                 status_id=OptionsEnum.ACTIVE, child__job_status_id=IOFOptionsEnum.PENDING)
            j_list = []
          #  if job:

                # for j in job:
                #     j_list.append(j.child.as_job_json())
                # if len(j_list) == 1:
                #     entity['assigned_jobs'] = j.child.as_job_json()
                # else:
                #     entity['assigned_jobs'] = j_list
            jobs = Activity.objects.filter(primary_entity_id=e_id, activity_status_id= IOFOptionsEnum.ACCEPTED).values(
                'created_datetime', 'id', 'primary_entity_id',
                'primary_entity__name', 'actor_id', 'actor__name', 'activity_status__label', 'activity_status_id')

            if len(jobs) ==1:
                entity['assigned_activity'] = list(jobs)
            else:
                entity['assigned_activity'] = j_list + list(jobs)

            flag, activity = check_entity_on_activity(d_id=None,t_id=e_id,c_id=c_id)

            if flag is True:
                entity['on_activity'] = flag
                entity['activity_id'] = activity.id

            return entity

        elif ent.type.id == DeviceTypeEntityEnum.DRIVER:
            entity = ent.as_driver_json()
            try:
                truck = Assignment.objects.get(child_id=e_id, type_id=DeviceTypeAssignmentEnum.DRIVER_ASSIGNMENT,
                                               status_id=OptionsEnum.ACTIVE).parent
                entity['assigned_truck'] = truck.as_entity_json()
            # job = Assignment.objects.filter(parent_id=truck.parent.id, type_id = DeviceTypeAssignmentEnum.JOB_ASSIGNMENT, status=OptionsEnum.ACTIVE).first()
            except:
                pass
            # TRUCK OF DRIVER
            #j_list = []
            # if truck:
            #     entity['assigned_truck'] = truck.as_truck_json()
            #
            #     job = Assignment.objects.filter(child_id=e_id, type_id=DeviceTypeAssignmentEnum.JOB_ASSIGNMENT,
            #                                     status_id=OptionsEnum.ACTIVE, child__job_status_id=IOFOptionsEnum.PENDING)
            #     if job:
            #
            #         for j in job:
            #             j_list.append(j.child.as_job_json())
            #         if len(j_list) == 1:
            #             entity['assigned_jobs'] = j.child.as_job_json()
            #         else:
            #             entity['assigned_jobs'] = j_list
            jobs = Activity.objects.filter(actor_id=e_id, activity_status_id=IOFOptionsEnum.ACCEPTED).values(
                'created_datetime', 'id', 'primary_entity_id',
                'primary_entity__name', 'actor_id', 'actor__name', 'activity_status__label', 'activity_status_id')
            entity['assigned_jobs'] = list(jobs)
            entity['shift_status'] = check_entity_on_current_shift(e_id, None, c_id)
            flag, activity = check_entity_on_activity(d_id=e_id, t_id=None, c_id=c_id)
            if flag is True:
                entity['on_activity'] = flag
                entity['activity_id'] = activity.id

            return entity

        elif ent.type.id == DeviceTypeEntityEnum.FLEET:
            entity = ent.as_fleet_json()
            fleet_trucks = Assignment.objects.filter(child__parent_id=e_id, type_id = DeviceTypeAssignmentEnum.TRUCK_ASSIGNMENT).first()
            fleet_territory = Assignment.objects.filter(child__parent_id=e_id, type_id = DeviceTypeAssignmentEnum.TERRITORY_ASSIGNMENT).first()
            if fleet_trucks:
                entity['assigned_trucks'] = fleet_trucks.child.as_truck_json()
                entity['assigned_territory'] = fleet_territory.child.as_territory_json()
            return entity

        elif ent.type.id == DeviceTypeEntityEnum.TERRITORY:
            entity = ent.as_territory_json()
            truck = Assignment.objects.filter(child_id=e_id, parent__type_id= DeviceTypeEntityEnum.TRUCK , type_id=DeviceTypeAssignmentEnum.TRUCK_ASSIGNMENT).first()
            fleet = Assignment.objects.filter(child_id=e_id, parent__type_id= DeviceTypeEntityEnum.FLEET , type_id=DeviceTypeAssignmentEnum.TRUCK_ASSIGNMENT).first()
            if truck:
                entity['assigned_truck'] = truck.parent.as_truck_json()
            if fleet:
                entity['assigned_fleet'] = fleet.parent.as_fleet_json()
            return entity

        elif ent.type.id == DeviceTypeEntityEnum.JOB:
            entity = ent.as_job_json()
            try:
                truck = Assignment.objects.get(child_id=e_id,  type_id=DeviceTypeAssignmentEnum.JOB_ASSIGNMENT).parent
                driver = Assignment.objects.get(parent=truck, type_id=DeviceTypeAssignmentEnum.DRIVER_ASSIGNMENT).child
            except:
                truck = None
                driver = None
            if truck:
                entity['assigned_truck'] = truck.as_truck_json()
            if driver:
                entity['assigned_driver'] = driver.as_driver_json()
            return entity

        elif ent.type.id == DeviceTypeEntityEnum.BIN:
            entity = ent.as_bin_json()
            try:
                truck = Assignment.objects.get(child_id=e_id,type_id=DeviceTypeAssignmentEnum.BIN_ASSIGNMENT, status_id=OptionsEnum.ACTIVE)
                entity['assigned_truck'] = truck.parent.as_truck_json()
            except:
                entity['assigned_truck'] = None
            try:
                contract = Assignment.objects.get(parent_id=e_id,type_id=DeviceTypeAssignmentEnum.CONTRACT_ASSIGNMENT, child__type_id=DeviceTypeEntityEnum.CONTRACT, status_id=OptionsEnum.ACTIVE)
                entity['assigned_contract'] = contract.child.as_entity_json()
            except:
                entity['assigned_contract'] = None
            try:
                area = Assignment.objects.get(parent_id=e_id,type_id=DeviceTypeAssignmentEnum.AREA_ASSIGNMENT, child__type_id=DeviceTypeEntityEnum.AREA, status_id=OptionsEnum.ACTIVE)
                entity['assigned_area'] = area.child.as_entity_json()
            except:
                entity['assigned_area'] = None
            try:
                current_collection = BinCollectionData.objects.get(action_item_id=e_id, status_id=IOFOptionsEnum.UNCOLLECTED)
                entity['activity_status'] = current_collection.activity.activity_status.id
                entity['current_activity'] = current_collection.activity.id
            except:
                entity['activity_status'] = None
                entity['current_activity'] = None
            
            bin_collection_data = BinCollectionData.objects.filter(action_item_id=e_id,
                                                                   status_id__in =[IOFOptionsEnum.WASTE_COLLECTED, IOFOptionsEnum.BIN_PICKED_UP]).order_by('-timestamp')
            
            bin_collection = []
            if bin_collection_data:
                for obj in bin_collection_data:
                    if not entity.get('last_collection'):
                        entity['last_collection'] = str(obj.timestamp)
                    bin_collection.append(obj.as_bin_collection_data_json())
                    
                entity['bin_collection_data'] = bin_collection
                
            else:
                entity['bin_collection_data'] = None
                entity['last_collection'] = None
            return entity
    else:
        return Entity.objects.filter(customer__id=c_id)


def get_entity_brief(c_id, m_id, t_id, context, e_id=None):
    # Entity Removed in Merge
    entity_dict = {}
    entity_list = []
    count = 0
    if c_id:
        # TODO module_id check to be added(REASON NO DATA)
        if int(t_id) == DeviceTypeEntityEnum.JOB:
            ent = ActivitySchedule.objects.filter(customer_id=c_id)

        elif t_id:
            ent = Entity.objects.filter(customer_id=c_id, type_id=t_id).exclude(status_id=OptionsEnum.DELETED).order_by(
                '-modified_datetime')
        elif e_id:
            ent = Entity.objects.filter(customer_id=c_id, id=e_id).exclude(status_id=OptionsEnum.DELETED).order_by(
                '-modified_datetime')



        for obj in ent:
            if int(t_id) == DeviceTypeEntityEnum.JOB:
                activity_data = ActivityScheduleSerializer(obj, context=context)
                entity_dict = activity_data.data

            elif obj.type_id == DeviceTypeEntityEnum.TRUCK:
                entity_dict = obj.as_truck_json()

            elif obj.type_id == DeviceTypeEntityEnum.BIN:
                bin_data = BinSerializer(obj, context=context)
                entity_dict = bin_data.data

            elif obj.type_id == DeviceTypeEntityEnum.RFID_SCANNER:
                entity_dict = obj.as_rfid_scanner_json()

            elif obj.type_id == DeviceTypeEntityEnum.DRIVER:
                driver_data = DriverSerializer(obj, context=context)
                entity_dict = driver_data.data
                try:
                    truck = Assignment.objects.get(child_id=obj.id, status=OptionsEnum.ACTIVE,
                                                   parent__type=DeviceTypeEntityEnum.TRUCK)
                    entity_dict['assigned_truck'] = truck.parent.as_entity_json()
                except Exception as e:
                    entity_dict['assigned_truck'] = None

            elif obj.type_id == DeviceTypeEntityEnum.AREA:
                entity_dict = obj.as_territory_json()
                try:
                    truck = Assignment.objects.filter(child_id=obj.id, status_id=OptionsEnum.ACTIVE,
                                                      parent__type_id=DeviceTypeEntityEnum.BIN,
                                                      type_id=DeviceTypeAssignmentEnum.AREA_ASSIGNMENT)
                    ass_truck = []

                    for e in truck:
                        ass_truck_dict = e.parent.as_entity_json()
                        ass_truck.append(ass_truck_dict)
                    entity_dict['assigned_bins'] = ass_truck
                    entity_dict['assigned_bins_count'] = truck.count()
                except Exception as e:
                    print(str(e))
                    entity_dict['assigned_bins'] = None

            elif obj.type_id == DeviceTypeEntityEnum.TERRITORY:
                entity_dict = obj.as_territory_json()
                try:
                    truck = Assignment.objects.filter(child_id=obj.id, status_id=OptionsEnum.ACTIVE,
                                                      parent__type_id=DeviceTypeEntityEnum.TRUCK,
                                                      type_id=DeviceTypeAssignmentEnum.TERRITORY_ASSIGNMENT)
                    ass_truck = []

                    for e in truck:
                        ass_truck_dict = e.parent.as_entity_json()
                        ass_truck.append(ass_truck_dict)
                    entity_dict['assigned_truck'] = ass_truck
                    entity_dict['assigned_trucks_count'] = truck.count()
                except Exception as e:
                    print(str(e))
                    entity_dict['assigned_truck'] = None

            elif obj.type_id == DeviceTypeEntityEnum.CONTRACT:
                contract_data = ClientContractSerializer(obj, context=context)
                entity_dict = contract_data.data
                try:
                    bins = Assignment.objects.filter(child_id=obj.id, status_id=OptionsEnum.ACTIVE,
                                                      type_id=DeviceTypeAssignmentEnum.CONTRACT_ASSIGNMENT)

                    area = Assignment.objects.get(child_id=obj.id, status_id=OptionsEnum.ACTIVE,
                                                      type_id=DeviceTypeAssignmentEnum.AREA_CONTRACT_ASSIGNMENT)

                    ass_truck = []

                    for e in bins:
                        ass_truck.append(e.parent.as_entity_json())
                    entity_dict['assigned_bins'] = ass_truck
                    entity_dict['assigned_bins_count'] = bins.count()
                    entity_dict['assigned_area_id'] = area.parent.id
                    entity_dict['assigned_area_name'] = area.parent.name

                except Exception as e:
                    print("Contact id: " + str(obj.id) + " Contact Name: " + obj.name)
                    count+=1
                    entity_dict['assigned_bins'] = None
                    entity_dict['assigned_bins_count'] = None
                    entity_dict['assigned_area_id'] = None
                    entity_dict['assigned_area_name'] = None

            elif obj.type_id == DeviceTypeEntityEnum.DUMPING_SITE:
                dumping_site_data = DumpingSiteSerializer(obj, context=context)
                entity_dict = dumping_site_data.data

            elif obj.type_id == DeviceTypeEntityEnum.SORTING_FACILITY:
                sorting_facility_data = SortingFacilitySerializer(obj, context=context)
                entity_dict = sorting_facility_data.data

            elif obj.type_id == DeviceTypeEntityEnum.SUPERVISOR:
                supervisor_data = ClientSupervisorSerializer(obj, context=context)
                entity_dict = supervisor_data.data

            elif obj.type_id == DeviceTypeEntityEnum.MAINTENANCE:
                entity_dict = obj.as_maintenance_json()
                try:
                    truck = Assignment.objects.filter(child_id=obj.id, status_id=OptionsEnum.ACTIVE,
                                                      parent__type_id=DeviceTypeEntityEnum.TRUCK)
                except Exception as e:
                    print(str(e))
                    # entity_dict['assigned_truck'] = None
            # if entity_dict:
            entity_list.append(entity_dict)
        print(count)
        return entity_list



def create_logistics_job(job_id, c_id, mod, truck, d_id, ent, actual_start_time, status):
    try:
        logistic_job = ActivityData.objects.get(device_id=job_id, entity_id=truck, person_id=d_id,
                                            job_status_id=status)
    except:
        logistic_job = ActivityData(
        device_id=job_id,
        customer_id=c_id,
        module_id=mod,
        entity_id=truck,
        person_id=d_id,
        job_start_timestamp=ent.job_start_datetime,
        job_end_timestamp=ent.job_end_datetime,
        job_start_lat_long=ent.source_latlong,
        job_end_lat_long=ent.destination_latlong,
        job_status=ent.job_status,
        actual_job_start_timestamp=actual_start_time,
        notes=ent.description
        )
        logistic_job.save()
    return logistic_job


def create_activity_data(job_id, truck, d_id, timestamp, status, lat_long, action_item, customer_id, module_id, supervisor=None):
    #try:
        #logistic_job = ActivityData.objects.get(scheduled_activity_id=job_id, entity_id=truck, person_id=d_id,
                                                #activity_status_id=status)
    #except:
        logistic_job = ActivityData(
            scheduled_activity_id=job_id,
            primary_entity_id=truck,
            actor_id=d_id,
            activity_status_id=status,
            timestamp = timestamp,
            lat_long = lat_long,
            action_items_id= action_item,
            customer_id = customer_id,
            module_id = module_id,
            supervisor = supervisor
        )
        return logistic_job


def create_bin_collection_data(job_id, truck, d_id, timestamp, status, action_item, customer_id, module_id, contract, client, area):
    try:
        logistic_job = BinCollectionData.objects.get(activity_id = job_id, status_id = status, action_item_id = action_item)
    except:
        logistic_job = BinCollectionData(
            activity_id=job_id,
            entity_id=truck,
            actor_id=d_id,
            timestamp=timestamp,
            status_id=status,
            action_item_id=action_item,
            customer_id=customer_id,
            module_id=module_id,
            contract_id = contract,
            client_id = client,
            area_id = area

        )
    return logistic_job


def update_bin_statuses(activity):
    try:
        BinCollectionData.objects.filter(activity_id=activity, status_id=IOFOptionsEnum.UNCOLLECTED)\
            .update(status_id=IOFOptionsEnum.ABORT_COLLECTION)
    except:
        traceback.print_exc()
        pass
    
    
def get_activites(j_id, d_id, c_id, status):
    if j_id:
        activities = Activity.objects.get(id=j_id, customer_id = c_id, activity_status_id__in = status)
    elif d_id:
        activities = Activity.objects.filter(actor_id=d_id, customer_id=c_id, activity_status_id__in = status)
    else:
        activities = Activity.objects.filter(customer_id = c_id)
    return activities


def get_time_info(obj_date_time):
    time = timezone.now() - obj_date_time
    minutes = round(time.total_seconds() / 60)
    if time.total_seconds() <= LAST_HOUR:
        result = "Few seconds ago"
    elif minutes > 0 and minutes < LAST_HOUR:
        result = str(round(time.total_seconds()/60)) + " minutes ago"
    elif minutes > 0 and minutes > LAST_HOUR and minutes < LAST_TWO_HOURS:
        result = "An Hour ago"
    elif minutes > LAST_TWO_HOURS and minutes < ONE_DAY:
        result = str(round(round(time.total_seconds() / 60) / 60)) + " Hours ago"
    elif minutes >= ONE_DAY and minutes <= TWO_DAYS:
        result = "1 Day Ago"
    elif minutes > TWO_DAYS and minutes < ONE_MONTH:
        result = str(round (round(round(time.total_seconds() / 60) / 60) / 24)) + " Days ago"
    elif minutes > ONE_MONTH and minutes < TWO_MONTHS:
        result = "A month ago"
    elif minutes > TWO_MONTHS and minutes < YEAR:
        result = str(round(round(round(time.total_seconds() / 60) / 60) / 24)/30) + " Months ago"
    elif minutes > YEAR and minutes < TWO_YEARS:
        result = "A Year ago"
    else:
        result = str(round(round(round(round(time.total_seconds() / 60) / 60) / 24)/30/12)) + " Years ago"
    return result


def check_activity_conflicts_review(serializer, preferences):
    #date_now = timezone.timedelta
    timestamp = serializer.get('activity_start_time')
    actor = serializer.get('actor')
    primary_entity = serializer.get('primary_entity')
    if not timestamp:
        timestamp = Activity.objects.get(id=serializer.get('id')).activity_start_time
        #timestamp = parser.parse(timestamp)
        #timestamp = pytz.utc.localize(timestamp)
    end_time = (timestamp + timezone.timedelta(minutes=preferences.average_activity_time))

    # Checking If driver conflicts with any current activity or future activity
    if actor:
        try:
            act = Activity.objects.get(actor_id=actor,activity_status_id__in=[IOFOptionsEnum.RUNNING, IOFOptionsEnum.ACCEPTED, IOFOptionsEnum.SUSPENDED])
            return True, act
        except:
            pass
        try:
            act = ActivityQueue.objects.get(actor_id=actor, activity_datetime__range=[timestamp, end_time])
            return True, act
        except:
            try:
                end_time = (timestamp - datetime.timedelta(minutes=preferences.average_activity_time))
                act = ActivityQueue.objects.get(actor_id=actor, activity_datetime__range=[end_time, timestamp])
                return True, act
            except:
                pass
    # Checking if Truck conflicts with any current or future activity
    end_time = (timestamp + timezone.timedelta(minutes=preferences.average_activity_time))
    if primary_entity:
        try:
            act = Activity.objects.get(primary_entity_id=primary_entity,activity_status_id__in=[IOFOptionsEnum.RUNNING, IOFOptionsEnum.ACCEPTED, IOFOptionsEnum.SUSPENDED])
            # act.activity_start_time
            return True, act
        except:
            pass
        try:
            act = ActivityQueue.objects.get(primary_entity_id=primary_entity, activity_datetime__range=[timestamp, end_time])
            return True, act
        except:
            try:
                end_time = (timestamp - datetime.timedelta(minutes=preferences.average_activity_time))
                act = ActivityQueue.objects.get(primary_entity_id=primary_entity, activity_datetime__range=[end_time, timestamp])
                return True, act
            except:
                pass
    return False, None
                
                    
def update_or_delete_activity(activity, serializer, preferences):
    new_timestamp = serializer.get('activity_start_time')
    buffer = (new_timestamp - timezone.now()).total_seconds()
    buffer = round(buffer / 60, 0)
    if preferences.enable_accept_reject:
        if buffer <= preferences.activity_accept_reject_buffer:
            update_activity_with_serializer(serializer, activity, preferences)
            # send notification based on review preferences
        else:
            add_queue_delete_activity_with_serializer(serializer, activity)
    else:
        if buffer <= preferences.activity_start_buffer:
            update_activity_with_serializer(serializer, activity, preferences)
            # send notification based on review preferences
        else:
            add_queue_delete_activity_with_serializer(serializer, activity)

            
def update_activity_with_serializer(serializer, activity, preferences):
    activity.actor = serializer.get('actor')
    activity.primary_entity = serializer.get('primary_entity')
    activity.action_items = serializer.get('action_items')
    activity.activity_start_time = serializer.get('activity_start_time')
    activity.activity_end_point = serializer.get('activity_end_point')
    activity.notification_sent = False
    activity.save()
    if preferences.enable_accept_reject:
        send_notification_to_admin(activity.primary_entity.id, activity.actor.id, activity.id, activity,
                               [User.objects.get(associated_entity = activity.actor).id], "Accept or reject this activity",
                               IOFOptionsEnum.NOTIFCIATION_DRIVER_ACCEPT_REJECT)
    
    

def add_queue_delete_activity_with_serializer(serializer, activity):
    aq = ActivityQueue()
    aq.primary_entity = serializer.get('primary_entity')
    aq.actor = serializer.get('actor')
    aq.action_items = serializer.get('action_items')
    aq.activity_start_time = serializer.data.get('activity_start_time')
    aq.customer = serializer.get('customer_id')
    aq.module = serializer.get('module_id')
    aq.activity_end_point = serializer.get('activity_end_point')
    aq.activity_schedule_id = activity.activity_schedule_id
    aq.save()
    activity.delete()

def append_activity(obj, list):
    list.append({
        'id': obj.id,
        'activity_type': obj.activity_schedule.activity_type.label if obj.activity_schedule.activity_type else None,
        'activity_status': obj.activity_status.label if obj.activity_status else None,
        'assigned_truck': obj.primary_entity.name if obj.primary_entity else None,
        'schedule_type': obj.activity_schedule.schedule_type.label if obj.activity_schedule.schedule_type else None,
        'activity_time': obj.activity_schedule.activity_start_time,
        'end_point_name': obj.activity_end_point.name if obj.activity_end_point else None,
        'end_point_lat_long': obj.activity_end_point.source_latlong if obj.activity_end_point else None,
        "check_point_name": obj.activity_check_point.name if obj.activity_check_point else None,
        "check_point_lat_long": obj.activity_check_point.source_latlong if obj.activity_check_point else None

    })
    return list


def driver_shift_management(truck, driver, start):
    if driver.type_id != DeviceTypeEntityEnum.DRIVER:
        return False, "Scanned RFID does not belong to a Driver. \nPlease contact your administrator"
    if start:
        try:
            shift = IofShifts.objects.get(child=driver, parent=truck, shift_end_time__isnull=True)
            return False, "You have already started your shift at:"+str(shift.shift_start_time)
        except:
            try:
                shift = IofShifts.objects.get(parent=truck, shift_end_time__isnull=True)
                shift.shift_end_time = timezone.now()
                shift.save()
            except:
                pass
            pass
        shift = IofShifts()
        shift.child = driver
        shift.parent = truck
        shift.customer = driver.customer
        shift.module = driver.module
        shift.type_id = DeviceTypeAssignmentEnum.SHIFT_ASSIGNMENT
        shift.save()
        return True, "You have succesfully started your shift on truck "+truck.name+" at: "+str(shift.shift_start_time)
    else:
        try:
            shift = IofShifts.objects.get(child=driver, parent = truck, shift_end_time__isnull=True)
        except:
            return False, "No Shift for Driver: " + driver.name
        try:
            Activity.objects.get(primary_entity=truck, actor=driver, status_id__in=[IOFOptionsEnum.RUNNING, IOFOptionsEnum.SUSPENDED])
            return False, "You are currently on an activity. Cannot end shift while on an activity"
        except:
            
            shift.shift_end_time = timezone.now()
            shift.save()
            return True, "You have succesfully ended the shift on truck " + truck.name + " at: " + str(
                shift.shift_start_time)


def driver_shift_management_simplified(truck, driver, response):
    try:
        if driver.type_id != DeviceTypeEntityEnum.DRIVER:
            return False, "Scanned RFID does not belong to a Driver. \nPlease contact your administrator"
        user = User.objects.get(associated_entity_id=driver.id)
        token = Token.objects.get_or_create(user=user)
    
        try:
            Activity.objects.get(actor=driver, activity_status_id__in=[IOFOptionsEnum.RUNNING, IOFOptionsEnum.SUSPENDED])
            return False, "Cannot END shift. An activity is currently assigned to you."
        except Activity.DoesNotExist:
            try:
                Activity.objects.get(primary_entity=truck,
                             activity_status_id__in=[IOFOptionsEnum.RUNNING, IOFOptionsEnum.SUSPENDED])
                return False, "Cannot END shift. An activity is currently assigned to you."
            except:
                pass
        try:
            shift = IofShifts.objects.get(child=driver, parent=truck, shift_end_time__isnull=True)
            shift.shift_end_time = timezone.now()
            response['TOKEN'] = 'abc'
            response['EMAIL'] = 'abc'
            shift.save()
            return True, "Shift ENDED successfully on truck " + truck.name
        except IofShifts.DoesNotExist:
            try:
                shift = IofShifts.objects.get(child=driver, shift_end_time__isnull=True)
                shift.shift_end_time = timezone.now()
                shift.save()
            except IofShifts.DoesNotExist:
                pass
        try:
            shift = IofShifts.objects.get(parent=truck, shift_end_time__isnull=True)
            shift.shift_end_time = timezone.now()
            shift.save()
        except IofShifts.DoesNotExist:
            pass
        shift = IofShifts()
        shift.child = driver
        shift.parent = truck
        shift.customer = driver.customer
        shift.module = driver.module
        shift.type_id = DeviceTypeAssignmentEnum.SHIFT_ASSIGNMENT
        shift.save()
        response['TOKEN'] = token[0].key
        response['EMAIL'] = user.email
        return True, "Shift STARTED successfully on truck " + truck.name
    except:
        traceback.print_exc()
        return False, "An issue has occurred. \nPlease Contact your Administrator."


def waste_collection_management(bin, truck, action, location):
    preference = CustomerPreferences.objects.get(customer= bin.customer)
    user_group = []
    on_shift , shift = check_shift_on_truck(truck)
    if not on_shift:
        return False, shift
    try:
        collection = BinCollectionData.objects.get(action_item=bin, status_id=IOFOptionsEnum.UNCOLLECTED)
    except:
        traceback.print_exc()
        return False, "Bin is already collected or bin is not part of any activity. Please contact administrator."
    
    latest_value = get_latest_value_of_truck(collection.entity.id)
    if not latest_value:
        return False, "No data is available to calculate weight. Please wait for a few minutes or contact your administrator."
    if not latest_value.validity:
        return False, "Valid weight is not available. Please scan again after a few minutes."
    
    if get_contract(bin):
        pass  # collection.weight * get_contract(bin)
    else:
        return False, "Contract does not exist for scanned bin"
    if action == IOFOptionsEnum.COLLECT_WASTE:
        # Logic to calculate invoice, UNCOMMENT when in production testing WALEED
        success, collection = calculate_invoice(action, collection, latest_value, bin)
        if not success:
            return success, collection
        # collection.pre_weight = float(latest_value.volume)
        activity_data = create_activity_data(collection.activity.id, shift.parent.id, shift.child.id, timezone.now(),
                             IOFOptionsEnum.COLLECT_WASTE, location, collection.action_item.id, collection.customer_id,
                             collection.module_id)
        activity_data.save()
        
        return True, "Succesfully performed operation"
        
    elif action == IOFOptionsEnum.WASTE_COLLECTED:
        # Logic to calculate invoice, UNCOMMENT when in production testing WALEED
        success, collection = calculate_invoice(action, collection, latest_value, bin)
        if not success:
            return success, collection
        
        # create_bin_event(collection.entity, bin, IOFOptionsEnum.WASTE_COLLECTED, collection.activity)
        activity_data = create_activity_data(collection.activity.id, shift.parent.id, shift.child.id, timezone.now(),
                             IOFOptionsEnum.WASTE_COLLECTED, location, collection.action_item.id, collection.customer_id,
                             collection.module_id)
        activity_data.save()
        
        if preference.waste_collection:
            driver = shift.child
            driver_user = User.objects.get(associated_entity=driver).id
            user_group.append(driver_user)
            admin = User.objects.filter(customer=bin.customer, role_id=1)
            for obj in admin:
                user_group.append(obj.id)
            notification = send_action_notification(collection.activity.primary_entity.id, collection.actor.id, None, collection.activity,
                                                    "Succesfully Collected Waste.\nID: " + bin.name + "\nClient:"+bin.client.name +".\nWeight Collected: " + str(collection.weight)+"\nInvoice: "+str(collection.invoice),
                                                    IOFOptionsEnum.NOTIFICATION_DRIVER_WASTE_COLLECTION)
            notification.save()
            save_users_group(notification, user_group)
        return True, "Succesfully Collected Waste.\nID: " + bin.name + "\nClient:"+bin.client.name +".\nWeight Collected: " + str(collection.weight)+"\nInvoice: "+str(collection.invoice)
    
        
def bin_collection_management(bin, truck, action, location):
    
    on_shift, shift = check_shift_on_truck(truck)
    if not on_shift:
        return False, shift
    
    if action == IOFOptionsEnum.DROPOFF_BIN:
        bin.obd2_compliant = True
        user_group = []
        preference = CustomerPreferences.objects.get(customer=bin.customer)
        bin.source_latlong = location
        bin.save()
        if truck:
            check, activity = check_entity_on_activity(None, truck.id, truck.customer.id)
            if check:
                return False, "Bin is part of an activity and cannot be Dropped Off. Please contact your administrator."
            else:
                activity_data = create_activity_data(None, shift.parent.id, shift.child.id,
                                                     timezone.now(),
                                                     IOFOptionsEnum.DROPOFF_BIN, location, bin.id,
                                                     bin.customer_id,
                                                     bin.module_id)
                activity_data.save()
                
            if preference.bin_dropoff:
                admin = User.objects.filter(customer=bin.customer, role_id=1)
                for obj in admin:
                    user_group.append(obj.id)
                notification = send_action_notification(truck.id, None, None,
                                                        bin,
                                                        "Successfully Dropped off Bin: " + bin.name,
                                                        IOFOptionsEnum.NOTIFICATION_DRIVER_BIN_DROPOFF)
                notification.save()
                save_users_group(notification, user_group)
        
        return True, "Successfully Dropped off Bin: "+bin.name
    
    else:
        on_shift, shift = check_shift_on_truck(truck)
        if not on_shift:
            return False, shift
        latest_value = get_latest_value_of_truck(truck.id)
        if not latest_value:
            return False, "No data is available to calculate weight. Please wait for a few minutes or contact your administrator."
        if not latest_value.validity:
            return False, "Valid weight is not available. Please scan again after a few minutes."
        
        if action == IOFOptionsEnum.PICKUP_BIN:
            try:
                collection = BinCollectionData.objects.get(action_item=bin, action_item__obd2_compliant=True,
                                                           status_id=IOFOptionsEnum.UNCOLLECTED)
            except:
                return False, "The Bin is not registered as Operational. Please Drop Bin before Picking Up Bin. Contact Administrator for details"
            
            bin.obd2_compliant = False
            bin.save()
            activity_data = create_activity_data(collection.activity.id, shift.parent.id, shift.child.id, timezone.now(),
                                 IOFOptionsEnum.PICKUP_BIN, None, collection.action_item.id, collection.customer_id,
                                 collection.module_id)
            activity_data.save()

            # Logic to calculate invoice, UNCOMMENT when in production testing WALEED
            # collection = calculate_invoice(action, collection, latest_value, None)
            collection.pre_weight = latest_value.volume
            collection.save()
            return True, "Successfully performed operation"
    
        elif action == IOFOptionsEnum.BIN_PICKED_UP:
            try:
                collection = BinCollectionData.objects.get(action_item=bin, action_item__obd2_compliant=False,
                                                           status_id=IOFOptionsEnum.UNCOLLECTED)
            except:
                traceback.print_exc()
                return False, "The Bin is registered as Stored. Please Drop Bin before Picking Up Bin. Contact Administrator for details."
            # Logic to calculate invoice, UNCOMMENT when in production testing WALEED
            # collection = calculate_invoice(action, collection, latest_value, bin)
            collection.post_weight = float(latest_value.volume)
            collection.weight = collection.post_weight - collection.pre_weight
            if get_contract(bin):
                collection.invoice = 20  # collection.weight * get_contract(bin)
            else:
                traceback.print_exc()
                return False, "Contract does not exist for scanned bin"
            collection.status_id = IOFOptionsEnum.BIN_PICKED_UP
            collection.timestamp = timezone.now()
            collection.save()
            activity_data = create_activity_data(collection.activity.id, shift.parent.id, shift.child.id, timezone.now(),
                                 IOFOptionsEnum.BIN_PICKED_UP, None, collection.action_item.id, collection.customer_id,
                                 collection.module_id)
            activity_data.save()

            preference = CustomerPreferences.objects.get(customer=bin.customer)
            if preference.bin_pickup:
                user_group = []
                driver = shift.child
                driver_user = User.objects.get(associated_entity=shift.child).id
                user_group.append(driver_user)
                admin = User.objects.filter(customer=shift.customer, role_id=1)
                for obj in admin:
                    user_group.append(obj.id)
                notification = send_action_notification(shift.parent.id, shift.child.id, None, shift,
                                         driver.name + "Succesfully Picked Up Bin" + bin.name + ".\n Weight Collected: " + str(
                                             collection.weight),
                                         IOFOptionsEnum.NOTIFICATION_DRIVER_BIN_PICKUP)
                notification.save()
                save_users_group(notification, user_group)
            return True, "Successfully Picked Up Bin"+ bin.name+".\n Weight Collected: "+ str(collection.weight)
        
        # return True, "Succesfully performed operation"
    

def verification_management(bin, supervisor, action):
    try:
        collection = BinCollectionData.objects.get(action_item=bin,
                                                   status_id__in=[IOFOptionsEnum.WASTE_COLLECTED,
                                                                  IOFOptionsEnum.BIN_PICKED_UP], verified__isnull=True)
    except:
        traceback.print_exc()
        return False, "Bin is not marked for collection or is not part of activity. Please contact you administrator"

    if action == IOFOptionsEnum.VERIFY_COLLECTION:
        try:
            supervisor = Entity.objects.get(name=supervisor)
        except ObjectDoesNotExist:
            return False, "RFID does not exist. Please contact administrator"
        try:
            supervisor = Assignment.objects.get(child=supervisor).parent
        except:
            return False, "RFID is not associated with any personnel. Please contact administrator"
        if supervisor.status_id == OptionsEnum.INACTIVE:
            return False, "Your record is inactive and you cannot verify any collection. Please contact your administrator"
        if supervisor.type_id != DeviceTypeEntityEnum.SUPERVISOR:
            return False, "RFID does not belong to a Supervisor. Please contact your administrator"
        if supervisor.client_id != bin.client_id:
            return False, "Supervisor does not belong to the same client as scanned bin. Please contact your administrator"
        collection.supervisor = supervisor
        collection.verified = True
        activity_data = create_activity_data(collection.activity.id, collection.entity.id, collection.actor.id,
                                             timezone.now(),
                                             IOFOptionsEnum.VERIFY_COLLECTION, None, collection.action_item.id,
                                             collection.customer_id,
                                             collection.module_id, supervisor)
        activity_data.save()
    elif action == IOFOptionsEnum.SKIP_VERIFITCATION:
        collection.verified = False
        activity_data = create_activity_data(collection.activity.id, collection.entity.id, collection.actor.id,
                                             timezone.now(),
                                             IOFOptionsEnum.SKIP_VERIFITCATION, None, collection.action_item.id,
                                             collection.customer_id,
                                             collection.module_id, supervisor)
        activity_data.save()
    collection.save()
    return True, "Succesfully performed operation"


def get_contract(bin):
    try:
        contract = Assignment.objects.get(child__type_id = DeviceTypeEntityEnum.CONTRACT, parent=bin,
                                          status_id=OptionsEnum.ACTIVE).child
        return contract
    except:
        return None
    

def create_bin_event(truck, bin, status, activity):
    if activity:
        col = BinCollectionData.objects.get(activity=activity, action_item=bin)
        col.activity = activity
        col.save()
    else:
        coll = BinCollectionData()
        coll.entity = truck
        coll.action_item = bin
        coll.timestamp = timezone.now()
        coll.status_id = status
        coll.customer = bin.customer
        coll.module = bin.module
        coll.save()

    
def create_child_parent_assigment(child, parent, type, customer, module, modified_by):
    ass = Assignment()
    ass.name = Entity.objects.get(pk=child).name + " Assigned to "+Entity.objects.get(id=parent).name
    ass.child_id = child
    ass.parent_id = parent
    ass.type_id = type
    ass.customer_id = customer
    ass.module_id = module
    ass.modified_by_id = modified_by
    ass.status_id = OptionsEnum.ACTIVE
    ass.save()



def util_create_incident_reporting(d_id, t_id, action_items, timestamp, activity_id, type_id, notes, customer_id, module_id):
    report = IncidentReporting(
        actor_id = d_id,
        primary_entity_id= t_id,
        action_items=action_items,
        scheduled_activity_id = activity_id,
        timestamp= timestamp,
        incident_type_id = type_id,
        notes = notes,
        customer_id = customer_id,
        module_id = module_id
    )
    return report


def get_schedule_type(activity):
    if activity.activity_schedule.end_date is None:
        return "Once"
    else:
        return "Multiple Days"


def incident_reporting_list(d_id,c_id,t_id):
    if d_id:
        incident_reporting = IncidentReporting.objects.filter(actor_id = d_id, customer_id = c_id).order_by('-timestamp')
    elif t_id:
        incident_reporting = IncidentReporting.objects.filter(actor_id=t_id, customer_id = c_id).order_by('-timestamp')
    else:
        incident_reporting = IncidentReporting.objects.filter(customer_id=c_id).order_by('-timestamp')

    return incident_reporting

# def check_entity_on_current_activity(d_id,t_id,c_id):
#     if d_id:
#         try:
#             Activity.objects.get(actor_id=d_id, customer_id=c_id, activity_status_id__in=[IOFOptionsEnum.RUNNING, IOFOptionsEnum.SUSPENDED])
#             return True
#         except:
#             return False
#
#     elif t_id:
#         try:
#             Activity.objects.get(primary_entity_id=t_id, customer_id=c_id, activity_status_id__in=[IOFOptionsEnum.RUNNING, IOFOptionsEnum.SUSPENDED])
#             return True
#         except:
#             return False
#
#     else:
#         return False

def check_entity_on_activity(d_id,t_id,c_id):
    if d_id:
        try:
            act = Activity.objects.get(actor_id=d_id, customer_id=c_id, activity_status_id__in=[IOFOptionsEnum.RUNNING, IOFOptionsEnum.SUSPENDED])
            return True, act
        except:
            return False, None

    elif t_id:
        try:
            act = Activity.objects.get(primary_entity_id=t_id, customer_id=c_id, activity_status_id__in=[IOFOptionsEnum.RUNNING, IOFOptionsEnum.SUSPENDED])
            return True, act
        except:
            return False, None

    else:
        return False, None


def check_entity_on_current_shift(d_id, t_id, c_id):
    if d_id:
        try:
            IofShifts.objects.get(child_id=d_id, customer_id=c_id, shift_end_time__isnull= True)
            return True
        except:
            return False

    elif t_id:
        try:
            IofShifts.objects.get(parent_id=t_id, customer_id=c_id, shift_end_time__isnull=True)
            return True
        except:
            return False

    else:
        try:
            IofShifts.objects.get(customer_id=c_id, shift_end_time__isnull=True)
            return True
        except:
            return False


def get_shift_data(d_id, t_id, c_id, start_date, end_date):
    if d_id:
        result = IofShifts.objects.filter(child_id=d_id)
    elif d_id:
        result = IofShifts.objects.filter(parent_id=t_id)
    elif c_id:
        result = IofShifts.objects.filter(customer_id=c_id)
        
    if start_date and end_date:
        result = result.filter(shift_start_time__range=[start_date, end_date])
    return  result


def get_assets_list(c_id, m_id, request, e_id=None):
    if c_id:

        if c_id:
            ent = Entity.objects.filter(customer=c_id, type_id__in=[DeviceTypeEntityEnum.TRUCK,
                                                                    DeviceTypeEntityEnum.BIN,
                                                                    DeviceTypeEntityEnum.RFID_CARD,
                                                                    DeviceTypeEntityEnum.RFID_TAG,
                                                                    DeviceTypeEntityEnum.RFID_SCANNER]).exclude(status=OptionsEnum.DELETED).order_by(
                '-modified_datetime')
        elif e_id:
            ent = Entity.objects.filter(customer=c_id, id=e_id).exclude(status=OptionsEnum.DELETED).order_by(
                '-modified_datetime')

        entity_dict = {}

        tags_list = []
        bins_list = []
        cards_list = []
        trucks_list = []
        rfid_scanners_list = []

        for obj in ent:
            if obj.type_id == DeviceTypeEntityEnum.RFID_TAG:
                entity = obj.as_entity_json()
                try:
                    asset = Assignment.objects.get(child_id=obj.id, status=OptionsEnum.ACTIVE,
                                                   parent__type_id=DeviceTypeEntityEnum.BIN, type_id=DeviceTypeAssignmentEnum.RFID_TAG_ASSIGMENT)
                    entity['assigned_asset'] = asset.parent.as_entity_json()
                except Exception as e:
                    entity['assigned_asset'] = None
                tags_list.append(entity)


            elif obj.type_id == DeviceTypeEntityEnum.RFID_CARD:
                entity = obj.as_entity_json()
                try:
                    asset = Assignment.objects.get(child_id=obj.id, status=OptionsEnum.ACTIVE,
                                                   type_id=DeviceTypeAssignmentEnum.RFID_CARD_ASSIGMENT)
                    entity['assigned_asset'] = asset.parent.as_entity_json()
                except Exception as e:
                    entity['assigned_asset'] = None
                cards_list.append(entity)


            elif obj.type_id == DeviceTypeEntityEnum.TRUCK:
                entity = obj.as_entity_json()
                try:
                    asset = Assignment.objects.get(parent_id=obj.id, status=OptionsEnum.ACTIVE,
                                                   child__type_id=DeviceTypeEntityEnum.RFID_SCANNER, type_id=DeviceTypeAssignmentEnum.RFID_ASSIGNMENT)
                    entity['assigned_asset'] = asset.child.as_entity_json()
                except Exception as e:
                    entity['assigned_asset'] = None
                trucks_list.append(entity)


            elif obj.type_id == DeviceTypeEntityEnum.BIN:
                bin_data = BinSerializer(obj, context={'request':request})
                entity = bin_data.data.copy()
                try:
                    asset = Assignment.objects.get(parent_id=obj.id, status=OptionsEnum.ACTIVE,
                                                   child__type_id=DeviceTypeEntityEnum.RFID_TAG, type_id=DeviceTypeAssignmentEnum.RFID_TAG_ASSIGMENT)
                    entity['assigned_asset'] = asset.child.as_entity_json()
                except Exception as e:
                    entity['assigned_asset'] = None
                bins_list.append(entity)


            elif obj.type_id == DeviceTypeEntityEnum.RFID_SCANNER:
                entity = obj.as_entity_json()
                try:
                    asset = Assignment.objects.get(child_id=obj.id, status=OptionsEnum.ACTIVE,
                                                   parent__type=DeviceTypeEntityEnum.TRUCK, type_id=DeviceTypeAssignmentEnum.RFID_ASSIGNMENT)
                    entity['assigned_asset'] = asset.parent.as_entity_json()
                except Exception as e:
                    entity['assigned_asset'] = None
                rfid_scanners_list.append(entity)

        contract = CustomerDevice.objects.filter(customer_id=c_id, module_id=m_id).values('device_id', 'assigned', 'status__label', 'status_id', 'type_id', 'created_at','entity__name', type_name=F('type__name'))
        entity_dict['bins'] = bins_list
        entity_dict['rfid_cards'] = cards_list
        entity_dict['rfid_tags'] = tags_list
        entity_dict['rfid_scanners'] = rfid_scanners_list
        entity_dict['trucks'] = trucks_list
        entity_dict['customer_devices'] = list(contract)

        return entity_dict


def get_latest_value_of_truck(truck_id):
    try:
        latest_value = HypernetPreData.objects.filter(device_id=truck_id).order_by('-timestamp').first()
        if latest_value:
            pass
        else:
            try:
                latest_value = HypernetPostData.objects.get(device_id=truck_id,
                                                            timestamp=Devices.objects.get(
                                                                device_id=truck_id).timestamp)
            except:
                traceback.print_exc()
                return False, "An error occured. Please scan again after a few minutes."
    finally:
        return latest_value
    
    
def calculate_invoice(action, collection, latest_value, bin):
    contract = get_contract(bin)
    if not contract:
        return False, "Contract does not exist for scanned bin"

    if action == IOFOptionsEnum.PICKUP_BIN or action == IOFOptionsEnum.COLLECT_WASTE:
        
        collection.pre_weight = latest_value.accelerometer_1
    
    elif action == IOFOptionsEnum.BIN_PICKED_UP or action == IOFOptionsEnum.WASTE_COLLECTED:
        if contract.leased_owned.id ==  IOFOptionsEnum.TRIP_BASED:
            collection.post_weight = float(latest_value.accelerometer_1)
            collection.weight = collection.post_weight - collection.pre_weight
            collection.invoice = contract.skip_rate
            collection.status_id = action
            collection.timestamp = timezone.now()
        elif contract.leased_owned.id ==  IOFOptionsEnum.WEIGHT_AND_TRIP_BASED:
            pass
        elif contract.leased_owned.id == IOFOptionsEnum.WEIGHT_BASED:
            collection.post_weight = float(latest_value.accelerometer_1)
            collection.weight = collection.post_weight - collection.pre_weight
            collection.invoice = 20 # Multiplier based on contract and bin waste type
            collection.status_id = action
            collection.timestamp = timezone.now()
            
        elif contract.leased_owned.id == IOFOptionsEnum.LUMP_SUM:
            pass
    collection.save()
    return True, collection


def update_skip_weight(truck, bin):
    try:
        val = get_latest_value_of_truck(truck.id)
        try:
            collection = BinCollectionData.objects.get(action_item=bin, entity=truck, status_id=IOFOptionsEnum.COLLECTED, weight__isnull=True)
            collection.weight = collection.pre_weight - val.volume
            # Logic to calculate invoice per kg waste collected.
            collection.save()
        except:
            pass
        finally:
            bin.volume_capacity = val.volume
            bin.save()
            return True, "Succesfully updated Skip Weight.\n ID:"+bin.name+"\nSkip Weight:"+bin.weight
    except:
        return False, "Unable to update weight at the moment. Please try again in a few minutes."


def check_activity_on_truck(truck):
    try:
        Activity.objects.get(primary_entity=truck,
                             activity_status_id__in=[IOFOptionsEnum.RUNNING, IOFOptionsEnum.SUSPENDED])
    except Activity.DoesNotExist:
        return False, "No activity for truck. Please ensure the RFID Scanner being used is the one authorised for this activity. " \
                                "\nIf the problem persists contact your administrator."
    return True, None


def check_shift_on_truck(truck):
    try:
        shift = IofShifts.objects.get(parent=truck, shift_end_time__isnull=True)
    except:
        return  False, "Truck shift data is not available. Please start shift before proceeding"
    return True, shift


def get_clients_invoice(client, customer, status, start_datetime, end_datetime, contracts=None):
    collection_data = None
    if client:
        collection_data = BinCollectionData.objects.filter(client_id=client, customer_id=customer, status_id__in = status)
        if contracts and collection_data:
            collection_data = collection_data.filter(contract_id__in=contracts, status_id__in=status)
    else:
        collection_data = BinCollectionData.objects.filter(customer_id=customer, status_id__in=status)

    if start_datetime and end_datetime:
        collection_data = collection_data.filter(timestamp__range=[start_datetime,end_datetime])

    return collection_data
