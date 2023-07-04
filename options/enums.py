from django_enumfield import enum

#
# class OptionsEnum(enum.Enum):
#     # Record Status
#     ACTIVE = 1
#     INACTIVE = 2
#     # Gender Status
#     MALE = 3
#     FEMALE = 4
#     OTHER = 5
#     # Marital Status
#     MARRIED = 6
#     SINGLE = 7
#     DIVORCED = 8
#
#     # Purchase Type
#     OWNED = 50
#     LEASED = 51
#     # Job Status
#     RUNNING = 52
#     PENDING = 53
#     FAILED = 54
#     ACCOMPLISHED = 55
#     # Territory Type
#     RED = 56
#     GREEN = 57
#     BLUE = 58
#     # Violation Types
#     SPEED = 59
#     VOLUME = 60
#     TEMPERATURE = 61
#     DENSITY = 62
#     HARSHBRAKING = 63
#     HARSHACCELERATION = 64
#     FILLUPTHRESHOLD = 65
#     DECANTTHRESHOLD = 66
#
#     #Training Type
#     CARDIO = 501
#     AEROBICS = 502
#     #Injury Type
#     NAME1 = 503
#     NAME2 = 504
#     NAME3 = 505
#     # Match Type
#     PRE_MATCH = 506
#     POST_MATCH = 507
#     #Training Status
#     PRE_TRAINING = 508
#     POST_TRAINING = 509
#     TRAINING_COMPLETED = 510
#     TRAINING_INCOMPLETE = 511
#     TRAINING_INPROGRESS = 512
#     #Match Status
#     WIN = 513
#     LOSS = 514
#     #Playing Status
#     PLAYING = 515
#     NOTPLAYING = 516
#     # Injury Status
#     INJURED = 517
#     NOTINJURED = 518
#     RECOVERING = 519
#     #Injury Position
#     SHOULDER = 520
#     KNEE = 521
#     HAND = 522
#     HEAD = 523
#     FOOT = 524
#     #Perceived Effect
#     POSITIVE = 525
#     NEGATIVE = 526
#     NOCHANGE = 527
#     # Contracted Type
#     CONTRACT_1 = 528
#     CONTRACT_2 = 529
#
#     labels = {
#         ACTIVE: "Active",
#         INACTIVE: "Inactive",
#         MALE: "Male",
#         FEMALE: "Female",
#         OTHER: "Other",
#         OWNED: "Owned",
#         LEASED: "Leased",
#         RUNNING: "Running",
#         PENDING: "Pending",
#         FAILED: "Failed",
#         ACCOMPLISHED: "Accomplished",
#         MARRIED: "Married",
#         SINGLE: "Single",
#         DIVORCED: "Divorced",
#         RED: "Red",
#         GREEN: "Green",
#         BLUE: "Blue",
#         CARDIO: "Cardio",
#         AEROBICS: "Aerobics",
#         NAME1: "Name 1",
#         NAME2: "Name 2",
#         NAME3: "Name 3",
#         PRE_MATCH: "Pre Match",
#         POST_MATCH: "Post Match",
#         PRE_TRAINING:"Pre Training",
#         POST_TRAINING:"Post Training",
#         TRAINING_COMPLETED: "Training Completed",
#         TRAINING_INCOMPLETE: "Training Incomplete",
#         TRAINING_INPROGRESS: "Training InProgress",
#         WIN: "Win",
#         LOSS: "Loss",
#         PLAYING: "Playing",
#         NOTPLAYING: "Not Playing",
#         INJURED: "Injured",
#         NOTINJURED: "Not Injured",
#         RECOVERING: "Recovering",
#         SHOULDER: "Shoulder",
#         KNEE: "Knee",
#         HAND: "Hand",
#         HEAD: "Head",
#         FOOT: "Foot",
#         POSITIVE: "Positive",
#         NEGATIVE: "Negative",
#         NOCHANGE: "No Change",
#         CONTRACT_1: "Contract 1",
#         CONTRACT_2: "Contract 2",
#         SPEED : "Speed",
#         VOLUME : "Volume",
#         TEMPERATURE : "Temperature",
#         DENSITY : "Density",
#         HARSHBRAKING : "Harsh Braking",
#         HARSHACCELERATION : "Harsh Acceleration",
#         FILLUPTHRESHOLD : "Fillup Threshold",
#         DECANTTHRESHOLD : "Decant Theshold",
#     }
