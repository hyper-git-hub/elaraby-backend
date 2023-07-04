from django.db import models


# Create your models here.

class Template(models.Model):
    ETYPE = (('internal', "This email will be sent internally and can be mute from edit user. "),
             ('external', "This email will be sent to user & can be mute from notification settings."),
             ('system', "This email will be sent system wide and can't be mute."))

    email_key = models.CharField(max_length=255, unique=True, null=False)
    subject = models.CharField(max_length=255, null=False)
    from_email = models.CharField(max_length=255)
    email_body = models.TextField(null=False)
    dtm = models.DateTimeField(null=True, blank=True)
    to_list = models.TextField(null=True, blank=True)
    # New Feilds
    cc_list = models.TextField(null=True, blank=True)
    bcc_list = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    placeholders = models.TextField(null=True, blank=True)
    email_type = models.CharField(max_length=200, null=True, blank=True, choices=ETYPE)

    def __unicode__(self):
        return u'%s' % self.msg_title

    def __str__(self):
        return self.email_key
