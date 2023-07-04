# PDSIP = "139.59.239.39"
PDSIP = "168.63.200.245"


# ------------ General Constants -----------------
TEXT_ALREADY_EXISTS = "Already Exists"
TEXT_DOES_NOT_EXISTS = "Does Not Exists"

ONE_SIGNAL_APP_ID = 'f4201e3f-8a83-4e49-9936-59a9cb302be2'
ONE_SIGNAL_APP_ID_NEW_TAGS = 'afa2ffbe-1208-4c2f-851c-592b1087e237'
ONE_SIGNAL_REST_API_KEY = 'NGZjYTJiOGUtNzBmOS00MDgxLWE1NjctOGZkZjg3NGVlMTdh'
ONE_SIGNAL_REST_API_KEY_NEW_TAGS = 'N2ViMTRmZDgtMjc0OC00YzFkLWIzYTAtZGRmN2Y2MDFmNTFk'

UNAUTHORIZED_USER = "Invalid Login credentials"
TEXT_OPERATION_UNSUCCESSFUL = "Operation_Unsuccessful"
TEXT_OPERATION_SUCCESSFUL = "Operation_Successful"
# TEXT_SUCCESSFUL = "Operation Successful"
TEXT_SUCCESSFUL = "Record has been added successfully"
TEXT_EDITED_SUCCESSFUL = "Record has been modified successfully"
METHOD_DOES_NOT_EXIST = "The specified method does not exist"
DEFAULT_ERROR_MESSAGE = "There is some issue your request cannot be processed."
TEXT_PARAMS_MISSING = "Params are missing"
TEXT_PARAMS_INCORRECT = "Incorrect param"
ALREADY_EXISTS = "Value already exists"
START_SHIFT = "Please start your shift first."
NOT_ALLOWED = 'You are not allowed to view this data'
INVALID_MODULE = 'Invalid module. Please try again'
TRUCK_OFFLINE_ACTIVITY = "Truck is offline. Please wait for the truck to be online or contact your administrator."
TRUCK_DATA_DOES_NOT_EXIST = "Truck data is not available. Please contact your administrator."
ACTIVITY_EXPIRED = "Activity is no longer valid. Please contact your administrator."

NO_ENTITY_SELECTED = " Please select the given "
EMAIL_INVITATION_MESSAGE = "This email is system generated for activation of your hypernet account."
EMAIL_FORGOT_PASSWORD_MESSAGE = "You've requested to change the password of your hypernet account."
NO_DATA_TO_DISPLAY = 'No data to display. Please try again'
email_list = ['waleed.shabbir@hypernymbiz.com', 'khizer.salman@hypernymbiz.com', 'hamza.rizwan@hypernymbiz.com']
client_email_list = ['waleed.shabbir@hypernymbiz.com', 'khizer.salman@hypernymbiz.com']
USER_DOES_NOT_EXIST  = "The specified user does not exist"
NO_LAST_ACTIVITY = "No Last Activity of the specified user."
HYPERNET_LANGUAGES = 'hypernet_languages'
ENGLISH = 'English'
FRENCH = 'French'
ITALIAN = "Italian"
DELETED = 'Deleted'
HYPERNET_ALERTS_STATUS = 'Hypernet_alerts'
ALERT_GENERATED = 'Generated'
ALERT_SCHEDULED = 'Scheduled'
ALERT_IGNORED = 'Ignored'

HYPERNET_ROUTINE_TYPE = 'routine_type'
ROUTINE_TYPE_DAILY = 'daily'
ROUTINE_TYPE_WEEKLY = 'weekly'
ROUTINE_TYPE_ONCE = 'once'
ROUTINE_TYPE_MONTHLY = 'monthly'
ROUTINE_TYPE_YEARLY = 'yearly'
ROUTINE_TYPE_ALTER_DAYS = 'alternate days'

ACTIVITY_PRIORITY = 'activity priority'
ACTIVITY_PRIORITY_HIGH = 'high'
ACTIVITY_PRIORITY_MEDIUM = 'medium'
ACTIVITY_PRIORITY_LOW = 'low'

WEEKDAYS = 'weekdays'
WEEKDAY_MONDAY = 'monday'
WEEKDAY_TUESDAY = 'tuesday'
WEEKDAY_WEDNESDAY = 'wednesday'
WEEKDAY_THURSDAY = 'thursday'
WEEKDAY_FRIDAY = 'friday'
WEEKDAY_SATURDAY =  'saturday'
WEEKDAY_SUNDAY = 'sunday'

NOTIFICATION_TYPE = 'notification_type'
NOTIFCIATION_DRIVER_ACCEPT_REJECT = 'notification_driver_accept_reject'
NOTIFICATION_ADMIN_ACTIVITY_REVIEW = 'notification_admin_activity_review'
NOTIFICATION_ADMIN_ACTIVITY_REVIEW_DRIVER_REJECT = 'notification_admin_activity_review_driver_reject'
NOTIFICATION_ADMIN_ACTIVITY_REVIEW_TRUCK_CONFLICT = 'notification_admin_activity_review_truck_conflict'
NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_ABORT = 'notification_admin_acknowledge_driver_abort'
NOTIFICATION_DRIVER_START_ACTIVITY = 'notification_driver_start_activity'
NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_ACCEPT = 'notification_admin_acknowledge_driver_accept'
NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_SUSPEND = 'notification_admin_acknowledge_driver_reject'
NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_RESUME = 'notification_admin_acknowledge_driver_suspend'
NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_COMPLETE = 'notification_admin_acknowledge_driver_complete'
NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_START = 'notification_admin_acknowledge_driver_start'
NOTIFICATION_ADMIN_ACTIVITY_REVIEW_NO_ACTION_ACCEPT_REJECT = 'notification_admin_activity_review_no_action_driver_accept_reject'
NOTIFICATION_ADMIN_ACTIVITY_REVIEW_DRIVER_CONFLICT = 'notification_admin_activity_review_driver_conflict'
NOTIFICATION_DRIVER_BIN_PICKUP = 'notification_driver_bin_pickup'
NOTIFICATION_DRIVER_WASTE_COLLECTION = 'notification_driver_waste_collection'
NOTIFICATION_DRIVER_BIN_DROPOFF = 'notification_driver_bin_dropoff'
NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_SHIFT_START = 'notification_admin_acknowledge_driver_shift_start'
NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_SHIFT_COMPLETE = 'notification_admin_acknowledge_driver_shift_complete'
NOTIFICATION_ADMIN_ACTIVITY_REVIEW_NO_ACTION_START_FAIL = 'notification_admin_activity_review_no_action_driver_start_fail'
NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_BIN = 'notifiation_admin_acknowledge_add_asset_bin'
NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_DRIVER = 'notifiation_admin_acknowledge_add_asset_driver'
NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_SUPERVISOR = 'notifiation_admin_acknowledge_add_asset_supervisor'
NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_RFID_CARD = 'notifiation_admin_acknowledge_add_asset_rfid_card'
NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_RFID_TAG = 'notifiation_admin_acknowledge_add_asset_rfid_tag'
NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_RFID_SCANNER = 'notifiation_admin_acknowledge_add_asset_rfid_scanner'



ENTITY_OCCUPIED = ' Truck/driver has an ongoing/accepted activity and is not available'
ENTITY_ALREADY_COLLECTED = ' Bin added is already collected for current activity. Please remove bin from list.'
REVIEW_ACTIVITY = 'No conflicts.Please review this activity'
hypernet_options_dict =[
    {'id': 1, 'value': 'Active', 'key': 'recordstatus'},
    {'id': 2, 'value': 'Inactive', 'key': 'recordstatus'},
    {'id': 3, 'value': "Male", 'key': 'gender'},
    {'id': 4, 'value': "Female", 'key': 'gender'},
    {'id': 5, 'value': "Other", 'key': 'gender'},
    {'id': 6, 'value': "Married", 'key': 'maritalstatus'},
    {'id': 7, 'value': "Single", 'key': 'maritalstatus'},
    {'id': 8, 'value': "Divorced", 'key': 'maritalstatus'},
    {'id': 9, 'key': HYPERNET_LANGUAGES, 'value': ENGLISH},
    {'id': 10, 'key': HYPERNET_LANGUAGES, 'value': FRENCH},
    {'id': 11, 'key': HYPERNET_LANGUAGES, 'value': ITALIAN},
    {'id': 12, 'key': 'recordstatus', 'value': DELETED},
    {'id': 13, 'key': HYPERNET_ALERTS_STATUS, 'value': ALERT_GENERATED},
    {'id': 14, 'key': HYPERNET_ALERTS_STATUS, 'value': ALERT_SCHEDULED},
    {'id': 15, 'key': HYPERNET_ALERTS_STATUS, 'value': ALERT_IGNORED},
    {'id': 16, 'key': HYPERNET_ROUTINE_TYPE, 'value': ROUTINE_TYPE_DAILY},
    {'id': 17, 'key': HYPERNET_ROUTINE_TYPE, 'value': ROUTINE_TYPE_WEEKLY},
    {'id': 18, 'key': HYPERNET_ROUTINE_TYPE, 'value': ROUTINE_TYPE_ONCE},
    {'id': 19, 'key': HYPERNET_ROUTINE_TYPE, 'value': ROUTINE_TYPE_MONTHLY},
    {'id': 20, 'key': HYPERNET_ROUTINE_TYPE, 'value': ROUTINE_TYPE_YEARLY},
    {'id': 21, 'key': HYPERNET_ROUTINE_TYPE, 'value': ROUTINE_TYPE_ALTER_DAYS},

    {'id': 22, 'key': ACTIVITY_PRIORITY, 'value': ACTIVITY_PRIORITY_HIGH},
    {'id': 23, 'key': ACTIVITY_PRIORITY, 'value': ACTIVITY_PRIORITY_MEDIUM},
    {'id': 24, 'key': ACTIVITY_PRIORITY, 'value': ACTIVITY_PRIORITY_LOW},

    {'id': 25, 'key': WEEKDAYS, 'value': WEEKDAY_MONDAY},
    {'id': 26, 'key': WEEKDAYS, 'value': WEEKDAY_TUESDAY},
    {'id': 27, 'key': WEEKDAYS, 'value': WEEKDAY_WEDNESDAY},
    {'id': 28, 'key': WEEKDAYS, 'value': WEEKDAY_THURSDAY},
    {'id': 29, 'key': WEEKDAYS, 'value': WEEKDAY_FRIDAY},
    {'id': 30, 'key': WEEKDAYS, 'value': WEEKDAY_SATURDAY},
    {'id': 31, 'key': WEEKDAYS, 'value': WEEKDAY_SUNDAY},
]

IOF_MAINTENANCE = 'iof_maintenance'
ENGINE_TUNING_MAINTENANCE = 'Engine Tuning'
SERVICE_MAINTENANCE = 'Service'
TYRE_REPLACEMENT_MAINTENANCE = 'Tyre Replacement'
SUSPENSION_REPAIR_MAINTENANCE = 'Suspension Repair'

IOF_MAINTENANCE_STATUSES = 'iof_maintenance_status'
MAINTENANCE_OVER_DUE = 'over due'
MAINTENANCE_COMPLETED = 'completed'
MAINTENANCE_DUE = 'due'

IOF_ACTIVITY_STATUSES = 'iof_activity_status'
ACTIVITY_BIN_COLLECTION = 'bin_collection'

#Incident types
INCIDENT_TYPE = 'incident_type'
TYRE_BURST = 'tyre_burst'
BREAK_FAILURE = 'break_failure'
ACCIDENT = 'accident'
OTHERS = 'others'

INVOICE_TYPE = "invoice type"
LUMP_SUM = "lump sum"
WEIGHT_BASED = "weight based"
TRIP_BASED = "trip based"
WEIGHT_AND_TRIP_BASED = "weight and trip based"
# latest 140
logistics_options_dict =[

{'id':50, 'value': "Owned",'key':'purchasestatus'},
{'id':51, 'value': "Leased",'key':'purchasestatus'},

{'id':52, 'value': "Running",'key':'jobstatus'},
{'id':53, 'value': "Pending",'key':'jobstatus'},
{'id':54, 'value': "Aborted",'key':'jobstatus'},
{'id':55, 'value': "Completed",'key':'jobstatus'},
{'id':74, 'value': "Accepted",'key':'jobstatus'},
{'id':75, 'value': "Rejected",'key':'jobstatus'},
{'id':78, 'value': "Suspended",'key':'jobstatus'},
{'id':79, 'value': "Resumed",'key':'jobstatus'},
{'id':78, 'value': "Suspended",'key':'jobstatus'},
{'id':92, 'value': "Collected",'key':'jobstatus'},
{'id':93, 'value': "Uncollected",'key':'jobstatus'},
{'id':94, 'value': "Started",'key':'jobstatus'},
{'id':95, 'value': "Reviewed",'key':'jobstatus'},
{'id':96, 'value': "Conflicting",'key':'jobstatus'},
{'id':117, 'value': "Failed",'key':'jobstatus'},


{'id':56, 'value': "Red",'key':'territorytype'},
{'id':57, 'value': "Green",'key':'territorytype'},
{'id':58, 'value': "Blue",'key':'territorytype'},

{'id':59, 'value': "Speed",'key':'iof_violationtype'},
{'id':60, 'value': "Volume",'key':'iof_violationtype'},
{'id':61, 'value': "Temperature",'key':'iof_violationtype'},
{'id':62, 'value': "Density",'key':'iof_violationtype'},
{'id':63, 'value': "HarshBraking",'key':'iof_violationtype'},
{'id':64, 'value': "HarshAcceleration",'key':'iof_violationtype'},
{'id':65, 'value': "FillupThreshold",'key':'iof_violationtype'},
{'id':66, 'value': "DecantThreshold",'key':'iof_violationtype'},
{'id':76, 'value': "VolumeOverflow",'key':'iof_violationtype'},
{'id': 124, 'value': "Territory Violation", 'key': 'iof_violationtype'},

    {'id': 67, 'key': IOF_MAINTENANCE, 'value': ENGINE_TUNING_MAINTENANCE},
    {'id': 68, 'key': IOF_MAINTENANCE, 'value': SERVICE_MAINTENANCE},
    {'id': 69, 'key': IOF_MAINTENANCE, 'value': TYRE_REPLACEMENT_MAINTENANCE},
    {'id': 70, 'key': IOF_MAINTENANCE, 'value': SUSPENSION_REPAIR_MAINTENANCE},

    {'id': 71, 'key': IOF_MAINTENANCE_STATUSES, 'value': MAINTENANCE_OVER_DUE},
    {'id': 72, 'key': IOF_MAINTENANCE_STATUSES, 'value': MAINTENANCE_COMPLETED},
    {'id': 73, 'key': IOF_MAINTENANCE_STATUSES, 'value': MAINTENANCE_DUE},
    {'id': 77, 'key': IOF_ACTIVITY_STATUSES, 'value': ACTIVITY_BIN_COLLECTION},

    {'id': 80, 'key': NOTIFICATION_TYPE, 'value': NOTIFCIATION_DRIVER_ACCEPT_REJECT},
    {'id': 81, 'key': NOTIFICATION_TYPE, 'value': NOTIFICATION_ADMIN_ACTIVITY_REVIEW},
    {'id': 82, 'key': NOTIFICATION_TYPE, 'value': NOTIFICATION_ADMIN_ACTIVITY_REVIEW_DRIVER_REJECT},
    {'id': 83, 'key': NOTIFICATION_TYPE, 'value': NOTIFICATION_ADMIN_ACTIVITY_REVIEW_TRUCK_CONFLICT},
    {'id': 84, 'key': NOTIFICATION_TYPE, 'value': NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_ABORT},
    {'id': 85, 'key': NOTIFICATION_TYPE, 'value': NOTIFICATION_DRIVER_START_ACTIVITY},
    {'id': 86, 'key': NOTIFICATION_TYPE, 'value': NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_ACCEPT},
    {'id': 87, 'key': NOTIFICATION_TYPE, 'value': NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_SUSPEND},
    {'id': 88, 'key': NOTIFICATION_TYPE, 'value': NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_RESUME},
    {'id': 89, 'key': NOTIFICATION_TYPE, 'value': NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_COMPLETE},
    {'id': 90, 'key': NOTIFICATION_TYPE, 'value': NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_START},
    {'id': 91, 'key': NOTIFICATION_TYPE, 'value': NOTIFICATION_ADMIN_ACTIVITY_REVIEW_NO_ACTION_ACCEPT_REJECT},
    {'id': 112, 'key': NOTIFICATION_TYPE, 'value': NOTIFICATION_ADMIN_ACTIVITY_REVIEW_DRIVER_CONFLICT},
    {'id': 113, 'key': NOTIFICATION_TYPE, 'value': NOTIFICATION_DRIVER_BIN_PICKUP},
    {'id': 114, 'key': NOTIFICATION_TYPE, 'value': NOTIFICATION_DRIVER_WASTE_COLLECTION},
    {'id': 115, 'key': NOTIFICATION_TYPE, 'value': NOTIFICATION_DRIVER_BIN_DROPOFF},
    {'id': 118, 'key': NOTIFICATION_TYPE, 'value': NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_SHIFT_START},
    {'id': 119, 'key': NOTIFICATION_TYPE, 'value': NOTIFICATION_ADMIN_ACKNOWLEDGE_DRIVER_SHIFT_COMPLETE},

    {'id':97, 'value': "Collect Waste",'key':'rfidapp'},
    {'id':98, 'value': "Waste Collected",'key':'rfidapp'},
    {'id':99, 'value': "Pickup Bin",'key':'rfidapp'},
    {'id':100, 'value': "Dropoff Bin",'key':'rfidapp'},
    {'id':111, 'key':  'rfidapp', 'value': "Bin Picked Up"},

    {'id':101, 'value': "Start Shift",'key':'rfidapp'},
    {'id':102, 'value': "End Shift",'key':'rfidapp'},

    {'id':103, 'value': "Verify Collection",'key':'rfidapp'},
    {'id':104, 'value': "Abort Collection",'key':'rfidapp'},

    {'id':105, 'key':  INCIDENT_TYPE, 'value': TYRE_BURST},
    {'id':106, 'key':  INCIDENT_TYPE, 'value': BREAK_FAILURE},
    {'id':107, 'key':  INCIDENT_TYPE, 'value': ACCIDENT},
    {'id':108, 'key':  INCIDENT_TYPE, 'value': OTHERS},
    {'id':116, 'key':  'rfidapp', 'value': "Skip Verification"},
    {'id':135, 'key':  'rfidapp', 'value': "Update Skip Weight"},

    {'id':120, 'key':  'bintypes', 'value': "Plastic"},
    {'id':121, 'key':  'bintypes', 'value': "Galvanized Metal or Plastic"},
    {'id':122, 'key':  'bintypes', 'value': "Galvanized Metal"},
    {'id': 134, 'key': 'bintypes', 'value': "Metal"},

    {'id': 131, 'key': 'trucktypes', 'value': "Compactor"},
    {'id': 132, 'key': 'trucktypes', 'value': "Hook Loader"},
    {'id': 133, 'key': 'trucktypes', 'value': "Chain Loader"},

    {'id':123, 'key':  NOTIFICATION_TYPE, 'value': NOTIFICATION_ADMIN_ACTIVITY_REVIEW_NO_ACTION_START_FAIL},

    {'id':125, 'key':  NOTIFICATION_TYPE, 'value': NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_BIN},
    {'id':126, 'key':  NOTIFICATION_TYPE, 'value': NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_DRIVER},
    {'id':127, 'key':  NOTIFICATION_TYPE, 'value': NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_SUPERVISOR},
    {'id':128, 'key':  NOTIFICATION_TYPE, 'value': NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_RFID_CARD},
    {'id':129, 'key':  NOTIFICATION_TYPE, 'value': NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_RFID_TAG},
    {'id':130, 'key':  NOTIFICATION_TYPE, 'value': NOTIFICATION_ADMIN_ACKNOWLEDGE_ADD_ASSET_RFID_SCANNER},

    {'id':136, 'key':  INVOICE_TYPE, 'value': LUMP_SUM},
    {'id':137, 'key':  INVOICE_TYPE, 'value': WEIGHT_BASED},
    {'id':138, 'key':  INVOICE_TYPE, 'value': TRIP_BASED},
    {'id':139, 'key':  INVOICE_TYPE, 'value': WEIGHT_AND_TRIP_BASED},

]


player_options_dict =[

{'id':501, 'value': "Cardio",'key':'trainingtype'},
{'id':502, 'value': "Aerobics",'key':'trainingtype'},

{'id':503, 'value': "Name 1",'key':'injurytype'},
{'id':504, 'value': "Name 2",'key':'injurytype'},
{'id':505, 'value': "Name 3",'key':'injurytype'},

{'id':506, 'value': "Pre",'key':'matchtype'},
{'id':507, 'value': "Post",'key':'matchtype'},

{'id':508, 'value':'Pre','key':'trainingstatus'},
{'id':509, 'value':"Post",'key':'trainingstatus'},
{'id':510, 'value':"Completed",'key':'trainingstatus'},
{'id':511, 'value':"Incomplete",'key':'trainingstatus'},
{'id':512, 'value':"InProgress",'key':'trainingstatus'},

{'id':513, 'value': "Win",'key':'matchstatus'},
{'id':514, 'value': "Loss",'key':'matchstatus'},

{'id':515, 'value': "Playing",'key':'playingstatus'},
{'id':516, 'value': "Not Playing",'key':'playingstatus'},

{'id':517, 'value': "Injured",'key':'injurystatus'},
{'id':518, 'value': "Not Injured",'key':'injurystatus'},
{'id':519, 'value': "Recovering",'key':'injurystatus'},

{'id':520, 'value': "Shoulder",'key':'injuryposition'},
{'id':521, 'value': "Knee",'key':'injuryposition'},
{'id':522, 'value': "Hand",'key':'injuryposition'},
{'id':523, 'value': "Head",'key':'injuryposition'},
{'id':524, 'value': "Foot",'key':'injuryposition'},

{'id':525, 'value': "Positive",'key':'perceivedeffect'},
{'id':526, 'value': "Negative",'key':'perceivedeffect'},
{'id':527, 'value': "No Change",'key':'perceivedeffect'},

{'id':528, 'value': "Contract 1",'key':'contracttype'},
{'id':529, 'value': "Contract 2",'key':'contracttype'}

]

ALERT_TYPE = "ioa_violation_type"
RUMINATION = "rumination"
LAMENESS = "lameness"
ESTRUS = "estrus"
TEMPERATURE = "temperature"


ACTIVITY_ACTION_STATUS = "ioa_activity_action_status"
COMPLETE = "complete"
INCOMPLETE = "incomplete"
PENDING = "pending"

TOTAL = "total"

ACTIVITY_TYPE = "ioa_activity_type"
MILKING = "milking"
FEEDING = "feeding"
BREEDING = "breeding"
INSPECTION = "inspection"

IOA_INFO_NOTIFICATION = "ioa_info_notification"
INFORMATION = "information"

ANIMAL_GROUP = "ioa_animal_group"
IN_LACTATION = "in_lactation"
HEIFERS = "heifers"
CALFS = "calfs"

ROUTINE_TYPE = "ioa_routine_type"
DAILY = "daily"
WEEKLY = "weekly"
ONCE = "once"

LACTATION_STATUS = "ioa_lactation_status"
DRY = "dry"
PREGNANT = "pregnant"
LACTATING = "lactating"
NON_LACTATING = "non_lactating"

ACTIVITY_PRIORITY = "ioa_activity_priority"
HIGH = "high"
MEDIUM = "medium"
LOW = "low"



OBJECT_DETAILS = 'object_details'

ioa_options_dict = [

    {'id': 1001, 'key': ALERT_TYPE, 'value': ESTRUS},
    {'id': 1002, 'key': ALERT_TYPE, 'value': RUMINATION},
    {'id': 1003, 'key': ALERT_TYPE, 'value': LAMENESS},
    {'id': 1004, 'key': ALERT_TYPE, 'value': TEMPERATURE},

    {'id': 1005, 'key': ACTIVITY_ACTION_STATUS, 'value': COMPLETE},
    {'id': 1006, 'key': ACTIVITY_ACTION_STATUS, 'value': INCOMPLETE},
    {'id': 1007, 'key': ACTIVITY_ACTION_STATUS, 'value': PENDING},

    {'id': 1008, 'key': ACTIVITY_TYPE, 'value': MILKING},
    {'id': 1009, 'key': ACTIVITY_TYPE, 'value': FEEDING},
    {'id': 1010, 'key': ACTIVITY_TYPE, 'value': BREEDING},

    {'id': 1011, 'key': ANIMAL_GROUP, 'value': IN_LACTATION},
    {'id': 1012, 'key': ANIMAL_GROUP, 'value': HEIFERS},
    {'id': 1013, 'key': ANIMAL_GROUP, 'value': CALFS},

    {'id': 1014, 'key': ROUTINE_TYPE, 'value': DAILY},
    {'id': 1015, 'key': ROUTINE_TYPE, 'value': WEEKLY},
    {'id': 1016, 'key': ROUTINE_TYPE, 'value': ONCE},

    {'id': 1017, 'key': LACTATION_STATUS, 'value': LACTATING},
    {'id': 1018, 'key': LACTATION_STATUS, 'value': NON_LACTATING},
    {'id': 1019, 'key': LACTATION_STATUS, 'value': PREGNANT},
    {'id': 1020, 'key': LACTATION_STATUS, 'value': DRY},

    {'id': 1021, 'key': ACTIVITY_PRIORITY, 'value': HIGH},
    {'id': 1022, 'key': ACTIVITY_PRIORITY, 'value': MEDIUM},
    {'id': 1023, 'key': ACTIVITY_PRIORITY, 'value': LOW},

    {'id': 1024, 'key': ACTIVITY_TYPE, 'value': INSPECTION},

    {'id': 1025, 'key': IOA_INFO_NOTIFICATION, 'value': INFORMATION},
]

IOA_VIOLATION_TYPES = [ESTRUS, RUMINATION, LAMENESS, TEMPERATURE]
# IOA_VIOLATION_THRESHOLD = []
IOA_VIOLATION_THRESHOLD = {ESTRUS: (1*60*60),  # more than 1 hour,
                           RUMINATION: (4*60*60),  # less than 4 hours - diff time for Heifers and Cows
                           LAMENESS: (1 * 60 * 60),
                           TEMPERATURE: (0)  # more than 1 hour
                           }
IOA_VIOLATION_INTERVAL = {ESTRUS: 1,  # max 1 alert in 24 hours.
                          RUMINATION: 1,
                          LAMENESS: 1
                          }

IOA_ESTRUS_CRITERIA = {'estrus_span': (20 * 60 * 60),  # 20 hours - duration of a single estrus onset.
                       'estrus_gap': (15*24*60*60),  # 15 days - time between estrus end and next onset.
                       'range_for_onset': (10*60),  # last 10 min AnimalStates to consider
                       'onset_threshold': 10,  # 10 messages (at 1 per 10 seconds)
                       'range_for_end': (20 * 60),  # last 20 min AnimalStates to consider
                       'end_threshold': 0
                       }

IOA_ACTIVITY_ACTION_STATUS = [COMPLETE, INCOMPLETE, PENDING]
IOA_ACTIVITY_TYPES = [MILKING, FEEDING, BREEDING]
IOA_ANIMAL_GROUPS = [CALFS, HEIFERS, IN_LACTATION]
IOA_ROUTINE_TYPES = [DAILY, WEEKLY, ONCE]
IOA_LACTATION_STATUS = [LACTATING, DRY,PREGNANT]
IOA_ACTIVITY_PRIORITY = [HIGH, MEDIUM, LOW]

LANGUAGES = [ENGLISH, FRENCH, ITALIAN]

STATUS_OK = True
STATUS_ERROR = False
RESPONSE_STATUS = "status"
RESPONSE_MESSAGE = "message"
RESPONSE_DATA = "response"



ERROR_RESPONSE_BODY = {
    RESPONSE_STATUS: 500,
    RESPONSE_MESSAGE: DEFAULT_ERROR_MESSAGE,
}

ERROR_PARAMS_MISSING_BODY = {
    RESPONSE_STATUS: STATUS_ERROR,
    RESPONSE_MESSAGE: TEXT_PARAMS_MISSING
}


TODAY = 1
LAST_TWO_DAYS = 2
LAST_WEEK = 7
LAST_2WEEKS = 14
LAST_THIRTY_DAYS = 30
# Used for slicing the variable will return 10
RECENT_DATA = 11

GRAPH_DATE_FORMAT = "%d-%b"

LAST_FIFTEEN_MINUTES = 15
LAST_THIRTY_MINUTES = 30
LAST_HOUR = 60
LAST_TWO_HOURS = 120
#Seconds
LAST_24_HOUR = 86400
#Minutes
ONE_DAY = 1440
TWO_DAYS = 2880
ONE_MONTH = 43800
TWO_MONTHS = 87600
YEAR = 525600
TWO_YEARS = 1051200
#HTTP Statuses
HTTP_ERROR_CODE = 500
HTTP_SUCCESS_CODE = 200

