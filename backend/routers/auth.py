"""Auth router — signup, login, me, logout."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from auth import create_access_token, hash_password, verify_password, get_current_user
from database import get_db
from db_models import User, Subscription

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str = ""


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    full_name: str
    plan: str
    is_admin: bool


class MeResponse(BaseModel):
    user_id: int
    email: str
    full_name: str
    plan: str
    is_admin: bool
    audits_this_month: int
    qa_this_month: int


# ── Helpers ───────────────────────────────────────────────────────────────────

_PLAN_LIMITS = {
    "free":       {"audit": 3,   "qa": 10},
    "pro":        {"audit": 50,  "qa": 999999},
    "enterprise": {"audit": 999999, "qa": 999999},
}

def _get_plan(user: User) -> str:
    if user.subscription:
        return user.subscription.plan
    return "free"

def _usage_this_month(db: Session, user_id: int, action: str) -> int:
    from datetime import datetime
    month = datetime.now().strftime("%Y-%m")
    from db_models import UsageRecord
    rec = db.query(UsageRecord).filter_by(user_id=user_id, action=action, month=month).first()
    return rec.count if rec else 0


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(body: SignupRequest, db: Session = Depends(get_db)) -> TokenResponse:
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="Email already registered.")

    if len(body.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters.")

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
    )
    db.add(user)
    db.flush()  # get user.id before adding subscription

    sub = Subscription(user_id=user.id, plan="free")
    db.add(sub)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name or "",
        plan="free",
        is_admin=user.is_admin,
    )


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated.")

    token = create_access_token(user.id)
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name or "",
        plan=_get_plan(user),
        is_admin=user.is_admin,
    )


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MeResponse:
    return MeResponse(
        user_id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name or "",
        plan=_get_plan(current_user),
        is_admin=current_user.is_admin,
        audits_this_month=_usage_this_month(db, current_user.id, "audit"),
        qa_this_month=_usage_this_month(db, current_user.id, "qa"),
    )
