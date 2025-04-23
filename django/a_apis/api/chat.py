from typing import Optional

from a_apis.auth.bearer import AuthBearer
from a_apis.schema.chat import (
    ChatRoomListResponseSchema,
    ChatRoomResponseSchema,
    CreateChatRoomResponseSchema,
    MessageListResponseSchema,
    SendMessageRequestSchema,
    SendMessageResponseSchema,
)
from a_apis.service.chat import ChatService
from ninja import Query, Router

# 인증된 사용자만 접근 가능한 라우터
router = Router(auth=AuthBearer())


@router.post("/create", response=CreateChatRoomResponseSchema)
def create_chat_room(request, product_id: int):
    """
    상품에 대한 새 채팅방 생성 API

    상품 ID를 받아 해당 상품에 대한 채팅방을 생성합니다.
    자신의 상품에 대해서는 채팅방을 생성할 수 없습니다.
    이미 존재하는 채팅방이면 해당 채팅방 ID를 반환합니다.
    """
    return ChatService.create_chat_room(product_id=product_id, user_id=request.user.id)


@router.get("/", response=ChatRoomListResponseSchema)
def get_chat_rooms(request, page: int = 1, page_size: int = 20):
    """
    내 채팅방 목록 조회 API

    사용자가 참여 중인 모든 채팅방을 조회합니다.
    최근 메시지 시간 순으로 정렬됩니다.
    """
    return ChatService.get_chat_rooms(
        user_id=request.user.id, page=page, page_size=page_size
    )


@router.get("/{chat_room_id}", response=ChatRoomResponseSchema)
def get_chat_room_detail(request, chat_room_id: int):
    """
    채팅방 상세 정보 조회 API

    채팅방의 상세 정보를 조회합니다.
    상품 정보, 판매자, 구매자 정보를 포함합니다.
    """
    return ChatService.get_chat_room_detail(
        chat_room_id=chat_room_id, user_id=request.user.id
    )


@router.get("/{chat_room_id}/messages", response=MessageListResponseSchema)
def get_chat_messages(request, chat_room_id: int, page: int = 1, page_size: int = 20):
    """
    채팅방 메시지 조회 API

    채팅방의 메시지 목록을 조회합니다.
    최근 메시지가 먼저 나오도록 정렬됩니다 (최신순).
    해당 API 호출 시 사용자의 읽음 상태가 자동으로 갱신됩니다.
    """
    return ChatService.get_chat_messages(
        chat_room_id=chat_room_id,
        user_id=request.user.id,
        page=page,
        page_size=page_size,
    )


@router.post("/{chat_room_id}/messages", response=SendMessageResponseSchema)
def send_message(request, chat_room_id: int, data: SendMessageRequestSchema):
    """
    메시지 전송 API

    채팅방에 새 메시지를 전송합니다.
    WebSocket 연결 없이 REST API로도 메시지를 보낼 수 있습니다.
    파일 첨부도 가능합니다.
    """
    return ChatService.send_message(
        chat_room_id=chat_room_id,
        user_id=request.user.id,
        message=data.message,
        file_id=data.file_id,
    )
