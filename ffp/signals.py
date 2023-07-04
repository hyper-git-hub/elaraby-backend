from ffp.cron_utils import get_users_list
from hypernet.enums import OptionsEnum
from hypernet.models import HypernetNotification, NotificationGroups

__author__ = 'nahmed'

from ffp.models import EmployeeViolations
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
import traceback


post_save.connect(receiver, sender=EmployeeViolations)
@receiver(post_save, sender=EmployeeViolations)
def violation_notifications_ffp(sender, instance, **kwargs):
    try:
        users_list = get_users_list(obj=instance)
        notify_users = HypernetNotification()
        notify_users.device = instance.employee
        notify_users.violation_type_id = instance.violations_type_id
        notify_users.type_id = instance.violations_type_id
        notify_users.timestamp = instance.violations_dtm
        notify_users.status_id = OptionsEnum.ACTIVE
        notify_users.customer = instance.customer
        notify_users.module = instance.module
        notify_users.title = instance.employee.name+' is '+instance.violations_type.label
        if instance.active_status:
            notify_users.title += ' and is '+instance.active_status.label
        notify_users.save()

        for user in users_list:
            gn = NotificationGroups(notification=notify_users, user_id=user)
            gn.save()

    except:
        print("Violation Signal: ")
        traceback.print_exc()