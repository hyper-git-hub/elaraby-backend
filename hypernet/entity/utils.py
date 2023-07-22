import traceback
import requests
from django.contrib.admin.utils import NestedObjects
from django.db.models import F, Count
import datetime
from django.db.models.functions import Concat
from django.db.models.signals import post_save
from django.dispatch import receiver

from customer.models import Customer, CustomerClients
from email_manager.email_util import extended_email_with_title
from hypernet.constants import EMAIL_INVITATION_MESSAGE,DEFAULT_TEMP
from hypernet.enums import OptionsEnum, DeviceTypeAssignmentEnum, ModuleEnum, IOFOptionsEnum, FFPOptionsEnum
from hypernet.models import Assignment, Entity, DeviceType, DeviceViolation, HypernetNotification, UserEntityAssignment, \
    EntityDocument
from hypernet.models import CustomerDevice
from hypernet.notifications.utils import send_action_notification, save_users_group
from hypernet.utils import error_message_serializers
from iof.models import Activity, ActivitySchedule, IofShifts, LogisticAggregations, LogisticsDerived, \
    LogisticMaintenance
from hypernet.enums import DeviceTypeEntityEnum
from iof.utils import check_activity_on_truck, check_schedule_on_truck
from options.models import Options
from user.models import Module, User
from user.serializers import UserSerializer
from user.utils import reset_user_token_reset
import uuid
from iop.models import  ReconfigurationTable,ReconfigurationLockMode
from hypernet import constants
# from iop.utils import signal_r_failure



def save_user_device_assignment(dev, user, is_admin=False):
    try:
        print("--------------------------------------------------")
        print(dev)
        u_d_assignment = UserEntityAssignment.objects.get(device=dev, user=user, status_id=OptionsEnum.ACTIVE)
        return True
    except:
        try:
            u_d_assignment = UserEntityAssignment()
            u_d_assignment.customer = dev.customer
            u_d_assignment.module = dev.module
            u_d_assignment.status_id = OptionsEnum.ACTIVE
            u_d_assignment.device = dev
            u_d_assignment.user = user
            u_d_assignment.modified_by = dev.modified_by
            u_d_assignment.type_id = DeviceTypeAssignmentEnum.IOP_DEVICE_USER_ASSIGNMENT
            u_d_assignment.is_admin = is_admin
            u_d_assignment.can_remove=False
            u_d_assignment.save()

            return True
        except:
            traceback.print_exc()
            return False


def save_customer_device(customer, rfid):
    try:
        customer_device = CustomerDevice.objects.get(device_id=rfid)
        flag = 0
        print("Flag == %d" % flag)

        return customer_device, flag

    except CustomerDevice.DoesNotExist:
        try:
            customer_device = CustomerDevice()
            customer_device.type_id = DeviceTypeEntityEnum.IOP_DEVICE
            customer_device.status_id = OptionsEnum.ACTIVE
            customer_device.customer_id = customer
            customer_device.module_id = ModuleEnum.IOP
            customer_device.device_id = rfid
            customer_device.primary_key = str(uuid.uuid4())
            customer_device.connection_string = 'askar-output'
            customer_device.save()
            flag = 1
            print("Flag == %d", flag)

        except:
            traceback.print_exc()
            customer_device.delete()
            customer_device = None
            flag = 2
            print("Flag == %d", flag)


    return customer_device, flag


def util_get_devices_dropdown(c_id, device_type, assignment=False):
    q_set = CustomerDevice.objects.filter(customer_id=c_id, status_id=OptionsEnum.ACTIVE,
                                          assigned=assignment, type_id=device_type)
    return list(q_set.values(device_name=F('device_id'), device=F('id')))


def unassigned_sites_or_zones(c_id, zone, site):
    if zone:
        zones = Assignment.objects.filter(customer_id=c_id, parent__type_id=DeviceTypeEntityEnum.ZONE,
                                          type_id=DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT,
                                          child__entity_sub_type_id=FFPOptionsEnum.ZONE_SUPERVISOR,
                                          status_id=OptionsEnum.ACTIVE)
        assigned_zones = zones.values_list('parent_id', flat=True)

        un_assigned_entity = Entity.objects.filter(customer_id=c_id, type_id=DeviceTypeEntityEnum.ZONE,
                                                   status_id=OptionsEnum.ACTIVE).exclude(pk__in=assigned_zones)
    elif site:
        sites = Assignment.objects.filter(customer_id=c_id, parent__type_id=DeviceTypeEntityEnum.SITE,
                                          type_id=DeviceTypeAssignmentEnum.SITE_EMPLOYEE_ASSIGNMENT,
                                          child__entity_sub_type_id=FFPOptionsEnum.SITE_SUPERVISOR,
                                          status_id=OptionsEnum.ACTIVE)
        assigned_sites = sites.values_list('parent_id', flat=True)

        un_assigned_entity = Entity.objects.filter(customer_id=c_id, type_id=DeviceTypeEntityEnum.SITE,
                                                   status_id=OptionsEnum.ACTIVE).exclude(pk__in=assigned_sites)

    else:
        un_assigned_entity = None

    return un_assigned_entity


def get_drivers_with_rfid_cards(c_id, m_id):
    drivers_list = []
    entity_drivers = Entity.objects.filter(customer_id=c_id, module_id=int(m_id), type_id=DeviceTypeEntityEnum.DRIVER,
                                           status_id=OptionsEnum.ACTIVE).values_list('id', flat=True)
    for driver in entity_drivers:
        try:
            driver_wt_cards = Assignment.objects.get(type_id=DeviceTypeAssignmentEnum.RFID_CARD_ASSIGMENT,
                                                     parent_id=driver, status_id=OptionsEnum.ACTIVE)
            # FIXME: TODO RETURN DRIVERS HAVING RFID CARDS.
        except:
            continue


def util_get_entity_dropdown(c_id, entity_type, m_id, parent=None, bins=None):
    if parent:
        q_set = Assignment.objects.filter(parent_id=parent, status_id=OptionsEnum.ACTIVE, module_id=m_id).values_list(
            'child').values(
            id=F('child__id'),
            label=F('child__name'),
            entity_location=F('child__source_latlong'),
        ).order_by(
            'id')

    else:
        if entity_type == DeviceTypeEntityEnum.label(DeviceTypeEntityEnum.BIN):
            bins = Entity.objects.filter(customer_id=c_id, type_id=DeviceTypeEntityEnum.BIN,
                                         status_id=OptionsEnum.ACTIVE, obd2_compliant=True)
            result = []
            for obj in bins:
                try:
                    Assignment.objects.get(parent_id=obj.id, customer=c_id,
                                           parent__type_id=DeviceTypeEntityEnum.BIN,
                                           child__type_id=DeviceTypeEntityEnum.TERRITORY,
                                           status_id=OptionsEnum.ACTIVE)
                except:
                    result.append({'id': obj.id, 'name': obj.name, 'entity_location': obj.source_latlong})
            q_set = result

        else:
            q_set = Entity.objects.filter(customer_id=c_id, type_id=int(entity_type),
                                          status_id=OptionsEnum.ACTIVE, module_id=int(m_id)) \
                .values('id', label=F('name'), entity_location=F('source_latlong'),
                        rec_status=F('status__label')).order_by('id')
    return q_set


def util_get_truck_without_scanner(c_id, m_id, form_type, dropdown_type):
    try:
        result = None
        if form_type == DeviceTypeEntityEnum.RFID_SCANNER and dropdown_type == DeviceTypeEntityEnum.TRUCK:
            q_set = Assignment.objects.filter(customer_id=c_id, type_id=DeviceTypeAssignmentEnum.RFID_ASSIGNMENT,
                                              status_id=OptionsEnum.ACTIVE, module_id=m_id).values_list('parent_id')
            result = Entity.objects.filter(customer_id=c_id, type_id=dropdown_type,
                                           status_id=OptionsEnum.ACTIVE).exclude(id__in=q_set).values('id', label=F(
                'name')).order_by('id')
        return result
    except:
        traceback.print_exc()


def util_get_unassigned_entities(c_id, entity, parent_typ, child_typ, ass_type):
    result = []
    for obj in entity:
        try:
            Assignment.objects.get(parent_id=obj.id, customer=c_id,
                                   parent__type_id=int(parent_typ),
                                   child__type_id=int(child_typ),
                                   status=OptionsEnum.ACTIVE,
                                   type_id=ass_type)
        except:
            if obj.source_latlong:
                result.append({'id': obj.id, 'label': obj.name, 'entity_location': obj.source_latlong})
            else:
                result.append({'id': obj.id, 'label': obj.name})
    return result


def util_get_unassigned_zones(c_id):
    trucks = Entity.objects.filter(customer=c_id, type__id=DeviceTypeEntityEnum.ZONE, status=OptionsEnum.ACTIVE)
    result = []
    for obj in trucks:
        try:
            t = Assignment.objects.get(child_id=obj.id, customer=c_id,
                                       type_id=DeviceTypeAssignmentEnum.SITE_ZONE_ASSIGNMENT,
                                       status=OptionsEnum.ACTIVE)
        except:
            result.append({'id': obj.id, 'label': obj.name, 'location': obj.source_latlong})
    return result


def util_get_clients_list(c_id, index_a, index_b):
    clients = CustomerClients.objects.filter(customer_id=c_id)
    return_list = []
    for i in range(index_a, index_b):
        try:
            cl = clients[i]
        except:
            return return_list, False
        return_list.append(cl.as_json())
    return return_list, True


from django.db.models import Value


def util_get_clients_dropdown(c_id):
    return list(CustomerClients.objects.filter(customer_id=c_id, status_id=OptionsEnum.ACTIVE).
                annotate(label=Concat('party_code', Value(' - ( '), 'name', Value(' )'))).values('id', 'label'))


def util_get_areas(c_id):
    q_set = Entity.objects.filter(customer_id=c_id, type_id=DeviceTypeEntityEnum.AREA, territory__isnull=True,
                                  status_id=OptionsEnum.ACTIVE)
    return q_set.values('id', label=F('name'))


def remove_assignments(pr_id, ch_id=[]):
    from hypernet.enums import OptionsEnum
    assignment = Assignment.objects.filter(parent_id=pr_id,
                                           child_id__in=ch_id,
                                           status=OptionsEnum.ACTIVE)
    if assignment:
        assignment.update(status=OptionsEnum.INACTIVE)
        return True
    else:
        return False


def save_driver_truck_assignment(customer, module, modified_by, truck, driver, type_enum):
    if truck:
        driver_assignment = Assignment(
            name="Driver Assigned to " + str(Entity.objects.get(id=truck).name),
            child_id=driver,
            parent_id=truck,
            customer_id=customer,
            module_id=module,
            type_id=type_enum,
            status_id=OptionsEnum.ACTIVE,
            modified_by_id=modified_by,
        )
        driver_assignment.save()


def save_job_truck_assignment(customer, module, modified_by, truck, job, end_datetime):
    if truck:
        # TODO Renaming
        job_assignment = Assignment(
            name="Job Assigned to" + str(Entity.objects.get(id=truck).name),
            child=Entity.objects.get(id=job),
            parent=Entity.objects.get(id=truck),
            customer=Customer.objects.get(id=customer),
            module=Module.objects.get(id=module),
            type=DeviceType.objects.get(id=DeviceTypeAssignmentEnum.JOB_ASSIGNMENT),
            status=Options.objects.get(id=OptionsEnum.ACTIVE),
            end_datetime=end_datetime,
            modified_by=User.objects.get(id=modified_by),
        )
        job_assignment.save()


def change_assignment(driver_id, log_user, assign_type, truck_id=None):
    from hypernet.enums import OptionsEnum
    try:
        new_truck = Entity.objects.get(pk=truck_id)
    except:
        delete_driver_ass(int(driver_id))
        new_truck = None

    if new_truck is not None:
        try:
            ass_driver = Assignment.objects.get(child_id=driver_id, status_id=OptionsEnum.ACTIVE,
                                                type_id=assign_type)
            if ass_driver.parent != new_truck:
                ass_driver.status_id = OptionsEnum.INACTIVE
                ass_driver.save()
                add_assignment(driver_id, new_truck, log_user, assign_type)

        except Exception as e:
            traceback.print_exc()
            add_assignment(driver_id, new_truck, log_user, assign_type)
        return True
    return True


def delete_driver_ass(ch_id):
    status = False
    from hypernet.enums import DeviceTypeEntityEnum
    try:
        old_ass_driver = Assignment.objects.get(child_id=ch_id, status=OptionsEnum.ACTIVE,
                                                parent__type=DeviceTypeEntityEnum.TRUCK)
        old_ass_driver.status_id = OptionsEnum.INACTIVE
        old_ass_driver.end_datetime = datetime.datetime.now()
        old_ass_driver.save()
        status = True
    except Exception as e:
        traceback.print_exc()
    return status


def add_assignment(driver_id, new_truck, log_user, assignment_type):
    from hypernet.enums import DeviceTypeAssignmentEnum
    new_assignment = Assignment(
        name=str(Entity.objects.get(pk=driver_id).name) +
             # "Assigned to" + str(Entity.objects.get(pk=new_truck).name),
             " Assigned to" + str(new_truck.name),
        child_id=driver_id,
        parent_id=new_truck.id,
        customer_id=new_truck.customer.id,
        module_id=new_truck.module.id,
        type_id=assignment_type,
        status_id=OptionsEnum.ACTIVE,
        modified_by_id=log_user)
    new_assignment.save()


def util_edit_job(pk, new_truck, serializer, n_driver=None):
    from hypernet.enums import DeviceTypeAssignmentEnum, DeviceTypeEntityEnum, OptionsEnum
    if Entity.objects.get(pk=pk):
        entity_obj = Entity.objects.get(pk=pk, status=OptionsEnum.ACTIVE)
        try:
            ass_truck = Assignment.objects.get(child_id=pk, status=OptionsEnum.ACTIVE,
                                               parent__type=DeviceTypeEntityEnum.TRUCK)
            if ass_truck.parent != Entity.objects.get(pk=new_truck):
                ass_truck.parent = Entity.objects.get(pk=new_truck)
                ass_truck.save()

        except Exception as e:
            job_assignment = Assignment(
                name=str(Entity.objects.get(pk=pk).name) + " Assigned to " +
                     str(Entity.objects.get(pk=new_truck).name),
                child_id=pk,
                parent_id=new_truck,
                customer_id=serializer.data['customer'],
                module_id=serializer.data['module'],
                type_id=DeviceTypeAssignmentEnum.JOB_ASSIGNMENT,
                status_id=OptionsEnum.ACTIVE,
                end_datetime=serializer.data['job_end_datetime'],
                modified_by_id=serializer.data['modified_by'])
            job_assignment.save()

        try:
            Assignment.objects.get(
                child_id=n_driver, parent_id=new_truck, status=OptionsEnum.ACTIVE)

        except Exception as e:
            driver_assignment = Assignment(
                name=str(Entity.objects.get(pk=n_driver).name) + " Assigned to " +
                     str(Entity.objects.get(pk=new_truck).name),
                child_id=n_driver,
                parent_id=new_truck,
                customer_id=serializer.data['customer'],
                module_id=serializer.data['module'],
                type_id=DeviceTypeAssignmentEnum.DRIVER_ASSIGNMENT,
                status_id=OptionsEnum.ACTIVE,
                modified_by_id=serializer.data['modified_by'])
            driver_assignment.save()
    return True


def remove_unassigned_trucks(ter_id, ter_list, type_id, entity_type):
    try:
        tru_ter_ass = Assignment.objects.filter(parent__type_id=entity_type, child_id=ter_id,
                                                type_id=type_id,
                                                status=OptionsEnum.ACTIVE).values_list('parent_id', flat=True)
        # TODO Optimization if needed after review.
        if ter_list:
            for tr in tru_ter_ass:
                if tr not in ter_list:
                    tru_ter_ass.filter(parent_id=tr).update(status_id=OptionsEnum.INACTIVE,
                                                            type_id=type_id)
        else:
            tru_ter_ass.update(status_id=OptionsEnum.INACTIVE)

    except Exception as e:
        traceback.print_exc()


def remove_unassigned_zones(ter_id, ter_list, type_id, entity_type):
    try:
        tru_ter_ass = Assignment.objects.filter(parent__type_id=entity_type, parent_id=ter_id,
                                                type_id=type_id,
                                                status=OptionsEnum.ACTIVE).values_list('child_id', flat=True)
        # TODO Optimization if needed after review.
        if ter_list:
            for tr in tru_ter_ass:
                if tr not in ter_list:
                    tru_ter_ass.filter(child_id=tr).update(status_id=OptionsEnum.INACTIVE,
                                                           type_id=type_id)
        else:
            tru_ter_ass.update(status_id=OptionsEnum.INACTIVE)

    except Exception as e:
        traceback.print_exc()


def save_parent_child_assignment(child, parent, serializer, type_id):
    old_ass = None
    try:
        old_ass = Assignment.objects.get(type_id=type_id, child_id=child, status=OptionsEnum.ACTIVE)
        Assignment.objects.get(parent_id=int(parent), child_id=child, status=OptionsEnum.ACTIVE)
    except:
        if old_ass:
            old_ass.status_id = OptionsEnum.INACTIVE
            old_ass.save()

        if child and parent:
            driver_assignment = Assignment(
                name=str(Entity.objects.get(pk=child)) + " Assigned to "
                     + str(Entity.objects.get(pk=parent).name),
                child_id=child,
                parent_id=parent,
                customer_id=serializer.data['customer'],
                module_id=serializer.data['module'],
                type_id=type_id,
                status_id=OptionsEnum.ACTIVE,
                modified_by_id=serializer.data['modified_by'],
            )
            driver_assignment.save()


def save_many_parent_child_assignment(area_id, bin_id, serializer, type_id):
    # old_ass = None
    try:
        # Assignment.objects.get(type_id=type_id, child_id=bin_id, status=OptionsEnum.ACTIVE)
        Assignment.objects.get(parent_id=int(bin_id), child_id=area_id, status=OptionsEnum.ACTIVE)
    except:
        driver_assignment = Assignment(
            name=str(Entity.objects.get(pk=area_id)) + " Assigned to "
                 + str(Entity.objects.get(pk=bin_id).name),
            child_id=area_id,
            parent_id=bin_id,
            customer_id=serializer.data['customer'],
            module_id=serializer.data['module'],
            type_id=type_id,
            status_id=OptionsEnum.ACTIVE,
            modified_by_id=serializer.data['modified_by'],
        )
        driver_assignment.save()


def delete_cascade_entity_assignments(pr_id=None, ch_id=None):
    try:
        if pr_id:
            Assignment.objects.filter(parent_id=pr_id).delete()
            return Entity.objects.filter(pk=pr_id).delete()
        elif ch_id:
            Assignment.objects.filter(child_id=ch_id).delete()
            return Entity.objects.filter(pk=ch_id).delete()
        else:
            return False
    except Exception as e:
        traceback.print_exc()
        return False


def util_create_activity(obj, driver, status_id, activity_start_time):
    try:
        print(obj.activity_schedule.id,'object is not ')
        activity = Activity.objects.get(activity_schedule_id=obj.activity_schedule.id)
        print( activity.activity_status.id,'activity id',status_id,'status')
        activity.activity_status_id = status_id
        activity.save()
    except:
        activity = Activity(
            activity_schedule=obj.activity_schedule,
            actor=driver,
            # user=User.objects.get(id=obj.activity_schedule.modified_by.id),
            activity_status=Options.objects.get(id=status_id),
            created_datetime=datetime.datetime.now(),
            start_datetime=None,
            end_datetime=None,
            action_items=obj.activity_schedule.action_items,
            primary_entity=obj.primary_entity,
            activity_start_time=activity_start_time,
            activity_end_point=obj.activity_end_point,
            activity_check_point=obj.activity_check_point,
            customer=obj.customer,
            module=obj.module,
        )
        

    return activity


def abornamlity_removal_util_create_activity(obj, driver, status_id, activity_start_time):
    try:
        activity = Activity.objects.get(activity_schedule_id=obj.activity_schedule.id)
        if activity.activity_status.id != status_id:
            activity.activity_status.id = status_id
            activity.save()
        else:
            print("Already same status")
    except:
        activity = Activity(
            activity_schedule=obj.activity_schedule,
            actor=driver,
            # user=User.objects.get(id=obj.activity_schedule.modified_by.id),
            activity_status=Options.objects.get(id=status_id),
            created_datetime=datetime.datetime.now(),
            start_datetime=None,
            end_datetime=None,
            action_items=obj.activity_schedule.action_items,
            primary_entity=obj.primary_entity,
            activity_start_time=activity_start_time,
            activity_end_point=obj.activity_end_point,
            activity_check_point=obj.activity_check_point,
            customer=obj.customer,
            module=obj.module,
        )

    return activity


def create_bins_list(bins):
    # bins = bins.prefetch_related('assignment_parent')
    result = []
    for ass in bins:
        result.append({'id': ass.id,
                       'label': ass.name, 'location': ass.source_latlong,
                       'skip_size': ass.skip_size.id if ass.skip_size else None,
                       'skip_size_label': ass.skip_size.label if ass.skip_size else None})
    return result


def create_contracts_list(contracts, contract=None):
    result = []
    if contracts:
        for obj in contracts:
            try:
                assigned_area = Assignment.objects.get(child__id=obj.id,
                                                       type_id=DeviceTypeAssignmentEnum.AREA_CONTRACT_ASSIGNMENT,
                                                       status_id=OptionsEnum.ACTIVE).parent
                dic = {'id': obj.id, 'label': obj.name + ' - ' + assigned_area.name, 'skip_rate': obj.skip_rate,
                       'area': assigned_area.name, 'location': None, 'client': obj.client.name}
            except:
                dic = {'id': obj.id, 'label': obj.name, 'skip_rate': obj.skip_rate,
                       'area': None, 'location': None, 'client': obj.client.name}
            try:
                assigned_location = Assignment.objects.get(child__id=obj.id,
                                                           type_id=DeviceTypeAssignmentEnum.LOCATION_CONTRACT_ASSIGNMENT,
                                                           status_id=OptionsEnum.ACTIVE).parent
                dic = {'id': obj.id, 'label': obj.name + ' - ' + assigned_area.name + ' - ' + assigned_location.name,
                       'skip_rate': obj.skip_rate,
                       'area': assigned_area.name, 'location': assigned_location.name, 'client': obj.client.name}
            except:
                if assigned_area:
                    pass
                else:
                    dic = {'id': obj.id, 'label': obj.name, 'skip_rate': obj.skip_rate,
                           'area': None, 'location': None, 'client': obj.client.name}
            if obj.entity_sub_type:
                dic['skip_type'] = obj.entity_sub_type.label
            else:
                dic['skip_type'] = None

            if obj.skip_size:
                dic['skip_size'] = obj.skip_size.label
            else:
                dic['skip_size'] = None
            result.append(dic)

    elif contract:
        try:
            assigned_area = Assignment.objects.get(child__id=contract.id,
                                                   parent__type_id=DeviceTypeEntityEnum.AREA,
                                                   status_id=OptionsEnum.ACTIVE).parent
            result = {'id': contract.id, 'label': contract.name, 'skip_rate': contract.skip_rate,
                      'area': assigned_area.name, 'location': None, 'client': contract.client.name}
        except:
            result = {'id': contract.id, 'label': contract.name,
                      'skip_rate': contract.skip_rate,
                      'area': None, 'location': None, 'client': contract.client.name}
        try:
            assigned_location = Assignment.objects.get(child__id=contract.id,
                                                       parent__type_id=DeviceTypeEntityEnum.LOCATION,
                                                       status_id=OptionsEnum.ACTIVE).parent
            result = {'id': contract.id, 'label': contract.name, 'skip_rate': contract.skip_rate,
                      'area': assigned_area.name, 'location': assigned_location.name, 'client': contract.client.name}
        except:
            if assigned_area:
                pass
            else:
                result = {'id': contract.id, 'label': contract.name,
                          'skip_rate': contract.skip_rate,
                          'area': None, 'location': None, 'client': contract.client.name}
        if contract.entity_sub_type:
            result['skip_type'] = contract.entity_sub_type.label
        else:
            result['skip_type'] = None
        if contract.skip_size:
            result['skip_size'] = contract.skip_size.label
        else:
            contract['skip_size'] = None
    return result


def check_rfid_in_system(name, type):
    try:
        Entity.objects.get(name=name, type=type)
        return True
    except:
        return False


def check_rfid_assignment(name, type):
    try:
        Assignment.objects.get(child_name=name, type_id=type, status_id=OptionsEnum.ACTIVE)
        return True
    except:
        return False


def create_bin_associations(contract_id, bin_id):
    area = None
    try:
        bin = Entity.objects.get(id=bin_id, type_id=DeviceTypeEntityEnum.BIN)
    except:
        return False
    if not contract_id:
        try:
            bin_contract_ass = Assignment.objects.get(parent_id=bin.id,
                                                      type_id=DeviceTypeAssignmentEnum.CONTRACT_ASSIGNMENT,
                                                      status_id=OptionsEnum.ACTIVE)
            bin_area_ass = Assignment.objects.get(parent_id=bin.id, status_id=OptionsEnum.ACTIVE,
                                                  type_id=DeviceTypeAssignmentEnum.AREA_ASSIGNMENT)
            bin_contract_ass.status_id = OptionsEnum.INACTIVE
            bin_area_ass.status_id = OptionsEnum.INACTIVE
            bin_contract_ass.save()
            bin_area_ass.save()
            bin.client = None
            bin.save()
            return True
        except:
            traceback.print_exc()
            return False
    try:
        contract = Entity.objects.get(id=contract_id, type_id=DeviceTypeEntityEnum.CONTRACT,
                                      status_id=OptionsEnum.ACTIVE)
    except:
        return False
    bin.client = contract.client
    # Set this to true to mark this contract as assigned to a bin
    contract.volume = True
    contract.save()
    if bin.skip_size != contract.skip_size:
        # Send warning notification to user
        user_group = []
        # driver_user = User.objects.get(associated_entity=shift.child).id
        # user_group.append(driver_user)
        admin = User.objects.filter(customer=bin.customer, role_id=1)
        for obj in admin:
            user_group.append(obj.id)
        notification = send_action_notification(None, None, None,
                                                bin, "Skip size and contract skip size do not match: \n"
                                                     "Bin: " + bin.name + "\n"
                                                                          "Client: " + contract.client.name + "\n"
                                                                                                              "Contract #: " + contract.name + "\n",
                                                IOFOptionsEnum.NOTIFICATION_DRIVER_BIN_PICKUP)

        notification.save()
        save_users_group(notification, user_group)
        pass
    # bin.skip_size = contract.skip_size
    # bin.entity_sub_type = contract.entity_sub_type
    bin.save()
    # Create contract to bin assignment
    current_ass = None
    old_ass = None
    try:
        # An assignment with any contract for the bin
        old_ass = Assignment.objects.get(type_id=DeviceTypeAssignmentEnum.CONTRACT_ASSIGNMENT, parent_id=bin.id,
                                         status_id=OptionsEnum.ACTIVE)
        # Assignment specific to the contract and bin
        current_ass = Assignment.objects.get(child_id=contract_id, parent_id=bin.id, status_id=OptionsEnum.ACTIVE)

    except:
        if old_ass:  # If there exists an active assignment at all
            if current_ass:  # If the assignment is same as before (unchanged)
                pass
            else:  # Mark old assignment as inactive
                old_ass.status_id = OptionsEnum.INACTIVE
                old_ass.save()
                bin_contract_assignment = Assignment(
                    name=contract.name + " Assigned to " + bin.name,
                    child_id=contract.id,
                    parent_id=bin.id,
                    customer_id=bin.customer.id,
                    module_id=ModuleEnum.IOL,
                    type_id=DeviceTypeAssignmentEnum.CONTRACT_ASSIGNMENT,
                    status_id=OptionsEnum.ACTIVE,
                    modified_by_id=bin.modified_by_id,
                )
                bin_contract_assignment.save()
                # If code reaches here then old ass exists but current is diff so create new assignment.
        else:  # No assignment at all, fresh item create assignment
            bin_contract_assignment = Assignment(
                name=contract.name + " Assigned to " + bin.name,
                child_id=contract.id,
                parent_id=bin.id,
                customer_id=bin.customer.id,
                module_id=ModuleEnum.IOL,
                type_id=DeviceTypeAssignmentEnum.CONTRACT_ASSIGNMENT,
                status_id=OptionsEnum.ACTIVE,
                modified_by_id=bin.modified_by_id,
            )
            bin_contract_assignment.save()

    # Create area to bin assignment
    current_ass = None
    old_ass = None
    try:
        area = Assignment.objects.get(type_id=DeviceTypeAssignmentEnum.AREA_CONTRACT_ASSIGNMENT, child_id=contract.id,
                                      status_id=OptionsEnum.ACTIVE).parent
        old_ass = Assignment.objects.get(type_id=DeviceTypeAssignmentEnum.AREA_ASSIGNMENT, parent_id=bin.id,
                                         status_id=OptionsEnum.ACTIVE)
        current_ass = Assignment.objects.get(child_id=area.id, parent_id=bin.id, status_id=OptionsEnum.ACTIVE,
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
                    name=area.name + " Assigned to " + bin.name,
                    child_id=area.id,
                    parent_id=bin.id,
                    customer_id=bin.customer.id,
                    module_id=ModuleEnum.IOL,
                    type_id=DeviceTypeAssignmentEnum.AREA_ASSIGNMENT,
                    status_id=OptionsEnum.ACTIVE,
                    modified_by_id=bin.modified_by_id, )
                bin_area_assignment.save()
        else:  # No assignment at all, fresh item create assignment
            bin_area_assignment = Assignment(
                name=area.name + " Assigned to " + bin.name,
                child_id=area.id,
                parent_id=bin.id,
                customer_id=bin.customer.id,
                module_id=ModuleEnum.IOL,
                type_id=DeviceTypeAssignmentEnum.AREA_ASSIGNMENT,
                status_id=OptionsEnum.ACTIVE,
                modified_by_id=bin.modified_by_id, )
            bin_area_assignment.save()

    # Create location to bin assignment
    current_ass = None
    old_ass = None
    location = None
    try:
        location = Assignment.objects.get(type_id=DeviceTypeAssignmentEnum.LOCATION_CONTRACT_ASSIGNMENT,
                                          child_id=contract.id,
                                          status_id=OptionsEnum.ACTIVE).parent
        old_ass = Assignment.objects.get(type_id=DeviceTypeAssignmentEnum.LOCATION_ASSIGNMENT, parent_id=bin.id,
                                         status_id=OptionsEnum.ACTIVE)
        current_ass = Assignment.objects.get(child_id=location.id, parent_id=bin.id, status_id=OptionsEnum.ACTIVE,
                                             type_id=DeviceTypeAssignmentEnum.LOCATION_ASSIGNMENT)
    except:
        # In case location is not defined for contract & dont do anything if contract location assignment duz not exist
        if location:
            if old_ass:
                if current_ass:
                    pass
                else:
                    # If code reaches here then old ass exists but current is diff so create new assignment.
                    old_ass.status_id = OptionsEnum.INACTIVE
                    old_ass.save()
                    bin_location_assignment = Assignment(
                        name=location.name + " Assigned to " + bin.name,
                        child_id=location.id,
                        parent_id=bin.id,
                        customer_id=bin.customer.id,
                        module_id=ModuleEnum.IOL,
                        type_id=DeviceTypeAssignmentEnum.LOCATION_ASSIGNMENT,
                        status_id=OptionsEnum.ACTIVE,
                        modified_by_id=bin.modified_by_id,
                    )
                    bin_location_assignment.save()
            else:
                # In case location is not defined for contract & dont do anything if contract location assignment duz not exist
                if location:
                    # No assignment at all, fresh item create assignment
                    bin_location_assignment = Assignment(
                        name=location.name + " Assigned to " + bin.name,
                        child_id=location.id,
                        parent_id=bin.id,
                        customer_id=bin.customer.id,
                        module_id=ModuleEnum.IOL,
                        type_id=DeviceTypeAssignmentEnum.LOCATION_ASSIGNMENT,
                        status_id=OptionsEnum.ACTIVE,
                        modified_by_id=bin.modified_by_id,
                    )
                    bin_location_assignment.save()

            return True
        else:
            return False


def update_contract_assignments(contract, area_id):
    current_ass = None
    old_ass = None
    try:
        old_ass = Assignment.objects.get(child_id=contract.id,
                                         type_id=DeviceTypeAssignmentEnum.AREA_CONTRACT_ASSIGNMENT,
                                         status_id=OptionsEnum.ACTIVE)
        current_ass = Assignment.objects.get(child_id=contract.id, parent_id=area_id,
                                             type_id=DeviceTypeAssignmentEnum.AREA_CONTRACT_ASSIGNMENT,
                                             status_id=OptionsEnum.ACTIVE)
    except:
        if old_ass:
            if current_ass:
                return
            else:
                old_ass.status_id = OptionsEnum.INACTIVE
                old_ass.save()
        bin_area_assignment = Assignment(
            name=contract.name + " Assigned to " + Entity.objects.get(id=area_id).name,
            child_id=contract.id,
            parent_id=area_id,
            customer_id=contract.customer.id,
            module_id=ModuleEnum.IOL,
            type_id=DeviceTypeAssignmentEnum.AREA_CONTRACT_ASSIGNMENT,
            status_id=OptionsEnum.ACTIVE,
            modified_by_id=contract.modified_by_id,
        )
        bin_area_assignment.save()


def update_contract_location_assignments(contract, location_id):
    current_ass = None
    old_ass = None
    try:
        old_ass = Assignment.objects.get(child_id=contract.id,
                                         type_id=DeviceTypeAssignmentEnum.LOCATION_CONTRACT_ASSIGNMENT,
                                         status_id=OptionsEnum.ACTIVE)
        current_ass = Assignment.objects.get(child_id=contract.id, parent_id=location_id,
                                             type_id=DeviceTypeAssignmentEnum.LOCATION_CONTRACT_ASSIGNMENT,
                                             status_id=OptionsEnum.ACTIVE)
    except:
        if old_ass:
            if current_ass:
                return
            else:
                old_ass.status_id = OptionsEnum.INACTIVE
                old_ass.save()
        bin_area_assignment = Assignment(
            name=contract.name + " Assigned to " + Entity.objects.get(id=location_id).name,
            child_id=contract.id,
            parent_id=location_id,
            customer_id=contract.customer.id,
            module_id=ModuleEnum.IOL,
            type_id=DeviceTypeAssignmentEnum.LOCATION_CONTRACT_ASSIGNMENT,
            status_id=OptionsEnum.ACTIVE,
            modified_by_id=contract.modified_by_id,
        )
        bin_area_assignment.save()


def disable_violations(entity, violation_type=None):
    try:
        device_viol = DeviceViolation.objects.get(violation_type_id=violation_type, device_id=entity.id,
                                                  status_id=OptionsEnum.ACTIVE, enabled=True)

        if device_viol:
            device_viol.enabled = False
            device_viol.status_id = OptionsEnum.INACTIVE
            device_viol.save()

    except:
        traceback.print_exc()
        return True


def save_edit_device_violation_thresholds(entity, viol_type, threshold_int=None, threshold_str=None):
    if entity:
        try:
            device_viol = DeviceViolation.objects.get(violation_type_id=viol_type, device_id=entity.id,
                                                      status_id=OptionsEnum.ACTIVE)
            if device_viol:
                if device_viol.threshold_number != threshold_int or device_viol.threshold_string != threshold_str:
                    device_viol.threshold_number = threshold_int
                    device_viol.threshold_string = threshold_str
                    device_viol.enabled = True
                    device_viol.violation_type_id = viol_type
                else:
                    pass
        except:
            traceback.print_exc()

            device_violations = DeviceViolation()
            device_violations.customer_id = entity.customer_id
            device_violations.module_id = entity.module_id
            device_violations.status_id = entity.status_id
            device_violations.device_id = entity.id
            device_violations.modified_by_id = entity.modified_by_id
            device_violations.threshold_number = threshold_int
            device_violations.threshold_string = threshold_str
            device_violations.violation_type_id = viol_type
            device_violations.enabled = True
            device_violations.save()


def save_violations_by_type(entity, threshold_int=None, threshold_str=None):
    if entity:
        if entity.speed is True:
            threshold_int = float(threshold_int)
            save_edit_device_violation_thresholds(entity=entity, viol_type=IOFOptionsEnum.SPEED,
                                                  threshold_int=threshold_int)

        elif entity.speed is False:
            disable_violations(entity, violation_type=IOFOptionsEnum.SPEED)

        if entity.location is True:
            save_edit_device_violation_thresholds(entity=entity, viol_type=IOFOptionsEnum.TERRITORY,
                                                  threshold_str=threshold_str)

        elif entity.location is False:
            disable_violations(entity, violation_type=IOFOptionsEnum.TERRITORY)

    return True


def check_entity_associations(ent):
    type_id = ent.type_id
    inactive_delete = True
    msg = None
    if type_id == DeviceTypeEntityEnum.TRUCK:
        act_sch = ActivitySchedule.objects.filter(primary_entity_id=id)
        shift = IofShifts.objects.filter(parent=ent, shift_end_time__isnull=True)
        scanner = Assignment.objects.get(parent=ent, type_id=DeviceTypeAssignmentEnum.RFID_ASSIGNMENT,
                                         status_id=OptionsEnum.ACTIVE)
        sensor_data = LogisticAggregations.objects.get(device=ent)
        fillups = LogisticsDerived.objects.filter(device=ent)
        violations = HypernetNotification.objects.filter(device=ent)

        if sensor_data or fillups or violations:
            msg = ent.name + " " + " has produced some sensor data and violation notifications"
            inactive_delete = True

        if act_sch or shift or scanner:
            msg_sch = None
            msg_shift = None
            msg_scanner = None
            if act_sch:
                msg_sch = ent.name + " " + " has some ongoing schedules"
            if shift:
                msg_shift = ent.name + " " + " has an ongoing shift"
            if scanner:
                msg_scanner = ent.name + " " + " has an associated scanner"

            msg = msg_scanner + "\n" + msg_sch + "\n" + msg_shift
            inactive_delete = False

    elif type_id == DeviceTypeEntityEnum.DRIVER:
        act_sch = ActivitySchedule.objects.filter(actor=ent)
        shift = IofShifts.objects.filter(child=ent, shift_end_time__isnull=True)
        violations = HypernetNotification.objects.filter(device=ent)

        if violations:
            data_msg = ent.name + " " + " has produced some sensor data and violation notifications"
            inactive_delete = True

        if act_sch or shift:
            msg_sch = None
            msg_shift = None
            if act_sch:
                msg_sch = ent.name + " " + " has some ongoing schedules"
            if shift:
                msg_shift = ent.name + " " + " has an ongoing shift"

            msg = msg_sch + "\n" + msg_shift
            inactive_delete = False

    elif type_id == DeviceTypeEntityEnum.CONTRACT:
        bins = Assignment.objects.filter(child=ent, type_id=DeviceTypeAssignmentEnum.CONTRACT_ASSIGNMENT,
                                         status_id=OptionsEnum.ACTIVE)

        if bins:
            msg = ent.name + " " + " has an associated bin"
            inactive_delete = True

    elif type_id == DeviceTypeEntityEnum.DUMPING_SITE:
        act_sch = ActivitySchedule.objects.filter(activity_end_point=ent)

        if act_sch:
            msg = ent.name + " " + " has some ongoing schedules"
            inactive_delete = True

    elif type_id == DeviceTypeEntityEnum.RFID_SCANNER:
        scanner = Assignment.objects.get(child=ent, type_id=DeviceTypeAssignmentEnum.RFID_ASSIGNMENT,
                                         status_id=OptionsEnum.ACTIVE)
        if scanner:
            msg = ent.name + " " + " has an associated truck"
            inactive_delete = True

    elif type_id == DeviceTypeEntityEnum.TERRITORY:
        trucks = Assignment.objects.filter(child=ent, type_id=DeviceTypeAssignmentEnum.TERRITORY_ASSIGNMENT,
                                           status_id=OptionsEnum.ACTIVE)
        if trucks:
            msg = ent.name + " " + " has an associated territory"
            inactive_delete = True

    elif type_id == DeviceTypeEntityEnum.AREA:
        area = Assignment.objects.filter(parent=ent, type_id=DeviceTypeAssignmentEnum.AREA_CONTRACT_ASSIGNMENT,
                                         status_id=OptionsEnum.ACTIVE)

        if area:
            msg = ent.name + " " + " has an associated Contract"
            inactive_delete = True

    elif type_id == DeviceTypeEntityEnum.BIN:
        cont = Assignment.objects.filter(parent=ent, type_id=DeviceTypeAssignmentEnum.AREA_CONTRACT_ASSIGNMENT,
                                         status_id=OptionsEnum.ACTIVE)

        if cont:
            msg = ent.name + " " + " has an associated Contract"
            inactive_delete = True

    else:
        return None, inactive_delete

    return msg, inactive_delete


def single_or_bulk_delete_check_related_objects(obj):
    # general_data_list = []
    # activity_sch_list = []
    general_data_msg = None
    activity_sch_msg = None
    client_data_msg = None

    collect = NestedObjects(using='default')
    collect.collect([obj])

    for i in (list(collect.data.values())):
        if i is not None:
            for item in i:
                if obj._meta.object_name == 'CustomerClients':
                    if collect.protected.__len__() > 0:
                        ent_protected = collect.protected.pop()
                        if ent_protected._meta.object_name == 'Entity':
                            return False, obj.name + " has associations with bins/contracts. You cannot delete or mark it as inactive \n"
                if item._meta.object_name == 'Assignment':
                    if item.status_id == OptionsEnum.ACTIVE:
                        if item.child.type.id == DeviceTypeEntityEnum.CONTRACT and item.parent.type.id == DeviceTypeEntityEnum.AREA:
                            return False, obj.name + " cannot be marked delete/inactive. \n It has valid assignment with contract: " + item.child.name
                        elif item.parent.type.id == DeviceTypeEntityEnum.BIN and item.child.type.id == DeviceTypeEntityEnum.CONTRACT:
                            return False, obj.name + " cannot be marked delete/inactive. \n It has valid assignment with bin: " + item.parent.name
                        elif item.parent.type.id == DeviceTypeEntityEnum.TRUCK and item.child.type.id == DeviceTypeEntityEnum.RFID_SCANNER:
                            check1, msg1 = check_activity_on_truck(item.parent)
                            check2, msg2 = check_schedule_on_truck(item.parent)
                            if check1 or check2:
                                return False, obj.name + " cannot be marked delete/inactive. \n It is associated with Truck: " + item.parent.name + " and has current/upcoming activity/schedule"

                elif item._meta.object_name == 'ActivitySchedule':
                    return False, obj.name + " has an activity schedule and has produced some respective data, so you cannot delete/inactive it \n"

                elif item._meta.object_name == 'ActivityData':
                    return False, obj.name + " has produced some Activity Data. You cannot delete/inactive it \n"

                elif item._meta.object_name == 'BinCollectionData':
                    return False, obj.name + " has an schedule/activity and has produced some respective data. You cannot delete/inactive it \n"

                elif collect.protected.__len__() > 0:
                    ent_protected = collect.protected.pop()
                    if ent_protected._meta.object_name == 'ActivitySchedule':
                        return False, obj.name + " has an activity schedule and has produced some respective data. You cannot delete/inactive it \n"

    try:
        return True, obj.name + "'s associations will be deleted/marked inactive \n"
    except:
        return True, obj.first_name + "'s associations will be deleted/marked inactive \n"
        # if activity_sch_msg:
        #     return False, activity_sch_msg
        # elif client_data_msg:
        #     return False, client_data_msg
        # else:
        #     return True, general_data_msg


def mark_related_obj_inactive(obj_id):
    try:
        ent = Entity.objects.get(id=obj_id)
        ent.status_id = OptionsEnum.INACTIVE
    except Entity.DoesNotExist:
        pass

    # PARENT
    try:
        assignments = Assignment.objects.filter(parent_id=obj_id)
        assignments.update(status_id=OptionsEnum.INACTIVE)
    except:
        pass

    # CHILD
    try:
        assignments = Assignment.objects.filter(child_id=obj_id)
        assignments.update(status_id=OptionsEnum.INACTIVE)
    except:
        pass

    # Device Violations
    try:
        device_violations = DeviceViolation.objects.filter(device_id=obj_id)
        device_violations.update(status_id=OptionsEnum.INACTIVE)
    except:
        return True


def get_bins_invoicing(contracts_list, areas_list, clients_list, c_id):
    bins_list = None

    if contracts_list:
        bins = Assignment.objects.filter(child_id__in=contracts_list,
                                         type_id=DeviceTypeAssignmentEnum.CONTRACT_ASSIGNMENT,
                                         parent__type_id=DeviceTypeEntityEnum.BIN).values_list('parent_id')

        bins_list = Entity.objects.filter(id__in=bins)

    if clients_list:
        if contracts_list:
            bins_list = Entity.objects.filter(id__in=bins_list, client_id__in=clients_list,
                                              type_id=DeviceTypeEntityEnum.BIN)
        else:
            bins_list = Entity.objects.filter(client_id__in=clients_list, type_id=DeviceTypeEntityEnum.BIN)

    if areas_list:
        contracts = Assignment.objects.filter(parent_id__in=areas_list,
                                              type_id=DeviceTypeAssignmentEnum.AREA_CONTRACT_ASSIGNMENT).values_list(
            'child_id', flat=True)

        bins = Assignment.objects.filter(child_id__in=contracts, type_id=DeviceTypeAssignmentEnum.CONTRACT_ASSIGNMENT,
                                         parent__type_id=DeviceTypeEntityEnum.BIN).values_list('parent_id')
        bins_list = Entity.objects.filter(id__in=bins)

        if contracts_list:
            intersect_contracts = [x for x in contracts if x in contracts_list]
            bins = Assignment.objects.filter(child_id__in=intersect_contracts,
                                             type_id=DeviceTypeAssignmentEnum.CONTRACT_ASSIGNMENT,
                                             parent__type_id=DeviceTypeEntityEnum.BIN).values_list('parent_id')
            bins_list = Entity.objects.filter(id__in=bins)
            if clients_list:
                bins_list = Entity.objects.filter(id__in=bins_list, client_id__in=clients_list,
                                                  type_id=DeviceTypeEntityEnum.BIN)
        if clients_list:
            bins_list = Entity.objects.filter(id__in=bins_list, client_id__in=clients_list,
                                              type_id=DeviceTypeEntityEnum.BIN)

    if bins_list:
        return bins_list.filter(customer_id=c_id).values('id', 'name')
    else:
        return bins_list


def update_customer_device(obj, d_name):
    try:
        device = CustomerDevice.objects.get(pk=obj.device_name.id)
        device.assigned = False
        device.save()
    except:
        traceback.print_exc()
        pass

    try:
        device = CustomerDevice.objects.get(pk=d_name)
        device.assigned = True
        device.save()

        obj.device_name.id = d_name
        obj.save()
    except:
        traceback.print_exc()
        pass


def add_associated_user(serializer, request, role, pref_module=1.0):
    name = serializer.data.get('name', '').split(' ')
    request.POST._mutable = True
    request.data['associated_entity'] = serializer.data['id']
    request.data['preferred_module'] = pref_module

    if name:
        request.data['first_name'] = name[0]
    if len(name) > 1:
        request.data['last_name'] = name[1]
    request.data['role'] = role
    request.POST._mutable = False
    if request.data.get('email'):
        user_serializer = UserSerializer(data=request.data, context={'request': request}, partial=True)
        if user_serializer.is_valid():
            user = user_serializer.save()
            email = user.email
            add_user = reset_user_token_reset(user_email=email)
            if add_user:
                url = add_user.reset_token
                email_message = EMAIL_INVITATION_MESSAGE
                extended_email_with_title(title="create_user", subject=None, to_list=[email],
                                          email_words_dict={'{0}': url, '{text}': email_message})
                notification_type = IOFOptionsEnum.NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_DRIVER

                return True, notification_type
        else:
            message = error_message_serializers(user_serializer.errors)
            Entity.objects.filter(id=serializer.data['id']).delete()

            return False, message


def modify_associated_user_details(serializer, pk, request):
    user_obj = User.objects.get(associated_entity_id=pk)
    user_old_email = user_obj.email
    name = serializer.data.get('name', '').split(' ')
    request.POST._mutable = True
    if name:
        request.data['first_name'] = name[0]
    if len(name) > 1:
        request.data['last_name'] = name[1]
    # request.data['password'] = user_obj.password
    request.POST._mutable = False

    if request.data.get('email'):
        user_serializer = UserSerializer(user_obj, data=request.data, context={'request': request}, partial=True)
        if user_serializer.is_valid():
            user_driver = user_serializer.save()
            if user_old_email != request.data.get('email'):
                email = user_driver.email
                add_user = reset_user_token_reset(user_email=email)
                if add_user:
                    url = add_user.reset_token
                    email_message = EMAIL_INVITATION_MESSAGE
                    extended_email_with_title(title="create_user", subject=None, to_list=[email],
                                              email_words_dict={'{0}': url, '{text}': email_message})
            return True, None
        else:
            message = error_message_serializers(user_serializer.errors)
            return False, message


def get_listing_counts(c_id, type_id, client_id):
    if client_id:
        return Entity.objects.filter(customer_id=c_id, client__name=client_id, type_id=type_id).count()
    if type_id == DeviceTypeEntityEnum.AREA or \
                    type_id == DeviceTypeEntityEnum.BIN or \
                    type_id == DeviceTypeEntityEnum.CONTRACT or \
                    type_id == DeviceTypeEntityEnum.DRIVER or \
                    type_id == DeviceTypeEntityEnum.DUMPING_SITE or \
                    type_id == DeviceTypeEntityEnum.RFID_CARD or \
                    type_id == DeviceTypeEntityEnum.RFID_TAG or \
                    type_id == DeviceTypeEntityEnum.RFID_SCANNER or \
                    type_id == DeviceTypeEntityEnum.SUPERVISOR or \
                    type_id == DeviceTypeEntityEnum.TERRITORY or \
                    type_id == DeviceTypeEntityEnum.LOCATION or \
                    type_id == DeviceTypeEntityEnum.TRUCK or \
                    type_id == DeviceTypeEntityEnum.VESSEL:
        return Entity.objects.filter(customer_id=c_id, type_id=type_id).count()
    elif type_id == DeviceTypeEntityEnum.CLIENT:
        return CustomerClients.objects.filter(customer_id=c_id).count()
    elif type_id == DeviceTypeEntityEnum.CUSTOMER_DEVICE:
        return CustomerDevice.objects.filter(customer_id=c_id).count()
    elif type_id == DeviceTypeEntityEnum.MAINTENANCE:
        return LogisticMaintenance.objects.filter(customer_id=c_id).count()


def maintenance_summary_counts(c_id):
    maintenance = LogisticMaintenance.objects.filter(customer_id=c_id)
    result = dict()
    due = 0
    over_due = 0
    completed = 0
    admin_approval = 0
    accepted = 0
    open_inprogress = 0
    waiting_for_parts = 0
    for m in maintenance:
        if m.status_id == IOFOptionsEnum.MAINTENANCE_DUE:
            due += 1
        elif m.status_id == IOFOptionsEnum.MAINTENANCE_OVER_DUE:
            over_due += 1
        elif m.status_id == IOFOptionsEnum.MAINTENANCE_COMPLETED:
            completed += 1
        elif m.status_id == IOFOptionsEnum.MAINTENANCE_APPROVAL:
            admin_approval += 1
        elif m.status_id == IOFOptionsEnum.MAINTENANCE_ACCEPTED:
            accepted += 1
        elif m.status_id == IOFOptionsEnum.MAINTENANCE_OPEN_INPROGRESS:
            open_inprogress += 1
        elif m.status_id == IOFOptionsEnum.MAINTENANCE_WAITING_FOR_PARTS:
            waiting_for_parts += 1

    result['due'] = due
    result['over_due'] = over_due
    result['completed'] = completed
    result['admin_approval'] = admin_approval
    result['accepted'] = accepted
    result['open_inprogress'] = open_inprogress
    result['waiting_for_parts'] = waiting_for_parts

    return result


def util_areas_from_clients(clients, customer):
    if clients:
        result = []
        clients = []

        customer_clients = CustomerClients.objects.filter(id__in=clients)

        print(customer_clients.count())
        if customer_clients.count() >= 1:
            client_bins = Entity.objects.filter(client__in=clients, type_id=DeviceTypeEntityEnum.BIN,
                                                status_id=OptionsEnum.ACTIVE, customer=customer)

            for c in client_bins:
                clients.append(c.id)
            areas = Assignment.objects.filter(parent_id__in=clients,
                                              type_id=DeviceTypeAssignmentEnum.AREA_ASSIGNMENT,
                                              status_id=OptionsEnum.ACTIVE).values('child_id')

            areas = Entity.objects.filter(id__in=areas)

            for a in areas:
                result.append({'id': a.id,
                               'name': a.name})
        else:
            result = None
        return result


def util_contracts_from_clients(clients, customer):
    if clients:
        bins_list = []

        result_list = []
        client_bins = Entity.objects.filter(client__in=clients, type_id=DeviceTypeEntityEnum.BIN,
                                            status_id=OptionsEnum.ACTIVE, customer=customer)

        for c in client_bins:
            bins_list.append(c.id)

        contracts = Assignment.objects.filter(parent_id__in=bins_list,
                                              type_id=DeviceTypeAssignmentEnum.CONTRACT_ASSIGNMENT,
                                              status_id=OptionsEnum.ACTIVE).values('child_id')

        ent_contracts = Entity.objects.filter(id__in=contracts)

        for e in ent_contracts:
            result_list.append({'id': e.id, 'name': e.name})
        return result_list


def util_get_area_from_contract(contracts, customer):
    if contracts:
        result = []
        area = Assignment.objects.filter(child_id__in=contracts,
                                         type_id=DeviceTypeAssignmentEnum.AREA_CONTRACT_ASSIGNMENT,
                                         status_id=OptionsEnum.ACTIVE, customer=customer).values('parent_id')

        areas_ent = Entity.objects.filter(id__in=area)

        for a in areas_ent:
            result.append({'id': a.id, 'name': a.name})
        return result


def patch_documents_to_contract(contract, request):
    files = request.FILES.getlist('files')
    # Delete all relationships cause they will be recreated
    EntityDocument.objects.filter(entity=contract).delete()
    for f in files:
        b = EntityDocument()
        filename = 'documents/' + f.name
        import os
        from django.conf import settings
        file_to_check = os.path.join(settings.BASE_DIR, 'media/documents/' + f.name).replace(' ', '_')
        print('filename: ' + filename)
        print('file to check: ' + file_to_check)
        try:
            # if it exists in the system

            if b.file.storage.exists(file_to_check):
                # File exists/ and we want the relationship (Make it!)
                EntityDocument.objects.create(entity=contract, file=filename.replace(' ', '_'))
                print('Found the file should make relation only')
            else:
                # File does not exist. Lets put it in the system and on our server.
                EntityDocument.objects.create(entity=contract, file=f)
                print('No file found, new file, save file also')
        except:
            traceback.print_exc()
            return None


def assign_territory_to_dump(obj, req):
    try:
        # If i can get it dont do anything just let is go...
        Assignment.objects.get(child=obj, parent_id=req.data.get('territory'),
                               type=DeviceTypeAssignmentEnum.DUMP_ASSIGNMENT)
    except:
        # uh oh, dint get the assignment better make one now
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


@receiver(post_save, sender=Entity)
def intercept_entity(sender, instance, **kwargs):
    from django.core.cache import cache
    if instance.type_id in [DeviceTypeEntityEnum.BIN, DeviceTypeEntityEnum.CONTRACT]:
        cache.delete(instance.id)


@receiver(post_save, sender=Assignment)
def intercept_assignments(sender, instance, **kwargs):
    from django.core.cache import cache
    if instance.child.type_id in [DeviceTypeEntityEnum.BIN, DeviceTypeEntityEnum.CONTRACT]:
        cache.delete(instance.child.id)
    elif instance.parent.type_id in [DeviceTypeEntityEnum.BIN, DeviceTypeEntityEnum.CONTRACT]:
        cache.delete(instance.parent.id)


from random import randrange
from datetime import timedelta


def random_date(start, end):
    """
    This function will return a random datetime between two datetime
    objects.
    """
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = randrange(int_delta)
    return start + timedelta(seconds=random_second)


def change_device_is_enabled(obj, status: bool):
    try:

        if (obj == True):
            Entity.is_enabled = False
        else:
            Entity.is_enabled = True

        # device = CustomerDevice.objects.get(pk=obj.device_name.id)
        # device.assigned = False
        Entity.save()
    except:
        traceback.print_exc()
        pass

def retry_mechanism_signal_shs_failure(signal_r_response, device, temperature,shs):
    try:
        print('INSIDE SIGNALR FAILURE EXCEPTION !!!!  ', device)
        row_to_update = ReconfigurationTable.objects.get(device=device.device)
        row_to_update.failure_code = signal_r_response.status_code
        row_to_update.temperature_set = temperature
        row_to_update.shs=shs
        row_to_update.datetime = datetime.now()
        print("Updating Reconfiguration table")
        row_to_update.save()
        print("Updated RECONFIGURATION TABLE !!!!")
    except Exception as e:
        print("INSIDE EXCEPTION in retry mechanism signalr failure")
        traceback.print_exc()
        
def retry_mechanism_signal_clm_mode_device(entity_obj,lock_mode):
    try:
        device_id=entity_obj.device_name.device_id
        print(device_id)
        url = 'https://IoTHWLabs.azure-devices.net/twins/{}/methods?api-version=2018-06-30'.format(device_id)

        print("URL : ", url)
        res = requests.post(url=url,
                        json={'methodName': 'slm',
                                'payload': {'l': '{}'.format(str(lock_mode)), },
                                'responseTimeoutInSeconds': 30},
                        headers={
                            'Authorization': 'SharedAccessSignature sr=IoTHWLabs.azure-devices.net&sig=5EeO2kvTkr0OgO8tS9OKFT9%2Bbam%2B8MIyABNYXZqKpwg%3D&se=1721152990&skn=iothubowner'}

                        )
        print("RESPONSE CODE FROM SIGNALR HIT for LOck Mode: ", res)
        signal_r_failure_lock_mode(res,entity_obj,lock_mode)
      
    except Exception as e:
        print(e)
        
def retry_mechanism_signal_shs_mode_device(entity_obj,standby_id):
    try:
        device_id=entity_obj.device_name.device_id
        print(device_id)
        if standby_id ==1:
            
            
            shs=1 #this is for on
            url = 'https://IoTHWLabs.azure-devices.net/twins/{}/methods?api-version=2018-06-30'.format(device_id)

            print("URL : ", url)
            res = requests.post(url=url,
                            json={'methodName': 'shs',
                                    'payload': {'s': '{}'.format(shs), },
                                    'responseTimeoutInSeconds': 30},
                            headers={
                                'Authorization': 'SharedAccessSignature sr=IoTHWLabs.azure-devices.net&sig=5EeO2kvTkr0OgO8tS9OKFT9%2Bbam%2B8MIyABNYXZqKpwg%3D&se=1721152990&skn=iothubowner'}

                            )
            print("RESPONSE CODE FROM SIGNALR HIT: ", res)
            signal_shs_failure(res,entity_obj,constants.DEFAULT_TEMP,shs)
        
        elif standby_id==2:
            shs=2 #this is standby
            url = 'https://IoTHWLabs.azure-devices.net/twins/{}/methods?api-version=2018-06-30'.format(device_id)

            print("URL : ", url)
            res = requests.post(url=url,
                            json={'methodName': 'shs',
                                    'payload': {'s': '{}'.format(shs), },
                                    'responseTimeoutInSeconds': 30},
                            headers={
                                'Authorization': 'SharedAccessSignature sr=IoTHWLabs.azure-devices.net&sig=5EeO2kvTkr0OgO8tS9OKFT9%2Bbam%2B8MIyABNYXZqKpwg%3D&se=1721152990&skn=iothubowner'}

                            )
            print("RESPONSE CODE FROM SIGNALR HIT: ", res)
            signal_shs_failure(res,entity_obj,constants.DEFAULT_TEMP,shs)
        
        else:
            shs=3 #this is off
            url = 'https://IoTHWLabs.azure-devices.net/twins/{}/methods?api-version=2018-06-30'.format(device_id)

            print("URL : ", url)
            res = requests.post(url=url,
                            json={'methodName': 'shs',
                                    'payload': {'s': '{}'.format(shs), },
                                    'responseTimeoutInSeconds': 30},
                            headers={
                                'Authorization': 'SharedAccessSignature sr=IoTHWLabs.azure-devices.net&sig=5EeO2kvTkr0OgO8tS9OKFT9%2Bbam%2B8MIyABNYXZqKpwg%3D&se=1721152990&skn=iothubowner'}

                            )
            print("RESPONSE CODE FROM SIGNALR HIT: ", res)
            signal_shs_failure(res,entity_obj,constants.DEFAULT_TEMP,shs)
    except Exception as e:
        print(e)
def signal_shs_failure(signal_r_response, device,temperature, shs):
    try:
        print('device in try cash   ', device)
        row_to_update = ReconfigurationTable.objects.get(device=device)
        row_to_update.failure_code = signal_r_response.status_code
        row_to_update.temperature_set = temperature
        row_to_update.shs=shs
        row_to_update.datetime =  datetime.datetime.now()
        print("Updating Reconfiguration table")
        row_to_update.save()
        print("Updated RECONFIGURATION TABLE !!!!")
    except Exception as e:
        print("ReconfigurationTable Execption:      ", e)
        row_to_save = ReconfigurationTable(device=device, temperature_set=temperature, failure_code=signal_r_response.status_code,shs=shs)
        row_to_save.save()

def change_standby_mode_device(entity_obj,standby_id):
    try:
        device_id=entity_obj.device_name.device_id
        print(device_id)
        if standby_id ==1:
            
            
            shs=3 #this is for on
            url = 'https://IoTHWLabs.azure-devices.net/twins/{}/methods?api-version=2018-06-30'.format(device_id)

            print("URL : ", url)
            res = requests.post(url=url,
                            json={'methodName': 'shs',
                                    'payload': {'s': '{}'.format(shs), },
                                    'responseTimeoutInSeconds': 30},
                            headers={
                                'Authorization': 'SharedAccessSignature sr=IoTHWLabs.azure-devices.net&sig=5EeO2kvTkr0OgO8tS9OKFT9%2Bbam%2B8MIyABNYXZqKpwg%3D&se=1721152990&skn=iothubowner'}

                            )
            print("RESPONSE CODE FROM SIGNALR HIT: ", res)
            signal_shs_failure(res,entity_obj,constants.DEFAULT_TEMP,shs)
        
        elif standby_id==2:
            shs=1 #this for off
            url = 'https://IoTHWLabs.azure-devices.net/twins/{}/methods?api-version=2018-06-30'.format(device_id)

            print("URL : ", url)
            res = requests.post(url=url,
                            json={'methodName': 'shs',
                                    'payload': {'s': '{}'.format(shs), },
                                    'responseTimeoutInSeconds': 30},
                            headers={
                                'Authorization': 'SharedAccessSignature sr=IoTHWLabs.azure-devices.net&sig=5EeO2kvTkr0OgO8tS9OKFT9%2Bbam%2B8MIyABNYXZqKpwg%3D&se=1721152990&skn=iothubowner'}

                            )
            print("RESPONSE CODE FROM SIGNALR HIT: ", res)
            signal_shs_failure(res,entity_obj,constants.DEFAULT_TEMP,shs)
        
        else:
            shs=2 #this is standby
            url = 'https://IoTHWLabs.azure-devices.net/twins/{}/methods?api-version=2018-06-30'.format(device_id)

            print("URL : ", url)
            res = requests.post(url=url,
                            json={'methodName': 'shs',
                                    'payload': {'s': '{}'.format(shs), },
                                    'responseTimeoutInSeconds': 30},
                            headers={
                                'Authorization': 'SharedAccessSignature sr=IoTHWLabs.azure-devices.net&sig=5EeO2kvTkr0OgO8tS9OKFT9%2Bbam%2B8MIyABNYXZqKpwg%3D&se=1721152990&skn=iothubowner'}

                            )
            print("RESPONSE CODE FROM SIGNALR HIT: ", res)
            signal_shs_failure(res,entity_obj,constants.DEFAULT_TEMP,shs)
    except Exception as e:
        print(e)
def signal_r_failure(signal_r_response, device, temperature):
    try:
        print('device in try cash   ', device)
        row_to_update = ReconfigurationTable.objects.get(device=device)
        row_to_update.failure_code = signal_r_response.status_code
        row_to_update.temperature_set = temperature
        row_to_update.datetime =  datetime.datetime.now()
        print("Updating Reconfiguration table")
        row_to_update.save()
        print("Updated RECONFIGURATION TABLE !!!!")
    except Exception as e:
        print("ReconfigurationTable Execption:      ", e)
        row_to_save = ReconfigurationTable(device=device, temperature_set=temperature, failure_code=signal_r_response.status_code)
        row_to_save.save()
        
def signal_r_failure_lock_mode(signal_r_response, device, lock_mode):
    try:
        print('device in try lock mode   ', device)
        row_to_update = ReconfigurationLockMode.objects.get(device=device)
        row_to_update.failure_code = signal_r_response.status_code
        row_to_update.datetime =  datetime.datetime.now()
        row_to_update.lock_mode=  lock_mode
        print("Updating ReconfigurationLockMode table")
        row_to_update.save()
        print("Updated ReconfigurationLockMode TABLE !!!!")
    except Exception as e:
        print("ReconfigurationLockMode Execption:      ", e)
        row_to_save = ReconfigurationLockMode(device=device, lock_mode=lock_mode, failure_code=signal_r_response.status_code)
        row_to_save.save()


def set_device_temperature_to_idle(ent, temp):  # util for setting stt of device to desired temperature

    try:
        print('ent device:  ', ent.device_name.device_id)
        url = 'https://IoTHWLabs.azure-devices.net/twins/{}/methods?api-version=2018-06-30'.format(ent.device_name.device_id)

        print("URL : ", url)
        res = requests.post(url=url,
                            json={'methodName': 'stt', 'payload': {'t': '{}'.format(temp),
                                                                    },
                                'responseTimeoutInSeconds': 30},
                            headers={
                                'Authorization': 'SharedAccessSignature sr=IoTHWLabs.azure-devices.net&sig=5EeO2kvTkr0OgO8tS9OKFT9%2Bbam%2B8MIyABNYXZqKpwg%3D&se=1721152990&skn=iothubowner'}

                            )
        print("RESPONSE CODE FROM SIGNALR HIT: ", res.status_code)
        if res.status_code.startswith("20"):
            print("Success set_device_temperature_to_idle")
        else:
            signal_r_failure(res, ent, temp)
            print("BELOW SIGNALR FAILURE CALL AT THE END - set_device_temperature_to_idle")
        return res.status_code
        
    except Exception as e:
        print(e)

def set_device_lock_mode(ent, lock_mode):  # util for setting stt of device to desired temperature

    try:
        print(str(lock_mode),'jasdjasdjasjdnasjdnjasndjsjdnajsndjasndjnasjdnasjdnjasndjasnjdnasj')
        print('ent device:  ', ent.device_name.device_id)
        url = 'https://IoTHWLabs.azure-devices.net/twins/{}/methods?api-version=2018-06-30'.format(ent.device_name.device_id)

        print("URL : ", url)
        res = requests.post(url=url,
                            json={'methodName': 'slm', 'payload': {'l': '{}'.format(str(lock_mode)),
                                                                    },
                                'responseTimeoutInSeconds': 30},
                            headers={
                                'Authorization': 'SharedAccessSignature sr=IoTHWLabs.azure-devices.net&sig=5EeO2kvTkr0OgO8tS9OKFT9%2Bbam%2B8MIyABNYXZqKpwg%3D&se=1721152990&skn=iothubowner'}

                            )
        print("RESPONSE CODE FROM SIGNALR HIT for set lock mode: ", res.status_code)
        signal_r_failure_lock_mode(res,ent,lock_mode)
        return res.status_code
        
    except Exception as e:
        print(e)