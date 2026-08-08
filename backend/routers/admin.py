"""Admin router — user management, usage stats, audit report list."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import get_current_admin
from database import get_db
from db_models import Subscription, UsageRecord, User

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class UserSummary(BaseModel):
    user_id: int
    email: str
    full_name: str
    plan: str
    is_active: bool
    is_admin: bool
    audits_this_month: int
    qa_this_month: int
    joined: str


class DashboardStats(BaseModel):
    total_users: int
    active_users: int
    free_users: int
    pro_users: int
    enterprise_users: int
    total_audits_this_month: int
    total_qa_this_month: int


# ── Helpers ───────────────────────────────────────────────────────────────────

def _current_month() -> str:
    return datetime.now().strftime("%Y-%m")

def _usage(db: Session, user_id: int, action: str) -> int:
    rec = db.query(UsageRecord).filter_by(
        user_id=user_id, action=action, month=_current_month()
    ).first()
    return rec.count if rec else 0

def _get_plan(user: User) -> str:
    return user.subscription.plan if user.subscription else "free"


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/stats", response_model=DashboardStats)
def get_stats(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> DashboardStats:
    month = _current_month()
    total = db.query(func.count(User.id)).scalar()
    active = db.query(func.count(User.id)).filter(User.is_active == True).scalar()

    plan_counts = dict(
        db.query(Subscription.plan, func.count(Subscription.id))
        .group_by(Subscription.plan)
        .all()
    )

    audits = db.query(func.sum(UsageRecord.count)).filter_by(action="audit", month=month).scalar() or 0
    qas = db.query(func.sum(UsageRecord.count)).filter_by(action="qa", month=month).scalar() or 0

    return DashboardStats(
        total_users=total,
        active_users=active,
        free_users=plan_counts.get("free", 0),
        pro_users=plan_counts.get("pro", 0),
        enterprise_users=plan_counts.get("enterprise", 0),
        total_audits_this_month=audits,
        total_qa_this_month=qas,
    )


@router.get("/users", response_model=list[UserSummary])
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> list[UserSummary]:
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [
        UserSummary(
            user_id=u.id,
            email=u.email,
            full_name=u.full_name or "",
            plan=_get_plan(u),
            is_active=u.is_active,
            is_admin=u.is_admin,
            audits_this_month=_usage(db, u.id, "audit"),
            qa_this_month=_usage(db, u.id, "qa"),
            joined=u.created_at.strftime("%Y-%m-%d"),
        )
        for u in users
    ]


@router.patch("/users/{user_id}/plan")
def update_plan(
    user_id: int,
    plan: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> dict:
    if plan not in ("free", "pro", "enterprise"):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid plan.")
    sub = db.query(Subscription).filter_by(user_id=user_id).first()
    if sub:
        sub.plan = plan
    else:
        db.add(Subscription(user_id=user_id, plan=plan))
    db.commit()
    return {"success": True, "user_id": user_id, "plan": plan}


@router.patch("/users/{user_id}/deactivate")
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> dict:
    user = db.query(User).filter_by(id=user_id).first()
    if user:
        user.is_active = False
        db.commit()
    return {"success": True, "user_id": user_id}
