from a_common.models import CommonModel

from django.contrib.auth import get_user_model
from django.contrib.gis.db import models  # PostGIS 필드 사용
from django.utils import timezone

User = get_user_model()


class ProductCategory(CommonModel):
    """상품 카테고리 모델"""

    name = models.CharField(max_length=50, verbose_name="카테고리명")
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="상위 카테고리",
    )
    order = models.PositiveIntegerField(default=0, verbose_name="정렬 순서")

    class Meta:
        db_table = "product_categories"
        verbose_name = "상품 카테고리"
        verbose_name_plural = "상품 카테고리 목록"
        ordering = ["order", "name"]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


class Product(CommonModel):
    class TradeType(models.TextChoices):
        SALE = "sale", "판매하기"
        SHARE = "share", "나눔하기"

    class Status(models.TextChoices):
        SELLING = "selling", "판매중"
        RESERVED = "reserved", "예약중"
        SOLDOUT = "soldout", "판매완료"

    class TradeCompleteStatus(models.TextChoices):
        """거래 완료 프로세스 상태"""

        NOT_COMPLETED = "not_completed", "거래 완료되지 않음"
        COMPLETED = "completed", "거래 완료됨"
        REVIEWED = "reviewed", "후기 작성 완료"
        RATED = "rated", "매너 평가 완료"

    user = models.ForeignKey(
        "a_user.User",  # 문자열로 User 모델 참조
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name="판매자",
    )
    region = models.ForeignKey(
        "a_apis.EupmyeondongRegion",
        on_delete=models.SET_NULL,
        null=True,
        related_name="products",
        verbose_name="등록 동네",
    )
    buyer = models.ForeignKey(
        "a_user.User",  # 구매자 정보
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="purchased_products",
        verbose_name="구매자",
    )
    title = models.CharField(max_length=100, verbose_name="상품 제목")
    trade_type = models.CharField(
        max_length=10,
        choices=TradeType.choices,
        default=TradeType.SALE,  # 기본값 지정
        verbose_name="거래 방식",
    )
    price = models.PositiveIntegerField(null=True, blank=True, verbose_name="판매 금액")
    final_price = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="최종 거래 금액"
    )
    accept_price_offer = models.BooleanField(
        default=False, verbose_name="가격 제안 허용"
    )
    description = models.TextField(verbose_name="상품 설명")
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        verbose_name="상품 카테고리",
    )
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
        default=Status.SELLING,
        verbose_name="상품 상태",
    )
    trade_complete_status = models.CharField(
        max_length=20,
        choices=TradeCompleteStatus.choices,
        default=TradeCompleteStatus.NOT_COMPLETED,
        verbose_name="거래 완료 프로세스 상태",
    )
    completed_at = models.DateTimeField(
        null=True, blank=True, verbose_name="거래 완료 시간"
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

    def mark_as_completed(self, buyer, final_price=None):
        """거래 완료 처리 메서드"""
        import logging

        logger = logging.getLogger("product_debug")

        try:
            logger.error(
                f"[mark_as_completed] 시작 - product_id: {self.id}, buyer: {buyer}, final_price: {final_price}"
            )

            self.status = self.Status.SOLDOUT
            self.buyer = buyer
            self.final_price = final_price if final_price else self.price
            self.completed_at = models.timezone.now()
            self.trade_complete_status = self.TradeCompleteStatus.COMPLETED

            logger.error(
                f"[mark_as_completed] 저장 전 - status: {self.status}, buyer_id: {self.buyer.id if self.buyer else None}"
            )

            self.save(
                update_fields=[
                    "status",
                    "buyer",
                    "final_price",
                    "completed_at",
                    "trade_complete_status",
                    "updated_at",
                ]
            )

            logger.error(f"[mark_as_completed] 성공 - product_id: {self.id}")
            return True
        except Exception as e:
            logger.error(
                f"[mark_as_completed] 오류 발생 - product_id: {self.id}, error: {str(e)}"
            )
            return False


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
        return f"{self.product.title} 이미지"  # name을 title로 변경


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
