from a_common.models import CommonModel

from django.db import models


class SidoRegion(CommonModel):
    """시도 행정구역"""

    name = models.CharField(max_length=20, verbose_name="시도명")
    code = models.CharField(max_length=2, unique=True, verbose_name="시도 코드")

    class Meta:
        db_table = "regions_sido"
        verbose_name = "시도"
        verbose_name_plural = "시도 목록"


class SigunguRegion(CommonModel):
    """시군구 행정구역"""

    sido = models.ForeignKey(
        SidoRegion, on_delete=models.CASCADE, related_name="sigungus"
    )
    name = models.CharField(max_length=20, verbose_name="시군구명")
    code = models.CharField(max_length=5, unique=True, verbose_name="시군구 코드")

    class Meta:
        db_table = "regions_sigungu"
        verbose_name = "시군구"
        verbose_name_plural = "시군구 목록"


class EupmyeondongRegion(CommonModel):
    """읍면동 행정구역"""

    sigungu = models.ForeignKey(
        SigunguRegion, on_delete=models.CASCADE, related_name="eupmyeondongs"
    )
    name = models.CharField(max_length=20, verbose_name="읍면동명")
    code = models.CharField(max_length=10, unique=True, verbose_name="읍면동 코드")

    class Meta:
        db_table = "regions_eupmyeondong"
        verbose_name = "읍면동"
        verbose_name_plural = "읍면동 목록"


class UserActivityRegion(CommonModel):
    """사용자 활동지역"""

    user = models.ForeignKey(
        "a_user.User", on_delete=models.CASCADE, related_name="activity_regions"
    )
    eupmyeondong = models.ForeignKey(
        EupmyeondongRegion, on_delete=models.CASCADE, related_name="user_activities"
    )
    is_primary = models.BooleanField(default=False, verbose_name="주 활동지역 여부")
    verified_at = models.DateTimeField(auto_now_add=True, verbose_name="최초 인증 일시")
    last_verified_at = models.DateTimeField(
        auto_now=True, verbose_name="마지막 인증 일시"
    )

    class Meta:
        db_table = "user_activity_regions"
        verbose_name = "사용자 활동지역"
        verbose_name_plural = "사용자 활동지역 목록"
        unique_together = ["user", "eupmyeondong"]
