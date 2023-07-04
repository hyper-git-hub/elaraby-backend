from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from ffp.reporting_utils import util_get_assets_count, util_get_sites_details, util_get_individual_site_details, \
    util_get_individual_zone_details, get_employee_subordinates, violations_list, create_zones_list, \
    get_attendance_record, \
    get_employee_supervisor, calculate_emp_durations_site_active, \
    calculate_emp_durations_zone_active, calculate_emp_durations_site, \
    calculate_emp_durations_zone, util_get_emp_over_time, util_graphical_data_productivity, util_get_ranked_sites, \
    get_employee_todays_data, get_sites_zones_of_employee
from hypernet.constants import ERROR_RESPONSE_BODY, HTTP_SUCCESS_CODE, RESPONSE_STATUS, RESPONSE_DATA, RESPONSE_MESSAGE, \
    TEXT_OPERATION_SUCCESSFUL, TEXT_PARAMS_MISSING, HTTP_ERROR_CODE, GRAPH_DATE_FORMAT, NO_DATA_TO_DISPLAY
from hypernet.utils import exception_handler, generic_response
import hypernet.utils as h_utils
from .serializers import ViolationSerializer
from hypernet.serializers import ZoneSerializer
from hypernet.models import Entity
from hypernet.enums import FFPOptionsEnum
from django.utils import timezone
from ffp.models import AttendanceRecord
@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_assets_count(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
    cust = h_utils.get_customer_from_request(self, None)
    http_status = HTTP_SUCCESS_CODE
    if cust:
        response_body[RESPONSE_DATA] = util_get_assets_count(c_id=cust)
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    else:
        response_body[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE

    return generic_response(response_body=response_body, http_status=http_status)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_sites_listing_dashboard(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
    cust = h_utils.get_customer_from_request(self, None)
    start_date = h_utils.get_default_param(self, 'start_date', None)
    end_date = h_utils.get_default_param(self, 'end_date', None)

    http_status = HTTP_SUCCESS_CODE
    if cust:
        response_body[RESPONSE_DATA] = util_get_sites_details(c_id=cust, s_date=start_date, e_date=end_date)
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    else:
        response_body[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE

    return generic_response(response_body=response_body, http_status=http_status)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_ranked_sites(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: {}}
    cust = h_utils.get_customer_from_request(self, None)
    start_date = h_utils.get_default_param(self, 'start_date', None)
    end_date = h_utils.get_default_param(self, 'end_date', None)

    http_status = HTTP_SUCCESS_CODE
    if cust:
        top, last = util_get_ranked_sites(c_id=cust, s_date=start_date, e_date=end_date)
        response_body[RESPONSE_DATA]['top'] = top
        # response_body[RESPONSE_DATA]['worst'] = last
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    else:
        response_body[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE

    return generic_response(response_body=response_body, http_status=http_status)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_site_details(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
    cust = h_utils.get_customer_from_request(self, None)
    site = h_utils.get_default_param(self, 'site_id', None)
    start_date = h_utils.get_default_param(self, 'start_date', None)
    end_date = h_utils.get_default_param(self, 'end_date', None)
    http_status = HTTP_SUCCESS_CODE
    if site and cust:
        response_body[RESPONSE_DATA] = util_get_individual_site_details(c_id=cust, s_id=site, s_date=start_date, e_date=end_date)
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    else:
        response_body[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE

    return generic_response(response_body=response_body, http_status=http_status)


# @csrf_exempt
# @api_view(['POST'])
# @permission_classes((AllowAny, ))
# @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
# def post_data_ffp_dummy(self):
#     response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
#     lat = h_utils.get_default_param(self, 'lat', None)
#     lng = h_utils.get_default_param(self, 'lng', None)
#     http_status = HTTP_SUCCESS_CODE
#     if lat and lng:
#         response_body[RESPONSE_DATA] = util_post_dummy_data_ffp(lat=lat, lng=lng)
#         response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
#         response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
#     else:
#         response_body[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
#         response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
#
#     return generic_response(response_body=response_body, http_status=http_status)
#

@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_zone_details(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
    cust = h_utils.get_customer_from_request(request, None)
    zone_id = h_utils.get_default_param(request, 'zone_id', None)
    start_date = h_utils.get_default_param(request, 'start_date', None)
    end_date = h_utils.get_default_param(request, 'end_date', None)

    http_status = HTTP_SUCCESS_CODE
    if zone_id and cust:
        response_body[RESPONSE_DATA] = util_get_individual_zone_details(c_id=cust, z_id=zone_id, s_date=start_date, e_date=end_date)
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    else:
        response_body[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE

    return generic_response(response_body=response_body, http_status=http_status)

@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def employee_subordinates(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
    cust = h_utils.get_customer_from_request(request, None)
    employee_id = h_utils.get_default_param(request, 'employee_id', None)
    http_status = HTTP_SUCCESS_CODE
    if employee_id and cust:
        response_body[RESPONSE_DATA] = get_employee_subordinates(employee_id = employee_id)
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    else:
        response_body[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def violations_dashboard(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
    cust = h_utils.get_customer_from_request(request, None)
    site = h_utils.get_default_param(request, 'site', None)
    zones_list = h_utils.get_list_param(request,'zones', None)
    start_datetime = h_utils.get_default_param(request,'start_datetime', None)
    end_datetime = h_utils.get_default_param(request,'end_datetime', None)
    e_id = h_utils.get_default_param(request,'e_id', None)
    http_status = HTTP_SUCCESS_CODE
    out_of_zone=0
    out_of_site=0
    inactive_violations=0
    final_result = {}

    if e_id:
        result = violations_list(None, None, e_id, None, None).filter(active_status=None, created_datetime__date = timezone.now().date())
        # result = result.filter(violations_dtm__date__gte = timezone.now().date(), violations_dtm__date__lte = timezone.now().date())
        result = result.order_by('-violations_dtm')
    if site and start_datetime and end_datetime:
        result = violations_list(site, None, None, start_datetime, end_datetime)

    if site and zones_list and start_datetime and end_datetime:
        result = violations_list(site, zones_list, None, start_datetime, end_datetime)

    for obj in result:
        if obj.violations_type.id == FFPOptionsEnum.OUT_OF_ZONE:
            out_of_zone+=1
        if obj.violations_type.id == FFPOptionsEnum.OUT_OF_SITE:
            out_of_site +=1
        if obj.active_status == False:
            inactive_violations +=1
    violations = ViolationSerializer(result, many=True)
    final_result['result'] = violations.data
    print(type(result))
    final_result['out_of_zone'] = out_of_zone
    final_result['out_of_site'] = out_of_site
    final_result['inactive_violations'] = inactive_violations
    final_result['total'] = result.count()
    response_body[RESPONSE_DATA] = final_result
    response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
    response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    return generic_response(response_body=response_body, http_status=http_status)



@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def site_zone_dropdown(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
    cust = h_utils.get_customer_from_request(request, None)
    site = h_utils.get_default_param(request, 'site', None)
    #print('Site is: ',site)
    http_status = HTTP_SUCCESS_CODE
    if site:
        zones = create_zones_list(site)
        #print('Zones are: ', zones)
        zones_entity = Entity.objects.filter(id__in=zones)
        result = ZoneSerializer(zones_entity, many=True)
        response_body[RESPONSE_DATA] = result.data
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    else:
        response_body[RESPONSE_DATA] = None
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def performance_analysis(request):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
    cust = h_utils.get_customer_from_request(request, None)
    e_id = h_utils.get_default_param(request, 'e_id', None)
    start_datetime = h_utils.get_default_param(request, 'start_datetime', None)
    end_datetime = h_utils.get_default_param(request, 'end_datetime', None)
    user = h_utils.get_user_from_request(request,None)
    http_status = HTTP_SUCCESS_CODE
    if e_id:
        r_list = []
        a_records = get_attendance_record(e_id,cust, start_datetime,end_datetime)
        for obj in a_records:
            r_dict = {}
            r_dict['clock_in_time'] = obj.site_checkin_dtm
            r_dict['clock_out_time'] = obj.site_checkout_dtm
            r_dict['site'] = obj.site.name
            r_dict['zone'] = obj.zone.name
            r_dict['date'] = obj.created_datetime
            r_dict['productive_hours'] = obj.productive_hours
            r_dict['zone_hrs'] = round(obj.duration_in_zone/60,0) if obj.duration_in_zone else None
            r_dict['active_hrs'] = round(obj.duration_in_site_active if obj.duration_in_site_active else 0, 0)
            r_dict['supervisor'] = get_employee_supervisor(e_id,cust, user=user)
            r_dict['employee_role'] = obj.employee.entity_sub_type.label
            r_dict['over_time'] = util_get_emp_over_time(e_id, obj.site, obj.zone, cust, obj)
            r_dict['violations'] = violations_list(None,None,e_id, None, None).filter(violations_dtm__date = obj.created_datetime.date(), violations_type_id__in=[FFPOptionsEnum.OUT_OF_SITE,
                                                                                                                                FFPOptionsEnum.OUT_OF_ZONE]).count()
            r_list.append(r_dict)
        response_body[RESPONSE_DATA] = r_list
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        return generic_response(response_body=response_body, http_status=http_status)



@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def employee_durations(request):
    from ffp.reporting_utils import calculate_emp_productivity
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
    e_id = h_utils.get_default_param(request, 'e_id', None)
    http_status = HTTP_SUCCESS_CODE
    if e_id:
        response_body[RESPONSE_DATA] = get_employee_todays_data(e_id=e_id)
        response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
        response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    else:
        response_body[RESPONSE_DATA] = None
        response_body[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE

    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def graph_data_productivity(request):
    from ffp.reporting_utils import  calculate_emp_productivity
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
    cust = h_utils.get_customer_from_request(request, None)
    site_id = h_utils.get_default_param(request, 'site_id', None)
    zone_id = h_utils.get_default_param(request, 'zone_id', None)
    employee = h_utils.get_default_param(request, 'employee_id', None)
    group_by = h_utils.get_default_param(request, 'group_by', None)
    start_datetime = h_utils.get_default_param(request, 'start_date', None)
    end_datetime = h_utils.get_default_param(request, 'end_date', None)
    group_by = "%H" if group_by == "hour" else GRAPH_DATE_FORMAT
    http_status = HTTP_SUCCESS_CODE

    response_body[RESPONSE_DATA] = util_graphical_data_productivity(site_id=site_id, z_id=zone_id, emp_id=employee, start_datetime=start_datetime, end_datetime=end_datetime, group_by=group_by)
    response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
    response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    return generic_response(response_body=response_body, http_status=http_status)



@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def zones_of_site(request):
    from ffp.reporting_utils import  calculate_emp_productivity
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: []}
    cust = h_utils.get_customer_from_request(request, None)
    e_id = h_utils.get_default_param(request, 'e_id', None)
    print("Employee id is: ", e_id)
    http_status = HTTP_SUCCESS_CODE
    result = []
    emps = get_sites_zones_of_employee(e_id)
    for obj in emps:
        dict = {}
        dict['zone_name'] = obj.child.name
        dict['zone_geo_fence'] = obj.child.territory
        result.append(dict)
    response_body[RESPONSE_DATA] = result
    response_body[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
    response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
    return generic_response(response_body=response_body, http_status=http_status)
