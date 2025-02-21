from a_user.models import User

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


class CustomUserAdmin(BaseUserAdmin):
    list_display = (
        "id",
        "username",
        "email",
        "phone_number",
        "is_email_verified",
        "is_social_login",
    )

    search_fields = ("username", "email", "phone_number", "is_social_login")
    ordering = ("id",)


# 커스텀 UserAdmin
admin.site.register(User, CustomUserAdmin)
