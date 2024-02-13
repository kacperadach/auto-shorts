from uuid import uuid4

from fastapi import FastAPI, Depends, HTTPException, Query, APIRouter, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from psycopg2.errors import UniqueViolation

from auth.auth import ValidUserFromJWT
from shared.db.models import (
    Repurposer,
    RepurposerChannel,
    YoutubeSubscription,
    User,
    get_db,
    RepurposerSocialMediaAccount,
)
from subscription.utils import check_limits
from enqueue import enqueue_channel_subscription
from shared.download import get_channel_info
from shared.slack_bot.slack import send_slack_message
from shared.s3.s3 import upload_file_obj_to_s3, download_image

router = APIRouter()


class RepurposerCreateRequest(BaseModel):
    name: str
    primary_channels: list[str]
    secondary_categories: list[str]
    topic: str


@router.post("/v1/repurposer")
async def create_repurposer(
    request: RepurposerCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(ValidUserFromJWT()),
):
    check_limits(Repurposer, user, db)

    repurposer_id = str(uuid4())

    repurposer = Repurposer(
        id=repurposer_id,
        name=request.name,
        secondary_categories=request.secondary_categories,
        topic=request.topic,
        user_id=user.id,
    )
    db.add(repurposer)

    channel_ids = []
    for channel in request.primary_channels:
        channel_info = get_channel_info(channel)
        if not channel_info:
            raise HTTPException(status_code=400, detail=f"Invalid channel url {channel}")

        image_data = download_image(channel_info["thumbnail_url"])
        thumbnail_s3_url = await upload_file_obj_to_s3(
            image_data, f"thumbnails/channels/{channel_info['channel_id']}.jpg"
        )
        channel_ids.append(channel_info["channel_id"])
        db.add(
            RepurposerChannel(
                repurposer_id=repurposer_id,
                youtube_channel_id=channel_info["channel_id"],
                name=channel_info["name"],
                thumbnail_url=thumbnail_s3_url,
            )
        )

    try:
        db.commit()
    except UniqueViolation:
        raise HTTPException(status_code=400, detail="Repurposer with this name already exists")

    db.refresh(repurposer)

    for channel_id in channel_ids:
        enqueue_channel_subscription(channel_id)

    send_slack_message(f"New repurposer created: {request.name} for user {user.email}")
    return repurposer


@router.put("/v1/repurposer/{repurposer_id}")
async def update_repurposer(
    repurposer_id: str,
    request: RepurposerCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(ValidUserFromJWT()),
):
    repurposer = db.query(Repurposer).filter(Repurposer.id == repurposer_id).one_or_none()
    if not repurposer or repurposer.user_id != user.id:
        raise HTTPException(status_code=404, detail="Repurposer not found")

    repurposer.secondary_categories = request.secondary_categories
    repurposer.topic = request.topic
    repurposer.name = request.name

    db.commit()
    db.refresh(repurposer)
    return repurposer


class AddChannelRequest(BaseModel):
    channel_url: str


@router.put("/v1/repurposer/{repurposer_id}/add-channel")
async def add_channel(
    repurposer_id: str,
    request: AddChannelRequest,
    db: Session = Depends(get_db),
    user: User = Depends(ValidUserFromJWT()),
):
    repurposer = db.query(Repurposer).filter(Repurposer.id == repurposer_id).one_or_none()
    if not repurposer or repurposer.user_id != user.id:
        raise HTTPException(status_code=404, detail="Repurposer not found")

    channel_info = get_channel_info(request.channel_url)
    if not channel_info:
        raise HTTPException(status_code=400, detail=f"Channel not found {request.channel_url}")

    image_data = download_image(channel_info["thumbnail_url"])
    thumbnail_s3_url = await upload_file_obj_to_s3(
        image_data, f"thumbnails/{channel_info['channel_id']}.jpg"
    )

    db.add(
        RepurposerChannel(
            repurposer_id=repurposer.id,
            youtube_channel_id=channel_info["channel_id"],
            name=channel_info["name"],
            thumbnail_url=thumbnail_s3_url,
        )
    )
    db.commit()
    db.refresh(repurposer)
    enqueue_channel_subscription(channel_info["channel_id"])
    return (
        db.query(Repurposer)
        .outerjoin(RepurposerChannel, Repurposer.id == RepurposerChannel.repurposer_id)
        .filter(Repurposer.id == repurposer_id)
        .filter(Repurposer.user_id == user.id)
        .options(joinedload(Repurposer.channels))
        .order_by(Repurposer.created_at.desc())
        .one_or_none()
    )


class RemoveChannelRequest(BaseModel):
    channel_id: str


@router.put("/v1/repurposer/{repurposer_id}/remove-channel")
async def remove_channel(
    repurposer_id: str,
    request: RemoveChannelRequest,
    db: Session = Depends(get_db),
    user: User = Depends(ValidUserFromJWT()),
):
    repurposer = db.query(Repurposer).filter(Repurposer.id == repurposer_id).one_or_none()
    if not repurposer or repurposer.user_id != user.id:
        raise HTTPException(status_code=404, detail="Repurposer not found")

    db.query(RepurposerChannel).filter(
        RepurposerChannel.youtube_channel_id == request.channel_id
    ).delete()
    db.commit()
    db.refresh(repurposer)
    return repurposer


@router.get("/v1/repurposer")
async def get_repurposers(
    db: Session = Depends(get_db),
    user: User = Depends(ValidUserFromJWT()),
):
    return (
        db.query(Repurposer)
        .outerjoin(RepurposerChannel, Repurposer.id == RepurposerChannel.repurposer_id)
        .outerjoin(
            RepurposerSocialMediaAccount,
            Repurposer.id == RepurposerSocialMediaAccount.repurposer_id,
        )
        .filter(Repurposer.user_id == user.id)
        .options(joinedload(Repurposer.channels))
        .options(joinedload(Repurposer.social_media_accounts))
        .order_by(Repurposer.created_at.desc())
        .all()
    )
