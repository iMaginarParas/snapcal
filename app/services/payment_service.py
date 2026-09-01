import hmac
import hashlib
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
import logging

from app.core.config import settings
from app.database.supabase import supabase_client, is_supabase_live
from app.schemas.payments import (
    PaymentPlan,
    CreateOrderResponse,
    VerifyPaymentResponse,
    SubscriptionStatusResponse,
    ApplyPromoResponse,
)

logger = logging.getLogger(__name__)

# Plan Catalog
PLANS_CATALOG: Dict[str, PaymentPlan] = {
    "monthly": PaymentPlan(
        id="monthly",
        name="Monthly Pro",
        duration_months=1,
        duration_days=30,
        price_inr=299,
        base_price_inr=299,
        discount_percent=0,
        per_month_price=299,
        description="Flexible monthly billing with full access to all features",
        features=[
            "Unlimited AI Food & Nutrition Vision Logging",
            "High-Resolution PDF Export Studio",
            "Complete Health & Fasting Analytics",
            "Custom Macro & Calorie Targets",
            "Priority Customer Support",
        ],
        badge=None,
        is_popular=False,
    ),
    "half_yearly": PaymentPlan(
        id="half_yearly",
        name="6 Months Pro",
        duration_months=6,
        duration_days=180,
        price_inr=1499,
        base_price_inr=1794,
        discount_percent=16,
        per_month_price=249,
        description="Commit to half-year fitness transformation",
        features=[
            "All Monthly Pro Features Included",
            "Save 16% compared to monthly plan",
            "Continuous Progress Tracking & Trends",
            "Early Access to New AI Features",
            "Priority Support & Cloud Backups",
        ],
        badge="POPULAR",
        is_popular=False,
    ),
    "yearly": PaymentPlan(
        id="yearly",
        name="Annual Pro Plan",
        duration_months=12,
        duration_days=365,
        price_inr=2799,
        base_price_inr=3588,
        discount_percent=22,
        per_month_price=233,
        description="Ultimate year-long health & fitness transformation",
        features=[
            "All Pro Features Unlocked for a Full Year",
            "Massive 22% Discount (Save ₹789)",
            "Only ₹233/month equivalent",
            "Unlimited Multi-Dish AI Vision Scans",
            "VIP Priority Customer Support",
            "All Future Pro Upgrades Included",
        ],
        badge="BEST VALUE",
        is_popular=True,
    ),
}

# In-memory fallback cache for development/mocking
_mock_subscriptions: Dict[str, Dict[str, Any]] = {}
_mock_payments: Dict[str, Dict[str, Any]] = {}


def get_razorpay_client():
    """Initializes and returns the Razorpay client if keys are configured."""
    key_id = settings.RAZORPAY_KEY_ID
    key_secret = settings.RAZORPAY_KEY_SECRET
    if not key_id or not key_secret:
        return None
    try:
        import razorpay
        return razorpay.Client(auth=(key_id, key_secret))
    except Exception as e:
        logger.warning(f"Failed to initialize razorpay client: {e}")
        return None


class PaymentService:
    @staticmethod
    def get_all_plans() -> List[PaymentPlan]:
        return list(PLANS_CATALOG.values())

    @staticmethod
    def get_plan(plan_id: str) -> Optional[PaymentPlan]:
        return PLANS_CATALOG.get(plan_id)

    @staticmethod
    def create_order(user_id: str, plan_id: str) -> CreateOrderResponse:
        plan = PLANS_CATALOG.get(plan_id)
        if not plan:
            raise ValueError(f"Invalid plan ID: {plan_id}. Available plans: {list(PLANS_CATALOG.keys())}")

        amount_paise = plan.price_inr * 100
        receipt_id = f"rcpt_{user_id[:8]}_{int(time.time())}"
        key_id = settings.RAZORPAY_KEY_ID or "rzp_test_mock_key"

        client = get_razorpay_client()
        order_id = None

        if client is not None:
            try:
                order_data = {
                    "amount": amount_paise,
                    "currency": "INR",
                    "receipt": receipt_id,
                    "notes": {
                        "user_id": user_id,
                        "plan_id": plan.id,
                        "plan_name": plan.name,
                    },
                }
                razorpay_order = client.order.create(data=order_data)
                order_id = razorpay_order.get("id")
            except Exception as e:
                logger.error(f"Razorpay order creation failed: {e}")
                # Fallback to deterministic mock order in case of sandbox/network issues
                order_id = f"order_{uuid.uuid4().hex[:16]}"
        else:
            logger.info("Razorpay keys not set; generating mock order ID for testing")
            order_id = f"order_{uuid.uuid4().hex[:16]}"

        # Record payment order in database
        try:
            if is_supabase_live():
                supabase_client.table("payments").insert({
                    "user_id": user_id,
                    "razorpay_order_id": order_id,
                    "plan_id": plan.id,
                    "amount": plan.price_inr,
                    "currency": "INR",
                    "status": "created",
                    "receipt": receipt_id,
                    "notes": {"user_id": user_id, "plan_id": plan.id},
                }).execute()
            else:
                _mock_payments[order_id] = {
                    "user_id": user_id,
                    "razorpay_order_id": order_id,
                    "plan_id": plan.id,
                    "amount": plan.price_inr,
                    "currency": "INR",
                    "status": "created",
                }
        except Exception as e:
            logger.warning(f"Error persisting payment order: {e}")

        return CreateOrderResponse(
            order_id=order_id,
            amount=amount_paise,
            currency="INR",
            key_id=key_id,
            plan_id=plan.id,
            plan_name=plan.name,
            amount_inr=plan.price_inr,
        )

    @staticmethod
    def verify_payment(
        user_id: str,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
        plan_id: str,
    ) -> VerifyPaymentResponse:
        plan = PLANS_CATALOG.get(plan_id)
        if not plan:
            raise ValueError(f"Invalid plan ID: {plan_id}")

        key_secret = settings.RAZORPAY_KEY_SECRET
        client = get_razorpay_client()

        # If Razorpay client and secret exist, verify signature
        if client and key_secret:
            try:
                # Razorpay verification
                generated_signature = hmac.new(
                    key_secret.encode(),
                    f"{razorpay_order_id}|{razorpay_payment_id}".encode(),
                    hashlib.sha256,
                ).hexdigest()

                if generated_signature != razorpay_signature:
                    # Also try client utility
                    try:
                        client.utility.verify_payment_signature({
                            "razorpay_order_id": razorpay_order_id,
                            "razorpay_payment_id": razorpay_payment_id,
                            "razorpay_signature": razorpay_signature,
                        })
                    except Exception:
                        raise ValueError("Payment signature verification failed")
            except Exception as e:
                logger.error(f"Signature verification error: {e}")
                raise ValueError(f"Payment verification failed: {e}")
        else:
            logger.info("Razorpay keys not configured; accepting mock signature in testing mode")

        # Calculate subscription dates
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=plan.duration_days)
        expires_at_iso = expires_at.isoformat()

        # Persist payment status update and subscription activation
        try:
            if is_supabase_live():
                # 1. Update payment record
                supabase_client.table("payments").update({
                    "razorpay_payment_id": razorpay_payment_id,
                    "razorpay_signature": razorpay_signature,
                    "status": "captured",
                    "updated_at": now.isoformat(),
                }).eq("razorpay_order_id", razorpay_order_id).execute()

                # 2. Insert active subscription record
                supabase_client.table("subscriptions").insert({
                    "user_id": user_id,
                    "plan_id": plan.id,
                    "plan_name": plan.name,
                    "amount": plan.price_inr,
                    "currency": "INR",
                    "status": "active",
                    "starts_at": now.isoformat(),
                    "expires_at": expires_at_iso,
                    "razorpay_order_id": razorpay_order_id,
                    "razorpay_payment_id": razorpay_payment_id,
                }).execute()

                # 3. Update public.users table
                supabase_client.table("users").update({
                    "is_pro": True,
                    "subscription_tier": "pro",
                    "subscription_plan_id": plan.id,
                    "subscription_expires_at": expires_at_iso,
                }).eq("id", user_id).execute()
            else:
                _mock_subscriptions[user_id] = {
                    "is_pro": True,
                    "subscription_tier": "pro",
                    "plan_id": plan.id,
                    "plan_name": plan.name,
                    "starts_at": now.isoformat(),
                    "expires_at": expires_at_iso,
                }
                if razorpay_order_id in _mock_payments:
                    _mock_payments[razorpay_order_id].update({
                        "razorpay_payment_id": razorpay_payment_id,
                        "razorpay_signature": razorpay_signature,
                        "status": "captured",
                    })
        except Exception as e:
            logger.error(f"Failed to persist subscription details: {e}")

        return VerifyPaymentResponse(
            success=True,
            message="Payment verified successfully! SABTRACK PRO is now active.",
            is_pro=True,
            subscription_tier="pro",
            plan_id=plan.id,
            plan_name=plan.name,
            expires_at=expires_at_iso,
        )

    @staticmethod
    def get_subscription_status(user_id: str) -> SubscriptionStatusResponse:
        try:
            if is_supabase_live():
                res = supabase_client.table("users").select(
                    "is_pro, subscription_tier, subscription_plan_id, subscription_expires_at, created_at"
                ).eq("id", user_id).execute()

                if res.data and len(res.data) > 0:
                    row = res.data[0]
                    expires_str = row.get("subscription_expires_at")
                    created_at_str = row.get("created_at")
                    plan_id = row.get("subscription_plan_id")
                    plan = PLANS_CATALOG.get(plan_id) if plan_id else None

                    now = datetime.now(timezone.utc)
                    is_active = False
                    days_remaining = 0
                    if expires_str:
                        expires_dt = datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
                        if expires_dt > now:
                            is_active = bool(row.get("is_pro", False))
                            days_remaining = max(0, (expires_dt - now).days)

                    # 7-day free trial calculation
                    is_trial_active = False
                    trial_days_remaining = 0
                    if created_at_str:
                        created_dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                        trial_ends_at = created_dt + timedelta(days=7)
                        if now < trial_ends_at:
                            is_trial_active = True
                            trial_days_remaining = max(1, (trial_ends_at - now).days + 1)

                    can_access_premium = is_active or is_trial_active

                    return SubscriptionStatusResponse(
                        is_pro=is_active,
                        subscription_tier="pro" if is_active else ("trial" if is_trial_active else "free"),
                        plan_id=plan_id if is_active else None,
                        plan_name=plan.name if (plan and is_active) else ("7-Day Free Trial" if is_trial_active else "Free Plan"),
                        expires_at=expires_str if is_active else None,
                        days_remaining=days_remaining,
                        is_active=is_active,
                        is_trial_active=is_trial_active,
                        trial_days_remaining=trial_days_remaining,
                        can_access_premium=can_access_premium,
                    )
        except Exception as e:
            logger.warning(f"Error fetching subscription status from Supabase: {e}")

        # Fallback to mock state if applicable
        mock_sub = _mock_subscriptions.get(user_id)
        if mock_sub and mock_sub.get("is_pro"):
            expires_str = mock_sub.get("expires_at")
            expires_dt = datetime.fromisoformat(expires_str)
            now = datetime.now(timezone.utc)
            days = max(0, (expires_dt - now).days)
            return SubscriptionStatusResponse(
                is_pro=True,
                subscription_tier="pro",
                plan_id=mock_sub.get("plan_id"),
                plan_name=mock_sub.get("plan_name"),
                starts_at=mock_sub.get("starts_at"),
                expires_at=expires_str,
                days_remaining=days,
                is_active=True,
                is_trial_active=False,
                trial_days_remaining=0,
                can_access_premium=True,
            )

        # Default local trial fallback (7 days free trial for new installs)
        return SubscriptionStatusResponse(
            is_pro=False,
            subscription_tier="trial",
            plan_id=None,
            plan_name="7-Day Free Trial",
            days_remaining=0,
            is_active=False,
            is_trial_active=True,
            trial_days_remaining=7,
            can_access_premium=True,
        )

    @staticmethod
    def apply_promo_code(user_id: str, promo_code: str) -> ApplyPromoResponse:
        code_clean = promo_code.strip().upper()
        if code_clean != "VIGATRON100":
            raise ValueError(f"Invalid promo code: '{promo_code}'. Please enter a valid coupon code.")

        now = datetime.now(timezone.utc)
        # Give 365 days of full VIP Pro access
        expires_at = now + timedelta(days=365)
        expires_at_iso = expires_at.isoformat()

        try:
            if is_supabase_live():
                # 1. Update user profile to Pro
                supabase_client.table("users").update({
                    "is_pro": True,
                    "subscription_tier": "pro",
                    "subscription_plan_id": "yearly",
                    "subscription_expires_at": expires_at_iso,
                }).eq("id", user_id).execute()

                # 2. Record promo subscription
                supabase_client.table("subscriptions").insert({
                    "user_id": user_id,
                    "plan_id": "yearly",
                    "plan_name": "VIP Pro (Promo VIGATRON100)",
                    "amount": 0,
                    "currency": "INR",
                    "status": "active",
                    "starts_at": now.isoformat(),
                    "expires_at": expires_at_iso,
                    "razorpay_order_id": "promo_vigatron100",
                    "razorpay_payment_id": "promo_100_free",
                }).execute()
            else:
                _mock_subscriptions[user_id] = {
                    "is_pro": True,
                    "subscription_tier": "pro",
                    "plan_id": "yearly",
                    "plan_name": "VIP Pro (Promo VIGATRON100)",
                    "starts_at": now.isoformat(),
                    "expires_at": expires_at_iso,
                }
        except Exception as e:
            logger.error(f"Error activating promo code: {e}")

        return ApplyPromoResponse(
            success=True,
            message="🎉 Promo Code VIGATRON100 Applied! 100% OFF — All Pro features are now unlocked for free.",
            is_pro=True,
            subscription_tier="pro",
            plan_id="yearly",
            plan_name="VIP Pro (Promo VIGATRON100)",
            expires_at=expires_at_iso,
            discount_percent=100,
        )
