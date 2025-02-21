import random
from datetime import timedelta

from a_common.models import CommonModel

from django.db import models
from django.utils import timezone


class EmailVerification(CommonModel):
    email = models.EmailField()
    verification_code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"{self.email} - {'Verified' if self.is_verified else 'Not Verified'}"

    def save(self, *args, **kwargs):
        if not self.pk:  # Only set expires_at when creating new object
            self.verification_code = str(random.randint(100000, 999999))
            self.expires_at = timezone.now() + timedelta(minutes=30)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
