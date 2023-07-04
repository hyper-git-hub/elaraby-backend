from django.db import models
from django.db.models import PROTECT, Sum, F
import json
from backend import settings
from customer.models import Customer, CustomerClients
from hypernet.enums import DeviceCategoryEnum, DeviceTypeEntityEnum, OptionsEnum, IOFOptionsEnum
from options.models import Options
from user.models import Module, Role, User
from .utils import get_notification_day

# Create your models here.
class BaseModel(models.Model):
    modified_datetime = models.DateTimeField(blank=True, null=True)
    created_datetime = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        abstract = True


class DeviceType(models.Model):
    name = models.CharField(null=False, max_length=50)
    category = models.IntegerField(null=False, default=DeviceCategoryEnum.ENTITY, choices=DeviceCategoryEnum.choices())
    created_datetime = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return self.name

    def natural_key(self):
        return self.name


class CustomerDevice(models.Model):
    primary_key = models.CharField(max_length=100, unique=True)
    device_id = models.CharField(max_length=50)
    customer = models.ForeignKey(Customer)
    assigned = models.BooleanField(default=False)
    status = models.ForeignKey(Options, on_delete=PROTECT)
    modified_at = models.DateTimeField(auto_now=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    type = models.ForeignKey(DeviceType, null=False)
    module = models.ForeignKey(Module)
    connection_string = models.CharField(blank=True, null=True, max_length=1000)


    def __str__(self):
        return self.device_id


class Entity(models.Model):
    name = models.CharField(max_length=250)
    type = models.ForeignKey(DeviceType, on_delete=PROTECT)
    customer = models.ForeignKey(Customer, on_delete=PROTECT)
    module = models.ForeignKey(Module, on_delete=PROTECT)
    status = models.ForeignKey(Options, on_delete=PROTECT, related_name="entity_record_status_id")
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL)
    created_datetime = models.DateTimeField(auto_now_add=True, db_index=True)
    modified_datetime = models.DateTimeField(blank=True, null=True)
    end_datetime = models.DateTimeField(blank=True, null=True)
    assignments = models.FloatField(blank=True, null=True, default=0)
    # Device specific columns
    is_enabled = models.BooleanField(default=False)
    device_name = models.ForeignKey(CustomerDevice, blank=True, null=True, on_delete=PROTECT)
    speed = models.NullBooleanField(default=False)
    volume = models.NullBooleanField(default=False)
    density = models.NullBooleanField(default=False)
    temperature = models.NullBooleanField(default=False)
    location = models.NullBooleanField(default=False)
    registration = models.CharField(blank=True, null=True, max_length=255)
    engine_number = models.CharField(blank=True, null=True, max_length=50)
    chassis_number = models.CharField(blank=True, null=True, max_length=50)
    make = models.CharField(blank=True, null=True, max_length=50)
    model = models.CharField(blank=True, null=True, max_length=50)
    color = models.CharField(blank=True, null=True, max_length=50)
    year = models.IntegerField(blank=True, null=True)
    odo_reading = models.IntegerField(blank=True, null=True)
    engine_capacity = models.IntegerField(blank=True, null=True)
    wheels = models.IntegerField(blank=True, null=True)
    volume_capacity = models.FloatField(blank=True, null=True)
    date_commissioned = models.DateField(blank=True, null=True)
    obd2_compliant = models.NullBooleanField(default=False)
    leased_owned = models.ForeignKey(Options, on_delete=PROTECT, related_name="entity_leased_owned_id", blank=True, null=True)
    # Driver specific columns
    cnic = models.CharField(blank=True, null=True, max_length=100)
    dob = models.DateField(blank=True, null=True)
    date_of_joining = models.DateField(blank=True, null=True)
    salary = models.IntegerField(blank=True, null=True)
    marital_status = models.ForeignKey(Options, on_delete=PROTECT, related_name="entity_marital_status_id", blank=True, null=True)
    gender = models.ForeignKey(Options, on_delete=PROTECT, related_name="entity_gender_id", blank=True, null=True)
    photo = models.ImageField(upload_to='avatars/', null=True, blank=True)
    # Job fence specific columns
    description = models.CharField(blank=True, null=True, max_length=1000)
    source_address = models.CharField(blank=True, null=True, max_length=250)
    destination_address = models.CharField(blank=True, null=True, max_length=250)
    destination_latlong = models.CharField(blank=True, null=True, max_length=250)
    source_latlong = models.CharField(blank=True, null=True, max_length=250)
    job_start_datetime = models.DateTimeField(blank=True, null=True)
    job_end_datetime = models.DateTimeField(blank=True, null=True)
    job_status = models.ForeignKey(Options, on_delete=PROTECT, related_name="entity_job_status_id", blank=True, null=True)
    territory_type = models.ForeignKey(Options, on_delete=PROTECT, related_name="entity_training_type_id", blank=True, null=True)
    territory = models.CharField(blank=True, null=True, max_length=10000)
    # Player specific columns
    age = models.IntegerField(blank=True, null=True)#Same will be use for animal
    squad_number = models.FloatField(blank=True, null=True)
    weight = models.FloatField(blank=True, null=True) #Same will be use for animal and skipsize for Contracts
    ethnicity = models.CharField(blank=True, null=True, max_length=50)
    past_club = models.CharField(blank=True, null=True, max_length=50)
    contracted_type = models.ForeignKey(Options, on_delete=PROTECT, related_name="entity_contracted_type_id", blank=True, null=True)
    player_position = models.CharField(blank=True, null=True, max_length=50)

    # Match Specific Columns
    date_of_match = models.DateField(null=True, blank=True, db_index=True)
    weather_forecast = models.CharField(blank=True, null=True, max_length=250)
    match_type = models.ForeignKey(Options, on_delete=PROTECT, related_name="match_type_id", blank=True, null=True)
    # Animal Specific Columns TO BE ADDED HERE
    group = models.ForeignKey(Options, related_name='animal_group', blank=True, null=True, on_delete=PROTECT)
    lactation_days = models.IntegerField(default=0, blank=True, null=True)
    lactation_status = models.ForeignKey(Options, related_name='lactation_key', blank=True, null=True,
                                         on_delete=PROTECT)
    breed = models.ForeignKey(Options, related_name='animal_breed', blank=True, null=True, on_delete=PROTECT)
    last_breeding = models.DateTimeField(blank=True, null= True, max_length=30)

    # Maintenance Related Fields.
    routine_type = models.ForeignKey(Options, related_name='maintenance_routine_type', null=True, on_delete=PROTECT, blank=True)
    maintenance_type = models.ForeignKey(Options, related_name='options_maintenance_type_id', null=True, on_delete=PROTECT, blank=True)

    # Bin Specific Fields.
    entity_sub_type = models.ForeignKey(Options, related_name='bin_sub_type_id', null=True, on_delete=PROTECT, blank=True)
    skip_size = models.ForeignKey(Options, related_name='skip_size_id', null=True, on_delete=PROTECT, blank=True)
    client = models.ForeignKey(CustomerClients, related_name='hypernet_clients', null=True, blank=True, on_delete=PROTECT)

    start_time = models.TimeField(blank=True, null=True, db_index=True)
    end_time = models.TimeField(blank=True, null=True, db_index=True)
    skip_rate = models.FloatField(blank=True, null=True)
    
    #IOP device manual mode and stand
    is_manual_mode = models.NullBooleanField(default=False)
    is_washing_machine = models.NullBooleanField(default=False)
    standby_mode= models.IntegerField(default=1, blank=True, null=True)


    def __str__(self):
        return self.name

    def get_delete_name(self):
        return self.name

    def natural_key(self):
        return self.name

    def animal_details_to_dict(self):
        from .enums import DeviceTypeEntityEnum
        if self.type.id is DeviceTypeEntityEnum.ANIMAL:
            return {
                "id": self.id,
                "name": self.name,
                "herd_id": "No Herd Found" if not self.get_parent else self.get_parent.id,
                "herd_name": "No Herd Found" if not self.get_parent else self.get_parent.name,
                "age": self.age,
                "lactation_status": "test_lactation" if not self.lactation_status else self.lactation_status.label,
                "group": "test_group" if not self.group else self.group.label,
                "lactation_days": self.lactation_days,
                "last_breeding_performed": str(self.last_breeding),
                "weight": self.weight,
                "type": self.type.name,
            }

    @property
    def get_parent(self):
        assignment = Assignment.objects.filter(child=self)
        return assignment[0].parent if assignment else None

    @property
    def get_truck(self):
        try:
            truck = Assignment.objects.get(child=self, parent__type=DeviceTypeEntityEnum.TRUCK,
                                           status=OptionsEnum.ACTIVE).parent
        except:
            truck = None
        return truck

    @property
    def get_driver(self):
        try:
            truck = Assignment.objects.get(child=self, parent__type=DeviceTypeEntityEnum.TRUCK,
                                           status=OptionsEnum.ACTIVE).parent
            driver = Assignment.objects.get(parent=truck, child__type=DeviceTypeEntityEnum.DRIVER,
                                            status=OptionsEnum.ACTIVE).child
        except:
            driver = None
        return driver

    @property
    def get_territory_of_truck(self):
        try:
            entity = Assignment.objects.get(parent=self, child__type_id=DeviceTypeEntityEnum.TERRITORY,
                                           status_id=OptionsEnum.ACTIVE).child
        except:
            entity = None
        return entity

    def as_json(self):
        entity = {
            "name": self.name,
            "type": self.type.name,
            "customer": self.customer.name,
            "status": self.status,
            "modified_by": self.modified_by.id if self.modified_by else None,
            "modified_by_name": self.modified_by.first_name + self.modified_by.last_name if self.modified_by else None,
            "modified_by_email": self.modified_by.email if self.modified_by else None,
            "created_datetime": self.created_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.created_datetime else None,
            "modified_datetime": self.modified_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.modified_datetime else None,
            "end_datetime": self.end_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.end_datetime else None,
            "assignments": self.assignments,
            # Device specific columns
            "device_id": self.device_name.device_id,
            "speed": self.speed,
            "volume": self.volume,
            "density": self.density,
            "temperature": self.temperature,
            "location": self.location,
            "registration": self.registration,
            "engine_number": self.engine_number,
            "chassis_number": self.chassis_number,
            "make": self.make,
            "model": self.model,
            "color": self.color,
            "year": self.year,
            "odo_reading": self.odo_reading,
            "engine_capacity": self.engine_capacity,
            "wheels": self.wheels,
            "volume_capacity": self.volume_capacity,
            "date_commissioned": str(self.date_commissioned) if self.date_commissioned else None,
            "obd2_compliant": self.obd2_compliant,
            "leased_owned": self.leased_owned,
            # Driver specific columns
            "cnic": self.cnic,
            "dob": str(self.dob),
            "date_of_joining": str(self.date_of_joining) if self.date_of_joining else None,
            "salary": self.salary,
            "marital_status": self.marital_status,
            "photo": str(self.photo),
            # Job fence specific columns
            "description": self.description,
            "source_address": self.source_address,
            "destination_address": self.destination_address,
            "destination_latlong": self.destination_latlong,
            "source_latlong": self.source_latlong,
            "job_start_datetime": str(self.job_start_datetime) if self.job_start_datetime else None,
            "job_end_datetime": str(self.job_end_datetime) if self.job_end_datetime else None,
            "job_status": self.job_status,
            "territory_type": self.territory_type,
            "territory": self.territory,
            # Player specific columns
            "age": self.age,
            "squad_number": self.squad_number,
            "weight": self.weight,
            "ethnicity": self.ethnicity,
            "past_club": self.past_club,
            "contracted_type": self.contracted_type,
            "player_position": self.player_position
        }
        return entity

    def as_player_json(self):
        player = {
        "name": self.name,
        "type": self.type.name,
        "customer": self.customer.name,
        "status": self.status.natural_key(),
        "modified_by": self.modified_by.id if self.modified_by else None,
        "modified_by_name": self.modified_by.first_name + self.modified_by.last_name if self.modified_by else None,
        "modified_by_email": self.modified_by.email if self.modified_by else None,
        "created_datetime": self.created_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.created_datetime else None,
        "modified_datetime": self.modified_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.modified_datetime else None,
        "end_datetime": self.end_datetime.strftime('%Y-%m-%dT%H:%M:%SZ'),
        "assignments": self.assignments,
        "age": self.age,
        "squad_number": self.squad_number,
        "weight": self.weight,
        "ethnicity": self.ethnicity,
        "past_club": self.past_club,
        "contracted_type": self.contracted_type.value if self.contracted_type else None,
        "player_position": self.player_position
        }
        return player

    @property
    def img_url(self):
        import socket
        if self.photo:
            return self.photo.url
            # photo_url = self.photo.url
            # return socket.gethostbyname(socket.gethostname())+photo_url
        else:
            return None

    @property
    def get_associated_user_email(self):
        try:
            email = User.objects.get(associated_entity_id=self.id).email
        except:
            email = None
        return email

    def as_driver_json(self):
        driver = {
        "id": self.id,
        "name": self.name,
        "customer": self.customer.name,
        "age": self.age,
        "cnic": self.cnic,
        "dob":str(self.dob) if self.dob else None,
        "gender": None if not self.gender else self.gender.label,
        "gender_id": None if not self.gender else self.gender.id,
        "assignments": self.assignments,
        "date_of_joining": str(self.date_of_joining),
        "salary": self.salary,
        "marital_status": self.marital_status.value if self.marital_status else None,
        "marital_status_id": self.marital_status.id if self.marital_status else None,
        "image":self.img_url,
        "status": self.status.value if self.status else None,
        "status_id":self.status.id if self.status else None,
        "modified_by": self.modified_by.id if self.modified_by else None,
        "modified_by_name": self.modified_by.first_name + self.modified_by.last_name if self.modified_by else None,
        "modified_by_email": self.modified_by.email if self.modified_by else None,
        "created_datetime": self.created_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.created_datetime else None,
        "modified_datetime": self.modified_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.modified_datetime else None,
        "end_datetime": self.end_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.end_datetime else None,
        "email": None if not self.get_associated_user_email else self.get_associated_user_email
        }
        return driver

    def as_entity_json(self):
        truck = {
            "id": self.id,
            "name": self.name,
            "source_latlong": None if not self.source_latlong else self.source_latlong,
            "territory": None if not self.territory else self.territory,
            "type_name": None if not self.type else self.type.name,
            "type_id": None if not self.type else self.type_id,
            # "modified_datetime": self.modified_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.modified_datetime else None,
            "modified_datetime": self.modified_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.modified_datetime else None,
            "modified_by_name": self.modified_by.first_name + self.modified_by.last_name if self.modified_by else None,
            "status": self.status.value if self.status else None,
            "status_id":self.status.id if self.status else None,
            "skip_size": self.skip_size.id if self.skip_size else None

        }
        return truck

    def as_contract_json(self):
        truck = {
            "id": self.id,
            "name": self.name,
            "source_latlong": None if not self.source_latlong else self.source_latlong,
            "type_name": None if not self.type else self.type.name,
            "type_id": None if not self.type else self.type_id,
            "modified_datetime": self.modified_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.modified_datetime else None,
            "modified_by_name": self.modified_by.first_name + self.modified_by.last_name if self.modified_by else None,
            "status": self.status.value if self.status else None,
            "status_id":self.status.id if self.status else None,
            "skip_size": self.skip_size.label if self.skip_size else None,
            "skip_rate": self.skip_rate,
            "client_name":self.client.name,
            "party_code":self.client.party_code,
        }
        return truck

    @property
    def get_device_violations(self):
        try:
            value = DeviceViolation.objects.get(device_id=self.id, status_id=OptionsEnum.ACTIVE, violation_type_id=IOFOptionsEnum.SPEED).threshold_number
        except:
            value = None
        return value

    def as_truck_json(self):
        truck = {
            "id": self.id,
            "name": self.name,
            "device_id": None if not self.device_name else self.device_name.device_id,
            "d_id": None if not self.device_name else self.device_name.id,
            "customer": self.customer.name,
            "status": self.status.value if self.status else None,
            "status_id": self.status_id if self.status else None,
            "modified_by": self.modified_by.id if self.modified_by else None,
            "modified_by_name": self.modified_by.first_name + self.modified_by.last_name if self.modified_by else None,
            "modified_by_email": self.modified_by.email if self.modified_by else None,
            "assignments": self.assignments,
            "created_datetime": self.created_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.created_datetime else None,
            "modified_datetime": self.modified_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.modified_datetime else None,
            "end_datetime": self.end_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.end_datetime else None,
            "speed": self.speed,
            "squad_number": None if not self.squad_number else self.squad_number,
            "volume": self.volume,
            "density": self.density,
            "temperature": self.temperature,
            "location": self.location,
            "registration": self.registration,
            "engine_number": self.engine_number,
            "chassis_number": self.chassis_number,
            "make": self.make,
            "model": self.model,
            "color": self.color,
            "year": self.year,
            "odo_reading": self.odo_reading,
            "engine_capacity": self.engine_capacity,
            "wheels": self.wheels,
            "volume_capacity": self.volume_capacity,
            "date_commissioned": str(self.date_commissioned) if self.date_commissioned else None,
            "obd2_compliant": self.obd2_compliant,
            "leased_owned": self.leased_owned.value if self.leased_owned else None,
            "leased_owned_id": self.leased_owned.id if self.leased_owned else None,
            "entity_sub_type": self.entity_sub_type.id if self.entity_sub_type else None,
            "entity_sub_type_name": self.entity_sub_type.label if self.entity_sub_type else None,
            "threshold_value": self.get_device_violations,

        }
        return truck

    def as_fleet_json(self):
        fleet = {
            "id": self.id,
            "name": self.name,
            "type": self.type.name,
            "customer": self.customer.name,
            "status": self.status,
            "assignments": self.assignments,
            "modified_by": self.modified_by.id if self.modified_by else None,
            "modified_by_name": self.modified_by.first_name + self.modified_by.last_name if self.modified_by else None,
            "modified_by_email": self.modified_by.email if self.modified_by else None,
            "created_datetime": self.created_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.created_datetime else None,
            "modified_datetime": self.modified_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.modified_datetime else None,
            "end_datetime": self.end_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.end_datetime else None,
            "description": self.description,
            "source_address": self.source_address,
            "destination_address": self.destination_address,
            "destination_latlong": self.destination_latlong,
            "source_latlong": self.source_latlong,
            "job_start_datetime": str(self.job_start_datetime) if self.job_start_datetime else None,
            "job_end_datetime": str(self.job_end_datetime) if self.job_end_datetime else None,
            "job_status": self.job_status,
            "territory_type": self.territory_type,
            "territory": self.territory,
        }
        return fleet

    def as_territory_json(self):
        territory = {
            "id": self.id,
            "name": self.name,
            "type": self.type.name,
            "customer": self.customer.name,
            "status_id": None if not self.status else self.status.id,
            "status": None if not self.status else self.status.label,
            "modified_by": self.modified_by.id if self.modified_by else None,
            "modified_by_name": self.modified_by.first_name + self.modified_by.last_name if self.modified_by else None,
            "modified_by_email": self.modified_by.email if self.modified_by else None,
            "created_datetime": self.created_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.created_datetime else None,
            "modified_datetime": self.modified_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.modified_datetime else None,
            "end_datetime": self.end_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.end_datetime else None,
            "description": self.description,
            "territory_type": None if not self.territory_type else self.territory_type.label,
            "territory_type_id": None if not self.territory_type else self.territory_type.id,
            "territory": None if not self.territory else self.territory,
        }
        return territory

    def as_maintenance_json(self):
        maintenance = {
            "id": self.id,
            "name": self.name,
            "type": self.type.name,
            "customer": self.customer.name,
            "status_id": None if not self.status else self.status.id,
            "status": None if not self.status else self.status.label,
            "modified_by": self.modified_by.id if self.modified_by else None,
            "modified_by_name": self.modified_by.first_name + self.modified_by.last_name if self.modified_by else None,
            "modified_by_email": self.modified_by.email if self.modified_by else None,
            "created_datetime": self.created_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.created_datetime else None,
            "modified_datetime": self.modified_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.modified_datetime else None,
            "end_datetime": self.end_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.end_datetime else None,
            "description": self.description,
            "maintenance_type": None if not self.maintenance_type else self.maintenance_type.label,
            "maintenance_type_id": None if not self.maintenance_type else self.maintenance_type.id,
            "routine_type": None if not self.routine_type else self.routine_type.label,
            "routine_type_id": None if not self.routine_type else self.routine_type.id,
            # TODO Remove after one to many relation.
            "assigned_truck": None if not self.get_truck else self.get_truck.as_entity_json(),
            "job_status": self.job_status.value if self.job_status else None,
            "job_status_id": self.job_status.id if self.job_status else None,


        }
        return maintenance

    def as_job_json(self):
        job = {
            "id": self.id,
            "name": self.name,
            "type": self.type.name,
            "customer": self.customer.name,
            "status": self.status.value,
            "status_id": self.status.id,
            "modified_by": self.modified_by.id if self.modified_by else None,
            "modified_by_name": self.modified_by.first_name + self.modified_by.last_name if self.modified_by else None,
            "modified_by_email": self.modified_by.email if self.modified_by else None,
            "created_datetime": self.created_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.created_datetime else None,
            "modified_datetime": self.modified_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.modified_datetime else None,
            "source_lat_lng": self.source_latlong,
            "destination_lat_lng": self.destination_latlong,
            "end_datetime": self.end_datetime.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "assignments": self.assignments,
            # Job fence specific columns
            "description": self.description,
            "job_start_datetime": str(self.job_start_datetime) if self.job_start_datetime else None,
            "job_end_datetime": str(self.job_end_datetime) if self.job_end_datetime else None,
            "job_status": self.job_status.value if self.job_status else None,
            "job_status_id": self.job_status.id if self.job_status else None,
            "assigned_truck": None if not self.get_truck else self.get_truck.as_entity_json(),
            "assigned_driver": None if not self.get_driver else self.get_driver.as_entity_json(),
        }

        return job

    def as_bin_json(self):
        bin = {
            "id": self.id,
            "name": self.name,
            "device_id": None if not self.device_name else self.device_name.device_id,
            "d_id": None if not self.device_name else self.device_name.id,
            "type": self.type.name,
            "customer": self.customer.name,
            "status": self.status.value,
            "status_id": self.status.id,
            "modified_by": self.modified_by.id if self.modified_by else None,
            "modified_by_name": self.modified_by.first_name + self.modified_by.last_name if self.modified_by else None,
            "modified_by_email": self.modified_by.email if self.modified_by else None,
            "created_datetime": self.created_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.created_datetime else None,
            "modified_datetime": self.modified_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.modified_datetime else None,
            "end_datetime": self.end_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.end_datetime else None,
            "assignments": self.assignments,
            "volume" : self.volume,
            "source_address": self.source_latlong,
            "volume_capacity": self.volume_capacity,
            "client_id": None if not self.client else self.client.id,
            "client_address": None if not self.client else self.client.address,
            "client_contact_number": None if not self.client else self.client.contact_number,
            "client_name": None if not self.client else self.client.name,
            "party_code": None if not self.client else self.client.party_code,
            "description": self.description if self.description else None,
            "operational": self.obd2_compliant if self.obd2_compliant else None,
            "entity_sub_type": self.entity_sub_type.id if self.entity_sub_type else None,
            "entity_sub_type_name": self.entity_sub_type.label if self.entity_sub_type else None,
            "skip_size": self.skip_size.id if self.skip_size else None,
            "skip_size_name": self.skip_size.label if self.skip_size else None,
            "leased_owned": self.leased_owned.value if self.leased_owned else None,
            "leased_owned_id": self.leased_owned.id if self.leased_owned else None,
            "skip_rate": self.skip_rate,
            
        }
        return bin

    def as_rfid_scanner_json(self):
        maintenance = {
            "id": self.id,
            "name": self.name,
            "type": self.type.name,
            "customer": self.customer.name,
            "status_id": None if not self.status else self.status.id,
            "status": None if not self.status else self.status.label,
            "modified_by": self.modified_by.id if self.modified_by else None,
            "modified_by_name": self.modified_by.first_name + self.modified_by.last_name if self.modified_by else None,
            "modified_by_email": self.modified_by.email if self.modified_by else None,
            "created_datetime": self.created_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.created_datetime else None,
            "modified_datetime": self.modified_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.modified_datetime else None,
            "end_datetime": self.end_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.end_datetime else None,
            "description": self.description,
            "assigned_truck": None if not self.get_truck else self.get_truck.as_entity_json(),

        }
        return maintenance
    
    def as_rfid_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.name,
            "customer": self.customer.name,
            "status_id": None if not self.status else self.status.id,
            "status": None if not self.status else self.status.label,
            "modified_by": self.modified_by.first_name + self.modified_by.last_name if self.modified_by else None,
            "created_datetime": self.created_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.created_datetime else None,
            "modified_datetime": self.modified_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if self.modified_datetime else None,
            "obd2_compliant": self.obd2_compliant,
        }


class EntityDocument(models.Model):
    entity = models.ForeignKey(Entity)
    file = models.FileField(upload_to='documents/')

    def __str__(self):
        return self.entity.name + ' assigned ' + self.file.name


class EntityMap(models.Model):
    """
        A copy of EntityMap of hypernet-proxy, for updating it as per insert/update on Entity.
        This model is excluded from makemigrations/migrate for the 'default' DB.

        A separate DB router 'hypernet.hypernetproxy_dbrouter' handles all QS operations, and routes
        them to the 'hypernet-proxy' database.
    """
    """
           Contains/Map necessary fields from the (back-end) Entity table.
       """
    device_id = models.CharField(max_length=100)  # the alphanumeric ID - IOT hub device ID.
    device_name = models.CharField(max_length=250)
    customer = models.IntegerField()  # customer ID
    primary_key = models.CharField(max_length=250)  # for SAS token generation.
    iot_hub = models.CharField(max_length=250)  # may have multiple iot hubs
    module = models.IntegerField()  # IOL=1, IOA=2, ..
    type = models.IntegerField()  # truck=3, cow=30, ..
    # ---- Animal fields ---
    animal_group = models.CharField(max_length=100, null=True, blank=True)
    breed = models.CharField(max_length=100, null=True, blank=True)
    lactation_status = models.CharField(max_length=100, null=True, blank=True)  # or, Boolean

    class Meta:
        # managed = False  # exclude it from makemigrations/migrate.
        app_label = 'data_handler'

class EntityAssociative(models.Model):
    entity = models.ForeignKey(Entity)
    mapped_id = models.IntegerField()
    module = models.ForeignKey(Module)
    customer = models.ForeignKey(Customer)

    def __str__(self):
        return self.entity.name


class UserEntityAssignment(models.Model):
    comments = models.CharField(max_length=1500)
    device = models.ForeignKey(Entity, related_name='user_device_assignment_device')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='user_device_assignment_user')
    can_edit = models.BooleanField(default=True)
    can_read = models.BooleanField(default=True)
    can_remove = models.BooleanField(default=True)
    can_share = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)
    type = models.ForeignKey(DeviceType)
    status = models.ForeignKey(Options)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='user_device_assignment_modified_by')
    modified_datetime = models.DateTimeField(blank=True, null=True)
    created_datetime = models.DateTimeField(auto_now_add=True, db_index=True)
    end_datetime = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.device.name + " assigned to user:  "+ self.user.email

    def users_assignments_as_json(self):
        data_dict = {
            "user_email": self.user.email,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "status_label": self.status.label,
            "status_id": self.status_id,
            "user_id": self.user_id,
            "privileges": {
                "is_admin": self.is_admin,
                "can_edit": self.can_edit,
                "can_read": self.can_read,
                "can_remove": self.can_remove,
                "can_share": self.can_share,
            }
        }
        return data_dict


class Assignment(models.Model):
    name = models.CharField(max_length=1000)
    comments = models.CharField(max_length=1500)
    child = models.ForeignKey(Entity, related_name='assignment_child')
    parent = models.ForeignKey(Entity, related_name='assignment_parent')
    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)
    type = models.ForeignKey(DeviceType)
    status = models.ForeignKey(Options)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='assignment_modified_by')
    modified_datetime = models.DateTimeField(blank=True, null=True)
    created_datetime = models.DateTimeField(auto_now_add=True, db_index=True)
    end_datetime = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.name

    def get_delete_name(self):
        return self.name

    def natural_key(self):
        return self.name

    def get_all_childs(self):
        return Assignment.objects.filter(parent_id=self.parent_id).values('child_id','child_id__name', 'parent_id__name')

    def get_all_child_objs(self):
        return Assignment.objects.filter(parent_id=self.parent_id).distinct('child_id')

    def get_animal_groups_in_herd(self):
        return {
            "group": self.child.group.value,
            "herd": self.parent.name,
        }

class AssignmentHistory(models.Model):
    name = models.CharField(max_length=50)
    comments = models.CharField(max_length=1500)
    child = models.ForeignKey(Entity, related_name='assignment_child_history')
    parent = models.ForeignKey(Entity, related_name='assignment_parent_history')
    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)
    status = models.ForeignKey(Options)
    type = models.ForeignKey(DeviceType)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='assignment_history_modified_by')
    modified_datetime = models.DateTimeField(blank=True, null=True)
    created_datetime = models.DateTimeField(auto_now_add=True, db_index=True)
    end_datetime = models.DateTimeField(blank=True, null=True)
    assignment = models.ForeignKey(Assignment)

    def __str__(self):
        return self.name

    def natural_key(self):
        return self.name


class EntityHistory(models.Model):
    name = models.CharField(max_length=50)
    type = models.ForeignKey(DeviceType)
    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)
    status = models.ForeignKey(Options, on_delete=PROTECT, related_name="entity_history_record_status_id")
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL)
    created_datetime = models.DateTimeField(auto_now_add=True, db_index=True)
    modified_datetime = models.DateTimeField(blank=True, null=True)
    end_datetime = models.DateTimeField(blank=True, null=True)
    assignments = models.IntegerField(blank=True, null=True, default=0)
    # Device specific columns
    device_name = models.ForeignKey(CustomerDevice, blank=True, null=True)
    speed = models.NullBooleanField(default=False)
    volume = models.NullBooleanField(default=False)
    density = models.NullBooleanField(default=False)
    temperature = models.NullBooleanField(default=False)
    location = models.NullBooleanField(default=False)
    registration = models.CharField(blank=True, null=True, max_length=15)
    engine_number = models.CharField(blank=True, null=True, max_length=50)
    chassis_number = models.CharField(blank=True, null=True, max_length=50)
    make = models.CharField(blank=True, null=True, max_length=50)
    model = models.CharField(blank=True, null=True, max_length=50)
    color = models.CharField(blank=True, null=True, max_length=50)
    year = models.IntegerField(blank=True, null=True)
    odo_reading = models.IntegerField(blank=True, null=True)
    engine_capacity = models.IntegerField(blank=True, null=True)
    wheels = models.IntegerField(blank=True, null=True)
    volume_capacity = models.IntegerField(blank=True, null=True)
    date_commissioned = models.DateField(blank=True, null=True)
    obd2_compliant = models.NullBooleanField(default=False)
    leased_owned = models.ForeignKey(Options, on_delete=PROTECT, related_name="entity_history_leased_owned_id",
                                     blank=True, null=True)
    # Driver specific columns
    cnic = models.CharField(blank=True, null=True, max_length=100)
    dob = models.DateField(blank=True, null=True)
    date_of_joining = models.DateField(blank=True, null=True)
    salary = models.IntegerField(blank=True, null=True)
    marital_status = models.ForeignKey(Options, on_delete=PROTECT, related_name="entity_history_marital_status_id",
                                       blank=True, null=True)
    gender = models.ForeignKey(Options, on_delete=PROTECT, related_name="entity_history_gender_id", blank=True, null=True)
    photo = models.ImageField(upload_to='photo/',blank=True, null=True)
    # Job fence specific columns
    description = models.CharField(blank=True, null=True, max_length=1000)
    source_address = models.CharField(blank=True, null=True, max_length=250)
    destination_address = models.CharField(blank=True, null=True, max_length=250)
    destination_latlong = models.CharField(blank=True, null=True, max_length=250)
    source_latlong = models.CharField(blank=True, null=True, max_length=250)
    job_start_datetime = models.DateTimeField(blank=True, null=True)
    job_end_datetime = models.DateTimeField(blank=True, null=True)
    job_status = models.ForeignKey(Options, on_delete=PROTECT, related_name="entity_history_job_status_id", blank=True,
                                   null=True)
    territory_type = models.ForeignKey(Options, on_delete=PROTECT, related_name="entity_history_territory_type_id",
                                       blank=True, null=True)
    territory = models.CharField(blank=True, null=True, max_length=10000)
    # Player specific columns
    age = models.IntegerField(blank=True, null=True)
    squad_number = models.IntegerField(blank=True, null=True)
    weight = models.FloatField(blank=True, null=True)
    ethnicity = models.CharField(blank=True, null=True, max_length=50)
    past_club = models.CharField(blank=True, null=True, max_length=50)
    contracted_type = models.CharField(blank=True, null=True, max_length=50)
    player_position = models.CharField(blank=True, null=True, max_length=50)
    # Match Specific Columns
    date_of_match = models.DateField(null=True, blank=True, db_index=True)
    weather_forecast = models.CharField(blank=True, null=True, max_length=250)
    match_type = models.ForeignKey(Options, on_delete=PROTECT, related_name="entity_history_match_type_id", blank=True, null=True)

    entity = models.ForeignKey(Entity)
    changed_fields = models.CharField(blank=True, null=True, max_length=1500)
    # Animal specific columns
    group = models.ForeignKey(Options, related_name='entity_history_animal_group', blank=True, null=True)
    lactation_days = models.IntegerField(default=0, blank=True, null=True)
    lactation_status = models.ForeignKey(Options, related_name='entity_history_lactation_key', blank=True, null=True)
    breed = models.ForeignKey(Options, related_name='entity_history_animal_breed', blank=True, null=True)
    last_breeding = models.DateTimeField(blank=True, null=True, max_length=30)
    
    def __str__(self):
        return self.name


class DeviceCalibration(models.Model):
    device = models.ForeignKey(Entity, related_name='calibration_device_id')
    actual_value = models.DecimalField(decimal_places=5, null=True, max_digits=20)
    calibrated_value = models.DecimalField(decimal_places=5, null=True, max_digits=20)
    calibration = models.CharField(null=True, blank=True, max_length=9000000)
    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)
    status = models.ForeignKey(Options)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='calibration_modified_by')
    created_datetime = models.DateTimeField(auto_now_add=True, db_index=True)
    end_datetime = models.DateTimeField(blank=True, null=True)
    skip_rate = models.FloatField(blank=True, null=True)

    def __str__(self):
        return self.device.name
    
    def as_json(self):
        return {
            "device": self.device.id,
            "calibration": json.loads(self.calibration),
            "customer": self.customer.id,
            "module": self.module.id,
            "status": self.status.value
            
        }


class DeviceViolation(models.Model):
    """
        Entity violation/alert configuration.

        For example:
        Cow -> Rumination, lameness, estrus, temperature.
    """
    device = models.ForeignKey(Entity, related_name='violation_device_id', null=True, blank=True)
    threshold_number = models.DecimalField(decimal_places=3, null=True, blank=True, max_digits=20)
    threshold_string = models.CharField(blank=True, null=True, max_length=50)
    violation_type = models.ForeignKey(Options, on_delete=PROTECT, related_name='notification_violation_type', null=True, blank=True)
    enabled = models.BooleanField(default=False)
    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)  # IOA/IOL/PPP
    status = models.ForeignKey(Options, on_delete=PROTECT, related_name='notification_record_status')
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notification_modified_by', null=True)  # null=True for crons
    created_datetime = models.DateTimeField(auto_now_add=True, db_index=True)
    end_datetime = models.DateTimeField(blank=True, null=True)
    trigger_datetime = models.DateTimeField(auto_now_add=True)  # time, last violation occurred.
    next_trigger_datetime = models.DateTimeField(auto_now_add=True)  # time, next trigger check.

    def __str__(self):
        return self.device.name

    def get_delete_name(self):
        return self.device.name+"'s  "+ self.violation_type.label +"  violation"

class RoleAssignment(models.Model):
    role = models.ForeignKey(Role, related_name='role_child')
    entity = models.ForeignKey(Entity, related_name='entity_parent')
    customer = models.ForeignKey(Customer)
    status = models.ForeignKey(Options)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='role_assignment_modified_by')
    modified_datetime = models.DateTimeField(blank=True, null=True)
    created_datetime = models.DateTimeField(auto_now_add=True, db_index=True)
    end_datetime = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.role.name + ' ' + self.entity.name


class RoleAssignmentHistory(models.Model):
    role = models.ForeignKey(Role, related_name='role_child_history')
    entity = models.ForeignKey(Entity, related_name='entity_parent_history')
    customer = models.ForeignKey(Customer)
    status = models.ForeignKey(Options)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='role_assignment_modified_by_history')
    modified_datetime = models.DateTimeField(blank=True, null=True)
    created_datetime = models.DateTimeField(auto_now_add=True, db_index=True)
    end_datetime = models.DateTimeField(blank=True, null=True)
    role_assignment = models.ForeignKey(RoleAssignment)

    def __str__(self):
        return self.role.name + ' ' + self.entity.name


####################################################################
############## backend Data Models ################################
####################################################################

class HypernetPreData(models.Model):
    device = models.ForeignKey(Entity, related_name='pre_data_device_id')
    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)
    type = models.ForeignKey(DeviceType)
    timestamp = models.DateTimeField(null=False, db_index=True)
    volume = models.DecimalField(decimal_places=3, null=True, blank=True, max_digits=20)
    temperature = models.DecimalField(decimal_places=3, null=True, blank=True,max_digits=20)
    ambient_temperature = models.DecimalField(decimal_places=3, null=True, blank=True,max_digits=20)
    density = models.DecimalField(decimal_places=3, null=True, blank=True,max_digits=20)
    speed = models.DecimalField(decimal_places=3, null=True, blank=True,max_digits=20)
    latitude = models.DecimalField(decimal_places=10, null=True, blank=True,max_digits=20)
    longitude = models.DecimalField(decimal_places=10, null=True, blank=True,max_digits=20)
    harsh_braking = models.BooleanField(default=False) #chs = on and off status
    harsh_acceleration = models.BooleanField(default=False)
    trip = models.NullBooleanField(default=None)   #in FFP, trip is used to check active/inactive
    timezone = models.CharField(null=True, blank=True, max_length=25)
    nn_interval = models.IntegerField(null=True, blank=True)
    accelerometer_1 = models.DecimalField(decimal_places=3, null=True, blank=True, max_digits=20)
    accelerometer_2 = models.DecimalField(decimal_places=3, null=True, blank=True,max_digits=20)
    accelerometer_3 = models.DecimalField(decimal_places=3, null=True, blank=True,max_digits=20)
    gyro_1 = models.DecimalField(decimal_places=3, null=True, blank=True, max_digits=20)
    gyro_2 = models.DecimalField(decimal_places=3, null=True, blank=True, max_digits=20)
    gyro_3 = models.DecimalField(decimal_places=3, null=True, blank=True, max_digits=20)
    hrv_value = models.IntegerField(null=True, blank=True)
    breathingrate_avg = models.DecimalField(decimal_places=3, null=True, blank=True,max_digits=20)
    breathingrate_min = models.DecimalField(decimal_places=3, null=True, blank=True,max_digits=20)
    breathingrate_max = models.DecimalField(decimal_places=3, null=True, blank=True,max_digits=20)
    duration = models.IntegerField(null=True, blank=True) #in FFP, duration ==> steps.
    heartrate_value = models.IntegerField(null=True, blank=True)
    heartrate_recovery = models.IntegerField(null=True, blank=True)
    distance_by_sensor = models.DecimalField(decimal_places=3, null=True, blank=True, max_digits=20)
    validity = models.BooleanField(default=True)
    active_score = models.IntegerField(null=True, blank=True) #current temperature threshold
    inactive_score = models.IntegerField(null=True, blank=True) #error code.
    debug_key = models.CharField(null=True, blank=True, max_length=255)
    ctt = models.IntegerField(null=True, blank=True)
    clm=models.PositiveIntegerField(null=True, blank=True)
    cdt=models.IntegerField(null=True, blank=True)


    def __str__(self):
        return self.device.name + '  -  ' + 'Time: ' + str(self.timestamp)

class HypernetPostData(models.Model):
    device = models.ForeignKey(Entity, related_name='post_data_device_id')
    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)
    type = models.ForeignKey(DeviceType)
    timestamp = models.DateTimeField(null=False, db_index=True)
    volume = models.DecimalField(decimal_places=3, null=True, blank=True,  max_digits=20)
    raw_volume = models.DecimalField(decimal_places=3, null=True, blank=True,  max_digits=20)
    temperature = models.DecimalField(decimal_places=3, null=True, blank=True,  max_digits=20)
    raw_temperature = models.DecimalField(decimal_places=3, null=True, blank=True,  max_digits=20)
    ambient_temperature = models.DecimalField(decimal_places=3, null=True, blank=True,max_digits=20)
    density = models.DecimalField(decimal_places=3, null=True, blank=True,  max_digits=20)
    speed = models.DecimalField(decimal_places=3, null=True, blank=True,  max_digits=20)
    #FIXME decimal_places to be 6 atleast
    latitude = models.DecimalField(decimal_places=10, null=True, blank=True,  max_digits=20)
    longitude = models.DecimalField(decimal_places=10, null=True, blank=True,  max_digits=20)
    harsh_braking = models.BooleanField(null=False, default=False) #on off status of device
    harsh_acceleration = models.BooleanField(null=False, default=False)
    trip = models.NullBooleanField(default=None)
    created_datetime = models.DateTimeField(auto_now_add=True, db_index=True)
    timezone = models.CharField(null=True, blank=True, max_length=25)
    nn_interval = models.IntegerField(null=True, blank=True)
    accelerometer_1 = models.DecimalField(decimal_places=3, null=True, blank=True,  max_digits=20)
    accelerometer_2 = models.DecimalField(decimal_places=3, null=True, blank=True,  max_digits=20)
    accelerometer_3 = models.DecimalField(decimal_places=3, null=True, blank=True,  max_digits=20)
    gyro_1 = models.DecimalField(decimal_places=3, null=True, blank=True, max_digits=20)
    gyro_2 = models.DecimalField(decimal_places=3, null=True, blank=True, max_digits=20)
    gyro_3 = models.DecimalField(decimal_places=3, null=True, blank=True, max_digits=20)
    hrv_value = models.IntegerField(null=True, blank=True)
    breathingrate_avg = models.DecimalField(decimal_places=3, null=True, blank=True,  max_digits=20)
    breathingrate_min = models.DecimalField(decimal_places=3, null=True, blank=True,  max_digits=20)
    breathingrate_max = models.DecimalField(decimal_places=3, null=True, blank=True, max_digits=20)
    duration = models.IntegerField(null=True, blank=True)
    heartrate_value = models.IntegerField(null=True, blank=True)
    heartrate_recovery = models.IntegerField(null=True, blank=True)
    distance_by_sensor = models.DecimalField(decimal_places=3, null=True, blank=True, max_digits=20)
    validity = models.BooleanField(default=True)

    processed = models.BooleanField(default=False)
    live = models.BooleanField(default=True)
    distance_travelled = models.DecimalField(decimal_places=3, null=True, max_digits=20)
    volume_consumed = models.DecimalField(decimal_places=3, null=True, max_digits=20)

    active_score = models.IntegerField(null=True, blank=True)  #current temperature threshold
    inactive_score = models.IntegerField(null=True, blank=True) #error code.
    debug_key = models.CharField(null=True, blank=True, max_length=255)
    ctt = models.IntegerField(null=True, blank=True)
    clm=models.PositiveIntegerField(null=True, blank=True)
    cdt=models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.device.name + '  -  ' +'Time: ' + str(self.timestamp)

class HypernetNotification(models.Model):
    from iof.models import Activity, ActivityQueue

    device = models.ForeignKey(Entity, related_name='notification_data_device_id', null=True, blank=True)
    timestamp = models.DateTimeField(null=False, db_index=True)
    violation_type = models.ForeignKey(Options, on_delete=PROTECT, related_name='violation_type_id', null=True, blank=True)
    threshold = models.DecimalField(decimal_places=3, null=True, max_digits=20, blank=True)
    value = models.IntegerField(null=True, blank=True)
    latitude = models.DecimalField(decimal_places=3, null=True, max_digits=20, blank=True)
    longitude = models.DecimalField(decimal_places=3, null=True, max_digits=20, blank=True)
    activity = models.ForeignKey(Activity, related_name='notification_job_id', null=True, blank=True)
    driver = models.ForeignKey(Entity, related_name='notification_driver_id', null=True, blank=True)
    created_datetime = models.DateTimeField(auto_now_add=True, db_index=True)
    customer = models.ForeignKey(Customer)  # for report filtering.
    module = models.ForeignKey(Module)  # for report filtering.
    title = models.CharField(blank=True, null=True, max_length=1000)
    status = models.ForeignKey(Options, on_delete=PROTECT, related_name='notification_status_id', null=True)
    description = models.CharField(max_length=1500, null=True, blank=True)
    # is_viewed = models.BooleanField(default=False)  # in through table - NotificationGroups
    threshold_string = models.CharField(blank=True, null=True, max_length=50)
    user = models.ManyToManyField(User, through='NotificationGroups')  # user to receive the notification
    type = models.ForeignKey(Options, on_delete=PROTECT, related_name="notification_type_id")

    def animal_alert_to_dict(self):
        if self is not None:
            from .enums import DeviceTypeEntityEnum
            if self.device.type.id is DeviceTypeEntityEnum.ANIMAL:
                return {
                    'violation_label': self.violation_type.label,
                    'violation_type': self.violation_type.value,
                    'animal_name': self.device.name,
                    'animal_id': self.device.id,
                    'violation_id': self.id,
                    'herd_id': None if not self.device.get_parent else self.device.get_parent.id,
                    'herd_name': None if not self.device.get_parent else self.device.get_parent.name,
                    'status': self.status.value,
                    'customer_name': self.customer.name,
                    'customer_id': self.customer.id,
                    'created_datetime': str(self.created_datetime.date()),
                    'created_time': self.created_datetime.time(),
                    'notification_description': 'You have been assigned a new job',
                    'value': self.value,
                    'string_value': self.threshold_string,
                    'animal_status': self.device.lactation_status.value,
                    'is_viewed': list(self.notificationgroups_set.annotate(viewed=F('is_viewed'),
                                                                           email=F('user__email')).values('viewed',
                                                                                                          'email')),
                }

    def as_job_notification_json(self):
        job_notification = {
            'assigned_device': None if not self.device else self.device.name,
            'assigned_device_id': None if not self.device else self.device.id,
            'notification_id': self.id,
            'activity_id': self.activity.id if self.activity else None,
            'activity_type': self.activity.activity_schedule.activity_type.label if self.activity else None,
            'activity_status': self.activity.activity_status.label if self.activity else None,
            'status': self.status.label if self.status else None,
            'status_id': self.status.id if self.status else None,
            'customer_name': self.customer.name,
            'customer_id': self.customer.id,
            'created_datetime': str(self.created_datetime.date()),
            'created_time': self.created_datetime.time(),
            'title':None if not self.title else self.title,
            # 'created_time': str(self.created_datetime.time().hour) + ':' + str(self.created_datetime.time().minute),
            'is_viewed': list(self.notificationgroups_set.annotate(viewed=F('is_viewed'),
                                                                   email=F('user__email')).values('viewed',
                                                                                                  'email')),
            'notification_type': self.type_id,
            'driver_id': self.driver_id if self.driver else None,
            'driver_name': self.driver.name if self.driver else None,
            'day': get_notification_day(self)
        }
        return job_notification

    def __str__(self):
        return self.device.name if self.device else 'No device'+ '-' + self.title


class Devices(models.Model):
    device = models.ForeignKey(Entity)
    timestamp = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return self.device.name + ' Updated at: ' + str(self.timestamp)


class NotificationGroups(models.Model):
    notification = models.ForeignKey(HypernetNotification)
    user = models.ForeignKey(User, null=True)
    is_viewed = models.BooleanField(default=False)


class InvoiceData(models.Model):
    invoice_number = models.CharField(blank=True, null=True, max_length=1000)
    customer = models.ForeignKey(Customer)  # for report filtering.
    module = models.ForeignKey(Module)  # for report filtering.
    created_datetime = models.DateTimeField(auto_now_add=True, db_index=True)
    client = models.ForeignKey(CustomerClients, null=True, blank=True, on_delete=PROTECT)
    contract = models.ForeignKey(Entity, related_name='invoice_contract_id', null=True, blank=True)
    contract_type = models.ForeignKey(Options, related_name='invoice_contract_type_id', null=True, on_delete=PROTECT,
                                        blank=True)
    area = models.ForeignKey(Entity, related_name='invoice_area_id', null=True, blank=True)
    start_datetime = models.DateTimeField(blank=True, null=True)
    end_datetime = models.DateTimeField(blank=True, null=True)
    payment_status = models.BooleanField(default=False)
    total_sum = models.DecimalField(decimal_places=3, null=True, max_digits=20, blank=True)
    invoice_path = models.CharField(blank=True, null=True, max_length=1000)

