import string
import os
import random
from django.utils import timezone
import http.client
import mimetypes
import json
# ------------------------------#
from hypernet.constants import LAST_24_HOUR
from .models import User
from user.enums import RoleTypeEnum
from hypernet.enums import OptionsEnum, ModuleEnum
from django.utils.crypto import get_random_string


def reset_user_token_reset(user_email):
    if user_email:
        try:
            user = User.objects.get(email=user_email)
            chars = string.ascii_letters + string.digits + '!@$*()'
            random.seed = (os.urandom(1024))
            token = ''.join(random.choice(chars) for i in range(30))
            user.reset_token = token
            user.reset_token_datetime = timezone.now()
            user.save()

            return user

        except User.DoesNotExist:
            return False

    else:
        return False


def user_reset_verify(user_email, token):
    try:
        user = User.objects.get(email=user_email)
        now = timezone.now()
        token_time = user.reset_token_datetime
        if (token == user.reset_token) and (user.reset_token != "") and (
                (now - token_time).total_seconds() < LAST_24_HOUR):
            return user
        else:
            return False
    except User.DoesNotExist:
        return False


def user_password_reset(new_password, email):
    try:
        user = User.objects.get(email=email)
        user.make_password(new_password)
        user.save()
        user.reset_token = ""
        user.save()

        return user
    except User.DoesNotExist:
        user = None
        return user


def info_bip_message(user, random_code):
    conn = http.client.HTTPSConnection("wp1z41.api.infobip.com")
    payload = {
        "messages": [
            {
                "from": "Elaraby",
                "destinations": [
                    {
                        "to": user.contact_number,
                        "messageId": "MESSAGE-ID-" + str(random_code)
                    }
                ],
                "text": "Welcome to Tornado Smart Home! Your verification pin is " + str(random_code),
                "flash": False,
                "language": {
                    "languageCode": "EN"
                },
                "transliteration": "ENGLISH",
                "notifyContentType": "application/json",
                "validityPeriod": 720
            }
        ],
        "bulkId": "BULK-ID-123-xyz",
        "tracking": {
            "track": "SMS",
            "type": "MY_CAMPAIGN"
        }
    }
    headers = {
        'Authorization': 'App 477d63c869bc62e06b6928f8ea6d0ce2-7a0a64f8-78eb-4cb0-9f7d-6383b11f8236',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    payload = json.dumps(payload)
    print(payload, 'OTP payload')
    conn.request("POST", "/sms/2/text/advanced", payload, headers)
    res = conn.getresponse()
    res.status = 200
    return res.status


def save_user_signup_confirm_code(user_confirm, device_info):
    user = User()
    user.customer = user_confirm.customer
    user.email = '{}.{}{}@elaraby.com'.format(user_confirm.first_name, user_confirm.last_name,
                                              get_random_string(length=5,
                                                                allowed_chars='0123456789'))  # making email with first,last name along with rand string because of design limitations
    # (since uniqueness of user depends upon ph_no and not email, however in our model, email will always be unique)
    user.password = user_confirm.reset_token
    user.role_id = RoleTypeEnum.USER
    user.status_id = OptionsEnum.ACTIVE
    user.preferred_module = ModuleEnum.IOP
    user.contact_number = user_confirm.contact_number
    user.reset_token = str(user_confirm.reset_token)  # get_random_string(length=6, allowed_chars='0123456789')
    user.first_name = user_confirm.first_name
    user.last_name = user_confirm.last_name
    user.last_login = timezone.now()
    user.android_device_info = json.dumps(device_info)
    user.save()
    print(user)
