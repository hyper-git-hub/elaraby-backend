from django.conf.urls import url
from ioa.aggregation.views import *

urlpatterns = [
    url(r'^get_animal_milk_yield/', CowMilkYieldAggregation.as_view()),
    url(r'^get_herd_milk_yield/', HerdMilkYieldAggregation.as_view()),
    url(r'^get_herd_feed/', HerdFeedAggregation.as_view()),
    url(r'^get_customer_milk_yield/', CustomerMilkYieldAggregation.as_view()),
    url(r'^get_customer_feed/', CustomerFeedAggregation.as_view()),
    url(r'^get_top_herds/', TopHerdsAggregationView.as_view()),
    url(r'^get_top_animals/', TopAnimalsAggregationView.as_view()),
    url(r'^get_top_milk_yielder/', TopMilkYielderAggregationView.as_view()),

    url(r'^get_customer_milk_yield_monthly/', MilkYieldMonthlyView.as_view()),
    url(r'^get_animal_milk_yield_monthly/', AnimalMilkYieldMonthlyView.as_view()),
    url(r'^get_herd_milk_yield_monthly/', HerdMilkYieldMonthlyView.as_view()),
    url(r'^get_herd_feed_yield_monthly/', HerdFeedYieldMonthlyView.as_view()),
    url(r'^get_feed_consumed_monthly/', feed_consumed_monthly),

    url(r'^get_milk_yield_monthly/', get_milk_yield_monthly),
]
