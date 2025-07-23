from urllib.parse import parse_qs

import jwt
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

User = get_user_model()


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        headers = dict((k.decode(), v.decode()) for k, v in scope.get("headers", []))
        token = None
        # 1. Authorization 헤더에서 토큰 추출
        auth_header = headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
        # 2. 쿼리스트링에서도 토큰 허용 (옵션)
        if not token:
            query_string = scope.get("query_string", b"").decode()
            params = parse_qs(query_string)
            token = params.get("token", [None])[0]
        user = await self.get_user(token)
        import logging

        logger = logging.getLogger("chatroom_debug")
        logger.error("[JWTAuthMiddleware] user set: %s", user)
        scope["user"] = user
        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user(self, token):
        if not token:
            return AnonymousUser()
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            if not user_id:
                return AnonymousUser()
            return User.objects.get(id=user_id)
        except Exception:
            return AnonymousUser()


def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(inner)
