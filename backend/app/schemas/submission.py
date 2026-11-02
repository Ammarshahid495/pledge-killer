"""
Submission and Version Schemas.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class SubmissionVersionResponse(BaseModel):
    id: str
    version_number: int
    sha256_hash: str
    file_size: int
    original_filename: str
    language: str
    processing_status: str
    created_at: datetime


class SubmissionResponse(BaseModel):
    id: str
    classroom_id: str
    status: str
    current_version: Optional[SubmissionVersionResponse] = None
    submitted_at: datetime
    updated_at: datetime
    raw_code: Optional[str] = None


class SubmissionStatusResponse(BaseModel):
    has_submission: bool
    status: Optional[str] = None
    version_count: int = 0
    submitted_at: Optional[datetime] = None
    classroom_threshold_met: bool = False
    valid_submissions: int = 0
    threshold: int = 5
