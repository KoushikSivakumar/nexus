"""GitHub commit history model for NEXUS."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.repository import Repository


class Commit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A commit belonging to a NEXUS repository (GitHub history)."""

    __tablename__ = "commits"
    __table_args__ = (
        UniqueConstraint(
            "repository_id", "external_id", name="uq_commits_repository_id_external_id"
        ),
        Index("ix_commits_repository_id_committed_at", "repository_id", "committed_at"),
    )

    repository_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False
    )
    # GitHub commit identifier (the commit SHA). Separate from the NEXUS UUID primary key.
    external_id: Mapped[str] = mapped_column(String(64), nullable=False)
    sha: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    author_name: Mapped[str] = mapped_column(String(255), nullable=False)
    author_email: Mapped[str] = mapped_column(String(255), nullable=False)
    committer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    committer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    # GitHub commit timestamp, kept separate from the NEXUS created_at/updated_at record timestamps.
    committed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    repository: Mapped["Repository"] = relationship(back_populates="commits")