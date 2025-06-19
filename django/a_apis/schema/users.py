from typing import Any, Dict, List, Optional

from ninja import Field, Schema
from pydantic import EmailStr, field_validator, model_validator


class EmailVerificationRequestSchema(Schema):
    email: EmailStr = Field(..., description="인증할 이메일 주소")


class SignupSchema(Schema):
    """회원가입 요청 스키마"""

    email: EmailStr = Field(..., description="사용자 이메일 주소")
    password: str = Field(..., description="비밀번호")
    nickname: str = Field(..., description="사용자 닉네임")
    phone_number: str = Field(..., description="휴대폰 번호 (예: 01012345678)")
    latitude: float = Field(..., description="위도 좌표 (현재 위치)")
    longitude: float = Field(..., description="경도 좌표 (현재 위치)")


class LoginSchema(Schema):
    email: EmailStr = Field(..., description="사용자 이메일")
    password: str = Field(..., description="비밀번호")


class TokenSchema(Schema):
    """토큰 스키마"""

    access: str = Field(..., description="액세스 토큰 (API 요청에 사용)")
    refresh: str = Field(..., description="리프레시 토큰 (토큰 갱신에 사용)")


class RegionSchema(Schema):
    """동네 정보 스키마"""

    id: int = Field(..., description="동네 ID")
    name: str = Field(..., description="동네명")
    code: str = Field(..., description="행정구역 코드")
    priority: int = Field(
        ..., description="동네 순서 (1: 대표 동네, 2: 두번째 동네, 3: 세번째 동네)"
    )
    latitude: Optional[float] = Field(None, description="위도 좌표")
    longitude: Optional[float] = Field(None, description="경도 좌표")


class ActiveRegionResponseSchema(Schema):
    """활성 동네 변경 응답 스키마"""

    success: bool = Field(..., description="요청 성공 여부")
    message: str = Field(..., description="응답 메시지")
    current_region: Optional[RegionSchema] = Field(
        None, description="현재 활성화된 동네 정보"
    )


class UserSchema(Schema):
    id: int = Field(..., description="사용자 ID")
    email: EmailStr = Field(..., description="사용자 이메일")
    nickname: str = Field(..., description="닉네임")
    phone_number: str = Field(..., description="휴대폰 번호")
    rating_score: float = Field(..., description="매너온도 (36.5°C 기본값)")
    is_activated: bool = Field(..., description="계정 활성화 상태")
    is_email_verified: bool = Field(..., description="이메일 인증 완료 여부")
    profile_img_url: Optional[str] = Field(None, description="프로필 이미지 URL")
    regions: List[RegionSchema] = Field([], description="인증한 동네 목록")
    current_region: Optional[RegionSchema] = Field(None, description="현재 선택한 동네")


class UserResponseSchema(Schema):
    id: int = Field(..., description="사용자 ID")
    email: EmailStr = Field(..., description="사용자 이메일")
    nickname: str = Field(..., description="닉네임")
    phone_number: str = Field(..., description="휴대폰 번호")
    is_activated: bool = Field(..., description="계정 활성화 상태")
    is_email_verified: bool = Field(..., description="이메일 인증 완료 여부")
    rating_score: float = Field(..., description="매너온도 (36.5°C 기본값)")
    profile_img_url: Optional[str] = Field(None, description="프로필 이미지 URL")
    regions: List[RegionSchema] = Field([], description="인증한 동네 목록")
    current_region: Optional[RegionSchema] = Field(None, description="현재 선택한 동네")


class BaseResponseSchema(Schema):
    """기본 응답 스키마"""

    success: bool = Field(..., description="요청 성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: Optional[Dict[str, Any]] = Field(None, description="응답 데이터")


class AuthResponseSchema(BaseResponseSchema):
    """인증 응답 스키마 (로그인/회원가입)"""

    tokens: Optional[TokenSchema] = Field(
        None, description="인증 토큰 (성공 시에만 제공)"
    )
    user: Optional[UserResponseSchema] = Field(
        None, description="사용자 정보 (성공 시에만 제공)"
    )


class ErrorResponseSchema(BaseResponseSchema):
    """단순 응답 스키마 (이메일 인증, 오류 등)"""

    # BaseResponseSchema 필드만 사용 (tokens 없음)
    pass


class RefreshTokenSchema(Schema):
    refresh: str = Field(..., description="리프레시 토큰")


class TokenResponseSchema(Schema):
    success: bool = Field(..., description="요청 성공 여부")
    message: str = Field(..., description="응답 메시지")
    tokens: Optional[TokenSchema] = Field(None, description="인증 토큰")


class WithdrawalSchema(Schema):
    password: str = Field(..., description="비밀번호")


class EmailVerificationSchema(Schema):
    email: EmailStr = Field(..., description="이메일 주소")
    code: str = Field(..., description="인증 코드 (6자리)")

    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        if not v or len(v) != 6:
            raise ValueError("유효하지 않은 인증코드입니다 (길이가 6자여야 함)")
        return v


class LogoutSchema(Schema):
    refresh_token: str = Field(..., description="리프레시 토큰")


class UpdateProfileSchema(Schema):
    nickname: Optional[str] = Field(None, description="변경할 닉네임")
    phone_number: Optional[str] = Field(None, description="변경할 휴대폰 번호")
    remove_profile_image: Optional[bool] = Field(
        False, description="프로필 이미지 삭제 여부"
    )


class PasswordChangeSchema(Schema):
    """비밀번호 변경 스키마"""

    current_password: str = Field(..., description="현재 비밀번호")
    new_password: str = Field(..., description="새 비밀번호")


# 유저 프로필 조회 관련 스키마 추가
class TopMannerRatingSchema(Schema):
    """상위 매너 평가 스키마"""

    rating_type: str = Field(..., description="평가 유형")
    rating_name: str = Field(..., description="평가명")
    count: int = Field(..., description="받은 횟수")


class RecentReviewSchema(Schema):
    """최근 거래후기 스키마"""

    reviewer_nickname: str = Field(..., description="후기 작성자 닉네임")
    reviewer_profile_img_url: Optional[str] = Field(
        None, description="작성자 프로필 이미지 URL"
    )
    reviewer_role: str = Field(..., description="작성자 역할 (buyer/seller)")
    reviewer_region: Optional[str] = Field(None, description="작성자 대표 동네")
    content: str = Field(..., description="후기 내용")
    created_at: str = Field(..., description="후기 작성일")


class UserProfileSchema(Schema):
    """유저 프로필 스키마"""

    id: int = Field(..., description="사용자 ID")
    created_at: str = Field(..., description="계정 생성일")
    email: EmailStr = Field(..., description="사용자 이메일")
    nickname: str = Field(..., description="닉네임")
    phone_number: str = Field(..., description="휴대폰 번호")
    is_activated: bool = Field(..., description="계정 활성화 상태")
    is_email_verified: bool = Field(..., description="이메일 인증 완료 여부")
    rating_score: float = Field(..., description="매너온도")
    profile_img_url: Optional[str] = Field(None, description="프로필 이미지 URL")
    selling_products_count: int = Field(..., description="현재 판매 중인 상품 수")
    top_manner_ratings: List[TopMannerRatingSchema] = Field(
        ..., description="가장 많이 받은 매너 평가 상위 3개"
    )
    total_review_count: int = Field(..., description="받은 거래후기 총 개수")
    recent_reviews: List[RecentReviewSchema] = Field(
        ..., description="최근 거래후기 3개"
    )


class UserProfileResponseSchema(Schema):
    """유저 프로필 조회 응답 스키마"""

    success: bool = Field(..., description="요청 성공 여부")
    message: str = Field(..., description="응답 메시지")
    user: Optional[UserProfileSchema] = Field(None, description="유저 프로필 정보")


# 매너평가 상세 조회 관련 스키마
class DetailedMannerRatingSchema(Schema):
    """상세 매너 평가 스키마"""

    rating_type: str = Field(..., description="평가 유형")
    rating_name: str = Field(..., description="평가명")
    count: int = Field(..., description="받은 횟수")


class PositiveMannerRatingsSchema(Schema):
    """긍정적 매너평가 응답 스키마"""

    total_count: int = Field(..., description="긍정적 평가 총 개수")
    ratings: List[DetailedMannerRatingSchema] = Field(
        ..., description="긍정적 매너평가 목록"
    )


class NegativeMannerRatingsSchema(Schema):
    """부정적 매너평가 응답 스키마"""

    total_count: int = Field(..., description="부정적 평가 총 개수")
    ratings: List[DetailedMannerRatingSchema] = Field(
        ..., description="부정적 매너평가 목록"
    )


class MannerRatingsDetailResponseSchema(Schema):
    """매너평가 상세 조회 응답 스키마"""

    success: bool = Field(..., description="요청 성공 여부")
    message: str = Field(..., description="응답 메시지")
    positive_ratings: Optional[PositiveMannerRatingsSchema] = Field(
        None, description="긍정적 매너평가"
    )
    negative_ratings: Optional[NegativeMannerRatingsSchema] = Field(
        None, description="부정적 매너평가"
    )


# 거래후기 상세 조회 관련 스키마
class DetailedReviewSchema(Schema):
    """상세 거래후기 스키마"""

    id: int = Field(..., description="후기 ID")
    reviewer_nickname: str = Field(..., description="후기 작성자 닉네임")
    reviewer_profile_img_url: Optional[str] = Field(
        None, description="작성자 프로필 이미지 URL"
    )
    reviewer_role: str = Field(..., description="작성자 역할 (buyer/seller)")
    reviewer_region: Optional[str] = Field(None, description="작성자 대표 동네")
    product_title: str = Field(..., description="거래 상품명")
    trade_date: str = Field(..., description="거래 날짜")
    content: str = Field(..., description="후기 내용")
    created_at: str = Field(..., description="후기 작성일")


class ReviewsDetailResponseSchema(Schema):
    """거래후기 상세 조회 응답 스키마"""

    success: bool = Field(..., description="요청 성공 여부")
    message: str = Field(..., description="응답 메시지")
    total_count: Optional[int] = Field(None, description="총 후기 개수")
    reviews: Optional[List[DetailedReviewSchema]] = Field(
        None, description="거래후기 목록"
    )
    page: Optional[int] = Field(None, description="현재 페이지")
    page_size: Optional[int] = Field(None, description="페이지 크기")
    total_pages: Optional[int] = Field(None, description="총 페이지 수")
