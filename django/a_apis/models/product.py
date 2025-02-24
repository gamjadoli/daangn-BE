from a_apis.models.files import File
from a_common.models import CommonModel

from django.db import models


class Product(CommonModel):
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
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.NEW,
        verbose_name="상품 상태",
    )
    price = models.PositiveIntegerField(verbose_name="판매 금액")
    view_count = models.PositiveIntegerField(default=0, verbose_name="조회수")
    description = models.TextField(verbose_name="상품 설명")
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
        File,
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
