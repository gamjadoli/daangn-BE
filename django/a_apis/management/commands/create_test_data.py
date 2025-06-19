import random
from datetime import datetime, timedelta

from a_apis.models.product import Product
from a_apis.models.region import EupmyeondongRegion
from a_user.models import MannerRating, Review, User

from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Create test data for user profile API testing"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Creating test data..."))

        # 기존 사용자 가져오기 (ID: 2, 지돌이)
        try:
            user = User.objects.get(id=2)
            self.stdout.write(f"Found user: {user.nickname}")
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("User with ID 2 not found"))
            return

        # 기본 지역 가져오기
        try:
            region = EupmyeondongRegion.objects.first()
            if not region:
                self.stdout.write(self.style.ERROR("No regions found"))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error getting region: {e}"))
            return

        # 다른 테스트 사용자들 생성
        test_users = []
        for i in range(3):
            try:
                test_user, created = User.objects.get_or_create(
                    email=f"testuser{i+1}@example.com",
                    defaults={
                        "username": f"testuser{i+1}@example.com",
                        "nickname": f"테스터{i+1}",
                        "phone_number": f"010123456{i+1:02d}",
                        "is_email_verified": True,
                    },
                )
                if created:
                    test_user.set_password("testpass123")
                    test_user.save()
                test_users.append(test_user)
                self.stdout.write(f"Created/found test user: {test_user.nickname}")
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error creating test user {i+1}: {e}")
                )

        # 1. 판매 상품 생성 (지돌이가 판매자)
        products = []
        for i in range(3):
            try:
                product = Product.objects.create(
                    user=user,
                    region=region,
                    title=f"테스트 상품 {i+1}",
                    description=f"테스트 상품 {i+1} 설명입니다.",
                    price=10000 + (i * 5000),
                    trade_type="sale",
                    status=(
                        "selling" if i == 0 else "soldout"
                    ),  # 첫번째는 판매중, 나머지는 판매완료
                    buyer=test_users[i % len(test_users)] if i > 0 else None,
                    completed_at=(
                        timezone.now() - timedelta(days=i * 10) if i > 0 else None
                    ),
                )
                products.append(product)
                self.stdout.write(f"Created product: {product.title}")
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error creating product {i+1}: {e}")
                )

        # 2. 거래후기 생성 (지돌이가 받는 후기)
        reviews_data = [
            {
                "reviewer": test_users[0],
                "content": "정말 친절하고 좋은 거래였습니다! 상품 상태도 설명과 일치했어요.",
                "days_ago": 5,
            },
            {
                "reviewer": test_users[1],
                "content": "빠른 응답과 시간 약속을 잘 지켜주셔서 감사했습니다.",
                "days_ago": 15,
            },
            {
                "reviewer": test_users[2],
                "content": "매너 좋은 판매자입니다. 추천해요!",
                "days_ago": 25,
            },
        ]

        for i, review_data in enumerate(reviews_data):
            if i < len(products) - 1:  # 판매완료된 상품에만 후기 작성
                try:
                    review = Review.objects.create(
                        product=products[i + 1],
                        reviewer=review_data["reviewer"],
                        receiver=user,
                        content=review_data["content"],
                    )
                    # 생성 시간 조정
                    review.created_at = timezone.now() - timedelta(
                        days=review_data["days_ago"]
                    )
                    review.save()
                    self.stdout.write(
                        f'Created review from {review_data["reviewer"].nickname}'
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error creating review {i+1}: {e}")
                    )

        # 3. 매너평가 생성 (지돌이가 받는 평가)
        manner_ratings_data = [
            # 긍정적 평가들
            {"reviewer": test_users[0], "rating_type": "time", "product_idx": 1},
            {"reviewer": test_users[0], "rating_type": "kind", "product_idx": 1},
            {"reviewer": test_users[1], "rating_type": "response", "product_idx": 2},
            {"reviewer": test_users[1], "rating_type": "accurate", "product_idx": 2},
            {"reviewer": test_users[2], "rating_type": "time", "product_idx": 1},
            {"reviewer": test_users[2], "rating_type": "kind", "product_idx": 1},
            # 부정적 평가 1개
            {
                "reviewer": test_users[0],
                "rating_type": "bad_response",
                "product_idx": 2,
            },
        ]

        for rating_data in manner_ratings_data:
            try:
                if rating_data["product_idx"] < len(products):
                    product = products[rating_data["product_idx"]]
                    if product.status == "soldout":  # 판매완료된 상품에만 매너평가
                        manner_rating = MannerRating.objects.create(
                            product=product,
                            rater=rating_data["reviewer"],
                            rated_user=user,
                            rating_type=rating_data["rating_type"],
                        )
                        self.stdout.write(
                            f'Created manner rating: {rating_data["rating_type"]} from {rating_data["reviewer"].nickname}'
                        )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error creating manner rating: {e}")
                )

        self.stdout.write(self.style.SUCCESS("Test data creation completed!"))
        self.stdout.write(f"Summary:")
        self.stdout.write(f"- User: {user.nickname} (ID: {user.id})")
        self.stdout.write(f"- Products created: {len(products)}")
        self.stdout.write(f"- Reviews: {Review.objects.filter(receiver=user).count()}")
        self.stdout.write(
            f"- Manner ratings: {MannerRating.objects.filter(rated_user=user).count()}"
        )
