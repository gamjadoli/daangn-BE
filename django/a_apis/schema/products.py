from decimal import Decimal
from typing import List, Optional

from ninja import Field, Schema
from pydantic import validator


class LocationSchema(Schema):
    """거래 희망 위치 스키마"""

    latitude: float = Field(..., description="위도")
    longitude: float = Field(..., description="경도")
    description: str = Field(..., description="거래 희망 장소 설명 (예: OO역 1번 출구)")


class ProductCreateSchema(Schema):
    """상품 등록 요청 스키마"""

    title: str = Field(
        ..., min_length=2, max_length=100, description="상품 제목 (2-100자)"
    )
    trade_type: str = Field(
        ..., description="거래 방식 (sale: 판매하기, share: 나눔하기)"
    )
    price: Optional[int] = Field(
        None,
        ge=0,
        description="판매 금액 (판매하기인 경우 필수, 나눔하기인 경우 무시됨)",
    )
    accept_price_offer: bool = Field(default=False, description="가격 제안 허용 여부")
    description: str = Field(
        ..., description="상품 설명 (상세 정보, 거래 관련 주의사항 등)"
    )
    meeting_location: LocationSchema = Field(..., description="거래 희망 위치 정보")

    @validator("price")
    def validate_price(cls, v, values):
        if values.get("trade_type") == "sale" and not v:
            raise ValueError("판매하기의 경우 가격을 입력해주세요")
        return v


class ProductResponseSchema(Schema):
    """상품 응답 스키마"""

    success: bool = Field(..., description="요청 처리 성공 여부")
    message: Optional[str] = Field(None, description="처리 결과 메시지")
    data: Optional[dict] = Field(None, description="응답 데이터")
