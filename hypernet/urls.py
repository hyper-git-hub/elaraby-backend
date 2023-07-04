"""Hypernet URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include

from hypernet.entity.function_views import *
from .cron_task import process_pre_data, logistics_truck_aggregation, process_logistics_truck_data, \
    process_logistics_bin_data, logistics_bin_aggregation, save_logistic_notification, check_maintenance_overdue, \
    schedule_activity, send_notification, schedule_activity2, remove_notifications
from .views import *

urlpatterns = [
    url(r'^data',HypernetDataIngestion.as_view()),
    url(r'^queued_data',HypernetQueuedDataIngestion.as_view()),
    url(r'^testing_cron',logistics_truck_aggregation),
    url(r'^testing_cr_1',process_logistics_truck_data),
    url(r'^testing_cr_2',process_logistics_bin_data),
    url(r'^testing_cr_3',logistics_bin_aggregation),
    url(r'^testing_cr_4',process_pre_data),
    url(r'^testing_cr_5',save_logistic_notification),
    url(r'^testing_cr_6', check_maintenance_overdue),
    url(r'^testing_cr_7', schedule_activity),
    url(r'^testing_cr_8', send_notification),
    url(r'^bin/(?P<bin_id>\d+)$',GetEntity.as_view()),
    url(r'^testing_cr_9', schedule_activity2),
    url(r'^testing_cr', remove_notifications),
    # Notifications calls
    url(r'^notifications/', include('hypernet.notifications.urls')),

    # Entity calls
    url(r'^entity/', include('hypernet.entity.urls')),

    url(r'^customer/', include('customer.urls')),
    
            ]
