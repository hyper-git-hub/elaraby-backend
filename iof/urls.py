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
    customer_dashboard, trip_sheet_reporting, invoice_reporting, check_count, manual_fillup, get_contracts_list, \
    post_renew_contract, invoice_listing, update_payment_status, add_fine, last_shift_data, vehicles_dashboard_reporting
from iof.wrappers_waleed import zooming_report_bins, drill_down_report, zooming_report_bins_new, \
    map_trail, snapshot, maintenance_details, get_fillups_list, get_violations_list, get_maintenance_summary, \
    get_territory_info, get_review_form_data, edit_activity, shift_reporting, check_invalid_assignments, \
    delete_invalid_assignment, migrate_skip_size, delete_invalid_assignments_by_tag, check_tags_without_bins, \
    get_tag_from_name, construct_clean_assignments, vehicle_summary, get_decantations_list, maintenance_data_of_entity, \
    maintenance_of_entity, truck_reporting_cms
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
    get_last_job, get_rfid_scanner_truck, \
    driver_shift_activity_status, \
    shift_login, \
    manual_waste_collection, e2e_actions, get_e2e_packages

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
    url(r'^get_decantations', get_decantations_list),
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
    url(r'^get_tag_from_name', get_tag_from_name),

    url(r'driver_shift_activity_status', driver_shift_activity_status),
    url(r'customer_dashboard', customer_dashboard),
    url(r'trip_sheet_reporting', trip_sheet_reporting),
    url(r'invoice_reporting', invoice_reporting),
    url(r'check_invalid_assignments', check_invalid_assignments),
    url(r'delete_invalid_assignment', delete_invalid_assignment),
    url(r'check_count', check_count),
    url(r'migrate_skip_size', migrate_skip_size),
    url(r'tag_assignments_delete', delete_invalid_assignments_by_tag),
    url(r'check_tags_without_bins', check_tags_without_bins),
    url(r'construct_clean_assignments', construct_clean_assignments),
    url(r'vehicle_summary', vehicle_summary),
    url(r'manual_fillup', manual_fillup),
    url(r'shift_login', shift_login),
    url(r'maintenance_data_of_entity', maintenance_data_of_entity),
    url(r'maintenance_of_entity', maintenance_of_entity),
    url(r'manual_waste_collection', manual_waste_collection),
    url(r'get_contracts_list', get_contracts_list),
    url(r'post_renew_contract', post_renew_contract),
    url(r'invoice_listing', invoice_listing),
    url(r'update_payment_status', update_payment_status),
    url(r'add_fine', add_fine),
    url(r'last_shift_data', last_shift_data),
    url(r'vehicles_dashboard_reporting', vehicles_dashboard_reporting),

    url(r'truck_reporting_cms', truck_reporting_cms),

    
    # For e2e TODO: Remove later
    url(r'e2e_actions', e2e_actions),
    url(r'get_e2e_packages', get_e2e_packages),

]