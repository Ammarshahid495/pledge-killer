"""
Authentication API Endpoints.
"""

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...models.user import User
from ...schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserProfileResponse
from ...schemas.common import ApiErrorDetail, ApiResponse
from ...services.auth_service import AuthService
from ..deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=ApiResponse[UserProfileResponse])
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    try:
        user = AuthService.register_user(db, req)
        return ApiResponse(
            success=True,
            data=UserProfileResponse(
                id=user.id,
                email=user.email,
                display_name=user.display_name,
                is_active=user.is_active,
            ),
            message="Registration successful",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "REGISTRATION_FAILED", "message": str(e)},
        )


@router.post("/login", response_model=ApiResponse[TokenResponse])
def login(req: LoginRequest, response: Response, db: Session = Depends(get_db)):
    try:
        user, access_token, refresh_token = AuthService.authenticate_user(db, req)

        # Set secure HttpOnly cookie for refresh token
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,  # Set to True in HTTPS production
            samesite="lax",
            max_age=14 * 24 * 3600,
        )

        return ApiResponse(
            success=True,
            data=TokenResponse(
                access_token=access_token,
                token_type="bearer",
                refresh_token=refresh_token,
                user_id=user.id,
                display_name=user.display_name,
                email=user.email,
            ),
            message="Login successful",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "LOGIN_FAILED", "message": str(e)},
        )


@router.post("/refresh", response_model=ApiResponse[TokenResponse])
def refresh(
    req: RefreshRequest,
    response: Response,
    refresh_token_cookie: str = Cookie(None, alias="refresh_token"),
    db: Session = Depends(get_db),
):
    token = req.refresh_token or refresh_token_cookie
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "MISSING_REFRESH_TOKEN", "message": "No refresh token provided"},
        )

    try:
        user, new_access, new_refresh = AuthService.refresh_session(db, token)

        response.set_cookie(
            key="refresh_token",
            value=new_refresh,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=14 * 24 * 3600,
        )

        return ApiResponse(
            success=True,
            data=TokenResponse(
                access_token=new_access,
                token_type="bearer",
                refresh_token=new_refresh,
                user_id=user.id,
                display_name=user.display_name,
                email=user.email,
            ),
            message="Token refreshed successfully",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_REFRESH_TOKEN", "message": str(e)},
        )


@router.post("/logout", response_model=ApiResponse[dict])
def logout(
    req: RefreshRequest,
    response: Response,
    refresh_token_cookie: str = Cookie(None, alias="refresh_token"),
    db: Session = Depends(get_db),
):
    token = req.refresh_token or refresh_token_cookie
    if token:
        AuthService.logout_session(db, token)

    response.delete_cookie(key="refresh_token")
    return ApiResponse(success=True, data={}, message="Logged out successfully")


@router.get("/me", response_model=ApiResponse[UserProfileResponse])
def get_me(current_user: User = Depends(get_current_user)):
    return ApiResponse(
        success=True,
        data=UserProfileResponse(
            id=current_user.id,
            email=current_user.email,
            display_name=current_user.display_name,
            is_active=current_user.is_active,
        ),
        message="Current user profile retrieved",
    )
