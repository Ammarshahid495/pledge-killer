"""
Analysis Schemas.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AnalysisStatusResponse(BaseModel):
    classroom_id: str
    status: str  # ACTIVE, WAITING_FOR_SUBMISSIONS, ANALYZING, COMPLETED
    active_submissions: int
    threshold: int
    can_trigger: bool
    latest_job_id: Optional[str] = None
    last_analyzed_at: Optional[datetime] = None


class TriggerAnalysisResponse(BaseModel):
    job_id: Optional[str]
    status: str
    message: str
