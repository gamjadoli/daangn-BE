from a_common.models import CommonModel

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("이메일은 필수 입력값입니다.")
        email = self.normalize_email(email)

        # username 필드가 없으면 email 값을 username으로 사용
        if "username" not in extra_fields:
            extra_fields["username"] = email

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
    rating_count = models.PositiveIntegerField(default=0, verbose_name="매너 평가 횟수")

    objects = UserManager()  # 커스텀 매니저 설정

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nickname", "phone_number"]

    class Meta:
        db_table = "users"
        verbose_name = "유저"
        verbose_name_plural = "유저 목록"

    def __str__(self):
        return f"{self.nickname} ({self.email})"

    def update_manner_temperature(self, rating_type):
        """매너온도 업데이트 메서드"""
        # 평가 유형에 따른 온도 변화
        temperature_changes = {
            # 긍정적 평가: 온도 상승
            "time": 0.2,  # 시간 약속을 잘 지켜요
            "response": 0.2,  # 응답이 빨라요
            "kind": 0.2,  # 친절하고 매너가 좋아요
            "accurate": 0.2,  # 상품 상태가 설명과 일치해요
            "negotiable": 0.2,  # 가격 제안에 대해 긍정적이에요
            # 부정적 평가: 온도 하락
            "bad_time": -0.5,  # 약속시간을 안 지켜요
            "bad_response": -0.5,  # 응답이 느려요
            "bad_manner": -0.5,  # 불친절해요
            "bad_accuracy": -0.5,  # 상품 상태가 설명과 달라요
            "bad_price": -0.5,  # 가격 흥정이 너무 심해요
        }

        # 기본 변화값 설정 (잘못된 평가 유형이 들어온 경우 0)
        change = temperature_changes.get(rating_type, 0)

        # 온도 범위는 0도 ~ 99.9도로 제한 (max_digits=3, decimal_places=1 제약조건을 고려)
        new_temperature = float(self.rating_score) + change
        new_temperature = max(0, min(99.9, new_temperature))

        # 업데이트 후 저장
        self.rating_score = new_temperature
        self.save(update_fields=["rating_score"])

        return new_temperature


class PriceOffer(CommonModel):
    """가격 제안 모델"""

    STATUS_CHOICES = (
        ("pending", "대기중"),
        ("accepted", "수락됨"),
        ("rejected", "거절됨"),
    )

    product = models.ForeignKey(
        "a_apis.Product",
        on_delete=models.CASCADE,
        related_name="price_offers",
        verbose_name="상품",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="price_offers",
        verbose_name="제안자",
    )
    price = models.PositiveIntegerField(verbose_name="제안 가격")
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="pending", verbose_name="상태"
    )
    chat_room = models.ForeignKey(
        "a_apis.ChatRoom",
        on_delete=models.CASCADE,
        related_name="price_offers",
        verbose_name="채팅방",
        null=True,
    )

    class Meta:
        db_table = "price_offers"
        verbose_name = "가격 제안"
        verbose_name_plural = "가격 제안 목록"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.nickname}의 {self.product.title}에 대한 가격 제안: {self.price}원"


class Review(CommonModel):
    """거래 후기 모델"""

    product = models.ForeignKey(
        "a_apis.Product",
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="상품",
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="written_reviews",
        verbose_name="작성자",
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_reviews",
        verbose_name="수신자",
    )
    content = models.TextField(verbose_name="후기 내용")

    class Meta:
        db_table = "reviews"
        verbose_name = "거래 후기"
        verbose_name_plural = "거래 후기 목록"
        ordering = ["-created_at"]
        # 한 상품에 대해 같은 사용자가 여러 후기를 남길 수 없도록 제한
        unique_together = ["product", "reviewer"]

    def __str__(self):
        return f"{self.reviewer.nickname}의 {self.product.title}에 대한 후기"


class MannerRating(CommonModel):
    """매너 평가 모델"""

    MANNER_TYPES = (
        ("time", "시간 약속을 잘 지켜요"),
        ("response", "응답이 빨라요"),
        ("kind", "친절하고 매너가 좋아요"),
        ("accurate", "상품 상태가 설명과 일치해요"),
        ("negotiable", "가격 제안에 대해 긍정적이에요"),
        ("bad_time", "약속시간을 안 지켜요"),
        ("bad_response", "응답이 느려요"),
        ("bad_manner", "불친절해요"),
        ("bad_accuracy", "상품 상태가 설명과 달라요"),
        ("bad_price", "가격 흥정이 너무 심해요"),
    )

    product = models.ForeignKey(
        "a_apis.Product",
        on_delete=models.CASCADE,
        related_name="manner_ratings",
        verbose_name="상품",
    )
    rater = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="given_ratings",
        verbose_name="평가자",
    )
    rated_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_ratings",
        verbose_name="피평가자",
    )
    rating_type = models.CharField(
        max_length=20, choices=MANNER_TYPES, verbose_name="평가 유형"
    )

    class Meta:
        db_table = "manner_ratings"
        verbose_name = "매너 평가"
        verbose_name_plural = "매너 평가 목록"
        ordering = ["-created_at"]
        # 한 거래에서 같은 유형의 평가는 한 번만 가능하도록 제한
        unique_together = ["product", "rater", "rating_type"]

    def __str__(self):
        return f"{self.rater.nickname}가 {self.rated_user.nickname}에게 준 평가: {self.get_rating_type_display()}"

    def save(self, *args, **kwargs):
        # 저장 시 피평가자의 매너온도 업데이트
        super().save(*args, **kwargs)
        self.rated_user.update_manner_temperature(self.rating_type)
