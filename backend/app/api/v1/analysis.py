"""
Classroom Similarity Analysis API Endpoints.
Enforces the mandatory 5-submission threshold rule.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...models.analysis import AnalysisJob
from ...models.classroom import Classroom, ClassroomMember
from ...models.submission import Submission
from ...schemas.analysis import AnalysisStatusResponse, TriggerAnalysisResponse
from ...schemas.common import ApiResponse
from ...services.analysis_service import AnalysisService
from ...services.classroom_service import ClassroomService
from ..deps import get_classroom_membership, get_current_user

router = APIRouter(prefix="/classrooms/{classroom_id}/analysis", tags=["Analysis"])


def trigger_analysis_job(classroom_id: str):
    from ...core.database import SessionLocal
    db = SessionLocal()
    try:
        service = AnalysisService()
        service.run_classroom_analysis(db, classroom_id)
    except Exception as e:
        print(f"Error executing analysis: {e}")
    finally:
        db.close()


@router.get("/status", response_model=ApiResponse[AnalysisStatusResponse])
def get_analysis_status(
    classroom_id: str,
    membership: ClassroomMember = Depends(get_classroom_membership),
    db: Session = Depends(get_db),
):
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    p_count, v_count = ClassroomService.get_classroom_counts(db, classroom_id)

    latest_job = (
        db.query(AnalysisJob)
        .filter(AnalysisJob.classroom_id == classroom_id)
        .order_by(AnalysisJob.created_at.desc())
        .first()
    )

    threshold = classroom.min_submissions if classroom else 5

    return ApiResponse(
        success=True,
        data=AnalysisStatusResponse(
            classroom_id=classroom_id,
            status=classroom.status,
            active_submissions=v_count,
            threshold=threshold,
            can_trigger=v_count >= threshold,
            latest_job_id=latest_job.id if latest_job else None,
            last_analyzed_at=latest_job.completed_at if latest_job else None,
        ),
        message="Analysis status retrieved",
    )


@router.post("/request", response_model=ApiResponse[TriggerAnalysisResponse])
def request_analysis(
    classroom_id: str,
    background_tasks: BackgroundTasks,
    membership: ClassroomMember = Depends(get_classroom_membership),
    db: Session = Depends(get_db),
):
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    threshold = classroom.min_submissions if classroom else 5

    _, v_count = ClassroomService.get_classroom_counts(db, classroom_id)
    if v_count < threshold:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "THRESHOLD_NOT_MET",
                "message": f"At least {threshold} distinct valid submissions are required before analysis (currently {v_count}/{threshold})",
            },
        )

    # Queue execution
    background_tasks.add_task(trigger_analysis_job, classroom_id)

    return ApiResponse(
        success=True,
        data=TriggerAnalysisResponse(
            job_id=None,
            status="QUEUED",
            message="Analysis job queued successfully",
        ),
        message="Analysis triggered",
    )
