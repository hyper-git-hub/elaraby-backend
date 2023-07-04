from datetime import timedelta
from django.db.models import Q, Avg, F, Sum

from customer.models import CustomerPreferences
from ffp.models import AttendanceRecord, EmployeeViolations, FFPDataDailyAverage
from ffp.reporting_utils import create_violation_data

__author__ = 'SyedUsman'
__version__ = '0.1'

from ast import literal_eval
from shapely.geometry import Point, Polygon
from shapely.ops import cascaded_union
from django.utils import timezone
from itertools import zip_longest

from hypernet.enums import DeviceTypeAssignmentEnum, DeviceTypeEntityEnum, OptionsEnum, FFPOptionsEnum
from hypernet.models import Assignment, Entity, HypernetNotification, HypernetPostData, HypernetPreData
from user.models import User
from user.enums import RoleTypeEnum

def get_geofence_violations(pre_data_obj):
    '''
    METHOD TO CHECK THE GEOFENCE VIOLATIONS.  ***[OUT OF GEOFENCE ONLY]***.
    :param pre_data_obj:
    :return: boolean value {If true-> out of zone violation has occured else-> None}
    '''

    if pre_data_obj.latitude and pre_data_obj.longitude:
        current_pt = Point(pre_data_obj.latitude,
                           pre_data_obj.longitude)
        print('Current_location [Polygon ops]\n')
        print(current_pt)
        pointList = []
        try:
            zone = Assignment.objects.get(child=pre_data_obj.device, type_id=DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT, status_id=OptionsEnum.ACTIVE)
            if zone:
                for p in literal_eval(zone.parent.territory):
                    pointList.append(Point(p['lat'], p['lng']))
                poly = Polygon([[p.x, p.y] for p in pointList])
                #FIXME [Manage True/False returns]
                if not poly.contains(current_pt):
                    print('out of zone' + pre_data_obj.device.name)
                    return True
                elif poly.contains(current_pt):
                    print('in zone' + pre_data_obj.device.name)
                    return False

            else:
                return False
        except Exception as e:
            print(e)
            return False
    else:
        return False


def get_employee_attendance(pre_data_obj):
    '''
    Attendance determination for laborers and Zone supervisors ONLY.
    :param pre_data_obj: Will be switched to PostData Object.
    :return [True/False] if Present True else False:
    '''
    # gmaps = googlemaps.Client(key=GOOGLE_API_KEY)
    # Geocoding an address
    if pre_data_obj.latitude and pre_data_obj.longitude:
        device_location = str(pre_data_obj.latitude)+','+str(pre_data_obj.longitude)
        # geocode_result = gmaps.geocode(device_location)
        current_pt = Point(pre_data_obj.latitude,
                           pre_data_obj.longitude)
        print('Current_location [Polygon ops]\n')
        print('X:', current_pt.x)
        print('Y:', current_pt.y)
        try:
            zone_of_employee = Assignment.objects.get(child=pre_data_obj.device, type_id=DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT, status_id=OptionsEnum.ACTIVE)
            site_of_zone = Assignment.objects.get(child=zone_of_employee.parent, type_id=DeviceTypeAssignmentEnum.SITE_ZONE_ASSIGNMENT, status_id=OptionsEnum.ACTIVE)
            zones_of_site = Assignment.objects.filter(parent=site_of_zone.parent, type_id=DeviceTypeAssignmentEnum.SITE_ZONE_ASSIGNMENT, status_id=OptionsEnum.ACTIVE)
        except:
            zones_of_site = None

        if zones_of_site:
            present = polygon_operations(zones=zones_of_site, curr_cordinates=current_pt)
            present_in_zone = get_geofence_violations(pre_data_obj)
            print("PRESENT IN ZONE (SIGNAL VALUE): ", present_in_zone)
            if present and (present_in_zone is True):
                return True, site_of_zone.parent, zone_of_employee.parent, False
            elif present and (present_in_zone is False):
                return True, site_of_zone.parent, zone_of_employee.parent, True
            else:
                return False, None, None, False
        else:
            return False, None, None, False
    else:
        return False, None, None, False


def polygon_operations(zones, curr_cordinates):
    '''
    HELPER FUNCTION FOR ATTENDANCE MODULE.
    creates polygons and performs cascaded union to form a site with zones provided
    :param zones -> query set:
    :param curr_cordinates -> coordinates of reference point:
    :return: True if point occurs inside else False.
    '''
    polygon_container = []
    for geofence in zones:
        if geofence.child.territory:
            cordinates = [[p['lat'], p['lng']] for p in literal_eval(geofence.child.territory)]
            polygon_container.append(Polygon(cordinates))
    union_polygon = cascaded_union(polygon_container)
    if union_polygon.contains(curr_cordinates):
        return True
    else:
        return False



def get_durations_site(emp_id, date, viol_q_set_site, date_time_aggregation=None):
    duration = 0
    viol_q_set_site = viol_q_set_site.filter(violations_dtm__date=date, employee_id=emp_id)
    violations_q_set_in_site = viol_q_set_site.filter(violations_type_id=FFPOptionsEnum.IN_SITE, active_status=None).order_by('violations_dtm')
    violations_q_set_out_site = viol_q_set_site.filter(violations_type_id=FFPOptionsEnum.OUT_OF_SITE, active_status=None).order_by('violations_dtm')

    if violations_q_set_out_site.count() > 0 and violations_q_set_in_site.count()>0:
        for obj_in, obj_out in zip_longest(violations_q_set_in_site, violations_q_set_out_site, fillvalue=None):
            if obj_in:
                dtm_in  = obj_in.violations_dtm
            if obj_out:
                dtm_out = obj_out.violations_dtm
            else:
                if date_time_aggregation:
                    dtm_out = date_time_aggregation
                else:
                    dtm_out = timezone.now()

            if dtm_in and dtm_out:
                diff_dtm = dtm_out - dtm_in

                dur = abs(round(diff_dtm.total_seconds()/60, 0))
                duration += dur
            else:
                duration+=0

    elif violations_q_set_out_site.count()==0 and violations_q_set_in_site.count() >0:
        dtm_in = violations_q_set_in_site.order_by('violations_dtm')[0].violations_dtm
        dtm_out = timezone.now()
        diff_dtm = dtm_out - dtm_in

        dur = abs(round(diff_dtm.total_seconds()/60, 0))
        duration += dur

    # else:
    #     for obj_in in violations_q_set_in_site:
    #         dtm_in = obj_in.violations_dtm
    #         dtm_out = timezone.now()
    #         diff_dtm = dtm_out - dtm_in
    #
    #         dur = round(diff_dtm.total_seconds() / 60, 0)
    #         duration += dur

    return abs(duration)


def get_durations_zone(emp_id, date, viol_q_set_zone, date_time_aggregation=None):
    duration = 0
    viol_q_set_zone = viol_q_set_zone.filter(violations_dtm__date=date, employee_id=emp_id)
    violations_q_set_in_zone = viol_q_set_zone.filter(violations_type_id=FFPOptionsEnum.IN_ZONE, active_status=None).order_by('violations_dtm')
    violations_q_set_out_zone = viol_q_set_zone.filter(violations_type_id=FFPOptionsEnum.OUT_OF_ZONE, active_status=None).order_by('violations_dtm')

    print('out of zone : '+ str(violations_q_set_out_zone.count()))
    print('in zone : '+ str(violations_q_set_in_zone.count()))

    if violations_q_set_out_zone.count() > 0 and violations_q_set_in_zone.count() > 0:
        for obj_in, obj_out in zip_longest(violations_q_set_in_zone, violations_q_set_out_zone, fillvalue=None):
            if obj_in:
                dtm_in  = obj_in.violations_dtm
            if obj_out:
                if obj_out.violations_dtm:
                    dtm_out = obj_out.violations_dtm
            else:
                if date_time_aggregation:
                    dtm_out = date_time_aggregation
                else:
                    dtm_out = timezone.now()
            if dtm_out and dtm_in:
                diff_dtm = dtm_out - dtm_in

                dur = abs(round(diff_dtm.total_seconds()/60, 0))
                duration += dur
            else:
                duration +=0

    elif violations_q_set_out_zone.count() == 0 and violations_q_set_in_zone.count()>0:
        dtm_in  = violations_q_set_in_zone.order_by('violations_dtm')[0].violations_dtm
        dtm_out = timezone.now()
        diff_dtm = dtm_out - dtm_in

        dur = abs(round(diff_dtm.total_seconds()/60, 0))
        duration += dur

    # else:
    #     for obj_in in violations_q_set_in_zone:
    #         dtm_in = obj_in.violations_dtm
    #         dtm_out = timezone.now()
    #         diff_dtm = dtm_out - dtm_in
    #
    #         dur = round(diff_dtm.total_seconds() / 60, 0)
    #         duration += dur

    return abs(duration)


def get_active_hours_zone(emp_id, date, viol_q_set_zone, date_time_aggregation=None):
    duration = 0
    viol_q_set_zone = viol_q_set_zone.filter(violations_dtm__date=date, employee_id=emp_id)
    violations_q_set_in_zone = viol_q_set_zone.filter(violations_type_id=FFPOptionsEnum.IN_ZONE, active_status=OptionsEnum.ACTIVE).order_by('violations_dtm')
    violations_q_set_out_zone = viol_q_set_zone.filter(violations_type_id=FFPOptionsEnum.IN_ZONE, active_status=OptionsEnum.INACTIVE).order_by('violations_dtm')

    print('Inactive in zone : '+ str(violations_q_set_out_zone.count()))
    print('active in zone : '+ str(violations_q_set_in_zone.count()))


    if violations_q_set_in_zone.count() > 0 and violations_q_set_out_zone.count() >0:
        if violations_q_set_in_zone.count() > violations_q_set_out_zone.count():
            for obj_in, obj_out in zip_longest(violations_q_set_in_zone, violations_q_set_out_zone, fillvalue=None):
                if obj_in:
                    dtm_in  = obj_in.violations_dtm
                if obj_out:
                    dtm_out = obj_out.violations_dtm
                else:
                    if date_time_aggregation:
                        dtm_out = date_time_aggregation
                    else:
                        dtm_out = timezone.now()
                if dtm_in and dtm_out:
                    diff_dtm = dtm_out - dtm_in
                    dur = abs(round(diff_dtm.total_seconds()/60, 0))
                    duration += dur

        elif violations_q_set_out_zone.count() > violations_q_set_in_zone.count():
            violations_q_set_out_site = violations_q_set_out_zone[0:violations_q_set_in_zone.count()]
            for obj_in, obj_out in zip_longest(violations_q_set_in_zone, violations_q_set_out_site, fillvalue=None):
                dtm_in  = obj_in.violations_dtm
                if obj_out:
                    dtm_out = obj_out.violations_dtm
                else:
                    dtm_out = timezone.now()

                diff_dtm = dtm_out - dtm_in
                dur = abs(round(diff_dtm.total_seconds()/60, 0))
                duration += dur

        else:
            for obj_in, obj_out in zip_longest(violations_q_set_in_zone, violations_q_set_out_zone, fillvalue=None):
                if obj_in:
                    dtm_in  = obj_in.violations_dtm
                if obj_out:
                    dtm_out = obj_out.violations_dtm
                else:
                    if date_time_aggregation:
                        dtm_out = date_time_aggregation
                    else:
                        dtm_out = timezone.now()
                if dtm_in and dtm_out:
                    diff_dtm = dtm_out - dtm_in
                    dur = abs(round(diff_dtm.total_seconds()/60, 0))
                    duration += dur


    elif violations_q_set_out_zone.count()==0 and violations_q_set_in_zone.count() > 0:
        dtm_in = violations_q_set_in_zone.order_by('violations_dtm')[0].violations_dtm
        dtm_out = timezone.now()
        diff_dtm = dtm_out - dtm_in

        dur = abs(round(diff_dtm.total_seconds() / 60, 0))
        duration += dur

    return abs(duration)


def get_active_hours_site(emp_id, date, viol_q_set_site, date_time_aggregation=None):
    duration = 0
    viol_q_set_site = viol_q_set_site.filter(violations_dtm__date=date, employee_id=emp_id)
    violations_q_set_in_site = viol_q_set_site.filter(violations_type_id=FFPOptionsEnum.IN_SITE, active_status=OptionsEnum.ACTIVE).order_by('violations_dtm')
    violations_q_set_out_site = viol_q_set_site.filter(violations_type_id=FFPOptionsEnum.IN_SITE, active_status=OptionsEnum.INACTIVE).order_by('violations_dtm')

    print('Inactive in site : '+ str(violations_q_set_out_site.count()))
    print('active in site : '+ str(violations_q_set_in_site.count()))


    if violations_q_set_in_site.count() > 0 and violations_q_set_out_site.count() >0:
        if violations_q_set_in_site.count() > violations_q_set_out_site.count():
            for obj_in, obj_out in zip_longest(violations_q_set_in_site, violations_q_set_out_site, fillvalue=None):
                if obj_in:
                    dtm_in  = obj_in.violations_dtm
                if obj_out:
                    dtm_out = obj_out.violations_dtm
                else:
                    if date_time_aggregation:
                        dtm_out = date_time_aggregation
                    else:
                        dtm_out = timezone.now()
                if dtm_in and dtm_out:
                    diff_dtm = dtm_out - dtm_in
                    dur = abs(round(diff_dtm.total_seconds()/60, 0))
                    duration += dur

        elif violations_q_set_out_site.count() > violations_q_set_in_site.count():
            violations_q_set_out_site = violations_q_set_out_site[0:violations_q_set_in_site.count()]
            for obj_in, obj_out in zip_longest(violations_q_set_in_site, violations_q_set_out_site, fillvalue=None):
                dtm_in  = obj_in.violations_dtm
                if obj_out:
                    dtm_out = obj_out.violations_dtm
                else:
                    dtm_out = timezone.now()

                diff_dtm = dtm_out - dtm_in
                dur = abs(round(diff_dtm.total_seconds()/60, 0))
                duration += dur

        else:
            for obj_in, obj_out in zip_longest(violations_q_set_in_site, violations_q_set_out_site, fillvalue=None):
                if obj_in:
                    dtm_in  = obj_in.violations_dtm
                if obj_out:
                    dtm_out = obj_out.violations_dtm
                else:
                    if date_time_aggregation:
                        dtm_out = date_time_aggregation
                    else:
                        dtm_out = timezone.now()
                if dtm_in and dtm_out:
                    diff_dtm = dtm_out - dtm_in
                    dur = abs(round(diff_dtm.total_seconds()/60, 0))
                    duration += dur


    elif violations_q_set_out_site.count()==0 and violations_q_set_in_site.count() > 0:
        dtm_in = violations_q_set_in_site.order_by('violations_dtm')[0].violations_dtm
        dtm_out = timezone.now()
        diff_dtm = dtm_out - dtm_in

        dur = abs(round(diff_dtm.total_seconds() / 60, 0))
        duration += dur

    return abs(duration)


def get_productivity(c_id, dur_active, site, zone=None):
    shift_hrs_zone = 0
    shift_hrs_site = 0
    shift_hrs_global = 0

    if zone:
        shift_hrs_zone = zone.squad_number if zone.squad_number > 0 else 0
    elif site and shift_hrs_zone <=0:
        shift_hrs_site = site.squad_number if site.squad_number > 0 else 0
    else:
        try:
            shift_hrs_global = CustomerPreferences.objects.get(customer_id=c_id).shift_hours
        except CustomerPreferences.DoesNotExist:
            shift_hrs_global = 0

    if shift_hrs_zone > 0:
        man_hours = shift_hrs_zone
    elif shift_hrs_site > 0:
        man_hours = shift_hrs_site
    elif shift_hrs_global > 0:
        man_hours = shift_hrs_global
    else:
        man_hours = None

    if man_hours:
        productivity = (dur_active / man_hours) * 100

    return productivity if productivity > 0 else 0

def daily_averages_ffp():
    employees_list = Entity.objects.filter(type_id=DeviceTypeEntityEnum.EMPLOYEE).exclude(entity_sub_type_id=FFPOptionsEnum.SITE_SUPERVISOR).values_list('id', flat=True)
    sites_list = Entity.objects.filter(type_id=DeviceTypeEntityEnum.SITE).values_list('id', flat=True)
    zones_list = Entity.objects.filter(type_id=DeviceTypeEntityEnum.ZONE).values_list('id', flat=True)
    #FIXME LAST DAY FOR TESTING
    # last_day = timezone.now() - timedelta(days=1)
    today_date  = timezone.now().date()
    today_date_dtm = timezone.now()


    # today_date  = timezone.now() - timedelta(days=1)
    # today_date = today_date.date()
    # today_date_dtm = timezone.now() - timedelta(days=1)

    _post_data = HypernetPostData.objects.filter(device_id__in=employees_list,timestamp__date=today_date)

    _post_data = _post_data.values('customer_id', 'module_id', 'device_id').order_by('device_id').annotate(avg_heart_rate=Avg('heartrate_value'),
                 avg_temperature=Avg('temperature'), avg_ambient_temperature=Avg('ambient_temperature'))
    if _post_data.__len__() > 0:
        customer = _post_data[0]['customer_id']
        module_id = _post_data[0]['module_id']

        for data in _post_data:
            zone = Assignment.objects.filter(child_id=data['device_id'], status_id=OptionsEnum.ACTIVE, type_id=DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT)
            site = Assignment.objects.filter(child=zone[0].parent if zone.__len__() == 1 else None, status_id=OptionsEnum.ACTIVE, type_id=DeviceTypeAssignmentEnum.SITE_ZONE_ASSIGNMENT)
            emp_average_daily = FFPDataDailyAverage()
            emp_average_daily.heart_rate = data['avg_heart_rate']
            emp_average_daily.temperature = data['avg_temperature']
            emp_average_daily.ambient_temperature = data['avg_ambient_temperature']
            emp_average_daily.employee_id = data['device_id']
            emp_average_daily.customer_id = data['customer_id']
            emp_average_daily.module_id = data['module_id']
            emp_average_daily.zone = zone[0].parent if zone.__len__() == 1 else None
            emp_average_daily.site = site[0].parent if site.__len__() == 1 else None
            emp_average_daily.timestamp = today_date
            emp_average_daily.save()

    for emp in employees_list:
        zone = Assignment.objects.filter(child_id=emp, status_id=OptionsEnum.ACTIVE, type_id=DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT)
        site = Assignment.objects.filter(child=zone[0].parent if zone.__len__() == 1 else None, status_id=OptionsEnum.ACTIVE, type_id=DeviceTypeAssignmentEnum.SITE_ZONE_ASSIGNMENT)
        try:
            present_emp = AttendanceRecord.objects.get((Q(site_checkin_dtm__date=today_date) | Q(attendance_dtm__date=today_date)) & (Q(present=True) | Q(present=False))
                                                       ,employee_id=emp)
            if present_emp.site_checkin_dtm:
                if present_emp.site_status:
                    vltn = check_employee_active_status(False, FFPOptionsEnum.IN_SITE, present_emp)
                    vltn.save()
                    present_emp.site_status = False
                    create_violation_data(attendace_record=present_emp, violation_type=FFPOptionsEnum.OUT_OF_SITE, active_status=None)

                if present_emp.zone_status:
                    vltn = check_employee_active_status(False, FFPOptionsEnum.IN_ZONE, present_emp)
                    vltn.save()
                    present_emp.zone_status = False
                    create_violation_data(attendace_record=present_emp, violation_type=FFPOptionsEnum.OUT_OF_ZONE, active_status=None)

        except:
            absent_record = AttendanceRecord(present=False, employee_id=emp,
                                         site=site[0].parent if site.__len__() == 1 else None,
                                         zone=zone[0].parent if zone.__len__() == 1 else None,
                                         duration_in_site=0,
                                         duration_in_zone=0,
                                         duration_in_site_active=0,
                                         duration_in_zone_active=0,
                                         customer_id=customer,
                                         module_id=module_id,
                                         attendance_dtm= today_date
                                         )
            absent_record.save()
            continue

        if present_emp:
            violations_qset = EmployeeViolations.objects.filter(violations_dtm__date=today_date, employee_id=emp)
            duration_in_zone = get_durations_zone(emp_id=emp, date=today_date, viol_q_set_zone=violations_qset, date_time_aggregation=today_date_dtm)
            duration_in_site = get_durations_site(emp_id=emp, date=today_date, viol_q_set_site=violations_qset, date_time_aggregation=today_date_dtm)
            duration_in_site_active = get_active_hours_site(emp_id=emp, date=today_date, viol_q_set_site=violations_qset, date_time_aggregation=today_date_dtm)
            duration_in_zone_active = get_active_hours_zone(emp_id=emp, date=today_date, viol_q_set_zone=violations_qset, date_time_aggregation=today_date_dtm)
            productivity = get_productivity(c_id=customer, dur_active=duration_in_site_active, site=site[0].parent if site.__len__() >0 else None, zone=zone[0].parent)
            present_emp.duration_in_site = duration_in_site
            present_emp.duration_in_zone = duration_in_zone
            present_emp.duration_in_site_active = duration_in_site_active
            present_emp.duration_in_zone_active = duration_in_zone_active
            present_emp.productive_hours = productivity
            present_emp.save()

    #TODO Average storage
    for s in sites_list:
        site_attendance = AttendanceRecord.objects.filter(attendance_dtm__date=today_date, site_id=s).order_by('site_id')
        site_avg_prod = site_attendance.values('site').annotate(site_prod_hrs = Avg('productive_hours')).values('site_prod_hrs')
        site_avg_dur = site_attendance.values('site').annotate(site_dur_hrs = Avg('duration_in_site')).values('site_dur_hrs')
        site_avg = FFPDataDailyAverage()
        site_avg.timestamp = today_date
        site_avg.customer_id = customer
        site_avg.module_id = module_id
        site_avg.site_id = s
        site_avg.site_durations_avg = site_avg_dur[0]['site_dur_hrs'] if site_avg_dur.__len__()>0 else 0
        site_avg.site_productivity_avg = site_avg_prod[0]['site_prod_hrs'] if site_avg_prod.__len__()>0 else 0
        site_avg.save()

    for z in zones_list:
        zone_attendance = AttendanceRecord.objects.filter(attendance_dtm__date=today_date, zone_id=z)
        zone_avg_prod = zone_attendance.values('zone').annotate(zone_prod_hrs = Avg('productive_hours')).values('zone_prod_hrs')
        zone_avg_dur = zone_attendance.values('zone').annotate(zone_dur_hrs = Avg('duration_in_zone')).values('zone_dur_hrs')
        zone_avg = FFPDataDailyAverage()
        zone_avg.timestamp = today_date
        zone_avg.customer_id = customer
        zone_avg.module_id = module_id
        zone_avg.zone_id = z
        zone_avg.zone_productivity_avg = zone_avg_dur[0]['zone_dur_hrs'] if zone_avg_dur.__len__()>0 else 0
        zone_avg.zone_durations_avg = zone_avg_prod[0]['zone_prod_hrs'] if zone_avg_prod.__len__()>0 else 0
        zone_avg.save()

    print("Averegaes saved at: ", timezone.now())

def get_users_list(obj):
    if obj:
        admins = User.objects.filter(role_id=RoleTypeEnum.ADMIN, customer=obj.customer) #fetching all admins
        result = [i.id for i in admins]

        zone_supervisor = Assignment.objects.get(parent = obj.zone, type_id=DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT,
                                                 child__entity_sub_type_id = FFPOptionsEnum.ZONE_SUPERVISOR).child

        zone_supervisor_user = User.objects.get(associated_entity_id = zone_supervisor.id)

        site_supervisor = Assignment.objects.get(parent=obj.site,
                                                 type_id=DeviceTypeAssignmentEnum.SITE_EMPLOYEE_ASSIGNMENT,
                                                 child__entity_sub_type_id=FFPOptionsEnum.SITE_SUPERVISOR).child

        site_supervisor_user = User.objects.get(associated_entity_id=site_supervisor.id)

        if obj.employee.entity_sub_type.id == FFPOptionsEnum.SITE_SUPERVISOR:
            pass
        elif obj.employee.entity_sub_type.id == FFPOptionsEnum.ZONE_SUPERVISOR:
            result.append(site_supervisor_user.id)
        elif obj.employee.entity_sub_type.id in [FFPOptionsEnum.TEAM_SUPERVISOR, FFPOptionsEnum.LABOUR]:
            result.append(zone_supervisor_user.id)

        return result


def check_employee_active_status(a_or_i_flag, presence, attn_obj):
    if a_or_i_flag:  #active employee
       violation= create_violation_data(attn_obj, violation_type=presence, active_status= OptionsEnum.ACTIVE)
    else:
       violation= create_violation_data(attn_obj, violation_type=presence, active_status=OptionsEnum.INACTIVE)
    #attn_obj.active_status = a_or_i_flag
    #attn_obj.save()
    return violation

