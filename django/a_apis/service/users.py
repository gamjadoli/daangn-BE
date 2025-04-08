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
            return {
                "success": True,
                "message": "로그인 되었습니다.",
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
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

            return {
                "success": True,
                "message": "인증된 사용자입니다.",
                "user": {"email": user.email},
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
