from typing import Optional
import os
from contextlib import contextmanager
import enum

from time import time
from uuid import uuid4
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Float,
    JSON,
    Enum,
    Integer,
    UniqueConstraint,
    Index,
    ForeignKey,
    DDL,
    event,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from pydantic import BaseModel

engine = create_engine(os.environ.get("POSTGRES_CONNECTION_STRING"))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


@contextmanager
def get_db_context_manager():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class SubscriptionTier(enum.Enum):
    FREE = "free"
    STARTER_MONTHLY = "starter_monthly"
    STARTER_YEARLY = "starter_yearly"
    PRO_MONTHLY = "pro_monthly"
    PRO_YEARLY = "pro_yearly"
    PREMIUM_MONTHLY = "premium_monthly"
    PREMIUM_YEARLY = "premium_yearly"


class SubscriptionStatus(enum.Enum):
    ACTIVE = "active"
    PAYMENT_FAILED = "payment_failed"
    INACTIVE = "inactive"


class SecondaryCategory(enum.Enum):
    SLIME = "slime"
    SOAP = "soap"
    GTA_RAMP = "gta_ramp"
    MINECRAFT = "minecraft"


class RunStatus(enum.Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class RunType(enum.Enum):
    MANUAL = "manual"
    AUTOMATED = "automated"


class BaseTable:
    id: String = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    created_at: float = Column(Float, default=time)
    updated_at: float = Column(Float, default=time)
    deleted_at: float = Column(Float, default=time)


class User(Base, BaseTable):
    __tablename__ = "users"

    email: str = Column(String, index=True)
    stripe_customer_id: str = Column(String)
    subscription_tier: str = Column(String, default=SubscriptionTier.FREE.value)
    subscription_status: str = Column(String, default=SubscriptionStatus.INACTIVE.value)
    subscription_id: str = Column(String)
    subscription_payment_at: float = Column(Float, default=0)


class SubtitleSettings(BaseModel):
    enabled: bool = True
    primary_color: str
    secondary_color: str


class Repurposer(Base, BaseTable):
    __tablename__ = "repurposers"

    user_id: str = Column(String, ForeignKey("users.id"), index=True)
    name: str = Column(String, unique=True, index=True)
    secondary_categories: list[SecondaryCategory] = Column(JSON, default=list)
    topic: str = Column(String, default="")
    subtitle_settings: dict = Column(JSON, default=dict)
    enabled: bool = Column(String, default=True)
    video_title: str = Column(String, default="")
    video_description: str = Column(String, default="")
    video_tags: list[str] = Column(JSON, default=list)

    channels = relationship("RepurposerChannel", back_populates="repurposer")
    social_media_accounts = relationship(
        "SocialMediaAccount",
        secondary="repurposer_social_media_accounts",
        back_populates="repurposers",
    )

    __table_args__ = (Index("user_id_created_at", "user_id", "created_at"),)


class RepurposerChannel(Base, BaseTable):
    __tablename__ = "repurposer_channels"

    repurposer_id: str = Column(String, ForeignKey("repurposers.id"), index=True)
    youtube_channel_id: str = Column(String, index=True)
    thumbnail_url: Optional[str] = Column(String)
    name: Optional[str] = Column(String)

    repurposer = relationship("Repurposer", back_populates="channels")

    __table_args__ = (
        UniqueConstraint(
            "repurposer_id", "youtube_channel_id", name="unique_repurposer_id_channel_id"
        ),
    )


class YoutubeSubscription(Base, BaseTable):
    __tablename__ = "youtube_subscriptions"

    channel_id: str = Column(String, index=True)
    last_subscribed: float = Column(Float, default=0)

    __table_args__ = (UniqueConstraint("channel_id", name="unique_channel_id"),)


class SecondaryVideo(Base, BaseTable):
    __tablename__ = "secondary_videos"

    category: SecondaryCategory = Column(String)
    video_id: int = Column(Integer)
    original_url: str = Column(String, index=True)
    original_start_time: int = Column(Integer, default=0)
    original_end_time: int = Column(Integer, default=0)
    s3_url: str = Column(String)

    # Define the unique constraint
    __table_args__ = (
        UniqueConstraint("category", "video_id", name="unique_category_video_id"),
        Index("index_category_video_id", "category", "video_id"),
    )


class RepurposeRun(Base, BaseTable):
    __tablename__ = "repurpose_runs"

    repurposer_id: str = Column(
        String,
        ForeignKey("repurposers.id"),
    )

    thumbnail_url: str = Column(String)
    video_title: str = Column(String)
    video_id: str = Column(String, index=True)
    channel_id: str = Column(String)
    run_type: str = Column(String, nullable=False)
    status: str = Column(String, default=RunStatus.RUNNING.value)
    audio_s3_url: str = Column(String)
    audio_segments: list[dict] = Column(JSON, default=None)
    clips: list[dict] = Column(JSON, default=None)
    clip_primary_urls: dict = Column(JSON, default={})
    clip_bounding_boxes: dict = Column(JSON, default={})

    renders = relationship("RenderedVideo", back_populates="run")

    __table_args__ = (
        Index("repurposer_id_video_id", "repurposer_id", "video_id"),
        Index("repurposer_id_channel_id", "repurposer_id", "channel_id"),
        Index("repurposer_id_created_at", "repurposer_id", "created_at"),
    )


class RenderedVideo(Base, BaseTable):
    __tablename__ = "rendered_videos"

    run_id: str = Column(
        String,
        ForeignKey("repurpose_runs.id"),
    )
    repurposer_id: str = Column(String, ForeignKey("repurposers.id"))
    channel_id: str = Column(String)
    video_id: str = Column(String)
    s3_url: str = Column(String)
    duration: int = Column(Integer)
    youtube_video_id: str = Column(String)

    run = relationship("RepurposeRun", back_populates="renders")

    __table_args__ = (
        Index("rendered_video_repurposer_id_created_at", "repurposer_id", "created_at"),
        Index(
            "repurposer_id_channel_id_created_at", "repurposer_id", "channel_id", "created_at"
        ),
        Index("repurposer_id_run_id_created_at", "repurposer_id", "run_id", "created_at"),
    )


class SocialMediaAccount(Base, BaseTable):
    __tablename__ = "social_media_accounts"

    user_id: str = Column(String, ForeignKey("users.id"), index=True)
    platform: str = Column(String)
    refresh_token: str = Column(String)
    channel_id: str = Column(String)
    title: str = Column(String)
    thumbnail_url: str = Column(String)

    repurposers = relationship(
        "Repurposer",
        secondary="repurposer_social_media_accounts",
        back_populates="social_media_accounts",
    )

    __table_args__ = (Index("user_id_platform", "user_id", "platform"),)


class RepurposerSocialMediaAccount(Base, BaseTable):
    __tablename__ = "repurposer_social_media_accounts"

    repurposer_id: str = Column(String, ForeignKey("repurposers.id"), index=True)
    social_media_account_id: str = Column(String, ForeignKey("social_media_accounts.id"))

    __table_args__ = (
        UniqueConstraint(
            "repurposer_id", "social_media_account_id", name="unique_repurposer_id_account_id"
        ),
    )


# Add a DDL statement for the partial index
partial_index = DDL(
    """
    CREATE UNIQUE INDEX unique_automated_repurposing ON repurpose_runs (repurposer_id, video_id) 
    WHERE run_type = 'automated';
"""
)

# Associate the DDL with the RepurposeRun class
event.listen(
    RepurposeRun.__table__, "after_create", partial_index.execute_if(dialect="postgresql")
)
