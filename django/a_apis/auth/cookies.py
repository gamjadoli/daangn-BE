from rest_framework_simplejwt.tokens import RefreshToken

from django.conf import settings
from django.http import JsonResponse


def create_auth_response(
    data: dict, access_token: str, refresh_token: str
) -> JsonResponse:
    """
    Create HTTP response with auth data and cookies
    """
    # settings.py에서 토큰 만료 시간 설정 가져오기
    access_token_lifetime = int(
        settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()
    )
    refresh_token_lifetime = int(
        settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()
    )

    response = JsonResponse(data, safe=False)
    # 환경에 따라 SameSite 설정을 달리 적용
    samesite = settings.SESSION_COOKIE_SAMESITE

    response.set_cookie(
        "access_token",
        str(access_token),
        httponly=True,
        secure=True,
        samesite=samesite,
        max_age=access_token_lifetime,  # settings에서 가져온 값 사용
        domain=(
            settings.SESSION_COOKIE_DOMAIN
            if hasattr(settings, "SESSION_COOKIE_DOMAIN")
            else None
        ),
    )
    response.set_cookie(
        "refresh_token",
        str(refresh_token),
        httponly=True,
        secure=True,
        samesite=samesite,
        max_age=refresh_token_lifetime,  # settings에서 가져온 값 사용
        domain=(
            settings.SESSION_COOKIE_DOMAIN
            if hasattr(settings, "SESSION_COOKIE_DOMAIN")
            else None
        ),
    )
    return response
