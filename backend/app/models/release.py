"""GitHub release history model for NEXUS."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.repository import Repository


class Release(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A release belonging to a NEXUS repository (GitHub history)."""

    __tablename__ = "releases"
    __table_args__ = (
        UniqueConstraint(
            "repository_id", "external_id", name="uq_releases_repository_id_external_id"
        ),
        UniqueConstraint(
            "repository_id", "tag_name", name="uq_releases_repository_id_tag_name"
        ),
        Index("ix_releases_repository_id_published_at", "repository_id", "published_at"),
    )

    repository_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    tag_name: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    author_username: Mapped[str] = mapped_column(String(255), nullable=False)
    draft: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # GitHub publish timestamp, separate from the NEXUS created_at/updated_at record timestamps.
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    repository: Mapped["Repository"] = relationship(back_populates="releases")