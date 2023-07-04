from .function_views import *
from django.conf.urls import url, include

urlpatterns = [
    
    url(r'^maintenance', add_update_maintenance),
    url(r'^add_maintenance_data', add_maintenance_data),
    # url(r'^edit_entity', edit_entity),
]
