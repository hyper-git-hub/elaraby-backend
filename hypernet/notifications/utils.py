from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from hypernet.enums import OptionsEnum
from hypernet.utils import async_util
from hypernet.models import HypernetNotification, NotificationGroups
from options.models import Options
import requests
import json


@async_util
def send_push(one_signal_app_id, one_signal_rest_api_key, email, data={}, send_after=None):
    header = {"Content-Type": "application/json",
              "Authorization": "Basic " + one_signal_rest_api_key}

    payload = {"app_id": one_signal_app_id,
               "filters": [
                   {"field": "tag", "key": "email", "relation": "=", "value": email}
               ],
               "contents": {"en": "Notification from hypernet."},
               "data": data,
               }

    req = requests.post("https://onesignal.com/api/v1/notifications", headers=header, data=json.dumps(payload))
#    print(req.text)
 #   print(data)
    return str(req.status_code) + str(req.reason)


@async_util
def update_alert_status(id, c_id, status, flag_is_viewed=False):
    update_status = False
    try:
        q_set = HypernetNotification.objects.filter(id=id, customer=c_id)
        opt_obj = Options.objects.get(value=status)
        q_set.update(status=opt_obj, is_viewed=flag_is_viewed)
        update_status = True
    except:
        pass
    return update_status


def util_user_notifications(u_id, c_id, m_id):
    from hypernet.models import NotificationGroups
    q_set = NotificationGroups.objects.filter(user=u_id, is_viewed=False).count()
    alerts_list = []
    alerts_dict = {}
    alerts_dict['count'] = q_set
    alerts_list.append(alerts_dict)
    return alerts_list

#TODO REFACTOR BUG IN FLOW.
def update_alert_flag_status(u_id, c_id, m_id):
    q_set = HypernetNotification.objects.filter(customer=c_id, module_id=m_id)
    for users in q_set:
        obj = users.notificationgroups_set.filter(user=u_id, is_viewed=False)

        for u in obj.all():
            u.is_viewed = True
            u.save()
    return True


@receiver(post_save, sender=HypernetNotification)
def intercept_violations(sender, instance, **kwargs):
    from hypernet.enums import DeviceTypeEntityEnum, IOFOptionsEnum
    one_signal_rest_key = "NGZjYTJiOGUtNzBmOS00MDgxLWE1NjctOGZkZjg3NGVlMTdh"



    if one_signal_rest_key and instance.activity is not None and instance.activity.activity_schedule.activity_type_id == IOFOptionsEnum.BIN_COLLECTION_JOB and instance.status.id == OptionsEnum.ACTIVE:
        # For Job notifications
        app_id = 'f4201e3f-8a83-4e49-9936-59a9cb302be2'
        rest_key = 'NGZjYTJiOGUtNzBmOS00MDgxLWE1NjctOGZkZjg3NGVlMTdh'
        for user in instance.user.all():
            send_push(one_signal_app_id=app_id,
                      one_signal_rest_api_key=rest_key,
                      data={'title': instance.title,
                            'message': instance.description, 'job_id': instance.activity.id, 'notification_type': instance.type.id},
                      email=user.email)

    elif one_signal_rest_key and instance.activity is None and instance.status.id == OptionsEnum.ACTIVE:
        app_id = 'f4201e3f-8a83-4e49-9936-59a9cb302be2'
        rest_key = 'NGZjYTJiOGUtNzBmOS00MDgxLWE1NjctOGZkZjg3NGVlMTdh'
        for user in instance.user.all():
            send_push(one_signal_app_id=app_id,
                      one_signal_rest_api_key=rest_key,
                      data={'title': instance.title,
                            'message': instance.description,
                            'notification_type': instance.type.id},
                      email=user.email)

    elif one_signal_rest_key and instance.device.type_id == DeviceTypeEntityEnum.ANIMAL:
        for user in instance.user.all():
            send_push(one_signal_app_id='e760d0cd-6dd5-48aa-b671-64a28b6ad437',
                      one_signal_rest_api_key='N2MzYTFkNjctYTYxZS00ZTk2LThkNjAtNTFkN2FmMTk0NjRj',
                      data={'title': instance.title, 'id': instance.id, 'message': instance.description},
                      email='bilal@yahoo.com')
    #elif one_signal_rest_key and instance.job.type_id == DeviceTypeEntityEnum.MAINTENANCE:
     #   app_id = 'f4201e3f-8a83-4e49-9936-59a9cb302be2'
      #  rest_key = 'NGZjYTJiOGUtNzBmOS00MDgxLWE1NjctOGZkZjg3NGVlMTdh'
       # for user in instance.user.all():
        #    send_push(one_signal_app_id=app_id,
         #             one_signal_rest_api_key=rest_key,
          #            data={'title': instance.title,
           #                 'message': instance.description, 'job_id': instance.job.id},
            #          email=user.email)

    else:
        return None


def send_notification_to_user(obj, activity, user_list, title, type):
    from hypernet.enums import DeviceTypeEntityEnum
    notification = HypernetNotification(
        device=activity.primary_entity,
        driver=activity.actor,
        activity=activity,
        customer_id=obj.activity.activity_schedule.customer.id,
        module_id=obj.activity.activity_schedule.module.id,
        status_id=OptionsEnum.ACTIVE,
        timestamp=timezone.now(),
        description="Activity",
        title=title,
        type_id = type
    )
    notification.save()
    for user in user_list:
        gn = NotificationGroups(notification=notification,
                                user=user)
        gn.save()
    notification.save()



def util_save_activity_notification(obj, activity, users_list, title, type):
    notification = HypernetNotification(
        device=obj.activity.primary_entity,
        driver=activity.actor,
        activity_id=activity.id,
        customer_id=obj.activity_schedule.customer.id,
        module_id=obj.activity_schedule.module.id,
        status_id=OptionsEnum.ACTIVE,
        timestamp=timezone.now(),
        description="Activity",
        title=title,
        type_id = type
    )
    notification.save()
    for user in users_list: #[User.objects.get(associated_entity=obj.activity.actor)]:
        gn = NotificationGroups(notification=notification,
                                user=user)
        gn.save()
    notification.save()


def send_notification_to_admin(assigned_truck, driver_id, job, ent, users_list, title, type, threshold=None, value=None):
    notification = HypernetNotification(
        device_id=assigned_truck,
        driver_id=driver_id,
        activity_id=job,
        customer_id=ent.activity_schedule.customer.id,
        module_id=ent.activity_schedule.module.id,
        status_id=OptionsEnum.ACTIVE,
        timestamp=timezone.now(),
        # description=obj.description,
        title=title,
        type_id = type,
        threshold = threshold,
        value = value,
    )

    notification.save()
    for user in users_list:
        gn = NotificationGroups(notification=notification,
                                user_id=user)
        gn.save()
    notification.save()


def send_action_notification(assigned_truck, driver_id, job, ent, title, type, threshold=None, value=None):
    notification = HypernetNotification(
        device_id=assigned_truck,
        driver_id=driver_id,
        activity_id=job,
        customer_id=ent.customer.id,
        module_id=ent.module.id,
        status_id=OptionsEnum.ACTIVE,
        timestamp=timezone.now(),
        # description=obj.description,
        title=title,
        type_id = type,
        threshold = threshold,
        value = value,
    )

    return notification


def save_users_group(notification, users_list):
    for user in users_list:
        gn = NotificationGroups(notification=notification,
                                user_id=user)
        gn.save()
    notification.save()


def send_notification_violations(device, driver_id, customer_id, module_id, title, users_list, threshold=None, value=None):
    notification = HypernetNotification(
        device_id=device,
        driver_id=driver_id,
        customer_id=customer_id,
        module_id=module_id,
        status_id=OptionsEnum.ACTIVE,
        timestamp=timezone.now(),
        # description=obj.description,
        title=title,
        type_id = 1,
        threshold = threshold,
        value = value,
    )

    notification.save()
    for user in users_list:
        gn = NotificationGroups(notification=notification,
                                user=user)
        gn.save()
    notification.save()


