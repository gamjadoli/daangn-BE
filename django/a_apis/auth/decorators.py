from functools import wraps

from a_apis.auth.bearer import AuthBearer
from rest_framework_simplejwt.tokens import AccessToken

from django.contrib.auth import get_user_model

User = get_user_model()


def optional_auth(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                try:
                    # JWT 토큰 디코딩 및 유저 조회
                    access_token = AccessToken(token)
                    user = User.objects.get(id=access_token["user_id"])
                    request.user = user
                    print(f"Token authenticated, User: {user.username}")  # 디버깅용
                except Exception as e:
                    print(f"Token validation failed: {str(e)}")  # 디버깅용
                    request.user = None
            else:
                request.user = None
        except Exception as e:
            print(f"Auth error: {str(e)}")  # 디버깅용
            request.user = None
        return func(request, *args, **kwargs)

    return wrapper
