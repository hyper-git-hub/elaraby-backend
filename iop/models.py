from django.db import models
from django.db.models import PROTECT, CASCADE

from hypernet.models import Entity, Customer
from hypernet.models import Module
# Create your models here.
from options.models import Options


class IopDerived(models.Model):
    device = models.ForeignKey(Entity, related_name="iop_device_derived", on_delete=CASCADE)
    customer = models.ForeignKey(Customer)
    timestamp = models.DateTimeField(null=True, blank=True)
    # TODO: Meta information will be added as per requirement.
    total_errors = models.IntegerField(default=0, null=True, blank=True)
    active_duration = models.IntegerField(default=0, null=True, blank=True)
    total_energy_consumed = models.IntegerField(default=0, null=True, blank=True)
    # average_energy_consumed = models.IntegerField(default=0, null=True, blank=True)
    average_temperature = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=3)

    def __str__(self):
        return str(self.device.name) + '-' + str(self.active_duration)


class IopAggregation(models.Model):
    # device = models.ForeignKey(Entity, related_name="iop_device_aggregation", on_delete=CASCADE)
    device = models.ForeignKey(Entity, related_name="iop_device_aggregation", on_delete=PROTECT)
    total_errors = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(null=True, blank=True)
    online_status = models.BooleanField(null=False, default=False)
    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)


# class IopDeviceErrors(models.Model):
#     device = models.ForeignKey(Entity, related_name="iop_device_errors", on_delete=PROTECT)
#     customer = models.ForeignKey(Customer)
#     timestamp = models.DateTimeField(null=True, db_index=True, blank=True)
#     error_code = models.IntegerField(default=0,null=True, blank=True)


class ApplianceQR(models.Model):
    ssid = models.CharField(max_length=200)
    password = models.CharField(max_length=200)
    created_datetime = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return str(self.ssid) + '-' + str(self.password) + '-' + str(self.created_datetime)


class EnergyConsumption(models.Model):
    device_id = models.ForeignKey(Entity)
    datetime = models.DateTimeField(db_index=True)
    energy_consumed = models.DecimalField(default=0, max_digits=20, decimal_places=2)
    ec_regular_appliance = models.DecimalField(default=0, max_digits=20, decimal_places=2)
    average_temperature = models.DecimalField(default=0, max_digits=20, decimal_places=2)
    average_ctt = models.DecimalField(default=0, max_digits=20, decimal_places=2)

    def __str__(self):
        return str(self.device_id.name) + '-' + str(self.datetime)


class ErrorLogs(models.Model):
    device = models.ForeignKey(Entity)
    datetime = models.DateTimeField(auto_now_add=True)
    err_datetime = models.DateTimeField()
    date = models.DateField(db_index=True, auto_now_add=True)
    inactive_score = models.DecimalField(default=0, max_digits=20, decimal_places=2)

    class Meta:
        db_table = 'error_logs'

    def __str__(self):
        return str(self.device_id) + ' - ' + str(self.date) + ' - ' + str(self.inactive_score)


class ReconfigurationTable(models.Model):
    device = models.ForeignKey(Entity)
    datetime = models.DateTimeField(auto_now_add=True)
    date = models.DateField(db_index=True, auto_now_add=True)
    failure_code = models.IntegerField(default=0)
    temperature_set = models.IntegerField(default=0)
    shs=models.IntegerField(default=3)

    class Meta:
        db_table = 'reconfiguration_table'

    def __str__(self):
        return str(self.device_id) + ' - ' + str(self.date) + ' - ' + str(self.failure_code)

class ReconfigurationLockMode(models.Model):
    device = models.ForeignKey(Entity)
    datetime = models.DateTimeField(auto_now_add=True)
    date = models.DateField(db_index=True, auto_now_add=True)
    failure_code = models.IntegerField(default=0)
    lock_mode = models.PositiveIntegerField(default=0)
    

    class Meta:
        db_table = 'Reconfiguration_lockMode'

    def __str__(self):
        return str(self.device_id) + ' - ' + str(self.date) + ' - ' + str(self.failure_code)


