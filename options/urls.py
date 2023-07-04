from options.views import OptionsAll
from options.views import OptionsKeys
from django.conf.urls import url
from django.contrib import admin


urlpatterns = [
    url(r'^get_values/',OptionsAll.as_view()),
    url(r'^get_keys/',OptionsKeys.as_view()),
            ]