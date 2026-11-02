"""
Assignment Submission API Endpoints.
Privacy: Every participant can only view and manage their own submission.
"""

from typing import List
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...models.classroom import ClassroomMember
from ...models.submission import Submission, SubmissionVersion
from ...models.user import User
from ...schemas.common import ApiResponse
from ...schemas.submission import (
    SubmissionResponse,
    SubmissionStatusResponse,
    SubmissionVersionResponse,
)
from ...services.analysis_service import AnalysisService
from ...services.classroom_service import ClassroomService
from ...services.submission_service import SubmissionService, SubmissionValidationError
from ..deps import get_classroom_membership, get_current_user

router = APIRouter(prefix="/classrooms/{classroom_id}/submissions", tags=["Submissions"])


def trigger_analysis_task(classroom_id: str):
    """Background task to run similarity analysis safely without blocking HTTP response."""
    from ...core.database import SessionLocal
    db = SessionLocal()
    try:
        service = AnalysisService()
        service.run_classroom_analysis(db, classroom_id)
    except Exception as e:
        print(f"Error executing analysis: {e}")
    finally:
        db.close()


@router.post("", response_model=ApiResponse[SubmissionResponse])
async def upload_submission(
    classroom_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    membership: ClassroomMember = Depends(get_classroom_membership),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        content = await file.read()
        sub, ver, should_analyze = SubmissionService.submit_assignment(
            db, classroom_id, current_user, file.filename, content
        )

        if should_analyze:
            background_tasks.add_task(trigger_analysis_task, classroom_id)

        source_code = content.decode("utf-8", errors="replace")

        return ApiResponse(
            success=True,
            data=SubmissionResponse(
                id=sub.id,
                classroom_id=sub.classroom_id,
                status=sub.status,
                current_version=SubmissionVersionResponse(
                    id=ver.id,
                    version_number=ver.version_number,
                    sha256_hash=ver.sha256_hash,
                    file_size=ver.file_size,
                    original_filename=ver.original_filename,
                    language=ver.language,
                    processing_status=ver.processing_status,
                    created_at=ver.created_at,
                ),
                submitted_at=sub.submitted_at,
                updated_at=sub.updated_at,
                raw_code=source_code,
            ),
            message="Submission uploaded successfully",
        )
    except (SubmissionValidationError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "UPLOAD_REJECTED", "message": str(e)},
        )


@router.get("/me", response_model=ApiResponse[SubmissionResponse])
def get_my_submission(
    classroom_id: str,
    membership: ClassroomMember = Depends(get_classroom_membership),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sub, ver, code = SubmissionService.get_user_active_submission(db, classroom_id, current_user.id)
    if not sub or not ver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NO_SUBMISSION", "message": "You have not submitted an assignment to this classroom"},
        )

    return ApiResponse(
        success=True,
        data=SubmissionResponse(
            id=sub.id,
            classroom_id=sub.classroom_id,
            status=sub.status,
            current_version=SubmissionVersionResponse(
                id=ver.id,
                version_number=ver.version_number,
                sha256_hash=ver.sha256_hash,
                file_size=ver.file_size,
                original_filename=ver.original_filename,
                language=ver.language,
                processing_status=ver.processing_status,
                created_at=ver.created_at,
            ),
            submitted_at=sub.submitted_at,
            updated_at=sub.updated_at,
            raw_code=code,
        ),
        message="Active submission retrieved",
    )


@router.get("/me/status", response_model=ApiResponse[SubmissionStatusResponse])
def get_my_submission_status(
    classroom_id: str,
    membership: ClassroomMember = Depends(get_classroom_membership),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sub, ver, _ = SubmissionService.get_user_active_submission(db, classroom_id, current_user.id)
    p_count, v_count = ClassroomService.get_classroom_counts(db, classroom_id)
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    threshold = classroom.min_submissions if classroom else 5

    version_count = len(sub.versions) if sub else 0

    return ApiResponse(
        success=True,
        data=SubmissionStatusResponse(
            has_submission=sub is not None,
            status=sub.status if sub else None,
            version_count=version_count,
            submitted_at=sub.submitted_at if sub else None,
            classroom_threshold_met=v_count >= threshold,
            valid_submissions=v_count,
            threshold=threshold,
        ),
        message="Submission status",
    )


@router.post("/me/resubmit", response_model=ApiResponse[SubmissionResponse])
async def resubmit_assignment(
    classroom_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    membership: ClassroomMember = Depends(get_classroom_membership),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Resubmission delegates to submit_assignment which handles version increments
    return await upload_submission(classroom_id, background_tasks, file, membership, current_user, db)


@router.get("/me/versions", response_model=ApiResponse[List[SubmissionVersionResponse]])
def get_my_submission_versions(
    classroom_id: str,
    membership: ClassroomMember = Depends(get_classroom_membership),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sub = (
        db.query(Submission)
        .filter(Submission.classroom_id == classroom_id, Submission.member_id == membership.id)
        .first()
    )
    if not sub:
        return ApiResponse(success=True, data=[], message="No versions")

    versions = (
        db.query(SubmissionVersion)
        .filter(SubmissionVersion.submission_id == sub.id)
        .order_by(SubmissionVersion.version_number.desc())
        .all()
    )

    return ApiResponse(
        success=True,
        data=[
            SubmissionVersionResponse(
                id=v.id,
                version_number=v.version_number,
                sha256_hash=v.sha256_hash,
                file_size=v.file_size,
                original_filename=v.original_filename,
                language=v.language,
                processing_status=v.processing_status,
                created_at=v.created_at,
            )
            for v in versions
        ],
        message="Submission versions",
    )


@router.delete("/me", response_model=ApiResponse[dict])
def withdraw_submission(
    classroom_id: str,
    membership: ClassroomMember = Depends(get_classroom_membership),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    success = SubmissionService.remove_user_submission(db, classroom_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NO_SUBMISSION", "message": "No active submission found to withdraw"},
        )
    return ApiResponse(success=True, data={}, message="Your submission has been withdrawn successfully")
