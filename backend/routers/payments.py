"""Payments router — Razorpay order creation and webhook verification."""
from __future__ import annotations

import hashlib
import hmac
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import get_current_user
from config import settings
from database import get_db
from db_models import Subscription, User

router = APIRouter(prefix="/api/payments", tags=["payments"])
logger = logging.getLogger(__name__)


# ── Plan config ───────────────────────────────────────────────────────────────

PLANS = {
    "pro": {
        "name": "LexAudit Pro",
        "price_inr": 99900,   # paise (₹999)
        "description": "50 audits/month, unlimited Q&A",
    },
    "enterprise": {
        "name": "LexAudit Enterprise",
        "price_inr": 499900,  # paise (₹4999)
        "description": "Unlimited everything, priority support",
    },
}


# ── Schemas ───────────────────────────────────────────────────────────────────

class CreateOrderRequest(BaseModel):
    plan: str  # "pro" | "enterprise"


class CreateOrderResponse(BaseModel):
    order_id: str
    amount: int
    currency: str
    key_id: str
    plan: str


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    plan: str


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/plans")
def list_plans() -> dict:
    """Public — return plan details for the pricing page."""
    return {
        "free": {"name": "Free", "price_inr": 0, "description": "3 audits/month, 10 Q&A/month"},
        **PLANS,
    }


@router.post("/create-order", response_model=CreateOrderResponse)
def create_order(
    body: CreateOrderRequest,
    current_user: User = Depends(get_current_user),
) -> CreateOrderResponse:
    if body.plan not in PLANS:
        raise HTTPException(status_code=400, detail=f"Unknown plan: {body.plan}")

    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        raise HTTPException(status_code=503, detail="Payment service not configured.")

    try:
        import razorpay  # lazy import — not installed in dev without key
        client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
        plan_info = PLANS[body.plan]
        order = client.order.create({
            "amount": plan_info["price_inr"],
            "currency": "INR",
            "receipt": f"lexaudit_{current_user.id}_{body.plan}",
            "notes": {"user_id": current_user.id, "plan": body.plan},
        })
    except ImportError:
        raise HTTPException(status_code=503, detail="razorpay package not installed.")
    except Exception as e:
        logger.exception("Razorpay order creation failed: %s", e)
        raise HTTPException(status_code=502, detail=str(e))

    return CreateOrderResponse(
        order_id=order["id"],
        amount=order["amount"],
        currency=order["currency"],
        key_id=settings.razorpay_key_id,
        plan=body.plan,
    )


@router.post("/verify")
def verify_payment(
    body: VerifyPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Verify Razorpay payment signature and upgrade user's plan."""
    if not settings.razorpay_key_secret:
        raise HTTPException(status_code=503, detail="Payment service not configured.")

    # Signature verification
    expected = hmac.new(
        settings.razorpay_key_secret.encode(),
        f"{body.razorpay_order_id}|{body.razorpay_payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, body.razorpay_signature):
        raise HTTPException(status_code=400, detail="Invalid payment signature.")

    # Upgrade subscription
    sub = db.query(Subscription).filter_by(user_id=current_user.id).first()
    if sub:
        sub.plan = body.plan
        sub.razorpay_subscription_id = body.razorpay_payment_id
        sub.status = "active"
        sub.expires_at = datetime.now() + timedelta(days=30)
    else:
        sub = Subscription(
            user_id=current_user.id,
            plan=body.plan,
            razorpay_subscription_id=body.razorpay_payment_id,
            status="active",
            expires_at=datetime.now() + timedelta(days=30),
        )
        db.add(sub)

    db.commit()
    logger.info("User %s upgraded to %s plan", current_user.email, body.plan)
    return {"success": True, "plan": body.plan}
