from jsonpickle.compat import unicode

from hypernet.entity.utils import single_or_bulk_delete_check_related_objects

__author__ = 'nahmed'

from django.db.models.signals import post_save, post_delete, pre_save
import csv
from django.dispatch import receiver
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from hypernet.utils import generic_response, get_customer_from_request, get_module_from_request
from ioa.utils import *
from reportlab import *



# from asyncio import

@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def animal_state_violation(request):
    from ioa.animal.animal_utils import animal_state_cron
    animal_state_cron()
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}

    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def animal_signal_test(request):
    from hypernet.models import Entity
    from customer.models import Customer
    customer = Customer.objects.filter(id=1)[0]

    entity = Entity()
    entity.name = customer.name + '_cow_' + str(101)
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
    entity.lactation_status_id = randint(1017, 1019)
    entity.customer = customer
    entity.modified_by_id = 1
    entity.module_id = ModuleEnum.IOA
    entity.status = Options.objects.get(value='Active', key='recordstatus')
    entity.type_id = DeviceTypeEntityEnum.ANIMAL
    entity.age = randint(1, 10)
    entity.weight = randint(100, 300)
    entity.save()
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}

    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def test_logging(request):
    import logging
    logger = logging.getLogger('hypernet')
    logger.debug('Logging DEBUG')
    logger.info('Logging INFO')
    logger.warning('Logging WARN')
    logger.error('Logging ERROR')
    # import hello
    try:
        import _json
    except ImportError as err:
        # logger.exception(err)
        logger.error(err, exc_info=True)
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def hypernet_search_bar(self):
    from django.db.models.functions import Concat
    from django.contrib.postgres.search import SearchVector
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    search_q = self.query_params.get('search')
    print(search_q)
    customer = get_customer_from_request(self, None)
    module_id = get_module_from_request(self, None)
    entity = Entity.objects.filter(customer=customer, module_id=module_id)
    search_results = entity.filter(). \
                         annotate(results=Concat('name', 'lactation_status__label', 'group__label', 'type__name')). \
                         filter(results__icontains=search_q)[:10]
    print(search_results)
    # for result in search_results:
    #     response_body[RESPONSE_DATA].append(result.animal_details_to_dict())
    response_body[RESPONSE_DATA] = list(search_results.values('id', title=F('name'), entity_type=F('type__name')))
    return generic_response(response_body=response_body, http_status=200)


# TEST CALL TO SAVE LIST OF DICT TO CSV
# ---------------------------------------------------------------------------------------------------------------------
@csrf_exempt
@api_view(['POST'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def data_to_csv(request):
    from email_manager.email_util import extended_email_with_title
    import csv
    from itertools import zip_longest
    response_body = {RESPONSE_MESSAGE: "Data Added to File", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: {}}

    q_set = Entity.objects.get(id=10295)

    flag, ent = single_or_bulk_delete_check_related_objects(q_set)
    response_body[RESPONSE_DATA] = [obj.as_entity_json() for obj in ent]
    # animals = Entity.objects.filter(customer_id=get_customer_from_request(request, None),
    #                                 module_id=ModuleEnum.IOL, type_id=DeviceTypeEntityEnum.TRUCK).values('name',
    #                                                                                                           'customer__name',
    #                                                                                                           'model', )
    # a = Assignment
    # dump(qs=Assignment, outfile_path='Test.csv')
    # export_data = zip_longest(*animals, fillvalue='')
    # with open('Test.csv', 'w', encoding="ISO-8859-1", newline='') as CSV_FILE:
    #     fields = ["name", "customer__name", "model"]
    #     csv_writer = csv.DictWriter(CSV_FILE, fieldnames=fields)
    #     # csv_writer.writerow(("name", "customer__name", "model"))
    #     for i in animals:
    #         csv_writer.writeheader()
    #         csv_writer.writerow(i.name)#, "customer__name":data.customer.name, "model": data.model})
    #         csv_writer.writerow(i.customer.name)
    # from email_manager.email_util import extended_email_with_title
    # csv_writer.writerow(['name', 'customer__name', 'model', 'modified_datetime'])
    # extended_email_with_title(title='activity_performed',
    #                           email_words_dict={})
    # send_sms_util()
    # response_body[RESPONSE_DATA] = cron_job_IOA_alerts()

    # import requests
    # email = request.data["email"]
    # password = request.data["password"]
    # data = {'email': email, 'password': password}
    # r = requests.post(url='http://188.166.226.185/api/users/login/', data=data)
    # result = r.content
    # jso = json.loads(result.decode('utf'))
    # response_body[RESPONSE_DATA] = jso["response"]
    return generic_response(response_body=response_body, http_status=200)


def dump(qs, outfile_path='Test.csv'):
    """
    Takes in a Django queryset and spits out a CSV file.

    Usage::

        >> from utils import dump2csv
        >> from dummy_app.models import *
        >> qs = DummyModel.objects.all()
        >> dump2csv.dump(qs, './data/dump.csv')

    Based on a snippet by zbyte64::

        http://www.djangosnippets.org/snippets/790/

    """
    model = qs
    writer = csv.writer(open(outfile_path, 'w'))
    headers = []

    field = [f for f in model._meta.fields if f.name != 'id' and f.name != 'child']

    for i in field:
        headers.append(i.name)
    print(field)
    writer.writerow(headers)
    for obj in qs.objects.all():
        row = []
        for field in headers:
            val = getattr(obj, field)
            if callable(val):
                val = val()
            # if type(val) == unicode:
            #     val = val.encode("utf-8")
            row.append(val)
        writer.writerow(row)

#TODO TEST
@receiver(post_save, sender=CustomerDevice)
def update_proxy_entitymap(sender, instance, **kwargs):
    from hypernet.models import EntityMap

    em, flag = EntityMap.objects.update_or_create(
        device_id=instance.device_id,
        defaults={
            'primary_key': instance.primary_key,
            'device_id':instance.device_id,
            'device_name':instance.device_id,
            'customer':instance.customer.id,
            'module':instance.module.id,
            'type':instance.type_id,
            'iot_hub':instance.connection_string
                })

    # if instance.type_id == DeviceTypeEntityEnum.ANIMAL:
    #     em.animal_group = instance.group.value
    #     em.lactation_status = instance.lactation_status.value
    #     em.breed = instance.breed.value
    #     em.save()

@receiver(post_delete, sender=CustomerDevice)
def delete_proxy_entitymap(sender, instance, **kwargs):
    from hypernet.models import EntityMap
    try:
        EntityMap.objects.filter(
            type=instance.type_id,
            primary_key=instance.primary_key,
        ).delete()

    except EntityMap.DoesNotExist:
        pass

    return None


# @receiver(pre_save, sender=CustomerDevice)
# def update_proxy_entitymap(sender, instance, **kwargs):
#     from hypernet.models import EntityMap
#     return None
