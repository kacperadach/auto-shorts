import re

from fastapi import FastAPI, Depends, HTTPException, Query, APIRouter, Request, Path, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from auth.auth import ValidUserFromJWT
from shared.db.models import Repurposer, RepurposeRun, RenderedVideo, User, get_db, RunType
from shared.s3.s3 import upload_file_obj_to_s3, download_image
from shared.download import download_youtube_info, extract_video_id

from cloudrun import call_cloudrun


router = APIRouter()


class RepurposeRunRequest(BaseModel):
    url: str


@router.post("/v1/repurposer-run/{repurposer_id}")
async def run_manual(
    repurposer_id: str = Path(...),
    request: RepurposeRunRequest = Body(...),
    db: Session = Depends(get_db),
    user: User = Depends(ValidUserFromJWT()),
):
    video_id = extract_video_id(request.url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    repurposer = db.query(Repurposer).filter(Repurposer.id == repurposer_id).one_or_none()
    if not repurposer or repurposer.user_id != user.id:
        raise HTTPException(status_code=404, detail="Repurposer not found")

    info = download_youtube_info(request.url)
    if not info:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    channel_id = info["channel_id"]

    image_data = download_image(info["thumbnail"])
    thumbnail_s3_url = await upload_file_obj_to_s3(
        image_data, f"thumbnails/videos/{video_id}.jpg"
    )

    run = RepurposeRun(
        repurposer_id=repurposer_id,
        video_id=video_id,
        channel_id=channel_id,
        run_type=RunType.MANUAL.value,
        thumbnail_url=thumbnail_s3_url,
        video_title=info["title"],
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    print(f"Calling cloudrun manually for {run.id}: {request.url}")
    call_cloudrun(run.id, video_id, channel_id, is_manual=True)


@router.get("/v1/repurposer-run/repurposer/{repurposer_id}/channel/{channel_id}")
async def get_channel_runs(
    repurposer_id: str = Path(...),
    channel_id: str = Path(...),
    db: Session = Depends(get_db),
    user: User = Depends(ValidUserFromJWT()),
):
    return (
        db.query(RepurposeRun)
        .outerjoin(Repurposer, Repurposer.id == RepurposeRun.repurposer_id)
        .filter(RepurposeRun.repurposer_id == repurposer_id)
        .filter(RepurposeRun.channel_id == channel_id)
        .options(joinedload(RepurposeRun.renders))
        .order_by(Repurposer.created_at.desc())
        .all()
    )


@router.get("/v1/repurposer-run/repurposer/{repurposer_id}")
async def get_repurposer_runs(
    repurposer_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(ValidUserFromJWT()),
):
    repurposer = db.query(Repurposer).filter(Repurposer.id == repurposer_id).one_or_none()
    if not repurposer or repurposer.user_id != user.id:
        raise HTTPException(status_code=404, detail="Repurposer not found")

    return (
        db.query(RepurposeRun)
        .outerjoin(RenderedVideo, RepurposeRun.id == RenderedVideo.run_id)
        .filter(RepurposeRun.repurposer_id == repurposer_id)
        .options(joinedload(RepurposeRun.renders))
        .order_by(desc(RepurposeRun.created_at))
        .all()
    )
