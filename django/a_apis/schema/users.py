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
    """기본 응답 스키마

    예시:
    {
        "success": true,
        "message": "회원가입이 완료되었습니다.",
        "data": {
            "id": 1,
            "email": "user@example.com",
            "nickname": "사용자"
        },
        "tokens": {
            "access": "eyJ0eXA...",
            "refresh": "eyJ0eXA..."
        }
    }
    """

    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    tokens: Optional[TokenSchema] = None


# AuthResponseSchema와 ErrorResponseSchema를 BaseResponseSchema로 통일
AuthResponseSchema = BaseResponseSchema
ErrorResponseSchema = BaseResponseSchema


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
