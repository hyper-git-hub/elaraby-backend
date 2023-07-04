from django.contrib import admin
from .models import *

from ppp.models import *
from iof.models import *
from user.models import *
from ioa.models import *
from customer.models import *
# Register your models here.

admin.site.register(Module)
admin.site.register(User)
admin.site.register(ModuleAssignment)
admin.site.register(Customer)
# HYPERNET
admin.site.register(HypernetPostData)
admin.site.register(Entity)
admin.site.register(Devices)
admin.site.register(DeviceCalibration)
admin.site.register(CustomerDevice)
admin.site.register(HypernetPreData)
admin.site.register(NotificationGroups)
admin.site.register(DeviceViolation)
admin.site.register(CustomerPreferences)
admin.site.register(CustomerClients)

#PPP
admin.site.register(PlayerDerived)
admin.site.register(MatchDetails)
admin.site.register(DeviceType)
admin.site.register(TeamDerived)
admin.site.register(TrainingMetrics)
admin.site.register(Injury)
admin.site.register(ReportedInjury)

#IOL
admin.site.register(LogisticsDerived)
admin.site.register(LogisticAggregations)
admin.site.register(ActivityData)
admin.site.register(TruckTrips)
admin.site.register(Assignment)
admin.site.register(Activity)
admin.site.register(ActivitySchedule)
admin.site.register(ActivityQueue)
admin.site.register(BinCollectionData)
admin.site.register(IofShifts)
admin.site.register(IncidentReporting)

#IOA
admin.site.register(ActivityList)
admin.site.register(Aggregation)
admin.site.register(Scheduling)
admin.site.register(AnimalStates)


# Hypernet Notifications
class NotificationGroupsInline(admin.TabularInline):
    model = NotificationGroups
    extra = 1

class HypernetNotificationAdmin(admin.ModelAdmin):
    inlines = (NotificationGroupsInline,)

class UserAdmin(admin.ModelAdmin):
    inlines = (NotificationGroupsInline,)

admin.site.register(HypernetNotification, HypernetNotificationAdmin)

# admin.site.register(CustomerClients)