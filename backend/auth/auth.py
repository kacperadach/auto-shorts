import os

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import time
from typing import Dict
import supabase
from supabase import create_client, Client
import jwt
from sqlalchemy.orm import Session

from shared.db.models import get_db, User
from shared.slack_bot.slack import send_slack_message


JWT_SECRET = os.environ.get("JWT_SECRET")
JWT_ALGORITHM = "HS256"

supabase: Client = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))


class ValidUserFromJWT:
    def __init__(self):
        pass

    async def __call__(self, request: Request, db: Session = Depends(get_db)):
        credentials: HTTPAuthorizationCredentials = await HTTPBearer()(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
            if not verify_jwt(credentials.credentials):
                raise HTTPException(status_code=403, detail="Invalid token or expired token.")
            user = get_user_from_JWT(credentials.credentials, db)
            if not user:
                raise HTTPException(status_code=403, detail="Invalid token")

            return user
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")


def verify_jwt(jwtoken: str) -> bool:
    try:
        return not not decodeJWT(jwtoken)
    except Exception:
        return False


def decodeJWT(token: str) -> Dict:
    try:
        decoded_token = jwt.decode(
            token, JWT_SECRET, algorithms=[JWT_ALGORITHM], options={"verify_aud": False}
        )
        return decoded_token if decoded_token["exp"] >= time.time() else None
    except Exception as e:
        print(f"Error decoding token: {e}")
        return {}


def get_user_from_JWT(token: str, db: Session) -> User | None:
    payload = decodeJWT(token)
    if not payload:
        print(f"Could not decode JWT: {token}")
        return None
    user_id = payload["sub"]

    if user_id is None:
        return None

    try:
        data = supabase.auth.get_user(token)
        if not data:
            print(f"User not found in supabase {user_id}")
            return None

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(
                id=user_id,
                email=data.user.email,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            send_slack_message(f"New user: {user.email}")

        return user
    except Exception as e:
        print(f"Error getting user {user_id}: {e}")
        return None
