from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

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

    latitude: Optional[float] = Field(None, description="위도")
    longitude: Optional[float] = Field(None, description="경도")
    description: Optional[str] = Field(
        None, description="거래 장소 설명 (예: OO역 1번 출구)"
    )
    distance_text: Optional[str] = Field(
        None, description="인증된 동네로부터의 거리 (예: 1.2km, 500m)"
    )

    @validator("latitude")
    def validate_latitude(cls, v):
        if v is not None and not -90 <= v <= 90:
            raise ValueError("위도는 -90에서 90 사이의 값이어야 합니다.")
        return v

    @validator("longitude")
    def validate_longitude(cls, v):
        if v is not None and not -180 <= v <= 180:
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
    region_id: int = Field(..., description="등록할 동네 ID (인증된 동네 중 선택)")
    meeting_location: Optional[LocationSchema] = Field(
        None, description="거래 희망 위치 정보 (선택사항)"
    )

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


class SellerSchema(Schema):
    """판매자 정보 스키마"""

    id: int = Field(..., description="판매자 ID")
    nickname: str = Field(..., description="판매자 닉네임")
    profile_image_url: Optional[str] = Field(None, description="프로필 이미지 URL")
    rating_score: float = Field(..., description="매너온도")


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
    price_offer_count: int = Field(0, description="현재 받은 가격 제안 개수")
    description: str = Field(..., description="상품 설명")
    view_count: int = Field(..., description="조회수")
    status: str = Field(
        ..., description="상품 상태 (new: 판매중, reserved: 예약중, soldout: 판매완료)"
    )
    created_at: str = Field(..., description="등록 일시")
    refresh_at: Optional[str] = Field(None, description="끌어올린 일시")
    seller: SellerSchema = Field(..., description="판매자 정보")
    meeting_location: Optional[LocationSchema] = Field(
        None, description="거래 희망 위치"
    )
    images: List[ProductImageSchema] = Field([], description="상품 이미지 목록")
    is_interested: bool = Field(False, description="관심상품 등록 여부")
    region_name: Optional[str] = Field(None, description="상품이 등록된 동네명")
    chat_count: int = Field(0, description="활성화된 채팅방 수")


class ProductListItemSchema(Schema):
    """상품 목록 아이템 스키마"""

    id: int = Field(..., description="상품 ID")
    title: str = Field(..., description="상품 제목")
    description: str = Field(..., description="상품 설명")
    price: Optional[int] = Field(None, description="판매 가격")
    status: str = Field(..., description="상품 상태 (new, reserved, soldout)")
    trade_type: str = Field(..., description="거래 방식 (sale, share)")
    created_at: str = Field(..., description="등록 일시")
    refresh_at: Optional[str] = Field(None, description="끌어올린 일시")
    image_url: Optional[str] = Field(None, description="대표 이미지 URL")
    seller_nickname: str = Field(..., description="판매자 닉네임")
    meeting_location: Optional[LocationSchema] = Field(
        None, description="거래 희망 위치 (위도, 경도, 설명, 거리 포함)"
    )
    interest_count: int = Field(0, description="관심 등록 수")
    chat_count: int = Field(0, description="활성화된 채팅방 수")
    region_name: Optional[str] = Field(None, description="상품이 등록된 동네명")


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


# 가격 제안 관련 스키마
class PriceOfferSchema(Schema):
    """가격 제안 스키마"""

    price: int = Field(..., description="제안 가격")

    @validator("price")
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError("제안 가격은 0보다 커야 합니다.")
        return v


class PriceOfferDetailSchema(Schema):
    """가격 제안 상세 스키마"""

    id: int = Field(..., description="가격 제안 ID")
    product_id: int = Field(..., description="상품 ID")
    product_title: str = Field(..., description="상품 제목")
    user_id: int = Field(..., description="제안자 ID")
    user_nickname: str = Field(..., description="제안자 닉네임")
    price: int = Field(..., description="제안 가격")
    status: str = Field(
        ..., description="상태 (pending: 대기중, accepted: 수락됨, rejected: 거절됨)"
    )
    created_at: str = Field(..., description="제안 일시")


class PriceOfferResponseSchema(Schema):
    """가격 제안 응답 스키마"""

    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: Optional[PriceOfferDetailSchema] = Field(None, description="가격 제안 정보")


class PriceOfferActionSchema(Schema):
    """가격 제안 응답 액션 스키마"""

    action: str = Field(..., description="액션 (accept: 수락, reject: 거절)")

    @validator("action")
    def validate_action(cls, v):
        if v not in ["accept", "reject"]:
            raise ValueError("액션은 'accept' 또는 'reject'만 가능합니다.")
        return v


# 거래 완료 관련 스키마
class TradeCompleteSchema(Schema):
    """거래 완료 스키마"""

    buyer_id: int = Field(..., description="구매자 ID")
    final_price: Optional[int] = Field(
        None, description="최종 거래 금액 (입력하지 않으면 원래 가격으로 적용)"
    )

    @validator("final_price")
    def validate_final_price(cls, v):
        if v is not None and v <= 0:
            raise ValueError("최종 가격은 0보다 커야 합니다.")
        return v


# 거래 후기 관련 스키마
class ReviewSchema(Schema):
    """거래 후기 스키마"""

    content: str = Field(..., description="후기 내용")

    @validator("content")
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError("후기 내용을 입력해주세요.")
        if len(v) > 500:
            raise ValueError("후기 내용은 500자 이내로 입력해주세요.")
        return v


class ReviewDetailSchema(Schema):
    """거래 후기 상세 스키마"""

    id: int = Field(..., description="후기 ID")
    product_id: int = Field(..., description="상품 ID")
    product_title: str = Field(..., description="상품 제목")
    reviewer_id: int = Field(..., description="작성자 ID")
    receiver_id: int = Field(..., description="수신자 ID")
    content: str = Field(..., description="후기 내용")
    created_at: str = Field(..., description="작성 일시")


class ReviewResponseSchema(Schema):
    """거래 후기 응답 스키마"""

    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: Optional[ReviewDetailSchema] = Field(None, description="거래 후기 정보")


# 매너 평가 타입을 위한 Enum 클래스 추가
class MannerRatingType(str, Enum):
    TIME = "time"
    RESPONSE = "response"
    KIND = "kind"
    ACCURATE = "accurate"
    NEGOTIABLE = "negotiable"
    BAD_TIME = "bad_time"
    BAD_RESPONSE = "bad_response"
    BAD_MANNER = "bad_manner"
    BAD_ACCURACY = "bad_accuracy"
    BAD_PRICE = "bad_price"


# 매너 평가 관련 스키마
class MannerRatingSchema(Schema):
    """매너평가 스키마"""

    rating_types: List[MannerRatingType] = Field(
        ..., description="평가 유형 목록", example=["time", "kind", "accurate"]
    )

    class Config:
        schema_extra = {"example": {"rating_types": ["time", "response", "kind"]}}

    @validator("rating_types")
    def validate_rating_types(cls, v):
        if not v:
            raise ValueError("최소 하나 이상의 평가 유형을 선택해주세요.")
        return v


class MannerRatingDetailSchema(Schema):
    """매너평가 상세 스키마"""

    product_id: int = Field(..., description="상품 ID")
    product_title: str = Field(..., description="상품 제목")
    rating_types: List[str] = Field(..., description="평가 유형 목록")
    created_at: str = Field(..., description="평가 일시")


class MannerRatingResponseSchema(Schema):
    """매너평가 응답 스키마"""

    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: Optional[MannerRatingDetailSchema] = Field(None, description="매너평가 정보")


class ProductInterestSchema(Schema):
    """상품 관심 등록/해제 요청 스키마"""

    # 추가 필드가 필요하다면 여기에 정의할 수 있습니다.
    # 현재는 빈 스키마로 정의하되, 추후 확장 가능성을 위해 클래스로 만듭니다.

    class Config:
        schema_extra = {"example": {}}  # 빈 예제로 시작


class PriceOfferListRequestSchema(Schema):
    """가격 제안 목록 요청 스키마"""

    # 향후 필터링 등의 옵션이 추가될 수 있으므로 스키마로 정의합니다.

    class Config:
        schema_extra = {"example": {}}
