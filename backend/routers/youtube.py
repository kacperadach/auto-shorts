from urllib.parse import urlparse, parse_qs
import random
import xml.etree.ElementTree as ET
from time import time

from fastapi import FastAPI, Depends, HTTPException, Query, APIRouter, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError

from cloudrun import call_cloudrun
from shared.db.models import (
    get_db,
    YoutubeSubscription,
    RepurposerChannel,
    RepurposeRun,
    RunStatus,
    Repurposer,
    RunType,
)
from shared.download import download_youtube_info
from shared.s3.s3 import upload_file_obj_to_s3, download_image
from subscribe import subscribe_to_channel
from enqueue import enqueue_channel_subscription


router = APIRouter()


@router.get("/v1/youtube-webhook", response_class=PlainTextResponse)
async def verify_subscription(
    request: Request,
    db: Session = Depends(get_db),
):
    hub_mode = request.query_params.get("hub.mode")
    hub_topic = request.query_params.get("hub.topic")
    hub_challenge = request.query_params.get("hub.challenge")
    hub_lease_seconds = request.query_params.get("hub.lease_seconds")

    if hub_mode != "subscribe":
        print(f"Invalid hub.mode {hub_mode}")
        raise HTTPException(status_code=400, detail="Invalid hub.mode")

    # hub.topic=https://www.youtube.com/xml/feeds/videos.xml%3Fchannel_id%3DUCZe2MISfXymQzwJjgW8d81w

    parsed_url = urlparse(hub_topic)
    query_params = parse_qs(parsed_url.query)
    channel_id = query_params.get("channel_id", [None])[0]
    if not channel_id:
        print(f"Could not parse channel_id from {hub_topic}")
        raise HTTPException(status_code=400, detail="Invalid channel_id")

    subscription = (
        db.query(YoutubeSubscription)
        .filter(YoutubeSubscription.channel_id == channel_id)
        .one_or_none()
    )
    if not subscription:
        print(f"No YoutubeSubscription row found for {channel_id}")
        raise HTTPException(status_code=400, detail="Invalid channel_id")

    now = time()
    update_statement = (
        update(YoutubeSubscription)
        .where(
            YoutubeSubscription.channel_id == channel_id,
            YoutubeSubscription.last_subscribed == subscription.last_subscribed,
        )
        .values(last_subscribed=now)
    )

    result = db.execute(update_statement)
    db.commit()
    if result.rowcount == 0:
        print(f"Failed to update last_subscribed for {channel_id}")
        raise HTTPException(status_code=400, detail="Failed to update last_subscribed")

    enqueue_channel_subscription(channel_id, delay=int(hub_lease_seconds))
    print(f"Enqueued subscription for {channel_id}")

    return hub_challenge


def parse_youtube_notification(xml_data):
    root = ET.fromstring(xml_data)

    # Define the namespaces used in the YouTube XML feed
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "yt": "http://www.youtube.com/xml/schemas/2015",
    }

    # Extracting the video ID, channel ID, and title
    entry = root.find("atom:entry", ns)
    if entry is not None:
        video_id = entry.find("yt:videoId", ns).text
        channel_id = entry.find("yt:channelId", ns).text
        video_title = entry.find("atom:title", ns).text

        return {"video_id": video_id, "channel_id": channel_id, "video_title": video_title}

    return None


# TODO: setup HMAC secret
@router.post("/v1/youtube-webhook")
async def youtube_webhook_post(request: Request, db: Session = Depends(get_db)):
    xml_data = await request.body()
    parsed_data = parse_youtube_notification(xml_data.decode("utf-8"))

    if not parsed_data:
        return

    channel_id = parsed_data["channel_id"]
    if not channel_id:
        print(f"Invalid channel_id {parsed_data}")
        raise HTTPException(status_code=400, detail="Invalid channel_id")

    video_id = parsed_data["video_id"]
    if not video_id:
        print(f"Invalid video_id {parsed_data}")
        raise HTTPException(status_code=400, detail="Invalid video_id")

    repurposer_channels = (
        db.query(RepurposerChannel)
        .filter(RepurposerChannel.youtube_channel_id == channel_id)
        .all()
    )
    if not repurposer_channels:
        print(f"No repurposer channels found for {channel_id}")
        return

    existing_runs = db.query(RepurposeRun).filter(RepurposeRun.video_id == video_id).all()

    primary_url = f"https://www.youtube.com/watch?v={video_id}"
    thumbnail_s3_url = ""
    try:
        info = download_youtube_info(primary_url)
        if not info:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")

        image_data = download_image(info["thumbnail"])
        if image_data:
            thumbnail_s3_url = await upload_file_obj_to_s3(
                image_data, f"thumbnails/videos/{video_id}.jpg"
            )
    except Exception as e:
        print(f"Failed to download youtube info/thumbnail for {video_id}: {e}")
        return

    for repurposer_channel in repurposer_channels:
        run = next(
            (
                run
                for run in existing_runs
                if run.repurposer_id == repurposer_channel.repurposer_id
            ),
            None,
        )
        if run:
            if run.status == RunStatus.COMPLETED.value:
                print(
                    f"Run {run.id} already completed for repurposer {repurposer_channel.repurposer_id}, skipping"
                )
                continue
            if run.status == RunStatus.RUNNING.value:
                print(
                    f"Run {run.id} already running for repurposer {repurposer_channel.repurposer_id}, skipping"
                )
                continue
            if run.status == RunStatus.FAILED.value:
                print(
                    f"Run {run.id} failed for repurposer {repurposer_channel.repurposer_id}, retrying"
                )

                update_statement = (
                    update(RepurposeRun)
                    .filter(RepurposeRun.id == run.id)
                    .filter(RepurposeRun.status == RunStatus.FAILED.value)
                    .values(status=RunStatus.RUNNING.value)
                )

                result = db.execute(update_statement)
                db.commit()
                if result.rowcount == 0:
                    print(f"Failed to update run status for failed run: {run.id}")
                    continue

        else:
            print(
                f"Creating run for repurposer {repurposer_channel.repurposer_id}, video {video_id}"
            )
            try:
                run = RepurposeRun(
                    repurposer_id=repurposer_channel.repurposer_id,
                    video_id=video_id,
                    channel_id=channel_id,
                    run_type=RunType.AUTOMATED.value,
                    video_title=info["title"],
                    thumbnail_url=thumbnail_s3_url,
                )
                db.add(run)
                db.commit()
                db.refresh(run)
            except IntegrityError:
                print(
                    f"Run already exists for repurposer {repurposer_channel.repurposer_id}, video {video_id}"
                )
                continue

        repurposer = (
            db.query(Repurposer)
            .filter(Repurposer.id == repurposer_channel.repurposer_id)
            .one_or_none()
        )
        if not repurposer:
            print(f"Repurposer {repurposer_channel.repurposer_id} not found")
            continue

        print(f"Calling cloudrun for {repurposer.id}: {primary_url}")
        # TODO: move this to a push queue
        call_cloudrun(run.id, video_id, channel_id, is_manual=False)


class SubscribeRequest(BaseModel):
    channel_id: str


# 10 days
SUBSCRIPTION_INTERVAL_SECONDS = 10 * 24 * 60 * 60


# TODO: add auth
@router.post("/v1/youtube-webhook/subscribe")
async def subscribe_to_youtube_webhook(
    request: SubscribeRequest,
    db: Session = Depends(get_db),
):
    print(f"Got subscription request to {request.channel_id}")

    # first check if any repurposers need this channel
    repurposer_channel = (
        db.query(RepurposerChannel)
        .filter(RepurposerChannel.youtube_channel_id == request.channel_id)
        .first()
    )
    if not repurposer_channel:
        print(f"No repurposer needs channel {request.channel_id}")
        # TODO: delete YoutubeSubscription row if it exists
        return

    # check for YoutubeSubscription row

    subscription = (
        db.query(YoutubeSubscription)
        .filter(YoutubeSubscription.channel_id == request.channel_id)
        .one_or_none()
    )
    if not subscription:
        print(f"No YoutubeSubscription row found for {request.channel_id}, creating one.")
        subscription = YoutubeSubscription(channel_id=request.channel_id)
        db.add(subscription)
        db.commit()
        db.refresh(subscription)

    current_timestamp = time()

    if current_timestamp - subscription.last_subscribed < SUBSCRIPTION_INTERVAL_SECONDS:
        print(f"Already subscribed to {request.channel_id} recently, skipping.")
        return

    print(f"Subscribing to {request.channel_id}")
    subscribe_to_channel(request.channel_id, lease_seconds=SUBSCRIPTION_INTERVAL_SECONDS)
