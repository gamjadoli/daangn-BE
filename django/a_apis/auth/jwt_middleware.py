from urllib.parse import parse_qs

import jwt
from channels.db import database_sync_to_async

from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


class JWTAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        return JWTAuthMiddlewareInstance(scope, self.inner)


class JWTAuthMiddlewareInstance:
    def __init__(self, scope, inner):
        self.scope = dict(scope)
        self.inner = inner

    async def __call__(self, receive, send):
        headers = dict(
            (k.decode(), v.decode()) for k, v in self.scope.get("headers", [])
        )
        token = None
        # 1. Authorization 헤더에서 토큰 추출
        auth_header = headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
        # 2. 쿼리스트링에서도 토큰 허용 (옵션)
        if not token:
            query_string = self.scope.get("query_string", b"").decode()
            params = parse_qs(query_string)
            token = params.get("token", [None])[0]
        user = await self.get_user(token)
        self.scope["user"] = user
        inner = self.inner(self.scope)
        return await inner(receive, send)

    @database_sync_to_async
    def get_user(self, token):
        if not token:
            from django.contrib.auth.models import AnonymousUser

            return AnonymousUser()
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            if not user_id:
                from django.contrib.auth.models import AnonymousUser

                return AnonymousUser()
            return User.objects.get(id=user_id)
        except Exception:
            from django.contrib.auth.models import AnonymousUser

            return AnonymousUser()


from asgiref.sync import sync_to_async

# 미들웨어 스택으로 사용하기 위한 헬퍼
from channels.middleware import BaseMiddleware


def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(inner)
