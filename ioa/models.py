from django.db import models
from hypernet.models import Entity, DeviceType, DeviceViolation, HypernetNotification, BaseModel, CustomerDevice
from user.models import Module, User
from customer.models import Customer
from options.models import Options
from hypernet.utils import estrus_datetime_init


class Scheduling(BaseModel):
    alert = models.ForeignKey(HypernetNotification, related_name='notifications', null=True)
    animal = models.ManyToManyField(Entity)
    customer = models.ForeignKey(Customer, null=True)
    comments = models.CharField(max_length=250, null=True)
    routine_type = models.ForeignKey(Options, related_name='sch_routine_type', null=True)
    activity_type = models.ForeignKey(Options, related_name='sch_activity_type', null=True)
    scheduled_start_time = models.TimeField(null=True)
    scheduled_end_time = models.TimeField(null=True)
    scheduled_start_date = models.DateField(null=True)
    scheduled_end_date = models.DateField(null=True)

    created_by = models.ForeignKey(User, related_name='scheduling_created_by', null=True)
    modified_by = models.ForeignKey(User, related_name='scheduling_modified_by', null=True)
    scheduled_next_date= models.DateField(null=True)
    perform_individually = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    assigned_to = models.ForeignKey(User, related_name='staff_assingment')
    activity_priority = models.ForeignKey(Options, related_name='scheduling_priority', null=True)

    def to_dict(self):
        activity_list = {
            "id": self.id,
            "animals": [obj.animal_details_to_dict() for obj in self.animal.all()],
            "comments": self.comments,
            "routine_type": self.routine_type.value,
            "activity_type": self.activity_type.value,
            "scheduled_start_time": self.scheduled_start_time,
            "scheduled_end_time": self.scheduled_end_time,
            "scheduled_start_date": self.scheduled_start_date,
            "scheduled_end_date": self.scheduled_end_date,
            "perform_individually": self.perform_individually,
            "is_active": self.is_active,
            "assigned_to": self.assigned_to_id,
            "assigned_to_name": self.assigned_to.get_full_name(),
            "activity_priority": self.activity_priority.value
        }
        return activity_list


class ActivityList(BaseModel):
    # REVIEW THE FIELDS OF MODELS A.M !!!!
    #activity_id = models.ForeignKey(Scheduling, related_name='act_list_id')
    animal = models.ForeignKey(Entity, related_name='alert_animal_id', null=True)
    customer = models.ForeignKey(Customer, null=True)
    derived_alerts = models.ForeignKey(HypernetNotification,
                                       related_name='animal_alerts', null=True)
    activity_type = models.ForeignKey(Options, related_name='activity_type', null=True)
    action_status = models.ForeignKey(Options, related_name='action_status', null=True)
    group = models.PositiveIntegerField(null=True)
    group_value = models.DecimalField(decimal_places=3, null=True, max_digits=20)  # Collective value provided by user
    perform_individually = models.BooleanField(default=True)  # Check
    individual_value = models.DecimalField(decimal_places=3, null=True, max_digits=20)  # Mikling value of Cow
    scheduled_start_time = models.DateTimeField(blank=True, null=True)
    scheduled_end_time = models.DateTimeField(blank=True, null=True)############
    scheduling_comments = models.TextField(null=True)
    performed_start_time = models.DateTimeField(blank=True, null=True)##########
    performed_end_time = models.DateTimeField(blank=True, null=True)#############
    performed_comments = models.TextField(null=True)
    is_on_time = models.BooleanField(default=False)  # Activity performance status

    created_by = models.ForeignKey(User, related_name='activity_created_by', null=True)
    modified_by = models.ForeignKey(User, related_name='activity_modified_by', null=True)
    activity_priority = models.ForeignKey(Options, related_name='activity_priority', null=True)
    assigned_to_activity = models.ForeignKey(User, related_name='activity_assigned_to')

    @property
    def performed_end_time_date(self):
        return self.performed_end_time.date()

    def to_dict(self,obj):
        activity_list = {
            "activity_id": self.id,
            "group_id": self.group,
            "activity_type": self.activity_type.label,
            "action_status": self.action_status.label,
            "perform_individually": self.perform_individually,
            "scheduled_start_time": self.scheduled_start_time,
            "scheduled_end_time": self.scheduled_end_time,
            "comments": self.scheduling_comments,
            "group_value": self.group_value,
            "performed_start_time": self.performed_start_time,
            "performed_end_time": self.performed_end_time,
            "performed_comments": self.performed_comments,
            "is_on_time": self.is_on_time,
            "activity_priority": self.activity_priority.label,
            "assigned_to": self.assigned_to_activity_id,
            "animals": obj
        }
        return activity_list

    def activity_caretaker(self):
        return ActivityList.objects.filter(assigned_to_activity=self.assigned_to_activity)



class AnimalStates(BaseModel):
    customer = models.ForeignKey(Customer, related_name='ioa_customer', null=True)  # TODO discuss if we need it ?
    device = models.ForeignKey(CustomerDevice, related_name='customer_device_id', null=True)
    module = models.ForeignKey(Module, related_name='animal_state_module', null=True)
    animal = models.ForeignKey(Entity, related_name='state_animal_id', null=True)
    animal_state = models.CharField(max_length=100, null=True)
    animal_state_value = models.FloatField(blank=True, null=True)  # for temperature values
    created_datetime = models.DateTimeField(null=True, auto_now_add=True)
    # is_processed = models.BooleanField(default=False)
    frequency = models.IntegerField(null=True)
    # created_by = models.ForeignKey(User, related_name='state_created_by', null=True)
    # modified_by = models.ForeignKey(User, related_name='state_modified_by', null=True)

class EstrusCriteria(BaseModel):
    """
        Each cow in the system has an entry in EstrusCriteria.
        The table has all the info related to Estrus state alert configuration.

        The datetime fields have to be initialized to some back datetime (e.g. using the estrus_gap), so we won't
        miss even the first estrus for a cow, as it enters the system.
    """
    animal = models.ForeignKey(Entity, related_name='estrus_animal_id', null=True)
    estrus_onset = models.BooleanField(default=False)
    current_onset_datetime = models.DateTimeField(default=estrus_datetime_init)
    current_off_datetime = models.DateTimeField(default=estrus_datetime_init)
    last_onset_datetime = models.DateTimeField(default=estrus_datetime_init)
    last_off_datetime = models.DateTimeField(default=estrus_datetime_init)


class Aggregation(BaseModel):
    # REVIEW THE FIELDS OF MODELS A.M !!!!
    herd = models.ForeignKey(Entity, related_name='herd_id', null=True)
    animal = models.ForeignKey(Entity, related_name='animal_id', null=True)
    avg_milk_yield = models.FloatField(blank=True, null=True)
    avg_standing_time = models.FloatField(blank=True, null=True)
    avg_rumination_time = models.FloatField(blank=True, null=True)
    avg_sitting_time = models.FloatField(blank=True, null=True)
    avg_temperature = models.FloatField(blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='aggregation_created_by', null=True)
    modified_by = models.ForeignKey(User, related_name='aggregation_modified_by', null=True)

    # customer_aggregations to be changed to CUSTOMER
    customer_aggregations = models.ForeignKey(Customer, related_name='Farm_data', null=True)
    expected_milk = models.FloatField(blank=True, null=True)
    feeding_value = models.FloatField(blank=True, null=True)

    def animal_milk_yield(self):
        milk_yield = {
            "animal_id": self.animal_id,
            "milk_yield": self.avg_milk_yield,
            "herd": self.herd_id,
            "created_date": str(self.created_datetime.date()),

        }
        return milk_yield

    def herd_milk_yield(self):
        milk_yield = {
            "herd_id": self.herd_id,
            "milk_yield": self.avg_milk_yield,
            "herd_name": self.herd.name,
            "customer": self.customer_aggregations.name,
            "created_date": str(self.created_datetime.date()),
        }
        return milk_yield

    def customer_milk_yield(self):
        milk_yield = {
            "customer_id": self.customer_aggregations_id,
            "customer": self.customer_aggregations.name,
            "milk_yield": self.avg_milk_yield if self.avg_milk_yield else 0,
            "expected_milk_yield": self.expected_milk if self.expected_milk else 0,
            "created_date": str(self.created_datetime.date()),
        }
        return milk_yield

    def herd_feed(self):
        herd_feed = {
            "herd_id": self.herd_id,
            "feed": self.feeding_value,
            # "herd": self.herd.name,
            "customer": self.customer_aggregations.name,
            "created_date": str(self.created_datetime.date()),
        }
        return herd_feed

    def customer_feed(self):
        customer_feed = {
            "customer": self.customer_aggregations_id,
            "feed": self.feeding_value,
            "created_date": str(self.created_datetime.date()),
        }
        return customer_feed

    def customer_graph_feeding(self):
        customer_feed = {
            # "customer_id": self.customer_aggregations_id,
            "value": self.feeding_value,
            "time": self.created_datetime,
        }
        return customer_feed

    def customer_graph_milking(self):
        customer_milk_yield = {
            # "customer_id": self.customer_aggregations_id,
            "value": self.avg_milk_yield,
            "time": self.created_datetime,
        }
        return customer_milk_yield

# -------------------------------------------------------
# TODO move it to a separate dir i.e. ioa/triggers
# from django.dispatch import receiver
# from django.db.models.signals import post_save
#
# from hypernet.models import Entity, DeviceViolation
#
#
# @receiver(post_save, sender=Entity)
# def add_animal_violations(sender, instance, **kwargs):
#     """
#     Trigger on new Entity object - add the required DeviceViolation for the animals i.e.
#     For cow add for enteries - estrus, rumination, lameness, temperature.
#
#     Issue with pre_save - device_id=None, as Entity yet to be written.
#
#     :param sender:
#     :param instance:
#     :param kwargs:
#     :return:
#     """
#
#     from hypernet.enums import DeviceTypeEntityEnum, ModuleEnum, IOAOPTIONSEnum
#     from hypernet.constants import IOA_VIOLATION_TYPES, ESTRUS, IOA_VIOLATION_THRESHOLD
#
#     if instance.type_id == DeviceTypeEntityEnum.ANIMAL:
#         for violation in IOA_VIOLATION_TYPES:
#             dv = DeviceViolation()
#             if violation.lower() == ESTRUS:
#                 dv.threshold_number = IOA_VIOLATION_THRESHOLD.get(violation)  # ??
#                 ec = EstrusCriteria()
#                 ec.animal_id = instance.id
#                 ec.save()
#             else:
#                 dv.threshold_number = IOA_VIOLATION_THRESHOLD.get(violation)
#             dv.enabled = True
#             dv.customer = instance.customer
#             dv.device_id = instance.id
#             dv.status_id = 1
#             dv.module_id = ModuleEnum.IOA
#             dv.violation_type_id = eval("IOAOPTIONSEnum.ALERT_TYPE_{0}".format(violation.upper()))
#             dv.save()
#     else:
#         pass  # make it better.
