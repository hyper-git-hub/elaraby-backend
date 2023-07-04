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
    def add_arguments(self, parser):
        parser.add_argument('filename', nargs='+', type=str)

    def handle(self, *args, **options):
        import xlrd
        try:
            fname = "ioa/management/commands/"
            fname += options['filename'][0]
            xl_workbook = xlrd.open_workbook(fname)
            xl_sheet = xl_workbook.sheet_by_index(0)
            xl_sheet.cell_value(1, 0)

            for i in range(1, xl_sheet.nrows):
                try:
                    obj = dict()
                    obj['customer'] = 13
                    obj['timestamp'] = parse_datefield(xl_sheet.cell_value(i, 0))
                    # create entities of type truck
                    obj['vehicle'] = get_or_create_entity(xl_sheet.cell_value(i, 2), DeviceTypeEntityEnum.TRUCK)
                    truck = obj['vehicle']
                    obj['vehicle'] = truck.id
                    truck, obj['office'] = truck_office_wheels(truck, xl_sheet.cell_value(i, 65))
                    truck = truck_make_model(truck, xl_sheet.cell_value(i, 66))
                    truck.save()
                    obj['loading_location'] = get_or_create_entity(xl_sheet.cell_value(i, 3),
                                                                   DeviceTypeEntityEnum.LOCATION).id
                    obj['loading_city'] = get_or_create_entity(xl_sheet.cell_value(i, 4), DeviceTypeEntityEnum.AREA).id
                    obj['destination'] = get_or_create_entity(xl_sheet.cell_value(i, 5), DeviceTypeEntityEnum.AREA).id
                    obj['vms'] = xl_sheet.cell_value(i, 6)
                    obj['trip_number'] = xl_sheet.cell_value(i, 7)
                    obj['order_number'] = xl_sheet.cell_value(i, 8)
                    obj['client'] = get_or_create_client(xl_sheet.cell_value(i, 9))
                    obj['trip_start_datetime'] = parse_datefield(xl_sheet.cell_value(i, 10))
                    obj['loaded_datetime'] = parse_datefield(xl_sheet.cell_value(i, 11))
                    obj['stops_loaded_duration'] = parse_timefield(xl_sheet.cell_value(i, 12))
                    obj['arrival_datetime'] = parse_datefield(xl_sheet.cell_value(i, 13))
                    obj['unloaded_datetime'] = parse_datefield(xl_sheet.cell_value(i, 14))
                    obj['stops_unloading_duration'] = parse_timefield(xl_sheet.cell_value(i, 15))
                    obj['arrival_datetime'] = parse_datefield(xl_sheet.cell_value(i, 16))

                    obj['halting'] = parse_intfield(xl_sheet.cell_value(i, 20))
                    # regionl_closing_month = parse_datefield(xl_sheet.cell_value(i, 21))


                    obj['loaded_workshop_in'] = parse_datefield(xl_sheet.cell_value(i, 53))
                    obj['loaded_workshop_out'] = parse_datefield(xl_sheet.cell_value(i, 54))
                    # calculate duration
                    obj['loaded_work_order_number'] = xl_sheet.cell_value(i, 55)
                    obj['loaded_workshop_remarks'] = xl_sheet.cell_value(i, 56)

                    obj['unloaded_workshop_in'] = parse_datefield(xl_sheet.cell_value(i, 57))
                    obj['unloaded_workshop_out'] = parse_datefield(xl_sheet.cell_value(i, 58))
                    obj['unloaded_work_order_no'] = xl_sheet.cell_value(i, 59)
                    obj['unloaded_workshop_remarks'] = xl_sheet.cell_value(i, 60)

                    obj['km_loaded'] = parse_intfield(xl_sheet.cell_value(i, 62))
                    obj['km_unloaded'] = parse_intfield(xl_sheet.cell_value(i, 63))
                    obj['total_km'] = parse_intfield(xl_sheet.cell_value(i, 64))

                    obj['supervisor'] = get_or_create_entity(xl_sheet.cell_value(i, 69), DeviceTypeEntityEnum.SUPERVISOR).id

                    serializer = CMSVehicleReportingSerializer(data=obj, context=None)
                    if serializer.is_valid():
                        entity = serializer.save()
                    else:
                        print(serializer.errors)
                except:
                    print('Serial Number of erroneous record: ' + str(xl_sheet.cell_value(i, 1)))
        except Exception as e:
            self.stdout.write(self.style.WARNING(str(e) + 'Failed.'))
            raise CommandError('Failed to Setup IOA Options')
