from fastapi import APIRouter, Depends, HTTPException, Request, Header
from typing import Optional
import logging

from app.core.dependencies import get_current_user_id
from app.core.config import settings
from app.schemas.payments import (
    PlansResponse,
    CreateOrderRequest,
    CreateOrderResponse,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
    SubscriptionStatusResponse,
    ApplyPromoRequest,
    ApplyPromoResponse,
)
from app.services.payment_service import PaymentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["Payments & Subscriptions"])


@router.get("/plans", response_model=PlansResponse)
def get_plans():
    """Retrieve all available SABTRACK Pro subscription plans."""
    plans = PaymentService.get_all_plans()
    return PlansResponse(
        plans=plans,
        currency="INR",
        razorpay_key_id=settings.RAZORPAY_KEY_ID or "rzp_test_mock",
    )


@router.post("/create-order", response_model=CreateOrderResponse)
def create_order(
    payload: CreateOrderRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Create a new Razorpay Order for a specific subscription plan."""
    try:
        order = PaymentService.create_order(user_id=user_id, plan_id=payload.plan_id)
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating payment order: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize payment order")


@router.post("/verify", response_model=VerifyPaymentResponse)
def verify_payment(
    payload: VerifyPaymentRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Verify Razorpay payment signature and activate Pro subscription."""
    try:
        res = PaymentService.verify_payment(
            user_id=user_id,
            razorpay_order_id=payload.razorpay_order_id,
            razorpay_payment_id=payload.razorpay_payment_id,
            razorpay_signature=payload.razorpay_signature,
            plan_id=payload.plan_id,
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error verifying payment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during verification")


@router.get("/status", response_model=SubscriptionStatusResponse)
def get_subscription_status(
    user_id: str = Depends(get_current_user_id),
):
    """Get current user subscription tier and status."""
    return PaymentService.get_subscription_status(user_id)


@router.post("/apply-promo", response_model=ApplyPromoResponse)
def apply_promo(
    payload: ApplyPromoRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Apply a promo code (e.g. VIGATRON100) to activate free VIP Pro access."""
    try:
        res = PaymentService.apply_promo_code(user_id=user_id, promo_code=payload.promo_code)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error applying promo code: {e}")
        raise HTTPException(status_code=500, detail="Failed to apply promo code")


@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None),
):
    """Handles incoming Razorpay webhook events (e.g. payment.captured)."""
    try:
        body = await request.body()
        # Log webhook receipt
        logger.info(f"Received Razorpay webhook event: {len(body)} bytes")
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return {"status": "error", "message": str(e)}
