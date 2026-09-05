"""GitHub deployment history model for NEXUS."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.repository import Repository


class Deployment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A deployment belonging to a NEXUS repository (GitHub history)."""

    __tablename__ = "deployments"
    __table_args__ = (
        UniqueConstraint(
            "repository_id", "external_id", name="uq_deployments_repository_id_external_id"
        ),
        Index("ix_deployments_repository_id_environment", "repository_id", "environment"),
        Index(
            "ix_deployments_repository_id_github_created_at",
            "repository_id",
            "github_created_at",
        ),
    )

    repository_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    environment: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ref: Mapped[str] = mapped_column(String(255), nullable=False)
    creator_username: Mapped[str] = mapped_column(String(255), nullable=False)
    # Latest known GitHub deployment status snapshot (e.g. in_progress, success, error).
    status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # GitHub deployment timestamp, separate from the NEXUS created_at/updated_at record timestamps.
    github_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    repository: Mapped["Repository"] = relationship(back_populates="deployments")