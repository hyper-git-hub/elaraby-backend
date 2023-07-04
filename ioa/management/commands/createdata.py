from datetime import timedelta
from random import randint
from django.core.management.base import BaseCommand, CommandError
from customer.models import Customer
from hypernet.enums import DeviceTypeEntityEnum, ModuleEnum, DeviceCategoryEnum, IOAOPTIONSEnum
from hypernet.models import Entity, Assignment, HypernetNotification, CustomerDevice
from options.models import Options
from ioa.models import Scheduling, User
from ioa.utils import get_random_date,get_random_time
from user.enums import RoleTypeEnum


class Command(BaseCommand):
    """"
        Command python manage.py setupstatuses
    """

    def handle(self, *args, **options):
        from datetime import datetime
        try:
            if Customer.objects.count() < 5:
                for number in range(1, 2):
                    Customer.objects.create(name='customer_'+str(number),
                                            status=Options.objects.get(value='Active', key='recordstatus'),
                                            subscription_is_valid=True)

            if Entity.objects.all().count() < 100:
                customers = Customer.objects.all()
                for customer in customers:
                    for i in range(1, 10):
                        entity = Entity()
                        entity.name = customer.name+'_cow_'+str(i)
                        entity.assignments = 0
                        entity.device_name = None
                        entity.speed = False
                        entity.volume = False
                        entity.location = False
                        entity.temperature = False
                        entity.density = False
                        entity.obd2_compliant = False
                        entity.lactation_days = randint(0, 180)
                        entity.group_id = randint(1011, 1013)
                        entity.lactation_status_id = randint(1017, 1020)
                        entity.customer = customer
                        entity.modified_by_id = 2
                        entity.module_id = ModuleEnum.IOA
                        entity.status = Options.objects.get(value='Active', key='recordstatus')
                        entity.type_id = DeviceTypeEntityEnum.ANIMAL
                        entity.age = randint(1, 10)
                        entity.weight = randint(100, 300)
                        entity.save()

                    for j in range(1, 2):
                        entity = Entity()
                        entity.name = customer.name+'_herd_' + str(j)
                        entity.assignments = 0
                        entity.device_name = None
                        entity.speed = False
                        entity.volume = False
                        entity.location = False
                        entity.temperature = False
                        entity.density = False
                        entity.obd2_compliant = False
                        entity.lactation_days = None
                        entity.customer = customer
                        entity.modified_by_id = 2
                        entity.module_id = ModuleEnum.IOA
                        entity.status = Options.objects.get(value='Active', key='recordstatus')
                        entity.type_id = DeviceTypeEntityEnum.HERD
                        entity.save()

            if Assignment.objects.all().count() < 100:
                customers = Customer.objects.all()
                for cust in customers:
                    entities = Entity.objects.filter(customer=cust, module=2, modified_by_id=2).order_by('id')
                    herds = entities.filter(type_id=DeviceTypeEntityEnum.HERD)[0:1]
                    animals = entities.filter(type_id=DeviceTypeEntityEnum.ANIMAL)[0:10]
                    for i in range(0, 10):
                        for j in range(0, 10):
                            assignment = Assignment()
                            assignment.name = herds[i].name
                            assignment.comments = herds[i].name+' comments'
                            assignment.customer = cust
                            assignment.parent = herds[i]
                            assignment.child = animals[i][j]
                            assignment.modified_by_id = 2
                            assignment.module_id = ModuleEnum.IOA
                            assignment.status_id = herds[i].status_id
                            assignment.type_id = DeviceCategoryEnum.ASSIGNMENT
                            assignment.save()

            if Scheduling.objects.all().count() < 60:
                customers = Customer.objects.all()
                for cust in customers:
                    entities = Entity.objects.filter(customer=cust).order_by('id')
                    herds = entities.filter(type_id=DeviceTypeEntityEnum.HERD)[0:1]
                    for h in herds:
                        rand_start_time, rand_end_time = get_random_time()
                        rand_date = get_random_date()
                        activity_type = randint(1008, 1010)
                        scheduling = Scheduling()
                        scheduling.comments = cust.name
                        scheduling.routine_type_id = randint(1014, 1016)
                        scheduling.activity_type_id = activity_type
                        scheduling.activity_priority_id = randint(1021, 1023)
                        scheduling.scheduled_start_time = rand_start_time
                        scheduling.scheduled_end_time = rand_end_time
                        scheduling.scheduled_start_date = rand_date
                        scheduling.scheduled_end_date = rand_date
                        scheduling.perform_individually = activity_type == 1008
                        scheduling.is_active = True
                        scheduling.scheduled_next_date = rand_date
                        scheduling.assigned_to_id = randint(14, 25)
                        scheduling.customer = cust
                        scheduling.save()
                        for cow in h.assignment_parent.first().get_all_childs():
                            scheduling.animal.add(Entity.objects.get(pk=int(cow['child_id'])))
                        scheduling.save()

            # customers = Customer.objects.all()
            # for cust in customers:
            #     entities = Entity.objects.filter(customer=cust).order_by('id')
            #     for i in range(1, 20):
            #         alert = HypernetNotification()
            #         alert.device = entities[randint(0, entities.count()-1)]
            #         alert.timestamp = datetime.now() - timedelta(days=randint(0, 10))
            #         alert.violation_type_id = randint(IOAOPTIONSEnum.ALERT_TYPE_ESTRUS,
            #                                           IOAOPTIONSEnum.ALERT_TYPE_TEMPERATURE)
            #         alert.threshold = randint(50, 200)
            #         alert.value = randint(10, 100)
            #         alert.module_id = ModuleEnum.IOA
            #         alert.customer = cust
            #         alert.status_id = 13
            #         alert.save()

            self.stdout.write(self.style.SUCCESS('Successful.'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(str(e) + 'Failed.'))
            raise CommandError('Failed to Create IOA Dummy Data')
