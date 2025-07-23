import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from django.utils import timezone

from .models import ChatMessage, ChatRoom, ChatRoomParticipant


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        import logging

        logger = logging.getLogger("chatroom_debug")
        logger.error("[ChatConsumer.connect] called, user=%s", self.scope.get("user"))
        """WebSocket 연결 시 호출되는 메소드"""
        # URL에서 채팅방 ID 추출
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        # 채팅방 그룹 이름 생성 (채팅방별로 그룹 생성)
        self.room_group_name = f"chat_{self.room_id}"

        # 채팅방 존재 여부 확인 및 접근 권한 확인
        can_connect = await self.can_connect_to_room()
        if not can_connect:
            # 연결 거부
            await self.close()
            return

        # 채팅방 그룹에 참여
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # WebSocket 연결 수락
        await self.accept()

    async def disconnect(self, close_code):
        """WebSocket 연결 종료 시 호출되는 메소드"""
        # 채팅방 그룹에서 나가기
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """클라이언트로부터 메시지 수신 시 호출되는 메소드"""
        try:
            # JSON 데이터 파싱
            text_data_json = json.loads(text_data)
            message = text_data_json["message"]
            sender_id = text_data_json["sender_id"]

            # 선택적 파일 첨부
            file_id = text_data_json.get("file_id")

            # 메시지 저장
            chat_message = await self.save_message(sender_id, message, file_id)

            # 메시지 전송 시간 형식화
            timestamp = chat_message.created_at.isoformat()

            # 발신자 닉네임 가져오기
            sender_nickname = await self.get_user_nickname(sender_id)

            # 채팅방 그룹에 메시지 이벤트 전송
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "sender_id": sender_id,
                    "sender_nickname": sender_nickname,
                    "timestamp": timestamp,
                    "message_id": chat_message.id,
                    "file_url": (
                        await self.get_file_url(chat_message) if file_id else None
                    ),
                },
            )
        except Exception as e:
            # 오류 발생 시 처리
            await self.send(text_data=json.dumps({"error": str(e), "type": "error"}))

    async def chat_message(self, event):
        """채팅방 그룹으로부터 메시지 수신 시 호출되는 메소드"""
        # 클라이언트에게 메시지 전송
        await self.send(
            text_data=json.dumps(
                {
                    "type": "message",
                    "message": event["message"],
                    "sender_id": event["sender_id"],
                    "sender_nickname": event["sender_nickname"],
                    "timestamp": event["timestamp"],
                    "message_id": event["message_id"],
                    "file_url": event.get("file_url"),
                }
            )
        )

    @database_sync_to_async
    def can_connect_to_room(self):
        """사용자가 채팅방에 접근할 수 있는지 확인 (logger로 강제 출력)"""
        import logging

        logger = logging.getLogger("chatroom_debug")
        try:
            user = self.scope.get("user")
            logger.error("[DEBUG][can_connect_to_room] user: %s", user)
            if not user or user.is_anonymous:
                logger.error(
                    "[DEBUG][can_connect_to_room] user is anonymous or not set"
                )
                return False

            try:
                chat_room = ChatRoom.objects.get(id=self.room_id)
                logger.error(
                    f"[DEBUG][can_connect_to_room] chat_room found: {chat_room}"
                )
            except Exception as e:
                logger.error(f"[DEBUG][can_connect_to_room] chat_room get error: {e}")
                return False

            exists = ChatRoomParticipant.objects.filter(
                chat_room=chat_room, user=user, is_active=True
            ).exists()
            logger.error(f"[DEBUG][can_connect_to_room] participant exists? {exists}")
            return exists
        except Exception as e:
            logger.error(f"[DEBUG][can_connect_to_room] Exception: {e}")
            return False
        except ChatRoom.DoesNotExist:
            logger.error("[DEBUG][can_connect_to_room] ChatRoom.DoesNotExist")
            return False
        except Exception as e:
            logger.error(f"[DEBUG][can_connect_to_room] Unknown Exception: {e}")
            return False

    @database_sync_to_async
    def save_message(self, sender_id, message, file_id=None):
        """채팅 메시지 저장"""
        chat_room = ChatRoom.objects.get(id=self.room_id)

        # 메시지 생성
        chat_message = ChatMessage.objects.create(
            chat_room=chat_room, sender_id=sender_id, message=message, file_id=file_id
        )

        # 채팅방 갱신 시간 업데이트 (최근 메시지 순 정렬 위함)
        chat_room.save(update_fields=["updated_at"])

        return chat_message

    @database_sync_to_async
    def get_user_nickname(self, user_id):
        """사용자 닉네임 가져오기"""
        from a_user.models import User

        try:
            user = User.objects.get(id=user_id)
            return user.nickname
        except User.DoesNotExist:
            return "알 수 없음"

    @database_sync_to_async
    def get_file_url(self, message):
        """첨부파일 URL 가져오기"""
        if message.file:
            return message.file.url
        return None
