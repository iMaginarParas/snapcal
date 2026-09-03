from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class PaymentPlan(BaseModel):
    id: str
    name: str
    duration_months: int
    duration_days: int
    price_inr: int
    base_price_inr: Optional[int] = None
    discount_percent: Optional[int] = None
    per_month_price: int
    description: str
    features: List[str]
    badge: Optional[str] = None
    is_popular: bool = False


class PlansResponse(BaseModel):
    plans: List[PaymentPlan]
    currency: str = "INR"
    razorpay_key_id: Optional[str] = None


class CreateOrderRequest(BaseModel):
    plan_id: str = Field(..., description="ID of the plan to purchase: 'monthly', 'half_yearly', or 'yearly'")


class CreateOrderResponse(BaseModel):
    order_id: str
    amount: int  # in paise (e.g. 29900)
    currency: str = "INR"
    key_id: str
    plan_id: str
    plan_name: str
    amount_inr: int


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    plan_id: str


class VerifyPaymentResponse(BaseModel):
    success: bool
    message: str
    is_pro: bool
    subscription_tier: str
    plan_id: str
    plan_name: str
    expires_at: str


class SubscriptionStatusResponse(BaseModel):
    is_pro: bool
    subscription_tier: str
    plan_id: Optional[str] = None
    plan_name: Optional[str] = None
    starts_at: Optional[str] = None
    expires_at: Optional[str] = None
    days_remaining: int = 0
    is_active: bool = False
    is_trial_active: bool = False
    trial_days_remaining: int = 0
    can_access_premium: bool = True


class ApplyPromoRequest(BaseModel):
    promo_code: str = Field(..., description="Promo code string")


class ApplyPromoResponse(BaseModel):
    success: bool
    message: str
    is_pro: bool
    subscription_tier: str
    plan_id: str
    plan_name: str
    expires_at: str
    discount_percent: int = 100
