from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, APIView
from hypernet.utils import generic_response, get_data_param, get_default_param, exception_handler
import calendar
from ioa.utils import *
from django.db.models import Sum
# import ioa.utils as utils # eventually move all aggregation_utils to ioa.utils
# from ioa.aggregation.aggregation_utils import *
import ioa.aggregation.aggregation_utils as utils  # for better readability


class CowMilkYieldAggregation(APIView):
    @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
    def get(self, request):
        from django.utils import dateparse
        from datetime import datetime
        response = {RESPONSE_STATUS: STATUS_ERROR,
                    RESPONSE_MESSAGE: DEFAULT_ERROR_MESSAGE}
        http_status = 400
        customer_id = (get_default_param(request, 'customer', None))
        created_date = (get_default_param(request, 'created_date', None))
        days = (get_default_param(request, 'days', None))
        cow_id = (get_default_param(request, 'cow_id', None))
        if not customer_id or not created_date or not cow_id:
            response[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        else:
            customer_id = int(customer_id)
            cow_id = int(cow_id)
            created_date_time = datetime.combine(dateparse.parse_date(created_date), datetime.min.time())
            response[RESPONSE_MESSAGE] = ""
            response[RESPONSE_STATUS] = STATUS_OK
            http_status = 200
            # response[RESPONSE_DATA] = {}
            response[RESPONSE_DATA] = utils.milk_yield_aggregation_by_cow(customer_id, cow_id, created_date_time, days)
            # if days:
            #     days = int(days)
            #     prev_date = created_date_time - timedelta(days=days)  # , hours=23, minutes=59, seconds=59)
            #     next_date = created_date_time + timedelta(hours=23, minutes=59, seconds=59)
            #     data = Aggregation.objects.filter(customer_aggregations_id=customer_id,
            #                                       animal_id=cow_id,
            #                                       created_datetime__gt=prev_date,
            #                                       created_datetime__lte=next_date)
            #     if data:
            #         total_milk_yield = data.values('animal_id').annotate(total=Sum('avg_milk_yield'))
            #         response[RESPONSE_DATA] = {"animal_id": total_milk_yield[0]['animal_id'],
            #                                    "milk_yield": total_milk_yield[0]['total']}
            # else:
            #     prev_date = created_date_time - timedelta(days=1, hours=23, minutes=59, seconds=59)
            #     next_date = created_date_time + timedelta(days=1)
            #     data = Aggregation.objects.filter(customer_aggregations_id=customer_id,
            #                                       animal_id=cow_id,
            #                                       created_datetime__gt=prev_date,
            #                                       created_datetime__lt=next_date)
            #     if data.count()>0:
            #         response[RESPONSE_DATA] = data[0].animal_milk_yield()

        return generic_response(response_body=response, http_status=http_status)


class HerdMilkYieldAggregation(APIView):
    @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
    def get(self, request):
        from django.utils import dateparse
        from datetime import datetime
        response = {RESPONSE_STATUS: STATUS_ERROR,
                    RESPONSE_MESSAGE: DEFAULT_ERROR_MESSAGE}
        http_status = 400
        customer_id = (get_default_param(request, 'customer', None))
        created_date = (get_default_param(request, 'created_date', None))
        days = (get_default_param(request, 'days', None))
        herd_id = (get_default_param(request, 'herd_id', None))
        if not customer_id or not herd_id or not created_date:
            response[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        else:
            customer_id = int(customer_id)
            herd_id = int(herd_id)
            created_date_time = datetime.combine(dateparse.parse_date(created_date), datetime.min.time())
            response[RESPONSE_MESSAGE] = ""
            response[RESPONSE_STATUS] = STATUS_OK
            http_status = 200
            response[RESPONSE_DATA] = {}
            if days:
                days = int(days)
                prev_date = created_date_time - timedelta(days=days)  # , hours=23, minutes=59, seconds=59)
                next_date = created_date_time + timedelta(hours=23, minutes=59, seconds=59)
                data = utils.milk_yield_aggregation_by_herd(customer_id, herd_id, prev_date, next_date)
                # data = Aggregation.objects.filter(customer_aggregations_id=customer_id,
                #                                   herd_id=herd_id,
                #                                   animal_id__isnull=True,
                #                                   created_datetime__gt=prev_date,
                #                                   created_datetime__lt=next_date)
                if data:
                    total_milk_yield = data.values('herd_id').annotate(total=Sum('avg_milk_yield'))
                    response[RESPONSE_DATA] = {"herd_id": total_milk_yield[0]['herd_id'],
                                               "milk_yield": total_milk_yield[0]['total']}
            else:
                prev_date = created_date_time - timedelta(days=1, hours=23, minutes=59, seconds=59)
                next_date = created_date_time + timedelta(days=1)
                data = utils.milk_yield_aggregation_by_herd(customer_id, herd_id, prev_date, next_date)
                # data = Aggregation.objects.filter(customer_aggregations_id=customer_id,
                #                                   herd_id=herd_id,
                #                                   animal_id__isnull=True,
                #                                   created_datetime__gt=prev_date,
                #                                   created_datetime__lt=next_date)
                if data.count()>0:
                    response[RESPONSE_DATA] = data[0].herd_milk_yield()

        return generic_response(response_body=response, http_status=http_status)


class HerdFeedAggregation(APIView):
    @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
    def get(self, request):
        from django.utils import dateparse
        from datetime import datetime
        response = {RESPONSE_STATUS: STATUS_ERROR,
                    RESPONSE_MESSAGE: DEFAULT_ERROR_MESSAGE}
        http_status = 400
        customer_id = (get_default_param(request, 'customer', None))
        created_date = (get_default_param(request, 'created_date', None))
        days = (get_default_param(request, 'days', None))
        herd_id = (get_default_param(request, 'herd_id', None))
        if not customer_id or not herd_id or not created_date:
            response[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        else:
            customer_id = int(customer_id)
            herd_id = int(herd_id)
            created_date_time = datetime.combine(dateparse.parse_date(created_date), datetime.min.time())
            response[RESPONSE_MESSAGE] = ""
            response[RESPONSE_STATUS] = STATUS_OK
            http_status = 200
            response[RESPONSE_DATA] = {}
            if days:
                days = int(days)
                prev_date = created_date_time - timedelta(days=days)  # , hours=23, minutes=59, seconds=59)
                next_date = created_date_time + timedelta(hours=23, minutes=59, seconds=59)
                data = utils.feed_aggregation_by_herd(customer_id, herd_id, prev_date, next_date)
                # data = Aggregation.objects.filter(customer_aggregations_id=customer_id,
                #                                   herd_id=herd_id,
                #                                   animal_id__isnull=True,
                #                                   feeding_value__isnull=False,
                #                                   created_datetime__gt=prev_date,
                #                                   created_datetime__lt=next_date)
                if data:
                    total_milk_yield = data.values('herd_id').annotate(total=Sum('feeding_value'))
                    response[RESPONSE_DATA] = {"herd_id": total_milk_yield[0]['herd_id'],
                                               "feed_consumed": total_milk_yield[0]['total']}
            else:
                prev_date = created_date_time - timedelta(days=1, hours=23, minutes=59, seconds=59)
                next_date = created_date_time + timedelta(days=1)
                data = utils.feed_aggregation_by_herd(customer_id, herd_id, prev_date, next_date)
                # data = Aggregation.objects.filter(customer_aggregations_id=customer_id,
                #                                   herd_id=herd_id,
                #                                   animal_id__isnull=True,
                #                                   feeding_value__isnull=False,
                #                                   created_datetime__gt=prev_date,
                #                                   created_datetime__lt=next_date)
                if data.count() > 0:
                    response[RESPONSE_DATA] = data[0].herd_feed()

        return generic_response(response_body=response, http_status=http_status)


class CustomerMilkYieldAggregation(APIView):
    @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
    def get(self, request):
        from django.utils import dateparse
        from datetime import datetime
        response = {RESPONSE_STATUS: STATUS_ERROR,
                    RESPONSE_MESSAGE: DEFAULT_ERROR_MESSAGE}
        http_status = 400
        customer_id = (get_default_param(request, 'customer', None))
        created_date = (get_default_param(request, 'created_date', None))
        days = (get_default_param(request, 'days', None))
        if not customer_id or not created_date:
            response[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        else:
            customer_id = int(customer_id)
            created_date_time = datetime.combine(dateparse.parse_date(created_date), datetime.min.time())
            response[RESPONSE_MESSAGE] = ""
            response[RESPONSE_STATUS] = STATUS_OK
            http_status = 200
            response[RESPONSE_DATA] = {}
            if days:
                days = int(days)
                prev_date = created_date_time - timedelta(days=days)  # , hours=23, minutes=59, seconds=59)
                next_date = created_date_time + timedelta(hours=23, minutes=59, seconds=59)
                data = utils.milk_yield_aggregation_by_customer(customer_id, prev_date, next_date)
                # data = Aggregation.objects.filter(customer_aggregations=customer_id,
                #                                   herd_id__isnull=True,
                #                                   animal_id__isnull=True,
                #                                   created_datetime__gt=prev_date,
                #                                   created_datetime__lt=next_date)
                if data:
                    total_milk_yield = data.values('customer_aggregations_id').annotate(total=Sum('avg_milk_yield'))
                    response[RESPONSE_DATA] = {"customer_id": total_milk_yield[0]['customer_aggregations_id'],
                                               "milk_yield": total_milk_yield[0]['total']}
            else:
                prev_date = created_date_time - timedelta(days=1, hours=23, minutes=59, seconds=59)
                next_date = created_date_time + timedelta(days=1)
                data = utils.milk_yield_aggregation_by_customer(customer_id, prev_date, next_date)
                # data = Aggregation.objects.filter(customer_aggregations=customer_id,
                #                                   herd_id__isnull=True,
                #                                   animal_id__isnull=True,
                #                                   created_datetime__gt=prev_date,
                #                                   created_datetime__lt=next_date)
                if data.count()>0:
                    response[RESPONSE_DATA] = data[0].customer_milk_yield()
        return generic_response(response_body=response, http_status=http_status)


class CustomerFeedAggregation(APIView):
    @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
    def get(self, request):
        from django.utils import dateparse
        from datetime import datetime
        response = {RESPONSE_STATUS: STATUS_ERROR,
                    RESPONSE_MESSAGE: DEFAULT_ERROR_MESSAGE}
        http_status = 400
        customer_id = (get_default_param(request, 'customer', None))
        # created_date = (get_default_param(request, 'created_date', None))
        days = (get_default_param(request, 'days', None))
        if not customer_id:  # or not created_date:
            response[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        else:
            customer_id = int(customer_id)
            # created_date_time = datetime.combine(dateparse.parse_date(created_date), datetime.min.time())
            created_date_time = datetime.today()
            response[RESPONSE_MESSAGE] = ""
            response[RESPONSE_STATUS] = STATUS_OK
            http_status = 200
            response[RESPONSE_DATA] = {}
            if days:
                days = int(days)
                prev_date = created_date_time - timedelta(days=days)  # , hours=23, minutes=59, seconds=59)
                next_date = created_date_time + timedelta(hours=23, minutes=59, seconds=59)
                data = utils.feed_aggregation_by_customer(customer_id, prev_date, next_date)

                if data.count() > 0:
                    total_feed_yield = data.values('customer_aggregations_id').annotate(total=Sum('feeding_value'))
                    response[RESPONSE_DATA] = {"customer_id": total_feed_yield[0]['customer_aggregations_id'],
                                               "feed_consumed": total_feed_yield[0]['total']}
            else:
                prev_date = created_date_time - timedelta(days=1, hours=23, minutes=59, seconds=59)
                next_date = created_date_time + timedelta(days=1)
                data = utils.feed_aggregation_by_customer(customer_id, prev_date, next_date)

                if data.count() > 0:
                    response[RESPONSE_DATA] = data[0].customer_feed()
        return generic_response(response_body=response, http_status=http_status)


class TopHerdsAggregationView(APIView):
    @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
    def get(self, request):
        from django.utils import dateparse
        from datetime import datetime
        response = {RESPONSE_STATUS: STATUS_ERROR,
                    RESPONSE_MESSAGE: DEFAULT_ERROR_MESSAGE}
        http_status = 400
        customer_id = (get_default_param(request, 'customer', None))
        if not customer_id:
            response[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        else:
            created_date = (get_default_param(request, 'created_date', None))
            feed_consumed = (get_default_param(request, 'feed_consumed', None))
            limit = (get_default_param(request, 'limit', None))
            created_date = created_date if created_date else str(datetime.now().date())
            limit = int(limit) if limit else 10
            created_date_time = datetime.combine(dateparse.parse_date(created_date), datetime.min.time())
            customer_id = int(customer_id)
            next_date = (last_day_of_month(created_date_time)+timedelta(hours=23, minutes=59, seconds=59))
            prev_date = created_date_time.replace(day=1)
            response[RESPONSE_MESSAGE] = ""
            response[RESPONSE_STATUS] = STATUS_OK
            http_status = 200
            # response[RESPONSE_DATA] = []
            response[RESPONSE_DATA] = utils.get_top_herds_aggregation(customer_id=customer_id, prev_date=prev_date,
                                                                      next_date=next_date, limit=limit,
                                                                      feed_consumed=feed_consumed)
            # if feed_consumed:
            #     data = Aggregation.objects.filter(customer_aggregations_id=customer_id,
            #                                       herd_id__isnull=False,
            #                                       animal_id__isnull=True,
            #                                       avg_milk_yield__isnull=True,
            #                                       created_datetime__gt=prev_date,
            #                                       created_datetime__lt=next_date)
            #     if data:
            #         total_feed_yield = data.values('herd_id','herd__name').annotate(
            #             feed_consumed=Sum('feeding_value')).order_by('-feed_consumed')[:limit]
            #         response[RESPONSE_DATA] = [get_json_queryset(x, 'herd_id', 'herd__name',
            #                                                      'feed_consumed') for x in total_feed_yield]
            #
            # else:
            #     data = Aggregation.objects.filter(customer_aggregations_id=customer_id,
            #                                       herd_id__isnull=False,
            #                                       animal_id__isnull=True,
            #                                       feeding_value__isnull=True,
            #                                       created_datetime__gt=prev_date,
            #                                       created_datetime__lt=next_date)
            #     if data:
            #         total_feed_yield = data.values('herd_id','herd__name').annotate(
            #             milk_yield=Sum('avg_milk_yield')).order_by('-milk_yield')[:limit]
            #         response[RESPONSE_DATA] = [get_json_queryset(x, 'herd_id', 'herd__name',
            #                                                      'milk_yield') for x in total_feed_yield]

        return generic_response(response_body=response, http_status=http_status)


class TopAnimalsAggregationView(APIView):
    @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
    def get(self, request):
        from django.utils import dateparse
        from datetime import datetime
        response = {RESPONSE_STATUS: STATUS_ERROR,
                    RESPONSE_MESSAGE: DEFAULT_ERROR_MESSAGE}
        http_status = 400
        customer_id = (get_default_param(request, 'customer', None))
        if not customer_id:
            response[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        else:
            created_date = (get_default_param(request, 'created_date', None))
            limit = (get_default_param(request, 'limit', None))
            created_date = created_date if created_date else str(datetime.now().date())
            limit = int(limit) if limit else 10
            created_date_time = datetime.combine(dateparse.parse_date(created_date), datetime.min.time())
            customer_id = int(customer_id)
            # next_date = (last_day_of_month(created_date_time)+timedelta(hours=23, minutes=59, seconds=59))
            # prev_date = created_date_time.replace(day=1)
            # data = Aggregation.objects.filter(customer_aggregations_id=customer_id,
            #                                   herd_id__isnull=False,
            #                                   animal_id__isnull=False,
            #                                   feeding_value__isnull=True,
            #                                   created_datetime__gt=prev_date,
            #                                   created_datetime__lt=next_date)
            response[RESPONSE_MESSAGE] = ""
            response[RESPONSE_STATUS] = STATUS_OK
            http_status = 200
            response[RESPONSE_DATA] = utils.get_top_animals_aggregation(customer_id, created_date_time, limit)
            # response[RESPONSE_DATA] = []
            # if data:
            #     total_milk_yield = data.values('animal_id', 'animal__name').annotate(
            #         milk_yield=Sum('avg_milk_yield')).order_by('-milk_yield')[:limit]
            #     response[RESPONSE_DATA] = [get_json_queryset(x, 'animal_id', 'animal__name', 'milk_yield')
            #                                for x in total_milk_yield]
        return generic_response(response_body=response, http_status=http_status)



class TopMilkYielderAggregationView(APIView):
    @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
    def get(self, request):
        from django.utils import dateparse
        from datetime import datetime
        response = {RESPONSE_STATUS: STATUS_ERROR,
                    RESPONSE_MESSAGE: DEFAULT_ERROR_MESSAGE}
        http_status = 400
        customer_id = (get_default_param(request, 'customer', None))
        if not customer_id:
            response[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        else:

            created_date = (get_default_param(request, 'created_date', None))
            limit = (get_default_param(request, 'limit', 10))
            created_date = created_date if created_date else str(datetime.now().date())
            created_date_time = datetime.combine(dateparse.parse_date(created_date), datetime.min.time())
            next_date = (last_day_of_month(created_date_time)+timedelta(hours=23, minutes=59, seconds=59))
            prev_date = created_date_time.replace(day=1)
            animal_milk_data = Aggregation.objects.filter(customer_aggregations_id=customer_id,
                                              herd_id__isnull=False,
                                              animal_id__isnull=False,
                                              feeding_value__isnull=True,
                                              created_datetime__gt=prev_date,
                                              created_datetime__lt=next_date)

            herd_milk_data = Aggregation.objects.filter(customer_aggregations_id=customer_id,
                                                  herd_id__isnull=False,
                                                  animal_id__isnull=True,
                                                  feeding_value__isnull=True,
                                                  created_datetime__gt=prev_date,
                                                  created_datetime__lt=next_date)


            response[RESPONSE_MESSAGE] = ""
            response[RESPONSE_STATUS] = STATUS_OK
            response[RESPONSE_DATA] = {
                'animal': [],
                'herd': []

            }
            http_status = 200
            if animal_milk_data:
                total_milk_yield_animal = animal_milk_data.values(entity_id=F('animal_id'), name=F('animal__name')).annotate(
                    milk_yield=Sum('avg_milk_yield')).order_by('-milk_yield')[:limit]
                response[RESPONSE_DATA]['animal'] = [get_json_queryset(x, 'entity_id', 'name', 'milk_yield')
                                           for x in total_milk_yield_animal]
            if herd_milk_data:
                total_milk_yield_herd = herd_milk_data.values(entity_id=F('herd_id'), name=F('herd__name')).annotate(
                        milk_yield=Sum('avg_milk_yield')).order_by('-milk_yield')[:limit]
                response[RESPONSE_DATA]['herd'] = [get_json_queryset(x, 'entity_id', 'name',
                                                                 'milk_yield') for x in total_milk_yield_herd]

        return generic_response(response_body=response, http_status=http_status)





class MilkYieldMonthlyView(APIView):
    @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
    def get(self, request):
        from django.utils import dateparse
        from datetime import datetime
        response = {RESPONSE_STATUS: STATUS_ERROR,
                    RESPONSE_MESSAGE: DEFAULT_ERROR_MESSAGE}
        http_status = 400
        customer_id = (get_default_param(request, 'customer', None))

        if not customer_id:
            response[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        else:
            created_date = (get_default_param(request, 'created_date', None))
            if not created_date:
                created_date = str(datetime.now().date())
            created_date_time = datetime.combine(dateparse.parse_date(created_date), datetime.min.time())
            customer_id = int(customer_id)
            next_date = (last_day_of_month(created_date_time)+timedelta(hours=23, minutes=59, seconds=59))
            prev_date = created_date_time.replace(day=1)
            data = Aggregation.objects.filter(customer_aggregations_id=customer_id,
                                              herd_id__isnull=True,
                                              animal_id__isnull=True,
                                              feeding_value__isnull=True,
                                              created_datetime__gt=prev_date,
                                              created_datetime__lt=next_date).order_by('created_datetime')
            response[RESPONSE_MESSAGE] = ""
            response[RESPONSE_STATUS] = STATUS_OK
            http_status = 200
            response[RESPONSE_DATA] = {
                "detail": [],
                "actual_this_month": 0,
                "actual_previous_month": 3000,
                "expected_this_month": 3600,
            }

            response[RESPONSE_DATA]["actual_this_month"] = utils.get_total_milk_yield_by_month(customer_id, prev_date,
                                                                                               next_date)
            last_month_next_date = last_day_of_month(next_date-timedelta(days=31))
            last_month_prev_date = str((last_month_next_date.replace(day=1)).date())
            last_month_prev_date = datetime.combine(dateparse.parse_date(last_month_prev_date), datetime.min.time())
            response[RESPONSE_DATA]["actual_previous_month"] = utils.get_total_milk_yield_by_month(customer_id,
                                                                                                   last_month_prev_date,
                                                                                                   last_month_next_date)
            if data:
                response[RESPONSE_DATA]["detail"] = [x.customer_milk_yield() for x in data]

        return generic_response(response_body=response, http_status=http_status)


from django.db.models.functions import TruncMonth


class AnimalMilkYieldMonthlyView(APIView):
    @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
    def get(self, request):
        response = {RESPONSE_STATUS: STATUS_ERROR,
                    RESPONSE_MESSAGE: DEFAULT_ERROR_MESSAGE}
        http_status = 400
        customer_id = (get_default_param(request, 'customer', None))

        if not customer_id:
            response[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        else:
            customer_id = int(customer_id)
            animals_data = Aggregation.objects.filter(customer_aggregations_id=customer_id,
                                                      animal_id__isnull=False,
                                                      feeding_value__isnull=True,
                                                      avg_milk_yield__isnull=False).\
                annotate(month=TruncMonth('created_datetime'))\
                .values('month', 'animal_id', 'animal__name', 'herd__name').annotate(total=Sum('avg_milk_yield'))\
                .order_by('-month')
            response[RESPONSE_MESSAGE] = ""
            response[RESPONSE_STATUS] = STATUS_OK
            http_status = 200
            response[RESPONSE_DATA] = []
            if animals_data:
                response[RESPONSE_DATA] = [{"animal_id": x['animal_id'],
                                            "name": x['animal__name'],
                                            "herd": x['herd__name'],
                                            "total": x['total'],
                                            "month": calendar.month_name[x['month'].month] + '/' + str(x['month'].year),
                                            "details": get_animals_milk_yield_monthly(customer_id,
                                                                                      x['month'],
                                                                                      x['animal_id'])}
                                           for x in animals_data]

        return generic_response(response_body=response, http_status=http_status)


class HerdMilkYieldMonthlyView(APIView):
    @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
    def get(self, request):
        response = {RESPONSE_STATUS: STATUS_ERROR,
                    RESPONSE_MESSAGE: DEFAULT_ERROR_MESSAGE}
        http_status = 400
        customer_id = (get_default_param(request, 'customer', None))
        if not customer_id:
            response[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        else:
            customer_id = int(customer_id)
            herds_data = Aggregation.objects.filter(customer_aggregations_id=customer_id,
                                                    animal_id__isnull=True,
                                                    herd_id__isnull=False,
                                                    feeding_value__isnull=True,
                                                    avg_milk_yield__isnull=False).\
                annotate(month=TruncMonth('created_datetime'))\
                .values('month', 'herd_id', 'herd__name').annotate(total=Sum('avg_milk_yield'))\
                .order_by('-month')
            response[RESPONSE_MESSAGE] = ""
            response[RESPONSE_STATUS] = STATUS_OK
            http_status = 200
            response[RESPONSE_DATA] = []
            if herds_data:
                response[RESPONSE_DATA] = [{"herd_id": x['herd_id'], "name":x['herd__name'], "total": x['total'],
                                            "month": calendar.month_name[x['month'].month] + '/' + str(x['month'].year),
                                            "details": get_herds_milk_yield_monthly(customer_id,
                                                                                    x['month'],
                                                                                    x['herd_id'])} for x in herds_data]
        return generic_response(response_body=response, http_status=http_status)


class HerdFeedYieldMonthlyView(APIView):
    @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
    def get(self, request):
        response = {RESPONSE_STATUS: STATUS_ERROR,
                    RESPONSE_MESSAGE: DEFAULT_ERROR_MESSAGE}
        http_status = 400
        customer_id = (get_default_param(request, 'customer', None))

        if not customer_id:
            response[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        else:
            customer_id = int(customer_id)
            herds_data = Aggregation.objects.filter(customer_aggregations_id=customer_id, animal_id__isnull=True,
                                                    herd_id__isnull=False, feeding_value__isnull=False,
                                                    avg_milk_yield__isnull=True).\
                annotate(month=TruncMonth('created_datetime')).values('month', 'herd_id', 'herd__name')\
                .annotate(total=Sum('feeding_value')).order_by('-month')

            response[RESPONSE_MESSAGE] = ""
            response[RESPONSE_STATUS] = STATUS_OK
            http_status = 200
            response[RESPONSE_DATA] = []
            if herds_data:
                response[RESPONSE_DATA] = [{"herd_id": x['herd_id'], "name": x['herd__name'], "total": x['total'],
                                            "month": calendar.month_name[x['month'].month]+'/'+str(x['month'].year),
                                            "details": get_herds_feed_yield_monthly(customer_id, x['month'],
                                                                                    x['herd_id'])} for x in herds_data]

        return generic_response(response_body=response, http_status=http_status)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_milk_yield_monthly(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: {}}
    customer = self.query_params["customer"]
    response_body[RESPONSE_DATA]['herd'] = list(herd_milk_yield_monthly(customer_id=customer))
    response_body[RESPONSE_DATA]['animal'] = list(animal_milk_yield_monthly(customer_id=customer))
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def feed_consumed_monthly(self):
    from django.utils import dateparse
    from datetime import datetime
    response = {RESPONSE_STATUS: STATUS_ERROR,
                RESPONSE_MESSAGE: DEFAULT_ERROR_MESSAGE}
    http_status = 400
    customer_id = self.query_params["customer"]
    if not customer_id:
        response[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
    else:
        created_date = self.query_params.get('created_date')
        if not created_date:
            created_date = str(datetime.now().date())
        created_date_time = datetime.combine(dateparse.parse_date(created_date), datetime.min.time())
        customer_id = int(customer_id)
        next_date = (last_day_of_month(created_date_time) + timedelta(hours=23, minutes=59, seconds=59))
        prev_date = created_date_time.replace(day=1)
        data = Aggregation.objects.filter(customer_aggregations_id=customer_id,
                                          herd_id__isnull=True,
                                          animal_id__isnull=True,
                                          avg_milk_yield__isnull=True,
                                          feeding_value__isnull=False,
                                          created_datetime__gt=prev_date,
                                          created_datetime__lt=next_date).order_by('created_datetime')
        response[RESPONSE_MESSAGE] = ""
        response[RESPONSE_STATUS] = STATUS_OK
        http_status = 200
        response[RESPONSE_DATA] = {
            "detail": [],
            "actual_this_month": 0,
            "actual_previous_month": 3000,
        }

        response[RESPONSE_DATA]["actual_this_month"] = utils.get_feed_consumed_by_month_customer(customer_id, prev_date,
                                                                                                 next_date)
        last_month_next_date = last_day_of_month(next_date - timedelta(days=31))
        last_month_prev_date = str((last_month_next_date.replace(day=1)).date())
        last_month_prev_date = datetime.combine(dateparse.parse_date(last_month_prev_date), datetime.min.time())
        response[RESPONSE_DATA]["actual_previous_month"] = utils.get_feed_consumed_by_month_customer(customer_id,
                                                                                                     last_month_prev_date,
                                                                                                     last_month_next_date)
        if data:
            response[RESPONSE_DATA]["detail"] = [x.customer_feed() for x in data]

    return generic_response(response_body=response, http_status=http_status)
