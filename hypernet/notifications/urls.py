from django.conf.urls import url, include
from .views import *

urlpatterns = [

    url(r'^get_user_alerts_count', get_user_notifications),
    url(r'^update_alert_flag_status/', update_alert_flag),
    url(r'^update_notifications_count', update_notifications_count),
    url(r'^update_alert_status/', update_alert_status),

]
