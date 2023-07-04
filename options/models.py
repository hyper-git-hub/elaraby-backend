from django.db import models

# Create your models here.
class Options(models.Model):
    # Key is the name to be displayed, active, inactive, speed high, etc
    key = models.CharField(max_length=100)
    # Value is the name of the group, recordstatus, violationtype, jobstatus, etc
    value = models.CharField(max_length=100)
    label = models.CharField(max_length=100)
    module = models.IntegerField(default=0)


    def __str__(self):
        return self.key+'-'+self.value

    def natural_key(self):
        return self.key

    @property
    def real_value(self):
        return self.__dict__['value']

    def option_as_dict(self):
        return {'label': self.label, 'id': self.id}