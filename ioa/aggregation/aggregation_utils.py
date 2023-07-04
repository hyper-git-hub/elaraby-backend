from ioa.utils import *  # too wild, cannot see where the timedelta was coming from
# from datetime import timedelta
from django.db.models import Sum
# from ioa.models import Aggregation


def get_total_milk_yield_by_month(c_id, prev_date, next_date):
    total = 0
    data = Aggregation.objects.filter(customer_aggregations_id=c_id,
                                      herd_id__isnull=True,
                                      animal_id__isnull=True,
                                      feeding_value__isnull=True,
                                      created_datetime__gt=prev_date,
                                      created_datetime__lt=next_date)
    if data.count() > 0:
        total_milk_yield = data.values('customer_aggregations_id').annotate(milk_yield=Sum('avg_milk_yield'))
        total = total_milk_yield[0]['milk_yield']

    return total

def milk_yield_aggregation_by_cow(customer_id, cow_id, created_date_time, days=None):
    """
    :param customer_id:
    :param cow_id:
    :param created_date_time:
    :param days:
    :return:
    """

    if days:
        days = int(days)
        prev_date = created_date_time - timedelta(days=days)  # , hours=23, minutes=59, seconds=59)
        next_date = created_date_time + timedelta(hours=23, minutes=59, seconds=59)
        data = Aggregation.objects.filter(customer_aggregations_id=customer_id,
                                          animal_id=cow_id,
                                          created_datetime__gt=prev_date,
                                          created_datetime__lte=next_date)
        if data:
            total_milk_yield = data.values('animal_id').annotate(total=Sum('avg_milk_yield'))
            return {"animal_id": total_milk_yield[0]['animal_id'],
                                               "milk_yield": total_milk_yield[0]['total']}
    else:
        prev_date = created_date_time - timedelta(days=1, hours=23, minutes=59, seconds=59)
        next_date = created_date_time + timedelta(days=1)
        data = Aggregation.objects.filter(customer_aggregations_id=customer_id,
                                          animal_id=cow_id,
                                          created_datetime__gt=prev_date,
                                          created_datetime__lt=next_date)
        if data.count() > 0:
            return data[0].animal_milk_yield()


def milk_yield_aggregation_by_herd(c_id, h_id, prev_date, next_date):
    """
    TODO: if any commonality between the cases - have the annotation here and than return the data
    TODO: shift it to the main utils
    TODO: combine the milk_yield_aggregations - using flags, and kwargs

    :param c_id:
    :param h_id:
    :param prev_date:
    :param next_date:
    :return:
    """

    data = Aggregation.objects.filter(customer_aggregations_id=c_id,
                                      herd_id=h_id,
                                      animal_id__isnull=True,
                                      created_datetime__gt=prev_date,
                                      created_datetime__lt=next_date)

    return data

def milk_yield_aggregation_by_customer(c_id, prev_date, next_date):
    """

    :param c_id:
    :param prev_date:
    :param next_date:
    :return:
    """
    data = Aggregation.objects.filter(customer_aggregations=c_id,
                                      herd_id__isnull=True,
                                      animal_id__isnull=True,
                                      created_datetime__gt=prev_date,
                                      created_datetime__lt=next_date)

    return data

def feed_aggregation_by_herd(c_id, h_id, prev_date, next_date):
    """

    :param c_id:
    :param h_id:
    :param prev_date:
    :param next_date:
    :return:
    """
    data = Aggregation.objects.filter(customer_aggregations_id=c_id,
                                      herd_id=h_id,
                                      animal_id__isnull=True,
                                      feeding_value__isnull=False,
                                      created_datetime__gt=prev_date,
                                      created_datetime__lt=next_date)
    return data

def feed_aggregation_by_customer(c_id, prev_date, next_date):
    """

    :param c_id:
    :param prev_date:
    :param next_date:
    :return:
    """
    data = Aggregation.objects.filter(customer_aggregations_id=c_id,
                                      herd_id__isnull=True,
                                      animal_id__isnull=True,
                                      feeding_value__isnull=False,
                                      created_datetime__gt=prev_date,
                                      created_datetime__lt=next_date)
    return data

def get_top_herds_aggregation(customer_id, prev_date, next_date, limit, feed_consumed=None):
    """

    :param c_id:
    :param prev_date:
    :param next_date:
    :param limit:
    :param feed_consumed:
    :return:
    """
    if feed_consumed:
        data = Aggregation.objects.filter(customer_aggregations_id=customer_id,
                                          herd_id__isnull=False,
                                          animal_id__isnull=True,
                                          avg_milk_yield__isnull=True,
                                          created_datetime__gt=prev_date,
                                          created_datetime__lt=next_date)
        if data:
            total_feed_yield = data.values('herd_id', 'herd__name').annotate(feed_consumed=Sum('feeding_value')
                                                                            ).order_by('-feed_consumed')[:limit]
            return [get_json_queryset(x, 'herd_id', 'herd__name', 'feed_consumed') for x in total_feed_yield]
    else:
        data = Aggregation.objects.filter(customer_aggregations_id=customer_id,
                                          herd_id__isnull=False,
                                          animal_id__isnull=True,
                                          feeding_value__isnull=True,
                                          created_datetime__gt=prev_date,
                                          created_datetime__lt=next_date)
        if data:
            total_feed_yield = data.values('herd_id','herd__name').annotate(
                milk_yield=Sum('avg_milk_yield')).order_by('-milk_yield')[:limit]
            return [get_json_queryset(x, 'herd_id', 'herd__name', 'milk_yield') for x in total_feed_yield]

def get_top_animals_aggregation(customer_id, created_date_time, limit):
    """

    :param customer_id:
    :param created_date_time:
    :param limit:
    :return:
    """
    next_date = (last_day_of_month(created_date_time)+timedelta(hours=23, minutes=59, seconds=59))
    prev_date = created_date_time.replace(day=1)
    data = Aggregation.objects.filter(customer_aggregations_id=customer_id,
                                      herd_id__isnull=False,
                                      animal_id__isnull=False,
                                      feeding_value__isnull=True,
                                      created_datetime__gt=prev_date,
                                      created_datetime__lt=next_date)
    if data:
        total_milk_yield = data.values('animal_id', 'animal__name').annotate(
            milk_yield=Sum('avg_milk_yield')).order_by('-milk_yield')[:limit]
        return [get_json_queryset(x, 'animal_id', 'animal__name', 'milk_yield') for x in total_milk_yield]
    else:
        return []  # see if necessary as previously - response[RESPONSE_DATA] = [] before data update


def get_feed_consumed_by_month_customer(c_id, prev_date, next_date):
    total = 0
    data = Aggregation.objects.filter(customer_aggregations=c_id,
                                      herd_id__isnull=True,
                                      animal_id__isnull=True,
                                      feeding_value__isnull=False,
                                      avg_milk_yield__isnull=True,
                                      created_datetime__gt=prev_date,
                                      created_datetime__lt=next_date)
    if data.count() > 0:
        total_feed_consumed = data.values('customer_aggregations_id').annotate(feed_consumed=Sum('feeding_value'))
        total = total_feed_consumed[0]['feed_consumed']

    return total
