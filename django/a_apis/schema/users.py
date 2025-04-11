from typing import Any, Dict, Optional

from ninja import Schema
from pydantic import EmailStr, field_validator, model_validator


class EmailVerificationRequestSchema(Schema):
    email: EmailStr


class SignupSchema(Schema):
    email: EmailStr
    password: str
    nickname: str
    phone_number: str
    latitude: float
    longitude: float


class LoginSchema(Schema):
    email: EmailStr
    password: str


class TokenSchema(Schema):
    """토큰 스키마"""

    access: str
    refresh: str


class UserSchema(Schema):
    email: EmailStr
    nickname: str
    phone_number: str
    rating_score: float
    is_activated: bool
    is_email_verified: bool
    profile_img_url: Optional[str] = None


class UserResponseSchema(Schema):
    email: EmailStr
    nickname: str
    phone_number: str
    is_activated: bool
    is_email_verified: bool
    rating_score: float
    profile_img_url: Optional[str] = None


class BaseResponseSchema(Schema):
    """기본 응답 스키마"""

    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class AuthResponseSchema(BaseResponseSchema):
    """인증 응답 스키마 (로그인/회원가입)"""

    tokens: TokenSchema


class ErrorResponseSchema(BaseResponseSchema):
    """단순 응답 스키마 (이메일 인증, 오류 등)"""

    # BaseResponseSchema 필드만 사용 (tokens 없음)
    pass


class RefreshTokenSchema(Schema):
    refresh: str


class TokenResponseSchema(Schema):
    success: bool
    message: str
    tokens: Optional[TokenSchema] = None


class WithdrawalSchema(Schema):
    password: str


class EmailVerificationSchema(Schema):
    email: EmailStr
    code: str

    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        if not v or len(v) != 6:
            raise ValueError("유효하지 않은 인증코드입니다 (길이가 6자여야 함)")
        return v


class LogoutSchema(Schema):
    refresh_token: str


class UpdateProfileSchema(Schema):
    nickname: Optional[str] = None
    password: Optional[str] = None
    phone_number: Optional[str] = None
