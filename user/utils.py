import string
import os
import random
from django.utils import timezone

#------------------------------#
from hypernet.constants import LAST_24_HOUR
from .models import User





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

