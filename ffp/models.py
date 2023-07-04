from django.db import models
from django.utils import timezone
# Create your models here.


#TODO Model to keep violations data for reporting.

#TODO Model to keep emplyee shifts and hours worked.
from django.db.models import PROTECT

from customer.models import Customer
from hypernet.models import Entity
from options.models import Options
from user.models import Module
from backend import settings

# class EmployeeAttendance(object):
#     def check_attendance(self):
#         pass
#
#     class Meta:
#         managed = False


#FIXME: Replace as Model before migration.
class AttendanceRecord(models.Model):
    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)
    created_datetime = models.DateTimeField(auto_now_add=True, db_index=True)
    last_updated = models.DateTimeField(auto_now=True, blank=True)
    attendance_dtm = models.DateTimeField(null=True, blank=True)

    employee = models.ForeignKey(Entity, related_name='ffp_attendance_record')
    attendance_type = models.ForeignKey(Options, related_name='attendance_type', null=True,blank=True)
    site_checkin_dtm = models.DateTimeField(blank=True, null=True)
    zone_checkin_dtm = models.DateTimeField(blank=True, null=True)
    site_checkout_dtm = models.DateTimeField(blank=True, null=True)
    zone_checkout_dtm = models.DateTimeField(blank=True, null=True)
    zone = models.ForeignKey(Entity, related_name='zone_of_attendance', null=True, blank=True)
    site = models.ForeignKey(Entity, related_name='site_of_attendance', null=True, blank=True)
    duration_in_site = models.IntegerField(null=True, blank=True, default=0)
    duration_in_zone = models.IntegerField(null=True, blank=True, default=0)
    duration_in_site_active = models.IntegerField(null=True, blank=True, default=0)
    duration_in_zone_active = models.IntegerField(null=True, blank=True, default=0)
    zone_status = models.BooleanField(default=False)
    site_status = models.BooleanField(default=False)
    site_attendance = models.BooleanField(default=False)
    zone_attendance = models.BooleanField(default=False)
    present = models.BooleanField(default=False)

    #new field to check active/inactive status
    active_status = models.BooleanField(default=False)
    productive_hours = models.IntegerField(null=True, blank=True, default=0)


    def __str__(self):
        return self.employee.name+"'s attendance "+'status '+ str(self.present) +(str(self.attendance_dtm.date()) if self.attendance_dtm else 'No date available')



class EmployeeViolations(models.Model):
    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)
    created_datetime = models.DateTimeField(auto_now_add=True, db_index=True)

    employee = models.ForeignKey(Entity, related_name='ffp_violation')
    violations_type = models.ForeignKey(Options, related_name='employee_violations_type', null=True,blank=True)
    violations_dtm = models.DateTimeField(blank=True, null=True)
    zone = models.ForeignKey(Entity, related_name='zone_of_violation', null=True, blank=True)
    site = models.ForeignKey(Entity, related_name='site_of_violation', null=True, blank=True)
    active_status = models.ForeignKey(Options, related_name='employee_active_status', null=True,blank=True)
    # violation_end_dtm = models.DateTimeField(blank=True, null=True)
    def __str__(self):
        return  str(self.active_status.label if self.active_status else "None" ) + " " + str(self.created_datetime)+" "+ self.employee.name+"'s violation: "+self.violations_type.label if self.violations_type else "No title" +" status: "+self.active_status.label if self.active_status else "No Status "

class Tasks(models.Model):
    '''
        assignee:       represent the person/employee which has to complete the task.
        responsible:    represent the person responsible for verifying/approving the updates in the task status.
    '''

    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)
    created_datetime = models.DateTimeField(auto_now_add=True, blank=True, db_index=True)

    assignee = models.ForeignKey(Entity, related_name='task_assignee_entity', null=True, blank=True)
    responsible = models.ForeignKey(Entity, related_name='task_responsible_entity', null=True, blank=True)
    task_status = models.ForeignKey(Options, related_name='task_status_id', null=True,blank=True)
    zone = models.ForeignKey(Entity, related_name='zone_of_task', null=True, blank=True)
    site = models.ForeignKey(Entity, related_name='site_of_task', null=True, blank=True)
    #Date Fields for accounting the actual and designated timelines of tasks
    start_datetime = models.DateTimeField(null=True, blank=True, db_index=True)
    end_datetime = models.DateTimeField(null=True, blank=True, db_index=True)
    actual_start_datetime = models.DateTimeField(null=True, blank=True, db_index=True)
    actual_end_datetime = models.DateTimeField(null=True, blank=True, db_index=True)
    notification_sent = models.BooleanField(default=False)
    # Data generated when job is ended
    violations = models.IntegerField(default=0, null=True)
    title = models.CharField(null=True, blank=True, max_length=250)
    notes = models.CharField(null=True, blank=True, max_length=3000)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='task_modified_by')
    approved = models.BooleanField(default=False)

    def __str__(self):
        return self.assignee.name if self.assignee else "No name "+"'s task: "+self.title if self.title else "No title" + str(self.created_datetime)


# class EmployeeActivityData():


class FFPDataDailyAverage(models.Model):
    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)
    timestamp = models.DateTimeField(null=True, db_index=True, blank=True)

    employee = models.ForeignKey(Entity, related_name='ffp_average_device_id', null=True, blank=True)
    zone = models.ForeignKey(Entity, related_name='average_of_zone', null=True, blank=True)
    site = models.ForeignKey(Entity, related_name='average_of_site', null=True, blank=True)

    average = models.BooleanField(null=False, default=False)
    temperature = models.DecimalField(decimal_places=3, default=0, max_digits=20, null=True)
    ambient_temperature = models.DecimalField(decimal_places=3, default=0, max_digits=20, null=True)
    heart_rate = models.DecimalField(decimal_places=3, default=0, max_digits=20, null=True)
    site_productivity_avg = models.IntegerField(default=0, null=True, blank=True)
    zone_productivity_avg = models.IntegerField(default=0, null=True, blank=True)
    site_durations_avg = models.IntegerField(default=0, null=True, blank=True)
    zone_durations_avg = models.IntegerField(default=0, null=True, blank=True)

    def __str__(self):
        return str(self.employee.name if self.employee else 'Daily Average' + str(self.timestamp.date() if self.timestamp else timezone.now().date()) + self.site.name if self.site else "No Site " + self.zone.name if self.zone else "No Zone " )
