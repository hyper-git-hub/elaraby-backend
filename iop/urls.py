from django.conf.urls import url
import iop.views as iop_views
from iop.crons.crons import energy_consumption, new_energy_consumption

urlpatterns =\
    [

    url(r'^get_iop_devices_count/', iop_views.get_iop_devices_count),
    url(r'^get_iop_devices_count_cards/', iop_views.get_iop_devices_count_cards),
    url(r'^get_iop_devices_sold_stats/', iop_views.get_iop_devices_sold_stats),
    url(r'^get_device_sold_stats_graph/', iop_views.get_device_sold_stats_graph),
    url(r'^get_device_usage_stats/', iop_views.get_device_usage_stats),
    url(r'^get_device_error_logs/', iop_views.get_device_error_logs),
    url(r'^graph_data_energy_active_duration/', iop_views.graph_data_energy_active_duration),
    url(r'^graph_data_energy_usage/', iop_views.new_graph_data_energy_active_duration),
    url(r'^get_device_listing_by_type/', iop_views.get_device_listing_by_type),
    url(r'^avg_errors_all_devices/', iop_views.avg_errors_all_devices),
    url(r'^avg_energy_all_devices/', iop_views.avg_energy_all_devices),
    url(r'^error_occuring_model/', iop_views.error_occuring_model),
    url(r'^most_sold_model/', iop_views.most_sold_model),
    url(r'^latest_data_iop_device/', iop_views.latest_data_iop_device),
    url(r'^get_sharing_code/', iop_views.get_sharing_code),
    url(r'^assigne_device_with_sharing_code/', iop_views.assigne_device_with_sharing_code),
    url(r'^manage_device_user_previliges/', iop_views.manage_device_user_previliges),
    url(r'^get_schedules_list/', iop_views.get_schedules_list),
    url(r'^energy_consumed_stats/', iop_views.energy_consumed_stats),
    url(r'^edit_appliance/', iop_views.edit_appliance),
    url(r'^get_single_appliance_details/', iop_views.get_single_appliance_details),
    url(r'^delete_appliance', iop_views.delete_appliance),
    url(r'^delete_device_frontend', iop_views.delete_appliance_frontend),
    url(r'^check_appliance_data', iop_views.check_appliance_data),
    url(r'^delete_user', iop_views.delete_user),
    url(r'^generate_qr_code/', iop_views.generate_qr_code),
    url(r'^save_appliance_details_for_qr/', iop_views.add_appliance_details_for_qr),
    url(r'^get_appliance_details_for_qr/', iop_views.get_appliance_details_for_qr),
    url(r'^deletion_qr_code/', iop_views.deletion_qr_code),
    url(r'^get_online_status_iop_device/', iop_views.get_online_status_iop_device),
    url(r'^get_quick_schedules/', iop_views.get_quick_schedules),
    url(r'^delete_schedule/', iop_views.delete_schedule),


    url(r'^energy_consumption_chron/', new_energy_consumption),
    url(r'^get_energy_consumed_graph/', iop_views.get_energy_consumed_graph),
    url(r'^get_temperature_graph/', iop_views.get_temperature_graph),
    url(r'^get_density_reporting_graph/', iop_views.get_density_reporting_graph),
    url(r'^get_events_created_graph/', iop_views.get_events_created_graph),
    url(r'^get_device_day_stats/', iop_views.get_device_day_stats),
    url(r'^sleep_mode_listing/', iop_views.sleep_mode_listing),

    ]

