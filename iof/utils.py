from __future__ import unicode_literals

import traceback

import dateutil
from django.core.exceptions import ObjectDoesNotExist
from jsonpickle import json
from rest_framework.authtoken.models import Token
from django.db.models import F, ExpressionWrapper, fields
import datetime
from django.db.models import Sum
from django.utils import timezone

from hypernet.constants import *
from hypernet.models import Entity, \
    Assignment, HypernetPostData, Devices, HypernetPreData, CustomerDevice, InvoiceData, UserEntityAssignment

from hypernet.serializers import DumpingSiteSerializer, RfidScannerSerializer, \
    ClientContractSerializer, ClientSupervisorSerializer, SortingFacilitySerializer, DriverSerializer, BinSerializer, \
    ZoneSerializer, EmployeeSerializer, SiteSerializer, VesselSerializer, EmployeeListingSerializer, \
    HomeAppliancesSerializer,HomeApplianceFrontendsSerializer
from iof.generic_utils import get_generic_distance_travelled, get_generic_volume_consumed
from iof.models import ActivityData, ActivitySchedule, IofShifts, IncidentReporting
from hypernet.enums import *
from iof.models import Activity, BinCollectionData, ActivityQueue, LogisticMaintenance, LogisticMaintenanceData
from user.models import User
from customer.models import CustomerPreferences
from iof.serializers import ActivityScheduleSerializer
from hypernet.notifications.utils import send_action_notification, save_users_group, send_notification_to_admin
from iof.models import LogisticAggregations


def get_device_lastest_data(device_id):
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

def get_entity(e_id, ent, c_id, context=None):
    from django.core.cache import cache
    if e_id:
        try:
            ent = Entity.objects.get(id=e_id, customer_id=c_id,
                                     status_id__in=[OptionsEnum.ACTIVE, OptionsEnum.INACTIVE])

        except:
            return None
    else:
        # added this because all subsequent calls use e_id
        e_id = ent.id
    if ent.type.id == DeviceTypeEntityEnum.TRUCK:
        entity = ent.as_truck_json()

        shift_status, shift_obj = check_entity_on_current_shift(d_id=None, t_id=e_id, c_id=c_id)
        if shift_status:
            entity['assigned_driver'] = shift_obj.child.as_entity_json()
        else:
            try:
                driver = Assignment.objects.get(parent_id=e_id, type_id=DeviceTypeAssignmentEnum.DRIVER_ASSIGNMENT,
                                                status_id=OptionsEnum.ACTIVE)
                entity['assigned_driver'] = driver.child.as_driver_json()
            except:
                pass
        flag, activity = check_entity_on_activity(d_id=None, t_id=e_id, c_id=c_id)

        if flag is True:
            entity['on_activity'] = flag
            entity['activity_id'] = activity.id
        try:
            maint = LogisticMaintenance.objects.get(truck_id=e_id, status_id__in=[IOFOptionsEnum.MAINTENANCE_ACCEPTED,
                                                                                  IOFOptionsEnum.MAINTENANCE_APPROVAL,
                                                                                  IOFOptionsEnum.MAINTENANCE_OPEN_INPROGRESS,
                                                                                  IOFOptionsEnum.MAINTENANCE_WAITING_FOR_PARTS])
            entity['maintenance_id'] = maint.status.id
            entity['maintenance_status'] = maint.status.label
        except:
            # traceback.print_exc()
            entity['maintenance_status'] = None
        return entity

    elif ent.type.id == DeviceTypeEntityEnum.DRIVER:
        entity = ent.as_driver_json()
        try:
            truck = Assignment.objects.get(child_id=e_id, type_id=DeviceTypeAssignmentEnum.DRIVER_ASSIGNMENT,
                                           status_id=OptionsEnum.ACTIVE).parent
            entity['assigned_truck'] = truck.as_entity_json()
        except:
            pass

        jobs = Activity.objects.filter(actor_id=e_id, activity_status_id=IOFOptionsEnum.ACCEPTED).values(
            'created_datetime', 'id', 'primary_entity_id',
            'primary_entity__name', 'actor_id', 'actor__name', 'activity_status__label', 'activity_status_id')
        entity['assigned_jobs'] = list(jobs)
        entity['shift_status'], shift_obj = check_entity_on_current_shift(e_id, None, c_id)
        if entity['shift_status']:
            entity['assigned_truck'] = shift_obj.parent.as_entity_json()
        flag, activity = check_entity_on_activity(d_id=e_id, t_id=None, c_id=c_id)
        if flag is True:
            entity['on_activity'] = flag
            entity['activity_id'] = activity.id

        return entity

    elif ent.type.id == DeviceTypeEntityEnum.FLEET:
        entity = ent.as_fleet_json()
        fleet_trucks = Assignment.objects.filter(child__parent_id=e_id,
                                                 type_id=DeviceTypeAssignmentEnum.TRUCK_ASSIGNMENT).first()
        fleet_territory = Assignment.objects.filter(child__parent_id=e_id,
                                                    type_id=DeviceTypeAssignmentEnum.TERRITORY_ASSIGNMENT).first()
        if fleet_trucks:
            entity['assigned_trucks'] = fleet_trucks.child.as_truck_json()
            entity['assigned_territory'] = fleet_territory.child.as_territory_json()
        return entity

    elif ent.type.id == DeviceTypeEntityEnum.TERRITORY:
        entity = ent.as_territory_json()
        truck = Assignment.objects.filter(child_id=e_id, parent__type_id=DeviceTypeEntityEnum.TRUCK,
                                          type_id=DeviceTypeAssignmentEnum.TRUCK_ASSIGNMENT).first()
        fleet = Assignment.objects.filter(child_id=e_id, parent__type_id=DeviceTypeEntityEnum.FLEET,
                                          type_id=DeviceTypeAssignmentEnum.TRUCK_ASSIGNMENT).first()
        if truck:
            entity['assigned_truck'] = truck.parent.as_truck_json()
        if fleet:
            entity['assigned_fleet'] = fleet.parent.as_fleet_json()
        return entity

    elif ent.type.id == DeviceTypeEntityEnum.JOB:
        entity = ent.as_job_json()
        try:
            truck = Assignment.objects.get(child_id=e_id, type_id=DeviceTypeAssignmentEnum.JOB_ASSIGNMENT).parent
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
        cache_key = ent.id  # needs to be unique
        data = cache.get(cache_key)  # returns None if no key-value pair
        if not data:
            entity = BinSerializer(ent, context=context)
            data = entity.data
            # Set the item in cache for the first time if cant get it
            cache.set(key=cache_key, value=data, timeout=None)
        # else:
        #     print('Found it!')
        return data
        # entity = ent.as_bin_json()
        # try:
        #     truck = Assignment.objects.get(child_id=e_id,type_id=DeviceTypeAssignmentEnum.BIN_ASSIGNMENT, status_id=OptionsEnum.ACTIVE)
        #     entity['assigned_truck'] = truck.parent.as_truck_json()
        # except:
        #     entity['assigned_truck'] = None
        # try:
        #     contract = Assignment.objects.get(parent_id=e_id,type_id=DeviceTypeAssignmentEnum.CONTRACT_ASSIGNMENT, child__type_id=DeviceTypeEntityEnum.CONTRACT, status_id=OptionsEnum.ACTIVE)
        #     entity['assigned_contract'] = contract.child.as_contract_json()
        #
        # except:
        #     entity['assigned_contract'] = None
        # try:
        #     old_contract = Assignment.objects.filter(parent_id=e_id, type_id=DeviceTypeAssignmentEnum.CONTRACT_ASSIGNMENT,
        #                               child__type_id=DeviceTypeEntityEnum.CONTRACT,
        #                               status_id=OptionsEnum.INACTIVE).order_by('-created_datetime')[0]
        #     entity['old_contract'] = old_contract.child.as_contract_json()
        #     old_area = Assignment.objects.filter(child=old_contract.child, type_id=DeviceTypeAssignmentEnum.AREA_CONTRACT_ASSIGNMENT,
        #                                   parent__type_id=DeviceTypeEntityEnum.AREA, status_id=OptionsEnum.INACTIVE).order_by('-created_datetime')
        #     entity['old_area'] = old_area[0].parent.as_entity_json()
        #     old_location = Assignment.objects.filter(child=old_contract.child, type_id=DeviceTypeAssignmentEnum.LOCATION_CONTRACT_ASSIGNMENT,
        #                                       parent__type_id=DeviceTypeEntityEnum.LOCATION,
        #                                       status_id=OptionsEnum.INACTIVE)
        #     entity['old_location'] = old_location[0].parent.as_entity_json()
        # except:
        #     # traceback.print_exc()
        #     entity['old_contract'] = None
        #     entity['old_area'] = None
        #     entity['old_location'] = None
        # try:
        #     area = Assignment.objects.get(parent_id=e_id,type_id=DeviceTypeAssignmentEnum.AREA_ASSIGNMENT, child__type_id=DeviceTypeEntityEnum.AREA, status_id=OptionsEnum.ACTIVE)
        #     entity['assigned_area'] = area.child.as_entity_json()
        # except:
        #     entity['assigned_area'] = None
        # try:
        #     location = Assignment.objects.get(parent_id=e_id,type_id=DeviceTypeAssignmentEnum.LOCATION_ASSIGNMENT, child__type_id=DeviceTypeEntityEnum.LOCATION, status_id=OptionsEnum.ACTIVE)
        #     entity['assigned_location'] = location.child.as_entity_json()
        # except:
        #     entity['assigned_location'] = None
        # try:
        #     current_collection = BinCollectionData.objects.get(action_item_id=e_id, status_id=IOFOptionsEnum.UNCOLLECTED)
        #     entity['activity_status'] = current_collection.activity.activity_status.id
        #     entity['current_activity'] = current_collection.activity.id
        # except:
        #     entity['activity_status'] = None
        #     entity['current_activity'] = None
        #
        # bin_collection_data = BinCollectionData.objects.filter(action_item_id=e_id,
        #                                                        status_id__in =[IOFOptionsEnum.WASTE_COLLECTED, IOFOptionsEnum.BIN_PICKED_UP]).order_by('-timestamp')
        #
        # bin_collection = []
        # if bin_collection_data:
        #     for obj in bin_collection_data:
        #         if not entity.get('last_collection'):
        #             entity['last_collection'] = obj.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        #         bin_collection.append(obj.as_bin_collection_data_json())
        #
        #     entity['bin_collection_data'] = bin_collection
        #
        # else:
        #     entity['bin_collection_data'] = None
        #     entity['last_collection'] = None
        return entity.data

    elif ent.type.id == DeviceTypeEntityEnum.EMPLOYEE:
        entity = EmployeeSerializer(ent, context=context)
        return entity.data

    elif ent.type.id == DeviceTypeEntityEnum.VESSEL:
        entity = VesselSerializer(ent, context=context)
        return entity.data

    elif ent.type.id == DeviceTypeEntityEnum.IOP_DEVICE:
        entity = HomeApplianceFrontendsSerializer(ent, context=context)
        return entity.data


def get_entity_brief(c_id, m_id, t_id, context, index_a, index_b, e_id=None, u_id=None):
    # Entity Removed in Merge
    from django.core.cache import cache
    entity_dict = {}
    entity_list = []
    last_data_list = []
    count = 0
    if c_id:
        # TODO module_id check to be added(REASON NO DATA)
        if int(t_id) == DeviceTypeEntityEnum.JOB:
            devices = ActivitySchedule.objects.filter(customer_id=c_id)
        # FOR IOP USERS APP ONLY.
        if int(t_id) == DeviceTypeEntityEnum.IOP_DEVICE:
            devices_assignments = UserEntityAssignment.objects.filter(customer_id=c_id, user=u_id,can_remove=False,
                                                                      status_id=OptionsEnum.ACTIVE).values_list(
                'device_id', flat=True)
            devices = Entity.objects.filter(pk__in=devices_assignments).exclude(status_id=OptionsEnum.DELETED).order_by(
                '-modified_datetime').distinct()



        elif t_id:
            devices = Entity.objects.filter(customer_id=c_id, type_id=t_id).exclude(
                status_id=OptionsEnum.DELETED).order_by(
                '-modified_datetime').distinct()
        elif e_id:
            devices = Entity.objects.filter(customer_id=c_id, id=e_id).exclude(status_id=OptionsEnum.DELETED).order_by(
                '-modified_datetime').distinct()

        for i in range(index_a, index_b):
            try:
                device = devices[i]
            except:
                return entity_list, False
            if int(t_id) == DeviceTypeEntityEnum.JOB:
                activity_data = ActivityScheduleSerializer(device, context=context)
                entity_dict = activity_data.data

            elif device.type_id == DeviceTypeEntityEnum.TRUCK:
                entity_dict = device.as_truck_json()

            elif device.type_id == DeviceTypeEntityEnum.BIN:
                cache_key = device.id  # needs to be unique
                entity_dict = cache.get(cache_key)  # returns None if no key-value pair
                if not entity_dict:
                    entity = BinSerializer(device, context=context)
                    entity_dict = entity.data
                    # Set the item in cache for the first time if cant get it
                    cache.set(key=cache_key, value=entity_dict, timeout=None)


            elif device.type_id == DeviceTypeEntityEnum.VESSEL:
                vessel_data = VesselSerializer(device, context=context)
                entity_dict = vessel_data.data

            elif device.type_id == DeviceTypeEntityEnum.RFID_SCANNER:
                entity_dict = device.as_rfid_scanner_json()

            elif device.type_id == DeviceTypeEntityEnum.DRIVER:
                driver_data = DriverSerializer(device, context=context)
                entity_dict = driver_data.data
                entity_dict['on_shift'], shift_obj = check_entity_on_current_shift(entity_dict['id'], None, c_id)

                try:
                    truck = Assignment.objects.get(child_id=device.id, status=OptionsEnum.ACTIVE,
                                                   parent__type=DeviceTypeEntityEnum.TRUCK)
                    entity_dict['assigned_truck'] = truck.parent.as_entity_json()
                except Exception as e:
                    entity_dict['assigned_truck'] = None

            elif device.type_id == DeviceTypeEntityEnum.AREA:
                entity_dict = device.as_territory_json()
                try:
                    truck = Assignment.objects.filter(child_id=device.id, status_id=OptionsEnum.ACTIVE,
                                                      parent__type_id=DeviceTypeEntityEnum.BIN,
                                                      type_id=DeviceTypeAssignmentEnum.AREA_ASSIGNMENT)
                    ass_truck = []
                    for e in truck:
                        ass_truck_dict = e.parent.as_entity_json()
                        ass_truck.append(ass_truck_dict)
                    entity_dict['assigned_bins'] = ass_truck
                    entity_dict['assigned_bins_count'] = truck.count()
                except Exception as e:
                    traceback.print_exc()
                    entity_dict['assigned_bins'] = None

            elif device.type_id == DeviceTypeEntityEnum.LOCATION:
                entity_dict = device.as_territory_json()
                try:
                    truck = Assignment.objects.filter(child_id=device.id, status_id=OptionsEnum.ACTIVE,
                                                      parent__type_id=DeviceTypeEntityEnum.BIN,
                                                      type_id=DeviceTypeAssignmentEnum.LOCATION_ASSIGNMENT)
                    ass_truck = []
                    for e in truck:
                        ass_truck_dict = e.parent.as_entity_json()
                        ass_truck.append(ass_truck_dict)
                    entity_dict['assigned_bins'] = ass_truck
                    entity_dict['assigned_bins_count'] = truck.count()
                except Exception as e:
                    traceback.print_exc()
                    entity_dict['assigned_bins'] = None

            elif device.type_id == DeviceTypeEntityEnum.TERRITORY:
                entity_dict = device.as_territory_json()
                try:
                    truck = Assignment.objects.filter(child_id=device.id, status_id=OptionsEnum.ACTIVE,
                                                      parent__type_id=DeviceTypeEntityEnum.TRUCK,
                                                      type_id=DeviceTypeAssignmentEnum.TERRITORY_ASSIGNMENT)
                    ass_truck = []

                    for e in truck:
                        ass_truck_dict = e.parent.as_entity_json()
                        ass_truck.append(ass_truck_dict)
                    entity_dict['assigned_truck'] = ass_truck
                    entity_dict['assigned_trucks_count'] = truck.count()
                except Exception as e:
                    traceback.print_exc()
                    entity_dict['assigned_truck'] = None

            elif device.type_id == DeviceTypeEntityEnum.CONTRACT:
                cache_key = device.id  # needs to be unique
                entity_dict = cache.get(cache_key)  # returns None if no key-value pair
                if not entity_dict:
                    zone_data = ClientContractSerializer(device, context=context)
                    entity_dict = zone_data.data
                    try:
                        ass_truck = []
                        bins = Assignment.objects.filter(child_id=device.id, status_id=OptionsEnum.ACTIVE,
                                                         type_id=DeviceTypeAssignmentEnum.CONTRACT_ASSIGNMENT)
                        for e in bins:
                            ass_truck.append(e.parent.as_entity_json())
                        entity_dict['assigned_bins'] = ass_truck
                        entity_dict['assigned_bins_count'] = bins.count()

                        area = Assignment.objects.get(child_id=device.id, status_id=OptionsEnum.ACTIVE,
                                                      type_id=DeviceTypeAssignmentEnum.AREA_CONTRACT_ASSIGNMENT)

                        entity_dict['assigned_area_id'] = area.parent.id
                        entity_dict['assigned_area_name'] = area.parent.name

                    except Exception as e:
                        area = None
                    try:
                        location = Assignment.objects.get(child_id=device.id, status_id=OptionsEnum.ACTIVE,
                                                          type_id=DeviceTypeAssignmentEnum.LOCATION_CONTRACT_ASSIGNMENT)
                        entity_dict['assigned_location_id'] = location.parent.id
                        entity_dict['assigned_location_name'] = location.parent.name
                    except:
                        if area:
                            pass
                        else:
                            count += 1
                            entity_dict['assigned_area_id'] = None
                            entity_dict['assigned_area_name'] = None
                            entity_dict['assigned_locaiton_id'] = None
                            entity_dict['assigned_location_name'] = None
                    cache.set(key=cache_key, value=entity_dict, timeout=None)

            elif device.type_id == DeviceTypeEntityEnum.DUMPING_SITE:
                dumping_site_data = DumpingSiteSerializer(device, context=context)
                entity_dict = dumping_site_data.data

            elif device.type_id == DeviceTypeEntityEnum.SORTING_FACILITY:
                sorting_facility_data = SortingFacilitySerializer(device, context=context)
                entity_dict = sorting_facility_data.data

            elif device.type_id == DeviceTypeEntityEnum.SUPERVISOR:
                supervisor_data = ClientSupervisorSerializer(device, context=context)
                entity_dict = supervisor_data.data

            elif device.type_id == DeviceTypeEntityEnum.MAINTENANCE:
                entity_dict = device.as_maintenance_json()
                try:
                    truck = Assignment.objects.filter(child_id=device.id, status_id=OptionsEnum.ACTIVE,
                                                      parent__type_id=DeviceTypeEntityEnum.TRUCK)
                except Exception as e:
                    traceback.print_exc()
                    # entity_dict['assigned_truck'] = None

            elif device.type_id == DeviceTypeEntityEnum.ZONE:
                zone_data = ZoneSerializer(device, context=context)
                entity_dict = zone_data.data
                try:
                    site = Assignment.objects.get(child=device, status_id=OptionsEnum.ACTIVE,
                                                  type_id=DeviceTypeAssignmentEnum.SITE_ZONE_ASSIGNMENT)

                    # supervisor = Assignment.objects.get(parent=obj, status_id=OptionsEnum.ACTIVE,
                    #                                   type_id=DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT)

                    entity_dict['assigned_site'] = site.parent.name
                    entity_dict['assigned_site_id'] = site.parent.id
                    # entity_dict['assigned_supervisor'] = supervisor.child.name

                except Exception as e:
                    # print("Some Exception in Zone")
                    entity_dict['assigned_supervisor'] = None
                    entity_dict['assigned_site'] = None

            elif device.type_id == DeviceTypeEntityEnum.EMPLOYEE:
                employee_data = EmployeeListingSerializer(device, context=context)
                entity_dict = employee_data.data

            elif device.type_id == DeviceTypeEntityEnum.SITE:
                site_data = SiteSerializer(device, context=context)
                entity_dict = site_data.data
                zones = Assignment.objects.filter(type_id=DeviceTypeAssignmentEnum.SITE_ZONE_ASSIGNMENT, parent=device,
                                                  status_id=OptionsEnum.ACTIVE)
                zones_list = []
                try:
                    site_supervisor = Assignment.objects.get(type_id=DeviceTypeAssignmentEnum.SITE_EMPLOYEE_ASSIGNMENT,
                                                             parent=device, status_id=OptionsEnum.ACTIVE)
                except:
                    site_supervisor = None

                if len(zones) > 0:
                    for z in zones:
                        zones_list.append(z.child.as_entity_json())
                    entity_dict['assgined_zones'] = zones_list
                else:
                    entity_dict['assgined_zones'] = None

                entity_dict['assigned_supervisor'] = site_supervisor.child.name if site_supervisor else None

            elif device.type_id == DeviceTypeEntityEnum.IOP_DEVICE:
                last_data_dict = {}
                latest_data = HypernetPreData.objects.filter(device=device, customer_id=c_id)
                # print('====================')
                # print(device.id, " ", DeviceTypeAssignmentEnum.IOP_DEVICE_USER_ASSIGNMENT, " ", OptionsEnum.ACTIVE)

                users_assignments = UserEntityAssignment.objects.filter(device_id=device.id,
                                                                        type_id=DeviceTypeAssignmentEnum.IOP_DEVICE_USER_ASSIGNMENT,
                                                                        status_id=OptionsEnum.ACTIVE)
                # print(users_assignments.count())
                if latest_data.count() == 0:
                    latest_data = HypernetPostData.objects.filter(device=device, customer_id=c_id)

                if latest_data.count() > 0:
                    latest_data = latest_data.latest('timestamp')
                    last_data_dict['error_code'] = latest_data.inactive_score
                    try:
                        status = LogisticAggregations.objects.get(device=device).online_status
                    except:
                        status = False

                    try:
                        latest_event_queue = Activity.objects \
                            .filter(
                            primary_entity_id=latest_data.device_id,
                            activity_status_id__in=[
                                IopOptionsEnums.IOP_SCHEDULE_READY,
                                IopOptionsEnums.IOP_SCHEDULE_IN_USE]) \
                            .latest('start_datetime')

                        last_data_dict['latest_event_state'] = latest_event_queue.activity_status.label
                        last_data_dict['latest_event_scheduled_by'] = latest_event_queue.activity_schedule.modified_by.email

                    except Exception as e:
                        print('latest event queue   ', e)
                        last_data_dict['latest_event_state'] = ''
                        last_data_dict['latest_event_scheduled_by'] = ''

                    last_data_dict['on_off_status'] = status
                    last_data_dict['temperature'] = latest_data.active_score
                    last_data_dict['temperature_threshold'] = latest_data.active_score
                    last_data_dict['current_heater_state']=latest_data.heartrate_value
                    last_data_dict['amb_temperature'] = latest_data.ambient_temperature
                    last_data_dict['timestamp'] = latest_data.timestamp
                    last_data_dict['clm']=latest_data.clm
                    last_data_dict['cdt']=latest_data.cdt
                else:
                    latest_data_dict = None

                devices_data = HomeAppliancesSerializer(device, context=context)
                entity_dict = devices_data.data.copy()
                entity_dict['latest_data'] = last_data_dict
                entity_dict['device_users'] = users_assignments.count()
                users_list = []
                for user in users_assignments:
                    users_list.append(user.users_assignments_as_json())
                entity_dict['users_data'] = users_list

            entity_list.append(entity_dict)

        return entity_list, True


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


def create_activity_data(job_id, truck, d_id, timestamp, status, lat_long, action_item, customer_id, module_id,
                         supervisor=None,
                         cost=None):
    # try:
    # logistic_job = ActivityData.objects.get(scheduled_activity_id=job_id, entity_id=truck, person_id=d_id,
    # activity_status_id=status)
    # except:
    logistic_job = ActivityData(
        scheduled_activity_id=job_id,
        primary_entity_id=truck,
        actor_id=d_id,
        activity_status_id=status,
        timestamp=timestamp,
        lat_long=lat_long,
        action_items_id=action_item,
        customer_id=customer_id,
        module_id=module_id,
        supervisor=supervisor,
        cost=cost,
    )
    return logistic_job


def create_bin_collection_data(job_id, truck, d_id, timestamp, status, action_item, customer_id, module_id):
    try:
        logistic_job = BinCollectionData.objects.get(activity_id=job_id, status_id=status, action_item_id=action_item)
    except:
        try:
            logistic_job = BinCollectionData.objects.get(action_item_id=action_item,
                                                         activity__activity_status_id__in=
                                                         [IOFOptionsEnum.RUNNING, IOFOptionsEnum.SUSPENDED])
        except:
            try:
                contract = Assignment.objects.get(parent_id=action_item, child__type_id=DeviceTypeEntityEnum.CONTRACT,
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
                client = Entity.objects.get(id=action_item).client.id
            except:
                client = None
            logistic_job = BinCollectionData(
                activity_id=job_id,
                entity_id=truck,
                actor_id=d_id,
                timestamp=timestamp,
                status_id=status,
                action_item_id=action_item,
                customer_id=customer_id,
                module_id=module_id,
                contract_id=contract,
                client_id=client,
                area_id=area

            )
    return logistic_job


def update_bin_statuses(activity):
    try:
        BinCollectionData.objects.filter(activity_id=activity, status_id=IOFOptionsEnum.UNCOLLECTED) \
            .update(status_id=IOFOptionsEnum.ABORT_COLLECTION)
    except:
        traceback.print_exc()
        pass


def get_activites(j_id, d_id, c_id, status):
    if j_id:
        activities = Activity.objects.get(id=j_id, customer_id=c_id, activity_status_id__in=status)
    elif d_id:
        activities = Activity.objects.filter(actor_id=d_id, customer_id=c_id, activity_status_id__in=status)
    else:
        activities = Activity.objects.filter(customer_id=c_id)
    return activities


def get_time_info(obj_date_time):
    time = timezone.now() - obj_date_time
    minutes = round(time.total_seconds() / 60)
    if time.total_seconds() <= LAST_HOUR:
        result = "Few seconds ago"
    elif minutes > 0 and minutes < LAST_HOUR:
        result = str(round(time.total_seconds() / 60)) + " minutes ago"
    elif minutes > 0 and minutes > LAST_HOUR and minutes < LAST_TWO_HOURS:
        result = "An Hour ago"
    elif minutes > LAST_TWO_HOURS and minutes < ONE_DAY:
        result = str(round(round(time.total_seconds() / 60) / 60)) + " Hours ago"
    elif minutes >= ONE_DAY and minutes <= TWO_DAYS:
        result = "1 Day Ago"
    elif minutes > TWO_DAYS and minutes < ONE_MONTH:
        result = str(round(round(round(time.total_seconds() / 60) / 60) / 24)) + " Days ago"
    elif minutes > ONE_MONTH and minutes < TWO_MONTHS:
        result = "A month ago"
    elif minutes > TWO_MONTHS and minutes < YEAR:
        result = str(round(round(round(time.total_seconds() / 60) / 60) / 24) / 30) + " Months ago"
    elif minutes > YEAR and minutes < TWO_YEARS:
        result = "A Year ago"
    else:
        result = str(round(round(round(round(time.total_seconds() / 60) / 60) / 24) / 30 / 12)) + " Years ago"
    return result


def check_activity_conflicts_review(serializer, preferences):
    # date_now = timezone.timedelta
    timestamp = serializer.get('activity_start_time')
    actor = serializer.get('actor')
    primary_entity = serializer.get('primary_entity')
    if not timestamp:
        timestamp = Activity.objects.get(id=serializer.get('id')).activity_start_time
        # timestamp = parser.parse(timestamp)
        # timestamp = pytz.utc.localize(timestamp)
    end_time = (timestamp + timezone.timedelta(minutes=preferences.average_activity_time))

    # Checking If driver conflicts with any current activity or future activity
    if actor:
        try:
            act = Activity.objects.get(actor_id=actor,
                                       activity_status_id__in=[IOFOptionsEnum.RUNNING, IOFOptionsEnum.ACCEPTED,
                                                               IOFOptionsEnum.SUSPENDED])
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
            act = Activity.objects.get(primary_entity_id=primary_entity,
                                       activity_status_id__in=[IOFOptionsEnum.RUNNING, IOFOptionsEnum.ACCEPTED,
                                                               IOFOptionsEnum.SUSPENDED])
            # act.activity_start_time
            return True, act
        except:
            pass
        try:
            act = ActivityQueue.objects.get(primary_entity_id=primary_entity,
                                            activity_datetime__range=[timestamp, end_time])
            return True, act
        except:
            try:
                end_time = (timestamp - datetime.timedelta(minutes=preferences.average_activity_time))
                act = ActivityQueue.objects.get(primary_entity_id=primary_entity,
                                                activity_datetime__range=[end_time, timestamp])
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
            act = update_activity_with_serializer(serializer, activity)
            return act
            # send notification based on review preferences
        else:
            aq = add_queue_delete_activity_with_serializer(serializer, activity)
            return aq
    else:
        if buffer <= preferences.activity_start_buffer:
            act = update_activity_with_serializer(serializer, activity)
            return act
            # send notification based on review preferences
        else:
            aq = add_queue_delete_activity_with_serializer(serializer, activity)
            return aq


def update_activity_with_serializer(serializer, activity):
    activity.actor = serializer.get('actor')
    activity.primary_entity = serializer.get('primary_entity')
    activity.action_items = serializer.get('action_items')
    activity.activity_start_time = serializer.get('activity_start_time')
    activity.activity_end_point = serializer.get('activity_end_point')
    activity.notification_sent = False
    return activity


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
    activity.delete()
    return aq


def append_activity(obj, list):
    list.append({
        'id': obj.id,
        'activity_type': obj.activity_schedule.activity_type.label if obj.activity_schedule.activity_type else None,
        'activity_status': obj.activity_status.label if obj.activity_status else None,
        'assigned_truck': obj.primary_entity.name if obj.primary_entity else None,
        'schedule_type': obj.activity_schedule.schedule_type.label if obj.activity_schedule.schedule_type else None,
        'activity_time': obj.activity_start_time,
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
            return False, "You have already started your shift at:" + str(shift.shift_start_time)
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
        return True, "You have succesfully started your shift on truck " + truck.name + " at: " + str(
            shift.shift_start_time)
    else:
        try:
            shift = IofShifts.objects.get(child=driver, parent=truck, shift_end_time__isnull=True)
        except:
            return False, "No Shift for Driver: " + driver.name
        try:
            Activity.objects.get(primary_entity=truck, actor=driver,
                                 status_id__in=[IOFOptionsEnum.RUNNING, IOFOptionsEnum.SUSPENDED])
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
        result = []
        admin = User.objects.filter(customer=user.customer, role_id=1)
        for obj in admin:
            result.append(obj.id)

        try:
            Activity.objects.get(actor=driver,
                                 activity_status_id__in=[IOFOptionsEnum.RUNNING, IOFOptionsEnum.SUSPENDED])
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
            if response:
                response['TOKEN'] = 'abc'
                response['EMAIL'] = 'abc'

            shift = calculate_shift_end_values(shift)
            shift.save()
            # Send notification to admin here
            notification = send_action_notification(shift.parent.id, shift.child.id, None, shift,
                                                    shift.child.name + " ended the shift on " + shift.parent.name,
                                                    IOFOptionsEnum.NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_SHIFT_START)
            notification.save()
            save_users_group(notification, result)
            return True, "Shift ENDED successfully on truck " + truck.name
        except IofShifts.DoesNotExist:
            try:
                # Check if any shift started by driver on any other truck
                shift = IofShifts.objects.get(child=driver, shift_end_time__isnull=True)
                shift.shift_end_time = timezone.now()
                calculate_shift_end_values(shift)
                shift.save()
                # send notification to admin abt this old shift ending
                notification = send_action_notification(shift.parent.id, shift.child.id, None, shift,
                                                        shift.child.name + " did not end shift on " + shift.parent.name,
                                                        IOFOptionsEnum.NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_SHIFT_START)
                notification.save()
                save_users_group(notification, result)
            except IofShifts.DoesNotExist:
                try:
                    # Check if any shift was already started on the truck
                    shift = IofShifts.objects.get(parent=truck, shift_end_time__isnull=True)
                    shift.shift_end_time = timezone.now()
                    shift = calculate_shift_end_values(shift)
                    shift.save()
                    # send notification to admin abt this old shift ending
                    notification = send_action_notification(shift.parent.id, shift.child.id, None, shift,
                                                            shift.child.name + " did not end shift on " + shift.parent.name,
                                                            IOFOptionsEnum.NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_SHIFT_START)
                    notification.save()
                    save_users_group(notification, result)
                except IofShifts.DoesNotExist:
                    # No shift exists on either truck or driver, continue with code.
                    pass
        # No shift data exists at all, create a fresh  shift and start it for driver
        shift = IofShifts()
        shift.child = driver
        shift.parent = truck
        shift.customer = driver.customer
        shift.module = driver.module
        shift.type_id = DeviceTypeAssignmentEnum.SHIFT_ASSIGNMENT
        shift.save()
        notification = send_action_notification(shift.parent.id, shift.child.id, None, shift,
                                                shift.child.name + " started the shift on " + shift.parent.name,
                                                IOFOptionsEnum.NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_SHIFT_START)
        notification.save()
        save_users_group(notification, result)
        # send notification to admin abt start shift
        if response:
            response['TOKEN'] = token[0].key
            response['EMAIL'] = user.email
        return True, "Shift STARTED successfully on truck " + truck.name
    except:
        traceback.print_exc()
        return False, "An issue has occurred. \nPlease Contact your Administrator."


def calculate_shift_end_values(shift):
    vol_consumed = HypernetPostData.objects.filter(device=shift.parent,
                                                   timestamp__range=[shift.shift_start_time,
                                                                     timezone.now()])
    d_travelled = HypernetPostData.objects.filter(device=shift.parent,
                                                  timestamp__range=[shift.shift_start_time, timezone.now()])

    d_travelled = d_travelled.aggregate(d_travelled=Sum('distance_travelled'))

    vol_consumed = vol_consumed.aggregate(vol_consumed=Sum('volume_consumed'))

    try:
        truck_ent = Entity.objects.get(pk=shift.parent.id)
    except:
        truck_ent = None

    if truck_ent:
        if vol_consumed['vol_consumed']:
            vol = float(vol_consumed['vol_consumed'])
            vol_consumed = (vol / 1000) * 0.219
        else:
            vol_consumed = 0.0

        if d_travelled['d_travelled']:
            distance = float(d_travelled['d_travelled'])
            d_travelled = distance / 1000

        else:
            d_travelled = 0.0

        if d_travelled == 0.0 and vol_consumed == 0.0:
            fuel_avg = 0.0

        elif vol_consumed == 0.0:
            fuel_avg = 0.0
        else:
            fuel_avg = d_travelled / vol_consumed

        shift.distance_travelled = d_travelled
        shift.volume_consumed = vol_consumed
        shift.fuel_avg = fuel_avg
        shift.shift_duration = int((shift.shift_end_time - shift.shift_start_time).total_seconds() / 60)
    return shift


def waste_collection_management(bin, truck, action, location):
    preference = CustomerPreferences.objects.get(customer=bin.customer)
    user_group = []
    on_shift, shift = check_shift_on_truck(truck)

    if not on_shift:
        return False, shift

    if not bin.obd2_compliant:
        return False, "Bin is already picked up and waste cannot be collected. Please drop off the bin in the field before picking up the bin."

    if get_contract(bin):
        pass  # collection.weight * get_contract(bin)
    else:
        return False, "Contract does not exist for scanned bin"

    # latest_value = get_latest_value_of_truck(truck.id, False)
    # if not latest_value:
    #     return False, "No data is available to calculate weight. Please wait for a few minutes or contact your administrator."
    # if not latest_value.validity:
    #     return False, "Valid weight is not available. Please scan again after a few minutes."

    if action == IOFOptionsEnum.COLLECT_WASTE:
        try:
            collection = BinCollectionData.objects.get(action_item=bin, status_id=IOFOptionsEnum.UNCOLLECTED)
        except:
            collection = create_bin_collection_data(None, shift.parent.id, shift.child.id, timezone.now(),
                                                    IOFOptionsEnum.UNCOLLECTED, bin.id, bin.customer.id,
                                                    bin.module.id)
        # Set the status of bin collection so we can check the values in the next packets.
        collection.status_id = IOFOptionsEnum.COLLECT_WASTE
        collection.timestamp = timezone.now()
        collection.save()
        if collection.activity:
            activity_data = create_activity_data(collection.activity.id, shift.parent.id, shift.child.id,
                                                 timezone.now(),
                                                 IOFOptionsEnum.COLLECT_WASTE, location, collection.action_item.id,
                                                 collection.customer_id,
                                                 collection.module_id)
            activity_data.save()
        else:
            activity_data = create_activity_data(None, shift.parent.id, shift.child.id,
                                                 timezone.now(),
                                                 IOFOptionsEnum.COLLECT_WASTE, location, collection.action_item.id,
                                                 collection.customer_id,
                                                 collection.module_id)
            activity_data.save()

        return True, "Successfully performed operation"

    elif action == IOFOptionsEnum.WASTE_COLLECTED:
        # try:
        #     BinCollectionData.objects.get(action_item=bin, status_id=IOFOptionsEnum.COLLECT_WASTE,
        #                                   pre_weight__isnull=True)
        #     return False, "Weight has not been updated in the system yet. Please try again in a moment."
        # except:
        try:
            collection = BinCollectionData.objects.get(action_item=bin, status_id=IOFOptionsEnum.COLLECT_WASTE,
                                                       post_weight__isnull=True)
        except:
            collection = create_bin_collection_data(None, shift.parent.id, shift.child.id, timezone.now(),
                                                    IOFOptionsEnum.UNCOLLECTED, bin.id, bin.customer.id,
                                                    bin.module.id)
        notification_already_sent = False
        # Set the status, time and invoice for skip, Post weight will be calculated by data ingestion.
        success, collection = calculate_invoice(action, collection, None, bin, shift)
        if not success:
            return success, collection

        # create_bin_event(collection.entity, bin, IOFOptionsEnum.WASTE_COLLECTED, collection.activity)
        if collection.activity:
            activity_data = create_activity_data(collection.activity.id, shift.parent.id, shift.child.id,
                                                 timezone.now(),
                                                 IOFOptionsEnum.WASTE_COLLECTED, location, collection.action_item.id,
                                                 collection.customer_id,
                                                 collection.module_id)
            activity_data.save()
        else:
            activity_data = create_activity_data(None, shift.parent.id, shift.child.id,
                                                 timezone.now(),
                                                 IOFOptionsEnum.WASTE_COLLECTED, location, collection.action_item.id,
                                                 collection.customer_id,
                                                 collection.module_id)
            activity_data.save()

        if preference.waste_collection and notification_already_sent is False:
            driver = shift.child
            driver_user = User.objects.get(associated_entity=driver).id
            user_group.append(driver_user)
            admin = User.objects.filter(customer=bin.customer, role_id=1)
            for obj in admin:
                user_group.append(obj.id)
            if collection.activity:
                notification = send_action_notification(shift.parent.id, shift.child.id, collection.activity.id, bin,
                                                        driver.name + " successfully Collected Waste.\nID: " + bin.name + "\nClient:" + bin.client.name + "\nInvoice: " + str(
                                                            collection.invoice),
                                                        IOFOptionsEnum.NOTIFICATION_DRIVER_WASTE_COLLECTION)
            else:
                notification = send_action_notification(shift.parent.id, shift.child.id, None, bin,
                                                        driver.name + " successfully Collected Waste.\nID: " + bin.name + "\nClient:" + bin.client.name + "\nInvoice: " + str(
                                                            collection.invoice),
                                                        IOFOptionsEnum.NOTIFICATION_DRIVER_WASTE_COLLECTION)
            notification.save()
            save_users_group(notification, user_group)
        return True, "Successfully Collected Waste.\nID: " + bin.name + "\nClient:" + bin.client.name + "\nInvoice: " + str(
            collection.invoice)


def bin_collection_management(bin, truck, action, location):
    notification_already_sent = False
    user_group = []
    preference = CustomerPreferences.objects.get(customer=bin.customer)
    on_shift, shift = check_shift_on_truck(truck)

    if not on_shift:
        return False, shift

    if action == IOFOptionsEnum.DROPOFF_BIN:
        if not bin.client:
            return False, "Bin cannot be dropped without client. Please set contract through Update Details or contact your administrator"
        else:
            if not dropoff_invoice(truck, bin, action, shift, notification_already_sent):
                if truck:
                    check, activity = check_entity_on_activity(None, truck.id, truck.customer.id, bin.id)
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
            bin.obd2_compliant = True
            bin.source_latlong = location
            bin.save()
        return True, "Successfully Dropped off Bin: " + bin.name + "\nClient: " + bin.client.name

    elif action == IOFOptionsEnum.WORKSHOP_DROP:
        bin.obd2_compliant = False
        bin.source_latlong = location
        bin.save()
        if not dropoff_invoice(truck, bin, action, shift, notification_already_sent):
            user_group = []
            preference = CustomerPreferences.objects.get(customer=bin.customer)
            if truck:
                # check, activity = check_entity_on_activity(None, truck.id, truck.customer.id, bin.id)
                # if check:
                #     return False, "Bin is part of an activity and cannot be Dropped Off. Please contact your administrator."
                # else:
                activity_data = create_activity_data(None, shift.parent.id, shift.child.id,
                                                     timezone.now(),
                                                     IOFOptionsEnum.WORKSHOP_DROP, location, bin.id,
                                                     bin.customer_id,
                                                     bin.module_id)
                activity_data.save()

                if preference.bin_dropoff:
                    admin = User.objects.filter(customer=bin.customer, role_id=1)
                    for obj in admin:
                        user_group.append(obj.id)
                    notification = send_action_notification(truck.id, None, None,
                                                            bin,
                                                            "Bin Dropped at workshop: " + bin.name,
                                                            IOFOptionsEnum.NOTIFICATION_DRIVER_BIN_DROPOFF)
                    notification.save()
                    save_users_group(notification, user_group)
        return True, "Successfully Dropped off Bin: " + bin.name

    elif action == IOFOptionsEnum.SPARE_SKIP_DEPOSIT:
        bin.obd2_compliant = False
        bin.source_latlong = location
        user_group = []
        preference = CustomerPreferences.objects.get(customer=bin.customer)
        bin.save()
        if truck:
            # check, activity = check_entity_on_activity(None, truck.id, truck.customer.id, bin.id)
            # if check:
            #     return False, "Bin is part of an activity and cannot be Dropped Off. Please contact your administrator."
            # else:
            activity_data = create_activity_data(None, shift.parent.id, shift.child.id,
                                                 timezone.now(),
                                                 IOFOptionsEnum.SPARE_SKIP_DEPOSIT, location, bin.id,
                                                 bin.customer_id,
                                                 bin.module_id)
            activity_data.save()

            if preference.bin_dropoff:
                admin = User.objects.filter(customer=bin.customer, role_id=1)
                for obj in admin:
                    user_group.append(obj.id)
                notification = send_action_notification(truck.id, None, None,
                                                        bin,
                                                        "Spare Bin Dropped at workshop: " + bin.name,
                                                        IOFOptionsEnum.NOTIFICATION_DRIVER_BIN_DROPOFF)
                notification.save()
                save_users_group(notification, user_group)

        return True, "Successfully Dropped off Bin: " + bin.name

    else:
        on_shift, shift = check_shift_on_truck(truck)
        if not on_shift:
            return False, shift
        latest_value = get_latest_value_of_truck(truck.id, False)
        if not latest_value:
            return False, "No data is available to calculate weight. Please wait for a few minutes or contact your administrator."
        if not latest_value.validity:
            return False, "Valid weight is not available. Please scan again after a few minutes."
        if bin.obd2_compliant == False:
            return False, "Bin is already picked up and waste cannot be collected. Please drop off the bin in the field before picking up the bin."
        if action == IOFOptionsEnum.PICKUP_BIN:
            try:
                collection = BinCollectionData.objects.get(action_item=bin, action_item__obd2_compliant=True,
                                                           status_id=IOFOptionsEnum.UNCOLLECTED)

                activity_data = create_activity_data(collection.activity.id, shift.parent.id, shift.child.id,
                                                     timezone.now(),
                                                     IOFOptionsEnum.PICKUP_BIN, location, collection.action_item.id,
                                                     collection.customer_id,
                                                     collection.module_id)
                activity_data.save()
            except:
                traceback.print_exc()
                # Collection object needs to be created for invoicing and trip sheets
                collection = create_bin_collection_data(None, shift.parent.id, shift.child.id, timezone.now(),
                                                        IOFOptionsEnum.UNCOLLECTED, bin.id, bin.customer.id,
                                                        bin.module.id)
                activity_data = create_activity_data(None, shift.parent.id, shift.child.id,
                                                     timezone.now(),
                                                     IOFOptionsEnum.PICKUP_BIN, location, collection.action_item.id,
                                                     collection.customer_id,
                                                     collection.module_id)
                activity_data.save()
            # collection.pre_weight = latest_value.volume
            collection.save()
            return True, "Successfully performed operation"

        elif action == IOFOptionsEnum.BIN_PICKED_UP:
            try:
                collection = BinCollectionData.objects.get(action_item=bin, action_item__obd2_compliant=True,
                                                           status_id=IOFOptionsEnum.UNCOLLECTED)
                success, collection = calculate_invoice(action, collection, latest_value, bin, shift)
                if not success:
                    return success, collection
            except:
                traceback.print_exc()
                return False, "The Bin is registered as Stored. Please Drop Bin before Picking Up Bin. Contact Administrator for details."

            collection.status_id = IOFOptionsEnum.BIN_PICKED_UP
            collection.timestamp = timezone.now()
            collection.save()
            bin.obd2_compliant = False
            bin.save()
            if collection.activity:
                activity_data = create_activity_data(collection.activity.id, shift.parent.id, shift.child.id,
                                                     timezone.now(),
                                                     IOFOptionsEnum.BIN_PICKED_UP, location, collection.action_item.id,
                                                     collection.customer_id,
                                                     collection.module_id)
                activity_data.save()
            else:
                activity_data = create_activity_data(None, shift.parent.id, shift.child.id,
                                                     timezone.now(),
                                                     IOFOptionsEnum.BIN_PICKED_UP, location, collection.action_item.id,
                                                     collection.customer_id,
                                                     collection.module_id)
                activity_data.save()
            return True, "Successfully Picked Up Bin " + bin.name + "\nClient:" + bin.client.name

        elif action == IOFOptionsEnum.MAINTENANCE_PICKUP:
            # Collection object needs to be created for bin events
            check, msg = check_activity_on_truck(truck)
            if check:
                return check, "Bin is part of an activity and cannot be picked for maintenance. Please contact your adiminstrator."
            collection = create_bin_collection_data(None, shift.parent.id, shift.child.id, timezone.now(),
                                                    IOFOptionsEnum.MAINTENANCE_PICKUP, bin.id, bin.customer.id,
                                                    bin.module.id)
            activity_data = create_activity_data(None, shift.parent.id, shift.child.id,
                                                 timezone.now(),
                                                 IOFOptionsEnum.MAINTENANCE_PICKUP, location, collection.action_item.id,
                                                 collection.customer_id,
                                                 collection.module_id)
            bin.obd2_compliant = False
            # TODO: location set to None for now, will be associated to trucks location somehow. Flag would be required to identify assignment and truck
            bin.source_latlong = None
            bin.save()
            activity_data.save()
            if preference.bin_pickup:
                admin = User.objects.filter(customer=bin.customer, role_id=1)
                for obj in admin:
                    user_group.append(obj.id)
                notification = send_action_notification(truck.id, None, None,
                                                        bin,
                                                        "Bin picked for maintenance: " + bin.name,
                                                        IOFOptionsEnum.NOTIFICATION_DRIVER_BIN_PICKUP)
                notification.save()
                save_users_group(notification, user_group)
            # collection.save()

            return True, "Successfully performed operation"

        elif action == IOFOptionsEnum.CONTRACT_TERMINATION:
            if shift.child.speed:
                check, msg = check_activity_on_truck(truck)
                if check:
                    return check, "Bin is part of an activity and contract cannot be terminated. Please contact your adiminstrator."
                collection = create_bin_collection_data(None, shift.parent.id, shift.child.id, timezone.now(),
                                                        IOFOptionsEnum.CONTRACT_TERMINATION, bin.id, bin.customer.id,
                                                        bin.module.id)
                activity_data = create_activity_data(None, shift.parent.id, shift.child.id,
                                                     timezone.now(),
                                                     IOFOptionsEnum.CONTRACT_TERMINATION, location,
                                                     collection.action_item.id,
                                                     collection.customer_id,
                                                     collection.module_id)
                bin.obd2_compliant = False
                bin.source_latlong = None
                bin.client = None
                assignments = bin.assignment_parent.all()
                for a in assignments:
                    if a.type_id == DeviceTypeAssignmentEnum.RFID_TAG_ASSIGMENT:
                        pass
                    else:
                        a.status_id = OptionsEnum.INACTIVE
                        a.save()
                bin.save()
                activity_data.save()
                if preference.bin_pickup:
                    admin = User.objects.filter(customer=bin.customer, role_id=1)
                    for obj in admin:
                        user_group.append(obj.id)
                    notification = send_action_notification(truck.id, None, None,
                                                            bin,
                                                            "Bin contract terminated: " + bin.name,
                                                            IOFOptionsEnum.NOTIFICATION_DRIVER_BIN_PICKUP)
                    notification.save()
                    save_users_group(notification, user_group)
            else:
                return False, "You are not authorized to perform this operation. Please contact your Administrator"

            # collection.save()
            return True, "Succesfully performed operation"


def verification_management(bin, shift, supervisor, action):
    try:
        collection = BinCollectionData.objects.get(action_item=bin,
                                                   status_id__in=[IOFOptionsEnum.WASTE_COLLECTED,
                                                                  IOFOptionsEnum.BIN_PICKED_UP], verified__isnull=True)
    except:
        traceback.print_exc()
        collection = None
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
        if collection:
            collection.supervisor = supervisor
            collection.verified = True
            if collection.activity:
                activity_data = create_activity_data(collection.activity.id, collection.entity.id, collection.actor.id,
                                                     timezone.now(),
                                                     IOFOptionsEnum.VERIFY_COLLECTION, None, collection.action_item.id,
                                                     collection.customer_id,
                                                     collection.module_id, supervisor)
                activity_data.save()
            else:
                activity_data = create_activity_data(None, shift.parent.id, shift.child.id,
                                                     timezone.now(),
                                                     IOFOptionsEnum.VERIFY_COLLECTION, None, bin.id,
                                                     bin.customer_id,
                                                     bin.module_id, supervisor)
                activity_data.save()
    elif action == IOFOptionsEnum.SKIP_VERIFITCATION:
        if collection:
            collection.verified = False
            if collection.activity:
                activity_data = create_activity_data(collection.activity.id, collection.entity.id, collection.actor.id,
                                                     timezone.now(),
                                                     IOFOptionsEnum.SKIP_VERIFITCATION, None, collection.action_item.id,
                                                     collection.customer_id,
                                                     collection.module_id, None)
                activity_data.save()
            else:
                activity_data = create_activity_data(None, shift.parent.id, shift.child.id,
                                                     timezone.now(),
                                                     IOFOptionsEnum.SKIP_VERIFITCATION, None, bin.id,
                                                     bin.customer_id,
                                                     bin.module_id, None)
                activity_data.save()
    if collection:
        collection.save()
    return True, "Succesfully performed operation"


def get_contract(bin):
    try:
        contract = Assignment.objects.get(child__type_id=DeviceTypeEntityEnum.CONTRACT, parent=bin,
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
    ass.name = Entity.objects.get(pk=child).name + " Assigned to " + Entity.objects.get(id=parent).name
    ass.child_id = child
    ass.parent_id = parent
    ass.type_id = type
    ass.customer_id = customer
    ass.module_id = module
    ass.modified_by_id = modified_by
    ass.status_id = OptionsEnum.ACTIVE
    ass.save()


def util_create_incident_reporting(d_id, t_id, action_items, timestamp, activity_id, type_id, notes, customer_id,
                                   module_id):
    report = IncidentReporting(
        actor_id=d_id,
        primary_entity_id=t_id,
        action_items=action_items,
        scheduled_activity_id=activity_id,
        timestamp=timestamp,
        incident_type_id=type_id,
        notes=notes,
        customer_id=customer_id,
        module_id=module_id
    )
    return report


def get_schedule_type(activity):
    if activity.activity_schedule.end_date is None:
        return "Once"
    else:
        return "Multiple Days"


def incident_reporting_list(d_id, c_id, t_id):
    if d_id:
        incident_reporting = IncidentReporting.objects.filter(actor_id=d_id, customer_id=c_id).order_by('-timestamp')
    elif t_id:
        incident_reporting = IncidentReporting.objects.filter(actor_id=t_id, customer_id=c_id).order_by('-timestamp')
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

def check_entity_on_activity(d_id, t_id, c_id, b_id=None):
    if d_id:
        try:
            act = Activity.objects.get(actor_id=d_id, customer_id=c_id,
                                       activity_status_id__in=[IOFOptionsEnum.RUNNING, IOFOptionsEnum.SUSPENDED])
            if b_id:
                try:
                    BinCollectionData.objects.get(action_item_id=b_id, activity=act)
                    return True, act
                except:
                    return False, None
            else:
                return True, act
        except:
            return False, None

    elif t_id:
        try:
            act = Activity.objects.get(primary_entity_id=t_id, customer_id=c_id,
                                       activity_status_id__in=[IOFOptionsEnum.RUNNING, IOFOptionsEnum.SUSPENDED])
            if b_id:
                try:
                    BinCollectionData.objects.get(action_item_id=b_id, activity=act)
                    return True, act
                except:
                    return False, None
            else:
                return True, act
        except:
            return False, None
    else:
        return False, None


def check_entity_on_current_shift(d_id, t_id, c_id):
    if d_id:
        try:
            obj = IofShifts.objects.get(child_id=d_id, customer_id=c_id, shift_end_time__isnull=True)
            return True, obj
        except:
            return False, None

    elif t_id:
        try:
            obj = IofShifts.objects.get(parent_id=t_id, customer_id=c_id, shift_end_time__isnull=True)
            return True, obj
        except:
            return False, None

    else:
        try:
            obj = IofShifts.objects.get(customer_id=c_id, shift_end_time__isnull=True)
            return True, obj
        except:
            return False, None


def get_shift_data(d_id, t_id, c_id, start_date, end_date):
    if d_id:
        result = IofShifts.objects.filter(child_id=d_id)
    elif t_id:
        result = IofShifts.objects.filter(parent_id=t_id)
    elif c_id:
        result = IofShifts.objects.filter(customer_id=c_id)

    if start_date and end_date:
        result1 = result.filter(shift_start_time__range=[start_date, end_date])
        result2 = result.filter(shift_end_time__range=[start_date, end_date])
        final_result = result1 | result2
        result = final_result.distinct()
    return result.order_by('-shift_start_time')


def get_assets_list(c_id, m_id, index_a, index_b, t_id):
    entity_dict = {}
    if c_id:
        if t_id:
            t_id = int(t_id)
            ent = Entity.objects.filter(customer=c_id, type_id=t_id).exclude(status=OptionsEnum.DELETED).order_by(
                '-modified_datetime')
        else:
            ent = Entity.objects.filter(customer=c_id, type_id__in=[DeviceTypeEntityEnum.RFID_CARD,
                                                                    DeviceTypeEntityEnum.RFID_TAG,
                                                                    DeviceTypeEntityEnum.RFID_SCANNER]).exclude(
                status=OptionsEnum.DELETED).order_by('-modified_datetime')
        # Code un-reachable...
        # elif e_id:
        #     ent = Entity.objects.filter(customer=c_id, id=e_id).exclude(status=OptionsEnum.DELETED).order_by('-modified_datetime')


        tags_list = []
        bins_list = []
        cards_list = []
        trucks_list = []
        rfid_scanners_list = []

        # for obj in ent:
        if t_id == DeviceTypeEntityEnum.RFID_TAG:
            for i in range(index_a, index_b):
                try:
                    device = ent[i]
                except:
                    entity_dict['rfid_tags'] = tags_list
                    return entity_dict, False
                entity = ent[i].as_entity_json()
                try:
                    asset = Assignment.objects.get(child_id=ent[i].id, status=OptionsEnum.ACTIVE,
                                                   parent__type_id=DeviceTypeEntityEnum.BIN,
                                                   type_id=DeviceTypeAssignmentEnum.RFID_TAG_ASSIGMENT)
                    entity['assigned_asset'] = asset.parent.as_entity_json()
                except Exception as e:
                    entity['assigned_asset'] = None
                tags_list.append(entity)
            entity_dict['rfid_tags'] = tags_list

        elif t_id == DeviceTypeEntityEnum.CUSTOMER_DEVICE:
            gateways = CustomerDevice.objects.filter(customer_id=c_id, module_id=m_id).values('device_id',
                                                                                              'assigned',
                                                                                              'status__label',
                                                                                              'status_id',
                                                                                              'type_id',
                                                                                              'created_at',
                                                                                              'entity__name',
                                                                                              type_name=F(
                                                                                                  'type__name'))
            entity_dict['customer_devices'] = list(gateways)
            return entity_dict, False

        elif t_id == DeviceTypeEntityEnum.RFID_CARD:
            for i in range(index_a, index_b):
                try:
                    device = ent[i]
                except:
                    entity_dict['rfid_cards'] = cards_list
                    return entity_dict, False
                entity = ent[i].as_entity_json()
                try:
                    asset = Assignment.objects.get(child_id=ent[i].id, status=OptionsEnum.ACTIVE,
                                                   type_id=DeviceTypeAssignmentEnum.RFID_CARD_ASSIGMENT)
                    entity['assigned_asset'] = asset.parent.as_entity_json()
                except Exception as e:
                    entity['assigned_asset'] = None
                cards_list.append(entity)
            entity_dict['rfid_cards'] = cards_list

        elif t_id == DeviceTypeEntityEnum.RFID_SCANNER:
            for i in range(index_a, index_b):
                try:
                    device = ent[i]
                except:
                    entity_dict['rfid_scanners'] = rfid_scanners_list
                    return entity_dict, False
                entity = ent[i].as_entity_json()
                try:
                    asset = Assignment.objects.get(child_id=ent[i].id, status=OptionsEnum.ACTIVE,
                                                   parent__type=DeviceTypeEntityEnum.TRUCK,
                                                   type_id=DeviceTypeAssignmentEnum.RFID_ASSIGNMENT)
                    entity['assigned_asset'] = asset.parent.as_entity_json()
                except Exception as e:
                    entity['assigned_asset'] = None
                rfid_scanners_list.append(entity)
            entity_dict['rfid_scanners'] = rfid_scanners_list

        return entity_dict, True


def get_latest_value_of_truck(truck_id, past):
    try:
        latest_value = None
        if past:
            # Get value of past somehow. 10 minutes before? Look in PostData.
            past_timestamp = datetime.datetime.now() - datetime.timedelta(minutes=15)
            try:
                latest_value = HypernetPostData.objects.filter(device_id=truck_id,
                                                               timestamp__year=past_timestamp.year,
                                                               timestamp__month=past_timestamp.month,
                                                               timestamp__day=past_timestamp.day,
                                                               timestamp__hour=past_timestamp.hour,
                                                               timestamp__minute=past_timestamp.minute) \
                    .order_by('-timestamp').first()
                print('Latest weight and time:' + str(latest_value.accelerometer_1) + ' ' + str(latest_value.timestamp))
            except:
                traceback.print_exc()
                return False, "An error occurred. Please scan again after a few minutes."
        else:
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
                    return False, "An error occurred. Please scan again after a few minutes."
    finally:
        return latest_value


def calculate_invoice(action, collection, latest_value, bin_name, shift):
    contract = get_contract(bin_name)
    message = ""
    if not contract:
        return False, "Contract does not exist for scanned bin"

    # if action == IOFOptionsEnum.PICKUP_BIN or action == IOFOptionsEnum.COLLECT_WASTE:
    # Replacing actions because now they make sense, record value of truck weight when skip is on it.
    # if action == IOFOptionsEnum.COLLECT_WASTE:
    #     collection.pre_weight = latest_value.accelerometer_1

    # elif action == IOFOptionsEnum.BIN_PICKED_UP or action == IOFOptionsEnum.WASTE_COLLECTED:
    # Replacing bin picked up with drop off to simulate when bin is being dropped at location after waste dumping in dumpyard
    if action == IOFOptionsEnum.DROPOFF_BIN or action == IOFOptionsEnum.WORKSHOP_DROP:
        message = "Warning! Picked up bin " + bin_name.name + " by driver " + shift.child.name + ". Weight collected is 0"
        if contract.leased_owned:
            if contract.leased_owned.id == IOFOptionsEnum.TRIP_BASED:
                collection.post_weight = float(latest_value.accelerometer_1)
                collection.weight = collection.post_weight - collection.pre_weight
                collection.invoice = contract.skip_rate
                collection.status_id = action
                collection.timestamp = timezone.now()
            elif contract.leased_owned.id == IOFOptionsEnum.WEIGHT_AND_TRIP_BASED:
                pass
            elif contract.leased_owned.id == IOFOptionsEnum.WEIGHT_BASED:
                collection.post_weight = float(latest_value.accelerometer_1)
                collection.weight = collection.post_weight - collection.pre_weight
                collection.invoice = 20  # Multiplier based on contract and bin waste type
                collection.status_id = action
                collection.timestamp = timezone.now()

            elif contract.leased_owned.id == IOFOptionsEnum.LUMP_SUM:
                pass
        else:
            if contract.skip_rate:
                collection.post_weight = float(latest_value.accelerometer_1)
                collection.weight = collection.post_weight - collection.pre_weight
                collection.invoice = contract.skip_rate
                collection.status_id = action
                collection.timestamp = timezone.now()
            else:
                return False, "Contract does not have any skip rate. \n" + contract.name
        if collection.weight is None or collection.weight <= 0:
            user_group = []
            driver_user = User.objects.get(associated_entity=shift.child).id
            user_group.append(driver_user)
            admin = User.objects.filter(customer=shift.customer, role_id=1)
            for obj in admin:
                user_group.append(obj.id)
            from hypernet.notifications.utils import send_action_notification, save_users_group
            collection_id = collection.activity.id if collection.activity else None
            notification = send_action_notification(shift.parent.id, shift.child.id, collection_id,
                                                    shift, message,
                                                    IOFOptionsEnum.NOTIFICATION_DRIVER_BIN_PICKUP)

            notification.save()
            save_users_group(notification, user_group)

    elif action == IOFOptionsEnum.WASTE_COLLECTED:
        if contract.leased_owned:
            if contract.leased_owned.id == IOFOptionsEnum.TRIP_BASED:
                collection.invoice = contract.skip_rate
                collection.status_id = action
                collection.timestamp_2 = timezone.now()
            elif contract.leased_owned.id == IOFOptionsEnum.WEIGHT_AND_TRIP_BASED:
                pass
            elif contract.leased_owned.id == IOFOptionsEnum.WEIGHT_BASED:
                collection.invoice = 20  # Multiplier based on contract and bin waste type
                collection.status_id = action
                collection.timestamp_2 = timezone.now()

            elif contract.leased_owned.id == IOFOptionsEnum.LUMP_SUM:
                pass
        else:
            if contract.skip_rate:
                collection.invoice = contract.skip_rate
                collection.status_id = action
                collection.timestamp_2 = timezone.now()
            else:
                return False, "Contract does not have any skip rate. \n" + contract.name

    if action == IOFOptionsEnum.DROPOFF_BIN or action == IOFOptionsEnum.WORKSHOP_DROP:
        # This is to avoid any confusion when generating reports.
        # Drop off bin is called during a collection then it is picked up and invoice is generated.
        collection.status_id = IOFOptionsEnum.BIN_PICKED_UP
    collection.save()
    return True, collection


def update_skip_weight(truck, bin):
    try:
        val = get_latest_value_of_truck(truck.id, False)
        try:
            collection = BinCollectionData.objects.get(action_item=bin, entity=truck,
                                                       status_id=IOFOptionsEnum.COLLECTED, weight__isnull=True)
            collection.weight = collection.pre_weight - val.volume
            # Logic to calculate invoice per kg waste collected.
            collection.save()
        except:
            pass
        finally:
            bin.volume_capacity = val.volume
            bin.save()
            return True, "Successfully updated Skip Weight.\n ID:" + bin.name + "\nSkip Weight:" + bin.weight
    except:
        return False, "Unable to update weight at the moment. Please try again in a few minutes."


def report_bin_maintenance(truck, bin):
    try:
        on_shift, shift = check_shift_on_truck(truck)
        if not on_shift:
            return False, shift
        maintenance = LogisticMaintenance()
        maintenance.truck = bin
        maintenance.customer = bin.customer
        maintenance.module = bin.module
        maintenance.modified_by = shift.child.associated_user.all()[0]
        # maintenance.modified_by = bin.customer.modified_by
        maintenance.driver = shift.child
        maintenance.start_datetime = timezone.now()
        maintenance.end_datetime = timezone.now() + datetime.timedelta(days=7)
        maintenance.maintenance_type_id = IOFOptionsEnum.SERVICE_MAINTENANCE
        maintenance.status_id = IOFOptionsEnum.MAINTENANCE_APPROVAL
        maintenance.save()
        try:
            data = LogisticMaintenanceData()
            data.maintenance = maintenance
            data.customer = bin.customer
            data.module = bin.module
            data.modified_by = shift.child.associated_user.all()[0]
            # data.modified_by = bin.customer.modified_by
            data.truck = bin
            data.driver = shift.child
            data.action_id = IOFOptionsEnum.SERVICE_MAINTENANCE
            data.timestamp = timezone.now()
            data.save()
        except:
            traceback.print_exc()
            return False, "An Error occurred while registering the maintenance. Please contact your Administrator."

        return True, "Succesfully reported maintenance for .\n ID:" + bin.name + "\nClient:" + bin.client.name
    except:
        traceback.print_exc()
        return False, "Unable to report maintenance. Please contact your Administrator."


def check_activity_on_truck(truck):
    try:
        act = Activity.objects.get(primary_entity=truck,
                                   activity_status_id__in=[IOFOptionsEnum.RUNNING, IOFOptionsEnum.SUSPENDED])
    except Activity.DoesNotExist:
        return False, "No activity for truck. Please ensure the RFID Scanner being used is the one authorised for this activity. " \
                      "\nIf the problem persists contact your administrator."
    return True, act


def check_schedule_on_truck(truck):
    data = ActivitySchedule.objects.filter(primary_entity=truck,
                                           schedule_activity_status_id__in=[OptionsEnum.ACTIVE])
    if data.count() > 0:
        return True, "Scanner cannot be marked inactive as it has a valid schedule. Suspend the schedule and try again." \
                     "\nIf the problem persists contact your administrator."
    else:
        return False, None


def check_shift_on_truck(truck):
    try:
        shift = IofShifts.objects.get(parent=truck, shift_end_time__isnull=True)
    except:
        return False, "Truck shift data is not available. Please start shift before proceeding"
    return True, shift


def get_shift_truck_of_driver(driver, driver_id=None):
    try:
        if driver:
            truck = IofShifts.objects.get(child=driver, shift_end_time__isnull=True).parent
        elif driver_id:
            truck = IofShifts.objects.get(child_id=driver_id, shift_end_time__isnull=True).parent
    except:
        return False, "Driver has no shift. Please contact your administrator"
    return True, truck


def get_clients_invoice(client, customer, status, start_datetime, end_datetime, contracts=None):
    collection_data = None
    if client:
        collection_data = BinCollectionData.objects.filter(client_id=client, customer_id=customer, status_id__in=status)
        if contracts and collection_data:
            collection_data = collection_data.filter(contract_id__in=contracts, status_id__in=status)
    else:
        collection_data = BinCollectionData.objects.filter(customer_id=customer, status_id__in=status)

    if start_datetime and end_datetime:
        collection_data = collection_data.filter(timestamp__range=[start_datetime, end_datetime])

    return collection_data


def check_bin_in_activity(activity, bin_data, response_body):
    flag = True
    for b_c in bin_data:
        if b_c.status_id == IOFOptionsEnum.WASTE_COLLECTED or b_c.status_id == IOFOptionsEnum.BIN_PICKED_UP or b_c.status_id == IOFOptionsEnum.UNCOLLECTED:
            if b_c.activity == activity:
                response_body[RESPONSE_DATA] = TEXT_OPERATION_UNSUCCESSFUL
                response_body[RESPONSE_MESSAGE] = ENTITY_ALREADY_COLLECTED + '\nBin ID: ' + b_c.action_item.name
                response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                flag = False

            elif b_c.activity.activity_status_id == IOFOptionsEnum.RUNNING or b_c.activity.activity_status_id == IOFOptionsEnum.SUSPENDED:
                response_body[RESPONSE_DATA] = TEXT_OPERATION_UNSUCCESSFUL
                response_body[
                    RESPONSE_MESSAGE] = ENTITY_PART_OF_ACTIVITY + '\nBin ID: ' + b_c.action_item.name
                response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                flag = False
    return flag


def check_activities_to_be_performed(c_id):
    if Activity.objects.filter(customer_id=c_id,
                               activity_status_id__in=[IOFOptionsEnum.RUNNING, IOFOptionsEnum.SUSPENDED,
                                                       IOFOptionsEnum.ACCEPTED]).count() > 0:
        return True
    else:
        return False


def check_asset_in_activity(bin_id, area_id, client_id, contract_id):
    if bin_id:
        try:
            BinCollectionData.objects.get(activity__activity_status_id=IOFOptionsEnum.RUNNING, action_item_id=bin_id,
                                          status_id__in=[IOFOptionsEnum.UNCOLLECTED,
                                                         IOFOptionsEnum.WASTE_COLLECTED,
                                                         IOFOptionsEnum.BIN_PICKED_UP])
            return True
        except:
            return False
    current_bins = BinCollectionData.objects.filter(activity__activity_status_id=IOFOptionsEnum.RUNNING,
                                                    status_id__in=[IOFOptionsEnum.UNCOLLECTED,
                                                                   IOFOptionsEnum.WASTE_COLLECTED,
                                                                   IOFOptionsEnum.BIN_PICKED_UP])
    found = False
    if area_id:
        for one_bin in current_bins:
            if one_bin.area_id == area_id:
                return True
        return False

    if client_id:
        for one_bin in current_bins:
            if one_bin.client_id == client_id:
                return True
        return False

    if contract_id:
        for one_bin in current_bins:
            if one_bin.contract_id == contract_id:
                return True
        return False


def maintain_excel(data):
    if data:
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = 'Quotation'
        for row, text in enumerate(data, start=1):
            ws.cell(column=1, row=row, value=text)
        wb.save('assignment_data.xlsx')
    else:
        return None


def parent_child_assignment(parent, child, type_id):
    assignment = Assignment(
        name=child.name + " Assigned to "
             + parent.name,
        child=child,
        parent=parent,
        customer=parent.customer,
        module=parent.module,
        type_id=type_id,
        status_id=OptionsEnum.ACTIVE,
        modified_by=parent.modified_by,
    )
    return assignment


def waste_collection_management_withou_rfid(bin, truck, action, location, invoice, weight):
    preference = CustomerPreferences.objects.get(customer=bin.customer)
    user_group = []
    on_shift, shift = check_shift_on_truck(truck)
    if not on_shift:
        return False, shift
    try:
        collection = BinCollectionData.objects.get(action_item=bin, status_id=IOFOptionsEnum.UNCOLLECTED)
    except:
        collection = create_bin_collection_data(None, shift.parent.id, shift.child.id, timezone.now(),
                                                IOFOptionsEnum.UNCOLLECTED, bin.id, bin.customer.id, bin.module.id)
        # return False, "Bin is already collected or bin is not part of any activity. Please contact administrator."
        traceback.print_exc()
    if bin.obd2_compliant == False:
        return False, "Bin is already picked up and waste cannot be collected. Please drop off the bin in the field before picking up the bin."
    # latest_value = get_latest_value_of_truck(collection.entity.id)
    # if not latest_value:
    #    return False, "No data is available to calculate weight. Please wait for a few minutes or contact your administrator."
    # if not latest_value.validity:
    #    return False, "Valid weight is not available. Please scan again after a few minutes."

    if get_contract(bin):
        pass  # collection.weight * get_contract(bin)
    else:
        return False, "Contract does not exist for scanned bin"

        # if action:
        # Logic to calculate invoice, UNCOMMENT when in production testing WALEED
        # success, collection = calculate_invoice(action, collection, latest_value, bin)
        # if not success:
        #   return success, collection

    collection.status_id = IOFOptionsEnum.WASTE_COLLECTED
    collection.timestamp = timezone.now()
    collection.invoice = invoice
    collection.weight = weight
    collection.save()
    # create_bin_event(collection.entity, bin, IOFOptionsEnum.WASTE_COLLECTED, collection.activity)
    if collection.activity:
        activity_data = create_activity_data(collection.activity.id, shift.parent.id, shift.child.id,
                                             timezone.now(),
                                             IOFOptionsEnum.WASTE_COLLECTED, location, collection.action_item.id,
                                             collection.customer_id,
                                             collection.module_id)
        activity_data.save()
    else:
        activity_data = create_activity_data(None, shift.parent.id, shift.child.id,
                                             timezone.now(),
                                             IOFOptionsEnum.WASTE_COLLECTED, location, collection.action_item.id,
                                             collection.customer_id,
                                             collection.module_id)
        activity_data.save()

    if preference.waste_collection:
        driver = shift.child
        driver_user = User.objects.get(associated_entity=driver).id
        user_group.append(driver_user)
        admin = User.objects.filter(customer=bin.customer, role_id=1)
        for obj in admin:
            user_group.append(obj.id)
        if collection.activity:
            notification = send_action_notification(shift.parent.id, shift.child.id, collection.activity.id, bin,
                                                    driver.name + " successfully Collected Waste.\nID: " + bin.name,
                                                    IOFOptionsEnum.NOTIFICATION_DRIVER_WASTE_COLLECTION)
        else:
            notification = send_action_notification(shift.parent.id, shift.child.id, None, bin,
                                                    driver.name + " successfully Collected Waste.\nID: " + bin.name,
                                                    IOFOptionsEnum.NOTIFICATION_DRIVER_WASTE_COLLECTION)
        notification.save()
        save_users_group(notification, user_group)
    return True, "Successfully Collected Waste.\nID: " + bin.name


def driver_shift_management_revised(truck, driver, start):
    if driver.type_id != DeviceTypeEntityEnum.DRIVER:
        return False, "Scanned RFID does not belong to a Driver. \nPlease contact your administrator"
    if start:
        try:
            shift = IofShifts.objects.get(child=driver, shift_end_time__isnull=True)
            return False, "You have already started your shift at:" + str(shift.shift_start_time)
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
        return True, "You have succesfully started your shift on truck " + truck.name + " at: " + str(
            shift.shift_start_time)
    else:
        try:
            shift = IofShifts.objects.get(child=driver, shift_end_time__isnull=True)
        except:
            return False, "No Shift for Driver: " + driver.name
        try:
            Activity.objects.get(primary_entity=truck, actor=driver,
                                 status_id__in=[IOFOptionsEnum.RUNNING, IOFOptionsEnum.SUSPENDED])
            return False, "You are currently on an activity. Cannot end shift while on an activity"
        except:

            shift.shift_end_time = timezone.now()
            shift.save()
            return True, "You have succesfully ended the shift on truck " + truck.name + " at: " + str(
                shift.shift_start_time)


def get_contract_listing(c_id, m_id, t_id, context, index_a, index_b, e_id=None):
    from django.core.cache import cache
    entity_list = []

    current_month = datetime.datetime.today().month
    current_year = datetime.datetime.today().year

    contracts = Entity.objects.filter(customer_id=c_id, type_id=DeviceTypeEntityEnum.CONTRACT).exclude(
        status_id=OptionsEnum.DELETED).order_by(
        '-modified_datetime').distinct()
    if t_id == 'new':
        contracts = contracts.filter(created_datetime__month=current_month,
                                     created_datetime__year=current_year).exclude(status_id=OptionsEnum.INACTIVE)
    elif t_id == 'expiring':
        contracts = contracts.filter(date_of_joining__month=current_month, date_of_joining__year=current_year).exclude(
            status_id=OptionsEnum.INACTIVE)
        contracts = contracts.filter(date_of_joining__gte=datetime.datetime.today().date()).exclude(
            status_id=OptionsEnum.INACTIVE).exclude(speed=True)
    elif t_id == 'expired':
        contracts = contracts.filter(date_of_joining__lte=datetime.datetime.today().date()).exclude(
            status_id=OptionsEnum.INACTIVE).exclude(speed=True)
    elif t_id == 'renewed':
        contracts = contracts.filter(speed=True)
    elif t_id == 'deactivated':
        contracts = contracts.filter(status_id=OptionsEnum.INACTIVE)

    for i in range(index_a, index_b):
        try:
            device = contracts[i]
        except:
            return entity_list, False

        cache_key = device.id  # needs to be unique
        entity_dict = cache.get(cache_key)  # returns None if no key-value pair
        if not entity_dict:
            contract_data = ClientContractSerializer(device, context=context)
            entity_dict = contract_data.data
            bins = Assignment.objects.filter(child_id=device.id, status_id=OptionsEnum.ACTIVE,
                                             type_id=DeviceTypeAssignmentEnum.CONTRACT_ASSIGNMENT)
            ass_truck = []

            for e in bins:
                ass_truck.append(e.parent.as_entity_json())
            entity_dict['assigned_bins'] = ass_truck
            entity_dict['assigned_bins_count'] = bins.count()
            try:
                area = Assignment.objects.get(child_id=device.id, status_id=OptionsEnum.ACTIVE,
                                              type_id=DeviceTypeAssignmentEnum.AREA_CONTRACT_ASSIGNMENT)

                entity_dict['assigned_area_id'] = area.parent.id
                entity_dict['assigned_area_name'] = area.parent.name

            except Exception as e:
                entity_dict['assigned_area_id'] = None
                entity_dict['assigned_area_name'] = None
            try:
                location = Assignment.objects.get(child_id=device.id, status_id=OptionsEnum.ACTIVE,
                                                  type_id=DeviceTypeAssignmentEnum.LOCATION_CONTRACT_ASSIGNMENT)

                entity_dict['assigned_location_id'] = location.parent.id
                entity_dict['assigned_location_name'] = location.parent.name

            except Exception as e:
                entity_dict['assigned_location_id'] = None
                entity_dict['assigned_location_name'] = None
            cache.set(key=cache_key, value=entity_dict, timeout=None)
        entity_list.append(entity_dict)
    return entity_list, True


def renew_contract(customer_id, contract_id, new_date):
    try:
        contract = Entity.objects.get(id=contract_id, customer_id=customer_id)
        if new_date:
            contract.date_of_joining = new_date
            contract.speed = True
        else:
            contract.status_id = OptionsEnum.INACTIVE
        contract.save()
        return True, None
    except:
        traceback.print_exc()
        return False, "An issue occurred. Please contact your Administrator."


def calculate_labour_cost(ent, duration):  # duration in mins
    if ent:
        if ent.salary:  # if salary is defined for the driver
            wage_per_min = ent.salary / 60
            total_cost = wage_per_min * duration
            return total_cost
    return 0


def calculate_fuel_cost(ent, fuel_consumed):
    if ent:
        try:
            if not fuel_consumed:
                fuel_consumed = 0
            try:
                pref_obj = CustomerPreferences.objects.get(customer=ent.customer)
            except:
                pref_obj = None
                traceback.print_exc()
            if pref_obj:
                if pref_obj.diesel_price:  # Incase diesel cost in not added to system
                    diesel_price = pref_obj.diesel_price
                    return diesel_price * fuel_consumed
                else:
                    return 0
        except:
            traceback.print_exc()
    else:
        return None


def calculate_trip_revenue(act_id, truck_id=None, driver_id=None):
    if act_id:
        b_collection = BinCollectionData.objects.filter(activity_id=act_id)

        total_revenue = b_collection.aggregate(revenue=Sum('invoice'))

        return total_revenue['revenue']


def calculate_trip_waste_collected(act_id, truck_id=None, driver_id=None):
    if act_id:
        b_collection = BinCollectionData.objects.filter(activity_id=act_id)

        total_waste_collected = b_collection.aggregate(Sum('weight'))

        return total_waste_collected['weight__sum']


def get_invoice_listing(invoice_id, customer, start_datetime, end_datetime):
    if invoice_id:
        result = InvoiceData.objects.get(id=invoice_id)
    else:
        result = InvoiceData.objects.filter(customer_id=customer)
    if start_datetime and end_datetime:
        result = result.filter(timestamp__range=[start_datetime, end_datetime])
    return result


def update_invoice_payment_status(invoice_id, payment_status, customer):
    try:
        if invoice_id:
            result = InvoiceData.objects.get(id=invoice_id, customer_id=customer)
            result.payment_status = payment_status
            result.save()
            return result
    except:
        traceback.print_exc()
        return None


def get_bins_collected(b_id, d_id, t_id, c_id, start_datetime, end_datetime, status):
    # action item = b_id, actor = d_id, entity = t_id
    if b_id:
        result = BinCollectionData.objects.filter(action_item_id=b_id, customer_id=c_id)
    elif d_id:
        result = BinCollectionData.objects.filter(actor_id=d_id, customer_id=c_id)
    elif t_id:
        result = BinCollectionData.objects.filter(entity_id=t_id, customer_id=c_id)
    else:
        result = BinCollectionData.objects.filter(customer_id=c_id)
    if start_datetime and end_datetime:
        result = result.filter(timestamp__range=[start_datetime, end_datetime])
    return result.filter(status_id__in=status)


def dropoff_invoice(truck, bin, action, shift, notification_already_sent):
    try:
        latest_value = get_latest_value_of_truck(truck.id, True)
        collection = BinCollectionData.objects.get(action_item_id=bin.id, action_item__obd2_compliant=False,
                                                   status_id=IOFOptionsEnum.BIN_PICKED_UP, invoice__isnull=True)
    except:
        latest_value = None
        collection = None
        traceback.print_exc()

        # return False, "The Bin is registered as Stored. Please Drop Bin before Picking Up Bin. Contact Administrator for details."
    if collection and latest_value:
        success, collection = calculate_invoice(action, collection, latest_value, bin, shift)
        if not success:
            return success, collection
        collection.save()
        preference = CustomerPreferences.objects.get(customer=bin.customer)
        if preference.bin_pickup and notification_already_sent is False:
            user_group = []
            driver = shift.child
            driver_user = User.objects.get(associated_entity=shift.child).id
            user_group.append(driver_user)
            admin = User.objects.filter(customer=shift.customer, role_id=1)
            for obj in admin:
                user_group.append(obj.id)
            if collection.activity:
                notification = send_action_notification(shift.parent.id, shift.child.id, collection.activity.id,
                                                        shift,
                                                        driver.name + " successfully completed collection\nBin: " + bin.name + "\nClient: " + bin.client.name + "\nWeight Collected: " + str(
                                                            collection.weight),
                                                        IOFOptionsEnum.NOTIFICATION_DRIVER_BIN_PICKUP)
            else:
                notification = send_action_notification(shift.parent.id, shift.child.id, None, shift,
                                                        driver.name + " successfully completed collection \nBin: " + bin.name + "\nClient: " + bin.client.name + "\nWeight Collected: " + str(
                                                            collection.weight),
                                                        IOFOptionsEnum.NOTIFICATION_DRIVER_BIN_PICKUP)
            notification.save()
            save_users_group(notification, user_group)
        return True
    else:
        return False


def vehicle_type_reporting(type_id, drivers, c_id, start_datetime, end_datetime, truck_ids=None):
    return_list = []
    try:
        if type_id:
            vehicles = Entity.objects.filter(entity_sub_type_id=type_id, customer_id=c_id).values_list('id', flat=True)
        else:
            vehicles = Entity.objects.filter(type_id=DeviceTypeEntityEnum.TRUCK, customer_id=c_id).values_list('id',
                                                                                                               flat=True)

        if drivers == 1:
            vehicles = Entity.objects.filter(type_id=DeviceTypeEntityEnum.DRIVER, customer_id=c_id).values_list('id',
                                                                                                                flat=True)

        # For zenath client truck reporting, hardcoded ids are sent here
        if truck_ids:
            vehicles = vehicles.filter(id__in=truck_ids)

        for v in vehicles:
            truck = Entity.objects.get(id=v).name
            single_record = dict()
            if drivers == 1:
                shifts = get_shift_data(v, None, c_id, start_datetime, end_datetime)
            else:
                shifts = get_shift_data(None, v, c_id, start_datetime, end_datetime)
            # To get latest in the end to reprsent a running shift
            shifts = shifts.order_by('shift_start_time')

            single_record['shifts'] = shifts.count()
            if single_record['shifts'] == 0:
                if drivers == 1:
                    single_record['driver'] = truck
                else:
                    single_record['truck'] = truck
                    single_record['truck'] = truck
                    single_record = initialize_record_truck_dashboard_reporting(single_record)
                    single_record = compute_collection_data_truck_dashboard_reporting(v, drivers, single_record,
                                                                                      start_datetime, end_datetime,
                                                                                      None)
                    single_record['total_distance'] = float(
                        get_generic_distance_travelled(c_id, v, None, None, start_datetime, end_datetime) / 1000)
                    single_record['volume_consumed'] = float(
                        get_generic_volume_consumed(c_id, v, None, None, start_datetime, end_datetime))
                    if single_record['volume_consumed'] > 0:
                        single_record['volume_consumed'] = round(single_record['volume_consumed'] / 1000 * 0.219, 3)
                        single_record['fuel_avg'] = single_record['total_distance'] / single_record[
                            'volume_consumed'] or 0
                    else:
                        single_record['fuel_avg'] = 0
                return_list.append(single_record)
            if shifts.exists():
                for shift in shifts:
                    single_record = dict()
                    if drivers == 1:
                        single_record['driver'] = truck
                        single_record['truck'] = shift.parent.name
                    else:
                        single_record['truck'] = truck
                        single_record['driver'] = shift.child.name
                    ################################################################################
                    if drivers == 1:
                        found, ind = find_index_of_existing(return_list, 'driver', truck, 'truck', shift.parent.name)
                    else:
                        found, ind = find_index_of_existing(return_list, 'truck', truck, 'driver', shift.child.name)
                    # Logic to get existing row or create new row if driver and truck mismatch
                    if found:
                        single_record = return_list[ind]
                    else:
                        single_record = initialize_record_truck_dashboard_reporting(single_record)
                        single_record = compute_collection_data_truck_dashboard_reporting(v, drivers, single_record,
                                                                                          start_datetime, end_datetime,
                                                                                          shift)
                        return_list.append(single_record)
                    ##################################################################################

                    single_record['shifts'] += 1
                    if shift.shift_end_time:
                        single_record['running'] = False
                        single_record['total_duration'] += shift.shift_duration
                        single_record['total_trips'] += shift.trips
                        single_record['total_distance'] += shift.distance_travelled or 0
                        single_record['volume_consumed'] += shift.volume_consumed or 0

                        if single_record['volume_consumed'] > 0:
                            single_record['fuel_avg'] = single_record['total_distance'] / single_record[
                                'volume_consumed'] or 0
                        else:
                            single_record['fuel_avg'] = 0
                    else:
                        single_record['running'] = True

        for obj in return_list:
            if obj.get('total_duration'):
                if obj['total_duration'] != 0:
                    obj['manpower'] = obj['manpower'] / obj['total_duration'] * 60
                else:
                    obj['manpower'] = 0


    except:
        traceback.print_exc()
    return return_list


def find_index_of_existing(dicts, key, value, key2, value2):
    class Null:
        pass

    for i, d in enumerate(dicts):
        if d.get(key, Null) == value:
            if d.get(key2, Null) == value2:
                return True, i
    else:
        return False, None


def initialize_record_truck_dashboard_reporting(single_record):
    single_record['shifts'] = 0
    single_record['total_collections'] = 0
    single_record['total_weight'] = 0
    single_record['total_duration'] = 0
    single_record['total_trips'] = 0
    single_record['total_distance'] = 0
    single_record['volume_consumed'] = 0
    single_record['fuel_avg'] = 0
    return single_record


def compute_collection_data_truck_dashboard_reporting(truck_id, drivers, single_record, start_datetime, end_datetime,
                                                      shift=None):
    ###################################################################################
    # Different skips stats to be inserted into this row
    val = 0
    if shift:
        if drivers == 1:
            data = BinCollectionData.objects.filter(entity_id=shift.parent.id, actor_id=truck_id,
                                                    timestamp__range=[start_datetime, end_datetime])
        else:
            data = BinCollectionData.objects.filter(entity_id=truck_id, actor_id=shift.child.id,
                                                    timestamp__range=[start_datetime, end_datetime])
    else:
        data = BinCollectionData.objects.filter(entity_id=truck_id, timestamp__range=[start_datetime, end_datetime])
    for d in data:
        if not single_record.get(IOFOptionsEnum.labels.get(d.action_item.skip_size.id)):
            single_record[IOFOptionsEnum.labels.get(d.action_item.skip_size.id)] = 1
        else:
            single_record[IOFOptionsEnum.labels.get(d.action_item.skip_size.id)] += 1
        if IOFOptionsEnum.labels.get(d.action_item.skip_size.id).split()[1] == 'cbm':
            val += float(IOFOptionsEnum.labels.get(d.action_item.skip_size.id).split()[0])
    single_record['total_collections'] = data.count()
    single_record['total_weight'] = data.aggregate(Sum('weight'))['weight__sum'] or 0
    single_record['manpower'] = val

    return single_record
    ######################## Data complete for collection  ##############################


def update_collection_for_truck(truck, weight, timestamp):
    on_shift, shift = check_shift_on_truck(truck)
    if not on_shift:
        return False, "Shift data not available."

    try:  # Check if there is a post weight to be added yet, weight calculation pending
        # Get latest of waste collected status Bins. These can be multiple depending on how impatient the driver is.
        # collection = BinCollectionData.objects.get(entity_id=truck.id, action_item__obd2_compliant=True,
        #                                                status_id=IOFOptionsEnum.WASTE_COLLECTED,
        #                                                 post_weight__isnull=True)
        # This query is incase a colleciton is fast forwarded and we never got the pre weight set for the collection in time
        collection = BinCollectionData.objects.filter(entity_id=truck.id, action_item__obd2_compliant=True,
                                                      status_id__in=[IOFOptionsEnum.COLLECT_WASTE,
                                                                     IOFOptionsEnum.WASTE_COLLECTED],
                                                      pre_weight__isnull=True).order_by('timestamp')
        if collection.exists():
            # We got a collection object, now we assign it to first instance that we got
            collection = collection.first()
            # Always check the times! This is new checkand very crucial to the working of weight calculation
            if timestamp > collection.timestamp:  # TODO: Need to test this code are they valid timestamps?
                collection.pre_weight = float(weight)
                collection.save()

        else:  # Now check if there is a pre weight to be added for a colleciton with the status of collect waste
            # This is when the driver has scanned and we have to get the value of truck as is currently
            collection = BinCollectionData.objects.filter(entity_id=truck.id, action_item__obd2_compliant=True,
                                                          status_id=IOFOptionsEnum.WASTE_COLLECTED,
                                                          post_weight__isnull=True, pre_weight__isnull=False,
                                                          # Added weight check for distinguishing suez and zenath collections
                                                          weight__isnull=True).order_by('timestamp_2')
            if collection.exists():
                # We got a collection object, now we assign it to first instance that we got
                collection = collection.first()
                # Always check the times! This is new checkand very crucial to the working of weight calculation
                if timestamp > collection.timestamp_2:  # TODO: Need to test this code are they valid timestamps?

                    collection.post_weight = float(weight)
                    collection.weight = collection.post_weight - collection.pre_weight
                    collection.save()
                return True, "Pre weight code segment for waste collection"
            else:
                try:
                    # This is when driver has placed the skip on his vehicle. After pressing the confirm button
                    collection = BinCollectionData.objects.get(entity_id=truck.id, action_item__obd2_compliant=False,
                                                               status_id=IOFOptionsEnum.BIN_PICKED_UP,
                                                               post_weight__isnull=True)
                    collection.pre_weight = float(weight)
                    collection.save()
                    return True, "Success"
                except:
                    collection = None
    except:
        traceback.print_exc()
        collection = None
        # print('No collection. Truck: ' + truck.name)
    if collection:
        if collection.status.id == IOFOptionsEnum.WASTE_COLLECTED:
            message = "Warning! Weight collected is 0. Waste collected from bin " + collection.action_item.name + \
                      "\n Client: " + collection.client.name + "\nDriver: " + shift.child.name
        elif collection.status.id == IOFOptionsEnum.BIN_PICKED_UP:
            message = "Warning! Weight collected is 0. Picked up bin " + collection.action_item.name + \
                      "\n Client: " + collection.client.name + "\nDriver: " + shift.child.name

        if collection.weight is None or collection.weight <= 0:
            user_group = []
            driver_user = User.objects.get(associated_entity=shift.child).id
            user_group.append(driver_user)
            admin = User.objects.filter(customer=shift.customer, role_id=1)
            for obj in admin:
                user_group.append(obj.id)
            from hypernet.notifications.utils import send_action_notification, save_users_group
            collection_id = collection.activity.id if collection.activity else None
            notification = send_action_notification(shift.parent.id, shift.child.id, collection_id,
                                                    shift, message,
                                                    IOFOptionsEnum.NOTIFICATION_DRIVER_BIN_PICKUP)

            notification.save()
            save_users_group(notification, user_group)
            return True, "Success"


############# e2e util for collection TODO: Remove in future
def collect_package(bin, location, user):
    user_group = []
    driver = user.associated_entity
    try:
        collection = BinCollectionData.objects.get(action_item=bin, status_id=IOFOptionsEnum.UNCOLLECTED)
        collection.status_id = IOFOptionsEnum.PACKAGE_DROP
        collection.timestamp = timezone.now()
        collection.save()
        # create_bin_event(collection.entity, bin, IOFOptionsEnum.WASTE_COLLECTED, collection.activity)

        activity_data = create_activity_data(None, None, driver.id,
                                             timezone.now(),
                                             IOFOptionsEnum.PACKAGE_DROP, location, collection.action_item.id,
                                             collection.customer_id,
                                             collection.module_id)
        activity_data.save()
        # driver_user = User.objects.get(associated_entity=driver).id
        # user_group.append(driver_user)
        admin = User.objects.filter(customer=bin.customer, role_id=1)
        for obj in admin:
            user_group.append(obj.id)

        notification = send_action_notification(None, None, None, bin,
                                                driver.name + " successfully Dropped of package.\nID: " + bin.name + "\nClient:" + bin.client.name,
                                                IOFOptionsEnum.NOTIFICATION_DRIVER_WASTE_COLLECTION)
        notification.save()
        save_users_group(notification, user_group)
        return True, "Successfully Dropped package.\nID: " + bin.name + "\nClient:" + bin.client.name
    except:
        traceback.print_exc()
        return False, "Operation failed. Please try again later"


def start_e2e_collection(location, user):
    user_group = []
    driver = user.associated_entity
    try:
        activity_data = create_activity_data(None, None, driver.id,
                                             timezone.now(),
                                             IOFOptionsEnum.STARTED, location, None,
                                             driver.customer_id,
                                             driver.module_id)
        activity_data.save()
        # driver_user = User.objects.get(associated_entity=driver).id
        # user_group.append(driver_user)
        admin = User.objects.filter(customer=driver.customer, role_id=1)
        for obj in admin:
            user_group.append(obj.id)

        notification = send_action_notification(None, None, None, driver,
                                                driver.name + " started activity for delivery",
                                                IOFOptionsEnum.NOTIFICATION_DRIVER_WASTE_COLLECTION)
        notification.save()
        save_users_group(notification, user_group)
        return True, "Successfully started activity"
    except:
        traceback.print_exc()
        return False, "Operation failed. Please try again later"
