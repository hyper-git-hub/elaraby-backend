from django.conf.urls import url
from ioa.activity.views import *
urlpatterns = [

    url(r'^schedule_activity/', SchedulingActivityView.as_view()),
    url(r'^get_activity/', ActivityListView.as_view()),
    url(r'^get_group_activities/', ActivityListView.as_view()),
    url(r'^perform_activity/', ActivityListView.as_view()),
    url(r'^get_activity_groups/', GroupActivities.as_view()),

    url(r'^get_activity/(?P<pk>[0-9]+)/$', get_activity),
    url(r'^delete_activity/(?P<pk>[0-9]+)/$', ScheduleAnActivity.as_view()),
    url(r'^update_activity/(?P<pk>[0-9]+)/$', ScheduleAnActivity.as_view()),

    # Function Based Views
    url(r'^get_activity_list/', get_activity_details_list),  ##OK {customer, days}
    url(r'^get_activity_graph_statistics/', ActivityGraphStatistics.as_view()),  ##OK {activity_type, days}
    url(r'^get_activities_status/', GroupActivitiesCount.as_view()),  ##OK
    url(r'^get_activity_statistics/', GetActivitiesStatistics.as_view()),  ##OK
    url(r'^get_milking_feeding_value_total/', get_milking_feeding_value_total),  ##OK {activity_type, days}
    url(r'^last_week_max_milk_yield/', last_week_max_milk_yield),  ##OK {customer}
    url(r'^last_week_feed_consumed/', last_week_feed_consumed),  ##OK {customer}
    url(r'^get_expected_milk_yield/', get_expected_milk_yield),  ##OK NONE REQUIRED DUMMY DATA
    url(r'^get_milking_values/', get_milking_values),  ##OK {customer, days}
    url(r'^get_feeding_value_today/', get_feeding_value_today),  ##OK {customer, days}

    url(r'^schedule_data_cron_job/', get_aggregations),  ##OK
]