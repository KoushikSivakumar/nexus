"""GitHub Actions workflow run history model for NEXUS."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.repository import Repository


class WorkFlowRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A GitHub Actions workflow run belonging to a NEXUS repository (GitHub history)."""

    __tablename__ = "workflow_runs"
    __table_args__ = (
        UniqueConstraint(
            "repository_id", "external_id", name="uq_workflow_runs_repository_id_external_id"
        ),
        UniqueConstraint(
            "repository_id", "run_number", name="uq_workflow_runs_repository_id_run_number"
        ),
        Index("ix_workflow_runs_repository_id_started_at", "repository_id", "started_at"),
        Index("ix_workflow_runs_repository_id_status", "repository_id", "status"),
    )

    repository_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    workflow_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    workflow_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    run_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    conclusion: Mapped[str | None] = mapped_column(String(32), nullable=True)
    branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    head_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # GitHub execution timestamps, separate from the NEXUS created_at/updated_at record timestamps.
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    repository: Mapped["Repository"] = relationship(back_populates="workflow_runs")