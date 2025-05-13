from datetime import datetime

from a_apis.auth.cookies import create_auth_response
from a_apis.models import EmailVerification
from a_apis.models.region import (
    EupmyeondongRegion,
    SidoRegion,
    SigunguRegion,
    UserActivityRegion,
)
from allauth.account.models import EmailAddress
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.gis.geos import Point
from django.db import transaction

User = get_user_model()


class UserService:
    @staticmethod
    def signup(data: dict):
        """회원가입 서비스

        Args:
            data: SignupSchema 데이터
                - email: 이메일
                - password: 비밀번호
                - nickname: 닉네임
                - phone_number: 전화번호
                - latitude: 위도 (위치 인증 좌표)
                - longitude: 경도 (위치 인증 좌표)
        """
        try:
            # 이메일 중복 체크
            if User.objects.filter(email=data.email).exists():
                return {
                    "success": False,
                    "message": "이미 가입된 이메일입니다.",
                    "data": None,
                    "tokens": None,
                }

            # 이메일 인증 여부 확인
            email_verification = EmailVerification.objects.filter(
                email=data.email, is_verified=True
            ).first()

            if not email_verification:
                return {
                    "success": False,
                    "message": "이메일 인증이 필요합니다.",
                    "data": None,
                    "tokens": None,
                }

            # 사용자 생성
            user = User.objects.create_user(
                username=data.email,
                email=data.email,
                password=data.password,
                nickname=data.nickname,
                phone_number=data.phone_number,
                is_email_verified=True,  # 이메일 인증 완료 상태로 설정
            )

            # 위치 정보가 제공된 경우 활동지역 등록
            if hasattr(data, "latitude") and hasattr(data, "longitude"):
                try:
                    # 위도/경도로 지역 정보 조회하여 활동지역 등록
                    from a_apis.service.region import SGISService

                    sgis = SGISService()
                    region_info = sgis.get_region_info(data.latitude, data.longitude)
                    eupmyeondong_code = region_info["adm_cd"]

                    # 좌표 및 버전 정보 생성
                    user_location = Point(data.longitude, data.latitude, srid=4326)

                    # 시도, 시군구, 읍면동 정보 조회 또는 생성
                    sido, _ = SidoRegion.objects.get_or_create(
                        code=region_info["sido_cd"],
                        defaults={"name": region_info["sido_nm"]},
                    )

                    sigungu, _ = SigunguRegion.objects.get_or_create(
                        code=region_info["sgg_cd"],
                        sido=sido,
                        defaults={"name": region_info["sgg_nm"]},
                    )

                    eupmyeondong, _ = EupmyeondongRegion.objects.get_or_create(
                        code=eupmyeondong_code,
                        sigungu=sigungu,
                        defaults={
                            "name": region_info["adm_nm"],
                            "center_coordinates": user_location,
                        },
                    )

                    # 사용자 활동지역 생성
                    UserActivityRegion.objects.create(
                        user=user,
                        activity_area=eupmyeondong,
                        priority=1,
                        location=user_location,
                    )
                except Exception as location_error:
                    # 위치 등록 실패는 회원가입 자체를 실패시키지 않음
                    print(f"위치 등록 실패: {str(location_error)}")

            # JWT 토큰 생성
            refresh = RefreshToken.for_user(user)

            return {
                "success": True,
                "message": "회원가입이 완료되었습니다.",
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
                "data": {  # user 필드를 data로 변경하여 일관성 유지
                    "id": user.id,
                    "email": user.email,
                    "nickname": user.nickname,
                },
            }
        except Exception as e:
            error_message = str(e)
            if "username" in error_message and "exists" in error_message:
                return {
                    "success": False,
                    "message": "이미 가입된 이메일입니다.",
                    "data": None,
                    "tokens": None,
                }
            return {
                "success": False,
                "message": f"회원가입 처리 중 오류가 발생했습니다: {str(e)}",
                "data": None,
                "tokens": None,
            }

    @staticmethod
    def login_user(request, data):
        """로그인 서비스

        Args:
            request: HTTP 요청 객체
            data: LoginSchema 데이터 (email, password 포함)
        """
        user = authenticate(request, username=data.email, password=data.password)
        if user:
            login(request, user)
            refresh = RefreshToken.for_user(user)

            # 사용자의 인증된 동네 목록 가져오기
            user_regions = []
            current_region = None

            user_activity_regions = (
                UserActivityRegion.objects.filter(user=user)
                .select_related("activity_area")
                .order_by("priority")
            )

            for user_region in user_activity_regions:
                region_data = {
                    "id": user_region.activity_area.id,
                    "name": user_region.activity_area.name,
                    "code": user_region.activity_area.code,
                    "priority": user_region.priority,
                }
                user_regions.append(region_data)

                # 우선순위가 1인 동네(대표 동네)를 현재 선택된 동네로 설정
                if user_region.priority == 1:
                    current_region = region_data

            # 응답 데이터 구성
            user_data = {
                "email": user.email,
                "nickname": user.nickname,
                "phone_number": user.phone_number,
                "is_activated": user.is_active,  # is_active 필드 사용
                "is_email_verified": user.is_email_verified,
                "rating_score": getattr(user, "rating_score", 36.5),  # 기본값 36.5
                "profile_img_url": (
                    user.profile_img.url
                    if hasattr(user, "profile_img") and user.profile_img
                    else None
                ),
                "regions": user_regions,
                "current_region": current_region,
            }

            return {
                "success": True,
                "message": "로그인 되었습니다.",
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
                "user": user_data,
            }
        return {"success": False, "message": "이메일 또는 비밀번호가 잘못되었습니다."}

    @staticmethod
    def refresh_token(refresh_token: str):
        try:
            refresh = RefreshToken(refresh_token)
            result = {
                "success": True,
                "message": "토큰이 갱신되었습니다.",
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
            }
            return create_auth_response(
                result, result["tokens"]["access"], result["tokens"]["refresh"]
            )
        except TokenError as e:
            return {"success": False, "message": "유효하지 않은 리프레시 토큰입니다."}

    @staticmethod
    def get_user(request):
        try:
            user = request.auth
            if not user:
                return {"success": False, "message": "인증되지 않은 사용자입니다."}

            from rest_framework_simplejwt.tokens import AccessToken

            access_token = AccessToken(user)
            user_id = access_token["user_id"]

            user = User.objects.get(id=user_id)

            # 사용자의 인증된 동네 목록 가져오기
            user_regions = []
            current_region = None

            user_activity_regions = (
                UserActivityRegion.objects.filter(user=user)
                .select_related("activity_area")
                .order_by("priority")
            )

            for user_region in user_activity_regions:
                region_data = {
                    "id": user_region.activity_area.id,
                    "name": user_region.activity_area.name,
                    "code": user_region.activity_area.code,
                    "priority": user_region.priority,
                }
                user_regions.append(region_data)

                # 우선순위가 1인 동네(대표 동네)를 현재 선택된 동네로 설정
                if user_region.priority == 1:
                    current_region = region_data

            # 응답 데이터 구성
            user_data = {
                "email": user.email,
                "nickname": user.nickname,
                "phone_number": user.phone_number,
                "is_activated": user.is_active,
                "is_email_verified": user.is_email_verified,
                "rating_score": getattr(user, "rating_score", 36.5),  # 기본값 36.5
                "profile_img_url": (
                    user.profile_img.url
                    if hasattr(user, "profile_img") and user.profile_img
                    else None
                ),
                "regions": user_regions,
                "current_region": current_region,
            }

            return {
                "success": True,
                "message": "인증된 사용자입니다.",
                "user": user_data,
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    @staticmethod
    def update_user_profile(request, data, profile_image=None):
        """회원정보 수정 서비스

        Args:
            request: HTTP 요청 객체
            data: UpdateProfileSchema 데이터 (nickname, phone_number 등)
            profile_image: 업로드된 프로필 이미지 파일 (옵션)

        Returns:
            dict: 처리 결과 메시지
        """
        try:
            # 인증된 사용자 확인 - request.auth(토큰) 또는 request.user(객체) 처리
            user_obj = None

            # request.user가 User 객체인 경우 (테스트용)
            if hasattr(request, "user") and isinstance(request.user, User):
                user_obj = request.user
            # request.auth가 토큰인 경우 (실제 API 호출)
            elif hasattr(request, "auth") and request.auth:
                from rest_framework_simplejwt.tokens import AccessToken

                access_token = AccessToken(request.auth)
                user_id = access_token["user_id"]
                user_obj = User.objects.get(id=user_id)

            if not user_obj:
                return {"success": False, "message": "인증되지 않은 사용자입니다."}

            updated_fields = []

            # 닉네임 변경
            if data.nickname:
                user_obj.nickname = data.nickname
                updated_fields.append("nickname")

            # 휴대폰 번호 변경
            if data.phone_number:
                user_obj.phone_number = data.phone_number
                updated_fields.append("phone_number")

            # 프로필 이미지 처리
            from a_apis.models.files import File
            from a_apis.service.files import FileService

            # 필드명 수정: profile_image -> profile_img
            old_profile_img = getattr(user_obj, "profile_img", None)

            # 프로필 이미지 처리 로직
            if data.remove_profile_image:
                # 프로필 이미지 삭제 요청
                if old_profile_img:
                    FileService.delete_file(old_profile_img)
                    user_obj.profile_img = None
                    updated_fields.append("profile_img")
            elif profile_image:
                # 새 이미지로 교체 요청
                if old_profile_img:
                    FileService.delete_file(old_profile_img)

                # 새 프로필 이미지 업로드
                file_obj = FileService.upload_file(profile_image, file_type="profile")
                user_obj.profile_img = file_obj
                updated_fields.append("profile_img")

            # 변경 사항이 있으면 저장
            if updated_fields:
                user_obj.save(update_fields=updated_fields + ["updated_at"])

                # 업데이트된 필드 표시
                updated_str = ", ".join([field for field in updated_fields])
                return {
                    "success": True,
                    "message": f"회원정보가 수정되었습니다. (변경: {updated_str})",
                }
            else:
                return {
                    "success": False,
                    "message": "변경할 정보가 없습니다.",
                }

        except User.DoesNotExist:
            return {"success": False, "message": "사용자를 찾을 수 없습니다."}
        except Exception as e:
            return {
                "success": False,
                "message": f"회원정보 수정 중 오류가 발생했습니다: {str(e)}",
            }

    @staticmethod
    def change_user_password(request, data):
        """비밀번호 변경 서비스

        Args:
            request: HTTP 요청 객체
            data: PasswordChangeSchema 데이터 (current_password, new_password 포함)

        Returns:
            dict: 처리 결과 메시지
        """
        try:
            # 인증된 사용자 확인
            user = request.auth
            if not user:
                return {"success": False, "message": "인증되지 않은 사용자입니다."}

            from rest_framework_simplejwt.tokens import AccessToken

            access_token = AccessToken(user)
            user_id = access_token["user_id"]

            user = User.objects.get(id=user_id)

            # 현재 비밀번호 검증
            if not user.check_password(data.current_password):
                return {
                    "success": False,
                    "message": "현재 비밀번호가 일치하지 않습니다.",
                }

            # 새 비밀번호가 현재 비밀번호와 같은지 확인
            if data.current_password == data.new_password:
                return {
                    "success": False,
                    "message": "새 비밀번호는 현재 비밀번호와 달라야 합니다.",
                }

            # 새 비밀번호 설정
            user.set_password(data.new_password)
            user.save(update_fields=["password", "updated_at"])

            return {
                "success": True,
                "message": "비밀번호가 성공적으로 변경되었습니다.",
            }

        except User.DoesNotExist:
            return {"success": False, "message": "사용자를 찾을 수 없습니다."}
        except Exception as e:
            return {
                "success": False,
                "message": f"비밀번호 변경 중 오류가 발생했습니다: {str(e)}",
            }

    @staticmethod
    def get_received_reviews(request=None, user_id=None, page=1, page_size=10):
        """
        사용자가 받은 거래 후기 목록을 조회합니다.
        request 또는 user_id 중 하나는 반드시 제공되어야 합니다.
        """
        try:
            from a_user.models import Review, User

            from django.core.paginator import Paginator

            # 사용자 ID 확인 (request에서 추출 또는 직접 전달)
            if user_id is None and request is not None:
                if hasattr(request, "user") and isinstance(request.user, User):
                    user_id = request.user.id
                elif hasattr(request, "auth") and request.auth:
                    from rest_framework_simplejwt.tokens import AccessToken

                    access_token = AccessToken(request.auth)
                    user_id = access_token["user_id"]

            if user_id is None:
                return {"success": False, "message": "사용자 ID가 제공되지 않았습니다."}

            # 사용자 확인
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return {"success": False, "message": "존재하지 않는 사용자입니다."}

            # 해당 사용자가 받은 모든 거래 후기 조회
            # receiver가 현재 사용자인 모든 리뷰
            reviews = (
                Review.objects.filter(receiver=user)
                .select_related("product", "reviewer", "receiver")
                .order_by("-created_at")
            )

            # 페이지네이션 적용
            paginator = Paginator(reviews, page_size)
            if page > paginator.num_pages:
                page = 1
            current_page = paginator.page(page)

            # 응답 데이터 구성
            reviews_data = []
            for review in current_page:
                # 리뷰 작성자의 프로필 이미지 URL 가져오기
                profile_img_url = None
                if review.reviewer.profile_img:
                    profile_img_url = review.reviewer.profile_img.url

                # 리뷰 작성자의 인증된 지역 가져오기
                location_name = None
                certification = review.reviewer.region_certifications.first()
                if certification:
                    location_name = (
                        certification.region.name if certification.region else None
                    )

                reviews_data.append(
                    {
                        "id": review.id,
                        "product_id": review.product.id,
                        "product_title": review.product.title,
                        "content": review.content,
                        "created_at": review.created_at.isoformat(),
                        "reviewer": {
                            "id": review.reviewer.id,
                            "nickname": review.reviewer.nickname,
                            "profile_img_url": profile_img_url,
                            "location": location_name,
                        },
                    }
                )

            return {
                "success": True,
                "message": "거래 후기 목록을 조회했습니다.",
                "data": reviews_data,
                "total_count": paginator.count,
                "page": page,
                "page_size": page_size,
                "total_pages": paginator.num_pages,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"거래 후기 목록 조회 중 오류가 발생했습니다: {str(e)}",
                "data": [],
            }

    @staticmethod
    def get_received_manner_ratings(request=None, user_id=None, page=1, page_size=10):
        """
        사용자가 받은 매너 평가 목록을 조회합니다.
        request 또는 user_id 중 하나는 반드시 제공되어야 합니다.
        """
        try:
            from a_apis.models.trade import MannerRating
            from a_user.models import User

            from django.core.paginator import Paginator

            # 사용자 ID 확인 (request에서 추출 또는 직접 전달)
            if user_id is None and request is not None:
                if hasattr(request, "user") and isinstance(request.user, User):
                    user_id = request.user.id
                elif hasattr(request, "auth") and request.auth:
                    from rest_framework_simplejwt.tokens import AccessToken

                    access_token = AccessToken(request.auth)
                    user_id = access_token["user_id"]

            if user_id is None:
                return {"success": False, "message": "사용자 ID가 제공되지 않았습니다."}

            # 사용자 확인
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return {"success": False, "message": "존재하지 않는 사용자입니다."}

            # 해당 사용자가 받은 모든 매너 평가 조회
            ratings = (
                MannerRating.objects.filter(rated_user=user)
                .select_related("product", "rater", "rated_user")
                .order_by("-created_at")
            )

            # 페이지네이션 적용
            paginator = Paginator(ratings, page_size)
            if page > paginator.num_pages:
                page = 1
            current_page = paginator.page(page)

            # 응답 데이터 구성
            ratings_data = []
            for rating in current_page:
                # 평가자의 프로필 이미지 URL 가져오기
                profile_img_url = None
                if rating.rater.profile_img:
                    profile_img_url = rating.rater.profile_img.url

                # 평가자의 인증된 지역 가져오기
                location_name = None
                certification = rating.rater.region_certifications.first()
                if certification:
                    location_name = (
                        certification.region.name if certification.region else None
                    )

                ratings_data.append(
                    {
                        "id": rating.id,
                        "product_id": rating.product.id,
                        "product_title": rating.product.title,
                        "rating_type": rating.rating_type,
                        "rating_display": rating.get_rating_type_display(),
                        "created_at": rating.created_at.isoformat(),
                        "rater": {
                            "id": rating.rater.id,
                            "nickname": rating.rater.nickname,
                            "profile_img_url": profile_img_url,
                            "location": location_name,
                        },
                    }
                )

            return {
                "success": True,
                "message": "매너 평가 목록을 조회했습니다.",
                "data": ratings_data,
                "total_count": paginator.count,
                "page": page,
                "page_size": page_size,
                "total_pages": paginator.num_pages,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"매너 평가 목록 조회 중 오류가 발생했습니다: {str(e)}",
                "data": [],
            }

    @staticmethod
    def change_active_region(request, region_id: int):
        """활성 동네 변경 서비스

        인증한 동네 중 하나를 활성 동네(기본 동네)로 설정합니다.

        Args:
            request: HTTP 요청 객체
            region_id: 활성화할 동네 ID
        """
        try:
            # 인증된 사용자 확인
            user = None
            if hasattr(request, "user") and isinstance(request.user, User):
                user = request.user
            elif hasattr(request, "auth") and request.auth:
                from rest_framework_simplejwt.tokens import AccessToken

                access_token = AccessToken(request.auth)
                user_id = access_token["user_id"]
                user = User.objects.get(id=user_id)

            if not user:
                return {"success": False, "message": "인증되지 않은 사용자입니다."}

            # 해당 동네가 사용자의 인증된 동네인지 확인
            user_region = UserActivityRegion.objects.filter(
                user=user, activity_area_id=region_id
            ).first()

            if not user_region:
                return {"success": False, "message": "인증되지 않은 동네입니다."}

            # 이미 활성 동네(우선순위 1)인 경우
            if user_region.priority == 1:
                current_region = {
                    "id": user_region.activity_area.id,
                    "name": user_region.activity_area.name,
                    "code": user_region.activity_area.code,
                    "priority": user_region.priority,
                }
                return {
                    "success": True,
                    "message": "이미 활성화된 동네입니다.",
                    "current_region": current_region,
                }

            # 동네 우선순위 변경 (현재 우선순위와 1순위 동네 교체)
            current_priority = user_region.priority

            # 기존 1순위 동네 찾기
            previous_primary_region = UserActivityRegion.objects.filter(
                user=user, priority=1
            ).first()

            # 트랜잭션으로 우선순위 교체
            with transaction.atomic():
                if previous_primary_region:
                    previous_primary_region.priority = current_priority
                    previous_primary_region.save(
                        update_fields=["priority", "updated_at"]
                    )

                user_region.priority = 1
                user_region.save(update_fields=["priority", "updated_at"])

            # 새로 설정된 활성 동네 정보만 반환
            current_region = {
                "id": user_region.activity_area.id,
                "name": user_region.activity_area.name,
                "code": user_region.activity_area.code,
                "priority": 1,  # 이제 우선순위가 1이 됨
            }

            return {
                "success": True,
                "message": f"활성 동네가 '{user_region.activity_area.name}'(으)로 변경되었습니다.",
                "current_region": current_region,
            }

        except User.DoesNotExist:
            return {"success": False, "message": "사용자를 찾을 수 없습니다."}
        except Exception as e:
            return {
                "success": False,
                "message": f"동네 변경 중 오류가 발생했습니다: {str(e)}",
            }
