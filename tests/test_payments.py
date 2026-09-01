from app.services.payment_service import PaymentService, PLANS_CATALOG
from app.schemas.payments import CreateOrderRequest, VerifyPaymentRequest


def test_payment_plans():
    plans = PaymentService.get_all_plans()
    assert len(plans) == 3
    
    plan_ids = [p.id for p in plans]
    assert "monthly" in plan_ids
    assert "half_yearly" in plan_ids
    assert "yearly" in plan_ids

    # Monthly: 299
    monthly = PLANS_CATALOG["monthly"]
    assert monthly.price_inr == 299
    assert monthly.duration_days == 30

    # 6-Months: 1499
    half_yearly = PLANS_CATALOG["half_yearly"]
    assert half_yearly.price_inr == 1499
    assert half_yearly.duration_days == 180

    # Yearly: 2799, base: 3588
    yearly = PLANS_CATALOG["yearly"]
    assert yearly.price_inr == 2799
    assert yearly.base_price_inr == 3588
    assert yearly.discount_percent == 22
    assert yearly.duration_days == 365


def test_create_order_and_verify():
    test_user_id = "test-user-12345"
    
    # Create order for yearly plan
    order = PaymentService.create_order(user_id=test_user_id, plan_id="yearly")
    assert order.order_id is not None
    assert order.amount == 279900  # 2799 * 100 paise
    assert order.plan_id == "yearly"

    # Verify payment (mock mode when secret not configured)
    verify_res = PaymentService.verify_payment(
        user_id=test_user_id,
        razorpay_order_id=order.order_id,
        razorpay_payment_id="pay_mock_98765",
        razorpay_signature="sig_mock_signature",
        plan_id="yearly",
    )
    assert verify_res.success is True
    assert verify_res.is_pro is True
    assert verify_res.subscription_tier == "pro"

    # Check subscription status
    status = PaymentService.get_subscription_status(test_user_id)
    assert status.is_pro is True
    assert status.subscription_tier == "pro"
    assert status.plan_id == "yearly"
    assert status.days_remaining >= 364


def test_promo_code():
    promo_user = "user-promo-test-99"
    # Apply VIGATRON100
    res = PaymentService.apply_promo_code(user_id=promo_user, promo_code="VIGATRON100")
    assert res.success is True
    assert res.is_pro is True
    assert res.discount_percent == 100

    # Verify status
    status = PaymentService.get_subscription_status(promo_user)
    assert status.is_pro is True
    assert status.can_access_premium is True
    assert status.subscription_tier == "pro"
    assert status.days_remaining >= 364
