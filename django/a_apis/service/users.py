from a_apis.auth.cookies import create_auth_response
from a_apis.models.email_verification import EmailVerification
from a_apis.schema.users import LoginSchema, SignupSchema
from allauth.account.models import EmailAddress
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import authenticate, get_user_model, login

User = get_user_model()


class UserService:
    @staticmethod
    # 회원가입 로직
    def signup(data: SignupSchema):
        try:
            # 이메일 인증 여부 확인
            verification = EmailVerification.objects.filter(
                email=data.email, is_verified=True
            ).first()

            if not verification:
                return {"success": False, "message": "이메일 인증이 필요합니다."}

            # 이메일 중복 확인
            if User.objects.filter(email=data.email).exists():
                return {"success": False, "message": "이미 존재하는 이메일입니다."}

            # 닉네임 중복 확인
            if User.objects.filter(nickname=data.nickname).exists():
                return {"success": False, "message": "이미 존재하는 닉네임입니다."}

            # 유저 생성 - create_user 메서드로 수정
            user = User.objects.create_user(
                username=data.email,  # email을 username으로 사용
                email=data.email,
                password=data.password,
                nickname=data.nickname,
                phone_number=data.phone_number,
                is_email_verified=True,  # 이미 인증된 상태로 설정
                rating_score=36.5,  # 기본 매너온도
            )

            # 토큰 생성
            refresh = RefreshToken.for_user(user)

            return {
                "success": True,
                "message": "회원가입이 완료되었습니다.",
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
                "user": {
                    "email": user.email,
                    "nickname": user.nickname,
                    "phone_number": user.phone_number,
                    "is_activated": user.is_activated,
                    "is_email_verified": user.is_email_verified,
                    "rating_score": float(user.rating_score),
                    "profile_img_url": (
                        user.profile_img.file.url if user.profile_img else None
                    ),
                },
            }
        except Exception as e:
            print(f"Signup error: {str(e)}")  # 디버깅용 로그 추가
            return {"success": False, "message": str(e)}

    @staticmethod
    def login_user(request, email: str, password: str):
        user = authenticate(request, username=email, password=password)
        if user:
            email_address = EmailAddress.objects.filter(user=user, primary=True).first()
            if email_address and email_address.verified:
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
            return {"success": False, "message": "이메일 인증이 필요합니다."}
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
