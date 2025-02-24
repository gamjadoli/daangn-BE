from a_user.models import User

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    list_display = (
        "id",
        "email",
        "nickname",
        "phone_number",
        "rating_score",
        "is_activated",
        "is_email_verified",
    )

    list_filter = (
        "is_activated",
        "is_email_verified",
        "is_staff",
        "created_at",
    )

    search_fields = (
        "email",
        "nickname",
        "phone_number",
    )

    ordering = ("-created_at",)

    fieldsets = (
        (
            "기본 정보",
            {
                "fields": (
                    "email",
                    "password",
                    "nickname",
                    "phone_number",
                )
            },
        ),
        (
            "프로필",
            {
                "fields": (
                    "profile_img",
                    "rating_score",
                )
            },
        ),
        (
            "상태",
            {
                "fields": (
                    "is_activated",
                    "is_email_verified",
                )
            },
        ),
        (
            "권한",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "중요 일자",
            {
                "fields": (
                    "last_login",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at")

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "nickname",
                    "phone_number",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
