import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from routers.oauth import router as oauth_router
from routers.render import router as render_router
from routers.youtube import router as youtube_router
from routers.payment import router as payment_router
from routers.repurposer import router as repurposer_router
from routers.repurposer_run import router as repurposer_run_router
from routers.social_media_accounts import router as social_media_accounts_router
from shared.db.models import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
    "https://app.autorepurpose.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(oauth_router)
app.include_router(render_router)
app.include_router(youtube_router)
app.include_router(repurposer_router)
app.include_router(repurposer_run_router)
app.include_router(social_media_accounts_router)
# app.include_router(payment_router)
