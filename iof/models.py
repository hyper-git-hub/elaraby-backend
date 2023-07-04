from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import PROTECT
from backend import settings
from hypernet.models import Entity, DeviceType
from customer.models import Customer, CustomerClients
from user.models import Module, User
from options.models import Options

# Create your models here.


class LogisticsDerived(models.Model):
    device = models.ForeignKey(Entity, related_name='truck_derived_data_device_id')
    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)
    latitude = models.DecimalField(decimal_places=3, null=True, max_digits=20)
    longitude = models.DecimalField(decimal_places=3, null=True, max_digits=20)
    post_fill_vol = models.DecimalField(decimal_places=3, null=True, max_digits=20)
    pre_fill_vol = models.DecimalField(decimal_places=3, null=True, max_digits=20)
    post_dec_vol = models.DecimalField(decimal_places=3, null=True, max_digits=20)
    pre_dec_vol = models.DecimalField(decimal_places=3, null=True, max_digits=20)
    temperature = models.DecimalField(decimal_places=2, null=True, max_digits=20)
    timestamp = models.DateTimeField(null=True, db_index=True)

    def __str__(self):
        return str(self.device)


class LogisticMaintenance(models.Model):
    device = models.ForeignKey(Entity, related_name='maintenance_data_device_id')
    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)
    timestamp = models.DateTimeField(null=False, db_index=True)
    maintenance_type = models.ForeignKey(Entity, related_name='maintenance_data_type_id')
    description = models.TextField(default="This is an auto generated text message.")


    def __str__(self):
        return str(self.device) +" "+ str(self.maintenance_type)


class TruckTrips(models.Model):
    device = models.ForeignKey(Entity, related_name='trips_data_device_id')
    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)
    on_job = models.BooleanField(null=False, default=False)
    job = models.ForeignKey(Entity, related_name='trip_job_id', null=True, blank=True)
    driver = models.ForeignKey(Entity, related_name='trips_data_driver_id')
    truck_odo = models.DecimalField(decimal_places=2, null=True, blank=True, max_digits=20)
    trip_distance = models.DecimalField(decimal_places=3, null=True, blank=True, max_digits=20)
    trip_volume_consumed = models.DecimalField(decimal_places=3, null=True, blank=True, max_digits=20)
    trip_start_lat_long = models.CharField(null=True, blank=True, max_length=250)
    trip_start_timestamp = models.DateTimeField(null=True, blank=True, db_index=True)
    # timestamp is exact copy of trip start time, for querying purpose and reducing code
    timestamp = models.DateTimeField(null=True, blank=True, db_index=True)
    trip_end_timestamp = models.DateTimeField(null=True, blank=True, db_index=True)
    trip_end_lat_long = models.CharField(null=True, blank=True, max_length=250)
    trip_duration = models.DecimalField(decimal_places=2, null=True, blank=True, max_digits=20)

    def __str__(self):
        return str(self.device)


class ActivitySchedule(models.Model):
    """
        suggestion for creating schedule name = truckname_jobtype_schedulefrequency
        Cron  will create activities daily using the asked schedule.

    """
    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)
    created_datetime = models.DateTimeField(auto_now_add=True, blank=True, db_index=True)
    # Activity type to be used during
    activity_type = models.ForeignKey(Options, related_name = 'activity_type_id', on_delete=PROTECT, null=True, blank=True)
    primary_entity = models.ForeignKey(Entity, related_name='activity_schedule_primary_entity', null=True, blank=True, on_delete=PROTECT)

    actor = models.ForeignKey(Entity, related_name='driver_id', null=True, blank=True)
    # In case the primary entity fails, optional -> if not given system will suggest best entity for job.
    activity_check_point = models.ForeignKey(Entity, related_name='activity_schedule_activity_check_point', null=True, blank=True, on_delete=PROTECT)

    # once, daily, weekly, alternate daily, every 6 hours, every 12 hours, etc.
    schedule_type = models.ForeignKey(Options, related_name = 'schedule_type_id',on_delete=PROTECT, null=True, blank=True)
    
    # only not Null if scheduled - the time part will be the activity start time on the day.
    start_date = models.DateField(null=True, blank=True, db_index=True)
    end_date = models.DateField(null=True, blank=True, db_index=True)
    #Job start time..
    activity_start_time = models.TimeField(null=True, blank=True, db_index=True)

    # on schedule -> pending -> accepted ()
    # the entity/list-of-entities to which the primary_entity will be dealing with i.e. for Truck it can be list of Bins
    action_items = models.CharField(null=True, blank=True, max_length=5000)     # list of Entity IDs i.e. Bins to collect.
    activity_route = models.CharField(null=True, blank=True, max_length=500)
    activity_priority = models.ForeignKey(Options, related_name = 'activity_priority_id', on_delete=PROTECT, null=True, blank=True)
    # TODO migrations #IF true schedule the activity else keep as job template
    schedule_activity_status = models.ForeignKey(Options, related_name = 'scheduled_activity_status_id', on_delete=PROTECT, null=True, blank=True)
    activity_end_point = models.ForeignKey(Entity, related_name='activity_schedule_dumping_site', null=True, blank=True, on_delete=PROTECT)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='schedule_modified_by')
    activity_meta = JSONField(null=True, blank=True)
    days_list = models.CharField(null=True, blank=True, max_length=50)
    notes = models.CharField(null=True, blank=True, max_length=5000)

    def __str__(self):
        return str(self.activity_type.label) + " " + str(self.actor.name) if self.actor else None

    def get_name(self):
        return str(self.activity_type.label) + " " + str(self.actor.name) if self.actor else None

    def get_delete_name(self):
        return str(self.activity_type.label) + " " + str(self.actor.name) if self.actor else None + " " + str(self.primary_entity.name) if self.primary_entity else None

# This table will contain all the times when the activity is dues, will be updated on addition and updates
class ActivityQueue(models.Model):
    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)

    activity_schedule = models.ForeignKey(ActivitySchedule)
    activity_datetime = models.DateTimeField(null=True, blank=True, db_index=True)
    primary_entity = models.ForeignKey(Entity, related_name='scheduled_activity_primary_entity', null=True, blank=True)
    actor = models.ForeignKey(Entity, related_name='scheduled_activity_driver', null=True, blank=True)
    action_items= models.CharField(null=True, blank=True, max_length=5000)
    activity_end_datetime = models.DateTimeField(null=True, blank=True)
    activity_end_point = models.ForeignKey(Entity, related_name='activity_queue_end_point', null=True, blank=True, on_delete=PROTECT)
    activity_check_point = models.ForeignKey(Entity, related_name='activity_queue_activity_check_point', null=True, blank=True, on_delete=PROTECT)


    def __str__(self):
        return str(self.activity_schedule) + " " + str(self.primary_entity)

    def as_queue_json(self):
        from hypernet.entity.job_V2.utils import util_get_bins_location
        return {
            "id": self.id,
            "name": str(self.activity_schedule) + " " + str(self.primary_entity),
            "customer": self.customer.name,
            "module": self.module.name,
            "schedule_status": None if not self.activity_schedule else self.activity_schedule.schedule_activity_status.label,
            "primary_entity": self.primary_entity.name,
            "activity_end_point": str(self.activity_end_point.name) if self.activity_end_point else None,
            "activity_end_point_lat_long": self.activity_end_point.source_latlong if self.activity_end_point else None,
            "action_items": util_get_bins_location(self.action_items),
            "actor": str(self.actor.name) if self.actor else None,
            "activity_datetime": str(self.activity_datetime),
            "check_point_name": self.activity_schedule.activity_check_point.name if self.activity_schedule.activity_check_point else None,
            "check_point_lat_long": self.activity_schedule.activity_check_point.source_latlong if self.activity_schedule.activity_check_point else None
        }


class Activity(models.Model):
    """
        TODO: on schedule mark the entity to act upon as unavailable (a column in Entity)
        Cron job will create an activity in this table using the ActivitySchedule.

        The
    """
    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)

    activity_schedule = models.ForeignKey(ActivitySchedule, related_name ='activity_id')
    # assigned Entity to Primary activity Entity i.e. Driver assigned to a Truck.

    actor = models.ForeignKey(Entity, related_name='actor_id', null=True, blank=True)
    primary_entity = models.ForeignKey(Entity, related_name='activity_primary_entity', null=True, blank=True)
    action_items = models.CharField(null=True, blank=True, max_length=5000)
    activity_status = models.ForeignKey(Options, related_name = 'activity_status_id', on_delete=PROTECT, null=True, blank=True)
    activity_end_point = models.ForeignKey(Entity, related_name='activity_end_point', null=True, blank=True,
                                           on_delete=PROTECT)
    activity_check_point = models.ForeignKey(Entity, related_name='activity_check_point', null=True, blank=True, on_delete=PROTECT)
    created_datetime = models.DateTimeField(auto_now_add=True, blank=True, db_index=True)
    start_datetime = models.DateTimeField(null=True, blank=True, db_index=True)
    end_datetime = models.DateTimeField(null=True, blank=True, db_index=True)
    notification_sent = models.BooleanField(default=False)
    start_lat_long = models.CharField(null=True, blank=True, max_length=250)
    end_lat_long = models.CharField(null=True, blank=True, max_length=250)
    activity_start_time = models.DateTimeField(null=True, blank=True, db_index=True)
    
    # Data generated when job is ended
    duration = models.DecimalField(decimal_places=2, null=True, blank=True, max_digits=20)
    distance = models.DecimalField(decimal_places=3, null=True, blank=True, max_digits=20)
    volume_consumed = models.DecimalField(decimal_places=3, null=True, blank=True, max_digits=20)
    violations = models.IntegerField(default=0, null=True)
    notes = models.CharField(null=True, blank=True, max_length=250)

    def __str__(self):
        return str(self.primary_entity.name) + " " + str(self.actor.name) if self.actor else None+ " " \
                                         + str(self.activity_status.label)

    def get_delete_name(self):
        return str(self.activity_schedule.activity_type.label) + " " + str(self.actor.name) if self.actor else None + " " + \
               str(self.primary_entity.name) if self.primary_entity else None + " " + \
               str(self.activity_status.label) if self.activity_status else None

    #start and end_lat_long should be there becuase once driver starts an activity, it will be saved here. Driver will
    # send start long ONLY when he starts the job. So here during the runing state, we must have lat long fields.
    #OTHER: The driver must send start and end lat long only when he completes a job.
class ActivityData(models.Model):
    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)

    scheduled_activity = models.ForeignKey(Activity, related_name='activity_template_id', null=True, blank=True)
    
    # Always make entry in these columns as necessary for query execution.
    primary_entity = models.ForeignKey(Entity, related_name='truck_job_id', null=True, blank=True)
    actor = models.ForeignKey(Entity, related_name='driver_job_id', null=True, blank=True)

    action_items = models.ForeignKey(Entity, related_name='action_item_id', null=True, blank=True)
    # Time when job was started and ended by the driver/person
    timestamp = models.DateTimeField(null=True, blank=True, db_index=True)

    # Location registered by the mobile app
    lat_long = models.CharField(null=True, blank=True, max_length=250)
    
    activity_status = models.ForeignKey(Options, related_name='activity_data_status_id', on_delete=PROTECT, null=True,
                                        blank=True)
    activity_end_point = models.ForeignKey(Entity, related_name='activity_data_end_point', null=True, blank=True, on_delete=PROTECT)
    activity_check_point = models.ForeignKey(Entity, related_name='activity_data_activity_check_point', null=True, blank=True, on_delete=PROTECT)

    created_datetime = models.DateTimeField(auto_now_add=True, db_index=True)
    notes = models.CharField(null=True, blank=True, max_length=250)

    supervisor = models.ForeignKey(Entity, null=True, blank=True, related_name='activity_data_supervisor_id')

    def __str__(self):
       return str(self.scheduled_activity.activity_schedule.activity_type.label + self.activity_status.label + " " + self.primary_entity.name + " "+ self.actor.name)
    
    def get_name(self):
       return str(self.scheduled_activity.activity_schedule.activity_type.label + self.activity_status.label + " " + self.primary_entity.name + " "+ self.actor.name)

    def get_delete_name(self):
       return str(self.scheduled_activity.activity_schedule.activity_type.label + self.activity_status.label + " " + self.primary_entity.name + " "+ self.actor.name)

class LogisticAggregations(models.Model):
    device = models.ForeignKey(Entity, related_name='logistics_aggregations_device_id')
    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)
    timestamp = models.DateTimeField(null=True, db_index=True, blank=True)
    total_distance = models.DecimalField(decimal_places=3, default=0, null=True, max_digits=20)
    total_volume_consumed = models.DecimalField(decimal_places=3, default=0, null=True, max_digits=20)
    total_trips = models.IntegerField(default=0, null=True)
    total_jobs_completed = models.IntegerField(default=0, null=True)
    total_jobs_failed = models.IntegerField(default=0, null=True)
    total_maintenances = models.IntegerField(default=0, null=True)
    total_violations = models.IntegerField(default=0, null=True)
    total_fillups = models.IntegerField(default=0, null=True)
    total_decantations = models.IntegerField(default=0, null=True)
    tdist_last24Hrs = models.DecimalField(decimal_places=3, default=0, max_digits=20, null=True)
    tvol_last24Hrs = models.DecimalField(decimal_places=3, default=0, max_digits=20, null=True)
    performance_rating = models.DecimalField(decimal_places=2, default=0, max_digits=20, null=True)
    online_status = models.BooleanField(null=False, default=False)
    last_updated = models.DateTimeField(null=False, db_index=True)
    last_volume = models.DecimalField(decimal_places=3, default=0, max_digits=20, null=True)
    last_temperature = models.DecimalField(decimal_places=3, default=0, max_digits=20, null=True)
    last_density = models.DecimalField(decimal_places=3, default=0, max_digits=20, null=True)
    last_speed = models.DecimalField(decimal_places=3, default=0, max_digits=20, null=True)
    last_latitude = models.DecimalField(decimal_places=3, default=0, max_digits=20, null=True)
    last_longitude = models.DecimalField(decimal_places=3, default=0, max_digits=20, null=True)
    last_fillup = models.DateTimeField(null=True, db_index=True, blank=True)
    last_decantation = models.DateTimeField(null=True, db_index=True, blank=True)
    
    def __str__(self):
        return str(self.device)


class BinCollectionData(models.Model):

    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)
    status = models.ForeignKey(Options, related_name='activity_collection_status_id', on_delete=PROTECT, null=True, blank=True)
    entity = models.ForeignKey(Entity, null=True, blank=True, related_name='activity_collection_entity_id')
    contract = models.ForeignKey(Entity, null=True, blank=True, related_name='activity_collection_contract_id')
    client = models.ForeignKey(CustomerClients, null=True, blank=True, related_name='activity_collection_client_id')
    area = models.ForeignKey(Entity, null=True, blank=True, related_name='activity_area_id')
    activity = models.ForeignKey(Activity, null=True, blank=True)
    action_item = models.ForeignKey(Entity, related_name='activity_collection_action_item_id')
    actor = models.ForeignKey(Entity, null=True, blank=True, related_name='activity_collection_actor_id')
    pre_weight = models.FloatField(null=True, blank=True)
    post_weight = models.FloatField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(null=True, blank=True)
    invoice = models.FloatField(null = True, blank=True)
    verified = models.NullBooleanField()
    supervisor = models.ForeignKey(Entity,null=True, blank=True, related_name='activity_collection_supervisor_id')
    

    def get_delete_name(self):
       return str(self.action_item.name + " "+ "waste collection invoice data")

    def __str__(self):
        return str(self.action_item.name) if self.action_item else None +" "+str(self.status.label) if self.status else None

    def as_bin_collection_data_json(self):
        return {
            "id": self.id,
            "customer": self.customer.name,
            "module": self.module.name,
            "collection_status": None if not self.status else self.status.label,
            "collection_status_id": None if not self.status else self.status.id,
            "primary_entity": self.entity.name,
            "activity_end_point": str(self.activity.activity_end_point.name) if self.activity.activity_end_point else None,
            "activity_end_point_lat_long": self.activity.activity_end_point.source_latlong if self.activity.activity_end_point else None,
            "bin_name": self.action_item.name,
            "bin_id": self.action_item.id,
            "actor": str(self.actor.name) if self.actor else None,
            "invoice": str(self.invoice) if self.invoice else None,
            "collection_datetime": str(self.timestamp),
        }


class IofShifts(models.Model):
    shift_start_time = models.DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
    shift_end_time = models.DateTimeField(blank=True, null=True, db_index=True)
    child = models.ForeignKey(Entity, related_name='shifts_child_id')
    parent = models.ForeignKey(Entity, related_name='shifts_parent_id')
    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)
    type = models.ForeignKey(DeviceType)

    def get_delete_name(self):
       return str(self.child.name +" "+ self.parent.name +" "+ "driver-truck, shift data")

    def as_json(self):
        return {
            "id": self.id,
            "customer": self.customer.name,
            "module": self.module.name,
            'driver': self.child.name,
            'driver_id': self.child.id,
            'truck': self.parent.name,
            'truck_id': self.parent.id,
            'type': self.type.name,
            'shift_start_time': self.shift_start_time,
            'shift_end_time': self.shift_end_time,
        }

class IncidentReporting(models.Model):
    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)
    scheduled_activity = models.ForeignKey(Activity, related_name= 'incident_schedule_id', null=True, blank=True)
    primary_entity = models.ForeignKey(Entity, related_name= 'incident_primary_entity_id',  null=True, blank=True)
    actor = models.ForeignKey(Entity, related_name= 'incident_actor_id', null=True, blank=True)

    action_items = models.CharField(null=True, blank=True, max_length=5000)
    # Time when job was started and ended by the driver/person
    timestamp = models.DateTimeField(null=True, blank=True, db_index=True)
    incident_type = models.ForeignKey(Options, related_name='incident_type_id', on_delete=PROTECT, null=True,
                                        blank=True)
    notes = models.CharField(null=True, blank=True, max_length=500)

