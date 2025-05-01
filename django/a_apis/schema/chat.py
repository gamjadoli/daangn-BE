from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from ninja import Field, Schema

from .products import LocationSchema, MannerRatingType


class MessageSchema(Schema):
    """채팅 메시지 스키마"""

    id: int = Field(..., description="메시지 ID")
    sender_id: int = Field(..., description="발신자 ID")
    sender_nickname: str = Field(..., description="발신자 닉네임")
    message: str = Field(..., description="메시지 내용")
    created_at: datetime = Field(..., description="메시지 작성 시간")
    is_deleted: bool = Field(False, description="메시지 삭제 여부")
    file_url: Optional[str] = Field(None, description="첨부 파일 URL")


class ChatRoomSchema(Schema):
    """채팅방 목록 아이템 스키마"""

    id: int = Field(..., description="채팅방 ID")
    product_id: int = Field(..., description="상품 ID")
    product_title: str = Field(..., description="상품 제목")
    product_image_url: Optional[str] = Field(None, description="상품 이미지 URL")
    last_message: Optional[str] = Field(None, description="마지막 메시지 내용")
    last_message_time: Optional[datetime] = Field(
        None, description="마지막 메시지 시간"
    )
    unread_count: int = Field(0, description="읽지 않은 메시지 수")


class ChatRoomDetailSchema(Schema):
    """채팅방 상세 정보 스키마"""

    id: int = Field(..., description="채팅방 ID")
    product_id: int = Field(..., description="상품 ID")
    product_title: str = Field(..., description="상품 제목")
    product_image_url: Optional[str] = Field(None, description="상품 이미지 URL")
    seller_id: int = Field(..., description="판매자 ID")
    seller_nickname: str = Field(..., description="판매자 닉네임")
    buyer_id: Optional[int] = Field(None, description="구매자 ID")
    buyer_nickname: Optional[str] = Field(None, description="구매자 닉네임")
    created_at: datetime = Field(..., description="채팅방 생성 시간")


class CreateChatRoomResponseSchema(Schema):
    """채팅방 생성 응답 스키마"""

    success: bool = Field(..., description="요청 성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: Optional[dict] = Field(None, description="응답 데이터 (생성된 채팅방 ID 등)")


class ChatRoomListResponseSchema(Schema):
    """채팅방 목록 응답 스키마"""

    success: bool = Field(..., description="요청 성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: List[ChatRoomSchema] = Field(..., description="채팅방 목록")


class ChatRoomResponseSchema(Schema):
    """채팅방 상세 응답 스키마"""

    success: bool = Field(..., description="요청 성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: ChatRoomDetailSchema = Field(..., description="채팅방 상세 정보")


class MessageListResponseSchema(Schema):
    """메시지 목록 응답 스키마"""

    success: bool = Field(..., description="요청 성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: List[MessageSchema] = Field(..., description="메시지 목록")
    total_count: int = Field(..., description="전체 메시지 수")
    page: int = Field(..., description="현재 페이지")
    page_size: int = Field(..., description="페이지 크기")
    total_pages: int = Field(..., description="전체 페이지 수")


class SendMessageRequestSchema(Schema):
    """메시지 전송 요청 스키마"""

    message: str = Field(..., description="메시지 내용")
    file_id: Optional[int] = Field(None, description="첨부 파일 ID (선택사항)")


class SendMessageResponseSchema(Schema):
    """메시지 전송 응답 스키마"""

    success: bool = Field(..., description="요청 성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: Optional[MessageSchema] = Field(None, description="전송된 메시지 정보")


class PriceOfferCreateSchema(Schema):
    """가격 제안 생성 스키마"""

    price: int = Field(..., description="제안 가격")
    chat_room_id: Optional[int] = Field(None, description="채팅방 ID (선택 사항)")


class PriceOfferResponseSchema(Schema):
    """가격 제안 응답 스키마"""

    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: Optional[Dict] = Field(None, description="가격 제안 정보")


class PriceOfferListSchema(Schema):
    """가격 제안 목록 응답 스키마"""

    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: List[Dict] = Field([], description="가격 제안 목록")


class PriceOfferActionSchema(Schema):
    """가격 제안 수락/거절 스키마"""

    action: str = Field(..., description="수락/거절 여부 (accept 또는 reject)")


class TradeCompleteSchema(Schema):
    """거래 완료 처리 스키마"""

    buyer_id: int = Field(..., description="구매자 ID")
    final_price: Optional[int] = Field(None, description="최종 거래 가격 (선택 사항)")


class ReviewCreateSchema(Schema):
    """거래 후기 작성 스키마"""

    content: str = Field(..., description="후기 내용")


class ReviewResponseSchema(Schema):
    """거래 후기 응답 스키마"""

    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: Optional[Dict] = Field(None, description="후기 정보")


class MannerRatingCreateSchema(Schema):
    """매너 평가 스키마"""

    rating_types: List[MannerRatingType] = Field(
        ..., description="평가 유형 목록", example=["time", "kind", "accurate"]
    )

    class Config:
        schema_extra = {"example": {"rating_types": ["time", "response", "kind"]}}


class MannerRatingResponseSchema(Schema):
    """매너 평가 응답 스키마"""

    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: Optional[Dict] = Field(None, description="매너 평가 정보")
