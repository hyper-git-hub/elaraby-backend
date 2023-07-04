from __future__ import unicode_literals
from rest_framework.decorators import api_view
import datetime
from hypernet import constants
from hypernet.utils import *
from hypernet.constants import ERROR_RESPONSE_BODY


###Wrappers for Truck and Fleet###
# Does not work, neeeds review
''''

# Does not work, neeeds review
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_truck_fleet_maintenance(request):
    c_id = get_default_param(request, 'customer_id', None)
    t_id = get_default_param(request, 'truck_id', None)
    f_id = get_default_param(request, 'fleet_id', None)
    d_id = get_default_param(request, 'driver_id', None)
    start_datetime = get_default_param(request, 'start_datetime', None)
    end_datetime = get_default_param(request, 'end_datetime', None)
    result = {}
    today = datetime.date.today()
    last_thirty_days = today - datetime.timedelta(days = 30)
    if c_id:
        result['total_maintenances'] = get_maintenances(c_id, f_id, t_id, start_datetime, end_datetime).count()
        result['maintenaces_last_thirty_days'] = get_maintenances(c_id, f_id, t_id, start_datetime, end_datetime).filter(timestamp__gte = last_thirty_days).count()
        result['maintenance_list'] = get_maintenances(c_id, f_id, t_id, start_datetime, end_datetime).values('maintenance_type__name','device__name','timestamp')
    else:
        return generic_response(response_json(False, None, constants.TEXT_PARAMS_MISSING), http_status=500)
    return generic_response(response_json(True, result))

'''

