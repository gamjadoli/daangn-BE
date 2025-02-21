from rest_framework_simplejwt.tokens import RefreshToken

from django.http import JsonResponse


def create_auth_response(
    data: dict, access_token: str, refresh_token: str
) -> JsonResponse:
    """
    Create HTTP response with auth data and cookies
    """
    response = JsonResponse(data, safe=False)
    response.set_cookie(
        "access_token",
        str(access_token),
        httponly=True,
        secure=True,
        samesite="Lax",
        max_age=30 * 60,  # 30분
    )
    response.set_cookie(
        "refresh_token",
        str(refresh_token),
        httponly=True,
        secure=True,
        samesite="Lax",
        max_age=7 * 24 * 60 * 60,  # 7일
    )
    return response
