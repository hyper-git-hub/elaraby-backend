from django.conf.urls import url, include
from .views import *

urlpatterns = [

    # ALERTS
    url(r'^send_email/', send_email),
]
