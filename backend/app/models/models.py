from app.db.session import Base
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID, JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    Text,
    String,
    BigInteger,
    SmallInteger,
    Computed,
    Numeric,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    Integer
)

from app.models.enums import AssetStatus, JobStatus, StepStatus, InsightType

# ---------------------
# VIDEO ASSETS
# ---------------------


class VideoAsset(Base):
    __tablename__ = "video_assets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    normalized_storage_path: Mapped[str | None] = mapped_column(String(1000))
    thumbnail_path: Mapped[str | None] = mapped_column(String(1000))
    status: Mapped[AssetStatus] = mapped_column(
        nullable=False, default=AssetStatus.UPLOADED
    )
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    duration_seconds: Mapped[float | None] = mapped_column(Numeric(10, 3))
    technical_metadata: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
        onupdate=datetime.now,
    )

    processing_jobs: Mapped[list["ProcessingJob"]] = relationship(
        back_populates="asset"
    )
    transcript_segments: Mapped[list["TranscriptSegment"]] = relationship(
        back_populates="asset"
    )
    insight_segments: Mapped[list["InsightSegment"]] = relationship(
        back_populates="asset"
    )
    summary: Mapped["VideoSummary | None"] = relationship(back_populates="asset")
    analytics_events: Mapped[list["AnalyticsEvent"]] = relationship(
        back_populates="asset"
    )


# ---------------------
# PROCESSING PIPELINE
# ---------------------


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("video_assets.id"), nullable=False, index=True
    )
    status: Mapped[JobStatus] = mapped_column(nullable=False, default=JobStatus.QUEUED)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
        onupdate=datetime.now,
    )

    asset: Mapped["VideoAsset"] = relationship(back_populates="processing_jobs")
    steps: Mapped[list["JobStep"]] = relationship(back_populates="job")


class JobStep(Base):
    __tablename__ = "job_steps"
    __table_args__ = (
        UniqueConstraint("job_id", "step_name"),
        Index("ix_job_steps_job_id_step_order", "job_id", "step_order", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("processing_jobs.id"), nullable=False
    )
    step_name: Mapped[str] = mapped_column(String(50), nullable=False)
    step_order: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    status: Mapped[StepStatus] = mapped_column(
        nullable=False, default=StepStatus.PENDING
    )
    attempts: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=3)
    error_message: Mapped[str | None] = mapped_column(Text)
    meta: Mapped[dict | None] = mapped_column(JSONB)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )
    job: Mapped["ProcessingJob"] = relationship(back_populates="steps")


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"
    __table_args__ = (
        Index("ix_transcript_segments_asset_start", "asset_id", "start_time"),
        Index(
            "ix_transcript_segments_text_search", "text_search", postgresql_using="gin"
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("video_assets.id"), nullable=False
    )
    segment_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    end_time: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    text_search = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('english', text)", persisted=True),
    )
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3))
    speaker_label: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )
 
    asset: Mapped["VideoAsset"] = relationship(back_populates="transcript_segments")


class InsightSegment(Base):
    __tablename__ = "insight_segments"
    __table_args__ = (
        Index("ix_insight_segments_asset_type", "asset_id", "insight_type"),
        Index("ix_insight_segments_asset_start", "asset_id", "start_time"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("video_assets.id"), nullable=False
    )
    insight_type: Mapped[InsightType] = mapped_column(nullable=False)
    start_time: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    end_time: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    result: Mapped[dict] = mapped_column(JSONB, nullable=False)
    score: Mapped[float | None] = mapped_column(Numeric(5, 3))
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )

    asset: Mapped["VideoAsset"] = relationship(back_populates="insight_segments")



class VideoSummary(Base):
    __tablename__ = "video_summaries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("video_assets.id"), unique=True, nullable=False
    )
    short_summary: Mapped[str] = mapped_column(Text, nullable=False)
    key_topics: Mapped[list] = mapped_column(JSONB, nullable=False)
    chapter_summaries: Mapped[list | None] = mapped_column(JSONB)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()", onupdate=datetime.now
    )

    asset: Mapped["VideoAsset"] = relationship(back_populates="summary")


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    __table_args__ = (
        Index("ix_analytics_events_type_created", "event_type", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("video_assets.id")
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )

    asset: Mapped["VideoAsset | None"] = relationship(back_populates="analytics_events")
