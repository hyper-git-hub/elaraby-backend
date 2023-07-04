from django.core.management.base import BaseCommand, CommandError

from hypernet.enums import ModuleEnum, DeviceTypeAssignmentEnum, OptionsEnum, DeviceTypeEntityEnum
from hypernet.constants import ioa_options_dict
from hypernet.models import Entity, Assignment
from ioa.tests.test_animal import create_location_ent, create_contract_location_ass
from options.models import Options

class Command(BaseCommand):
    """"
        Command python manage.py setupstatuses
    """

    def handle(self, *args, **options):
        try:
            import xlrd
            fname = '/Users/metis/IOT/Hypernet/hypernet/hypernet-backend/ioa/management/commands/19 VMR_02_FEB 19 Saqib.xlsx'
            xl_workbook = xlrd.open_workbook(fname)
            xl_sheet = xl_workbook.sheet_by_index(0)
            xl_sheet.cell_value(1, 0)

            contract_lst = []
            locations_lst = []

            for i in range(1, xl_sheet.nrows):
                try:
                    if xl_sheet.cell_value(i, 6) is not '':
                        val_locations = xl_sheet.cell_value(i, 6)
                        val_contracts = int(xl_sheet.cell_value(i, 0))
                        contract_lst.append(val_contracts)
                        locations_lst.append(val_locations)

                    else:
                        continue
                except:
                    continue

            print(len(contract_lst))
            print(len(locations_lst))
            # create_locations = create_location_ent(loc_list=locations_lst)
            # create_contract_location_ass(con_lst=contract_lst, loc_lst=locations_lst)

            self.stdout.write(self.style.SUCCESS('Successful.'))

        except Exception as e:
            self.stdout.write(self.style.WARNING(str(e) + ' Failed.'))
            raise CommandError('Failed to Add Excel Data')
