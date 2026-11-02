"""
AnalysisJob, SimilarityMatch, and MatchRegion Database Models.
"""

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from ..core.database import Base
from .user import generate_uuid, utc_now


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    classroom_id = Column(String(36), ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), default="QUEUED", nullable=False)  # QUEUED, PROCESSING, COMPLETED, FAILED
    job_type = Column(String(20), default="INITIAL", nullable=False)  # INITIAL, INCREMENTAL
    engine_version = Column(String(20), default="1.0.0", nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    error_code = Column(String(50), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    classroom = relationship("Classroom", back_populates="analysis_jobs")


class SimilarityMatch(Base):
    __tablename__ = "similarity_matches"
    __table_args__ = (
        UniqueConstraint("version_a_id", "version_b_id", name="uq_version_match_pair"),
        Index("idx_matches_classroom", "classroom_id"),
        Index("idx_matches_sub_a", "submission_a_id"),
        Index("idx_matches_sub_b", "submission_b_id"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    classroom_id = Column(String(36), ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False)
    submission_a_id = Column(String(36), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    submission_b_id = Column(String(36), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    version_a_id = Column(String(36), ForeignKey("submission_versions.id", ondelete="CASCADE"), nullable=False)
    version_b_id = Column(String(36), ForeignKey("submission_versions.id", ondelete="CASCADE"), nullable=False)
    similarity_a_to_b = Column(Float, nullable=False)
    similarity_b_to_a = Column(Float, nullable=False)
    shared_fingerprint_count = Column(Integer, nullable=False, default=0)
    engine_version = Column(String(20), default="1.0.0", nullable=False)
    matched_functions_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    classroom = relationship("Classroom", back_populates="matches")
    regions = relationship("MatchRegion", back_populates="match", cascade="all, delete-orphan")


class MatchRegion(Base):
    __tablename__ = "match_regions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    similarity_match_id = Column(String(36), ForeignKey("similarity_matches.id", ondelete="CASCADE"), nullable=False, index=True)
    version_a_start_line = Column(Integer, nullable=False)
    version_a_end_line = Column(Integer, nullable=False)
    version_b_start_line = Column(Integer, nullable=False)
    version_b_end_line = Column(Integer, nullable=False)
    matched_token_count = Column(Integer, nullable=False)
    region_score = Column(Float, default=1.0, nullable=False)
    match_type = Column(String(20), default="EXACT", nullable=False)  # EXACT or LOGICAL
    function_name = Column(String(100), nullable=True)
    peer_function_name = Column(String(100), nullable=True)

    match = relationship("SimilarityMatch", back_populates="regions")
