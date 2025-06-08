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


# 거래 후기 관련 스키마 추가
class ReviewerSchema(Schema):
    """후기 작성자 정보 스키마"""

    id: int = Field(..., description="작성자 ID")
    nickname: str = Field(..., description="닉네임")
    profile_img_url: Optional[str] = Field(None, description="프로필 이미지 URL")
    location: Optional[str] = Field(None, description="인증한 동네")


class ReceivedReviewSchema(Schema):
    """받은 거래 후기 스키마"""

    id: int = Field(..., description="후기 ID")
    product_id: int = Field(..., description="상품 ID")
    product_title: str = Field(..., description="상품 제목")
    content: str = Field(..., description="후기 내용")
    created_at: str = Field(..., description="작성 일시")
    reviewer: ReviewerSchema = Field(..., description="작성자 정보")


class ReceivedReviewsResponseSchema(Schema):
    """받은 거래 후기 응답 스키마"""

    success: bool = Field(..., description="요청 성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: Optional[List[ReceivedReviewSchema]] = Field(
        None, description="받은 후기 목록"
    )
    total_count: Optional[int] = Field(None, description="총 후기 수")
    page: Optional[int] = Field(None, description="현재 페이지")
    page_size: Optional[int] = Field(None, description="페이지 크기")
    total_pages: Optional[int] = Field(None, description="총 페이지 수")


class ReceivedMannerRatingSchema(Schema):
    """받은 매너 평가 스키마"""

    id: int = Field(..., description="평가 ID")
    product_id: int = Field(..., description="상품 ID")
    product_title: str = Field(..., description="상품 제목")
    rating_type: str = Field(..., description="평가 유형")
    rating_display: str = Field(..., description="평가 표시명")
    created_at: str = Field(..., description="작성 일시")
    rater: ReviewerSchema = Field(..., description="평가자 정보")


class ReceivedMannerRatingsResponseSchema(Schema):
    """받은 매너 평가 응답 스키마"""

    success: bool = Field(..., description="요청 성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: Optional[List[ReceivedMannerRatingSchema]] = Field(
        None, description="받은 매너 평가 목록"
    )
    total_count: Optional[int] = Field(None, description="총 매너 평가 수")
    page: Optional[int] = Field(None, description="현재 페이지")
    page_size: Optional[int] = Field(None, description="페이지 크기")
    total_pages: Optional[int] = Field(None, description="총 페이지 수")
