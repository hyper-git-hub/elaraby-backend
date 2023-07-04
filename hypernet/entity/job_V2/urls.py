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
    url(r'^update_running_activity', update_running_activity),
    url(r'^get_collection_events', get_collection_events),
    url(r'^add_activity_scehdule_appliance', add_activity_scehdule_appliance),
    # Added temporary url for e2e
    url(r'^add_activity_schedule_e2e', add_activity_schedule_e2e),
    url(r'^get_e2e_activity_data', get_e2e_activity_data),
    url(r'^delete_sleep_mode', delete_sleep_mode),
    url(r'^check_potential_conflicts', check_potential_conflicts),
    url(r'^fetch_next_available_time', fetch_next_available_time),
    url(r'^event_suggesstion', event_suggesstion),


    # url(r'^edit_entity', edit_entity),
]
