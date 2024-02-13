from fastapi import FastAPI, Depends, HTTPException, Query, APIRouter, Request, Path, Body
from sqlalchemy.orm import Session, joinedload


from auth.auth import ValidUserFromJWT
from shared.db.models import Repurposer, RepurposeRun, RenderedVideo, User, get_db, RunType

router = APIRouter()


@router.get("/v1/rendered-videos/run/{run_id}")
async def get_repurposer_run(
    run_id: str = Path(...),
    db: Session = Depends(get_db),
    user: User = Depends(ValidUserFromJWT()),
):
    return (
        db.query(RepurposeRun)
        .outerjoin(RenderedVideo, RepurposeRun.id == RenderedVideo.run_id)
        .filter(RepurposeRun.id == run_id)
        .options(joinedload(RepurposeRun.renders))
        .order_by(Repurposer.created_at.desc())
        .one_or_none()
    )
