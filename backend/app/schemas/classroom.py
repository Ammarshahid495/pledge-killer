"""
Classroom and Membership Schemas.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ClassroomCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    language: str = "cpp"
    min_submissions: int = Field(default=5, ge=2, le=500)
    deadline: Optional[datetime] = None
    max_participants: Optional[int] = Field(None, ge=2, le=500)


class ClassroomResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    language: str
    status: str
    min_submissions: int = 5
    deadline: Optional[datetime] = None
    max_participants: Optional[int] = None
    created_at: datetime
    participant_count: int = 0
    valid_submission_count: int = 0
    threshold_met: bool = False
    my_anonymous_label: Optional[str] = None
    join_token: Optional[str] = None
    join_url: Optional[str] = None
    has_starter: bool = False
    starter_filename: Optional[str] = None


class ClassroomDetailResponse(ClassroomResponse):
    has_submitted: bool = False
    my_submission_id: Optional[str] = None
    has_report: bool = False
    my_report_id: Optional[str] = None
    starter_source: Optional[str] = None


class StarterTemplateResponse(BaseModel):
    has_starter: bool
    filename: Optional[str] = None
    source_code: Optional[str] = None
    sha256: Optional[str] = None


class ClassroomMemberResponse(BaseModel):
    anonymous_label: str
    joined_at: datetime
    status: str


class ClassroomStatusResponse(BaseModel):
    classroom_id: str
    status: str
    participant_count: int
    valid_submission_count: int
    threshold: int
    threshold_met: bool
    deadline: Optional[datetime] = None
