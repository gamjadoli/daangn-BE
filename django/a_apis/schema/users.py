from typing import Any, Dict, Optional

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


class UserSchema(Schema):
    email: EmailStr = Field(..., description="사용자 이메일")
    nickname: str = Field(..., description="닉네임")
    phone_number: str = Field(..., description="휴대폰 번호")
    rating_score: float = Field(..., description="매너온도 (36.5°C 기본값)")
    is_activated: bool = Field(..., description="계정 활성화 상태")
    is_email_verified: bool = Field(..., description="이메일 인증 완료 여부")
    profile_img_url: Optional[str] = Field(None, description="프로필 이미지 URL")


class UserResponseSchema(Schema):
    email: EmailStr = Field(..., description="사용자 이메일")
    nickname: str = Field(..., description="닉네임")
    phone_number: str = Field(..., description="휴대폰 번호")
    is_activated: bool = Field(..., description="계정 활성화 상태")
    is_email_verified: bool = Field(..., description="이메일 인증 완료 여부")
    rating_score: float = Field(..., description="매너온도 (36.5°C 기본값)")
    profile_img_url: Optional[str] = Field(None, description="프로필 이미지 URL")


class BaseResponseSchema(Schema):
    """기본 응답 스키마"""

    success: bool = Field(..., description="요청 성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: Optional[Dict[str, Any]] = Field(None, description="응답 데이터")


class AuthResponseSchema(BaseResponseSchema):
    """인증 응답 스키마 (로그인/회원가입)"""

    tokens: TokenSchema = Field(..., description="인증 토큰")


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
    password: Optional[str] = Field(None, description="변경할 비밀번호")
    phone_number: Optional[str] = Field(None, description="변경할 휴대폰 번호")
