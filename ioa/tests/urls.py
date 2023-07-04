from ioa.tests.report_test import ReportViewInvoice, ReportViewTripSheet

__author__ = 'nahmed'

from django.conf.urls import url, include
from ioa.tests.test_animal import *

urlpatterns = [

    url(r'^violation_test/', animal_state_violation),
    url(r'^new_animal_signal_test/', animal_signal_test),
    url(r'^test_logging/', test_logging),
    url(r'^search_bar/', hypernet_search_bar),
    url(r'^csv_data/', data_to_csv),  ##OK
    url(r'^zenath_report/', ReportViewInvoice.as_view()),  ##OK
    url(r'^zenath_trips_report/', ReportViewTripSheet.as_view()),  ##OK
]
