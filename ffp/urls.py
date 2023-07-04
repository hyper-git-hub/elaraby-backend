from django.conf.urls import url, include

from ffp.task_views import add_tasks, employee_dropdown, get_tasks, edit_tasks, delete_tasks, zone_dropdown, \
    assigned_zone_dropdown, get_task_rate, update_task_status, get_productivity_percentage
from ffp.views import get_assets_count, get_sites_listing_dashboard, \
    get_site_details, get_zone_details, employee_subordinates, violations_dashboard, site_zone_dropdown, \
    performance_analysis, employee_durations, graph_data_productivity, get_ranked_sites, zones_of_site

urlpatterns = [

    url(r'^get_assets_count', get_assets_count),
    url(r'^get_sites_listing_dashboard', get_sites_listing_dashboard),
    url(r'^get_site_details', get_site_details),
    url(r'^get_zone_details', get_zone_details),
    url(r'^get_ranked_sites', get_ranked_sites),

    #FIXME
    # url(r'^get_employee_dashboard', None),


    url(r'^add_tasks', add_tasks),
    url(r'^edit_tasks', edit_tasks),
    url(r'^delete_tasks', delete_tasks),
    url(r'^update_task_status', update_task_status),
    url(r'^get_tasks', get_tasks),

    url(r'^employee_dropdown', employee_dropdown),
    url(r'^zone_dropdown', zone_dropdown),
    url(r'^assigned_zone_dropdown', assigned_zone_dropdown),
    url(r'^get_task_rate', get_task_rate),
    url(r'^get_productivity_percentage', get_productivity_percentage),
    url(r'^employee_subordinates', employee_subordinates),


    #FIXME DUMMY DATA API
    # url(r'^post_data_ffp_dummy', post_data_ffp_dummy),
    url(r'^violations_dashboard', violations_dashboard),
    url(r'^site_zone_dropdown', site_zone_dropdown),
    url(r'^performance_analysis', performance_analysis),
    url(r'^employee_durations', employee_durations),
    url(r'^graph_data_productivity', graph_data_productivity),
    url(r'^zones_of_site', zones_of_site),


]
