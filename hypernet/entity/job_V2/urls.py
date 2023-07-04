from .function_views import *
from django.conf.urls import url, include

urlpatterns = [
    url(r'^add_new_job', add_activity_scehdule),
    url(r'^edit_activity_scehdule', edit_activity_scehdule),
    url(r'^mark_job_inactive', mark_activity_inactive),
    url(r'^get_activity_schedules', get_activity_schedules),
    url(r'^get_activities_data', get_activities_data),
    url(r'^suspend_resume_activity_schedule', suspend_schedule),
    url(r'^get_upcoming_activities', get_upcoming_activities),
    url(r'^get_activities_details', get_activities_details),
    url(r'^get_bins_activities', get_bins_activities),
    # url(r'^edit_entity', edit_entity),
]
