"""
PrivateReport and AuditLog Database Models.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import relationship
from ..core.database import Base
from .user import generate_uuid, utc_now


class PrivateReport(Base):
    __tablename__ = "private_reports"
    __table_args__ = (
        Index("idx_reports_user", "user_id"),
        Index("idx_reports_classroom", "classroom_id"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    classroom_id = Column(String(36), ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    submission_id = Column(String(36), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    report_version = Column(Integer, default=1, nullable=False)
    status = Column(String(20), default="GENERATED", nullable=False)  # GENERATED, UPDATED
    summary_metrics = Column(Text, nullable=False)  # JSON serialized summary
    generated_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    classroom = relationship("Classroom", back_populates="reports")
    user = relationship("User", back_populates="reports")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    actor_user_id = Column(String(36), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(36), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    metadata_json = Column(Text, nullable=True)
