from typing import Optional

from ninja import Schema


class TokenSchema(Schema):
    access: str
    refresh: str


class UserSchema(Schema):
    email: str
    username: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = None
    is_email_verified: Optional[bool] = None
    is_social_login: Optional[bool] = None


class SocialLoginResponseSchema(Schema):
    success: bool
    message: str
    tokens: TokenSchema
    user: UserSchema
    redirect_url: str
