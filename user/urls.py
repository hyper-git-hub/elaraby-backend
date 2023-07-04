from django.conf.urls import url
from django.contrib import admin

from user.views import get_user_profile, modify_user_details, regenerate_reset_token, verfiy_user_token, \
    reset_user_password_token, user_sign_up_invitation_manager, users_details_list
from . import views

urlpatterns = [
    url(r'^login/$', views.UserLoginAPIView.as_view(), name='login'),
    url(r'^password_reset_request/$', views.UserPasswordResetRequest.as_view(), name='password_reset_angular'),
    url(r'^reset_token_verify/$', views.UserResetTokenVerify.as_view()),
    url(r'^change_password/$', views.UserChangePassword.as_view()),
    url(r'^register/$', views.UserCreateAPIView.as_view(), name='register'),
    url(r'^team/$', views.UsersAPIView.as_view(), name='users'),
    url(r'^team/(?P<user_id>\d+)/$', views.UserAPIView.as_view(), name='user'),

    url(r'^get_user_profile', get_user_profile),
    url(r'^modify_user_details', modify_user_details),
    url(r'^regenerate_reset_token', regenerate_reset_token),
    url(r'^verfiy_user_token', verfiy_user_token),
    url(r'^reset_user_password_token', reset_user_password_token),
    url(r'^user_sign_up_invitation_manager', user_sign_up_invitation_manager),
    url(r'^users_details_list', users_details_list),
]
