from django.conf.urls import url
from ioa.caretaker.views import *
urlpatterns = [

    url(r'^add_caretaker/', UserViews.as_view()),
    url(r'^update_caretaker/', UserViews.as_view()),
    url(r'^login_caretaker/', CaretakerLogin.as_view()),
    url(r'^get_staff_list/', get_staff_list),  ##OK {customer, days}
    url(r'^get_staff_dropdown/', get_staff_dropdown),  ##OK {customer, days}
    url(r'^get_staff_roles/', get_staff_roles),
]