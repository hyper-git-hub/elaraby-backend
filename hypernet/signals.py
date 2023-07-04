import traceback

from ffp.cron_utils import get_employee_attendance

__author__ = 'nahmed'

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from hypernet.models import HypernetPreData
from ffp.models import AttendanceRecord, EmployeeViolations
from hypernet.enums import DeviceTypeEntityEnum, FFPOptionsEnum


post_save.connect(receiver, sender=HypernetPreData)
@receiver(post_save, sender=HypernetPreData)
def check_employee_attendance(sender, instance, **kwargs):
    try:
        if instance.device.type_id == DeviceTypeEntityEnum.EMPLOYEE:
            if instance.device.entity_sub_type and instance.device.entity_sub_type_id is not FFPOptionsEnum.SITE_SUPERVISOR:
                try:
                    employee_attendance = AttendanceRecord.objects.get(employee_id=instance.device_id, site_checkin_dtm__date=timezone.now().date(),
                                                                       site_checkin_dtm__isnull=False)
                except:
                    flag, site, zone, z_flag = get_employee_attendance(pre_data_obj=instance)
                    if flag:
                        save_attendance = AttendanceRecord()
                        save_attendance.customer = instance.customer
                        save_attendance.module = instance.module
                        save_attendance.employee = instance.device
                        save_attendance.attendance_dtm = instance.timestamp
                        #SITE
                        save_attendance.site_checkin_dtm = instance.timestamp
                        save_attendance.site_status = True
                        save_attendance.site = site
                        save_attendance.present = True
                        #ZONE
                        save_attendance.zone = zone
                        if z_flag is True:
                            save_attendance.zone_checkin_dtm = instance.timestamp
                            save_attendance.zone_status = True
                        save_attendance.last_updated = timezone.now()
                        save_attendance.save()

                        if site or zone:
                            try:
                                EmployeeViolations.objects.get(violations_dtm__date=timezone.now().date(), employee_id=instance.device_id,
                                                               violations_type_id=FFPOptionsEnum.IN_SITE)
                            except:
                                if site:
                                    violations_initial_site = EmployeeViolations()
                                    violations_initial_site.customer = instance.customer
                                    violations_initial_site.module = instance.module
                                    violations_initial_site.site = site
                                    violations_initial_site.employee = instance.device
                                    violations_initial_site.violations_dtm = instance.timestamp
                                    violations_initial_site.violations_type_id = FFPOptionsEnum.IN_SITE
                                    if zone:
                                        violations_initial_site.zone = zone
                                    violations_initial_site.save()

                            try:
                                EmployeeViolations.objects.get(violations_dtm__date=timezone.now().date(),
                                                                   employee_id=instance.device_id,
                                                                   violations_type_id=FFPOptionsEnum.IN_ZONE)
                            except:
                                if zone and (z_flag is True):
                                    print('Now Saving In Zone Violation')
                                    violations_initial_zone = EmployeeViolations()
                                    violations_initial_zone.customer = instance.customer
                                    violations_initial_zone.module = instance.module
                                    violations_initial_zone.zone = zone
                                    violations_initial_zone.employee = instance.device
                                    violations_initial_zone.violations_dtm = instance.timestamp
                                    violations_initial_zone.violations_type_id = FFPOptionsEnum.IN_ZONE
                                    if site:
                                        violations_initial_zone.site = site
                                    violations_initial_zone.save()

    except:
        traceback.print_exc()
