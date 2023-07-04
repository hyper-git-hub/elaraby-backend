import datetime as dt
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
import hypernet.utils as h_utils
from hypernet.utils import generic_response, get_user_from_request, get_default_param, \
    verify_request_params, get_customer_from_request, get_module_from_request
from ioa.utils import *
from django.utils import timezone
from hypernet.enums import *
from random import uniform
import traceback
from dateutil.parser import parse
import random
from hypernet.utils import get_month_from_str

@csrf_exempt
@api_view(['GET'])
# @verify_request_params(params=["customer"])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_alerts_count(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    user = get_user_from_request(request, None)
    # c_id = get_default_param(request, "customer", None)
    c_id = get_customer_from_request(request, None)
    animal = get_default_param(request, "animal", None)
    time = dt.date.today() - timedelta(days=float(get_default_param(request, "days", LAST_WEEK)))
    response_body[RESPONSE_DATA] = get_alerts(c_id=c_id, days=time, a_id=animal)
    # response_body[RESPONSE_DATA]['User'] = str(user)
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_recent_alerts_pi(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    time = dt.date.today() - timedelta(days=float(self.query_params.get("days", LAST_WEEK)))
    # q_customer_id = self.query_params["customer"]
    q_customer_id = get_customer_from_request(self, None)
    response_body[RESPONSE_DATA] = list(get_alerts_recent(customer_id=q_customer_id, date_range=time))
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_recent_alerts_detail(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    # user = get_user_from_request(self, None)
    # module_id = get_module_from_request(self, None)
    animal_id = self.query_params.get('animal')
    customer_id = get_customer_from_request(self, None)
    herd_id = self.query_params.get('herd')
    alert_status = self.query_params.get('status')
    limit = int(self.query_params.get('limit', RECENT_DATA))
    recent_alerts = util_get_recent_alerts(customer_id=customer_id, animal_id=animal_id, herd_id=herd_id,
                                           no_alerts=limit, status=alert_status)

    activity_type = Options.objects.get(key=ACTIVITY_TYPE, value=INSPECTION)
    alert_action = {'activity_type': activity_type.label,
                    'activity_type_id': activity_type.id}

    for alert in recent_alerts:
        alert_dict = alert.animal_alert_to_dict()
        if alert_dict:
            alert_dict.update(alert_action)
            response_body[RESPONSE_DATA].append(alert_dict)
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_alert_graph_data(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    # customer_id = self.query_params['customer']
    customer_id = get_customer_from_request(self, None)
    days = self.query_params.get('days', LAST_WEEK)
    group_by = self.query_params.get('group_by')
    group_by, days = ("%H", days) if group_by == "hour" else (GRAPH_DATE_FORMAT, days)
    from_date = dt.date.today() - timedelta(int(days))
    response_body[RESPONSE_DATA] = util_get_alerts_data_modified(customer_id, from_date, group_by)
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_herds_list(self):
    from random import randint
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    customer = self.query_params["customer"]
    for i in range(5, 11):
        response_body[RESPONSE_DATA].append(
            {
                "id": i,
                "name": "Name "+str(i),
                "cows": i*10,
                "heifers": randint(10, 15),
                "calves": randint(10, 15),
                "in lactation": randint(10, 15)
            }
        )
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@verify_request_params(params=['customer'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_scheduling_form_data(self):
    from hypernet.entity.utils import util_get_entity_dropdown
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: {}}
    customer = self.query_params["customer"]
    herd = self.query_params.get("herd")
    response_body[RESPONSE_DATA]['herd'] = (
        list(util_get_entity_dropdown(c_id=customer, entity_type=DeviceTypeEntityEnum.HERD)))
    response_body[RESPONSE_DATA]['animals'] = (list(get_herd_animal_ids(herd_id=herd)))
    response_body[RESPONSE_DATA]['staff'] = (list(get_all_staff(c_id=customer)))
    # REFACTOR THE option_key according to constants
    response_body[RESPONSE_DATA]['activity_type'] = (list(options_data(options_key='ioa_activity_type')))
    response_body[RESPONSE_DATA]['activity_routine_type'] = (list(options_data(options_key='ioa_routine_type')))
    response_body[RESPONSE_DATA]['activity_priority'] = (list(options_data(options_key='ioa_activity_priority')))
    return generic_response(response_body=response_body, http_status=200)


# @csrf_exempt
# @api_view(['GET'])
# @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
# def ignore_alert(self):
#     response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
#     pk = self.query_params['pk']
#     customer_id = self.query_params['customer']
#     response_body[RESPONSE_DATA] = update_alert_status(id=pk, c_id=customer_id, flag_is_viewed=False, status=None)
#     return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_alert_count_by_type(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    time = dt.date.today() - timedelta(days=float(self.query_params.get("days")))
    alert_name = self.query_params.get("alert")
    # c_id = self.query_params["customer"]
    c_id = get_customer_from_request(self, None)
    response_body[RESPONSE_DATA] = list(get_alerts_by_type(customer_id=c_id, s_date=time, alert_type=alert_name))
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['PATCH'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def update_alert_flag(request):
    from hypernet.notifications.utils import update_alert_flag_status
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    user = get_user_from_request(request, None).id
    customer = get_customer_from_request(request, None)
    module_id = get_module_from_request(request, None)
    update_status = update_alert_flag_status(u_id=user, c_id=customer, m_id=module_id)
    if update_status:
        response_body[RESPONSE_DATA] = TEXT_OPERATION_SUCCESSFUL
    else:
        response_body[RESPONSE_DATA] = DEFAULT_ERROR_MESSAGE
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_user_notifications(request):
    from hypernet.notifications.utils import util_user_notifications
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    user = get_user_from_request(request, None)
    customer = get_customer_from_request(request, None)
    module_id = get_module_from_request(request, None)
    response_body[RESPONSE_DATA] = util_user_notifications(u_id=user, c_id=customer, m_id=int(module_id))
    return generic_response(response_body=response_body, http_status=200)


# TODO Remove this API (Use from Hypernet Instead)
@csrf_exempt
@api_view(['PATCH'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def update_alerts_status(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    pk = request.data["pk"]
    customer = get_customer_from_request(request, None)
    module_id = get_module_from_request(request, None)
    status = request.data["status"]
    update_status = update_alert_status(id=pk, c_id=customer, status=status, m_id=module_id)
    print(update_status)
    if update_status:
        response_body[RESPONSE_DATA] = TEXT_OPERATION_SUCCESSFUL
    else:
        response_body[RESPONSE_DATA] = DEFAULT_ERROR_MESSAGE
    return generic_response(response_body=response_body, http_status=200)




#test comamnds



@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def create_entitites(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    type = get_default_param(request, 'type', None)
    items = get_default_param(request, 'items', None)
    user = get_user_from_request(request,None)
    customer = get_customer_from_request(request, None)
    module = get_customer_from_request(request, None)
    print(module)
    try:
        #arr = ['employee', 'truck', 'bin', 'driver']
        #type = options['type'][0]
        type = int(type)
        #print(type)
        for i in range(int(items)):

            devices = CustomerDevice.objects.filter(type_id=type, assigned=False)
            if devices:
                devices = devices[0]
            else:
                devices = None
            entity = Entity()
            if type == DeviceTypeEntityEnum.EMPLOYEE:
                entity.name = 'employee ' +str(generate_word(5))
            elif type == DeviceTypeEntityEnum.TRUCK:
                entity.name = 'truck ' + str(generate_word(5))
            elif type == DeviceTypeEntityEnum.BIN:
                entity.name = 'bin ' + str(generate_word(5))
            elif type == DeviceTypeEntityEnum.DRIVER:
                entity.name = 'driver ' + str(generate_word(5))
            elif type == DeviceTypeEntityEnum.RFID_SCANNER:
                entity.name = 'RFID Scanner ' + str(generate_word(5))
            elif type == DeviceTypeEntityEnum.RFID_TAG:
                entity.name = 'RFID Tag ' + str(generate_word(5))
            elif type == DeviceTypeEntityEnum.RFID_CARD:
                entity.name = 'RFID Card ' + str(generate_word(5))

            elif type == DeviceTypeEntityEnum.CONTRACT:
                entity.name = 'Contract ' + str(generate_word(5))
                x = random.choice([IOFOptionsEnum.METAL,
                                                           IOFOptionsEnum.GALVANIZED_METAL,
                                                           IOFOptionsEnum.GALVANIZED_METAL_OR_PLASTIC,
                                                           IOFOptionsEnum.PLASTIC])
                entity.entity_sub_type = Options.objects.get(id=x)
                entity.skip_rate = random.randint(1,100)
            elif type == DeviceTypeEntityEnum.CLIENT:
                entity.name = 'Client ' + str(generate_word(5))

            elif type == DeviceTypeEntityEnum.AREA:
                entity.name = 'Area  ' + str(generate_word(5))

            elif type == DeviceTypeEntityEnum.DUMPING_SITE:
                entity.name = 'Dump Site ' + str(generate_word(5))
                x, y = uniform(50,50), uniform(100, 100)
                entity.source_latlong = str(x)+ ',' +str(y)

            if type in [DeviceTypeEntityEnum.TRUCK, DeviceTypeEntityEnum.DRIVER,
                        DeviceTypeEntityEnum.BIN, DeviceTypeEntityEnum.RFID_SCANNER,
                        DeviceTypeEntityEnum.RFID_CARD, DeviceTypeEntityEnum.RFID_TAG,
                        DeviceTypeEntityEnum.DUMPING_SITE, DeviceTypeEntityEnum.CLIENT,
                        DeviceTypeEntityEnum.CONTRACT, DeviceTypeEntityEnum.AREA]:

                entity.module= Module.objects.get(id=1)


            if type in [DeviceTypeEntityEnum.EMPLOYEE]:
                entity.module= Module.objects.get(id=4)


            entity.status = Options.objects.get(id=OptionsEnum.ACTIVE)
            entity.customer = Customer.objects.get(id=customer)
            entity.type = DeviceType.objects.get(id=type)
            entity.modified_by = user
            entity.device_name = devices

            if type in [DeviceTypeEntityEnum.DRIVER, DeviceTypeEntityEnum.EMPLOYEE]:
                entity.cnic = '111-111-111'
                entity.dob = timezone.now()
                entity.date_of_joining = timezone.now()
                entity.gender = Options.objects.get(id=OptionsEnum.MALE)
                entity.marital_status = Options.objects.get(id=OptionsEnum.SINGLE)

            if type == DeviceTypeEntityEnum.EMPLOYEE:
                entity.entity_sub_type = Options.objects.get(id=FFPOptionsEnum.LABOUR)

            if type in [DeviceTypeEntityEnum.TRUCK, DeviceTypeEntityEnum.BIN]:
                entity.volume = False
                entity.speed = False
                entity.density = False
                entity.temperature = False
                entity.location = False
                entity.location = False
            if type == DeviceTypeEntityEnum.TRUCK:
                entity.make = 'Honda'
                entity.model = '2012'
                entity.color = 'Black'
            entity.save()
            if devices:
                devices.assigned = True
                devices.save()
            print("Total items saved: " + str(i))
            response_body[RESPONSE_DATA] = TEXT_OPERATION_SUCCESSFUL
        #self.stdout.write(self.style.SUCCESS('Successful.'))

    except Exception as e:
        print(e)
        response_body[RESPONSE_DATA] = TEXT_OPERATION_SUCCESSFUL
    return generic_response(response_body=response_body, http_status=200)





@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def create_devices(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    type = int(get_default_param(request, 'type', None))
    items = get_default_param(request, 'items', None)
    customer = get_customer_from_request(request, None)
    module = get_customer_from_request(request, None)
    print(module)
    label = DeviceType.objects.get(id=type).name
    total_devices = CustomerDevice.objects.filter(type_id=type).count()
    current_devices = total_devices
    try:
        print(type)
        for i in range(int(items)):
            device = CustomerDevice()
            device.primary_key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=14))
            device.device_id = 'device- ' + label + str(current_devices)
            device.status = Options.objects.get(id=OptionsEnum.ACTIVE)
            device.customer = Customer.objects.get(id=customer)
            device.type = DeviceType.objects.get(id=type)
            device.module = Module.objects.get(id=1)
            device.connection_string = 'Askar-output'
            device.save()
            current_devices+=1
    except Exception as e:
        print(e)
        response_body[RESPONSE_DATA] = TEXT_OPERATION_SUCCESSFUL
    return generic_response(response_body=response_body, http_status=200)

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import (
    AllowAny,)

@api_view(['GET'])
@permission_classes((AllowAny,))
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def alter_suez_data(request):
    import xlrd
    from datetime import datetime
    fname = 'ioa/management/commands/Copy of Book111.xlsx'
    xl_workbook = xlrd.open_workbook(fname)
    xl_sheet = xl_workbook.sheet_by_index(0)
    xl_sheet.cell_value(1, 0)

    same_end_date = 0
    different_end_date = 0
    count=0

    for i in range(1, xl_sheet.nrows):
        try:
            val_contract_name = xl_sheet.cell_value(i, 2)

            try:
                ent = Entity.objects.get(customer_id=2, name=val_contract_name)

            except:
                ent = None
                traceback.print_exc()

            if ent:
                count+=1
                print('{}st Row'.format(count))
                year = int(xl_sheet.cell_value(i, 5))
                month = xl_sheet.cell_value(i, 6)
                day = int(xl_sheet.cell_value(i, 7))

                month = get_month_from_str(month)

                end_date = datetime(year=year,
                         month=month, day=day, hour=0,
                         minute=0, second=0)
                if ent.date_of_joining != end_date.date():
                    ent.date_of_joining = end_date
                    ent.save()
                    different_end_date+=1
                    print('Contract end date modified')
                else:
                    same_end_date+=1
                    print('Same end date')
                    continue
        except:
            traceback.print_exc()
    print('Contracts with same end date: {}'.format(same_end_date))
    print('Contracts with different end date: {}'.format(different_end_date))

