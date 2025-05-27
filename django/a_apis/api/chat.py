from typing import Optional

from a_apis.auth.bearer import AuthBearer
from a_apis.schema.chat import (
    ChatRoomListResponseSchema,
    ChatRoomResponseSchema,
    CreateChatRoomResponseSchema,
    MessageListResponseSchema,
    SendMessageRequestSchema,
    SendMessageResponseSchema,
    TradeAppointmentActionSchema,
    TradeAppointmentCreateSchema,
    TradeAppointmentListResponseSchema,
    TradeAppointmentResponseSchema,
)
from a_apis.service.chat import ChatService
from ninja import Query, Router

# 인증된 사용자만 접근 가능한 라우터
router = Router(auth=AuthBearer())


@router.post("", response=CreateChatRoomResponseSchema)
def create_chat_room(request, product_id: int):
    """
    상품에 대한 새 채팅방 생성 API

    상품 ID로 채팅방 생성.
    자신의 상품에 대해서는 채팅방 생성 불가.
    이미 존재하는 채팅방이면 해당 채팅방 ID 반환.
    """
    return ChatService.create_chat_room(product_id=product_id, user_id=request.user.id)


@router.get("", response=ChatRoomListResponseSchema)
def get_chat_rooms(request, page: int = 1, page_size: int = 20):
    """
    내 채팅방 목록 조회 API

    참여 중인 모든 채팅방 조회.
    최근 메시지 시간 순 정렬.
    """
    return ChatService.get_chat_rooms(
        user_id=request.user.id, page=page, page_size=page_size
    )


@router.get("/{chat_room_id}", response=ChatRoomResponseSchema)
def get_chat_room_detail(request, chat_room_id: int):
    """
    채팅방 상세 정보 조회 API

    채팅방 상세 정보 조회.
    상품 정보, 판매자, 구매자 정보 포함.
    """
    return ChatService.get_chat_room_detail(
        chat_room_id=chat_room_id, user_id=request.user.id
    )


@router.get("/{chat_room_id}/messages", response=MessageListResponseSchema)
def get_chat_messages(
    request, chat_room_id: int, page: int = 1, page_size: int = 20, sort: str = "newest"
):
    """
    채팅방 메시지 조회 API

    채팅방 메시지 목록 조회.
    최신순 정렬.
    API 호출 시 읽음 상태 자동 갱신.

    쿼리 파라미터:
    - page: 페이지 번호 (기본값: 1)
    - page_size: 페이지 크기 (기본값: 20)
    - sort: 정렬 방식 (newest: 최신순, oldest: 과거순, 기본값: newest)
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

    채팅방에 새 메시지 전송.
    REST API로 메시지 전송 가능.
    파일 첨부 가능.
    """
    return ChatService.send_message(
        chat_room_id=chat_room_id,
        user_id=request.user.id,
        message=data.message,
        file_id=data.file_id,
    )


@router.post("/{chat_room_id}/appointments", response=TradeAppointmentResponseSchema)
def create_appointment(request, chat_room_id: int, data: TradeAppointmentCreateSchema):
    """
    거래약속 생성 API

    채팅방에서 판매자와 구매자 간 거래 약속 생성.
    약속 일시와 장소 설정.
    생성 시 상품 상태가 예약중으로 변경됨.
    """
    return ChatService.create_appointment(
        chat_room_id=chat_room_id,
        user_id=request.user.id,
        appointment_date=data.appointment_date,
        location_lat=data.location.latitude,
        location_lng=data.location.longitude,
        location_desc=data.location.description,
    )


@router.get("/{chat_room_id}/appointments", response=TradeAppointmentListResponseSchema)
def get_appointments_for_chat(request, chat_room_id: int):
    """
    채팅방 거래약속 목록 조회 API

    채팅방에 설정된 모든 거래약속 조회.
    """
    return ChatService.get_appointments_for_chat(
        chat_room_id=chat_room_id, user_id=request.user.id
    )


@router.get("/appointments/{appointment_id}", response=TradeAppointmentResponseSchema)
def get_appointment(request, appointment_id: int):
    """
    거래약속 상세 조회 API

    특정 거래약속 상세 정보 조회.
    판매자 또는 구매자만 조회 가능.
    """
    return ChatService.get_appointment(
        appointment_id=appointment_id, user_id=request.user.id
    )


@router.patch(
    "/appointments/{appointment_id}/status", response=TradeAppointmentResponseSchema
)
def update_appointment_status(
    request, appointment_id: int, data: TradeAppointmentActionSchema
):
    """
    거래약속 상태 변경 API

    거래약속 상태 변경 (confirm: 확정, cancel: 취소, complete: 완료)
    판매자 또는 구매자만 상태 변경 가능.
    취소 시 상품 상태가 다시 판매중으로 변경됨.
    """
    return ChatService.update_appointment_status(
        appointment_id=appointment_id, user_id=request.user.id, action=data.action
    )
