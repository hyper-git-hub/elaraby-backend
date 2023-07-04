from django.core.management.base import BaseCommand, CommandError

from hypernet.enums import ModuleEnum, DeviceTypeAssignmentEnum, OptionsEnum, DeviceTypeEntityEnum
from hypernet.constants import ioa_options_dict
from hypernet.models import Entity, Assignment
from ioa.tests.test_animal import *
from options.models import Options
from dateutil.parser import parse


class Command(BaseCommand):
    """"
        Command python manage.py setupstatuses
    """
    '''
    def handle(self, *args, **options):
        try:
            import xlrd
            from datetime import datetime
            from hypernet.utils import get_month_from_str
            fname = 'ioa/management/commands/med_data.xlsx'
            xl_workbook = xlrd.open_workbook(fname)
            xl_sheet = xl_workbook.sheet_by_index(0)
            xl_sheet.cell_value(1, 0)

            client_lst = []
            party_code_lst = []
            contract_name_lst = []
            locations_lst = []
            area_lst = []

            start_time_lst = []
            end_time_lst = []

            for i in range(1, xl_sheet.nrows):
                try:
                    val_client = xl_sheet.cell_value(i, 1)
                    val_party_code = int(xl_sheet.cell_value(i, 0))
                    val_contract_name = xl_sheet.cell_value(i, 2)
                    val_location = xl_sheet.cell_value(i, 3)
                    val_area = xl_sheet.cell_value(i, 4)

                    contract_start_year = int(xl_sheet.cell_value(i, 6))
                    start_month = xl_sheet.cell_value(i, 8)
                    contract_start_month = get_month_from_str(start_month)

                    contract_start_day = int(xl_sheet.cell_value(i, 9))

                    contract_end_year = int(xl_sheet.cell_value(i, 10))
                    end_month = xl_sheet.cell_value(i, 12)

                    contract_end_month = get_month_from_str(end_month)

                    contract_end_day = int(xl_sheet.cell_value(i, 13))

                    contract_start_datetime = datetime(year=contract_start_year,
                                                       month=contract_start_month, day=contract_start_day, hour=0,
                                                       minute=0, second=0)

                    contract_end_datetime = datetime(year=contract_end_year,
                                                     month=contract_end_month, day=contract_end_day, hour=0,
                                                     minute=0, second=0)

                    start_time_lst.append(contract_start_datetime)
                    end_time_lst.append(contract_end_datetime)
                    client_lst.append(val_client)
                    party_code_lst.append(val_party_code)
                    contract_name_lst.append(val_contract_name)
                    locations_lst.append(val_location)
                    area_lst.append(val_area)


                except:
                    traceback.print_exc()

            create_clients(client_lst, party_code_lst)

            create_ent_with_type(contract_name_lst, DeviceTypeEntityEnum.CONTRACT, start_time_lst, end_time_lst,
                                 client_lst)
            create_generic_ent(area_lst, DeviceTypeEntityEnum.AREA)
            create_generic_ent(locations_lst, DeviceTypeEntityEnum.LOCATION)
            create_area_contract_loc_assignment(contract_name_lst, area_lst, locations_lst)



            self.stdout.write(self.style.SUCCESS('Successful.'))

        except Exception as e:
            self.stdout.write(self.style.WARNING(str(e) + 'Failed.'))
            raise CommandError('Failed to Setup IOA Options')
    
    '''


    def handle(self, *args, **options):
        try:
            import xlrd
            from datetime import datetime
            from hypernet.utils import get_month_from_str
            fname = 'ioa/management/commands/med_data.xlsx'
            xl_workbook = xlrd.open_workbook(fname)
            xl_sheet = xl_workbook.sheet_by_index(0)
            xl_sheet.cell_value(1, 0)


            for i in range(1, xl_sheet.nrows):
                try:
                    val_contract_name = xl_sheet.cell_value(i, 2)

                    try:
                        ent = Entity.objects.get(customer_id=2, name=val_contract_name)

                    except:
                        ent = None
                        traceback.print_exc()

                    if ent:
                        end_date = xl_sheet.cell_value(i, 4)
                        end_date = parse(end_date)
                        ent.date_of_joining = end_date
                        ent.save()


                except:
                    traceback.print_exc()
            self.stdout.write(self.style.SUCCESS('Successful.'))

        except Exception as e:
            self.stdout.write(self.style.WARNING(str(e) + 'Failed.'))
            raise CommandError('Failed to Setup IOA Options')