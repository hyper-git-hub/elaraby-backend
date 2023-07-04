from django.conf.urls import url, include
from ioa.function_views import *
import backend.settings as settings


urlpatterns =[

    # ALERTS
    url(r'^get_alert_graph_data/', get_alert_graph_data),  ##OK {animal/herd, customer, no_alerts}
    url(r'^get_alerts_count/', get_alerts_count),  ##OK {customer, days}
    url(r'^get_recent_alerts_pi/', get_recent_alerts_pi),  ##OK {days, customer}
    url(r'^get_user_alerts_dropdown/', get_user_notifications),  ##OK {user}


    url(r'^get_recent_alerts_detail/', get_recent_alerts_detail), ##OK {animal/herd, customer, no_alerts}
    url(r'^get_alerts_type/', get_alert_count_by_type),

    url(r'^update_alert_flag_status/', update_alert_flag),
    url(r'^update_alert_statues/', update_alerts_status),
    url(r'^create_entitites/', create_entitites),
    url(r'^create_devices/', create_devices),
    url(r'^alter_suez_data/', alter_suez_data),


    url(r'^get_scheduling_form_data/', get_scheduling_form_data),
    url(r'^aggregation/', include('ioa.aggregation.urls')),
    url(r'^activity/', include('ioa.activity.urls')),
    url(r'^animal/', include('ioa.animal.urls')),
    url(r'^staff/', include('ioa.caretaker.urls')),

    # ----- separate tests ------
    # url(r'^tests/', include('ioa.tests.urls')),
]

# if settings.DEBUG:
if settings.TESTS:
    urlpatterns = urlpatterns + [
        url(r'^tests/', include('ioa.tests.urls')),
    ]
