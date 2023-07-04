# from ioa.tests.iot_hub_cloud_to_device import send_message_to_device_api
from ioa.tests.report_test import ReportViewInvoice, ReportViewTripSheet, ReportViewTrucks, ReportViewActivities

__author__ = 'nahmed'

from django.conf.urls import url, include
from ioa.tests.test_animal import *
#from ioa.tests.iot_hub_cloud_to_device import *

urlpatterns = [

    url(r'^violation_test/', animal_state_violation),
    url(r'^new_animal_signal_test/', animal_signal_test),
    url(r'^test_logging/', test_logging),
    url(r'^search_bar/', hypernet_search_bar),
    url(r'^csv_data/', data_to_csv),  ##OK
    url(r'^zenath_report/', ReportViewInvoice.as_view()),  ##OK
    url(r'^zenath_trips_report/', ReportViewTripSheet.as_view()),  ##OK
    url(r'^zenath_trucks_report/', ReportViewTrucks.as_view()),  ##OK
    url(r'^test_post_iot_hub/', test_post_iot_hub),  ##OK
   #  url(r'^send_message_to_device_api/', send_message_to_device_api),  ##OK
   # url(r'^temporary_sign_up_hypernet/', temporary_sign_up_hypernet),  ##OK
    url(r'^evaluate_apis/', evaluate_apis),  ##OK
    url(r'^zenath_activity_report/', ReportViewActivities.as_view()),  ##OK
    url(r'^save_contract_location_ass/', save_contract_location_ass),  ##OK
    url(r'^upload_data_cms', upload_data_cms),  ##OK
    url(r'^clean_data_duplicate_bins/', clean_data_duplicate_bins),  ##OK
    url(r'^create_cms_entities/', create_cms_entities),
    url(r'^change_customer_devices/', change_customer_devices),
    url(r'^create_new_customer_device/', create_new_customer_device),
]
