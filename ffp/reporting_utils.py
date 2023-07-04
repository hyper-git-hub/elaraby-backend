import traceback
from collections import Counter

from datetime import timedelta
import itertools
from dateutil.parser import parse
from django.db.models import Q, F, Count, Avg, Max
#from ffp.cron_utils import get_active_hours_zone

from ffp.models import Tasks, AttendanceRecord, EmployeeViolations, FFPDataDailyAverage
from ffp.serializers import TaskSerializer
from hypernet.constants import LAST_WEEK
from user.enums import RoleTypeEnum
from user.models import User
__author__ = 'SyedUsman'

from django.utils import timezone
from hypernet.enums import OptionsEnum, DeviceTypeEntityEnum, FFPOptionsEnum, DeviceTypeAssignmentEnum, IOFOptionsEnum
from hypernet.models import Entity, Assignment, HypernetPostData, HypernetPreData
from hypernet.serializers import SiteSerializer, ZoneSerializer, EmployeeSerializer

from customer.models import CustomerPreferences

def util_get_assets_count(c_id):
    employees = Entity.objects.filter(customer_id=c_id, status_id=OptionsEnum.ACTIVE, type_id=DeviceTypeEntityEnum.EMPLOYEE)
    total_employee = employees.count()
    total_site_supervisors = employees.filter(entity_sub_type_id=FFPOptionsEnum.SITE_SUPERVISOR).count()
    total_zone_supervisors = employees.filter(entity_sub_type_id=FFPOptionsEnum.ZONE_SUPERVISOR).count()
    total_team_supervisors = employees.filter(entity_sub_type_id=FFPOptionsEnum.TEAM_SUPERVISOR).count()
    total_labors = employees.filter(entity_sub_type_id=FFPOptionsEnum.LABOUR).count()



    sites = Entity.objects.filter(customer_id=c_id, status_id=OptionsEnum.ACTIVE, type_id=DeviceTypeEntityEnum.SITE)
    total_sites = sites.count()

    zones = Entity.objects.filter(customer_id=c_id, status_id=OptionsEnum.ACTIVE, type_id=DeviceTypeEntityEnum.ZONE)
    total_zones = zones.count()

    total_violations_today = EmployeeViolations.objects.filter(customer_id=c_id,violations_type_id__in = [FFPOptionsEnum.OUT_OF_SITE,
                                                                FFPOptionsEnum.OUT_OF_ZONE] ,violations_dtm__date = timezone.now().date()).count()

    most_violating_site = EmployeeViolations.objects.filter(violations_type_id__in = [FFPOptionsEnum.OUT_OF_SITE,
                                                                FFPOptionsEnum.OUT_OF_ZONE], violations_dtm__date = timezone.now().date()).values('site__name').annotate(violating_site = Count('id')).order_by('-violating_site')

    total_violations_by_site = most_violating_site.count()
    most_violating_zone = EmployeeViolations.objects.filter(violations_type_id__in = [FFPOptionsEnum.OUT_OF_SITE,
                                                                FFPOptionsEnum.OUT_OF_ZONE], violations_dtm__date = timezone.now().date()).values('zone__name').annotate(violating_zone = Count('id')).order_by('-violating_zone')
    total_violations_by_zone = most_violating_zone.count()

    most_violating_employee = EmployeeViolations.objects.filter(violations_type_id__in = [FFPOptionsEnum.OUT_OF_SITE,
                                                                FFPOptionsEnum.OUT_OF_ZONE], violations_dtm__date = timezone.now().date()).values('employee__name').annotate(violating_employee = Count('id')).order_by('-violating_employee')
    total_violations_by_employee = most_violating_employee.count()
    avg_productivity_last_day_q_set = FFPDataDailyAverage.objects.filter(customer_id=c_id, timestamp__date=(timezone.now() - timedelta(days=1)).date())
    avg_productivity_last_day = avg_productivity_last_day_q_set.values('customer').annotate(site_prod_hrs = Avg('site_productivity_avg')).values('site_prod_hrs')
    most_productive_site = avg_productivity_last_day.values('site').annotate(Max('site_productivity_avg')).values('site', 'site__name')
    most_productive_zone = avg_productivity_last_day.values('zone').annotate(Max('zone_productivity_avg')).values('zone', 'zone__name')

    most_productive_emp_q_set = AttendanceRecord.objects.filter(customer_id=c_id, attendance_dtm__date=(timezone.now() - timedelta(days=1)).date())
    most_productive_emp = most_productive_emp_q_set.values('employee').annotate(Max('productive_hours')).values('employee', 'employee__name')

    return_dict = {'total_employees': total_employee,
                        'total_site_supervisors': total_site_supervisors,
                        'total_zone_supervisors': total_zone_supervisors,
                        'total_team_supervisors': total_team_supervisors,
                        'total_labors': total_labors,
                        'total_sites': total_sites,
                        'total_zones': total_zones,
                        'most_violating_site': most_violating_site[0]['site__name'] if most_violating_site.__len__() > 0 else None,
                        'total_violations_by_site': total_violations_by_site,
                        'most_violating_zone': most_violating_zone[0]['zone__name'] if most_violating_zone.__len__() > 0 else None,
                        'total_violations_by_zone': total_violations_by_zone,
                        'most_violating_employee': most_violating_employee[0]['employee__name'] if most_violating_employee.__len__() > 0 else None,
                        'total_violations_by_employee': total_violations_by_employee,
                        'total_violations_today': total_violations_today,
                        'avg_productive_last_day': avg_productivity_last_day[0]['site_prod_hrs'] if avg_productivity_last_day.__len__()>0 else 0,

                        'most_productive_site': most_productive_site[0]['site__name'] if most_productive_site.__len__()>0 else None,
                        'most_productive_site_id': most_productive_site[0]['site'] if most_productive_site.__len__()>0 else None,
                        'most_productive_zone': most_productive_zone[0]['zone__name'] if most_productive_zone.__len__()>0 else None,
                        'most_productive_zone_id': most_productive_zone[0]['zone'] if most_productive_zone.__len__()>0 else None,
                        'most_productive_employee': most_productive_emp[0]['employee__name'] if most_productive_emp.__len__()>0 else None,
                        'most_productive_employee_id': most_productive_emp[0]['employee'] if most_productive_emp.__len__()>0 else None,

                   }

    return return_dict


def util_get_sites_details(c_id, s_date=None, e_date=None):
    sites_list = []

    sites = Entity.objects.filter(customer_id=c_id, type_id=DeviceTypeEntityEnum.SITE)
    employees = Entity.objects.filter(customer_id=c_id, status_id=OptionsEnum.ACTIVE, type_id=DeviceTypeEntityEnum.EMPLOYEE)
    total_employee = employees.count()

    for obj in sites:
        serializer = SiteSerializer(obj, context=None)
        sites_dict = serializer.data
        zones_of_site = Assignment.objects.filter(type_id=DeviceTypeAssignmentEnum.SITE_ZONE_ASSIGNMENT, parent=obj, status_id=OptionsEnum.ACTIVE)
        emp_of_site = Assignment.objects.filter(parent_id__in=zones_of_site.values_list('child_id'), status_id=OptionsEnum.ACTIVE,
                                                      type_id=DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT)
        try:
            supervisor_of_site = Assignment.objects.get(type_id=DeviceTypeAssignmentEnum.SITE_EMPLOYEE_ASSIGNMENT, parent=obj, status_id=OptionsEnum.ACTIVE)
        except:
            supervisor_of_site = None

        present_employee = AttendanceRecord.objects.filter(site=obj, site_checkin_dtm__date=timezone.now().date(), present=True)

        violations = EmployeeViolations.objects.filter(site=obj, active_status=None , violations_dtm__date=(timezone.now() - timedelta(days=LAST_WEEK)).date())
        violations_last_day = EmployeeViolations.objects.filter(site=obj, violations_dtm__date=(timezone.now() - timedelta(days=1)).date(), active_status=None)

        sites_dict['zones_count'] = zones_of_site.count()
        sites_dict['zone_shape'] = [zone.child.territory for zone in zones_of_site]
        sites_dict['total_employees'] = emp_of_site.count()
        sites_dict['total_employees_present'] = present_employee.count()
        sites_dict['total_employees_absent'] = emp_of_site.count() - present_employee.count() or 0
        sites_dict['supervisor'] = supervisor_of_site.child.name if supervisor_of_site else None
        sites_dict['violations'] = [{k: [{c: len(list(a))} for c, a in itertools.groupby(g, lambda g: g.violations_type.label)]}
                                    for k, g in itertools.groupby(violations, lambda viol: viol.site.name)]

        sites_dict['violations_last_day'] = violations_last_day.count()
        sites_dict['total_employee'] = total_employee

        sites_list.append(sites_dict)

    return sites_list


def util_get_ranked_sites(c_id, s_date=None, e_date=None):
    sites_list = []
    sites = Entity.objects.filter(customer_id=c_id, type_id=DeviceTypeEntityEnum.SITE)

    for obj in sites:
        sites_dict = {}
        violations_last_day = EmployeeViolations.objects.filter(site=obj, violations_dtm__date=timezone.now() - timedelta(days=1), active_status=None)
        productivity_yesterday_data = FFPDataDailyAverage.objects.filter(timestamp__date=(timezone.now() - timedelta(days=1)).date(),
                                                         site=obj, employee=None, zone=None)

        productivity_yesterday_data = productivity_yesterday_data[0].site_productivity_avg if productivity_yesterday_data.__len__() > 0 else 0

        if violations_last_day.count() > 0 and productivity_yesterday_data > 0:
            ratio = (productivity_yesterday_data / violations_last_day.count())

            sites_dict['site_id'] = obj.id
            sites_dict['site_name'] = obj.name
            sites_dict['ratio'] = ratio
            sites_list.append(sites_dict)

        else:
            sites_dict['site_id'] = obj.id
            sites_dict['site_name'] = obj.name
            sites_dict['ratio'] = 0
            sites_list.append(sites_dict)

    final_data = sorted(sites_list, key=lambda ratio:ratio.get('ratio'), reverse=True)
    top_three = final_data[0:2]
    worst_three = final_data[-3:-1]

    return top_three, worst_three




def get_all_employees_attendance(c_id):
    from ffp.cron_utils import get_employee_attendance
    all_emps = Entity.objects.filter(customer_id=c_id, type_id=DeviceTypeEntityEnum.EMPLOYEE, status_id=OptionsEnum.ACTIVE)
    present_emps = 0
    td = timezone.now() - timedelta(minutes=1)
    pre_data = HypernetPostData.objects.filter(device_id__in=all_emps.values_list('id'), timestamp__gte=td)
    for pre_obj in pre_data:
        attendance = get_employee_attendance(pre_data_obj=pre_obj)
        if attendance is True:
            present_emps += 1
    return present_emps


def get_all_employees_active(c_id):
    from ffp.cron_utils import get_geofence_violations
    all_emps = Entity.objects.filter(customer_id=c_id, type_id=DeviceTypeEntityEnum.EMPLOYEE, status_id=OptionsEnum.ACTIVE)
    active_emps = 0
    td = timezone.now() - timedelta(minutes=1)
    pre_data = HypernetPostData.objects.filter(device_id__in=all_emps.values_list('id'), timestamp__gte=td)
    for pre_obj in pre_data:
        attendance = get_geofence_violations(pre_data_obj=pre_obj)
        if attendance is True:
            active_emps += 1
    return active_emps


def util_get_individual_site_details(s_id, c_id, s_date=None, e_date=None):
    site_dict = {}
    site_list = []
    zones_list = []
    try:
        site = Entity.objects.get(pk=s_id, customer_id=c_id, type_id=DeviceTypeEntityEnum.SITE)
    except:
        site = None
    # for obj in site:
    serializer = SiteSerializer(site, context=None)
    sites_dict = serializer.data
    zones_of_site = Assignment.objects.filter(type_id=DeviceTypeAssignmentEnum.SITE_ZONE_ASSIGNMENT, parent=site, status_id=OptionsEnum.ACTIVE)
    emp_of_site = Assignment.objects.filter(parent_id__in=zones_of_site.values_list('child_id'), status_id=OptionsEnum.ACTIVE,
                                                  type_id=DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT)
    try:
        supervisor_of_site = Assignment.objects.get(type_id=DeviceTypeAssignmentEnum.SITE_EMPLOYEE_ASSIGNMENT, parent=site, status_id=OptionsEnum.ACTIVE)
    except:
        supervisor_of_site = None
    assigned_zones = Entity.objects.filter(pk__in= zones_of_site.values('child_id'))
    zones_data = ZoneSerializer(assigned_zones, many=True)
    present_employee = AttendanceRecord.objects.filter(site_id=s_id, site_checkin_dtm__date=timezone.now().date(), present=True)
    violations = EmployeeViolations.objects.filter(site_id=s_id, violations_dtm__date=(timezone.now() - timedelta(days=LAST_WEEK)).date(),
                                                   violations_type_id__in=[FFPOptionsEnum.OUT_OF_ZONE, FFPOptionsEnum.OUT_OF_SITE]).order_by('violations_type_id')

    violations_last_day = EmployeeViolations.objects.filter(site_id=s_id,
                                                            violations_type_id__in=[FFPOptionsEnum.OUT_OF_ZONE,FFPOptionsEnum.OUT_OF_SITE],
                                                            violations_dtm__date=timezone.now() - timedelta(days=1)).order_by('violations_type_id')

    violations_today = EmployeeViolations.objects.filter(site_id=s_id,
        violations_type_id__in=[FFPOptionsEnum.OUT_OF_ZONE,FFPOptionsEnum.OUT_OF_SITE],
        violations_dtm__date=timezone.now().date()).order_by('violations_type_id')

    violations_of_site = [{k: [{c: len(list(a))} for c, a in
                                itertools.groupby(g, lambda g: g.violations_type.label)]} for k, g in
                                itertools.groupby(violations, lambda viol: viol.zone.name)]

    for obj in zones_data.data:
        zones_list.append(obj)
    sites_dict['zones_count'] = zones_of_site.count()
    sites_dict['assigned_zones'] = zones_list
    sites_dict['total_employees'] = emp_of_site.count()
    sites_dict['supervisor'] = supervisor_of_site.child.name if supervisor_of_site else None
    sites_dict['supervisor_id'] = supervisor_of_site.child.id if supervisor_of_site else None
    sites_dict['violations_last_day'] = violations_last_day.count() if violations_last_day.__len__() > 0 else 0
    sites_dict['violations_today'] = violations_today.count() if violations_today.__len__() > 0 else 0
    sites_dict['violations'] = violations_of_site
    sites_dict['man_hours'] = None

    #TODO: Data for keys below need to be produced.
    sites_dict['present_employees'] = present_employee.count()
    sites_dict['absent_employees'] = emp_of_site.count() - present_employee.count() or 0
    sites_dict['active_employees'] = present_employee.filter(active_status=True).count()
    sites_dict['inactive_employees'] = present_employee.filter(active_status=True).count() - present_employee.filter(active_status=False).count()

    return sites_dict


def util_get_tasks_employees(loged_user):
    r_list = []

    employees = None
    if loged_user.associated_entity:
        emp_type = loged_user.associated_entity.entity_sub_type_id
    else:
        emp_type = None

    try:
        supervisor = loged_user.associated_entity
    except:
        supervisor = None

    if loged_user.role_id == RoleTypeEnum.ADMIN:
        employees = Entity.objects.filter(customer=loged_user.customer, status_id=OptionsEnum.ACTIVE,
                                      type_id=DeviceTypeEntityEnum.EMPLOYEE,
                                      entity_sub_type_id=FFPOptionsEnum.SITE_SUPERVISOR)
        supervisor = None

    if supervisor and emp_type:
        if emp_type == FFPOptionsEnum.SITE_SUPERVISOR:
            try:
                site_of_sup = Assignment.objects.get(child=supervisor, status_id=OptionsEnum.ACTIVE,
                                                     type_id=DeviceTypeAssignmentEnum.SITE_EMPLOYEE_ASSIGNMENT)
            except:
                site_of_sup = None

            if site_of_sup:
                zones_of_sites = Assignment.objects.filter(parent=site_of_sup.parent, type_id=DeviceTypeAssignmentEnum.SITE_ZONE_ASSIGNMENT,
                                                           status_id=OptionsEnum.ACTIVE)
                employees = Assignment.objects.filter(parent_id__in=zones_of_sites.values_list('child_id'), status_id=OptionsEnum.ACTIVE,
                                                      type_id=DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT)

        elif emp_type == FFPOptionsEnum.ZONE_SUPERVISOR:
            try:
                zone_of_sup = Assignment.objects.filter(child=supervisor, status_id=OptionsEnum.ACTIVE,
                                                     type_id=DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT)
            except:
                zone_of_sup = None

            if zone_of_sup:
                employees = Assignment.objects.filter(parent_id__in=zone_of_sup.values_list('parent_id'),
                                                      status_id=OptionsEnum.ACTIVE,
                                                      type_id=DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT)

        elif emp_type == FFPOptionsEnum.TEAM_SUPERVISOR:
            #FIXME: Labor-Team lead assignment.
            pass

    if employees:
        for emp in employees:
            if emp_type == FFPOptionsEnum.SITE_SUPERVISOR:
                if emp.child.entity_sub_type_id == FFPOptionsEnum.ZONE_SUPERVISOR:
                    r_list.append(emp.child.as_entity_json())

            elif emp_type == FFPOptionsEnum.ZONE_SUPERVISOR:
                if emp.child.entity_sub_type_id == FFPOptionsEnum.TEAM_SUPERVISOR:
                    r_list.append(emp.child.as_entity_json())

            elif emp_type == FFPOptionsEnum.TEAM_SUPERVISOR:
                if emp.child.entity_sub_type_id == FFPOptionsEnum.LABOUR:
                    r_list.append(emp.child.as_entity_json())

            elif loged_user.role_id == RoleTypeEnum.ADMIN:
                r_list.append(emp.as_entity_json())

        return r_list

    else:
        return None


def get_site_or_zone_of_supervisor(s_sup_id, get_zone=None):
    if s_sup_id.entity_sub_type_id == FFPOptionsEnum.SITE_SUPERVISOR:
        try:
            site = Assignment.objects.get(child_id=s_sup_id, status_id=OptionsEnum.ACTIVE,
                                          type_id=DeviceTypeAssignmentEnum.SITE_EMPLOYEE_ASSIGNMENT, child__entity_sub_type_id=FFPOptionsEnum.SITE_SUPERVISOR)
        except:
            site = None

        if site:
            return site.parent
        else:
            return None

    elif s_sup_id.entity_sub_type_id in [FFPOptionsEnum.ZONE_SUPERVISOR, FFPOptionsEnum.TEAM_SUPERVISOR]:
        try:
            zone = Assignment.objects.get(child_id=s_sup_id, status_id=OptionsEnum.ACTIVE,
                                          type_id=DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT, child__entity_sub_type_id=FFPOptionsEnum.ZONE_SUPERVISOR)
            if get_zone:
                return zone.parent
        except:
            zone = None

        if zone:
            site = Assignment.objects.get(child=zone.parent, status_id=OptionsEnum.ACTIVE,
                                          type_id=DeviceTypeAssignmentEnum.SITE_ZONE_ASSIGNMENT)

            if site:
                return site.parent
            else:
                return None

def get_zones_of_site(s_sup_id):
    zones_list = []
    try:
        site = Assignment.objects.get(child_id=s_sup_id, status_id=OptionsEnum.ACTIVE,
                                      type_id=DeviceTypeAssignmentEnum.SITE_EMPLOYEE_ASSIGNMENT, child__entity_sub_type_id=FFPOptionsEnum.SITE_SUPERVISOR)
    except:
        site = None
    if site:
        zones = Assignment.objects.filter(parent=site.parent, status_id=OptionsEnum.ACTIVE, type_id=DeviceTypeAssignmentEnum.SITE_ZONE_ASSIGNMENT)
        return zones.values(zone_id=F('child_id'), label=F('child__name'))
    else:
        return None


def get_zones_list(customer, entity_id):
    entities_list = []
    return_list = dict()

    if entity_id:
        try:
            entity = Entity.objects.get(pk=entity_id)
            if entity.entity_sub_type_id in [FFPOptionsEnum.ZONE_SUPERVISOR, FFPOptionsEnum.TEAM_SUPERVISOR, FFPOptionsEnum.LABOUR]:
                try:
                    assigned_entity = Assignment.objects.get(customer_id=customer, child_id=entity_id,
                                                            type_id=DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT,
                                                            status_id=OptionsEnum.ACTIVE)

                    entities_list.append({'id': assigned_entity.parent_id,
                                 'label': assigned_entity.parent.name})
                    return_list['assigned_flag'] = True
                    return_list['zones_list'] = entities_list

                except:
                    return_list['assigned_flag'] = False
                    return_list['zones_list'] = None

        except:
            return None
    return return_list


def util_get_tasks(loged_user, employee=None):
    r_list = []
    if employee:
        tasks = Tasks.objects.filter(Q(assignee_id=employee) | Q(responsible_id=employee), customer_id=loged_user.customer_id)
        responsible_tasks = tasks.filter(responsible_id=employee)
        assigned_tasks = tasks.filter(assignee_id=employee)

    else:
        supervisor =loged_user.associated_entity_id
        tasks = Tasks.objects.filter(Q(assignee_id=supervisor) | Q(responsible_id=supervisor), customer_id=loged_user.customer_id)
        responsible_tasks = tasks.filter(responsible_id=supervisor)
        assigned_tasks = tasks.filter(assignee_id=supervisor)

    responsible_tasks_data = {}
    assignee_tasks_data = {}
    responsible_tasks_list = []
    assigned_tasks_list = []

    for task in responsible_tasks:
        serializer = TaskSerializer(task, partial=True)
        responsible_tasks_list.append(serializer.data)

    for task in assigned_tasks:
        serializer = TaskSerializer(task, partial=True)
        assigned_tasks_list.append(serializer.data)

    responsible_tasks_data['responsible'] = responsible_tasks_list
    assignee_tasks_data['assignee'] = assigned_tasks_list

    r_list.append(responsible_tasks_data)
    r_list.append(assignee_tasks_data)

    return r_list


def util_get_individual_zone_details(z_id, c_id, s_date=None, e_date=None):
    zone_list = []
    if z_id:
        try:
            zone = Entity.objects.get(pk=z_id, customer_id=c_id, type_id=DeviceTypeEntityEnum.ZONE)
            zone_ser = ZoneSerializer(zone, context=None)
            zone_dict = zone_ser.data

            emp_of_zone = Assignment.objects.filter(parent=zone,status_id=OptionsEnum.ACTIVE,type_id=DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT)
            assigned_employees = Entity.objects.filter(pk__in=emp_of_zone.values('child_id'))
            present_employee = AttendanceRecord.objects.filter(zone_id=z_id, site_checkin_dtm__date=timezone.now().date(), present=True)
            violations = EmployeeViolations.objects.filter(zone_id=z_id, violations_type_id__in=[FFPOptionsEnum.OUT_OF_ZONE, FFPOptionsEnum.OUT_OF_SITE], active_status=None).order_by('violations_type_id')
                                                        # violations_dtm__range=[s_date, e_date]).order_by('violations_type_id')
            violations_last_day = EmployeeViolations.objects.filter(zone_id=z_id, violations_type_id__in=[FFPOptionsEnum.OUT_OF_ZONE, FFPOptionsEnum.OUT_OF_SITE],
                                                        violations_dtm__date=timezone.now() - timedelta(days=1), active_status=None).order_by('violations_type_id')
            violations_today = EmployeeViolations.objects.filter(zone_id=z_id, violations_type_id__in=[FFPOptionsEnum.OUT_OF_ZONE, FFPOptionsEnum.OUT_OF_SITE],
                                                        violations_dtm__date=timezone.now().date(), active_status=None).order_by('violations_type_id')

            in_zone = present_employee.filter(zone_status=True)
            out_of_zone = present_employee.filter(zone_status=False)
            active_emps = present_employee.filter(active_status=True)
            inactive_emps = present_employee.filter(active_status=False)

            try:
                site = Assignment.objects.get(child_id=z_id, type_id=DeviceTypeAssignmentEnum.SITE_ZONE_ASSIGNMENT, status_id=OptionsEnum.ACTIVE)
            except:
                site = None

            zone_dict['assigned_site'] = site.parent.name if site else None
            zone_dict['assigned_site_id'] = site.parent_id if site else None
            zone_dict['total_employees'] = emp_of_zone.count()
            zone_dict['present_employees'] = present_employee.count()
            zone_dict['absent_employees'] = emp_of_zone.count() - present_employee.count() or 0
            zone_dict['violations_last_day'] = violations_last_day.count() if violations_last_day.__len__() > 0 else 0
            zone_dict['violations_today'] = violations_today.count() if violations_today.__len__() > 0 else 0
            zone_dict['violations'] = [{k: len(list(g))} for k, g in
                                        itertools.groupby(violations, lambda viol: viol.violations_type.label)]
            zone_dict['in_zone'] = in_zone.count()
            zone_dict['out_of_zone'] = out_of_zone.count()
            zone_dict['active_emps'] = active_emps.count()
            zone_dict['inactive_emps'] = inactive_emps.count()

            for obj in assigned_employees:
                employee = EmployeeSerializer(obj)
                zone_list.append(employee.data)
            zone_dict['assigned_employees'] = zone_list
            return zone_dict
        except:
            traceback.print_exc()


def util_get_task_rate(loged_user, site, zone, employee, s_date, e_date, st_id):
    r_list = []

    if loged_user.associated_entity:
        supervisor =loged_user.associated_entity_id
        tasks = Tasks.objects.filter(Q(assignee_id=supervisor) | Q(responsible_id=supervisor), customer_id=loged_user.customer_id)
    else:
        tasks = Tasks.objects.filter(customer_id=loged_user.customer_id)

    if site:
        tasks = tasks.filter(site_id=site)
    if zone:
        tasks = tasks.filter(zone_id=zone)
    if employee:
        tasks = tasks.filter(assignee_id=employee)
    if st_id:
        tasks = tasks.filter(task_status_id=st_id)

    if s_date and e_date:
        s_date = parse(s_date)
        e_date = parse(e_date)
        tasks = tasks.filter(start_datetime__range=[s_date, e_date])

    return tasks


# def util_get_task_line_graph_data_site(group_by, q_set):
#     q_set = q_set.filter(site__isnull=False).order_by('start_datetime')
#     group_list = [{k: list({i.site.name: i.id, 'total': sum(1 for x in g)}  for i in g)}
#                   for k, g in itertools.groupby(q_set, lambda task: task.start_datetime.strftime(group_by))]
#     return group_list


def util_get_task_line_graph_data_site(group_by, q_set):
    q_set = q_set.filter(site__isnull=False).order_by('start_datetime')
    group_list = [{k: [{c: len(list(a))} for c, a in itertools.groupby(g, lambda g: g.site.name)]} for k, g in itertools.groupby(q_set, lambda task: task.start_datetime.strftime(group_by))]
    return group_list


def util_get_task_line_graph_data_zone(group_by, q_set):
    q_set = q_set.filter(zone__isnull=False).order_by('start_datetime')
    group_list = [{k: [{c: len(list(a))} for c, a in itertools.groupby(g, lambda g: g.zone.name)]} for k, g in
                                itertools.groupby(q_set, lambda task: task.start_datetime.strftime(group_by))]
    return group_list


# def util_get_task_line_graph_data_test(q_set):
#     # q_set = q_set.order_by('start_datetime')
#     group_list = [{k: [{c: len(list(a))} for c, a in
#                                 itertools.groupby(g, lambda g: g.violations_type.label)]} for k, g in
#                                 itertools.groupby(q_set, lambda viol: viol.zone.name)]
#
#     return group_list



def get_employee_subordinates(employee_id):
    if employee_id:
        #admin = User.objects.get(associated_entity_id=employee_id)
        result= []
        inner_dict = {}
        try:
            employee = Entity.objects.get(id=employee_id)
            if employee.entity_sub_type.id == FFPOptionsEnum.SITE_SUPERVISOR:
                try:
                    assigned_site = Assignment.objects.get(child=employee,
                                                       type_id = DeviceTypeAssignmentEnum.SITE_EMPLOYEE_ASSIGNMENT).parent

                    assigned_zones = Assignment.objects.filter(parent = assigned_site,
                                                                   type_id = DeviceTypeAssignmentEnum.SITE_ZONE_ASSIGNMENT).values('child_id')
                    if assigned_zones:
                        zone_supervisors = Assignment.objects.filter(parent_id__in = assigned_zones,
                                                      type_id = DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT,
                                                      child__entity_sub_type_id = FFPOptionsEnum.ZONE_SUPERVISOR).values('child_id')

                    supervisors = Entity.objects.filter(id__in=zone_supervisors)
                    zone_supervisors_data = EmployeeSerializer(supervisors, many=True)

                    result = zone_supervisors_data.data

                    for obj in result:

                        inner_dict['site_supervisor'] = employee.name
                        inner_dict['zone_supervisor'] = None
                        inner_dict['team_supervisor'] = None

                        obj['management'] = inner_dict


                    #return result
                except:
                    assigned_site = None
            if employee.entity_sub_type.id == FFPOptionsEnum.ZONE_SUPERVISOR:
                assigned_zones = Assignment.objects.filter(child=employee,
                                                           type_id = DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT).values('parent_id')
                if assigned_zones:
                    assigned_site = Assignment.objects.filter(child_id__in=assigned_zones,
                                                              type_id = DeviceTypeAssignmentEnum.SITE_ZONE_ASSIGNMENT)[0].parent_id

                    zone_labors = Assignment.objects.filter(parent_id__in = assigned_zones,
                                                            type_id=DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT,
                                                            child__entity_sub_type_id = FFPOptionsEnum.LABOUR).values('child_id')

                    team_leads = Assignment.objects.filter(parent_id__in = assigned_zones,
                                                           type_id = DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT,
                                                           child__entity_sub_type_id = FFPOptionsEnum.TEAM_SUPERVISOR).values('child_id')

                    labors = Entity.objects.filter(id__in=zone_labors)


                    team_supervisors = Entity.objects.filter(id__in =team_leads)
                    employees_union = team_supervisors.union(labors)

                    employees_union_data = EmployeeSerializer(employees_union, many=True)

                    result = employees_union_data.data

                    for obj in result:

                        try:
                            site_supervisor = Assignment.objects.get(parent_id=assigned_site,
                                                                 type_id=DeviceTypeAssignmentEnum.SITE_EMPLOYEE_ASSIGNMENT,
                                                                 child__entity_sub_type_id=FFPOptionsEnum.SITE_SUPERVISOR).child.name

                        except:
                            site_supervisor=None

                        inner_dict['site_supervisor'] = site_supervisor
                        inner_dict['zone_supervisor'] = employee.name

                        if obj['entity_sub_type'] == FFPOptionsEnum.LABOUR:
                            inner_dict['team_supervisor'] = team_supervisors[0].name
                        else:
                            inner_dict['team_supervisor'] = None
                        obj['management'] = inner_dict


            if employee.entity_sub_type.id == FFPOptionsEnum.TEAM_SUPERVISOR:
                try:
                    assigned_zone = Assignment.objects.get(child_id=employee.id,
                                                       type_id=DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT).parent_id

                    team_labors = Assignment.objects.filter(parent=assigned_zone,
                                                            type_id=DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT,
                                                            child__entity_sub_type_id=FFPOptionsEnum.LABOUR).values('child_id')
                    try:
                        zone_supervisor = Assignment.objects.get(parent_id = assigned_zone,
                                                             type_id=DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT,
                                                             child__entity_sub_type_id=FFPOptionsEnum.ZONE_SUPERVISOR).child.name

                        try:
                            site = Assignment.objects.get(child_id=assigned_zone,
                                                          type_id = DeviceTypeAssignmentEnum.SITE_ZONE_ASSIGNMENT).parent_id
                            try:
                                site_supervisor = Assignment.objects.get(parent_id=site,
                                                                         type_id = DeviceTypeAssignmentEnum.SITE_EMPLOYEE_ASSIGNMENT,
                                                                         child__entity_sub_type_id=FFPOptionsEnum.SITE_SUPERVISOR).child.name
                                print(site_supervisor)
                            except Exception as e:
                                print(e)
                                site_supervisor = None
                        except Exception as e:
                            print(e)
                            site=None
                    except Exception as e:
                        print(e)
                        zone_supervisor=None
                except:
                    assigned_zone = None


                if team_labors:
                    labors = Entity.objects.filter(id__in=team_labors)
                    labors_data = EmployeeSerializer(labors, many=True)
                    result=labors_data.data

                    for obj in result:
                        inner_dict['site_supervisor'] = site_supervisor
                        inner_dict['zone_supervisor'] = zone_supervisor
                        inner_dict['team_supervisor'] = employee.name
                    obj['management'] = inner_dict


            return result
        except Exception as e:
            print (e)
            return None


def violations_list(s_id,z_id, e_id, start_datetime,end_datetime):
    if s_id:
        result = EmployeeViolations.objects.filter(site_id=s_id)
    if e_id:
        result = EmployeeViolations.objects.filter(employee_id=e_id)
    if result and z_id:
        print("ZONES ARE: ", z_id)
        result = result.filter(zone_id__in = z_id)

    if start_datetime and end_datetime:
        result = result.filter(created_datetime__range = [start_datetime,end_datetime])

    return result.order_by('-violations_dtm')


def create_zones_list(s_id):
    if s_id:
        zones = Assignment.objects.filter(parent_id=s_id,
                                  type_id = DeviceTypeAssignmentEnum.SITE_ZONE_ASSIGNMENT,
                                          status_id = OptionsEnum.ACTIVE).values('child_id')

    else:
        zones = None

    return zones

def create_violation_data(attendace_record, violation_type, active_status=None):
    violation = EmployeeViolations(
        customer=attendace_record.customer,
        module = attendace_record.module,
        created_datetime = timezone.now(),
        employee = attendace_record.employee,
        violations_type_id = violation_type,
        violations_dtm = timezone.now(),
        zone = attendace_record.zone,
        site = attendace_record.site,
        active_status_id = active_status
    )
    return violation


def get_ffp_last_data(c_id, e_id):
    if c_id and e_id:
        data = HypernetPostData.objects.filter(customer_id=c_id, device_id=e_id, timestamp__date=timezone.now().date()).first()
    else:
        data = None

    if data:
        return data


def calculate_entity_productivty(e_id, day):
    employee_tasks_completed = Tasks.objects.filter(assignee_id=e_id,
                                                    task_status_id=IOFOptionsEnum.COMPLETED, approved=True,
                                                    start_datetime__date__gte=day,
                                                    end_datetime__date__lte=day).count()

    employee_tasks_total = Tasks.objects.filter(assignee_id=e_id,
                                                start_datetime__date__gte=day,
                                                end_datetime__date__lte=day).count()

    if employee_tasks_total > 0:
        productivity = (employee_tasks_completed / employee_tasks_total) * 100
    else:
        productivity = 0
    return productivity


def get_attendance_record(e_id, c_id, start_datetime, end_datetime):
    if e_id:
        a_records = AttendanceRecord.objects.filter(customer_id = c_id, employee_id = e_id)
    else:
        a_records = AttendanceRecord.objects.filter(customer_id = c_id)

    if start_datetime and end_datetime:
        a_records = a_records.filter(created_datetime__range = [start_datetime,end_datetime])
    return  a_records


def get_employee_supervisor(e_id, c_id, user=None):
    if e_id:
        #user = User.objects.get(id=user.id)
        try:
            entity = Entity.objects.get(pk=e_id)
        except:
            entity = None
        if entity:
            if entity.entity_sub_type.id == FFPOptionsEnum.SITE_SUPERVISOR:
                assigned_supervisor = None
            elif entity.entity_sub_type.id == FFPOptionsEnum.ZONE_SUPERVISOR:
                assigned_zone = Assignment.objects.get(child_id = entity.id,
                                                       type_id = DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT,
                                                       ).parent_id
                assigned_site = Assignment.objects.get(child_id=assigned_zone, type_id = DeviceTypeAssignmentEnum.SITE_ZONE_ASSIGNMENT
                                                       ).parent_id

                assigned_supervisor = Assignment.objects.filter(parent_id=assigned_site,
                                                             type_id = DeviceTypeAssignmentEnum.SITE_EMPLOYEE_ASSIGNMENT)


            elif entity.entity_sub_type.id == FFPOptionsEnum.TEAM_SUPERVISOR:
                assigned_zone = Assignment.objects.get(child_id=entity.id,
                                                       type_id=DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT,
                                                       ).parent_id

                assigned_supervisor = Assignment.objects.filter(parent_id=assigned_zone,
                                                             type_id=DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT,
                                                             child__entity_sub_type_id= FFPOptionsEnum.ZONE_SUPERVISOR)

            elif entity.entity_sub_type.id == FFPOptionsEnum.LABOUR:
                assigned_zone = Assignment.objects.get(child_id=entity.id,
                                                       type_id=DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT,
                                                       ).parent_id
                print(assigned_zone)
                assigned_supervisor = Assignment.objects.filter(parent_id=assigned_zone,
                                                             type_id=DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT,
                                                             child__entity_sub_type_id=FFPOptionsEnum.TEAM_SUPERVISOR)

            if assigned_supervisor:
                assigned_supervisor = assigned_supervisor[0].child.name
            return assigned_supervisor


def calculate_emp_durations_site_active(obj):
    from ffp.cron_utils import get_active_hours_site
    violations_now = EmployeeViolations.objects.filter(violations_dtm__date=timezone.now().today().date(), employee=obj)
    duration_in_site = get_active_hours_site(emp_id=obj.id, date=timezone.now().date(), viol_q_set_site=violations_now)
    return duration_in_site


def calculate_emp_durations_zone_active(obj):
    from ffp.cron_utils import get_active_hours_zone
    violations_now = EmployeeViolations.objects.filter(violations_dtm__date=timezone.now().today().date(), employee=obj)
    duration_in_zone = get_active_hours_zone(emp_id=obj.id, date=timezone.now().date(), viol_q_set_zone=violations_now)
    return duration_in_zone

def calculate_emp_durations_site(obj):
        from ffp.cron_utils import get_durations_site
        violations_now = EmployeeViolations.objects.filter(violations_dtm__date=timezone.now().today().date(), employee=obj)
        duration_in_site = get_durations_site(emp_id=obj.id, date=timezone.now().date(), viol_q_set_site=violations_now)
        return duration_in_site

def calculate_emp_durations_zone(obj):
        from ffp.cron_utils import get_durations_zone
        violations_now = EmployeeViolations.objects.filter(violations_dtm__date=timezone.now().today().date(), employee=obj)
        duration_in_zone = get_durations_zone(emp_id=obj.id, date=timezone.now().date(), viol_q_set_zone=violations_now)
        return duration_in_zone



def util_get_productivity_data_site(group_by, site_id, last_week):
    zones = Assignment.objects.filter(parent_id=site_id, status_id=OptionsEnum.ACTIVE, type_id=DeviceTypeAssignmentEnum.SITE_ZONE_ASSIGNMENT).values_list('child_id')
    q_set = FFPDataDailyAverage.objects.filter(zone_id__in=zones, timestamp__gte=last_week)
    q_set = q_set.values('zone__name', 'attendance_dtm').order_by('zone_id').annotate(avg_productive_hours=Avg('productive_hours')).order_by('zone_id')
    print(q_set)

    group_list = [{k: [{c:prod['avg_productive_hours'] for prod in a} for c, a in itertools.groupby(g, lambda g: g['zone__name'])]} for k, g in
                                itertools.groupby(q_set, lambda task: task['attendance_dtm'].strftime(group_by))]
    print(group_list)
    return group_list


def util_get_emp_over_time(e_id, site, zone, cust, att_obj):
    if e_id:
        if not att_obj.duration_in_site_active:
            att_obj.duration_in_site_active = 0

        if zone.squad_number:
            shift_time = zone.squad_number
        elif site.squad_number:
            shift_time = site.squad_number
        else:
            shift_time = CustomerPreferences.objects.get(customer_id=cust).shift_hours

        if att_obj.duration_in_site_active>shift_time:
            over_time = att_obj.duration_in_site_active-shift_time
        else:
            over_time= 0

        return over_time


def util_graphical_data_productivity(site_id, z_id, emp_id, start_datetime, end_datetime, group_by):
    if site_id:
        zones_of_sites = Assignment.objects.filter(type_id=DeviceTypeAssignmentEnum.SITE_ZONE_ASSIGNMENT,
                                                                   parent=site_id, status_id=OptionsEnum.ACTIVE).values('child_id')

        avg_data = FFPDataDailyAverage.objects.filter(zone_id__in = zones_of_sites,
                                           timestamp__range = [start_datetime,end_datetime])

    elif z_id:
        avg_data = FFPDataDailyAverage.objects.filter(zone_id=z_id,
                                                      timestamp__range=[start_datetime, end_datetime])

    elif emp_id:
        avg_data = AttendanceRecord.objects.filter(employee_id=emp_id,
                                                   attendance_dtm__range=[start_datetime, end_datetime])\
            .values('employee', 'attendance_dtm').annotate(employee_prod_hrs = Avg('productive_hours')).values('employee_prod_hrs', 'attendance_dtm')

    final_list = []
    list = []

    if site_id or z_id:
        grouped = itertools.groupby(avg_data, lambda alert: alert.timestamp.strftime(group_by))
    elif emp_id:
        grouped = itertools.groupby(avg_data, lambda alert: alert['attendance_dtm'].strftime(group_by))
    # print (len(grouped))
    alerts_dict = {}
    if site_id or z_id:
        for time, alerts_this_day in grouped:
            # print(len(alerts_this_day))
            for obj in alerts_this_day:
                list = []
                zone_dict = {}
                zone_dict[obj.zone.name] = obj.zone_productivity_avg
                list.append(zone_dict)
            alerts_dict[time] = list
        final_list.append(alerts_dict)
        print(final_list)

    elif emp_id:
        for time, alerts_this_day in grouped:
            for obj in alerts_this_day:
                list = []
                zone_dict = {}
                zone_dict['prodcutivity_percentage'] = obj['employee_prod_hrs']
                list.append(zone_dict)
            alerts_dict[time] = list
        final_list.append(alerts_dict)
        # print(final_list)

    return final_list


def get_employee_todays_data(e_id):
    from ffp.cron_utils import get_active_hours_site, get_productivity

    r_dict = {}
    violations_now = EmployeeViolations.objects.filter(violations_dtm__date=timezone.now().today().date(), employee_id=e_id)
    duration_in_site = get_active_hours_site(emp_id=e_id, date=timezone.now().date(), viol_q_set_site=violations_now)

    try:
        zone = Assignment.objects.get(child_id=e_id, status_id=OptionsEnum.ACTIVE,
                                      type_id=DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT).parent
    except:
        zone = None
    try:
        site = Assignment.objects.get(child=zone, status_id=OptionsEnum.ACTIVE,
                                      type_id=DeviceTypeAssignmentEnum.SITE_ZONE_ASSIGNMENT).parent
    except:
        site = None

    productivity = get_productivity(c_id=site.customer_id, dur_active=duration_in_site, site=site, zone=None)

    ent = Entity.objects.get(pk=e_id)
    try:
        atten_rec = AttendanceRecord.objects.get(employee=ent, site_checkin_dtm__date=timezone.now().date(), present=True)
    except:
        atten_rec = None

    r_dict['in_zone_active_duration'] = calculate_emp_durations_zone_active(ent)
    r_dict['in_site_active_duration'] = calculate_emp_durations_site_active(ent)
    r_dict['clock_in_time'] = atten_rec.site_checkin_dtm if atten_rec else None
    r_dict['last_clock_out_time'] = atten_rec.site_checkout_dtm if atten_rec.site_checkout_dtm and atten_rec else None
    # r_dict['in_site_active'] = atten_rec.site_checkout_dtm if atten_rec else None #FIXME ???
    r_dict['in_site_duration'] = calculate_emp_durations_site(ent)
    r_dict['in_zone_duration'] = calculate_emp_durations_zone(ent)
    r_dict['productivity'] = productivity

    return r_dict



def calculate_emp_productivity(emp):
    from ffp.cron_utils import get_active_hours_zone
    try:
        emp = AttendanceRecord.objects.get(employee=emp, attendance_dtm__date = timezone.now().date().today(),
                                           present = True)
    except:
        emp = None
    try:
        prefrences = CustomerPreferences.objects.get(customer=emp.customer)
    except:
        prefrences = None
    if emp:
        zone = emp.zone
        if zone.squad_number:
            shift_time = zone.squad_number
        else:
            if prefrences:
                shift_time = prefrences.shift_hours

        violations_now = EmployeeViolations.objects.filter(violations_dtm__date=timezone.now().today().date(),
                                                           employee=emp)
        duration_in_zone = get_active_hours_zone(emp_id=emp.id, date=timezone.now().date(),
                                                 viol_q_set_zone=violations_now)


        shift_time = round(shift_time/60,0)
        duration_in_zone = round(duration_in_zone/60,0)

        productivity = duration_in_zone/shift_time*100
        return productivity


def get_sites_zones_of_employee(e_id):
    if e_id:
        entity = Entity.objects.get(pk=e_id)
        if entity.entity_sub_type.id in [FFPOptionsEnum.TEAM_SUPERVISOR, FFPOptionsEnum.ZONE_SUPERVISOR, FFPOptionsEnum.LABOUR]:
            try:
                assigned_zone = Assignment.objects.get(child_id = e_id, type_id =DeviceTypeAssignmentEnum.ZONE_EMPLOYEE_ASSIGNMENT, status_id= OptionsEnum.ACTIVE)
            except:
                assigned_zone = None

            try:
                assigned_site = Assignment.objects.get(child_id=assigned_zone.parent.id,
                                                       type_id=DeviceTypeAssignmentEnum.SITE_ZONE_ASSIGNMENT, status_id= OptionsEnum.ACTIVE)

            except:
                assigned_site = None

        else:
            assigned_site = Assignment.objects.get(child_id = e_id, type_id = DeviceTypeAssignmentEnum.SITE_EMPLOYEE_ASSIGNMENT, status=OptionsEnum.ACTIVE)

        assigned_zones = Assignment.objects.filter(parent_id = assigned_site.parent.id,
                                                           type_id=DeviceTypeAssignmentEnum.SITE_ZONE_ASSIGNMENT, status_id= OptionsEnum.ACTIVE)
        return  assigned_zones


