import datetime
import traceback
import xlrd as xlsx_reader
import xlsxwriter

from hypernet.enums import OptionsEnum, DeviceTypeEntityEnum, ModuleEnum, DeviceTypeAssignmentEnum, IOFOptionsEnum
from .models import CustomerPreferences, CustomerClients
from hypernet.models import Entity, Assignment


# @receiver(post_save, sender=Customer)
def create_customer_prefrences(instance):

    try:
        customer_prefrences = CustomerPreferences()
        customer_prefrences.customer_id = instance.id
        customer_prefrences.save()

    except Exception as e:
        print(str(e))


'''
    EXCEL DATA INGESTION UTILS.
    pre-requisites 
    
    pip install xlrd
    
    update default file or provide in commands params.
    update default sheet name or provide in the command params. 
'''
FILE_NAME = ''
SHEET_NAME = ''

def create_customer_clients_csv(customer, file=None):
    print(file)
    if file:
        workbook = xlsx_reader.open_workbook(file)
    else:
        workbook = xlsx_reader.open_workbook('client_data_zenath.xlsx')

    worksheet = workbook.sheet_by_name(sheet_name='Sheet1')
    clients_list = []  # The row where we stock the name of the column
    area_list = []
    contract_list = []
    skip_list = []
    rate_list = []
    for row in range(worksheet.nrows):
        if row <= 7:
            continue
        clients_list.append(worksheet.cell_value(row, 1))
        contract_list.append(worksheet.cell_value(row, 2))
        area_list.append(worksheet.cell_value(row, 3))
        skip_list.append(worksheet.cell_value(row, 4))
        rate_list.append(worksheet.cell_value(row, 5))

    for client, contract, area, skip_size, rate in zip(clients_list, contract_list, area_list, skip_list, rate_list):
        client_obj, flag = CustomerClients.objects.get_or_create(name=client, customer_id=customer, status_id=OptionsEnum.ACTIVE,
                                              modified_by_id=1)

        area_obj, flag = Entity.objects.get_or_create(name=area, customer_id=customer, status_id=OptionsEnum.ACTIVE, modified_by_id=1,
                                     type_id=DeviceTypeEntityEnum.AREA, module_id=ModuleEnum.IOL)

        contract_obj, flag = Entity.objects.get_or_create(name=int(contract), customer_id=customer, status_id=OptionsEnum.ACTIVE,
                                              modified_by_id=1, type_id=DeviceTypeEntityEnum.CONTRACT,
                                              module_id=ModuleEnum.IOL, weight=skip_size, skip_rate=rate, client=client_obj)

        name= str(int(contract))+" "+area+" "+client
        Assignment.objects.get_or_create(name=name ,child=contract_obj, parent=area_obj, customer_id=customer,
            module_id=ModuleEnum.IOL,
            type_id=DeviceTypeAssignmentEnum.AREA_CONTRACT_ASSIGNMENT,
            status_id=OptionsEnum.ACTIVE,
            modified_by_id=1)


#Added Bin types in contracts.
def fixingdata_customer_clients_csv(customer, file=None):

    if file:
        workbook = xlsx_reader.open_workbook(file)
    else:
        workbook = xlsx_reader.open_workbook('client_data_zenath.xlsx')

    worksheet = workbook.sheet_by_name(sheet_name='Sheet1')
    clients_list = []  # The row where we stock the name of the column
    area_list = []
    contract_list = []
    skip_list = []
    rate_list = []
    for row in range(worksheet.nrows):
        if row <= 7:
            continue
        clients_list.append(worksheet.cell_value(row, 1))
        contract_list.append(worksheet.cell_value(row, 2))
        area_list.append(worksheet.cell_value(row, 3))
        skip_list.append(worksheet.cell_value(row, 4))
        rate_list.append(worksheet.cell_value(row, 5))

    print(contract_list[:10])

    for contract, skip_size in zip(contract_list, skip_list):
        # client_obj, flag = CustomerClients.objects.get_or_create(name=client, customer_id=customer, status_id=OptionsEnum.ACTIVE,
        #                                       modified_by_id=1)
        #
        # area_obj, flag = Entity.objects.get_or_create(name=area, customer_id=customer, status_id=OptionsEnum.ACTIVE, modified_by_id=1,
        #                              type_id=DeviceTypeEntityEnum.AREA, module_id=ModuleEnum.IOL)
        try:
            contract_obj = Entity.objects.get(name=int(contract), customer_id=customer, status_id=OptionsEnum.ACTIVE,
                                                  modified_by_id=1, type_id=DeviceTypeEntityEnum.CONTRACT,
                                                  module_id=ModuleEnum.IOL)

            # contract_obj.weight = skip_size
            # contract_obj.odo_reading = None
            if float(skip_size) == 0.240:
                contract_obj.entity_sub_type_id = IOFOptionsEnum.PLASTIC

            elif float(skip_size) == 1.1:
                contract_obj.entity_sub_type_id = IOFOptionsEnum.GALVANIZED_METAL_OR_PLASTIC

            elif float(skip_size) == 2.5:
                contract_obj.entity_sub_type_id = IOFOptionsEnum.GALVANIZED_METAL

            elif float(skip_size) >= 5:
                contract_obj.entity_sub_type_id = IOFOptionsEnum.METAL

            contract_obj.save()

        # name= str(int(contract))+" "+area+" "+client
        # Assignment.objects.get_or_create(name=name ,child=contract_obj, parent=area_obj, customer_id=customer,
        #     module_id=ModuleEnum.IOL,
        #     type_id=DeviceTypeAssignmentEnum.AREA_CONTRACT_ASSIGNMENT,
        #     status_id=OptionsEnum.ACTIVE,
        #     modified_by_id=1)

        except Entity.DoesNotExist:
            traceback.print_exc()


#Contract and Clients additional columns.
def modifying_zenath_data(customer, file=None):
    print(file)
    if file:
        workbook = xlsx_reader.open_workbook(file)
    else:
        workbook = xlsx_reader.open_workbook('client_data_zenath.xlsx')

    worksheet = workbook.sheet_by_name(sheet_name='ZNTH-CONTRCT')
    clients_list = []  # The row where we stock the name of the column
    contract_list = []
    party_code_list = []
    start_date_list = []
    end_date_list = []
    areas_list = []
    cont_signed_date = [] #dob
    cont_remarks_list = [] #description
    skip_size_list = [] #weight
    skip_rate_list = [] #skip_rate
    waste_type_list = []

    for row in range(worksheet.nrows):
        if row < 1:
            continue
        contract_list.append(worksheet.cell_value(row, 0))
        clients_list.append(worksheet.cell_value(row, 1))
        areas_list.append(worksheet.cell_value(row, 7))
        cont_signed_date.append(worksheet.cell_value(row, 3))
        party_code_list.append(worksheet.cell_value(row, 4))

        start_date_list.append(worksheet.cell_value(row, 5))
        end_date_list.append(worksheet.cell_value(row, 6))

        if worksheet.cell_value(row, 9) is "":
            skip_size_list.append(None)
        else:
            skip_size_list.append(worksheet.cell_value(row, 9))

        if worksheet.cell_value(row, 10) is "":
            skip_rate_list.append(None)
        else:
            skip_rate_list.append(worksheet.cell_value(row, 10))

        cont_remarks_list.append(worksheet.cell_value(row, 12))


        # waste_type_list.append(worksheet.cell_value(row, 9))

        #TODO Remarks for each contract....
        # cont_remarks_list.append(worksheet.cell_value(row, 10))


    # print(contract_list[:10])
    # print("clients")
    # print(clients_list[:10])
    # print("Skip $|ZE")
    # print(len(skip_size_list[189]))
    print(type(skip_size_list[189]))
    print((skip_size_list[189:192]))

    

    for contract, client, party_code, start_date, end_date, area, skip_size, skip_rate, remarks in \
            zip(contract_list, clients_list, party_code_list, start_date_list, end_date_list, areas_list, skip_size_list, skip_rate_list, cont_remarks_list):
        #Date Parse.
        cont_e_date = xlsx_reader.xldate_as_datetime(end_date, workbook.datemode).strftime('%Y-%m-%d')
        cont_s_date = xlsx_reader.xldate_as_datetime(start_date, workbook.datemode).strftime('%Y-%m-%d')
        client_obj = None
        area_obj = None
        contract_obj = None
        #CLIENT
        try:
            client_obj = CustomerClients.objects.get(name=str(client))
            if client_obj:
                client_obj.party_code = party_code
                client_obj.save()
        except CustomerClients.DoesNotExist:
            client_obj = CustomerClients.objects.create(name=client, customer_id=customer,
                                                        status_id=OptionsEnum.ACTIVE,
                                                        modified_by_id=1, party_code=party_code)
        #AREA
        try:
            area_obj = Entity.objects.get(name=area, type_id=DeviceTypeEntityEnum.AREA)
        except Entity.DoesNotExist:
            area_obj = Entity.objects.create(name=area, customer_id=customer, status_id=OptionsEnum.ACTIVE,
                                             modified_by_id=1,
                                             type_id=DeviceTypeEntityEnum.AREA, module_id=ModuleEnum.IOL)

        #CONTRACT
        if skip_size is not None:
            sub_type = entity_sub_type_method(skip_size)
        else:
            sub_type = None

        # if skip_size or skip_rate is None:
        #     skip_size = None
        #     skip_rate = None

        try:
            contract_obj = Entity.objects.get(name=str(int(contract)), type_id=DeviceTypeEntityEnum.CONTRACT)
            if contract_obj:
                contract_obj.client = client_obj
                contract_obj.date_commissioned = cont_s_date
                contract_obj.date_of_joining = cont_e_date
                contract_obj.entity_sub_type_id = sub_type
                contract_obj.weight = skip_size
                contract_obj.skip_rate = skip_rate
                contract_obj.save()
        except Entity.DoesNotExist:
            try:
                contract_obj = Entity.objects.create(name=int(contract), customer_id=customer,
                                                     status_id=OptionsEnum.ACTIVE,
                                                     modified_by_id=1, type_id=DeviceTypeEntityEnum.CONTRACT,
                                                     module_id=ModuleEnum.IOL, weight=skip_size,
                                                     skip_rate=skip_rate, client=client_obj, date_commissioned = cont_s_date,
                                                     date_of_joining = cont_e_date, entity_sub_type_id=sub_type)
            except:
                traceback.print_exc()
                break

        
        try:
            Assignment.objects.get(child=contract_obj, parent=area_obj)
        except Assignment.DoesNotExist:
            name = str(contract_obj.name) + " " + area_obj.name
            Assignment.objects.create(name=name, child=contract_obj, parent=area_obj, customer_id=customer,
                                         module_id=ModuleEnum.IOL,
                                         type_id=DeviceTypeAssignmentEnum.AREA_CONTRACT_ASSIGNMENT,
                                         status_id=OptionsEnum.ACTIVE,
                                         modified_by_id=1)


def modified_fixingdata_customer_clients_csv(customer, file=None):
    print(file)
    if file:
        workbook = xlsx_reader.open_workbook(file)
    else:
        workbook = xlsx_reader.open_workbook('client_data_zenath.xlsx')

    worksheet = workbook.sheet_by_name(sheet_name='NO PARTY CODE')
    clients_list = []  # The row where we stock the name of the column
    party_code_list = []
    for row in range(worksheet.nrows):
        if row <= 1:
            continue
        clients_list.append(worksheet.cell_value(row, 0))
        party_code_list.append(worksheet.cell_value(row, 4))

    print(clients_list[:10])
    print(party_code_list[:10])

    for client, party_code in zip(clients_list, party_code_list):
        try:
            client_cust = CustomerClients.objects.get(name=str(client))
            if client_cust:
                client_cust.party_code = party_code
                client_cust.save()

        except CustomerClients.DoesNotExist:
            # traceback.print_exc()
            print("Chutia Clients")
            print(client)


def dump(contract, area, client, outfile_path=None):

    workbook = xlsxwriter.Workbook(outfile_path)
    writer = workbook.add_worksheet("Incomplete-Data-Zenath")
    bold = workbook.add_format({'bold':True})
    wrap = workbook.add_format({'text_wrap': True, 'valign': 'top'})
    allign = workbook.add_format({'text_wrap': True, 'valign': 'top'})
    # wrap.set_text_wrap()
    row = 0
    writer.set_column(2, 2, 100)
    writer.write(row, 2,"We need complete data against these contracts, i.e. their area/client/skipsize/skiprate/start_date... etc. " ,bold)
    row +=2
    headers = []
    headers.append('Contracts') #0
    headers.append(' ')
    # headers.append('Areas') #1
    # headers.append(' ')
    # headers.append('Clients') #2

    # print(area[20:10])
    for i, elem in enumerate(headers):
        writer.write(row, i, elem, bold)
    row = 3
    for con, a, cl in zip(contract, area, client):
        writer.set_column(1, 3, 15)
        writer.write(row, 0, con, allign)
        row += 1
    workbook.close()


def entity_sub_type_method(skip_size):
    try:
        entity_sub_type = None
        if skip_size!= None:
            skip_size = float(skip_size)
        else:
            skip_size = 0

        if skip_size == 0.240:
            entity_sub_type = IOFOptionsEnum.PLASTIC

        elif (skip_size) == 1.1:
            entity_sub_type = IOFOptionsEnum.GALVANIZED_METAL_OR_PLASTIC

        elif (skip_size) == 2.5:
            entity_sub_type = IOFOptionsEnum.GALVANIZED_METAL

        elif (skip_size) >= 5.0:
            entity_sub_type = IOFOptionsEnum.METAL

        return entity_sub_type
    except:
        print("BC")
        print(type(skip_size))
        traceback.print_exc()
