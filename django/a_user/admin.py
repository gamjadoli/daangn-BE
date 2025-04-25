from a_user.models import User

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "nickname", "phone_number")

    def save(self, commit=True):
        user = super().save(commit=False)
        # username 필드를 이메일 값으로 자동 설정
        user.username = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    # 커스텀 생성 폼 사용
    add_form = CustomUserCreationForm

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

    def save_model(self, request, obj, form, change):
        # 사용자 생성 또는 수정 시 username 필드를 이메일로 설정
        if not change:  # 새 사용자를 생성할 때만
            obj.username = obj.email
        super().save_model(request, obj, form, change)
