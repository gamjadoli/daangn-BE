from a_common.models import CommonModel

from django.contrib.gis.db import models  # GeoDjango 모델 임포트


class SidoRegion(CommonModel):
    """시도 행정구역"""

    name = models.CharField(max_length=20, verbose_name="시도명")
    code = models.CharField(max_length=2, unique=True, verbose_name="시도 코드")
    # 행정구역 경계 필드 - 다각형 형태로 시도의 경계를 저장
    # 예: 서울시의 외곽 경계선, 경기도의 경계선 등
    geometry = models.MultiPolygonField(
        srid=4326,
        null=True,
        verbose_name="행정구역 경계",
        help_text="시도 행정구역의 경계 좌표",
    )

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

    # 읍면동 영역을 표현하는 다각형 좌표들
    region_polygon = models.MultiPolygonField(
        srid=4326,
        null=True,
        verbose_name="읍면동 영역",
        help_text="행정구역의 경계를 이루는 다각형 좌표들",
    )

    # 읍면동의 중심 좌표
    center_coordinates = models.PointField(
        srid=4326,
        null=True,
        verbose_name="중심 좌표",
        help_text="행정구역의 중심점 좌표",
    )

    class Meta:
        db_table = "regions_eupmyeondong"
        verbose_name = "읍면동"
        verbose_name_plural = "읍면동 목록"


class UserActivityRegion(CommonModel):
    """사용자 활동지역"""

    user = models.ForeignKey(
        "a_user.User", on_delete=models.CASCADE, related_name="activity_regions"
    )
    activity_area = models.ForeignKey(
        EupmyeondongRegion,
        on_delete=models.CASCADE,
        related_name="user_activities",
        verbose_name="활동지역",
    )
    priority = models.IntegerField(
        default=1,
        verbose_name="동네 순서",
        help_text="1: 대표 동네, 2: 두번째 동네, 3: 세번째 동네",
    )
    verified_at = models.DateTimeField(auto_now_add=True, verbose_name="최초 인증 일시")
    last_verified_at = models.DateTimeField(
        auto_now=True, verbose_name="마지막 인증 일시"
    )
    location = models.PointField(srid=4326, null=True, verbose_name="인증 위치")

    class Meta:
        db_table = "user_activity_regions"
        verbose_name = "사용자 활동지역"
        verbose_name_plural = "사용자 활동지역 목록"
        unique_together = ["user", "activity_area"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "priority"], name="unique_user_priority"
            )
        ]
