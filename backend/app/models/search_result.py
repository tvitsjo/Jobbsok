import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SearchResult(Base):
    __tablename__ = "search_results"
    __table_args__ = (UniqueConstraint("user_id", "job_listing_id", name="uq_user_job"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    search_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("search_runs.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    job_listing_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job_listings.id"), nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False)
    llm_reasoning: Mapped[str | None] = mapped_column(Text)
    is_seen: Mapped[bool] = mapped_column(Boolean, default=False)
    is_saved: Mapped[bool] = mapped_column(Boolean, default=False)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False)
    dismiss_reason: Mapped[str | None] = mapped_column(Text)
    is_notified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    search_run: Mapped["SearchRun"] = relationship(back_populates="results")
    user: Mapped["User"] = relationship(back_populates="search_results")
    job_listing: Mapped["JobListing"] = relationship(back_populates="search_results")
