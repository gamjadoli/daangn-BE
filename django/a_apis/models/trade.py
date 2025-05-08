from a_common.models import CommonModel

from django.contrib.gis.db import models
from django.utils import timezone


class PriceOffer(CommonModel):
    """가격 제안 모델"""

    class Status(models.TextChoices):
        PENDING = "pending", "대기중"
        ACCEPTED = "accepted", "수락됨"
        REJECTED = "rejected", "거절됨"

    product = models.ForeignKey(
        "a_apis.Product",
        on_delete=models.CASCADE,
        related_name="apis_price_offers",
        verbose_name="상품",
    )
    user = models.ForeignKey(
        "a_user.User",
        on_delete=models.CASCADE,
        related_name="apis_price_offers",
        verbose_name="제안자",
    )
    price = models.PositiveIntegerField(verbose_name="제안 가격")
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="상태",
    )
    chat_room = models.ForeignKey(
        "a_apis.ChatRoom",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="apis_price_offers",
        verbose_name="채팅방",
    )
    responded_at = models.DateTimeField(null=True, blank=True, verbose_name="응답 일시")

    class Meta:
        db_table = "apis_price_offers"
        verbose_name = "가격 제안"
        verbose_name_plural = "가격 제안 목록"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product.title} - {self.price}원 ({self.get_status_display()})"

    def accept(self):
        """가격 제안 수락"""
        self.status = self.Status.ACCEPTED
        self.responded_at = timezone.now()
        self.save()
        return self

    def reject(self):
        """가격 제안 거절"""
        self.status = self.Status.REJECTED
        self.responded_at = timezone.now()
        self.save()
        return self


class Trade(CommonModel):
    """거래 완료 모델"""

    product = models.OneToOneField(
        "a_apis.Product",
        on_delete=models.CASCADE,
        related_name="trade",
        verbose_name="상품",
    )
    seller = models.ForeignKey(
        "a_user.User",
        on_delete=models.CASCADE,
        related_name="sold_trades",
        verbose_name="판매자",
    )
    buyer = models.ForeignKey(
        "a_user.User",
        on_delete=models.CASCADE,
        related_name="bought_trades",
        verbose_name="구매자",
    )
    final_price = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="최종 거래 가격"
    )
    reviewed_by_seller = models.BooleanField(
        default=False, verbose_name="판매자 리뷰 작성 여부"
    )
    reviewed_by_buyer = models.BooleanField(
        default=False, verbose_name="구매자 리뷰 작성 여부"
    )
    seller_manner_rated = models.BooleanField(
        default=False, verbose_name="판매자 매너 평가 작성 여부"
    )
    buyer_manner_rated = models.BooleanField(
        default=False, verbose_name="구매자 매너 평가 작성 여부"
    )

    class Meta:
        db_table = "trades"
        verbose_name = "거래"
        verbose_name_plural = "거래 목록"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product.title} ({self.seller.nickname} → {self.buyer.nickname})"


class TradeReview(CommonModel):
    """거래 후기 모델"""

    trade = models.ForeignKey(
        Trade,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="거래",
    )
    writer = models.ForeignKey(
        "a_user.User",
        on_delete=models.CASCADE,
        related_name="apis_written_reviews",
        verbose_name="작성자",
    )
    receiver = models.ForeignKey(
        "a_user.User",
        on_delete=models.CASCADE,
        related_name="apis_received_reviews",
        verbose_name="대상자",
    )
    content = models.TextField(verbose_name="내용")

    class Meta:
        db_table = "apis_trade_reviews"
        verbose_name = "거래 후기"
        verbose_name_plural = "거래 후기 목록"
        ordering = ["-created_at"]
        unique_together = [("trade", "writer")]  # 거래당 한 명이 한 번만 작성 가능

    def __str__(self):
        return f"{self.trade.product.title} - {self.writer.nickname}의 후기"


class MannerRatingType(CommonModel):
    """매너 평가 유형 모델"""

    name = models.CharField(max_length=100, verbose_name="평가명")
    is_positive = models.BooleanField(default=True, verbose_name="긍정 평가 여부")
    score_delta = models.FloatField(default=0.1, verbose_name="점수 변화량")

    class Meta:
        db_table = "manner_rating_types"
        verbose_name = "매너 평가 유형"
        verbose_name_plural = "매너 평가 유형 목록"
        ordering = ["-is_positive", "name"]

    def __str__(self):
        prefix = "😊" if self.is_positive else "😞"
        return f"{prefix} {self.name}"


class MannerRating(CommonModel):
    """매너 평가 모델"""

    class RatingType(models.TextChoices):
        POSITIVE = "positive", "긍정적"
        NEGATIVE = "negative", "부정적"

    trade = models.ForeignKey(
        Trade,
        on_delete=models.CASCADE,
        related_name="manner_ratings",
        verbose_name="거래",
    )
    rater = models.ForeignKey(
        "a_user.User",
        on_delete=models.CASCADE,
        related_name="apis_given_ratings",
        verbose_name="평가자",
    )
    rated_user = models.ForeignKey(
        "a_user.User",
        on_delete=models.CASCADE,
        related_name="apis_received_ratings",
        verbose_name="평가 대상자",
    )
    rating_type = models.CharField(
        max_length=10,
        choices=RatingType.choices,
        verbose_name="평가 유형",
    )
    tags = models.JSONField(default=list, verbose_name="평가 태그")
    comment = models.TextField(blank=True, null=True, verbose_name="추가 코멘트")

    class Meta:
        db_table = "apis_manner_ratings"
        verbose_name = "매너 평가"
        verbose_name_plural = "매너 평가 목록"
        ordering = ["-created_at"]
        unique_together = [
            ("trade", "rater", "rated_user")
        ]  # 거래당 한 명이 한 명에게 한 번만 평가 가능

    def __str__(self):
        return f"{self.rater.nickname}의 {self.rated_user.nickname}에 대한 평가"

    def save(self, *args, **kwargs):
        # 새로 생성되는 경우(id가 없는 경우) 매너온도 업데이트
        is_new = self.id is None
        super().save(*args, **kwargs)

        if is_new:
            from a_apis.service.users import UserService

            # 매너온도 업데이트 (긍정적이면 +0.5, 부정적이면 -0.5)
            change = 0.5 if self.rating_type == self.RatingType.POSITIVE else -0.5
            UserService.update_manner_temperature(self.rated_user.id, change)


class TradeAppointment(CommonModel):
    """거래약속 모델"""

    class Status(models.TextChoices):
        PENDING = "pending", "대기중"
        CONFIRMED = "confirmed", "확정됨"
        CANCELED = "canceled", "취소됨"
        COMPLETED = "completed", "완료됨"

    product = models.ForeignKey(
        "a_apis.Product",
        on_delete=models.CASCADE,
        related_name="appointments",
        verbose_name="상품",
    )
    seller = models.ForeignKey(
        "a_user.User",
        on_delete=models.CASCADE,
        related_name="seller_appointments",
        verbose_name="판매자",
    )
    buyer = models.ForeignKey(
        "a_user.User",
        on_delete=models.CASCADE,
        related_name="buyer_appointments",
        verbose_name="구매자",
    )
    appointment_date = models.DateTimeField(verbose_name="약속 날짜 및 시간")
    location = models.PointField(srid=4326, verbose_name="약속 장소")
    location_description = models.CharField(
        max_length=200, verbose_name="약속 장소 설명"
    )
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="약속 상태",
    )
    chat_room = models.ForeignKey(
        "a_apis.ChatRoom",
        on_delete=models.CASCADE,
        related_name="appointments",
        verbose_name="채팅방",
    )

    class Meta:
        db_table = "trade_appointments"
        verbose_name = "거래 약속"
        verbose_name_plural = "거래 약속 목록"
        ordering = ["-appointment_date"]

    def __str__(self):
        return f"{self.product.title} - {self.appointment_date.strftime('%Y-%m-%d %H:%M')} ({self.get_status_display()})"

    def confirm(self):
        """약속 확정 처리"""
        self.status = self.Status.CONFIRMED
        self.save(update_fields=["status", "updated_at"])
        return self

    def cancel(self):
        """약속 취소 처리"""
        self.status = self.Status.CANCELED
        self.save(update_fields=["status", "updated_at"])
        return self

    def complete(self):
        """약속 완료 처리"""
        self.status = self.Status.COMPLETED
        self.save(update_fields=["status", "updated_at"])
        return self
