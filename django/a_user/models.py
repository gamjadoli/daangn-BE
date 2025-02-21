from a_common.models import CommonModel

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser, CommonModel):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)
    is_social_login = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "users"
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return self.email


class SocialUser(CommonModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="social_users"
    )
    social_id = models.CharField(max_length=255)
    social_type = models.CharField(max_length=255)

    class Meta:
        db_table = "social_users"
        verbose_name = "social user"
        verbose_name_plural = "social users"
        unique_together = ["user", "social_type"]

    def __str__(self):
        return f"{self.user.email} - {self.social_type}"
