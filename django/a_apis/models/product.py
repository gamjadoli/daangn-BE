from a_common.models import CommonModel

from django.contrib.gis.db import models  # PostGIS 필드 사용


class Product(CommonModel):
    class TradeType(models.TextChoices):
        SALE = "sale", "판매하기"
        SHARE = "share", "나눔하기"

    class Status(models.TextChoices):
        NEW = "new", "판매중"
        RESERVED = "reserved", "예약중"
        SOLDOUT = "soldout", "판매완료"

    user = models.ForeignKey(
        "a_user.User",  # 문자열로 User 모델 참조
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name="판매자",
    )
    title = models.CharField(max_length=100, verbose_name="상품 제목")
    trade_type = models.CharField(
        max_length=10,
        choices=TradeType.choices,
        default=TradeType.SALE,  # 기본값 지정
        verbose_name="거래 방식",
    )
    price = models.PositiveIntegerField(null=True, blank=True, verbose_name="판매 금액")
    accept_price_offer = models.BooleanField(
        default=False, verbose_name="가격 제안 허용"
    )
    description = models.TextField(verbose_name="상품 설명")
    meeting_location = models.PointField(
        srid=4326, null=True, verbose_name="거래 희망 위치"
    )
    location_description = models.CharField(
        max_length=200,
        verbose_name="거래 위치 설명",
        null=True,  # null 허용
        blank=True,  # 폼에서 빈값 허용
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.NEW,
        verbose_name="상품 상태",
    )
    view_count = models.PositiveIntegerField(default=0, verbose_name="조회수")
    refresh_at = models.DateTimeField(
        null=True, blank=True, verbose_name="끌어올린 시간"
    )

    class Meta:
        db_table = "products"
        verbose_name = "상품"
        verbose_name_plural = "상품 목록"
        ordering = ["-refresh_at", "-created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class ProductImage(CommonModel):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images", verbose_name="상품"
    )
    file = models.ForeignKey(
        "a_apis.File",  # 직접 임포트 대신 문자열 참조로 변경
        on_delete=models.CASCADE,
        related_name="product_images",
        verbose_name="이미지 파일",
    )

    class Meta:
        db_table = "product_images"
        verbose_name = "상품 이미지"
        verbose_name_plural = "상품 이미지 목록"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.product.name} 이미지"


class InterestProduct(CommonModel):
    """관심 상품"""

    user = models.ForeignKey(
        "a_user.User",
        on_delete=models.CASCADE,
        related_name="interest_products",
        verbose_name="사용자",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="interested_users",
        verbose_name="관심 상품",
    )

    class Meta:
        db_table = "interest_products"
        verbose_name = "관심 상품"
        verbose_name_plural = "관심 상품 목록"
        unique_together = [
            "user",
            "product",
        ]  # 한 사용자가 같은 상품을 중복으로 관심등록 못하도록
        ordering = ["-created_at"]  # 최근 관심등록 순으로 정렬

    def __str__(self):
        return f"{self.user.email} - {self.product.title}"
