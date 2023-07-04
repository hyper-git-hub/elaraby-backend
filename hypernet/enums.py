from django_enumfield import enum


class DeviceTypeEntityEnum(enum.Enum):
    # FIXME Add new Enums starting from [67] and Increment this number.
    # FIXME [ Enums from 23 till 29 are available]
    JOB = 1
    FLEET = 2
    TRUCK = 3
    COMPARTMENT = 4
    DRIVER = 5
    TERRITORY = 6
    DEPOT = 7
    VESSEL = 8
    MAINTENANCE = 9
    PLAYER = 16
    TEAM = 17
    MATCH = 18
    COMPETITION = 19
    VENUE = 20
    BIN = 21
    FREEZER = 22
    ANIMAL = 30
    HERD = 31
    CLIENT = 36
    DUMPING_SITE = 37
    AREA = 38
    CUSTOMER_DEVICE = 39
    RFID_SCANNER = 40
    CONTRACT = 42
    SUPERVISOR = 44
    WORKFORCE = 46
    RFID_TAG = 47
    RFID_CARD = 48
    SORTING_FACILITY = 51
    # FFP
    EMPLOYEE = 54
    ZONE = 55
    SITE = 57

    IOP_DEVICE = 62
    MAINTENANCE_DATA = 63
    LOCATION = 65

    #  DeviceTypeEntityEnum  anf DeviceTypeAssignmentEnum are associated and new enum value must not conflict with both enums
    labels = \
        {
            JOB: "Job",
            FLEET: "Fleet",
            TRUCK: "Truck",
            COMPARTMENT: "Compartment",
            DRIVER: "Driver",
            TERRITORY: "Territory",
            DEPOT: "Depot",
            VESSEL: "Vessel",
            MAINTENANCE: "Maintenance",
            PLAYER: "Player",
            TEAM: "Team",
            MATCH: "Match",
            COMPETITION: "Competition",
            VENUE: "Venue",
            BIN: "Bin",
            FREEZER: "Freezer",
            ANIMAL: "Animal",
            HERD: "Herd",
            CLIENT: "Client",
            DUMPING_SITE: "Dumping Site",
            AREA: "Area",
            CUSTOMER_DEVICE: "Customer Device",
            RFID_SCANNER: "RFID Scanner",
            CONTRACT: "Contract",
            SUPERVISOR: "Supervisor",
            WORKFORCE: "Workforce",
            RFID_CARD: "RFID Card",
            RFID_TAG: "RFID Tag",
            SORTING_FACILITY: "Sorting Facility",
            ZONE: "Zone",
            SITE: "Site",
            IOP_DEVICE: "Iop Device",
            MAINTENANCE_DATA: "Maintenance Data",
            LOCATION: "Location"
        }


class DeviceTypeAssignmentEnum(enum.Enum):
    # FIXME Add new Enums starting from [70] and Increment this number.

    TRUCK_ASSIGNMENT = 10
    VESSEL_ASSIGNMENT = 11
    COMPARTMENT_ASSIGNMENT = 12
    JOB_ASSIGNMENT = 13
    DRIVER_ASSIGNMENT = 14
    TERRITORY_ASSIGNMENT = 15

    HERD_ASSIGNMENT = 32
    BIN_ASSIGNMENT = 33
    MAINTENANCE_ASSIGNEMENT = 34
    AREA_ASSIGNMENT = 35
    RFID_ASSIGNMENT = 41
    CONTRACT_ASSIGNMENT = 43
    SHIFT_ASSIGNMENT = 45
    RFID_CARD_ASSIGMENT = 49
    RFID_TAG_ASSIGMENT = 50
    AREA_CONTRACT_ASSIGNMENT = 52
    SUPERVISOR_CONTRACT_ASSIGNMENT = 53

    # FFP
    ZONE_EMPLOYEE_ASSIGNMENT = 56
    SITE_EMPLOYEE_ASSIGNMENT = 58
    SITE_ZONE_ASSIGNMENT = 60
    LABOR_TEAM_LEAD_ASSIGNMENT = 61

    IOP_DEVICE_USER_ASSIGNMENT = 64
    LOCATION_CONTRACT_ASSIGNMENT = 66
    LOCATION_ASSIGNMENT = 68
    DUMP_ASSIGNMENT = 69

    #  DeviceTypeEntityEnum  anf DeviceTypeAssignmentEnum are associated and new enum value must not conflict with both enums
    labels = {
        TRUCK_ASSIGNMENT: "Truck Assignment",
        VESSEL_ASSIGNMENT: "Vessel Assignment",
        COMPARTMENT_ASSIGNMENT: "Compartment Assignment",
        JOB_ASSIGNMENT: "Job Assignment",
        DRIVER_ASSIGNMENT: "Driver Assignment",
        TERRITORY_ASSIGNMENT: "Territory Assignment",
        HERD_ASSIGNMENT: "Herd Assignment",
        BIN_ASSIGNMENT: "Bin Assignment",
        MAINTENANCE_ASSIGNEMENT: "Maintenance Assignment",
        AREA_ASSIGNMENT: "Area Assignment",
        RFID_ASSIGNMENT: "RFID Assignment",
        CONTRACT_ASSIGNMENT: "Contract Assignment",
        SHIFT_ASSIGNMENT: "Shift Assignment",
        RFID_CARD_ASSIGMENT: "RFID Card Assignment",
        RFID_TAG_ASSIGMENT: "RFID Tag Assignment",
        AREA_CONTRACT_ASSIGNMENT: "Area Contract Assignment",
        SUPERVISOR_CONTRACT_ASSIGNMENT: "Supervisor Contract Assignment",

        # FFP
        ZONE_EMPLOYEE_ASSIGNMENT: "Zone Employee Assignment",
        SITE_EMPLOYEE_ASSIGNMENT: "Site Employee Assignment",
        SITE_ZONE_ASSIGNMENT: "Site Zone Assignment",
        LABOR_TEAM_LEAD_ASSIGNMENT: "Labor Team Lead Assignment",

        # IOP
        IOP_DEVICE_USER_ASSIGNMENT: "Iop Device User Assignment",
        LOCATION_CONTRACT_ASSIGNMENT: "Location Contract Assignment",
        LOCATION_ASSIGNMENT: "Location Assignment",
        DUMP_ASSIGNMENT: "Dump Assignment",

    }


class DeviceCategoryEnum(enum.Enum):
    ENTITY = 1
    ASSIGNMENT = 2

    labels = {
        ENTITY: "Entity",
        ASSIGNMENT: "Assignment",
    }


class IOAOPTIONSEnum(enum.Enum):
    ALERT_TYPE_ESTRUS = 1001
    ALERT_TYPE_RUMINATION = 1002
    ALERT_TYPE_LAMENESS = 1003
    ALERT_TYPE_TEMPERATURE = 1004

    ACTIVITY_ACTION_STATUS_COMPLETE = 1005
    ACTIVITY_ACTION_STATUS_INCOMPLETE = 1006
    ACTIVITY_ACTION_STATUS_PENDING = 1007

    ACTIVITY_TYPE_MILKING = 1008
    ACTIVITY_TYPE_FEEDING = 1009
    ACTIVITY_TYPE_BREEDING = 1010

    ANIMAL_GROUP_IN_LACTATION = 1011
    ANIMAL_GROUP_IN_HEIFERS = 1012
    ANIMAL_GROUP_IN_CALFS = 1013

    ROUTINE_TYPE_DAILY = 1014
    ROUTINE_TYPE_WEEKLY = 1015
    ROUTINE_TYPE_ONCE = 1016

    LACTATION_STATUS_LACTATING = 1017
    LACTATION_STATUS_NON_LACTATING = 1018
    LACTATION_STATUS_PREGNANT = 1019
    LACTATION_STATUS_DRY = 1020

    ACTIVITY_PRIORITY_HIGH = 1021
    ACTIVITY_PRIORITY_MEDIUM = 1022
    ACTIVITY_PRIORITY_LOW = 1023

    ACTIVITY_TYPE_INSPECTION = 1024


# To start from 2006

class IopOptionsEnums(enum.Enum):
    AIR_CONDITIONER = 2000
    WATER_HEATER = 2001
    REFRIGIRATOR = 2002
    DEEP_FREEZER = 2003
    WASHING_MACHINE = 2004
    WATER_DISPENSER = 2005

    WATER_HEATER_MODEL_1 = 2006
    WATER_HEATER_MODEL_2 = 2007
    WATER_HEATER_MODEL_3 = 2008
    WATER_HEATER_MODEL_4 = 2009

    IOP_SCHEDULE_ON_DEMAND = 2010
    IOP_SCHEDULE_DAILY = 2011
    IOP_QUICK_SCHEDULE = 2012

    IOP_SLEEP_MODE = 2016
    IOP_USE_NOW = 2017
    IOP_SCHEDULE_FAILED = 2023
    IOP_SCHEDULE_SKIPPED = 2024
    IOP_SCHEDULE_RETRYING=2025
    IOP_SCHEDULE_READY = 2018
    IOP_SCHEDULE_IN_USE = 2019
    IOP_SCHEDULE_COMPLETED = 2020
    IOP_SCHEDULE_CANCELLED = 2021
    RECURRING_SLEEP_MODE = 2022

    labels = {
        AIR_CONDITIONER: "Air conditioner",
        WATER_HEATER: "Water Heater",
        REFRIGIRATOR: "Refigirator",
        DEEP_FREEZER: "Deep Freezer",
        WASHING_MACHINE: "Washing machine",
        WATER_DISPENSER: "Water Dispenser",

        WATER_HEATER_MODEL_1: "EWH-S35CSE",
        WATER_HEATER_MODEL_2: "EWH-S45CSE",
        WATER_HEATER_MODEL_3: "EWH-S55CSE",
        WATER_HEATER_MODEL_4: "EWH-S65CSE",

        IOP_SCHEDULE_ON_DEMAND: "Iop Schedule on demand",
        IOP_SCHEDULE_DAILY: "Iop Schedule daily",
        IOP_QUICK_SCHEDULE: "Iop quick schedule",

        IOP_SLEEP_MODE: "Iop Sleep Mode",
        IOP_USE_NOW: "Iop Use Now",

        IOP_SCHEDULE_READY: "Iop Schedule Ready",
        IOP_SCHEDULE_IN_USE: "Iop Schedule In Use",
        IOP_SCHEDULE_COMPLETED: "Iop Schedule Completed",
        IOP_SCHEDULE_CANCELLED: "Iop Schedule Cancelled",
        IOP_SCHEDULE_FAILED: "Iop Schedule failed",
        IOP_SCHEDULE_SKIPPED: "Iop Schedule Skipped",
        IOP_SCHEDULE_RETRYING:' Iop Schedule Retrying',
        RECURRING_SLEEP_MODE: "Iop recurring sleep mode"
    }


class IopErrorEnums(enum.Enum):
    IOP_DEVICE_ERR_1 = 1
    IOP_DEVICE_ERR_2 = 2
    IOP_DEVICE_ERR_3 = 3
    IOP_DEVICE_ERR_4 = 4
    IOP_DEVICE_ERR_5 = 5
    IOP_DEVICE_ERR_6 = 6
    IOP_DEVICE_ERR_7 = 7
    IOP_DEVICE_ERR_8 = 8
    IOP_DEVICE_ERR_9 = 9
    IOP_DEVICE_ERR_10 = 10
    IOP_DEVICE_ERR_11 = 11
    IOP_DEVICE_ERR_12 = 12


class DimensionEnum(enum.Enum):
    YEAR = 1
    QUARTER = 2
    MONTH = 3
    DAY = 4
    HOUR = 5
    MINUTE = 6
    SECOND = 7

    labels = {
        YEAR: "Year",
        QUARTER: "Quarter",
        MONTH: "Month",
        DAY: "Day",
        HOUR: "Hour",
        MINUTE: "Minute",
        SECOND: "Second",
    }


class ModuleEnum(enum.Enum):
    IOL = 1
    IOA = 2
    PPP = 3
    FFP = 4
    IOP = 5

    labels = {
        IOL: "Internet of Logistics",
        IOA: "Internet of Animals",
        PPP: "Player Performance Platform",
        FFP: "Field Force Performance",
        IOP: "Internet of Power",
    }


class SubModuleEnum(enum.Enum):
    IOL_TRUCKS = 1.1
    IOL_BINS = 1.2
    IOL_FREEZERS = 1.3
    IOL_GENERATORS = 1.4
    IOL_COMPARTMENTS = 1.5
    # VESSELS.
    IOA_ANIMALS = 2.0
    PPP_PLAYER = 3.0

    labels = {
        IOL_TRUCKS: "Internet of Logistics(TRUCKS)",
        IOL_BINS: "Internet of Logistics(BINS)",
        IOL_FREEZERS: "Internet of Logistics(FREEZERS)",
        IOL_GENERATORS: "Internet of Logistics(GENERATORS)",
        IOL_COMPARTMENTS: "Internet of Logistics(COMPARTMENTS)",
    }


class AggregationEnum(enum.Enum):
    AVG = 1
    SUM = 2
    MIN = 3
    MAX = 4

    labels = {
        AVG: "Avg",
        SUM: "Sum",
        MIN: "Min",
        MAX: "Max",
    }


class DrillTableEnum(enum.Enum):
    HypernetPostData = 1
    HypernetNotification = 2
    HypernetMaintenance = 3
    LogisticJobs = 4
    LogisticTrips = 5

    labels = {
        HypernetPostData: "HypernetPostData",
        HypernetNotification: "HypernetNotification",
        HypernetMaintenance: "HypernetMaintenance",
        LogisticJobs: "LogisticJobs",
        LogisticTrips: "LogisticTrips",
    }


# 32
class OptionsEnum(enum.Enum):
    # Record Status
    ACTIVE = 1
    INACTIVE = 2
    # Gender Status
    MALE = 3
    FEMALE = 4
    OTHER = 5
    # Marital Status
    MARRIED = 6
    SINGLE = 7
    DIVORCED = 8
    ENGLISH = 9
    FRENCH = 10
    ITALIAN = 11
    DELETED = 12
    ALERT_GENERATED = 13
    ALERT_SCHEDULED = 14
    ALERT_IGNORED = 15

    ROUTINE_TYPE_DAILY = 16
    ROUTINE_TYPE_WEEKLY = 17
    ROUTINE_TYPE_ONCE = 18
    ROUTINE_TYPE_MONTHLY = 19
    ROUTINE_TYPE_YEARLY = 20
    ROUTINE_TYPE_ALTER_DAYS = 21

    ACTIVITY_PRIORITY_HIGH = 22
    ACTIVITY_PRIORITY_MEDIUM = 23
    ACTIVITY_PRIORITY_LOW = 24

    WEEKDAY_MONDAY = 25
    WEEKDAY_TUESDAY = 26
    WEEKDAY_WEDNESDAY = 27
    WEEKDAY_THURSDAY = 28
    WEEKDAY_FRIDAY = 29
    WEEKDAY_SATURDAY = 30
    WEEKDAY_SUNDAY = 31

    labels = {
        ACTIVE: "Active",
        INACTIVE: "Inactive",
        MALE: "Male",
        FEMALE: "Female",
        OTHER: "Other",
        MARRIED: "Married",
        SINGLE: "Single",
        DIVORCED: "Divorced",
        ENGLISH: 'English',
        FRENCH: 'French',
        ITALIAN: 'Italian',
        DELETED: 'Deleted',
        ALERT_GENERATED: 'Generated',
        ALERT_SCHEDULED: 'Scheduled',
        ALERT_IGNORED: 'Ignored',

        ROUTINE_TYPE_DAILY: 'daily',
        ROUTINE_TYPE_WEEKLY: 'weekly',
        ROUTINE_TYPE_ONCE: 'once',
        ROUTINE_TYPE_MONTHLY: 'monthly',
        ROUTINE_TYPE_YEARLY: 'yearly',
        ROUTINE_TYPE_ALTER_DAYS: 'alternate days',

        ACTIVITY_PRIORITY_HIGH: 'high',
        ACTIVITY_PRIORITY_MEDIUM: 'medium',
        ACTIVITY_PRIORITY_LOW: 'low',

        WEEKDAY_MONDAY: 'monday',
        WEEKDAY_TUESDAY: 'tuesday',
        WEEKDAY_WEDNESDAY: 'wednesday',
        WEEKDAY_THURSDAY: 'thursday',
        WEEKDAY_FRIDAY: 'friday',
        WEEKDAY_SATURDAY: 'saturday',
        WEEKDAY_SUNDAY: 'sunday',
    }


# Latest 183 - Next to be added 184.
class IOFOptionsEnum(enum.Enum):
    # Purchase Type
    OWNED = 50
    LEASED = 51
    # Job Status
    RUNNING = 52
    PENDING = 53
    ABORTED = 54
    COMPLETED = 55
    SUSPENDED = 78
    RESUMED = 79
    FAILED = 117
    TRIP_INCREMENT = 165
    TRIP_DECREMENT = 166
    # Territory Type
    RED = 56
    GREEN = 57
    BLUE = 58
    # Violation Types
    SPEED = 59
    VOLUME = 60
    TEMPERATURE = 61
    DENSITY = 62
    HARSHBRAKING = 63
    HARSHACCELERATION = 64
    FILLUPTHRESHOLD = 65
    DECANTTHRESHOLD = 66
    VOLUME_OVERFLOW = 76
    TERRITORY = 124

    ENGINE_TUNING_MAINTENANCE = 67
    SERVICE_MAINTENANCE = 68
    TYRE_REPLACEMENT_MAINTENANCE = 69
    SUSPENSION_REPAIR_MAINTENANCE = 70

    MAINTENANCE_OVER_DUE = 71
    MAINTENANCE_COMPLETED = 72
    MAINTENANCE_DUE = 73
    MAINTENANCE_WAITING_FOR_PARTS = 159
    ADDITION_OF_COST = 167
    MAINTENANCE_APPROVAL = 168
    MAINTENANCE_OPEN_INPROGRESS = 169
    MAINTENANCE_ACCEPTED = 170

    ACCEPTED = 74
    REJECTED = 75

    BIN_COLLECTION_JOB = 77
    # Notification types:
    NOTIFICATION_ADMIN_ACTIVITY_REVIEW = 81  # Review notification sent to Admin (1.0)
    NOTIFICATION_ADMIN_ACTIVITY_REVIEW_TRUCK_CONFLICT = 83  # If truck conflicts during activity creation(1.1)
    NOTIFICATION_ADMIN_ACTIVITY_REVIEW_DRIVER_CONFLICT = 112  # Notificaiton sent to Admin when Driver conflicts (1.2)
    NOTIFCIATION_DRIVER_ACCEPT_REJECT = 80  # Notification sent to driver to accept reject an activity (2.0)
    NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_ACCEPT = 86  # Notification sent to Admin when Driver Accepts activity (2.1)
    NOTIFICATION_ADMIN_ACTIVITY_REVIEW_NO_ACTION_ACCEPT_REJECT = 91  # Notificaiton sent to Admin when driver takes no action (2.1).
    NOTIFICATION_ADMIN_ACTIVITY_REVIEW_DRIVER_REJECT = 82  # When Driver Rejects the activity, send notification to Admin for review (3.2)

    NOTIFICATION_DRIVER_START_ACTIVITY = 85  # Notification sent to Driver to start/fail activity (4)
    NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_START = 90  # Notification sent to Admin when Driver Starts activity (4.1)
    NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_SUSPEND = 87  # Notification sent to Admin when Driver Suspends activity (4.2)
    NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_RESUME = 88  # Notification sent to Admin when Driver Resumes activity (4.3)
    NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_COMPLETE = 89  # Notification sent to Admin when Driver Completes activity (4.4.0)
    NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_ABORT = 84  # Notification sent to Admin that activity is Failed (4.4.1)
    NOTIFICATION_DRIVER_BIN_PICKUP = 113  # Notification sent to driver app after a bin collected
    NOTIFICATION_DRIVER_WASTE_COLLECTION = 114  # Notification sent to driver app after waste is collected
    NOTIFICATION_DRIVER_BIN_DROPOFF = 115  # Notification sent to driver when in is dropped
    NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_SHIFT_START = 118
    NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_SHIFT_COMPLETE = 119
    NOTIFICATION_ADMIN_ACTIVITY_REVIEW_NO_ACTION_START_FAIL = 123

    NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_BIN = 125
    NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_DRIVER = 126
    NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_SUPERVISOR = 127
    NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_RFID_CARD = 128
    NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_RFID_TAG = 129
    NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_RFID_SCANNER = 130
    NOTIFICATION_DRIVER_ACKNOWLEDGE_BINS_UPDATE = 140
    NOTIFICATION_DRIVER_ACKNOWLEDGE_ACTIVITY_ABORT = 141
    NOTIFICATION_ADMIN_ACTIVITY_REVIEW_BIN_CONFLICT = 142

    COLLECTED = 92
    UNCOLLECTED = 93
    STARTED = 94
    REVIEWED = 95
    CONFLICTING = 96

    COLLECT_WASTE = 97
    WASTE_COLLECTED = 98
    PICKUP_BIN = 99
    DROPOFF_BIN = 100
    START_SHIFT = 101
    END_SHIFT = 102
    VERIFY_COLLECTION = 103
    ABORT_COLLECTION = 104
    BIN_PICKED_UP = 111
    SKIP_VERIFITCATION = 116
    UPDATE_SKIP_WEIGHT = 135
    REPORT_MAINTENANCE = 171
    CONTRACT_TERMINATION = 176
    MAINTENANCE_PICKUP = 177

    UPDATE_SKIP_DETAILS = 178
    WORKSHOP_DROP = 179
    SPARE_SKIP_DEPOSIT = 180

    PACKAGE_DROP = 183

    # Incident types
    TYRE_BURST = 105
    BREAK_FAILURE = 106
    ACCIDENT = 107
    OTHERS = 108

    PLASTIC = 120
    GALVANIZED_METAL_OR_PLASTIC = 121
    GALVANIZED_METAL = 122
    METAL = 134

    # Types of Trucks
    COMPACTOR = 131
    HOOK_LOADER = 132
    CHAIN_LOADER = 133
    TIPPER_TRUCK = 146
    PICKUP_TRUCK = 181

    # Invoice types
    LUMP_SUM = 136
    WEIGHT_BASED = 137
    TRIP_BASED = 138
    WEIGHT_AND_TRIP_BASED = 139
    ACTIVITY_UPDATED = 143

    # Types of Vessels
    CONTAINER = 144
    TANK = 145

    SKIP_SIZE_1 = 158
    SKIP_SIZE_2 = 147
    SKIP_SIZE_3 = 148
    SKIP_SIZE_4 = 149
    SKIP_SIZE_5 = 150
    SKIP_SIZE_6 = 151
    SKIP_SIZE_7 = 152
    SKIP_SIZE_8 = 153
    SKIP_SIZE_9 = 154
    SKIP_SIZE_10 = 155
    SKIP_SIZE_11 = 156
    SKIP_SIZE_12 = 157
    SKIP_SIZE_13 = 175
    SKIP_SIZE_14 = 182
    MAINTENANCE_DATA_COST_LABOR = 160
    MAINTENANCE_DATA_COST_PARTS = 161
    MAINTENANCE_DATA_COST_TAXES = 162
    MAINTENANCE_DATA_COST_DISCOUNT = 163
    MAINTENANCE_DATA_COST_FINE = 164

    # Cost breakdown enums
    FUEL_COST = 172
    LABOUR_COST = 173
    OTHER_COST = 174

    ### CMS ENUMS  ####
    WHEELER_6 = 184
    WHEELER_14 = 185
    WHEELER_18 = 186
    WHEELER_22 = 187

    labels = {

        OWNED: "Owned",
        LEASED: "Leased",

        ACCEPTED: "Accepted",
        REJECTED: "Rejected",
        RUNNING: "Running",
        PENDING: "Pending",
        ABORTED: "Aborted",
        FAILED: "Failed",
        COMPLETED: "Completed",
        SUSPENDED: "Suspended",
        RESUMED: "Resumed",
        TRIP_INCREMENT: "Trip",
        COLLECTED: "Collected",
        UNCOLLECTED: "Un-Collected",
        STARTED: "Started",
        REVIEWED: "Reviewed",
        CONFLICTING: "Conflicting",
        RED: "Red",
        GREEN: "Green",
        BLUE: "Blue",

        SPEED: "Speed",
        VOLUME: "Volume",
        TEMPERATURE: "Temperature",
        DENSITY: "Density",
        HARSHBRAKING: "Harsh Braking",
        HARSHACCELERATION: "Harsh Acceleration",
        FILLUPTHRESHOLD: "Fillup Threshold",
        DECANTTHRESHOLD: "Decant Theshold",
        TERRITORY: "Territory Violation",

        ENGINE_TUNING_MAINTENANCE: "Engine Tuning",
        SERVICE_MAINTENANCE: "Service",
        TYRE_REPLACEMENT_MAINTENANCE: "Tyre Replacement",
        SUSPENSION_REPAIR_MAINTENANCE: "Suspension Repair",

        MAINTENANCE_OVER_DUE: "Over-Due",
        MAINTENANCE_COMPLETED: "Completed",
        MAINTENANCE_DUE: "Maintenance Due",
        MAINTENANCE_WAITING_FOR_PARTS: "Waiting for Parts",
        MAINTENANCE_APPROVAL: 'Admin Approval',
        MAINTENANCE_OPEN_INPROGRESS: 'Open/ In Progress',
        MAINTENANCE_ACCEPTED: 'Accepted',

        ADDITION_OF_COST: "Addition of Cost",

        BIN_COLLECTION_JOB: "bin collection",
        NOTIFCIATION_DRIVER_ACCEPT_REJECT: "notification driver accept reject",
        NOTIFICATION_ADMIN_ACTIVITY_REVIEW: "notification admin review",
        NOTIFICATION_ADMIN_ACTIVITY_REVIEW_DRIVER_REJECT: "notification admin review driver reject",
        NOTIFICATION_ADMIN_ACTIVITY_REVIEW_TRUCK_CONFLICT: "notification admin review truck conflict",
        NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_ABORT: "notification admin review driver abort",
        NOTIFICATION_DRIVER_START_ACTIVITY: "notification driver start activity",
        NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_ACCEPT: "notification admin acknowledge driver accept",
        NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_SUSPEND: "notification admin acknowledge driver suspend",
        NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_RESUME: "notification admin acknowledge driver resume",
        NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_COMPLETE: "notification admin acknowledge driver complete",
        NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_START: "notification admin acknowledge driver start",
        NOTIFICATION_ADMIN_ACTIVITY_REVIEW_NO_ACTION_ACCEPT_REJECT: 'notification admin review no action driver accept reject',
        NOTIFICATION_ADMIN_ACTIVITY_REVIEW_DRIVER_CONFLICT: 'notification admin review driver conflict',
        NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_SHIFT_START: 'notification admin acknowledge driver shift start',
        NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_SHIFT_COMPLETE: 'notification admin acknowledge driver shift complete',
        NOTIFICATION_ADMIN_ACTIVITY_REVIEW_NO_ACTION_START_FAIL: 'notifiaton admin activity review no action start fail',

        NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_BIN: 'notification admin acknowledge add asset bin',
        NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_DRIVER: 'notification admin acknowledge add asset driver',
        NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_SUPERVISOR: 'notification admin acknowledge add asset supervisor',
        NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_RFID_CARD: 'notification admin acknowledge add asset rfid card',
        NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_RFID_TAG: 'notification admin acknowledge add asset rfid tag',
        NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_RFID_SCANNER: 'notification admin acknowledge add asset rfid scanner',
        NOTIFICATION_DRIVER_ACKNOWLEDGE_BINS_UPDATE: 'notification driver acknowledge bins update',
        NOTIFICATION_DRIVER_ACKNOWLEDGE_ACTIVITY_ABORT: 'notification driver acknowledge activity abort',
        NOTIFICATION_ADMIN_ACTIVITY_REVIEW_BIN_CONFLICT: 'notification admin review bin conflict',

        COLLECT_WASTE: "Collect Waste",
        WASTE_COLLECTED: "Waste Collected",
        PICKUP_BIN: "Pick up Bin",
        DROPOFF_BIN: "Drop off Bin",
        START_SHIFT: "Start Shift",
        END_SHIFT: "End Shift",
        VERIFY_COLLECTION: "Verify Collection",
        ABORT_COLLECTION: "Abort Collection",
        BIN_PICKED_UP: "Bin Picked Up",
        SKIP_VERIFITCATION: "Skip Verification",
        UPDATE_SKIP_WEIGHT: "Update Skip Weight",
        CONTRACT_TERMINATION: "Contract Termination",
        MAINTENANCE_PICKUP: "Maintenance Pick up",
        UPDATE_SKIP_DETAILS: "Details Updated",
        WORKSHOP_DROP: "Workshop Drop",
        SPARE_SKIP_DEPOSIT: "Spare Bin Deposit",

        PACKAGE_DROP: "Package Dropped",

        TYRE_BURST: "Tyre Burst",
        BREAK_FAILURE: "Break Failure",
        ACCIDENT: "Accident",
        OTHERS: "others",

        PLASTIC: "Plastic",
        GALVANIZED_METAL_OR_PLASTIC: "Galvanized Metal or Plastic",
        GALVANIZED_METAL: "Galvanized Metal",
        METAL: "Metal",

        LUMP_SUM: "Lump Sum",
        WEIGHT_BASED: "Weight Based",
        TRIP_BASED: "Trip Based",
        WEIGHT_AND_TRIP_BASED: "Weight and trip based",

        ACTIVITY_UPDATED: "Activity Updated",
        CONTAINER: "Container",
        TANK: "Tank",

        COMPACTOR: "compactor",
        HOOK_LOADER: "hook loader",
        CHAIN_LOADER: "chain loader",
        TIPPER_TRUCK: "tipper truck",

        SKIP_SIZE_1: '1.1 cbm',
        SKIP_SIZE_2: '2.5 cbm',
        SKIP_SIZE_3: '5 cbm',
        SKIP_SIZE_4: '8 cbm',
        SKIP_SIZE_5: '10 cbm',
        SKIP_SIZE_6: '12 cbm',
        SKIP_SIZE_7: '14 cbm',
        SKIP_SIZE_8: '18 cbm',
        SKIP_SIZE_9: '20 cbm',
        SKIP_SIZE_10: '26 cbm',
        SKIP_SIZE_11: '30 cbm',
        SKIP_SIZE_12: '240 liters',
        SKIP_SIZE_13: '40 cbm',
        SKIP_SIZE_14: 'Medical Waste',

        MAINTENANCE_DATA_COST_LABOR: "Labor",
        MAINTENANCE_DATA_COST_PARTS: "Parts",
        MAINTENANCE_DATA_COST_TAXES: "Tax",
        MAINTENANCE_DATA_COST_DISCOUNT: "Discount",
        MAINTENANCE_DATA_COST_FINE: "Fine",

        FUEL_COST: "Fuel Cost",
        LABOUR_COST: "Labour Cost",
        OTHER_COST: "Other Cost",

        WHEELER_6: "6 Wheeler",
        WHEELER_14: "14 Wheeler",
        WHEELER_18: "18 Wheeler",
        WHEELER_22: "22 Wheeler"
    }


# Starting From 1512
class FFPOptionsEnum(enum.Enum):
    # EMPLOYEE TYPES
    SITE_SUPERVISOR = 1500
    ZONE_SUPERVISOR = 1501
    TEAM_SUPERVISOR = 1502
    LABOUR = 1503

    # TASKS
    TASK_COMPLETED = 1504
    TASK_APPROVED = 1505

    # Violations
    OUT_OF_ZONE = 1506
    IN_ZONE = 1509
    IN_SITE = 1510
    OUT_OF_SITE = 1511

    # Attendance
    CHECK_IN = 1507
    CHECK_OUT = 1508

    labels = {
        SITE_SUPERVISOR: "site supervisor",
        ZONE_SUPERVISOR: "zone Supervisor",
        TEAM_SUPERVISOR: "team supervisor",
        LABOUR: "labour",

        TASK_COMPLETED: "task completed",
        TASK_APPROVED: "task approved",

        IN_ZONE: "in zone",
        OUT_OF_ZONE: "out of zone",
        IN_SITE: "in site",
        OUT_OF_SITE: "out of site",
        CHECK_IN: "checked in",
        CHECK_OUT: "check out",

    }


class PPPOptionsEnum(enum.Enum):
    # Training Type
    CARDIO = 501
    AEROBICS = 502
    # Injury Type
    NAME1 = 503
    NAME2 = 504
    NAME3 = 505
    # Match Type
    PRE_MATCH = 506
    POST_MATCH = 507
    # Training Status
    PRE_TRAINING = 508
    POST_TRAINING = 509
    TRAINING_COMPLETED = 510
    TRAINING_INCOMPLETE = 511
    TRAINING_INPROGRESS = 512
    # Match Status
    WIN = 513
    LOSS = 514
    # Playing Status
    PLAYING = 515
    NOTPLAYING = 516
    # Injury Status
    INJURED = 517
    NOTINJURED = 518
    RECOVERING = 519
    # Injury Position
    SHOULDER = 520
    KNEE = 521
    HAND = 522
    HEAD = 523
    FOOT = 524
    # Perceived Effect
    POSITIVE = 525
    NEGATIVE = 526
    NOCHANGE = 527
    # Contracted Type
    CONTRACT_1 = 528
    CONTRACT_2 = 529

    label = {
        CARDIO: "Cardio",
        AEROBICS: "Aerobics",
        NAME1: "Name 1",
        NAME2: "Name 2",
        NAME3: "Name 3",
        PRE_MATCH: "Pre Match",
        POST_MATCH: "Post Match",
        PRE_TRAINING: "Pre Training",
        POST_TRAINING: "Post Training",
        TRAINING_COMPLETED: "Training Completed",
        TRAINING_INCOMPLETE: "Training Incomplete",
        TRAINING_INPROGRESS: "Training InProgress",
        WIN: "Win",
        LOSS: "Loss",
        PLAYING: "Playing",
        NOTPLAYING: "Not Playing",
        INJURED: "Injured",
        NOTINJURED: "Not Injured",
        RECOVERING: "Recovering",
        SHOULDER: "Shoulder",
        KNEE: "Knee",
        HAND: "Hand",
        HEAD: "Head",
        FOOT: "Foot",
        POSITIVE: "Positive",
        NEGATIVE: "Negative",
        NOCHANGE: "No Change",
        CONTRACT_1: "Contract 1",
        CONTRACT_2: "Contract 2",
    }


class NewIopEnum():
    modelTypes = [
        {'type': 'EWH-S35CSE', 'capacity': 35, 'weight': 8.5, 'dimensions': {'height': 480, 'diameter': 420}},
        {'type': 'EWH-S45CSE', 'capacity': 45, 'weight': 9.8, 'dimensions': {'height': 567, 'diameter': 420}},
        {'type': 'EWH-S55CSE', 'capacity': 55, 'weight': 10.8, 'dimensions': {'height': 657, 'diameter': 420}},
        {'type': 'EWH-S35CSE', 'capacity': 65, 'weight': 11.8, 'dimensions': {'height': 746, 'diameter': 420}},
    ]
    VOLTAGE = 220
    FREQUENCY = 50
    POWER = 1800
    TANK_TYPE = "Vertical Tank"
    CLASSIFICATION = "Class 1 = IPX 1"


class EntityStandModeEnum(enum.Enum):
    ON = 1
    OFF = 2
    STANDBY = 3

    labels = {
        ON: "On",
        OFF: "Off",
        STANDBY: "Standby",
    }
    

class Enum:
    
    def get_standby_mode(self, standby):
        """Returns a random key for given type."""
        stand_by_dict = {1: 'On', 2: 'Off', 3: 'Standby'}
        if type(standby).__name__ == 'int':
            for key, value in stand_by_dict.items():
                if value == standby:
                    return key
        if stand_by_dict.get(standby):
            return stand_by_dict[standby]
        return 0
    
    def get_chs_mode(self, chs):
        """Returns a random key for given type."""
        chs_by_dict = {1: 'off', 2: 'standby', 3: 'idle',4:'heating',5:'failure'}
        if type(chs).__name__ == 'int':
            for key, value in chs_by_dict.items():
                if value == chs:
                    return key
        if chs_by_dict.get(chs):
            return chs_by_dict[chs]
        return 0

    def get_event_type_mode(self, event_types):
        """Returns a random key for given type."""
        type_by_dict = {50: 'warm', 60: 'hot', 70: 'very hot'}
        if type(event_types).__name__ == 'int':
            for key, value in type_by_dict.items():
                if value == event_types:
                    return key
        if type_by_dict.get(event_types):
            return type_by_dict[event_types]
        return 0

