"""GitHub pull request history model for NEXUS."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.pull_request_review import PullRequestReview
    from app.models.repository import Repository


class PullRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A pull request belonging to a NEXUS repository (GitHub history)."""

    __tablename__ = "pull_requests"
    __table_args__ = (
        UniqueConstraint(
            "repository_id", "external_id", name="uq_pull_requests_repository_id_external_id"
        ),
        UniqueConstraint(
            "repository_id", "number", name="uq_pull_requests_repository_id_number"
        ),
        Index(
            "ix_pull_requests_repository_id_github_created_at",
            "repository_id",
            "github_created_at",
        ),
        Index("ix_pull_requests_repository_id_state", "repository_id", "state"),
    )

    repository_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    author_username: Mapped[str] = mapped_column(String(255), nullable=False)
    # GitHub lifecycle timestamps, kept separate from the NEXUS created_at/updated_at record timestamps.
    github_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    github_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    merged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    repository: Mapped["Repository"] = relationship(back_populates="pull_requests")
    reviews: Mapped[list["PullRequestReview"]] = relationship(back_populates="pull_request")