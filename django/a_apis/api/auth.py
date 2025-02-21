from typing import Dict

from a_apis.schema.auth import SocialLoginResponseSchema
from a_apis.service.auth import GoogleAuthService, KakaoAuthService, NaverAuthService
from ninja import Router

from django.conf import settings
from django.shortcuts import redirect

router = Router()


@router.get("/google/login/dev")
def google_auth_start_local(request):
    auth_url = GoogleAuthService.start_google_auth(
        settings.SERVER_BASE_URL_DEV, settings.AUTH_GOOGLE_CLIENT_ID
    )
    return redirect(auth_url)


@router.get("/google/callback/dev", response=SocialLoginResponseSchema)
def google_auth_callback_local(request, code: str = None):
    """
    Google 로그인 콜백 API
    is_active 값이 False인 경우 처음 로그인 한 회원이므로, 회원가입 페이지로 이동

    Args:
        request: Django 요청 객체
        code (str): 인증 코드

    Returns:
        SocialLoginResponseSchema: 로그인 응답 데이터
    """
    return GoogleAuthService.callback_google_auth(
        code=code,
        server_base_url=settings.SERVER_BASE_URL_DEV,
        client_id=settings.AUTH_GOOGLE_CLIENT_ID,
        client_secret=settings.AUTH_GOOGLE_CLIENT_SECRET,
        login_redirect_url=settings.LOGIN_REDIRECT_URL_DEV,
    )


@router.get("/google/login")
def google_auth_start(request):
    auth_url = GoogleAuthService.start_google_auth(
        settings.SERVER_BASE_URL, settings.AUTH_GOOGLE_CLIENT_ID
    )
    return redirect(auth_url)


@router.get("/google/callback", response=SocialLoginResponseSchema)
def google_auth_callback(request, code: str = None):
    return GoogleAuthService.callback_google_auth(
        code=code,
        server_base_url=settings.SERVER_BASE_URL,
        client_id=settings.AUTH_GOOGLE_CLIENT_ID,
        client_secret=settings.AUTH_GOOGLE_CLIENT_SECRET,
        login_redirect_url=settings.LOGIN_REDIRECT_URL,
    )


@router.get("/kakao/login/dev")
def kakao_auth_start_local(request):
    auth_url = KakaoAuthService.start_kakao_auth(
        settings.SERVER_BASE_URL_DEV, settings.AUTH_KAKAO_CLIENT_ID
    )
    return redirect(auth_url)


@router.get("/kakao/callback/dev", response=Dict)
def kakao_auth_callback_local(request, code: str = None):
    response_data = KakaoAuthService.callback_kakao_auth(
        code=code,
        server_base_url=settings.SERVER_BASE_URL_DEV,
        client_id=settings.AUTH_KAKAO_CLIENT_ID,
        client_secret=settings.AUTH_KAKAO_CLIENT_SECRET,
        login_redirect_url=settings.LOGIN_REDIRECT_URL_DEV,
    )
    return response_data


@router.get("/kakao/login")
def kakao_auth_start(request):
    auth_url = KakaoAuthService.start_kakao_auth(
        settings.SERVER_BASE_URL, settings.AUTH_KAKAO_CLIENT_ID
    )
    return redirect(auth_url)


@router.get("/kakao/callback", response=Dict)
def kakao_auth_callback(request, code: str = None):
    return KakaoAuthService.callback_kakao_auth(
        code=code,
        server_base_url=settings.SERVER_BASE_URL,
        client_id=settings.AUTH_KAKAO_CLIENT_ID,
        client_secret=settings.AUTH_KAKAO_CLIENT_SECRET,
        login_redirect_url=settings.LOGIN_REDIRECT_URL,
    )


@router.get("/naver/login/dev")
def naver_auth_start_local(request):
    auth_url = NaverAuthService.start_naver_auth(
        settings.SERVER_BASE_URL_DEV, settings.AUTH_NAVER_CLIENT_ID
    )
    return redirect(auth_url)


@router.get("/naver/callback/dev", response=Dict)
def naver_auth_callback_local(request, code: str = None):
    response_data = NaverAuthService.callback_naver_auth(
        code=code,
        server_base_url=settings.SERVER_BASE_URL_DEV,
        client_id=settings.AUTH_NAVER_CLIENT_ID,
        client_secret=settings.AUTH_NAVER_CLIENT_SECRET,
        login_redirect_url=settings.LOGIN_REDIRECT_URL_DEV,
    )
    return response_data


@router.get("/naver/login")
def naver_auth_start(request):
    auth_url = NaverAuthService.start_naver_auth(
        settings.SERVER_BASE_URL, settings.AUTH_NAVER_CLIENT_ID
    )
    return redirect(auth_url)


@router.get("/naver/callback", response=Dict)
def naver_auth_callback(request, code: str = None):
    return NaverAuthService.callback_naver_auth(
        code=code,
        server_base_url=settings.SERVER_BASE_URL,
        client_id=settings.AUTH_NAVER_CLIENT_ID,
        client_secret=settings.AUTH_NAVER_CLIENT_SECRET,
        login_redirect_url=settings.LOGIN_REDIRECT_URL,
    )
