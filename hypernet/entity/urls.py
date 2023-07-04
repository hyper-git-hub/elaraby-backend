from .function_views import *
from .temp import *
from django.conf.urls import url, include
urlpatterns = [
    url(r'^add_new_entity', add_entity),
    url(r'^edit_entity', edit_entity),
    url(r'^fetch_entity', fetch_entity),
    url(r'^delete_entity', delete_entity),
    url(r'^check_entity_relations', check_entity_relations),
    url(r'^get_entity_type_dropdown/', get_entity_type_dropdown),  ##OK {customer}

    url(r'^get_drivers_list', get_drivers_list),
    #Testing APIs.
    url(r'^add_job', add_job),
    url(r'^edit_job', edit_job),

    url(r'^get_unassigned_trucks', get_unassigned_trucks),
    url(r'^get_unassigned_trucks_ter', get_unassigned_trucks_territory),

    url(r'^get_devices_dropdown', get_devices_dropdown),
    url(r'^hypernet_search_bar', hypernet_search_bar),

    url(r'^add_new_client', add_client),
    url(r'^edit_client', edit_client),
    url(r'^get_clients_list', get_clients_list),
    url(r'^delete_clients', delete_clients),

    url(r'^get_bins_list', get_bins_list),
    url(r'^get_contracts_listing', get_contracts_listing),
    url(r'^get_bins_contract_dropdown', get_contract_bins_clients),
    url(r'^get_bins_witout_contract', get_bins_witout_contract),
    url(r'^get_area_bins', get_unassigned_bins),
    url(r'^get_contract_bins', get_contract_bins),

    #NEW DROPDOWN CALL FOR UNASSIGNED ASSETS
    url(r'^get_unassigned_entity_dropdown', get_unassigned_entity_dropdown),
    url(r'^get_contract_details_dropdown', get_contract_details_dropdown),
    
    url(r'^get_contracts_list', get_contracts_list),
    url(r'^invoice_listing_filters', invoice_listing_filters),



    url(r'^V2/', include('hypernet.entity.job_V2.urls')),
]


discarded_urls = [
    # url(r'^add_assignment', add_assignment),
    # url(r'^edit_assignment', edit_assignment),
    # url(r'^delete_assignment', delete_assignment),
    # url(r'^get_assignment', fetch_assignments),
]
