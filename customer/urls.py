from .views import *
from django.conf.urls import url, include

urlpatterns = [
    url(r'^get_preferences', get_preferences),
    url(r'^modify_preferences', modify_preferences),
]
