from django.conf.urls import url
from ioa.animal.views import *

urlpatterns =[
    url(r'^save_animal/', AnimalControl.as_view()),
    url(r'^get_all_animal/', get_all_animals),
    url(r'^delete_animal/(?P<pk>[0-9]+)/$', AnimalControl.as_view()),
    url(r'^update_animal/(?P<pk>[0-9]+)/$', AnimalControl.as_view()),
    url(r'^get_animal/(?P<pk>[0-9]+)/$', AnimalControl.as_view()),
    url(r'^get_animal_today_alerts_count/', get_animal_today_alerts_count),  ##OK {animal, customer}
    url(r'^get_animal_groups/', get_animal_groups),  ##OK {customer}
    url(r'^get_total_animals/', get_total_animals),  ##OK {customer}
    url(r'^get_animals_by_group/', get_animals_by_group),  ##OK {group, customer}
    url(r'^get_animals_by_status/', get_animals_by_status),  ##OK {group, customer}

    url(r'^get_herd_information/', get_herd_information),  ##OK {customer}

    # TODO Remove these urls after front-end change
    url(r'^get_entity_type_dropdown/', get_entity_type_dropdown),  ##OK {customer}
    url(r'^get_devices_dropdown/', get_devices_dropdown),  ##OK {customer}
    #TODO

    url(r'^get_total_herds/', get_total_herds),  ##OK {customer}
    url(r'^get_herd_alerts/', get_herd_alerts_date),  ##OK {customer, herd}

    url(r'^get_animal_detail/', get_animal_detail), ##OK {animal/herd, customer}

    url(r'^get_animal_page_details/', get_animal_milk_yield_and_details),
    url(r'^get_animal_activities/', get_animal_activities),
    url(r'^get_animal_milk_yield/', get_animal_milk_cow_page),
    url(r'^get_statistics/', AnimalStats.as_view()),

]