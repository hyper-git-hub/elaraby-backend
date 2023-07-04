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
from django.conf.urls import url
from django.contrib import admin
# from iof.wrappers import get_bins_summary, \
#     get_bins_list, \
#     get_bin

from iof.generic_wrappers import get_generic_entities_summary, \
    get_generic_entities_list, get_entity_calibration, get_generic_entity_info, get_entities_list, get_job_details, \
    get_generic_person_info, get_jobs_details_list, get_drivers_list, get_assets_details, \
    customer_dashboard, trip_sheet_reporting, invoice_reporting
from iof.wrappers_waleed import zooming_report_bins, drill_down_report, zooming_report_bins_new, \
    map_trail, snapshot, maintenance_details, get_fillups_list, get_violations_list, get_maintenance_summary, \
    get_territory_info, get_review_form_data, edit_activity, shift_reporting
from iof.views import get_app_jobs, \
    get_driver_info, \
    DriverJobUpdate, \
    get_notifications, \
    MaintenanceUpdate, \
    get_app_maintenances, \
    get_rfid_scan_admin, \
    get_rfid_scan_driver, \
    get_rfid_card_tag_scan_admin, \
    update_rfid_scan_driver, \
    report_incident, \
    incident_report_list, \
    get_last_job, get_rfid_scanner_truck,\
    driver_shift_activity_status

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^zooming_report_new$',zooming_report_bins_new),
    url(r'^zooming_report$',zooming_report_bins),
    url(r'^map_trail$',map_trail),
    url(r'^drill_report', drill_down_report),

    url(r'^entities_summary', get_generic_entities_summary),
    url(r'^entity_calibration/(?P<entity_id>\d+)$', get_entity_calibration),
    url(r'^entities/(?P<entity_id>\d+)$', get_generic_entity_info),
    url(r'^get_person_info/(?P<person_id>\d+)$', get_generic_person_info),
    url(r'^entities$', get_generic_entities_list),
    url(r'^get_app_jobs', get_app_jobs),
    url(r'^get_driver_info', get_driver_info),
    url(r'^get_notifications', get_notifications),

    url(r'^get_entities_list/', get_entities_list),
    url(r'^get_assets_details/', get_assets_details),

    url(r'^get_job_details/', get_job_details),

    url(r'^driver_job_update', DriverJobUpdate.as_view()),
    url(r'^maintenance_update', MaintenanceUpdate.as_view()),
    url(r'^get_app_maintenances', get_app_maintenances),
    url(r'^get_snapshot', snapshot),
    url(r'^maintenance_details', maintenance_details),
    url(r'^get_fillups', get_fillups_list),
    url(r'^get_violations_list', get_violations_list),
    url(r'^get_maintenance_summary', get_maintenance_summary),
    url(r'^get_territory_info', get_territory_info),
    url(r'^get_jobs_details_list', get_jobs_details_list),
    url(r'^get_review_form_data', get_review_form_data),
    url(r'^edit_activity', edit_activity),
    
    url(r'^get_rfid_scan_driver', get_rfid_scan_driver),
    url(r'^get_rfid_scan_admin', get_rfid_scan_admin),
    url(r'^get_rfid_card_tag_scan_admin', get_rfid_card_tag_scan_admin),
    url(r'^update_rfid_scan_driver', update_rfid_scan_driver),
    url(r'^get_rfid_scanner_truck', get_rfid_scanner_truck),
    url(r'^report_incident', report_incident),
    url(r'^incident_report_list', incident_report_list),
    url(r'^get_drivers_list', get_drivers_list),
    url(r'^get_last_job', get_last_job),
    url(r'^shift_reporting', shift_reporting),

    url(r'driver_shift_activity_status', driver_shift_activity_status),
    url(r'customer_dashboard', customer_dashboard),
    url(r'trip_sheet_reporting', trip_sheet_reporting),
    url(r'invoice_reporting', invoice_reporting)


]