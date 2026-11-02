"""
User Profile and Account Update Schemas.
"""

from pydantic import BaseModel, EmailStr, Field


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    display_name: str
    is_active: bool


class UserUpdate(BaseModel):
    display_name: str = Field(..., min_length=2, max_length=100)


class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
