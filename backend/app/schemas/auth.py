"""
Authentication Schemas.
"""

from typing import Optional
import email_validator
email_validator.CHECK_DELIVERABILITY = False

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    display_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None
    user_id: str
    display_name: str
    email: str


class UserProfileResponse(BaseModel):
    id: str
    email: str
    display_name: str
    is_active: bool
