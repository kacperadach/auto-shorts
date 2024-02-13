from shared.db.models import User, SubscriptionTier
from fastapi import HTTPException
from shared.slack_bot.slack import send_slack_message


from sqlalchemy.orm import Session


#  LIMIT EXAMPLE
#  Render.__name__: {
#    SubscriptionTier.FREE.value: 1,
#    SubscriptionTier.STARTER_MONTHLY.value: 10,
#    SubscriptionTier.STARTER_YEARLY.value: 10 * 12,
#    SubscriptionTier.PRO_MONTHLY.value: 100,
#    SubscriptionTier.PRO_YEARLY.value: 100 * 12,
#    SubscriptionTier.PREMIUM_MONTHLY.value: "unlimited",
#    SubscriptionTier.PREMIUM_YEARLY.value: "unlimited",
# }

LIMIT_DICT = {}

# Use this function to check if user has exceeded subscription limit
def check_limits(model, user: User, db: Session, is_monthy: bool = True):
    if model.__name__ not in LIMIT_DICT:
        print(f"Model {model.__name__} not in limit dict")
        return

    limit = LIMIT_DICT[model.__name__][user.subscription_tier]
    if limit == "unlimited":
        return

    if is_monthy:
        usage = (
            db.query(model)
            .filter(model.user_id == user.id)
            .filter(model.created_at > user.subscription_payment_at)
            .count()
        )
    else:
        usage = db.query(model).filter(model.user_id == user.id).count()

    if usage >= limit:
        send_slack_message(f"Limit exceeded for {model.__name__}s for user {user.email}")
        raise HTTPException(status_code=403, detail="Limit exceeded")
