from typing import Optional

from ninja import Schema
from pydantic import EmailStr, field_validator, model_validator


class EmailVerificationRequestSchema(Schema):
    email: str


class SignupSchema(Schema):
    username: str
    password: Optional[str] = None
    phone_number: str
    email: str


class LoginSchema(Schema):
    email: str
    password: str


class TokenSchema(Schema):
    access: str
    refresh: str


class UserSchema(Schema):
    email: str


class UserResponseSchema(Schema):
    email: str
    username: str
    phone_number: str
    is_active: bool


class AuthResponseSchema(Schema):
    success: bool
    message: str
    tokens: Optional[TokenSchema] = None
    user: Optional[UserResponseSchema] = None


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


class ErrorResponseSchema(Schema):
    success: bool
    message: Optional[str] = None


class UpdateProfileSchema(Schema):
    username: Optional[str] = None
    password: Optional[str] = None
    phone_number: Optional[str] = None
