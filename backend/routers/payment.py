import os
from time import time

from fastapi import Depends, APIRouter, HTTPException, Header, Request
from sqlalchemy.orm import Session
import stripe
from pydantic import BaseModel

from auth.auth import ValidUserFromJWT
from shared.db.models import (
    get_db,
    User,
    SubscriptionTier,
    SubscriptionStatus,
)
from shared.slack_bot.slack import send_slack_message

router = APIRouter()

# stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

PRODUCTS = [
    {
        "price_id": "price_id",
        "tier": SubscriptionTier.STARTER_MONTHLY,
    },
    {
        "price_id": "price_id",
        "tier": SubscriptionTier.STARTER_YEARLY,
    },
    {
        "price_id": "price_id",
        "tier": SubscriptionTier.PRO_MONTHLY,
    },
    {
        "price_id": "price_id",
        "tier": SubscriptionTier.PRO_YEARLY,
    },
    {
        "price_id": "price_id",
        "tier": SubscriptionTier.PREMIUM_MONTHLY,
    },
    {
        "price_id": "price_id",
        "tier": SubscriptionTier.PREMIUM_YEARLY,
    },
]


def create_stripe_user(email: str):
    customer = stripe.Customer.create(
        api_key=stripe.api_key,
        email=email,
        idempotency_key=email,
    )
    return customer.id


def find_product_by_price_id(price_id: str):
    return next((product for product in PRODUCTS if product["price_id"] == price_id), None)


def find_product_by_tier(tier: str):
    return next((product for product in PRODUCTS if product["tier"].value == tier), None)


@router.post("/v1/payment/create-checkout-session/{tier}")
async def create_checkout_session(
    tier: str,
    user: User = Depends(ValidUserFromJWT()),
    db: Session = Depends(get_db),
):
    product = find_product_by_tier(tier)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if not user.stripe_customer_id:
        user.stripe_customer_id = create_stripe_user(user.email)
        db.commit()
        db.refresh(user)

    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price": product["price_id"],
                    "quantity": 1,
                },
            ],
            mode="subscription",
            success_url=os.environ["APP_BASE_URL"] + "?payment_success=true",
            cancel_url=os.environ["APP_BASE_URL"],
            automatic_tax={"enabled": True},
            customer=user.stripe_customer_id,
            customer_update={
                "address": "auto",
            },
            metadata={
                "price_id": product["price_id"],
                "user_id": user.id,
            },
        )
    except Exception as e:
        send_slack_message(
            f"ERROR: User {user.email} failed to start checkout session for {product['tier'].value}"
        )
        raise HTTPException(
            status_code=500, detail="Failed to create Stripe checkout session"
        ) from e

    send_slack_message(
        f"User {user.email} started checkout session for {product['tier'].value}"
    )
    return {"url": checkout_session.url}


@router.post("/v1/payment/create-customer-portal-session")
async def create_customer_portal_session(
    user: User = Depends(ValidUserFromJWT()),
    db: Session = Depends(get_db),
):
    if not user.stripe_customer_id:
        user.stripe_customer_id = create_stripe_user(user.email)
        db.commit()
        db.refresh(user)

    session = stripe.billing_portal.Session.create(
        customer=user.stripe_customer_id, return_url=os.environ["APP_BASE_URL"]
    )
    send_slack_message(f"User {user.email} started customer portal session")
    return {"url": session.url}


@router.post("/v1/payment/webhook")
async def webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: Session = Depends(get_db),
):
    event = None
    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, os.getenv("STRIPE_WEBHOOK_SECRET")
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload") from e
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature") from e

    send_slack_message(f"New Stripe webhook received: {event['type']}")

    if event["type"] == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        subscription_id = invoice["subscription"]
        customer = invoice["customer"]
        line_items = invoice.get("lines", {}).get("data", [])
        price_id = line_items[0]["price"]["id"] if line_items else None
        if not price_id:
            price_id = invoice.get("metadata", {}).get("price_id")

        product = find_product_by_price_id(price_id)
        if not product:
            raise HTTPException(status_code=400, detail="Invalid price_id")

        user = db.query(User).filter(User.stripe_customer_id == customer).first()
        if not user:
            raise HTTPException(status_code=400, detail="Invalid user")

        user.subscription_tier = product["tier"].value
        user.subscription_status = SubscriptionStatus.ACTIVE.value
        user.subscription_id = subscription_id
        user.subscription_payment_at = time()

        db.commit()
        send_slack_message(
            f"Payment succeeded for user {user.email} for tier {product['tier'].value}"
        )
    elif event["type"] == "invoice.payment_failed":
        invoice = event["data"]["object"]
        subscription_id = invoice["subscription"]
        customer = invoice["customer"]
        line_items = invoice.get("lines", {}).get("data", [])
        price_id = line_items[0]["price"]["id"] if line_items else None
        if not price_id:
            price_id = invoice.get("metadata", {}).get("price_id")

        product = find_product_by_price_id(price_id)
        if not product:
            raise HTTPException(status_code=400, detail="Invalid price_id")

        user = db.query(User).filter(User.stripe_customer_id == customer).first()
        if not user:
            raise HTTPException(status_code=400, detail="Invalid user")

        user.subscription_status.value = SubscriptionStatus.PAYMENT_FAILED.value
        db.commit()
        send_slack_message(
            f"Payment failed for user {user.email} for tier {product['tier'].value}"
        )
