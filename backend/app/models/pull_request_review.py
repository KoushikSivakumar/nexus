"""GitHub pull request review history model for NEXUS."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.pull_request import PullRequest


class PullRequestReview(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A review on a GitHub pull request (belongs to a PullRequest)."""

    __tablename__ = "pull_request_reviews"
    __table_args__ = (
        UniqueConstraint(
            "pull_request_id",
            "external_id",
            name="uq_pull_request_reviews_pull_request_id_external_id",
        ),
        Index(
            "ix_pull_request_reviews_pull_request_id_submitted_at",
            "pull_request_id",
            "submitted_at",
        ),
    )

    pull_request_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("pull_requests.id"), nullable=False
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    reviewer_username: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    # GitHub review submission timestamp, separate from the NEXUS created_at/updated_at record timestamps.
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    pull_request: Mapped["PullRequest"] = relationship(back_populates="reviews")