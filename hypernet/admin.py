from django.contrib import admin
from .models import *

from ppp.models import *
from iof.models import *
from user.models import *
from ioa.models import *
from customer.models import *
from ffp.models import *
# Register your models here.
from iop.models import *
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
admin.site.register(InvoiceData)
admin.site.register(UserEntityAssignment)
admin.site.register(EntityDocument)

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
admin.site.register(LogisticMaintenance)
admin.site.register(LogisticMaintenanceData)

#IOA
admin.site.register(ActivityList)
admin.site.register(Aggregation)
admin.site.register(Scheduling)
admin.site.register(AnimalStates)

#FFP
admin.site.register(Tasks)
admin.site.register(AttendanceRecord)
admin.site.register(EmployeeViolations)
admin.site.register(FFPDataDailyAverage)


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


#  IoP
admin.site.register(IopDerived)
admin.site.register(IopAggregation)
admin.site.register(EnergyConsumption)
admin.site.register(ApplianceQR)
