import traceback

from django.contrib.admin.utils import NestedObjects
from django.db.models import F, Count
import datetime

from django.db.models.functions import Concat

from customer.models import Customer, CustomerClients
from hypernet.enums import OptionsEnum, DeviceTypeAssignmentEnum, ModuleEnum, IOFOptionsEnum
from hypernet.models import Assignment, Entity, DeviceType, DeviceViolation, HypernetNotification
from hypernet.models import CustomerDevice
from iof.models import Activity, ActivitySchedule, IofShifts, LogisticAggregations, LogisticsDerived
from hypernet.enums import DeviceTypeEntityEnum
from options.models import Options
from user.models import Module, User


def util_get_devices_dropdown(c_id, device_type, assignment=False):
    q_set = CustomerDevice.objects.filter(customer_id=c_id, status_id=OptionsEnum.ACTIVE,
                                          assigned=assignment, type_id=device_type)
    return list(q_set.values(device_name=F('device_id'), device=F('id')))

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
                    result.append({'id': obj.id, 'name': obj.name, 'entity_location':obj.source_latlong})
            q_set = result

        else:
            q_set = Entity.objects.filter(customer_id=c_id, type_id=int(entity_type),
                                          status_id=OptionsEnum.ACTIVE, module_id=int(m_id)) \
                .values('id', label=F('name'), entity_location=F('source_latlong'),  rec_status = F('status__label')).order_by('id')
    return q_set

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


def util_get_clients_list(c_id):
    return list(CustomerClients.objects.filter(customer_id=c_id).values
                ('id', 'contact_number','email', 'description', 'address' , 'modified_by', 'created_datetime',
                'modified_datetime', 'end_datetime', 'status', 'party_code', status_label=F('status__label'), label=F('name'),
                 modified_by_name=F('modified_by__first_name'), modified_by_email=F('modified_by__email'),))


from django.db.models import Value
def util_get_clients_dropdown(c_id):
    return list(CustomerClients.objects.filter(customer_id=c_id, status_id=OptionsEnum.ACTIVE).
                annotate(label=Concat('party_code', Value(' - ( '), 'name', Value(' )'))).values('id', 'label'))


def util_get_areas(c_id):
    q_set = Entity.objects.filter(customer_id=c_id, type_id=DeviceTypeEntityEnum.AREA, territory__isnull=True)
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


def save_driver_truck_assignment(customer, module, modified_by, truck, driver, end_datetime):
    if truck:
        driver_assignment = Assignment(
            name="Driver Assigned to " + str(Entity.objects.get(id=truck).name),
            child_id=driver,
            parent_id=truck,
            customer_id=customer,
            module_id=module,
            type_id=DeviceTypeAssignmentEnum.DRIVER_ASSIGNMENT,
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
    from hypernet.enums import DeviceTypeEntityEnum, OptionsEnum
    try:
        new_truck = Entity.objects.get(pk=truck_id)
    except:
        delete_driver_ass(int(driver_id))
        new_truck = None

    if new_truck is not None:
        try:
            ass_driver = Assignment.objects.get(child_id=driver_id, status_id=OptionsEnum.ACTIVE,
                                                parent__type_id=DeviceTypeEntityEnum.TRUCK)
            if ass_driver.parent != new_truck:
                ass_driver.status_id = OptionsEnum.INACTIVE
                ass_driver.save()
                add_assignment(driver_id, new_truck, log_user, assign_type)

        except Exception as e:
            print(str(e))
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
        print(str(e))
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
        tru_ter_ass = Assignment.objects.filter(parent__type=entity_type, child_id=ter_id,
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
        print(str(e))


def save_parent_child_assignment(child, parent, serializer, type_id):
    old_ass = None
    try:
        old_ass = Assignment.objects.get(type_id=type_id, child_id=child, status=OptionsEnum.ACTIVE)
        Assignment.objects.get(parent_id=int(parent), child_id=child, status=OptionsEnum.ACTIVE)
    except:
        if old_ass:
            old_ass.status_id = OptionsEnum.INACTIVE
            old_ass.save()

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
        

# def get_entity_brief(c_id, m_id, t_id, context, e_id=None):
#     # Entity Removed in Merge
#     entity_dict = {}
#     entity_list = []
#     if c_id:
#         ent = Entity.objects.filter(customer=c_id, type=t_id).exclude(status=OptionsEnum.DELETED)
#         for obj in ent:
#             if obj.type_id == DeviceTypeEntityEnum.TRUCK:
#                 entity_dict = obj.as_truck_json()
#
#             elif obj.type_id == DeviceTypeEntityEnum.JOB:
#                 entity_dict = obj.as_job_json()
#
#             elif obj.type_id == DeviceTypeEntityEnum.BIN:
#                 entity_dict = obj.as_bin_json()
#
#             elif obj.type_id == DeviceTypeEntityEnum.DRIVER:
#                 from hypernet.serializers import DriverSerializer
#                 driver_data = DriverSerializer(obj, partial=True, context=context)
#                 entity_dict = driver_data.data
#                 try:
#                     truck = Assignment.objects.get(child_id=obj.id, status=OptionsEnum.ACTIVE,
#                                                    parent__type=DeviceTypeEntityEnum.TRUCK)
#                     entity_dict['assigned_truck'] = truck.parent.as_entity_json()
#                 except Exception as e:
#                     entity_dict['assigned_truck'] = None
#             elif obj.type_id == DeviceTypeEntityEnum.TERRITORY:
#                 entity_dict = obj.as_territory_json()
#
#             entity_list.append(entity_dict.copy())
#         return entity_list


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
        print(str(e))
        return False

def util_create_activity(obj, driver, status_id, activity_start_time):
    activity = Activity(
        activity_schedule=obj.activity_schedule,
        actor=driver,
        #user=User.objects.get(id=obj.activity_schedule.modified_by.id),
        activity_status=Options.objects.get(id=status_id),
        created_datetime=datetime.datetime.now(),
        start_datetime=None,
        end_datetime=None,
        action_items = obj.activity_schedule.action_items,
        primary_entity= obj.primary_entity,
        activity_start_time = activity_start_time,
        activity_end_point= obj.activity_end_point,
        activity_check_point= obj.activity_check_point,
        customer = obj.customer,
        module = obj.module,
    )
    return activity

def create_bins_list(bins):
    # bins = bins.prefetch_related('assignment_parent')
    result =[]
    for ass in bins:
        result.append({'id': ass.id,
                             'label': ass.name, 'location':ass.source_latlong})
    return result

def create_contracts_list(contracts, contract=None):
    result =[]
    if contracts:
        for obj in contracts:
            try:
                assigned_area = Assignment.objects.get(child__id=obj.id,
                                                          type_id=DeviceTypeAssignmentEnum.AREA_CONTRACT_ASSIGNMENT,
                                                          status_id=OptionsEnum.ACTIVE).parent
                dic = {'id': obj.id, 'label': obj.name +' - '+assigned_area.name, 'skip_size': obj.weight, 'skip_rate': obj.skip_rate, 'area':assigned_area.name, 'client': obj.client.name}
            except:
                dic = {'id': obj.id, 'label': obj.name+' - '+assigned_area.name, 'skip_size': obj.weight, 'skip_rate': obj.skip_rate,
                               'area': None, 'client': obj.client.name}
            if obj.entity_sub_type:
                dic['skip_type'] = obj.entity_sub_type.label
            else:
                dic['skip_type'] = None
            result.append(dic)
            
    elif contract:
        try:
            assigned_area = Assignment.objects.get(child__id=contract.id,
                                                   parent__type_id=DeviceTypeEntityEnum.AREA,
                                                   status_id=OptionsEnum.ACTIVE).parent
            result = {'id': contract.id, 'label': contract.name, 'skip_size': contract.weight, 'skip_rate': contract.skip_rate,
                           'area': assigned_area.name, 'client': contract.client.name}
        except:
            result = {'id': contract.id, 'label': contract.name, 'skip_size': contract.weight,
                      'skip_rate': contract.skip_rate,
                      'area': None, 'client': contract.client.name}
        if contract.entity_sub_type:
            result['skip_type'] = contract.entity_sub_type.label
        else:
            result['skip_type'] = None
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
                                   type_id=DeviceTypeAssignmentEnum.CONTRACT_ASSIGNMENT,status_id=OptionsEnum.ACTIVE)
            bin_area_ass = Assignment.objects.get(parent_id=bin.id, status_id=OptionsEnum.ACTIVE,
                                   type_id=DeviceTypeAssignmentEnum.AREA_ASSIGNMENT)
            bin_contract_ass.status_id= OptionsEnum.INACTIVE
            bin_area_ass.status_id= OptionsEnum.INACTIVE
            bin_contract_ass.save()
            bin_area_ass.save()
            bin.client = None
            bin.save()
            return True
        except:
            traceback.print_exc()
            return False
    try:
        contract = Entity.objects.get(id=contract_id, type_id=DeviceTypeEntityEnum.CONTRACT, status_id=OptionsEnum.ACTIVE)
    except:
        return False
    bin.client =  contract.client
    bin.weight = contract.weight
    bin.entity_sub_type = contract.entity_sub_type
    bin.save()
    # Create contract to bin assignment
    current_ass = None
    old_ass = None
    try:
        old_ass = Assignment.objects.get(type_id=DeviceTypeAssignmentEnum.CONTRACT_ASSIGNMENT, parent_id=bin.id,
                               status_id=OptionsEnum.ACTIVE)
        current_ass = Assignment.objects.get(child_id= contract_id, parent_id=bin.id, status_id=OptionsEnum.ACTIVE)
    
    except:
        if old_ass:
            if current_ass:
                return True
            else:
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
        
    # Create area to bin assignment
    current_ass = None
    old_ass = None
    try:
        area = Assignment.objects.get(type_id=DeviceTypeAssignmentEnum.AREA_CONTRACT_ASSIGNMENT, child_id=contract.id, status_id=OptionsEnum.ACTIVE).parent
        old_ass = Assignment.objects.get(type_id=DeviceTypeAssignmentEnum.AREA_ASSIGNMENT, parent_id=bin.id, status_id=OptionsEnum.ACTIVE)
        current_ass = Assignment.objects.get(child_id=area.id,parent_id=bin.id,status_id=OptionsEnum.ACTIVE, type_id=DeviceTypeAssignmentEnum.AREA_ASSIGNMENT)
    except:
        if old_ass:
            if current_ass:
                return True
            else:
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
        modified_by_id=bin.modified_by_id,
        )
        bin_area_assignment.save()
    return True


def update_contract_assignments(contract, area_id):
    current_ass = None
    old_ass = None
    try:
        old_ass = Assignment.objects.get(child_id=contract.id, type_id=DeviceTypeAssignmentEnum.AREA_CONTRACT_ASSIGNMENT, status_id=OptionsEnum.ACTIVE)
        current_ass = Assignment.objects.get(child_id=contract.id, parent_id=area_id, type_id=DeviceTypeAssignmentEnum.AREA_CONTRACT_ASSIGNMENT, status_id=OptionsEnum.ACTIVE)
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

def disable_violations(entity, violation_type=None):
    try:
        device_viol = DeviceViolation.objects.get(violation_type_id=violation_type, device_id=entity.id, status_id=OptionsEnum.ACTIVE, enabled=True)

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
                if device_viol.threshold_number != threshold_int or device_viol.threshold_string !=threshold_str:
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
            save_edit_device_violation_thresholds(entity=entity, viol_type=IOFOptionsEnum.SPEED, threshold_int=threshold_int)

        elif entity.speed is False:
            disable_violations(entity, violation_type=IOFOptionsEnum.SPEED)

        if entity.location is True:
            save_edit_device_violation_thresholds(entity=entity, viol_type=IOFOptionsEnum.TERRITORY, threshold_str=threshold_str)

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
        scanner = Assignment.objects.get(parent=ent, type_id=DeviceTypeAssignmentEnum.RFID_ASSIGNMENT, status_id=OptionsEnum.ACTIVE)
        sensor_data = LogisticAggregations.objects.get(device=ent)
        fillups = LogisticsDerived.objects.filter(device=ent)
        violations = HypernetNotification.objects.filter(device=ent)

        if sensor_data or fillups or violations:
            msg = ent.name+" "+" has produced some sensor data and violation notifications"
            inactive_delete = True

        if act_sch or shift or scanner:
            msg_sch = None
            msg_shift= None
            msg_scanner = None
            if act_sch:
                msg_sch = ent.name+" "+" has some ongoing schedules"
            if shift:
                msg_shift = ent.name+" "+" has an ongoing shift"
            if scanner:
                msg_scanner = ent.name+" "+" has an associated scanner"

            msg = msg_scanner+"\n"+ msg_sch +"\n"+ msg_shift
            inactive_delete = False

    elif type_id == DeviceTypeEntityEnum.DRIVER:
        act_sch = ActivitySchedule.objects.filter(actor=ent)
        shift = IofShifts.objects.filter(child=ent, shift_end_time__isnull=True)
        violations = HypernetNotification.objects.filter(device=ent)

        if violations:
            data_msg = ent.name+" "+" has produced some sensor data and violation notifications"
            inactive_delete = True

        if act_sch or shift:
            msg_sch = None
            msg_shift= None
            if act_sch:
                msg_sch = ent.name+" "+" has some ongoing schedules"
            if shift:
                msg_shift = ent.name+" "+" has an ongoing shift"

            msg = msg_sch +"\n"+ msg_shift
            inactive_delete = False

    elif type_id == DeviceTypeEntityEnum.CONTRACT:
        bins = Assignment.objects.filter(child=ent, type_id=DeviceTypeAssignmentEnum.CONTRACT_ASSIGNMENT, status_id=OptionsEnum.ACTIVE)

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
        trucks = Assignment.objects.filter(child=ent, type_id=DeviceTypeAssignmentEnum.TERRITORY_ASSIGNMENT, status_id=OptionsEnum.ACTIVE)
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
            objet = i.pop()
            if objet._meta.object_name == 'Assignment':
                general_data_msg = obj.name+"'s associations will be deleted/marked inactive \n"

            elif objet._meta.object_name == 'ActivitySchedule':
                activity_sch_msg = obj.name+" has an activity schedule and has produced some respective data, so you cannot delete/inactive it \n"

            elif objet._meta.object_name == 'BinCollectionData':
                activity_sch_msg = obj.name+" has an schedule/activity and has produced some respective data, so you cannot delete/inactive it \n"

            elif objet._meta.object_name == 'CustomerDevice':
                general_data_msg += obj.name+"'s association with be " +objet.device_id+" deleted/marked inactive \n"

            if obj._meta.object_name == 'CustomerClients':
                if collect.protected.__len__() > 0:
                    ent_protected = collect.protected.pop()
                    if ent_protected._meta.object_name == 'Entity':
                        client_data_msg = obj.name+" has associations with bins/contracts, you cannot deleted or mark it inactive \n"

    if activity_sch_msg:
        return False, activity_sch_msg
    elif client_data_msg:
        return False, client_data_msg
    else:
        return True, general_data_msg

def mark_related_obj_inactive(obj_id):
    try:
        ent = Entity.objects.get(id=obj_id)
        ent.status_id = OptionsEnum.INACTIVE
    except Entity.DoesNotExist:
        pass

    #PARENT
    try:
        assignments = Assignment.objects.filter(parent_id=obj_id)
        assignments.update(status_id=OptionsEnum.INACTIVE)
    except:
        pass

    #CHILD
    try:
        assignments = Assignment.objects.filter(child_id=obj_id)
        assignments.update(status_id=OptionsEnum.INACTIVE)
    except:
        pass

    #Device Violations
    try:
        device_violations = DeviceViolation.objects.filter(device_id=obj_id)
        device_violations.update(status_id=OptionsEnum.INACTIVE)
    except:
        return True


def get_bins_invoicing(contracts_list, areas_list, clients_list, c_id):
    bins_list = None

    if contracts_list:
        bins = Assignment.objects.filter(child_id__in=contracts_list, type_id=DeviceTypeAssignmentEnum.CONTRACT_ASSIGNMENT,
                                                   parent__type_id=DeviceTypeEntityEnum.BIN).values_list('parent_id')

        bins_list = Entity.objects.filter(id__in=bins)

    if clients_list:
        if contracts_list:
            bins_list = Entity.objects.filter(id__in=bins_list, client_id__in=clients_list, type_id=DeviceTypeEntityEnum.BIN)
        else:
            bins_list = Entity.objects.filter(client_id__in=clients_list, type_id=DeviceTypeEntityEnum.BIN)

    if areas_list:
        contracts = Assignment.objects.filter(parent_id__in=areas_list, type_id=DeviceTypeAssignmentEnum.AREA_CONTRACT_ASSIGNMENT).values_list('child_id', flat=True)

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
        print(bins_list)
        return bins_list.filter(customer_id=c_id).values('id', 'name')
    else:
        return bins_list


def update_customer_device(obj, d_name):
    try:
        device = CustomerDevice.objects.get(pk=obj.device_name.id)
        device.assigned = False
        device.save()
        print('old device: ' + device.device_id)
    except:
        traceback.print_exc()
        pass
    
    try:
        device = CustomerDevice.objects.get(pk=d_name)
        device.assigned = True
        device.save()
        print('device name: ' + device.device_id)
        
        obj.device_name.id = d_name
        obj.save()
        print('name of latest device: ' + obj.device_name.device_id)
    except:
        traceback.print_exc()
        pass
    