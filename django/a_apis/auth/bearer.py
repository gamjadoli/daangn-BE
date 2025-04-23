from ninja.security import HttpBearer
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from django.contrib.auth import get_user_model

User = get_user_model()


class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        try:
            # 토큰 검증
            access_token = AccessToken(token)
            # 사용자 ID 추출
            user_id = access_token.payload.get("user_id")

            if user_id:
                # 사용자 객체 가져오기
                user = User.objects.get(id=user_id)
                # 요청 객체에 사용자 할당
                request.user = user
                return token
            return None
        except TokenError:
            return None
        except User.DoesNotExist:
            return None
