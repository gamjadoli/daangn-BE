from django.urls import re_path

from .consumers import ChatConsumer

# WebSocket URL 패턴 정의
websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<room_id>\w+)/$", ChatConsumer.as_asgi()),
]
