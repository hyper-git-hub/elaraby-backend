from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import PROTECT, Sum
from django.utils import timezone
from backend import settings
from hypernet.models import Entity, DeviceType
from customer.models import Customer, CustomerClients
from user.models import Module, User
from options.models import Options
from hypernet.enums import IOFOptionsEnum
# Create your models here.
import calendar

class LogisticsDerived(models.Model):
    device = models.ForeignKey(Entity, related_name='truck_derived_data_device_id')
    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)
    latitude = models.DecimalField(decimal_places=3, null=True, max_digits=20)
    longitude = models.DecimalField(decimal_places=3, null=True, max_digits=20)
    post_fill_vol = models.DecimalField(decimal_places=3, null=True, blank=True, max_digits=20)
    pre_fill_vol = models.DecimalField(decimal_places=3, null=True, blank=True, max_digits=20)
    post_dec_vol = models.DecimalField(decimal_places=3, null=True, blank=True, max_digits=20)
    pre_dec_vol = models.DecimalField(decimal_places=3, null=True, blank=True, max_digits=20)
    temperature = models.DecimalField(decimal_places=2, null=True, max_digits=20)
    timestamp = models.DateTimeField(null=True, db_index=True)
    fuel_avg =  models.DecimalField(decimal_places=3, null=True, max_digits=20)
    fuel_consumed =  models.DecimalField(decimal_places=3, null=True, max_digits=20)
    distance_travelled =  models.DecimalField(decimal_places=3, null=True, max_digits=20)

    def __str__(self):
        return str(self.device)


class LogisticMaintenance(models.Model):
    truck = models.ForeignKey(Entity, null=True, blank=True, related_name='maintenance_truck_id')
    driver = models.ForeignKey(Entity, null=True, blank=True, related_name='maintenance_driver_id')
    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)
    maintenance_type = models.ForeignKey(Options, related_name='maintenance_type_id')
    status = models.ForeignKey(Options, related_name='maintenance_status_id',
                                                 on_delete=PROTECT, null=True, blank=True)
    issued_datetime = models.DateTimeField(auto_now_add=True, blank=True, db_index=True)
    start_datetime = models.DateTimeField(null=True, db_index=True)
    end_datetime = models.DateTimeField(null=True, db_index=True)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='logistic_maintenance_modified_by')

    def __str__(self):
        return str(self.truck) +" "+ str(self.maintenance_type.label)


class LogisticMaintenanceData(models.Model):
    maintenance = models.ForeignKey(LogisticMaintenance, null=True, blank=True,related_name='maintenance_data_device_id')
    driver = models.ForeignKey(Entity, null=True, blank=True, related_name='maintenance_date_driver')
    truck = models.ForeignKey(Entity, null=True, blank=True, related_name='maintenance_data_truck')
    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='logistic_maintenance_data_modified_by')
    action = models.ForeignKey(Options, related_name='maintenance_data_action_id',
                               on_delete=PROTECT, null=True, blank=True)
    cost = models.FloatField(null=True, blank=True)
    cost_type = models.ForeignKey(Options, related_name='maintenance_data_type_id',
                               on_delete=PROTECT, null=True, blank=True)
    timestamp = models.DateTimeField(null=False, db_index=True)
    notes = models.CharField(null=True, blank=True, max_length=5000)

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

    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)
    suggestion=models.NullBooleanField(default=False,null=True,blank=True)
    created_datetime = models.DateTimeField(auto_now_add=True, blank=True, db_index=True)
    activity_type = models.ForeignKey(Options, related_name = 'activity_type_id', on_delete=PROTECT, null=True, blank=True)
    #primary_entity: Appliance on which the schedule is being created
    primary_entity = models.ForeignKey(Entity, related_name='activity_schedule_primary_entity', null=True, blank=True, on_delete=PROTECT)

    actor = models.ForeignKey(Entity, related_name='driver_id', null=True, blank=True)
    activity_check_point = models.ForeignKey(Entity, related_name='activity_schedule_activity_check_point', null=True, blank=True, on_delete=PROTECT)

    #schedule_type: Use now, Once, Recurring, Quick, Sleep Mode, Recurring Sleep Mode
    schedule_type = models.ForeignKey(Options, related_name = 'schedule_type_id',on_delete=PROTECT, null=True, blank=True)
    
    start_date = models.DateField(null=True, blank=True, db_index=True)
    end_date = models.DateField(null=True, blank=True, db_index=True)

    #old activity start time (No longer used, however kept and updated in the code)
    activity_start_time = models.TimeField(null=True, blank=True, db_index=True)
    #old activity end time (No longer used, however kept and updated in the code)
    activity_end_time = models.TimeField(null=True, blank=True, db_index=True)

    #new activity start time (No longer used, however kept and updated in the code)

    u_activity_start_time = models.TimeField(null=True, blank=True, db_index=True)

    #new activity end time (No longer used, however kept and updated in the code)
    u_activity_end_time = models.TimeField(null=True, blank=True, db_index=True)
    old_start_dt = models.DateTimeField(null=True, blank=True) #Old activity start datetime
    new_start_dt = models.DateTimeField(null=True, blank=True) #New activity end datetime
    old_end_dt = models.DateTimeField(null=True, blank=True) #Old activity end datetime
    new_end_dt = models.DateTimeField(null=True, blank=True) #New activity end datetime

    action_items = models.CharField(null=True, blank=True, max_length=5000) #Desired temperature of user

    activity_route = models.CharField(null=True, blank=True, max_length=500) #Usage type of schedule

    activity_priority = models.ForeignKey(Options, related_name = 'activity_priority_id', on_delete=PROTECT, null=True, blank=True)
    # TODO migrations #IF true schedule the activity else keep as job template
    schedule_activity_status = models.ForeignKey(Options, related_name = 'scheduled_activity_status_id', on_delete=PROTECT, null=True, blank=True)
    activity_end_point = models.ForeignKey(Entity, related_name='activity_schedule_dumping_site', null=True, blank=True, on_delete=PROTECT)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='schedule_modified_by')
    activity_meta = JSONField(null=True, blank=True)
    days_list = models.CharField(null=True, blank=True, max_length=50, db_index=True)  #old days_list
    u_days_list = models.CharField(null=True, blank=True, max_length=50, db_index=True) #New days list
    notes = models.CharField(null=True, blank=True, max_length=5000) #duration of a schedule

    current_ctt=models.IntegerField(default=75,null=True,blank=True)
    suspend_status = models.BooleanField(default=False)
    multi_days = models.BooleanField(default=False)  #This flag is true when a schedule spans on mutiple days. False otherwise
    suspended_by = models.ForeignKey('self',null=True,blank=True)   #To check a schedule is suspended by which other schedule
    sleep_mode = models.BooleanField(default=False)  #Set only incase when a sleep mode is saved. When sleep mode runs, this flag is set to true
    validity_date=models.DateField(null=True, blank=True)

    temp_after_usage = models.FloatField(null=True, blank=True) #Temperature After Usage. Calculated for every schedule when it is created

    def __str__(self):
        start_time = str(self.u_activity_start_time) if self.u_activity_start_time else 'No start time'
        end_time = str(self.u_activity_end_time) if self.u_activity_end_time else 'No end time'
        suspend_status = str(self.suspend_status)
        active_status = str(self.schedule_activity_status.label)
        day_of_week = self.u_days_list if self.u_days_list else 'No days'
        suspended_by = ' Affected by: '+str(self.suspended_by.pk) if self.suspended_by else ' Not affected '
        entity_name = self.primary_entity.name if self.primary_entity else ' No entity'
        type = self.schedule_type.label if self.schedule_type else 'No type'
        return str(self.id) + ' - ' + str(self.module.name) + ' ' + start_time + ' - ' + end_time + ' - ' + suspend_status + ' - ' + active_status  + ' - ' + day_of_week + ' - ' + suspended_by + ' ' + entity_name + ' ' + type

    def get_name(self):
        name = str(self.activity_type.label) + " " + str(self.actor.name) + " " + str(self.primary_entity.name)
        return name


    def get_delete_name(self):
        return str(self.activity_type.label) + " " + str(self.actor.name) if self.actor else None + " " + str(self.primary_entity.name) if self.primary_entity else None

# This table will contain all the times when the activity is dues, will be updated on addition and updates
class ActivityQueue(models.Model):
    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)

    activity_schedule = models.ForeignKey(ActivitySchedule, null=True, blank=True)
    activity_datetime = models.DateTimeField(null=True, blank=True, db_index=True) #start datetime for a schedule

    #primary_entity is the entity on which schedule is created
    primary_entity = models.ForeignKey(Entity, related_name='scheduled_activity_primary_entity', null=True, blank=True)
    actor = models.ForeignKey(Entity, related_name='scheduled_activity_driver', null=True, blank=True)
    action_items= models.CharField(null=True, blank=True, max_length=5000)  #temperature on which heater will be set
    activity_end_datetime = models.DateTimeField(null=True, blank=True)   #end datetime for a schedule
    activity_end_point = models.ForeignKey(Entity, related_name='activity_queue_end_point', null=True, blank=True, on_delete=PROTECT)
    activity_check_point = models.ForeignKey(Entity, related_name='activity_queue_activity_check_point', null=True, blank=True, on_delete=PROTECT)

    is_on = models.NullBooleanField(default=False) #This flag will be set when time of schedule comes and notification is sent to user
    is_off = models.NullBooleanField(default=False) #This flag is set when a schedule is completed

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='queue_user', null=True, blank=True) #user who is making the schedule

    type = models.ForeignKey(Options, related_name = 'queue_type_id',on_delete=PROTECT, null=True, blank=True) #Not used

    day_of_week = models.CharField(null=True, blank=True, max_length=50) #u_days_list from Activity Schedule
    minutes=models.IntegerField(default=0,null=True,blank=True) # every 15 min check temperature
    temperature=models.IntegerField(default=55,null=True,blank=True) # check temperature for every 15 min
    suspend = models.BooleanField(default=False) #Not used

    temp_set = models.BooleanField(default=False)  #This flag is set when the API call is made on heater to set it to user's desired temperature

    def __str__(self):
        return_string = str(self.activity_schedule.id) + '-' + str(self.activity_datetime.date()) +" "+ str(self.activity_datetime.time())
        if self.activity_end_datetime:
            return_string += " --- " + str(self.activity_end_datetime.time())
        if self.primary_entity:
            return_string += " "+str(self.primary_entity.name)

        return_string += "--Is On: "+str(self.is_on)
        return_string += "--Is Off: "+str(self.is_off)
        return_string += "--Heater Switched On : "+str(self.temp_set)
        return return_string

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
            "activity_datetime": self.activity_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
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
    trips = models.IntegerField(default=0, null=True)

    trip_cost = models.FloatField(null=True, blank=True)
    trip_revenue = models.FloatField(null=True, blank=True)
    fuel_avg = models.FloatField(null=True, blank=True)
    waste_collected = models.FloatField(null=True, blank=True)

    diesel_price = models.FloatField(null=True, blank=True)

    def __str__(self):
        return str(self.primary_entity.name) +'-'+ str(self.activity_status.label)
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

    cost = models.FloatField(null=True,blank=True)


    def __str__(self):
        if self.primary_entity:
            return str(self.activity_status.label + " " + self.primary_entity.name + " "+ self.actor.name)
        else:
            return str(self.activity_status.label + " "+ self.actor.name)
    
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
    timestamp_2 = models.DateTimeField(null=True, blank=True)
    invoice = models.FloatField(null = True, blank=True)
    verified = models.NullBooleanField()
    supervisor = models.ForeignKey(Entity,null=True, blank=True, related_name='activity_collection_supervisor_id')
    

    def get_delete_name(self):
       return str(self.action_item.name + " "+ "waste collection invoice data")

    def __str__(self):
        ret_str =None
        if self.action_item:
            ret_str = self.action_item.name
        if self.status:
            ret_str += " "+self.status.label
        return ret_str

    def as_bin_collection_data_json(self):
        return {
            "id": self.id,
            "customer": self.customer.name,
            "module": self.module.name,
            "collection_status": None if not self.status else self.status.label,
            "collection_status_id": None if not self.status else self.status.id,
            "primary_entity": self.entity.name,
            "activity_end_point": str(self.activity.activity_end_point.name)  if self.activity else None,
            "activity_end_point_lat_long": self.activity.activity_end_point.source_latlong if self.activity else None,
            "bin_name": self.action_item.name,
            "bin_id": self.action_item.id,
            "actor": str(self.actor.name) if self.actor else None,
            "invoice": str(self.invoice) if self.invoice else None,
            "collection_datetime": self.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ") if self.timestamp else None,
        }


class IofShifts(models.Model):
    shift_start_time = models.DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
    shift_end_time = models.DateTimeField(blank=True, null=True, db_index=True)
    child = models.ForeignKey(Entity, related_name='shifts_child_id')
    parent = models.ForeignKey(Entity, related_name='shifts_parent_id')
    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)
    type = models.ForeignKey(DeviceType)
    volume_consumed = models.DecimalField(decimal_places=3, null=True, blank=True, max_digits=20)
    distance_travelled = models.DecimalField(decimal_places=3, null=True, blank=True, max_digits=20)
    fuel_avg = models.DecimalField(decimal_places=3, null=True, blank=True, max_digits=20)
    trips = models.IntegerField(default=0, null=True, blank=True)
    shift_duration = models.IntegerField(default=0, null=True, blank=True)
    # @property
    # def shift_duration(self):
    #     if self.shift_end_time:
    #         return (self.shift_end_time - self.shift_start_time).total_seconds() / 60
    #     else:
    #         return 0

    def get_delete_name(self):
       return str(self.child.name +" "+ self.parent.name +" "+ "driver-truck, shift data")

    def as_json(self, driver_id=None, truck_id=None):
        # TO incorporate data generation for current running shift.
        if not self.shift_end_time:
            end_datetime = timezone.now()
        else:
            end_datetime = self.shift_end_time
            
        if driver_id:
            bins = BinCollectionData.objects.filter(timestamp__range=[self.shift_start_time, end_datetime],
                                                    status_id__in= [IOFOptionsEnum.BIN_PICKED_UP,IOFOptionsEnum.WASTE_COLLECTED] ,
                                                    actor_id=driver_id)
            activities = Activity.objects.filter(start_datetime__range=[self.shift_start_time, end_datetime],
                                                    activity_status_id__in= [IOFOptionsEnum.COMPLETED,IOFOptionsEnum.FAILED],
                                                    actor_id=driver_id)
        elif truck_id:
            bins = BinCollectionData.objects.filter(timestamp__range=[self.shift_start_time, end_datetime],
                                                    status_id__in=[IOFOptionsEnum.BIN_PICKED_UP,
                                                                   IOFOptionsEnum.WASTE_COLLECTED],
                                                    entity_id=truck_id)
            activities = Activity.objects.filter(start_datetime__range=[self.shift_start_time, end_datetime],
                                                 activity_status_id__in=[IOFOptionsEnum.COMPLETED, IOFOptionsEnum.FAILED],
                                                    primary_entity_id = truck_id)
        else:
            bins = BinCollectionData.objects.filter(timestamp__range=[self.shift_start_time, end_datetime],
                                                    status_id__in=[IOFOptionsEnum.BIN_PICKED_UP,
                                                                   IOFOptionsEnum.WASTE_COLLECTED],
                                                    customer_id=self.customer_id)
            activities = Activity.objects.filter(start_datetime__range=[self.shift_start_time, end_datetime],
                                                 activity_status_id__in=[IOFOptionsEnum.COMPLETED, IOFOptionsEnum.FAILED],
                                                 customer_id=self.customer_id)
        collections = dict()
        return_dict = {
            "id": self.id,
            "customer": self.customer.name,
            "module": self.module.name,
            'driver': self.child.name,
            'driver_id': self.child.id,
            'truck': self.parent.name,
            'truck_id': self.parent.id,
            'type': self.type.name,
            'shift_start_time': self.shift_start_time.strftime("%Y-%m-%dT%H:%M:%SZ") if self.shift_start_time else None,
            'shift_end_time': self.shift_end_time.strftime("%Y-%m-%dT%H:%M:%SZ") if self.shift_end_time else None,
            'shift_duration': self.shift_duration,
            'volume_consumed': self.volume_consumed,
            'distance_travelled': self.distance_travelled,
            'fuel_avg': self.fuel_avg,
            'trips_completed': activities.aggregate(Sum('trips')).get('trips__sum') or 0,
            # 'trips_completed': self.trips,
            'waste_collected': bins.aggregate(Sum('weight')).get('weight__sum') or 0,
        }
        for b in bins:
            # increment skip size labels in list against each shift. Do not have to rewrite this piece of code ever again!
            if not collections.get(IOFOptionsEnum.labels.get(b.action_item.skip_size.id)):
                collections[IOFOptionsEnum.labels.get(b.action_item.skip_size.id)] = 1
            else:
                collections[IOFOptionsEnum.labels.get(b.action_item.skip_size.id)] += 1
        collections['Total Bins'] = bins.count()
        return_dict['collections'] = collections
        return return_dict

    
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


class InvoicesFiles(models.Model):
    customer = models.ForeignKey(Customer)
    invoice_number = models.CharField(null=True, blank=True, max_length=500)
    file = models.CharField(null=True, blank=True, max_length=1000)
    client = models.ForeignKey(CustomerClients, null=True, blank=True, related_name='invoice_file_client_id')


######################################################################################################################
####   Specific model for CMS group for data representation against API calls  #######################################
class CMSVehicleReporting(models.Model):
    customer = models.ForeignKey(Customer)
    vehicle = models.ForeignKey(Entity, related_name= 'cms_vehicle_entity_id', null=True, blank=True)
    driver = models.ForeignKey(Entity, related_name= 'cms_driver_entity_id', null=True, blank=True)
    # remove this and use entity wheel attribute
    vehicle_wheel_type = models.ForeignKey(Options, related_name='cms_vehicle_wheel_type_id', null=True, on_delete=PROTECT,
                                        blank=True)
    # compute this based on input into serialzier object
    vehicle_status = models.ForeignKey(Options, related_name='cms_vehicle_status_id', on_delete=PROTECT, null=True,
                               blank=True)
    timestamp = models.DateTimeField(null=True, blank=True, db_index=True)

    # Data from Excel
    loading_location = models.ForeignKey(Entity, related_name='cms_loading_location_id', null=True, blank=True)
    loading_city = models.ForeignKey(Entity, related_name='cms_loading_city_id', null=True, blank=True)
    destination = models.ForeignKey(Entity, related_name='cms_destination_id', null=True, blank=True)

    vms = models.CharField(null=True, blank=True, max_length=1000)
    trip_number = models.CharField(null=True, blank=True, max_length=1000)
    order_number = models.CharField(null=True, blank=True, max_length=1000)

    client = models.ForeignKey(CustomerClients, null=True, blank=True)
    # Timestamps for different events in the trip
    trip_start_datetime = models.DateTimeField(null=True, blank=True, db_index=True)
    loaded_datetime = models.DateTimeField(null=True, blank=True, db_index=True)

    stops_loaded_duration = models.IntegerField(default=0, null=True, blank=True)

    arrival_datetime = models.DateTimeField(null=True, blank=True, db_index=True)
    unloaded_datetime = models.DateTimeField(null=True, blank=True, db_index=True)

    halting = models.IntegerField(default=0, null=True, blank=True)
    stops_unloading_duration = models.IntegerField(default=0, null=True, blank=True)

    loaded_workshop_in = models.DateTimeField(null=True, blank=True, db_index=True)
    loaded_workshop_out = models.DateTimeField(null=True, blank=True, db_index=True)
    loaded_work_order_number = models.CharField(null=True, blank=True, max_length=1000)
    loaded_workshop_remarks = models.CharField(null=True, blank=True, max_length=1000)
    loaded_workshop_duration = models.IntegerField(default=0, null=True, blank=True)

    unloaded_workshop_in = models.DateTimeField(null=True, blank=True, db_index=True)
    unloaded_workshop_out = models.DateTimeField(null=True, blank=True, db_index=True)
    unloaded_work_order_number = models.CharField(null=True, blank=True, max_length=1000)
    unloaded_workshop_remarks = models.CharField(null=True, blank=True, max_length=1000)

    unloaded_workshop_duration = models.IntegerField(default=0, null=True, blank=True)


    km_loaded = models.IntegerField(default=0, null=True, blank=True)
    km_unloaded = models.IntegerField(default=0, null=True, blank=True)

    office = models.CharField(null=True, blank=True, max_length=1000)

    supervisor = models.ForeignKey(Entity, related_name='cms_supervisor_id', null=True, blank=True)

