from hypernet.models import Entity, Assignment
from iof.models import ActivityData
from hypernet.enums import *
import datetime
import hypernet.constants as const


def maintenance_cron_job():
    maintenance = ActivityData.objects.all()  # .filter(some_flag)
    for obj in maintenance:
        assigned_truck = obj.device
        assigned_driver = Assignment.objects.filter(parent_id=obj.device,
                                                    child__type=DeviceTypeEntityEnum.DRIVER).values_list('child')
        if assigned_driver:
            due_time = obj.timestamp.date()
            notify_time = due_time - datetime.timedelta(days=const.LAST_TWO_DAYS)
            if datetime.date.today() == notify_time:
                pass

            # TODO entry in notifications table.
