"""Auth utilities — password hashing, JWT creation/verification, FastAPI dependency."""
from __future__ import annotations

from datetime import datetime, timedelta, UTC
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from db_models import User

# ── Password hashing ──────────────────────────────────────────────────────────

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _safe_truncate(plain: str) -> str:
    """Bcrypt silently truncates at 72 bytes; passlib raises ValueError in some builds.
    Truncate explicitly to avoid the bug."""
    encoded = plain.encode("utf-8")
    return encoded[:72].decode("utf-8", errors="ignore")

def hash_password(plain: str) -> str:
    return _pwd_context.hash(_safe_truncate(plain))

def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(_safe_truncate(plain), hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────

_ALGORITHM = "HS256"
_bearer = HTTPBearer(auto_error=False)


def create_access_token(user_id: int, expires_minutes: int = 60 * 24 * 7) -> str:
    """Create a JWT that expires in 7 days by default."""
    expire = datetime.now(UTC) + timedelta(minutes=expires_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=_ALGORITHM)


def _decode_token(token: str) -> int:
    """Decode JWT and return user_id. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[_ALGORITHM])
        user_id = int(payload["sub"])
        return user_id
    except (JWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── FastAPI Dependencies ───────────────────────────────────────────────────────

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Dependency: require a valid JWT, return the User object."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = _decode_token(credentials.credentials)
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    return user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency: require admin role."""
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return current_user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Dependency: return User if authenticated, None otherwise (for optional auth)."""
    if credentials is None:
        return None
    try:
        user_id = _decode_token(credentials.credentials)
        return db.query(User).filter(User.id == user_id, User.is_active == True).first()
    except HTTPException:
        return None
