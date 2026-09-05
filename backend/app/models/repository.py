from typing import TYPE_CHECKING

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.commit import Commit
    from app.models.deployment import Deployment
    from app.models.issue import Issue
    from app.models.pull_request import PullRequest
    from app.models.release import Release
    from app.models.workflow_run import WorkFlowRun


class Repository(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "repositories"
    __table_args__ = (UniqueConstraint("owner", "name", name="uq_repositories_owner_name"),)

    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # GitHub history collections.
    commits: Mapped[list["Commit"]] = relationship(back_populates="repository")
    pull_requests: Mapped[list["PullRequest"]] = relationship(back_populates="repository")
    issues: Mapped[list["Issue"]] = relationship(back_populates="repository")
    releases: Mapped[list["Release"]] = relationship(back_populates="repository")
    workflow_runs: Mapped[list["WorkFlowRun"]] = relationship(back_populates="repository")
    deployments: Mapped[list["Deployment"]] = relationship(back_populates="repository")
