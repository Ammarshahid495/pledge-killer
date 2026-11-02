"""
Classroom and ClassroomMember Database Models.
Adheres strictly to the Equal Permissions principle (no teacher/owner role column).
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from ..core.database import Base
from .user import generate_uuid, utc_now


class Classroom(Base):
    __tablename__ = "classrooms"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    join_token = Column(String(100), nullable=True)
    join_token_hash = Column(String(64), unique=True, nullable=False, index=True)
    language = Column(String(20), default="cpp", nullable=False)
    status = Column(String(30), default="ACTIVE", nullable=False)  # ACTIVE, WAITING_FOR_SUBMISSIONS, etc.
    min_submissions = Column(Integer, default=5, nullable=False)
    deadline = Column(DateTime(timezone=True), nullable=True)
    max_participants = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    # Shared assignment starter (not student work). Any peer may set/replace it.
    starter_storage_key = Column(String(255), nullable=True)
    starter_filename = Column(String(255), nullable=True)
    starter_sha256 = Column(String(64), nullable=True)

    members = relationship("ClassroomMember", back_populates="classroom", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="classroom", cascade="all, delete-orphan")
    analysis_jobs = relationship("AnalysisJob", back_populates="classroom", cascade="all, delete-orphan")
    matches = relationship("SimilarityMatch", back_populates="classroom", cascade="all, delete-orphan")
    reports = relationship("PrivateReport", back_populates="classroom", cascade="all, delete-orphan")


class ClassroomMember(Base):
    __tablename__ = "classroom_members"
    __table_args__ = (
        UniqueConstraint("classroom_id", "user_id", name="uq_classroom_member"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    classroom_id = Column(String(36), ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    anonymous_label = Column(String(50), nullable=False)  # e.g. "Peer A", "Peer B"
    joined_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    status = Column(String(20), default="ACTIVE", nullable=False)

    classroom = relationship("Classroom", back_populates="members")
    user = relationship("User", back_populates="memberships")
    submissions = relationship("Submission", back_populates="member", cascade="all, delete-orphan")
