from typing import Any, Dict, List, Optional

from ninja import Field, Schema
from pydantic import validator


class ProductCategorySchema(Schema):
    """카테고리 스키마"""

    id: int = Field(..., description="카테고리 ID")
    name: str = Field(..., description="카테고리명")
    parent_id: Optional[int] = Field(None, description="상위 카테고리 ID")


class CategoryListResponseSchema(Schema):
    """카테고리 목록 응답 스키마"""

    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: List[ProductCategorySchema] = Field([], description="카테고리 목록")


class CategorySearchResponseSchema(Schema):
    """카테고리 검색 응답 스키마"""

    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: List[ProductCategorySchema] = Field([], description="추천 카테고리 목록")


class LocationSchema(Schema):
    """거래 위치 스키마"""

    latitude: float = Field(..., description="위도")
    longitude: float = Field(..., description="경도")
    description: Optional[str] = Field(
        None, description="거래 장소 설명 (예: OO역 1번 출구)"
    )

    @validator("latitude")
    def validate_latitude(cls, v):
        if not -90 <= v <= 90:
            raise ValueError("위도는 -90에서 90 사이의 값이어야 합니다.")
        return v

    @validator("longitude")
    def validate_longitude(cls, v):
        if not -180 <= v <= 180:
            raise ValueError("경도는 -180에서 180 사이의 값이어야 합니다.")
        return v


class ProductCreateSchema(Schema):
    """상품 등록 스키마"""

    title: str = Field(..., description="상품 제목")
    trade_type: str = Field(
        ..., description="거래 방식 (sale: 판매하기, share: 나눔하기)"
    )
    price: Optional[int] = Field(None, description="판매 가격 (나눔하기인 경우 무시)")
    accept_price_offer: bool = Field(False, description="가격 제안 허용 여부")
    category_id: Optional[int] = Field(None, description="카테고리 ID")
    description: str = Field(
        ..., description="상품 설명 (상세 정보, 거래 관련 주의사항 등)"
    )
    meeting_location: LocationSchema = Field(..., description="거래 희망 위치 정보")

    @validator("title")
    def title_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("상품 제목을 입력해주세요.")
        if len(v) > 100:
            raise ValueError("상품 제목은 100자 이내로 입력해주세요.")
        return v.strip()

    @validator("trade_type")
    def validate_trade_type(cls, v):
        if v not in ["sale", "share"]:
            raise ValueError("거래 방식은 'sale' 또는 'share'만 가능합니다.")
        return v

    @validator("price")
    def validate_price(cls, v, values):
        if (
            "trade_type" in values
            and values.get("trade_type") == "sale"
            and (v is None or v < 0)
        ):
            raise ValueError("판매가격을 입력해주세요.")
        if v is not None and v > 10000000:  # 천만원 제한
            raise ValueError("가격은 천만원 이하로 입력해주세요.")
        return v

    @validator("description")
    def description_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("상품 설명을 입력해주세요.")
        return v.strip()


class ProductImageSchema(Schema):
    """상품 이미지 스키마"""

    id: int = Field(..., description="이미지 ID")
    url: str = Field(..., description="이미지 URL")


class ProductDetailSchema(Schema):
    """상품 상세 정보 스키마"""

    id: int = Field(..., description="상품 ID")
    title: str = Field(..., description="상품 제목")
    trade_type: str = Field(
        ..., description="거래 방식 (sale: 판매하기, share: 나눔하기)"
    )
    price: Optional[int] = Field(None, description="판매 가격")
    category: Optional[ProductCategorySchema] = Field(None, description="상품 카테고리")
    accept_price_offer: bool = Field(..., description="가격 제안 허용 여부")
    description: str = Field(..., description="상품 설명")
    view_count: int = Field(..., description="조회수")
    status: str = Field(
        ..., description="상품 상태 (new: 판매중, reserved: 예약중, soldout: 판매완료)"
    )
    created_at: str = Field(..., description="등록 일시")
    refresh_at: Optional[str] = Field(None, description="끌어올린 일시")
    seller_nickname: str = Field(..., description="판매자 닉네임")
    seller_id: int = Field(..., description="판매자 ID")
    meeting_location: LocationSchema = Field(..., description="거래 희망 위치")
    images: List[ProductImageSchema] = Field([], description="상품 이미지 목록")
    is_interested: bool = Field(False, description="관심상품 등록 여부")


class ProductListItemSchema(Schema):
    """상품 목록 아이템 스키마"""

    id: int = Field(..., description="상품 ID")
    title: str = Field(..., description="상품 제목")
    price: Optional[int] = Field(None, description="판매 가격")
    status: str = Field(..., description="상품 상태 (new, reserved, soldout)")
    trade_type: str = Field(..., description="거래 방식 (sale, share)")
    created_at: str = Field(..., description="등록 일시")
    refresh_at: Optional[str] = Field(None, description="끌어올린 일시")
    image_url: Optional[str] = Field(None, description="대표 이미지 URL")
    seller_nickname: str = Field(..., description="판매자 닉네임")
    location_description: Optional[str] = Field(None, description="거래 장소 설명")
    interest_count: int = Field(0, description="관심 등록 수")


class ProductResponseSchema(Schema):
    """상품 응답 스키마"""

    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: Optional[ProductDetailSchema] = Field(None, description="상품 상세 정보")


class ProductListResponseSchema(Schema):
    """상품 목록 응답 스키마"""

    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: List[ProductListItemSchema] = Field([], description="상품 목록")
    total_count: int = Field(0, description="전체 상품 수")
    page: int = Field(1, description="현재 페이지")
    page_size: int = Field(20, description="페이지 크기")
    total_pages: int = Field(1, description="전체 페이지 수")


class ProductStatusUpdateSchema(Schema):
    """상품 상태 업데이트 스키마"""

    status: str = Field(
        ...,
        description="변경할 상태 (new: 판매중, reserved: 예약중, soldout: 판매완료)",
    )

    @validator("status")
    def validate_status(cls, v):
        if v not in ["new", "reserved", "soldout"]:
            raise ValueError(
                "상품 상태는 'new', 'reserved', 'soldout' 중 하나여야 합니다."
            )
        return v


class ProductSearchSchema(Schema):
    """상품 검색 스키마"""

    keyword: Optional[str] = Field(None, description="검색어")
    status: Optional[str] = Field(
        None, description="상품 상태로 필터링 (new, reserved, soldout)"
    )
    trade_type: Optional[str] = Field(
        None, description="거래 방식으로 필터링 (sale, share)"
    )
    min_price: Optional[int] = Field(None, description="최소 가격")
    max_price: Optional[int] = Field(None, description="최대 가격")
