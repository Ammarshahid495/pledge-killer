"""
Authentication and Session Service.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from ..core.config import settings
from ..core.security import (
    create_access_token,
    generate_secure_token,
    hash_password,
    hash_token,
    verify_password,
)
from ..models.user import RefreshSession, User
from ..schemas.auth import LoginRequest, RegisterRequest


class AuthService:
    @staticmethod
    def register_user(db: Session, req: RegisterRequest) -> User:
        existing = db.query(User).filter(User.email == req.email.lower()).first()
        if existing:
            raise ValueError("Email is already registered")

        pwd_hash = hash_password(req.password)
        user = User(
            email=req.email.lower(),
            display_name=req.display_name.strip(),
            password_hash=pwd_hash,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate_user(db: Session, req: LoginRequest) -> Tuple[User, str, str]:
        user = db.query(User).filter(User.email == req.email.lower()).first()
        if not user or not verify_password(req.password, user.password_hash):
            raise ValueError("Invalid email or password")

        if not user.is_active:
            raise ValueError("Account is inactive")

        # Generate tokens
        access_token = create_access_token(user.id)
        raw_refresh_token = generate_secure_token(48)
        refresh_hash = hash_token(raw_refresh_token)

        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        session = RefreshSession(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=expires_at,
        )
        db.add(session)
        db.commit()

        return user, access_token, raw_refresh_token

    @staticmethod
    def refresh_session(db: Session, raw_refresh_token: str) -> Tuple[User, str, str]:
        token_hash = hash_token(raw_refresh_token)
        session = db.query(RefreshSession).filter(RefreshSession.token_hash == token_hash).first()

        now = datetime.now(timezone.utc)
        if not session or session.revoked_at is not None:
            raise ValueError("Invalid or expired refresh token")

        expires_at = session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < now:
            raise ValueError("Invalid or expired refresh token")

        user = db.query(User).filter(User.id == session.user_id, User.is_active == True).first()
        if not user:
            raise ValueError("User not found or inactive")

        # Revoke old refresh session (rotation)
        session.revoked_at = now

        # Create new pair
        new_access_token = create_access_token(user.id)
        new_raw_refresh = generate_secure_token(48)
        new_refresh_hash = hash_token(new_raw_refresh)

        new_expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        new_session = RefreshSession(
            user_id=user.id,
            token_hash=new_refresh_hash,
            expires_at=new_expires_at,
        )
        db.add(new_session)
        db.commit()

        return user, new_access_token, new_raw_refresh

    @staticmethod
    def logout_session(db: Session, raw_refresh_token: str) -> bool:
        token_hash = hash_token(raw_refresh_token)
        session = db.query(RefreshSession).filter(RefreshSession.token_hash == token_hash).first()
        if session:
            session.revoked_at = datetime.now(timezone.utc)
            db.commit()
            return True
        return False
