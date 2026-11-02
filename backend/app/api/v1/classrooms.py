"""
Classroom API Endpoints.
Equal permissions enforced: all classroom participants have the exact same capabilities.
"""

from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.security import generate_secure_token, hash_token
from ...models.classroom import Classroom, ClassroomMember
from ...models.report import PrivateReport
from ...models.submission import Submission
from ...models.user import User
from ...schemas.classroom import (
    ClassroomCreate,
    ClassroomDetailResponse,
    ClassroomMemberResponse,
    ClassroomResponse,
    ClassroomStatusResponse,
    StarterTemplateResponse,
)
from ...schemas.common import ApiResponse
from ...services.classroom_service import ClassroomService
from ...services.submission_service import SubmissionValidationError
from ..deps import get_classroom_membership, get_current_user

router = APIRouter(prefix="/classrooms", tags=["Classrooms"])


@router.post("", response_model=ApiResponse[ClassroomResponse])
def create_classroom(
    req: ClassroomCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    base_url = str(request.base_url).rstrip("/")
    classroom, join_url = ClassroomService.create_classroom(db, current_user, req, base_url)

    participant_count, valid_count = ClassroomService.get_classroom_counts(db, classroom.id)

    return ApiResponse(
        success=True,
        data=ClassroomResponse(
            id=classroom.id,
            title=classroom.title,
            description=classroom.description,
            language=classroom.language,
            status=classroom.status,
            min_submissions=classroom.min_submissions,
            deadline=classroom.deadline,
            max_participants=classroom.max_participants,
            created_at=classroom.created_at,
            participant_count=participant_count,
            valid_submission_count=valid_count,
            threshold_met=valid_count >= classroom.min_submissions,
            my_anonymous_label="Peer A",
            join_token=classroom.join_token,
            join_url=join_url,
        ),
        message="Classroom created successfully",
    )


@router.get("", response_model=ApiResponse[List[ClassroomResponse]])
def list_my_classrooms(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classrooms = ClassroomService.get_user_classrooms(db, current_user.id)
    results = []

    for c in classrooms:
        p_count, v_count = ClassroomService.get_classroom_counts(db, c.id)
        # Find user's member label
        m = (
            db.query(ClassroomMember)
            .filter(ClassroomMember.classroom_id == c.id, ClassroomMember.user_id == current_user.id)
            .first()
        )
        results.append(
            ClassroomResponse(
                id=c.id,
                title=c.title,
                description=c.description,
                language=c.language,
                status=c.status,
                min_submissions=c.min_submissions,
                deadline=c.deadline,
                max_participants=c.max_participants,
                created_at=c.created_at,
                participant_count=p_count,
                valid_submission_count=v_count,
                threshold_met=v_count >= c.min_submissions,
                my_anonymous_label=m.anonymous_label if m else None,
            )
        )

    return ApiResponse(success=True, data=results, message="My classrooms")


@router.get("/{classroom_id}", response_model=ApiResponse[ClassroomDetailResponse])
def get_classroom_detail(
    classroom_id: str,
    membership: ClassroomMember = Depends(get_classroom_membership),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CLASSROOM_NOT_FOUND", "message": "Classroom not found"},
        )

    # Ensure join_token is always populated
    if not classroom.join_token:
        raw_token = generate_secure_token(32)
        classroom.join_token = raw_token
        classroom.join_token_hash = hash_token(raw_token)
        db.commit()
        db.refresh(classroom)

    p_count, v_count = ClassroomService.get_classroom_counts(db, classroom.id)

    # Check user submission
    sub = (
        db.query(Submission)
        .filter(
            Submission.classroom_id == classroom_id,
            Submission.member_id == membership.id,
            Submission.status == "ACTIVE",
            Submission.current_version_id.isnot(None),
        )
        .first()
    )

    # Check user report
    rep = (
        db.query(PrivateReport)
        .filter(
            PrivateReport.classroom_id == classroom_id,
            PrivateReport.user_id == current_user.id,
        )
        .first()
    )

    return ApiResponse(
        success=True,
        data=ClassroomDetailResponse(
            id=classroom.id,
            title=classroom.title,
            description=classroom.description,
            language=classroom.language,
            status=classroom.status,
            min_submissions=classroom.min_submissions,
            deadline=classroom.deadline,
            max_participants=classroom.max_participants,
            created_at=classroom.created_at,
            participant_count=p_count,
            valid_submission_count=v_count,
            threshold_met=v_count >= classroom.min_submissions,
            my_anonymous_label=membership.anonymous_label,
            join_token=classroom.join_token,
            join_url=f"/join/{classroom.join_token}" if classroom.join_token else None,
            has_submitted=sub is not None,
            my_submission_id=sub.id if sub else None,
            has_report=rep is not None,
            my_report_id=rep.id if rep else None,
        ),
        message="Classroom details",
    )


@router.post("/join/{join_token:path}", response_model=ApiResponse[ClassroomResponse])
def join_classroom(
    join_token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        classroom = ClassroomService.join_classroom(db, current_user, join_token)
        p_count, v_count = ClassroomService.get_classroom_counts(db, classroom.id)

        m = (
            db.query(ClassroomMember)
            .filter(ClassroomMember.classroom_id == classroom.id, ClassroomMember.user_id == current_user.id)
            .first()
        )

        return ApiResponse(
            success=True,
            data=ClassroomResponse(
                id=classroom.id,
                title=classroom.title,
                description=classroom.description,
                language=classroom.language,
                status=classroom.status,
                min_submissions=classroom.min_submissions,
                deadline=classroom.deadline,
                max_participants=classroom.max_participants,
                created_at=classroom.created_at,
                participant_count=p_count,
                valid_submission_count=v_count,
                threshold_met=v_count >= classroom.min_submissions,
                my_anonymous_label=m.anonymous_label if m else None,
                join_token=classroom.join_token,
                join_url=f"/join/{classroom.join_token}" if classroom.join_token else None,
            ),
            message="Successfully joined classroom",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "JOIN_FAILED", "message": str(e)},
        )


@router.get("/{classroom_id}/members", response_model=ApiResponse[List[ClassroomMemberResponse]])
def get_classroom_members(
    classroom_id: str,
    membership: ClassroomMember = Depends(get_classroom_membership),
    db: Session = Depends(get_db),
):
    members = (
        db.query(ClassroomMember)
        .filter(ClassroomMember.classroom_id == classroom_id, ClassroomMember.status == "ACTIVE")
        .all()
    )

    # Privacy: only anonymous labels and join dates are exposed; NEVER emails or user ids
    return ApiResponse(
        success=True,
        data=[
            ClassroomMemberResponse(
                anonymous_label=m.anonymous_label,
                joined_at=m.joined_at,
                status=m.status,
            )
            for m in members
        ],
        message="Classroom members",
    )


@router.get("/{classroom_id}/status", response_model=ApiResponse[ClassroomStatusResponse])
def get_classroom_status(
    classroom_id: str,
    membership: ClassroomMember = Depends(get_classroom_membership),
    db: Session = Depends(get_db),
):
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    p_count, v_count = ClassroomService.get_classroom_counts(db, classroom_id)

    return ApiResponse(
        success=True,
        data=ClassroomStatusResponse(
            classroom_id=classroom_id,
            status=classroom.status,
            participant_count=p_count,
            valid_submission_count=v_count,
            threshold=classroom.min_submissions,
            threshold_met=v_count >= classroom.min_submissions,
            deadline=classroom.deadline,
        ),
        message="Classroom status",
    )


@router.post("/{classroom_id}/leave", response_model=ApiResponse[dict])
def leave_classroom(
    classroom_id: str,
    membership: ClassroomMember = Depends(get_classroom_membership),
    db: Session = Depends(get_db),
):
    membership.status = "LEFT"
    # Also withdraw active submission if any
    sub = (
        db.query(Submission)
        .filter(Submission.classroom_id == classroom_id, Submission.member_id == membership.id)
        .first()
    )
    if sub:
        sub.status = "WITHDRAWN"

    db.commit()
    return ApiResponse(success=True, data={}, message="Successfully left the classroom")
