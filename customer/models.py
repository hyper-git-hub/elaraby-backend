from django.db import models
from django.db.models import PROTECT
from backend import settings
from hypernet.enums import SubModuleEnum
from options.models import Options
from django.contrib.postgres.fields import JSONField

# Create your models here.
class Customer(models.Model):
    name = models.CharField(max_length=50, blank=False)
    subscription_is_valid = models.BooleanField(blank=False, default=True)
    status = models.ForeignKey(Options)
    created_datetime = models.DateTimeField(auto_now_add=True, db_index=True)
    end_datetime = models.DateTimeField(blank=True, null=True)
    one_signal_app_id = models.CharField(blank=True, null=True, max_length=50)
    one_signal_rest_api_key = models.CharField(blank=True, null=True, max_length=50)

    # TODO Migrate after specification is finailized
    # allowed_modules = JSONField(null=True, blank=True, max_length=100)


    # Theme
    def __str__(self):
        return self.name

    def natural_key(self):
        return self.name


class CustomerPreferences(models.Model):
    # All defaults represent Minutes..

    customer = models.ForeignKey(Customer)
    # Activity Review part. admin can change bool field to False, IF false review feature  will be OFF.
    activity_review = models.BooleanField(default=True)
    activity_review_admin_buffer = models.IntegerField(default=5)
    activity_accept_driver_buffer = models.IntegerField(default=5)
    activity_start_driver_buffer = models.IntegerField(default=5)

    # Activity Notifications
    activity_start = models.BooleanField(default=True)
    activity_end = models.BooleanField(default=True)
    activity_reject = models.BooleanField(default=True)
    activity_accept = models.BooleanField(default=True)
    activity_suspend = models.BooleanField(default=True)
    activity_resume = models.BooleanField(default=True)
    activity_abort = models.BooleanField(default=True)

    activity_accept_reject_buffer = models.IntegerField(default=1440)

    activity_start_buffer = models.IntegerField(default=60)
    average_activity_time = models.IntegerField(default=180)

    enable_accept_reject = models.BooleanField(default=True)

    #Shift Notifications
    shift_start = models.BooleanField(default=True)
    shift_end = models.BooleanField(default=True)

    #Bin and waste notifications
    bin_pickup =  models.BooleanField(default=True)
    bin_dropoff = models.BooleanField(default=True)
    waste_collection = models.BooleanField(default=True)

    #Violation notifications.
    speed_violations = models.BooleanField(default=True)
    territory_violations = models.BooleanField(default=True)
    speed_violation_global = models.IntegerField(default=60)

    #Add Assets notifications
    assets_notification = models.BooleanField(default=False)

    value_added_tax = models.FloatField(default=5)
    company_name = models.TextField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    phone_no = models.TextField(null=True, blank=True)
    fax_no = models.TextField(null=True, blank=True)
    email = models.TextField(null=True, blank=True)
    url = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.customer.name + "'s  " + "Preferences"

    def get_vat_percentage(self):
        return (self.value_added_tax/100)

class CustomerClients(models.Model):
    address = models.CharField(null=True, blank=True, max_length=300)
    name = models.CharField(null=True, blank=True, max_length=100)
    customer = models.ForeignKey(Customer, blank=True, null=True, on_delete=PROTECT)
    contact_number = models.CharField(blank=True, null=True, max_length=50)
    email = models.CharField(blank=True, null=True, max_length=100)
    status = models.ForeignKey(Options, on_delete=PROTECT)
    description = models.CharField(null=True, blank=True, max_length=200)
    party_code = models.CharField(null=True, blank=True, max_length=50)

    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL)
    created_datetime = models.DateTimeField(auto_now_add=True, db_index=True)
    modified_datetime = models.DateTimeField(blank=True, null=True)
    end_datetime = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        if self.party_code:
            return self.party_code+' - ( '+self.name+' )'
        else:
            return self.name

    def get_delete_name(self):
       return str(self.name + " - "+self.party_code)

