from django.utils import timezone
from itertools import chain

from customer.utils import entity_sub_type_method
from email_manager.email_util import extended_email_with_title
from hypernet.entity.utils import util_get_devices_dropdown, save_parent_child_assignment, remove_unassigned_trucks, \
    add_assignment, save_job_truck_assignment, save_driver_truck_assignment, \
    create_bins_list, util_get_clients_list, util_get_areas, util_get_unassigned_entities, \
    change_assignment, create_bin_associations, create_contracts_list, \
    update_contract_assignments, disable_violations, save_edit_device_violation_thresholds, save_violations_by_type, \
    util_get_clients_dropdown, single_or_bulk_delete_check_related_objects, get_bins_invoicing, update_customer_device
from hypernet.notifications.utils import send_notification_to_user, send_action_notification, save_users_group
from hypernet.serializers import *
from hypernet.constants import *
from hypernet.enums import OptionsEnum, DeviceTypeAssignmentEnum, IOFOptionsEnum
from hypernet.utils import generic_response, exception_handler, get_default_param
import hypernet.utils as h_utils
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from iof.utils import get_entity
from user.enums import RoleTypeEnum
from user.models import  User
from customer.models import CustomerPreferences
from user.serializers import UserSerializer
from hypernet.enums import DeviceTypeEntityEnum

# ---------------------------------------------------------------------------------------------------------
# TODO Move these wrappers to hypernet views.
from user.utils import reset_user_token_reset


@api_view(['POST'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def add_entity(request):
    
    response_body = {RESPONSE_MESSAGE: TEXT_SUCCESSFUL, RESPONSE_STATUS: HTTP_ERROR_CODE, RESPONSE_DATA: {}}
    http_status = HTTP_ERROR_CODE

    truck = h_utils.get_data_param(request, 'truck', None)
    driver = h_utils.get_data_param(request, 'driver', None)
    type_id = int(h_utils.get_data_param(request, 'type', 0))
    assignment_flag = h_utils.get_data_param(request, 'assignment_flag', None)
    end_datetime = h_utils.get_data_param(request, 'end_datetime', None)
    ter_trucks = h_utils.get_data_param(request, 'trucks_list', None)
    rfid = h_utils.get_data_param(request, 'rfid', None)
    territory_truck = h_utils.get_data_param(request, 'territory', None)
    user = h_utils.get_user_from_request(request, None)
    customer = h_utils.get_customer_from_request(request, None)
    
    if user.role.id != RoleTypeEnum.ADMIN:
        http_status = HTTP_SUCCESS_CODE
        response_body[RESPONSE_MESSAGE] = 'You do not have sufficient privileges to perform this action.'
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
        return generic_response(response_body=response_body, http_status=http_status)
    request.POST._mutable = True
    request.data['status'] = OptionsEnum.ACTIVE
    request.data['customer'] = h_utils.get_customer_from_request(request, None)
    request.data['module'] = h_utils.get_module_from_request(request, None)
    request.data['job_status'] = IOFOptionsEnum.PENDING
    request.data['routine_type'] = OptionsEnum.ROUTINE_TYPE_ONCE
    request.data['modified_by'] = h_utils.get_user_from_request(request,None).id  # h_utils.get_user_from_request(request, None)
    request.data['modified_datetime'] = timezone.now()
    request.POST._mutable = False
    user_group = []

    preference = CustomerPreferences.objects.get(customer_id=customer)
    if rfid:
        rfid = Entity.objects.get(name=rfid, customer_id=customer, status_id = OptionsEnum.ACTIVE, type_id__in=[DeviceTypeEntityEnum.RFID_CARD, DeviceTypeEntityEnum.RFID_TAG])

    if type_id:
        # Truck Serializer
        if (type_id) == DeviceTypeEntityEnum.TRUCK:
            serializer = TruckSerializer(data=request.data, context={'request': request})

        #Job Serializer
        elif (type_id) == DeviceTypeEntityEnum.JOB:
            serializer = JobSerializer(data=request.data, partial=True, context={'request': request})

        #Bin Serializer
        elif (type_id) == DeviceTypeEntityEnum.BIN:
            serializer = BinSerializer(data=request.data, context={'request': request})

        #Territory Serializer
        elif (type_id) == DeviceTypeEntityEnum.TERRITORY:
            serializer = TerritorySerializer(data=request.data, context={'request': request})

        elif (type_id) == DeviceTypeEntityEnum.AREA:
            serializer = TerritorySerializer(data=request.data, context={'request': request})

        #Driver Serializer
        elif (type_id) == DeviceTypeEntityEnum.DRIVER:
            serializer = DriverSerializer(data=request.data, context={'request': request})

        # Maintenance Serializer
        elif (type_id) == DeviceTypeEntityEnum.MAINTENANCE:
            request.POST._mutable = True
            request.data['job_status'] = IOFOptionsEnum.MAINTENANCE_DUE
            request.POST._mutable = False
            serializer = MaintenanceSerializer(data=request.data, context={'request': request})

        #Dumping Site Serializer
        elif (type_id) == DeviceTypeEntityEnum.DUMPING_SITE:
            serializer = DumpingSiteSerializer(data=request.data, context={'request':request})

        elif (type_id) == DeviceTypeEntityEnum.SORTING_FACILITY:
            serializer = SortingFacilitySerializer(data=request.data, context={'request':request})

        elif (type_id) == DeviceTypeEntityEnum.RFID_SCANNER:
            serializer = RfidScannerSerializer(data=request.data, context={'request':request})
        
        elif (type_id) == DeviceTypeEntityEnum.RFID_CARD:
            serializer = RfidCardTagSerializer(data=request.data, context={'request':request})
            
        elif (type_id) == DeviceTypeEntityEnum.RFID_TAG:
            serializer = RfidCardTagSerializer(data=request.data, context={'request': request})
        
        elif (type_id) == DeviceTypeEntityEnum.CONTRACT:
            if request.data.get('skip_size') is not None:
                sub_type = entity_sub_type_method(request.data.get('skip_size'))
                request.POST._mutable = True
                request.data['entity_sub_type'] = sub_type
                request.POST._mutable = False
            serializer = ClientContractSerializer(data=request.data, context={'request':request})
        
        elif (type_id) == DeviceTypeEntityEnum.SUPERVISOR:
            serializer = ClientSupervisorSerializer(data=request.data, context={'request':request})

        if serializer.is_valid():
            entity = serializer.save()
            mod_by = serializer.data.get('modified_by')
            send_notification = True
            if entity.type_id == DeviceTypeEntityEnum.DRIVER:
                if truck:
                    try:
                        save_driver_truck_assignment(request.data.get('customer'),
                                                     request.data.get('module'),
                                                     request.data.get('modified_by'),
                                                     truck, serializer.data['id'],
                                                     end_datetime)
                    except:
                        response_body[RESPONSE_MESSAGE] = "Invalid truck selected\nOr\nit does does not exists in the system."
                        http_status = HTTP_SUCCESS_CODE
                        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                        Entity.objects.filter(id=serializer.data['id']).delete()
                        return generic_response(response_body=response_body, http_status=http_status)
                # RFID assignment logic here
                if rfid:
                    save_parent_child_assignment(child=rfid.id, parent=serializer.data['id'], serializer=serializer,
                                                 type_id=DeviceTypeAssignmentEnum.RFID_CARD_ASSIGMENT)
                    rfid.obd2_compliant = True
                    rfid.save()

                name = serializer.data.get('name', '').split(' ')
                request.POST._mutable = True
                request.data['associated_entity'] = serializer.data['id']
                if name:
                    request.data['first_name'] = name[0]
                if len(name) > 1:
                    request.data['last_name'] = name[1]
                request.data['role'] = RoleTypeEnum.USER
                request.POST._mutable = False
                print(request.data['first_name'])
                if request.data.get('email'):
                    user_serializer = UserSerializer(data=request.data, context={'request': request}, partial=True)
                    if user_serializer.is_valid():
                        user = user_serializer.save()
                        email = user.email
                        add_user = reset_user_token_reset(user_email=email)
                        if add_user:
                            url = add_user.reset_token
                            email_message = EMAIL_INVITATION_MESSAGE
                            extended_email_with_title(title="create_user", to_list=[email], email_words_dict={'{0}':url, '{text}':email_message})
                            notification_type = IOFOptionsEnum.NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_DRIVER

                    else:
                        response_body[RESPONSE_MESSAGE] = h_utils.error_message_serializers(user_serializer.errors)
                        http_status = HTTP_SUCCESS_CODE
                        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                        Entity.objects.filter(id=serializer.data['id']).delete()
                        return generic_response(response_body=response_body, http_status=http_status)

            elif entity.type_id == DeviceTypeEntityEnum.TRUCK:
                if request.data.get('threshold'):
                    save_violations_by_type(entity=entity, threshold_int=request.data.get('threshold'), threshold_str=None)
                update_customer_device(entity, request.data.get('device_name'))
                send_notification = False
                
            elif entity.type_id == DeviceTypeEntityEnum.TERRITORY:
                ter_list = ter_trucks
                territory = entity.id
                if ter_list:
                    for trucks in ter_list:
                        save_parent_child_assignment(child=territory, parent=trucks, serializer=serializer,
                                                     type_id=DeviceTypeAssignmentEnum.TERRITORY_ASSIGNMENT)
                send_notification = False

            elif entity.type_id == DeviceTypeEntityEnum.AREA:
                ter_list = ter_trucks
                area = entity.id
                if ter_list:
                    for bin in ter_list:
                        save_parent_child_assignment(child=area, parent=bin, serializer=serializer,
                                                     type_id=DeviceTypeAssignmentEnum.AREA_ASSIGNMENT)
                send_notification = False

            elif entity.type_id == DeviceTypeEntityEnum.CONTRACT:
                ter_list = ter_trucks
                contract = serializer.data['id']
                area = request.data.get('area')
                save_parent_child_assignment(child=contract, parent=area, serializer=serializer,
                                             type_id=DeviceTypeAssignmentEnum.AREA_CONTRACT_ASSIGNMENT)
                if ter_list:
                    for bin in ter_list:
                        create_bin_associations(contract, bin)
                send_notification = False

            elif entity.type_id == DeviceTypeEntityEnum.RFID_SCANNER:
                if truck:
                    save_parent_child_assignment(child=entity.id, parent=truck, serializer=serializer,
                                                 type_id=DeviceTypeAssignmentEnum.RFID_ASSIGNMENT)
                    # admin = User.objects.filter(customer=preference.customer, role_id=RoleTypeEnum.ADMIN)
                    # for obj in admin:
                    #     user_group.append(obj.id)
                    # notification = send_action_notification(entity.id,
                    #                                         None, None, entity,
                    #                                         "Successfully added RFID Scanner " + str(entity.name),
                    #                                         IOFOptionsEnum.NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_RFID_SCANNER)
                    # notification.save()
                    # save_users_group(notification, user_group)
                    notification_type = IOFOptionsEnum.NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_RFID_SCANNER

            elif entity.type_id == DeviceTypeEntityEnum.MAINTENANCE:
                import datetime
                try:
                    ass_type = DeviceTypeAssignmentEnum.MAINTENANCE_ASSIGNEMENT
                    truck_main = Entity.objects.get(pk=truck)
                    main_pk = Entity.objects.get(pk=serializer.data['id']).id
                    add_assignment(driver_id=main_pk, new_truck=truck_main, log_user=mod_by, assignment_type=ass_type)
                    #For sending maintenance notification:
                    try:
                        assigned_driver = Assignment.objects.get(parent = truck_main,
                                                             child__type = DeviceTypeEntityEnum.DRIVER,
                                                             status = OptionsEnum.ACTIVE).child_id

                        if entity.end_datetime.date() == datetime.date.today():
                            send_notification_to_user(truck_main.id, assigned_driver, entity, [User.objects.get(associated_entity=assigned_driver)],
                                                  "Upcoming maintenance")
                    except:
                        http_status = HTTP_ERROR_CODE
                        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                        pass
                except Exception as e:
                    http_status = HTTP_ERROR_CODE
                    response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
            
            elif entity.type_id == DeviceTypeEntityEnum.RFID_CARD or entity.type_id == DeviceTypeEntityEnum.RFID_TAG:
                response_body[RESPONSE_MESSAGE] = entity.as_rfid_json()

                if entity.type.id == DeviceTypeEntityEnum.RFID_CARD:
                    notification_type = IOFOptionsEnum.NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_RFID_CARD

                if entity.type.id == DeviceTypeEntityEnum.RFID_TAG:
                    notification_type = IOFOptionsEnum.NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_RFID_TAG

            elif entity.type_id == DeviceTypeEntityEnum.BIN:
                if rfid:
                    save_parent_child_assignment(child=rfid.id, parent=entity.id,
                                                 serializer=serializer,
                                                 type_id=DeviceTypeAssignmentEnum.RFID_TAG_ASSIGMENT)
                    rfid.obd2_compliant = True
                    rfid.save()

                    contract_id = h_utils.get_data_param(request, 'contract', None)
                    if contract_id:
                        contract_id = int(contract_id)
                        create_bin_associations(contract_id,entity.id)
                    notification_type = IOFOptionsEnum.NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_BIN
                    
            elif entity.type_id == DeviceTypeEntityEnum.SUPERVISOR:
                
                if rfid:
                    save_parent_child_assignment(child=rfid.id, parent=entity.id,
                                             serializer=serializer,
                                             type_id=DeviceTypeAssignmentEnum.RFID_CARD_ASSIGMENT)
                    rfid.obd2_compliant = True
                    rfid.save()
                contracts = h_utils.get_data_param(request, 'contracts_list', None)
                if contracts:
                    for c in contracts:
                        save_parent_child_assignment(child=entity.id, parent=c,
                                                     serializer=serializer,
                                                     type_id=DeviceTypeAssignmentEnum.SUPERVISOR_CONTRACT_ASSIGNMENT)
                notification_type = IOFOptionsEnum.NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_SUPERVISOR

            if preference.assets_notification and send_notification:
                admin = User.objects.filter(customer=preference.customer, role_id=RoleTypeEnum.ADMIN)
                for obj in admin:
                    user_group.append(obj.id)
                notification = send_action_notification(entity.id,
                                                        None, None, entity,
                                                        "Successfully added "+str(entity.type.name)+": "+ str(entity.name),
                                                        notification_type)
                notification.save()
                save_users_group(notification, user_group)
            
            http_status = HTTP_SUCCESS_CODE
            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        else:
            for errors in serializer.errors:
                if errors == 'non_field_errors':
                    response_body[RESPONSE_MESSAGE] = serializer.errors[errors][0]
                else:
                    response_body[RESPONSE_MESSAGE] = h_utils.error_message_serializers(serializer.errors)
            http_status = HTTP_SUCCESS_CODE
            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
            
            # print(error_list)
    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['PATCH'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def edit_entity(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: {}}
    pk = h_utils.get_data_param(request, 'id', None)
    customer = h_utils.get_customer_from_request(request, None)
    entity_obj = Entity.objects.get(pk=pk, customer=customer)
    type_id = entity_obj.type.id
    new_truck = h_utils.get_data_param(request, 'truck', None)
    new_driver = h_utils.get_data_param(request, 'driver', None)
    ter_trucks = h_utils.get_data_param(request, 'trucks_list', None)
    rfid = h_utils.get_data_param(request, 'rfid', None)
    territory_truck = h_utils.get_data_param(request, 'territory', None)
    user = h_utils.get_user_from_request(request, None)

    if user.role.id != RoleTypeEnum.ADMIN:
        http_status = HTTP_SUCCESS_CODE
        response_body[RESPONSE_MESSAGE] = 'You do not have sufficient privileges to perform this action.'
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
        return generic_response(response_body=response_body, http_status=http_status)
    request.POST._mutable = True
    request.data['status'] = OptionsEnum.ACTIVE
    request.data['customer'] = h_utils.get_customer_from_request(request, None)
    request.data['module'] = h_utils.get_module_from_request(request, None)
    request.data['job_status'] = IOFOptionsEnum.PENDING
    request.data['modified_by'] = h_utils.get_user_from_request(request, None).id
    request.data['modified_datetime'] = timezone.now()
    request.data['user'] = h_utils.get_user_from_request(request, None).id
    request.POST._mutable = False

    if int(type_id) == DeviceTypeEntityEnum.TRUCK:
        update_customer_device(entity_obj, request.data.get('device_name'))
        serializer = TruckSerializer(entity_obj, data=request.data, partial=True, context={'request': request})
    
    elif int(type_id) == DeviceTypeEntityEnum.JOB:
        serializer = JobSerializer(entity_obj, data=request.data, partial=True, context={'request': request})

    elif int(type_id) == DeviceTypeEntityEnum.TERRITORY:
        serializer = TerritorySerializer(entity_obj, data=request.data, partial=True, context={'request': request})

    elif int(type_id) == DeviceTypeEntityEnum.AREA:
        serializer = TerritorySerializer(entity_obj, data=request.data, partial=True, context={'request': request})

    elif int(type_id) == DeviceTypeEntityEnum.BIN:
        serializer = BinSerializer(entity_obj, data=request.data, partial=True, context={'request': request})

    elif int(type_id) == DeviceTypeEntityEnum.DRIVER:
        serializer = DriverSerializer(entity_obj, data=request.data, partial=True, context={'request': request})

    elif int(type_id) == DeviceTypeEntityEnum.MAINTENANCE:
        serializer = MaintenanceSerializer(entity_obj, data=request.data, partial=True, context={'request': request})

    elif int(type_id) == DeviceTypeEntityEnum.RFID_SCANNER:
        serializer = RfidScannerSerializer(entity_obj, data=request.data, partial=True, context={'request': request})

    elif int(type_id) == DeviceTypeEntityEnum.DUMPING_SITE:
        serializer = DumpingSiteSerializer(entity_obj, data=request.data, partial=True, context={'request': request})

    elif int(type_id) == DeviceTypeEntityEnum.SORTING_FACILITY:
        serializer = SortingFacilitySerializer(entity_obj, data=request.data, partial=True, context={'request': request})

    elif int(type_id) == DeviceTypeEntityEnum.CONTRACT:
        serializer = ClientContractSerializer(entity_obj, data=request.data, partial=True, context={'request': request})

    elif int(type_id) == DeviceTypeEntityEnum.SUPERVISOR:
        serializer = ClientSupervisorSerializer(entity_obj, data=request.data, partial=True, context={'request': request})

    http_status = HTTP_SUCCESS_CODE

    if serializer.is_valid():
        serializer.validated_data.get('modified_by')  # Trigger to initiate serializer methods to perform actions appropriately
        entity = serializer.save()
        if pk:
            if entity.type_id == DeviceTypeEntityEnum.DRIVER:
                ass_type = DeviceTypeAssignmentEnum.DRIVER_ASSIGNMENT
                e_assignment = change_assignment(driver_id=pk, truck_id=new_truck, log_user=request.data.get('user'),
                                                 assign_type=ass_type)

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
                                extended_email_with_title(title="create_user", to_list=[email], email_words_dict={'{0}':url, '{text}':email_message})
                    else:
                        response_body[RESPONSE_MESSAGE] = h_utils.error_message_serializers(user_serializer.errors)
                        http_status = HTTP_SUCCESS_CODE
                        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                        return generic_response(response_body=response_body, http_status=http_status)

                if not e_assignment:
                    http_status = HTTP_SUCCESS_CODE
                    response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                    response_body[RESPONSE_MESSAGE] = TEXT_EDITED_SUCCESSFUL
                    return generic_response(response_body=response_body, http_status=http_status)

            elif entity.type_id == DeviceTypeEntityEnum.TRUCK:
                save_violations_by_type(entity=entity, threshold_int=request.data.get('threshold'), threshold_str=None)
                update_customer_device(entity, request.data.get('device_name'))
                # if territory_truck:
                # save_parent_child_assignment(child=int(territory_truck), parent=entity.id, serializer=serializer,
                #                                      type_id=DeviceTypeAssignmentEnum.TERRITORY_ASSIGNMENT)

            elif entity.type_id == DeviceTypeEntityEnum.RFID_SCANNER:
                ass_type = DeviceTypeAssignmentEnum.RFID_ASSIGNMENT
                e_assignment = change_assignment(driver_id=pk, truck_id=new_truck, log_user=request.data.get('user'),
                                                 assign_type=ass_type)

                if not e_assignment:
                    response_body[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: False}
                    http_status = HTTP_SUCCESS_CODE
                    response_body[RESPONSE_STATUS] = STATUS_ERROR
                    return generic_response(response_body=response_body, http_status=http_status)

            elif entity.type_id == DeviceTypeEntityEnum.TERRITORY:
                # ter_list_str = ter_trucks.split(",")
                # ter_list = list(map(int, ter_list_str))
                ter_list = ter_trucks
                territory = int(pk)
                if ter_list:
                    for truck in ter_list:
                        save_parent_child_assignment(child=territory, parent=int(truck), serializer=serializer, type_id=DeviceTypeAssignmentEnum.TERRITORY_ASSIGNMENT)
                remove_unassigned_trucks(ter_id=territory, ter_list=ter_list, type_id=DeviceTypeAssignmentEnum.TERRITORY_ASSIGNMENT, entity_type=DeviceTypeEntityEnum.TRUCK)

            elif entity.type_id == DeviceTypeEntityEnum.AREA:
                # ter_list_str = ter_trucks.split(",")
                # ter_list = list(map(int, ter_list_str))
                ter_list = ter_trucks
                territory = int(pk)
                if ter_list:
                    for truck in ter_list:
                        save_parent_child_assignment(child=territory, parent=int(truck), serializer=serializer, type_id=DeviceTypeAssignmentEnum.AREA_ASSIGNMENT)
                remove_unassigned_trucks(ter_id=territory, ter_list=ter_list, type_id=DeviceTypeAssignmentEnum.AREA_ASSIGNMENT, entity_type=DeviceTypeEntityEnum.BIN)

            elif entity.type_id == DeviceTypeEntityEnum.CONTRACT:
                area = request.data.get('area')
                update_contract_assignments(entity, area)
                
            elif entity.type_id == DeviceTypeEntityEnum.MAINTENANCE:
                ass_type = DeviceTypeAssignmentEnum.MAINTENANCE_ASSIGNEMENT
                change_assignment(driver_id=pk, log_user=request.data.get('user'), truck_id=new_truck, assign_type=ass_type)
            
            elif entity.type_id == DeviceTypeEntityEnum.BIN:
                contract_id = int(h_utils.get_data_param(request, 'contract', 0))
                create_bin_associations(contract_id,entity.id)
            
            elif entity.type_id == DeviceTypeEntityEnum.SUPERVISOR:
                contracts = h_utils.get_data_param(request, 'contracts_list', None)
                if contracts:
                    for c in contracts:
                        save_parent_child_assignment(child=entity.id, parent=c,
                                                     serializer=serializer,
                                                     type_id=DeviceTypeAssignmentEnum.SUPERVISOR_CONTRACT_ASSIGNMENT)
                
            http_status = HTTP_SUCCESS_CODE
            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
            response_body[RESPONSE_MESSAGE] = TEXT_EDITED_SUCCESSFUL

    else:
        response_body[RESPONSE_MESSAGE] = h_utils.error_message_serializers(serializer.errors)
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE

    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def fetch_entity(request):
    customer = h_utils.get_customer_from_request(request, None)
    type_id = h_utils.get_default_param(request, 'type_id', None)
    list = []
    # assignments = Assignment.objects.filter(customer=customer)
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}

    if int(type_id) == DeviceTypeEntityEnum.JOB:
        ent = Entity.objects.filter(customer=customer, type=DeviceTypeEntityEnum.JOB).exclude(
            status=OptionsEnum.DELETED)
        if ent:
            for obj in ent:
                serializer = JobSerializer(obj)
                result = get_entity(serializer.data['id'], customer)
                list.append(result)
                response_body[RESPONSE_DATA] = list
        return generic_response(response_body=response_body, http_status=200)

    if int(type_id) == DeviceTypeEntityEnum.TRUCK:
        ent = Entity.objects.filter(customer=customer, type=DeviceTypeEntityEnum.TRUCK).exclude(
            status=OptionsEnum.DELETED)
        if ent:
            for obj in ent:
                serializer = TruckSerializer(obj)
                result = get_entity(serializer.data['id'], customer)
                list.append(result)
                response_body[RESPONSE_DATA] = list
        return generic_response(response_body=response_body, http_status=200)

    if int(type_id) == DeviceTypeEntityEnum.BIN:
        ent = Entity.objects.filter(customer=customer, type=DeviceTypeEntityEnum.BIN).exclude(
            status=OptionsEnum.DELETED)
        if ent:
            for obj in ent:
                serializer = BinSerializer(obj, context={'request': request})
                result = get_entity(serializer.data['id'], customer)
                list.append(result)
                response_body[RESPONSE_DATA] = list
        return generic_response(response_body=response_body, http_status=200)

    if int(type_id) == DeviceTypeEntityEnum.DRIVER:
        ent = Entity.objects.filter(customer=customer, type=DeviceTypeEntityEnum.DRIVER).exclude(
            status=OptionsEnum.DELETED)
        if ent:
            for obj in ent:
                serializer = BinSerializer(obj, context={'request': request})
                result = get_entity(serializer.data['id'], customer)
                list.append(result)
                response_body[RESPONSE_DATA] = list
        return generic_response(response_body=response_body, http_status=200)

    if int(type_id) == DeviceTypeEntityEnum.TERRITORY:
        ent = Entity.objects.filter(customer=customer, type=DeviceTypeEntityEnum.TERRITORY).exclude(
            status=OptionsEnum.DELETED)
        if ent:
            for obj in ent:
                serializer = BinSerializer(obj, context={'request': request})
                result = get_entity(serializer.data['id'], customer)
                list.append(result)
                response_body[RESPONSE_DATA] = list
        return generic_response(response_body=response_body, http_status=200)


@api_view(['PATCH'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def delete_entity(request):
    import datetime
    status = int(h_utils.get_data_param(request, 'status', None))
    r_truck = h_utils.get_data_param(request, 'truck_id', None)
    r_driver = h_utils.get_data_param(request, 'driver_id', None)
    flag_d = h_utils.get_data_param(request, 'flag', None)
    list_id = h_utils.get_data_param(request, 'id_list', None)
    customer = h_utils.get_customer_from_request(request, None)
    user = h_utils.get_user_from_request(request, None)
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    http_status = HTTP_ERROR_CODE
    
    if user.role.id != RoleTypeEnum.ADMIN:
        response_body[RESPONSE_DATA] = {TEXT_OPERATION_UNSUCCESSFUL: False}
        http_status = HTTP_SUCCESS_CODE
        response_body[RESPONSE_MESSAGE] = 'You do not have sufficient privleges to perform this action.'
        response_body[RESPONSE_STATUS] = STATUS_ERROR
        return generic_response(response_body=response_body, http_status=http_status)
    # TODO Refactoring
    for id in list_id:
        if status in [OptionsEnum.INACTIVE]:
            ent = Entity.objects.get(id=id)
            type_id = int(ent.type_id)
            ent.status_id = status
            ent.description = ""
            ent.save()
            if type_id == DeviceTypeEntityEnum.JOB:
                Assignment.objects.filter(child_id=id, child__type=DeviceTypeEntityEnum.JOB,
                                          customer=customer).update(status_id=status)
            elif type_id == DeviceTypeEntityEnum.TRUCK:
                Assignment.objects.filter(parent_id=id, parent__type=DeviceTypeEntityEnum.TRUCK,
                                          customer=customer).update(status_id=status)
                # Customer Device Status update
                CustomerDevice.objects.filter(pk=Entity.objects.get(pk=id).device_name.id
                                              ).update(assigned=False)

                Entity.objects.filter(pk=id, type_id=DeviceTypeEntityEnum.TRUCK).update(device_name=None,
                                                                                        end_datetime=datetime.datetime.now())
                # if status == OptionsEnum.DELETED:
                #     delete_cascade_entity_assignments(pr_id=id)
                #     ent.delete()

            elif type_id == DeviceTypeEntityEnum.BIN:
                Assignment.objects.filter(parent_id=id, parent__type=DeviceTypeEntityEnum.BIN,
                                          customer=customer).update(status_id=status,
                                                                    end_datetime=datetime.datetime.now())
                # Customer Device Status update
                CustomerDevice.objects.filter(pk=Entity.objects.get(pk=id).device_name.id
                                              ).update(assigned=False)

                Entity.objects.filter(pk=id, type_id=DeviceTypeEntityEnum.BIN).update(device_name=None,
                                                                                      end_datetime=datetime.datetime.now(), obd2_compliant = False)
                # if status == OptionsEnum.DELETED:
                #     delete_cascade_entity_assignments(pr_id=id)

            elif type_id == DeviceTypeEntityEnum.DRIVER:
                job_of_truck = Assignment.objects.filter(parent_id=r_truck,
                                                         child__type=DeviceTypeEntityEnum.JOB,
                                                         customer=customer).values_list('child_id')
                if job_of_truck:  # and flag_d is True:
                    Assignment.objects.filter(child_id=r_driver, parent_id=r_truck,
                                              parent__type=DeviceTypeEntityEnum.TRUCK,
                                              child__type=DeviceTypeEntityEnum.DRIVER,
                                              customer=customer).update(status_id=status,
                                                                        end_datetime=datetime.datetime.now())
                    from .utils import remove_assignments
                    removed = remove_assignments(pr_id=r_truck, ch_id=job_of_truck)
                elif flag_d is False:
                    Assignment.objects.filter(child_id=r_driver, parent_id=r_truck,
                                              parent__type=DeviceTypeEntityEnum.TRUCK,
                                              child__type=DeviceTypeEntityEnum.DRIVER,
                                              customer=customer).update(status_id=status,
                                                                        end_datetime=datetime.datetime.now())

                elif type_id == DeviceTypeEntityEnum.MAINTENANCE:
                    if id:
                        Assignment.objects.filter(child_id=id, child__type=DeviceTypeEntityEnum.MAINTENANCE,
                                                  customer=customer).update(status_id=status)
                    elif list_id:
                        for obj in list_id:
                            Assignment.objects.filter(child_id=obj, child__type=DeviceTypeEntityEnum.MAINTENANCE,
                                                      customer=customer).update(status_id=status,
                                                                                end_datetime=datetime.datetime.now())

                    response_body[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: True}
                    http_status = HTTP_SUCCESS_CODE
                    response_body[RESPONSE_STATUS] = STATUS_OK

        elif int(status) == OptionsEnum.DELETED:
            try:
                ent = Entity.objects.get(pk=int(id))
                try:
                    device = ent.device_name.id
                except:
                    device = None
                if device and ent.type_id == DeviceTypeEntityEnum.TRUCK or ent.type_id == DeviceTypeEntityEnum.BIN:
                    CustomerDevice.objects.filter(pk=device
                                                  ).update(assigned=False)
                ent.delete()
                # print(ent)
            except Exception as e:
                print(str(e))
        response_body[RESPONSE_STATUS] = STATUS_OK
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
        http_status = HTTP_SUCCESS_CODE

    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def check_entity_relations(request):

    import datetime
    list_id = h_utils.get_list_param(request, 'id_list', None)
    user = h_utils.get_user_from_request(request, None)
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: HTTP_ERROR_CODE, RESPONSE_DATA: {}}

    if user.role.id != RoleTypeEnum.ADMIN:
        response_body[RESPONSE_DATA] = {TEXT_OPERATION_UNSUCCESSFUL: False}
        http_status = HTTP_SUCCESS_CODE
        response_body[RESPONSE_MESSAGE] = 'You do not have sufficient privleges to perform this action.'
        response_body[RESPONSE_STATUS] = STATUS_ERROR
        return generic_response(response_body=response_body, http_status=http_status)


    flag = None
    relations = {}

    for id in list_id:
        ent = None
        try:
            ent = Entity.objects.get(id=id)
        except Entity.DoesNotExist:
            try:
                ent = CustomerClients.objects.get(id=id)
            except CustomerClients.DoesNotExist:
                response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                response_body[RESPONSE_MESSAGE] = "The record you're trying delete no longer exists"
                return generic_response(response_body=response_body, http_status=HTTP_SUCCESS_CODE)

        flag, data = single_or_bulk_delete_check_related_objects(ent)
        # relations = {obj._meta.object_name: obj.get_delete_name() for obj in data if obj._meta.object_name != 'Entity'}
        if flag is False:
            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
            response_body[RESPONSE_MESSAGE] = data
            return generic_response(response_body=response_body, http_status=HTTP_SUCCESS_CODE)

        elif flag is True and data is None:
            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
            response_body[RESPONSE_MESSAGE] = None

        elif flag is True and data is not None:
            response_body[RESPONSE_STATUS] = 400
            response_body[RESPONSE_MESSAGE] = data
            return generic_response(response_body=response_body, http_status=HTTP_SUCCESS_CODE)

    return generic_response(response_body=response_body, http_status=HTTP_SUCCESS_CODE)

@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_drivers_list(request):
    customer = h_utils.get_customer_from_request(request, None)
    entity_id = get_default_param(request, 'entity_id', None)
    entities_list = []
    return_list = dict()

    if entity_id:
        try:
            entity = Entity.objects.get(pk=entity_id)
            if entity.type_id == DeviceTypeEntityEnum.TRUCK:
                try:
                    assigned_entity = Assignment.objects.get(customer_id=customer, parent_id=entity_id,
                                                        child__type_id = DeviceTypeEntityEnum.DRIVER,
                                                     status_id=OptionsEnum.ACTIVE)

                    entities_list.append({'id': assigned_entity.child_id,
                                 'label': assigned_entity.child.name})
                    return_list['assigned_flag'] = True
                    return_list['drivers_list'] = entities_list

                except Exception as e:
                    # ass = Assignment.objects.filter(child__type_id=DeviceTypeEntityEnum.DRIVER,
                    #                                 parent__type_id=DeviceTypeEntityEnum.TRUCK,
                    #                                 status_id=OptionsEnum.ACTIVE).values_list('child_id')
                    #
                    # u_drivers = Entity.objects.filter(type_id=DeviceTypeEntityEnum.DRIVER,
                    #                                   customer_id=customer, status_id=OptionsEnum.ACTIVE).exclude(id__in=ass)
                    #
                    # for obj in u_drivers:
                    #     entities_list.append({'id': obj.id, 'label': obj.name})
                    # return_list['drivers_list'] = entities_list
                    return_list['assigned_flag'] = False
                    return_list['drivers_list'] = None

            if entity.type_id == DeviceTypeEntityEnum.DRIVER:
                try:
                    assigned_entity = Assignment.objects.get(customer_id=customer, child_id=entity_id,
                                                             parent__type_id=DeviceTypeEntityEnum.TRUCK,
                                                             status_id=OptionsEnum.ACTIVE)

                    entities_list.append({'id': assigned_entity.parent_id,
                                         'label': assigned_entity.parent.name})
                    return_list['assigned_flag'] = True
                    return_list['truck_list'] = entities_list

                except Exception as e:
                    return_list['assigned_flag'] = False
                    return_list['truck_list'] = None

            if entity.type_id == DeviceTypeEntityEnum.TERRITORY and entity.territory_type_id == IOFOptionsEnum.BLUE:
                try:
                    assigned_entity = Assignment.objects.get(customer_id=customer, child__id=entity_id,
                                                             parent__type_id=DeviceTypeEntityEnum.BIN,
                                                             status_id=OptionsEnum.ACTIVE)

                    entities_list.append({'id': assigned_entity.child_id,
                                         'label': assigned_entity.child.name})
                    return_list['assigned_flag'] = True
                    return_list['drivers_list'] = entities_list

                except Exception as e:
                    return_list['assigned_flag'] = False
                    return_list['drivers_list'] = None

        except:
            generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500)
    return generic_response(h_utils.response_json(True, return_list))


@csrf_exempt
@api_view(['GET'])
@h_utils.verify_request_params(params=['entity'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_entity_type_dropdown(self):
    from .utils import util_get_entity_dropdown
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
    customer_id = h_utils.get_customer_from_request(self, None)
    module_id = h_utils.get_module_from_request(self, None)
    entity = self.query_params.get('entity')
    # bins = get_default_param(self, 'bins', None)
    # Parent is for IOA(Herd's Animals)
    parent = self.query_params.get('parent')

    if int(entity) == DeviceTypeEntityEnum.CLIENT:
        response_body[RESPONSE_DATA] = list(util_get_clients_dropdown(c_id=customer_id))
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE

    elif int(entity) == DeviceTypeEntityEnum.AREA:
        response_body[RESPONSE_DATA] = list(util_get_areas(c_id=customer_id))
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE

    else:
        response_body[RESPONSE_DATA] = list(util_get_entity_dropdown(c_id=customer_id, entity_type=entity, parent=parent, m_id=module_id))
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE

    return generic_response(response_body=response_body, http_status=HTTP_SUCCESS_CODE)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_SUCCESS_CODE))
def get_unassigned_trucks(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
    customer = h_utils.get_customer_from_request(request, None)
    trucks = Entity.objects.filter(customer = customer, type__id = DeviceTypeEntityEnum.TRUCK, status=OptionsEnum.ACTIVE)
    result = []
    for obj in trucks:
        try:
            t = Assignment.objects.get(parent_id=obj.id, customer=customer,
                                       parent__type=DeviceTypeEntityEnum.TRUCK,
                                       child__type=DeviceTypeEntityEnum.DRIVER,
                                       status=OptionsEnum.ACTIVE)
        except:
            result.append({'id': obj.id, 'label': obj.name})
            response_body[RESPONSE_DATA] = result
    return generic_response(response_body=response_body, http_status=HTTP_SUCCESS_CODE)



# TODO REMOVE THIS FUNCTION RE-WRITE IT GENERIC
@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_unassigned_entity_dropdown(request):
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}

    customer = h_utils.get_customer_from_request(request, None)
    form_entity = int(h_utils.get_default_param(request, 'form_entity', 0))
    drop_down_entity = int(h_utils.get_default_param(request, 'drop_down_entity', 0))

    entity = Entity.objects.filter(customer_id=customer, type_id=drop_down_entity, status_id=OptionsEnum.ACTIVE)
    result = None

    if form_entity == DeviceTypeEntityEnum.TRUCK:
        result = util_get_devices_dropdown(c_id=customer, device_type=DeviceTypeEntityEnum.TRUCK, assignment=False)
        # if drop_down_entity == DeviceTypeEntityEnum.CUSTOMER_DEVICE:
        #     result = util_get_devices_dropdown(c_id=customer, device_type=DeviceTypeEntityEnum.TRUCK, assignment=False)

    elif form_entity == DeviceTypeEntityEnum.BIN:
        result = util_get_devices_dropdown(c_id=customer, device_type=DeviceTypeEntityEnum.BIN, assignment=False)

    elif form_entity == DeviceTypeEntityEnum.DRIVER:
        result = util_get_unassigned_entities(c_id=customer, entity=entity, parent_typ=DeviceTypeEntityEnum.TRUCK,
                                              child_typ=DeviceTypeEntityEnum.DRIVER, ass_type=DeviceTypeAssignmentEnum.DRIVER_ASSIGNMENT)

    elif form_entity == DeviceTypeEntityEnum.AREA:
        result = util_get_unassigned_entities(c_id=customer, entity=entity, parent_typ=DeviceTypeEntityEnum.BIN,
                                              child_typ=DeviceTypeEntityEnum.AREA, ass_type=DeviceTypeAssignmentEnum.AREA_ASSIGNMENT)

    elif form_entity == DeviceTypeEntityEnum.RFID_SCANNER:
        result = util_get_unassigned_entities(c_id=customer, entity=entity, parent_typ=DeviceTypeEntityEnum.TRUCK,
                                              child_typ=DeviceTypeEntityEnum.RFID_SCANNER, ass_type=DeviceTypeAssignmentEnum.RFID_ASSIGNMENT)

    response_body[RESPONSE_DATA] = result
    http_status = HTTP_SUCCESS_CODE
    response_body[RESPONSE_STATUS] = STATUS_OK


    return generic_response(response_body=response_body, http_status=http_status)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_unassigned_bins(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    customer = h_utils.get_customer_from_request(request, None)
    trucks = Entity.objects.filter(customer = customer, type_id = DeviceTypeEntityEnum.BIN, status=OptionsEnum.ACTIVE)
    http_status = HTTP_SUCCESS_CODE
    result = []
    for obj in trucks:
        try:
            Assignment.objects.get(parent_id=obj.id, customer=customer,
                                       parent__type=DeviceTypeEntityEnum.BIN,
                                       child__type=DeviceTypeEntityEnum.AREA,
                                       status=OptionsEnum.ACTIVE)
        except:
            result.append({'id': obj.id, 'label': obj.name, 'entity_location':obj.source_latlong})
            response_body[RESPONSE_DATA] = result
            response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    return generic_response(response_body=response_body, http_status=http_status)

@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_contract_bins(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    customer = h_utils.get_customer_from_request(request, None)
    bins = Entity.objects.filter(customer = customer, type_id = DeviceTypeEntityEnum.BIN, status=OptionsEnum.ACTIVE)
    http_status = HTTP_SUCCESS_CODE
    result = []
    for obj in bins:
        try:
            Assignment.objects.get(parent_id=obj.id, customer=customer,
                                       parent__type=DeviceTypeEntityEnum.BIN,
                                       child__type=DeviceTypeEntityEnum.CONTRACT,
                                       status=OptionsEnum.ACTIVE)
        except:
            result.append({'id': obj.id, 'label': obj.name, 'entity_location':obj.source_latlong})
            response_body[RESPONSE_DATA] = result
            response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    return generic_response(response_body=response_body, http_status=http_status)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_contract_bins_clients(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    customer = h_utils.get_customer_from_request(request, None)
    clients = h_utils.get_list_param(request, 'clients', None)
    area = h_utils.get_list_param(request, 'territories', None)
    http_status = HTTP_SUCCESS_CODE
    result = []
    bins = []
    if clients:
        bins = Entity.objects.filter(customer_id=customer, type_id = DeviceTypeEntityEnum.BIN, status=OptionsEnum.ACTIVE, client_id__in=clients)
        if area:
            assigned_bins = Assignment.objects.filter(customer_id=customer, child__id__in=area,
                                                   parent__type=DeviceTypeEntityEnum.BIN,
                                                   status=OptionsEnum.ACTIVE).values_list('parent_id')
            bins = bins.filter(id__in=assigned_bins)
    else:
        bins = Entity.objects.filter(customer_id=customer, type_id=DeviceTypeEntityEnum.BIN, status=OptionsEnum.ACTIVE)

    for obj in bins:
        try:
            Assignment.objects.get(parent_id=obj.id, customer_id=customer,
                                       parent__type=DeviceTypeEntityEnum.BIN,
                                       child__type=DeviceTypeEntityEnum.CONTRACT,
                                       status=OptionsEnum.ACTIVE)
        except:
            result.append({'id': obj.id, 'label': obj.name, 'entity_location':obj.source_latlong})
            response_body[RESPONSE_DATA] = result
            response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    return generic_response(response_body=response_body, http_status=http_status)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_bins_witout_contract(request):
    customer = h_utils.get_customer_from_request(request, None)
    result = []

    bins = Entity.objects.filter(customer_id=customer, type_id=DeviceTypeEntityEnum.BIN, status=OptionsEnum.ACTIVE)
    assigned_bins = Assignment.objects.filter(customer_id=customer, type_id=DeviceTypeAssignmentEnum.CONTRACT_ASSIGNMENT, status_id=OptionsEnum.ACTIVE).values_list('parent_id')
    bins = bins.exclude(id__in=assigned_bins, type_id=DeviceTypeEntityEnum.BIN)
    for obj in bins:
        result.append({'id': obj.id, 'label': obj.name, 'entity_location': obj.source_latlong})
    return generic_response(h_utils.response_json(True, result))

# TODO REMOVE THIS FUNCTION RE-WRITE IT GENERIC
@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_unassigned_trucks_territory(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    customer = h_utils.get_customer_from_request(request, None)
    trucks = Entity.objects.filter(customer=customer, type__id=DeviceTypeEntityEnum.TRUCK, status=OptionsEnum.ACTIVE)
    result = []
    http_status = HTTP_SUCCESS_CODE
    for obj in trucks:
        try:
            t = Assignment.objects.get(parent_id=obj.id, customer=customer,
                                       parent__type=DeviceTypeEntityEnum.TRUCK,
                                       child__type=DeviceTypeEntityEnum.TERRITORY,
                                       status=OptionsEnum.ACTIVE)
        except:
            result.append({'id': obj.id, 'label': obj.name})
            response_body[RESPONSE_DATA] = result
            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
            response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
    return generic_response(response_body=response_body, http_status=http_status)


# ------------------------------------------------------------------------------------------



@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_devices_dropdown(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    http_status = HTTP_SUCCESS_CODE
    cust = h_utils.get_customer_from_request(self, None)
    d_type = h_utils.get_default_param(self, 'type', None)
    response_body[RESPONSE_DATA] = util_get_devices_dropdown(c_id=cust, assignment=False, device_type=d_type)
    response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    return generic_response(response_body=response_body, http_status=http_status)


from django.db.models.functions import Concat
@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def hypernet_search_bar(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    try:
        search_q = self.query_params.get('search')
        customer = h_utils.get_customer_from_request(self, None)
        module_id = h_utils.get_module_from_request(self, None)
        entity = Entity.objects.filter(customer=customer, module_id=int(module_id))
        search_results = entity.filter(). \
                             annotate(results=Concat('name', 'type__name')). \
                             filter(results__icontains=search_q)[:10]
        response_body[RESPONSE_DATA] = list(
            search_results.values('id', title=F('name'), entity_type=F('type__name')))
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    except:
        traceback.print_exc()
    return generic_response(response_body=response_body, http_status=200)


# TODO replacement from IOF
# @csrf_exempt
# @api_view(['GET'])
# @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=403))
# def get_entities_list(request):
#     from .utils import get_entity_brief
#     response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
#     c_id = get_customer_from_request(request, None)
#     t_id = get_default_param(request, 'type_id', None)
#     m_id = h_utils.get_module_from_request(request, None)
#     response_body[RESPONSE_DATA] = get_entity_brief(c_id=c_id, m_id=int(m_id), t_id=int(t_id), e_id=None,
#                                                     context={'request': request})
#     return generic_response(response_body=response_body, http_status=200)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_bins_list(request):
    customer = h_utils.get_customer_from_request(request, None)
    territories = h_utils.get_list_param(request, 'territories', None)
    clients = h_utils.get_list_param(request, 'clients', None)
    contracts = h_utils.get_list_param(request, 'contracts', None)
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: HTTP_ERROR_CODE, RESPONSE_DATA: {}}
    return_list = dict()
    http_status = HTTP_SUCCESS_CODE

    bins = Entity.objects.filter(customer_id=customer, type_id=DeviceTypeEntityEnum.BIN, status_id=OptionsEnum.ACTIVE,
                                 obd2_compliant=True)
    
    if territories:
        try:
            assigned_bins = Assignment.objects.filter(customer=customer, child__id__in=territories,
                                                   parent__type=DeviceTypeEntityEnum.BIN,
                                                   status=OptionsEnum.ACTIVE).values_list('parent_id')

            bins = Entity.objects.filter(pk__in=assigned_bins, type_id=DeviceTypeEntityEnum.BIN, obd2_compliant=True)
        except:
            return generic_response(response_body=response_body, http_status=http_status)

    if clients:
        try:
            bins = bins.filter(client_id__in=clients)
        except:
            response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_UNSUCCESSFUL
            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
            return generic_response(response_body=response_body, http_status=http_status)
    
    if contracts:
        try:
            assigned_bins = Assignment.objects.filter(customer=customer, child__id__in=contracts,
                                                   parent__type=DeviceTypeEntityEnum.BIN,
                                                   status=OptionsEnum.ACTIVE).values_list('parent_id')
            if bins:
                bins = list(chain(bins,
                                         Entity.objects.filter(pk__in=assigned_bins, type_id=DeviceTypeEntityEnum.BIN,
                                                               obd2_compliant=True)))
            else:
                bins = Entity.objects.filter(pk__in=assigned_bins, type_id=DeviceTypeEntityEnum.BIN, obd2_compliant=True)
            
        except:
            return generic_response(response_body=response_body, http_status=http_status)
        
    drivers_list = create_bins_list(bins)
    return_list['bins_list'] = drivers_list
    response_body[RESPONSE_DATA] = return_list
    response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
    response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['POST'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def add_client(request):
    request.POST._mutable = True
    request.data['customer'] = h_utils.get_customer_from_request(request, None)
    request.data['status'] = OptionsEnum.ACTIVE
    request.data['modified_by'] = h_utils.get_user_from_request(request, None).id
    request.POST._mutable = False

    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: HTTP_ERROR_CODE, RESPONSE_DATA: {}}
    http_status = HTTP_ERROR_CODE

    serializer = CustomerClientsSerializer(data=request.data, context={'request': request})

    if serializer.is_valid():
        serializer.save()
        response_body[RESPONSE_MESSAGE] = TEXT_SUCCESSFUL
        http_status = HTTP_SUCCESS_CODE
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    else:
        response_body[RESPONSE_MESSAGE] = h_utils.error_message_serializers(serializer.errors)
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE

        # print(error_list)
    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['PATCH'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def edit_client(request):
    pk = h_utils.get_data_param(request, 'id', 0)

    entity_obj = CustomerClients.objects.get(pk=int(pk))

    request.POST._mutable = True
    request.data['customer'] = h_utils.get_customer_from_request(request, None)
    request.data['modified_by'] = h_utils.get_user_from_request(request, None).id
    request.data['status'] = OptionsEnum.ACTIVE
    request.data['modified_datetime'] = timezone.now()
    request.POST._mutable = False

    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: HTTP_ERROR_CODE, RESPONSE_DATA: {}}
    http_status = HTTP_ERROR_CODE

    serializer = CustomerClientsSerializer(entity_obj, data=request.data, context={'request': request})

    if serializer.is_valid():
        serializer.save()
        response_body[RESPONSE_MESSAGE] = TEXT_EDITED_SUCCESSFUL
        http_status = HTTP_SUCCESS_CODE
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    else:
        response_body[RESPONSE_MESSAGE] = h_utils.error_message_serializers(serializer.errors)
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE

    return generic_response(response_body=response_body, http_status=http_status)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_clients_list(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
    cust = h_utils.get_customer_from_request(self, None)
    http_status = HTTP_SUCCESS_CODE
    if cust:
        response_body[RESPONSE_DATA] = util_get_clients_list(c_id=cust)
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    else:
        response_body[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE

    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['PATCH'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def delete_clients(request):
    list_id = h_utils.get_data_param(request, 'id_list', None)
    status_id = h_utils.get_data_param(request, 'status_id', None)

    # print(list_id)
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: HTTP_ERROR_CODE, RESPONSE_DATA: []}
    http_status = HTTP_ERROR_CODE
    #TODO Refactoring
    for id in list_id:
        if status_id is not None and int(status_id) in [OptionsEnum.INACTIVE]:
            try:
                CustomerClients.objects.filter(pk=id, status_id=OptionsEnum.ACTIVE).update(status_id=OptionsEnum.INACTIVE)
                response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
                response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
                http_status = HTTP_SUCCESS_CODE

            except Exception as e:
                response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_UNSUCCESSFUL + ' ' + str(e)
                http_status = HTTP_ERROR_CODE

        elif status_id is None:
            try:
                CustomerClients.objects.get(id=id).delete()
                response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
                response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
                http_status = HTTP_SUCCESS_CODE
            except Exception as e:
                response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_UNSUCCESSFUL + ' ' + str(e)
                http_status = HTTP_ERROR_CODE
        else:
            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
            response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_UNSUCCESSFUL + ' ' + 'Param Missing bad Request'
            http_status = 400

    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_contracts_listing(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
    http_status = HTTP_SUCCESS_CODE
    customer = h_utils.get_customer_from_request(request, None)
    client = h_utils.get_default_param(request, 'client', None)
    contract = h_utils.get_default_param(request, 'contract', None)

    return_list = dict()
    if client:
        client = int(client)
        try:
            contracts = Entity.objects.filter(client_id=client, type_id=DeviceTypeEntityEnum.CONTRACT, customer_id=customer)
            return_list['contracts_list'] = create_contracts_list(contracts, None)
            response_body[RESPONSE_DATA] = return_list
            response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        except:
            #traceback.print_exc()
            response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_UNSUCCESSFUL
            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
            return generic_response(response_body=response_body, http_status=http_status)

    elif contract:
        contract = int(contract)
        try:
            contract = Entity.objects.get(id=contract, type_id=DeviceTypeEntityEnum.CONTRACT, customer_id=customer)
            return_list['contract_details'] = create_contracts_list(None, contract)
            response_body[RESPONSE_DATA] = return_list
            response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        except:
            response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_UNSUCCESSFUL
            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
            return generic_response(response_body=response_body, http_status=http_status)

    return generic_response(response_body=response_body, http_status=http_status)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_contract_details_dropdown(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
    http_status = HTTP_SUCCESS_CODE
    client = h_utils.get_default_param(request, 'client', None)
    customer = h_utils.get_customer_from_request(request, None)
    if client:
        client = int(client)
        try:
            contracts = Entity.objects.filter(client_id=client, type_id=DeviceTypeEntityEnum.CONTRACT, customer_id=customer)
            response_body[RESPONSE_DATA] = create_contracts_list(contracts, None)
            response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
            
        except:
            # traceback.print_exc()
            response_body[RESPONSE_MESSAGE] = "An error occured. Please try again later."
            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
        
    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_contracts_list(request):
    customer = h_utils.get_customer_from_request(request, None)
    area = h_utils.get_default_param(request, 'area', None)
    client = h_utils.get_default_param(request, 'client', None)
    response_body = {RESPONSE_MESSAGE: TEXT_PARAMS_MISSING, RESPONSE_STATUS: HTTP_ERROR_CODE, RESPONSE_DATA: {}}
    return_list = dict()
    http_status = HTTP_SUCCESS_CODE
    
    contracts = Entity.objects.filter(customer_id=customer, type_id=DeviceTypeEntityEnum.CONTRACT, status_id=OptionsEnum.ACTIVE)
    
    if area:
        try:
            assigned_bins = Assignment.objects.filter(customer_id=customer, parent__id=area,
                                                      child__type_id=DeviceTypeEntityEnum.CONTRACT,
                                                      status_id=OptionsEnum.ACTIVE).values_list('child_id')
            
            contracts = Entity.objects.filter(pk__in=assigned_bins, type_id=DeviceTypeEntityEnum.CONTRACT, status_id=OptionsEnum.ACTIVE)
        except:
            return generic_response(response_body=response_body, http_status=http_status)
    
    if client:
        try:
            contracts = contracts.filter(client_id=client)
        except:
            response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_UNSUCCESSFUL
            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
            return generic_response(response_body=response_body, http_status=http_status)
    return_list['contracts_list'] = create_contracts_list(contracts, None)
    response_body[RESPONSE_DATA] = return_list
    response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
    response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    return generic_response(response_body=response_body, http_status=http_status)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_SUCCESS_CODE))
def invoice_listing_filters(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: {}}
    customer = h_utils.get_customer_from_request(request, None)
    area_list = get_default_param(request, 'area_list', None)
    client_list = get_default_param(request, 'client_list', None)
    contract_list = get_default_param(request, 'contract_list', None)

    client_list = [2589]
    contract_list = [7570]
    area_list = [7569]
    response_body[RESPONSE_DATA] = list(get_bins_invoicing(areas_list=area_list, contracts_list=contract_list, clients_list=client_list, c_id=customer))
    return generic_response(response_body=response_body, http_status=HTTP_SUCCESS_CODE)
