from a_apis.models.files import File
from a_common.models import CommonModel

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("이메일은 필수 입력값입니다.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("nickname", "admin")  # 기본 닉네임 설정
        extra_fields.setdefault("phone_number", "00000000000")  # 기본 전화번호 설정

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser, CommonModel):
    email = models.EmailField(unique=True, verbose_name="이메일")
    nickname = models.CharField(
        max_length=12, unique=True, verbose_name="닉네임"  # nickname은 unique해야 함
    )
    phone_number = models.CharField(max_length=11, verbose_name="휴대폰 번호")
    rating_score = models.DecimalField(
        max_digits=3, decimal_places=1, default=36.5, verbose_name="매너온도"
    )
    profile_img = models.ForeignKey(
        "a_apis.File",  # 문자열로 모델 참조
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_profile",
        verbose_name="프로필 이미지",
    )
    is_activated = models.BooleanField(default=True, verbose_name="계정 활성화 여부")
    is_email_verified = models.BooleanField(
        default=False, verbose_name="이메일 인증 여부"
    )

    objects = UserManager()  # 커스텀 매니저 설정

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nickname", "phone_number"]

    class Meta:
        db_table = "users"
        verbose_name = "유저"
        verbose_name_plural = "유저 목록"

    def __str__(self):
        return f"{self.nickname} ({self.email})"
