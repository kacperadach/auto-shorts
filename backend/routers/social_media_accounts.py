from fastapi import FastAPI, Depends, HTTPException, Query, APIRouter, Request
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel

from shared.db.models import (
    User,
    get_db,
    SocialMediaAccount,
    Repurposer,
    RepurposerSocialMediaAccount,
)
from auth.auth import ValidUserFromJWT

router = APIRouter()


@router.get("/v1/social-media-accounts")
async def get_accounts(
    db: Session = Depends(get_db),
    user: User = Depends(ValidUserFromJWT()),
):
    return db.query(SocialMediaAccount).filter(SocialMediaAccount.user_id == user.id).all()


@router.put("/v1/social-media-accounts/{account_id}/add-to-repurposer/{repurposer_id}")
async def add_to_repurposer(
    account_id: str,
    repurposer_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(ValidUserFromJWT()),
):
    social_media_account = (
        db.query(SocialMediaAccount).filter(SocialMediaAccount.id == account_id).first()
    )
    if not social_media_account or social_media_account.user_id != user.id:
        raise HTTPException(status_code=404, detail="Account not found")

    repurposer = db.query(Repurposer).filter(Repurposer.id == repurposer_id).one_or_none()
    if not repurposer or repurposer.user_id != user.id:
        raise HTTPException(status_code=404, detail="Repurposer not found")

    db.query(RepurposerSocialMediaAccount).filter(
        RepurposerSocialMediaAccount.repurposer_id == repurposer_id
    ).filter(RepurposerSocialMediaAccount.social_media_account_id == account_id).delete()
    db.commit()

    repurposer_social_media_account = RepurposerSocialMediaAccount(
        repurposer_id=repurposer.id,
        social_media_account_id=social_media_account.id,
    )

    db.add(repurposer_social_media_account)
    db.commit()
    db.refresh(repurposer_social_media_account)
    return repurposer_social_media_account


@router.put("/v1/social-media-accounts/{account_id}/remove-from-repurposer/{repurposer_id}")
async def remove_from_repurposer(
    account_id: str,
    repurposer_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(ValidUserFromJWT()),
):
    social_media_account = (
        db.query(SocialMediaAccount).filter(SocialMediaAccount.id == account_id).one_or_none()
    )
    if not social_media_account or social_media_account.user_id != user.id:
        raise HTTPException(status_code=404, detail="Account not found")

    repurposer = db.query(Repurposer).filter(Repurposer.id == repurposer_id).one_or_none()
    if not repurposer or repurposer.user_id != user.id:
        raise HTTPException(status_code=404, detail="Repurposer not found")

    db.query(RepurposerSocialMediaAccount).filter(
        RepurposerSocialMediaAccount.repurposer_id == repurposer_id
    ).filter(RepurposerSocialMediaAccount.social_media_account_id == account_id).delete()
    db.commit()


@router.delete("/v1/social-media-accounts/{account_id}")
async def delete_social_media_account(
    account_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(ValidUserFromJWT()),
):
    social_media_account = (
        db.query(SocialMediaAccount).filter(SocialMediaAccount.id == account_id).one_or_none()
    )
    if not social_media_account or social_media_account.user_id != user.id:
        raise HTTPException(status_code=404, detail="Account not found")

    db.delete(social_media_account)
    db.commit()
