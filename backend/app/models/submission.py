"""
Submission and SubmissionVersion Database Models.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from ..core.database import Base
from .user import generate_uuid, utc_now


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (
        UniqueConstraint("classroom_id", "member_id", name="uq_classroom_member_submission"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    classroom_id = Column(String(36), ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False, index=True)
    member_id = Column(String(36), ForeignKey("classroom_members.id", ondelete="CASCADE"), nullable=False, index=True)
    current_version_id = Column(String(36), nullable=True)  # References submission_versions.id
    status = Column(String(20), default="ACTIVE", nullable=False)  # ACTIVE, SUPERSEDED, WITHDRAWN
    submitted_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    classroom = relationship("Classroom", back_populates="submissions")
    member = relationship("ClassroomMember", back_populates="submissions")
    versions = relationship(
        "SubmissionVersion",
        back_populates="submission",
        cascade="all, delete-orphan",
        order_by="desc(SubmissionVersion.version_number)",
    )


class SubmissionVersion(Base):
    __tablename__ = "submission_versions"
    __table_args__ = (
        UniqueConstraint("submission_id", "version_number", name="uq_submission_version"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    submission_id = Column(String(36), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False, default=1)
    storage_key = Column(String(255), nullable=False)
    sha256_hash = Column(String(64), nullable=False)
    file_size = Column(Integer, nullable=False)
    original_filename = Column(String(255), nullable=False)
    language = Column(String(20), default="cpp", nullable=False)
    processing_status = Column(String(20), default="PENDING", nullable=False)  # PENDING, PROCESSED, ERROR
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    submission = relationship("Submission", back_populates="versions")
