from django.contrib import admin
from .models import UserProfile, EmailOTP


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "phone",
        "city",
        "pincode",
        "created_at"
    )

    search_fields = (
        "user__email",
        "phone",
        "city"
    )

    list_filter = (
        "city",
        "created_at"
    )


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):

    list_display = (
        "email",
        "otp",
        "created_at"
    )