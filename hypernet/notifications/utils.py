import traceback

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import pyrebase

from backend import settings
from hypernet.enums import OptionsEnum
from hypernet.utils import async_util
from hypernet.models import HypernetNotification, NotificationGroups
from options.models import Options
import requests
import json

from user.models import User


@async_util
def send_push(one_signal_app_id, one_signal_rest_api_key, email, data={}, send_after=None):
    header = {"Content-Type": "application/json",
              "Authorization": "Basic " + one_signal_rest_api_key}

    payload = {"app_id": one_signal_app_id,
               "filters": [
                   {"field": "tag", "key": "email", "relation": "=", "value": email}
               ],
               "contents": {"en": data['title']},
               "data": data,
               }

    req = requests.post("https://onesignal.com/api/v1/notifications", headers=header, data=json.dumps(payload))
    print(req.text)
    print(data)
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


def util_user_notifications(u_id, c_id=None, m_id=None):
    from hypernet.models import NotificationGroups
    q_set = NotificationGroups.objects.filter(user=u_id, is_viewed=False).count()
    alerts_list = []
    alerts_dict = {}
    alerts_dict['count'] = q_set
    alerts_list.append(alerts_dict)
    return alerts_list


def update_alert_flag_status(u_id, c_id, m_id):
    '''

    :param u_id: User id, whose notification needs to be flushed
    :param c_id: Customer
    :param m_id: module
    :return: True if Success
    '''

    q_set = HypernetNotification.objects.filter(customer=c_id, module_id=m_id)

    try:
        users = User.objects.filter(pk=u_id)
        user = users[0]
        firebase = pyrebase.initialize_app(settings.config_firebase)
        db = firebase.database()
        if db and user:
            try:
                if db and firebase:
                    db.child(str(user.email).replace('.', '-')).set(0)
                    # db.child(str(user.email).replace('.', '-')+'-text').set(instance.title+"|"+ instance.description if instance.title and instance.description else "Alert|You have a new notification")
            except:
                traceback.print_exc()
                pass

        obj = NotificationGroups.objects.filter(user=user, is_viewed=False)
        print(obj.count())
        for o in obj:
            o.is_viewed=True
            o.save()


    except:
        traceback.print_exc()
        user = None


    return True

    '''
    for users in q_set:
        try:
            firebase = pyrebase.initialize_app(settings.config_firebase)
            db = firebase.database()
            if db:
                try:
                    user = User.objects.get(pk=u_id)
                except:
                    user = None
                if user:
                    try:
                        if db and firebase:
                            db.child(str(user.email).replace('.', '-')).set(0)
                        # db.child(str(user.email).replace('.', '-')+'-text').set(instance.title+"|"+ instance.description if instance.title and instance.description else "Alert|You have a new notification")
                    except:
                        print(user.email)
                        traceback.print_exc()
                        pass
        except:  # TODO Find Exception sets of FireBase Connections.
            traceback.print_exc()
            db = None
        obj = users.notificationgroups_set.filter(user=u_id, is_viewed=False)
        for u in obj.all():
            u.is_viewed = True
            u.save()

    return True
    '''

@receiver(post_save, sender=HypernetNotification)
def intercept_violations(sender, instance, **kwargs):
    from hypernet.enums import DeviceTypeEntityEnum, IOFOptionsEnum
    # one_signal_rest_key = "NGZjYTJiOGUtNzBmOS00MDgxLWE1NjctOGZkZjg3NGVlMTdh"
    one_signal_rest_key = "ZjEwNDM3NmItMjcxOS00ZDlkLWJjNmQtNDFhMzdjMWI2OGY3" # production key
    try:
        firebase = pyrebase.initialize_app(settings.config_firebase)
        db = firebase.database()

    except: #TODO Find Exception sets of FireBase Connections.
        traceback.print_exc()
        db = None

    if one_signal_rest_key and instance.activity is not None and instance.activity.activity_schedule.activity_type_id == IOFOptionsEnum.BIN_COLLECTION_JOB and instance.status.id == OptionsEnum.ACTIVE:
        # For Job notifications
        # app_id = 'f4201e3f-8a83-4e49-9936-59a9cb302be2'
        # rest_key = 'NGZjYTJiOGUtNzBmOS00MDgxLWE1NjctOGZkZjg3NGVlMTdh'
        app_id = '3d9e70b0-11ac-4375-9dee-6fa5036d2591' #for production
        rest_key = 'ZjEwNDM3NmItMjcxOS00ZDlkLWJjNmQtNDFhMzdjMWI2OGY3'
        for user in instance.user.all():
            send_push(one_signal_app_id=app_id,
                      one_signal_rest_api_key=rest_key,
                      data={'title': instance.title,
                            'message': instance.description, 'job_id': instance.activity.id, 'notification_type': instance.type.id},
                      email=user.email)
            # duplicate notification for suez trucks. Avoid existing issues so redundant notification. Zenath will not be effected
            if instance.device.cnic:
                send_push(one_signal_app_id=app_id,
                          one_signal_rest_api_key=rest_key,
                          data={'title': instance.title,
                                'message': instance.description, 'job_id': instance.activity.id,
                                'notification_type': instance.type.id},
                          email=instance.device.cnic)


    elif one_signal_rest_key and instance.activity is None and instance.status.id == OptionsEnum.ACTIVE:
        app_id = '3d9e70b0-11ac-4375-9dee-6fa5036d2591'
        rest_key = 'ZjEwNDM3NmItMjcxOS00ZDlkLWJjNmQtNDFhMzdjMWI2OGY3' # production key
        # app_id = 'f4201e3f-8a83-4e49-9936-59a9cb302be2'
        # rest_key = 'NGZjYTJiOGUtNzBmOS00MDgxLWE1NjctOGZkZjg3NGVlMTdh'
        for user in instance.user.all():
            print("notification email:  ", user.email)
            send_push(one_signal_app_id=app_id,
                      one_signal_rest_api_key=rest_key,
                      data={'title': instance.title,
                            'message': instance.description,
                            'notification_type': instance.type.id},
                      email=user.email)


    if db:
        for user in instance.user.all():
            try:
                count = util_user_notifications(u_id=user)
                db.child(str(user.email).replace('.', '-')).set(count[0]['count'])
                # db.child(str(user.email).replace('.', '-')+'-text').set(instance.title+"|"+ instance.description if instance.title and instance.description else "Alert|You have a new notification")
            except:
                traceback.print_exc()
                pass


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


def send_notification_violations(device, driver_id, customer_id, module_id, title, users_list, threshold=None, value=None, type_id=1, description=None):
    try:
        notification = HypernetNotification(
            device_id=device,
            driver_id=driver_id,
            customer_id=customer_id,
            module_id=module_id,
            status_id=OptionsEnum.ACTIVE,
            timestamp=timezone.now(),
            description=description,
            title=title,
            type_id = type_id,
            threshold = threshold,
            value = value

        )

        print('notification called      ', notification)
        notification.save()
        print('notification check')
        for user in users_list:
            print(user.get_full_name(), "   ", user.contact_number)
            gn = NotificationGroups(notification=notification,
                                    user=user)
            gn.save()
        notification.save()
    except Exception as e:
        print(e)
