from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, APIView
from rest_framework.generics import ListAPIView
from ioa.serializer import *
from hypernet.utils import generic_response, get_data_param, get_default_param, exception_handler, \
    get_customer_from_request, get_module_from_request
from datetime import datetime,timedelta
from ioa.utils import *

# Create your views here.
class AnimalControl(APIView):

    @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
    def get(self, request, pk):
        obj = Entity.objects.filter(pk=pk)
        response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
        if obj:
            obj = obj[0]
            serializer = AnimalSerializer(obj)
            data = serializer.data
            response_body[RESPONSE_DATA] = data
            return generic_response(response_body=response_body, http_status=200)
        return response_body

    def post(self, request):
        response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
        response_body[RESPONSE_DATA] = util_add_cows(request=request)
        return generic_response(response_body=response_body, http_status=200)



    def delete(self, pk):
        obj = Entity.objects.filter(pk=pk)
        response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
        if obj:
            obj = obj[0]
            # obj.status = Options.objects.get(key='', value='')
            obj.delete()
            data = obj.id
            response_body[RESPONSE_DATA] = data
            return generic_response(response_body=response_body, http_status=200)
        return response_body

    def patch(self, request, pk):
        obj = Entity.objects.filter(pk=pk)
        response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
        if obj:
            obj = obj[0]
            serializer = AnimalSerializer(obj, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                data = serializer.data
                response_body[RESPONSE_DATA] = data
                return generic_response(response_body=response_body, http_status=200)
            return response_body


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_animal_today_alerts_count(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    curr_date = datetime.date.today() - timedelta(days=100)
    animal_id = self.query_params['animal']
    customer_id = self.query_params['customer']
    response_body[RESPONSE_DATA] = list(
        get_animal_alerts_count(customer_id=customer_id, days=curr_date, animal_id=animal_id))
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_all_animals(self):
    # cust = self.query_params["customer"]
    cust = get_customer_from_request(self, 2)
    response_body = {RESPONSE_MESSAGE: ""}
    objs = Entity.objects.filter(type=DeviceTypeEntityEnum.ANIMAL, customer=cust).order_by('-id')
    serializer = AnimalSerializer(objs, many=True)
    response_body[RESPONSE_STATUS] = STATUS_OK
    response_body[RESPONSE_DATA] = serializer.data
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_animal_recent_alerts(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    animal_id = self.query_params.get('animal')
    customer_id = self.query_params.get('customer')
    herd_id = self.query_params.get('herd')
    no_alerts = self.query_params.get('no_alerts', RECENT_DATA)
    recent_alerts = util_get_recent_alerts(customer_id=customer_id, animal_id=animal_id, herd_id=herd_id,
                                           no_alerts=no_alerts)
    for alert in recent_alerts:
        response_body[RESPONSE_DATA].append(alert.animal_alert_to_dict())
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_animal_groups(self):
    # customer_id = self.query_params["customer"]
    customer_id = get_customer_from_request(self, 2)
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK,
                     RESPONSE_DATA: util_get_animal_group_count(customer_id)}
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_animal_detail(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    animal_id = self.query_params.get('animal')
    # customer_id = self.query_params['customer']
    customer_id = get_customer_from_request(self, 2)
    herd_id = self.query_params.get('herd')
    response_body[RESPONSE_DATA] = get_animals(a_id=animal_id, c_id=customer_id, h_id=herd_id)
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_animals_by_group(self):
    response_body = {RESPONSE_MESSAGE: "Successful", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    animal_group = self.query_params['group']
    # customer = self.query_params['customer']
    customer = get_customer_from_request(self, 2)
    response_body[RESPONSE_DATA] = list(get_animal_by_group(grp=animal_group, c_id=customer))
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_animals_by_status(self):
    response_body = {RESPONSE_MESSAGE: "Successful", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    animal_group = self.query_params['group']
    # customer = self.query_params['customer']
    customer = get_customer_from_request(self, 2)
    response_body[RESPONSE_DATA] = list(get_animal_by_status(sts=animal_group, c_id=customer))
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_total_animals(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: {}}
    # c_id = self.query_params.get("customer")
    c_id = get_customer_from_request(self, 2)
    response_body[RESPONSE_DATA]["total_animal"] = util_get_total_animals(customer_id=c_id).filter(
        type=DeviceTypeEntityEnum.ANIMAL).count()
    response_body[RESPONSE_DATA]["total_herd"] = util_get_total_animals(customer_id=c_id).filter(
        type=DeviceTypeEntityEnum.HERD).count()
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_animal_milk_yield_and_details(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    time = datetime.date.today() - timedelta(days=float(self.query_params.get("days")))
    animal = self.query_params["animal"]
    c_id = self.query_params["customer"]
    response_body[RESPONSE_DATA] = list(get_animal_milk_yield_last_two_days(c_id=c_id, a_id=animal, from_dtm=time))
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_animal_activities(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    time = datetime.date.today() - timedelta(days=float(self.query_params.get("days")))
    animal = self.query_params.get("animal")
    c_id = self.query_params["customer"]
    response_body[RESPONSE_DATA] = list(get_animal_activities_cow_page(c_id=c_id, a_id=animal, from_dtm=time))
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_animals_by_status(self):
    response_body = {RESPONSE_MESSAGE: "Successful", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    animal_status = self.query_params['status']
    # customer = self.query_params['customer']
    customer = get_customer_from_request(self, 2)
    response_body[RESPONSE_DATA] = list(get_animal_by_status(sts=animal_status, c_id=customer))
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_herd_information(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    # customer_id = self.query_params['customer']
    customer_id = int(get_customer_from_request(self, 2))
    response_body[RESPONSE_DATA] = list(get_herd_details_list(c_id=customer_id))
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_total_herds(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    # customer_id = self.query_params['customer']
    customer_id = get_customer_from_request(self, 2)
    response_body[RESPONSE_DATA] = util_get_total_herds(customer_id=customer_id)
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_herd_alerts_date(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    # customer_id = self.query_params['customer']
    customer_id = get_customer_from_request(self, 2)
    herd_id = self.query_params.get('herd')
    time_range = datetime.date.today() - timedelta(days=float(self.query_params.get("days", LAST_2WEEKS)))
    response_body[RESPONSE_DATA] = list(util_herd_alerts_date(customer_id=customer_id, herd_id=herd_id,
                                                              d_range=time_range))
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_animal_milk_cow_page(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    cust = self.query_params["customer"]
    animal = self.query_params.get("animal")
    time_range = datetime.date.today() - timedelta(days=float(self.query_params.get("days", TODAY)))
    response_body[RESPONSE_DATA] = list(get_animal_milk_yield(c_id=cust, a_id=animal, time_range=time_range))
    return generic_response(response_body=response_body, http_status=200)


class AnimalStats(APIView):
    @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
    def get(self, request):
        response = {RESPONSE_STATUS: STATUS_OK,
                    RESPONSE_MESSAGE: ""}
        http_status = 200
        print('calling')
        response[RESPONSE_DATA] = {}
        result = {
            "animal_stats": {
                LACTATING: [],
                DRY: [],
                PREGNANT: [],
                ESTRUS: [],
                RUMINATION: [],
                LAMENESS: [],
                TEMPERATURE: []
            },
            "animals": {},
            "max_milk_yield_animal": {
                "animal_id": 0,
                "animal_name": "",
                "animal_milk_yield": 0,
                "previous_animal_id": 0,
                "previous_animal_name": "",
                "previous_animal_milk_yield": 0
            },
            # "herd_feed_consumed": {
            #     "herd_id": 0,
            #     "herd_name": "",
            #     "feed_consumed": 0,
            #     "previous_herd_id": 0,
            #     "previous_herd_name": "",
            #     "previous_feed_consumed": 0
            # },
            "customer_feed_consumed": {
                "feed_value": 0,
                "previous_feed_value": 0
            },
            "milk_yield": {
                "current_milk_yield": 0,
                "expected_milk_yield": 0
            }
        }
        # customer_id = (get_default_param(request, 'customer', None))
        customer_id = get_customer_from_request(request, None)
        herd_id = (get_default_param(request, 'herd', None))
        if not customer_id:
            response[RESPONSE_MESSAGE] = 'params missing'
            response[RESPONSE_STATUS] = STATUS_ERROR
            http_status = 400
        else:
            customer_id = int(customer_id)
            result["animal_stats"][LACTATING] = get_cows_by_status(LACTATING, customer_id, herd_id)
            result["animal_stats"][DRY] = get_cows_by_status(DRY, customer_id, herd_id)
            result["animal_stats"][PREGNANT] = get_cows_by_status(PREGNANT, customer_id, herd_id)
            result["animal_stats"][ESTRUS] = get_cows_by_alerts(ESTRUS, customer_id, herd_id)
            result["animal_stats"][RUMINATION] = get_cows_by_alerts(RUMINATION, customer_id, herd_id)
            result["animal_stats"][LAMENESS] = get_cows_by_alerts(LAMENESS, customer_id, herd_id)
            result["animal_stats"][TEMPERATURE] = get_cows_by_alerts(TEMPERATURE, customer_id, herd_id)
            result["animals"] = util_get_animal_group_count(customer_id, herd_id)

            result["max_milk_yield_animal"]["animal_id"], result["max_milk_yield_animal"]["animal_name"], \
            result["max_milk_yield_animal"]["animal_milk_yield"] = get_this_week_top_cow(customer_id, herd_id)

            result["max_milk_yield_animal"]["previous_animal_id"], result["max_milk_yield_animal"]["previous_animal_name"], \
            result["max_milk_yield_animal"]["previous_animal_milk_yield"] = get_last_week_top_cow(customer_id, herd_id)
            result["customer_feed_consumed"]["feed_value"] = get_this_week_feed(customer_id, herd_id)
            result["customer_feed_consumed"]["previous_feed_value"] = get_last_week_feed(customer_id, herd_id)
            result["milk_yield"]["current_milk_yield"] = get_customer_current_milk_yield(customer_id, herd_id)
            result["milk_yield"]["expected_milk_yield"] = 0
            response[RESPONSE_DATA] = result

        return generic_response(response_body=response, http_status=http_status)


# TODO move to hypernet entity views.
@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_devices_dropdown(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    # cust = self.query_params["customer"]
    cust = get_customer_from_request(self, None)
    assigned_flag = self.query_params.get("assigned")
    response_body[RESPONSE_DATA] = util_get_devices_dropdown(c_id=cust, assignment=assigned_flag)
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_entity_type_dropdown(self):
    from hypernet.entity.utils import util_get_entity_dropdown
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    # customer_id = self.query_params['customer']
    customer_id = get_customer_from_request(self, None)
    module_id = int(get_module_from_request(self, None))
    entity = self.query_params['entity']
    # Parent is for IOA(Herd's Animals)
    parent = self.query_params.get('parent')
    response_body[RESPONSE_DATA] = list(
        get_entity_dropdown(c_id=customer_id, entity_type=entity, parent=parent, m_id=module_id))
    return generic_response(response_body=response_body, http_status=200)
