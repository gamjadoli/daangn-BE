from a_apis.auth.cookies import create_auth_response
from allauth.account.models import EmailAddress
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import authenticate, get_user_model, login

User = get_user_model()


class UserService:
    @staticmethod
    def create_user(email: str, password: str, nickname: str):
        try:
            user = User.objects.create_user(
                username=email, email=email, password=password, nickname=nickname
            )
            email_address = EmailAddress.objects.create(
                user=user, email=email, primary=True, verified=False
            )
            email_address.send_confirmation()
            return {
                "success": True,
                "message": "회원가입이 완료되었습니다. 이메일을 확인해주세요.",
            }
        except Exception as e:
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
