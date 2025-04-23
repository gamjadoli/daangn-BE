from datetime import datetime
from typing import List, Optional

from ninja import Field, Schema


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
