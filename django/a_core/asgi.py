"""
ASGI config for a_core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

# 설정 모듈 기본값 설정
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "a_core.settings.development")

# Django 앱 설정이 로드된 후에 다른 모듈 임포트
from django.core.asgi import get_asgi_application

# HTTP 요청을 처리하기 위한 ASGI 애플리케이션 가져오기
django_asgi_app = get_asgi_application()

# 웹소켓 라우팅 설정 임포트 (Django 앱 초기화 후)
from a_apis.auth.jwt_middleware import JWTAuthMiddlewareStack
from a_apis.routing import websocket_urlpatterns
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

# ASGI 애플리케이션 구성 (AllowedHostsOriginValidator 제거)
application = ProtocolTypeRouter(
    {
        # HTTP 요청 처리
        "http": django_asgi_app,
        # WebSocket 요청 처리
        "websocket": JWTAuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
