"""
User Account API Endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.security import hash_password, verify_password
from ...models.user import User
from ...schemas.common import ApiResponse
from ...schemas.user import PasswordUpdate, UserResponse, UserUpdate
from ..deps import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=ApiResponse[UserResponse])
def get_user_me(current_user: User = Depends(get_current_user)):
    return ApiResponse(
        success=True,
        data=UserResponse(
            id=current_user.id,
            email=current_user.email,
            display_name=current_user.display_name,
            is_active=current_user.is_active,
        ),
        message="Profile details",
    )


@router.patch("/me", response_model=ApiResponse[UserResponse])
def update_user_me(
    req: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.display_name = req.display_name.strip()
    db.commit()
    db.refresh(current_user)
    return ApiResponse(
        success=True,
        data=UserResponse(
            id=current_user.id,
            email=current_user.email,
            display_name=current_user.display_name,
            is_active=current_user.is_active,
        ),
        message="Profile updated successfully",
    )


@router.patch("/me/password", response_model=ApiResponse[dict])
def update_user_password(
    req: PasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(req.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_PASSWORD", "message": "Current password is incorrect"},
        )

    current_user.password_hash = hash_password(req.new_password)
    db.commit()
    return ApiResponse(success=True, data={}, message="Password changed successfully")
