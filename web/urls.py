from django.urls import path
from . import views

urlpatterns = [

    path("", views.home, name="home"),

    path("auth/", views.auth_page, name="auth"),

    path("send-otp/", views.send_signup_otp, name="send_otp"),

    path("verify-otp/", views.verify_signup_otp, name="verify_otp"),

    path("login-user/", views.login_user, name="login_user"),

    path("save-details/", views.save_details, name="save_details"),

    path("get-location/", views.get_location_by_pincode, name="get_location"),

    path(
    "reverse-geocode/",
    views.reverse_geocode,
    name="reverse_geocode"
),

path(
    "resend-otp/",
    views.resend_otp,
    name="resend_otp"
),

path(
    "profile/",
    views.profile,
    name="profile"
),

path(
    "logout/",
    views.logout_user,
    name="logout_user"
),
]