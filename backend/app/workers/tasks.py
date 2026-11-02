"""
Celery Task Definitions for Pledge Fighter.
"""

from celery import Celery
import os
from ..core.config import settings

celery_app = Celery(
    "pledge_fighter_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(name="tasks.run_similarity_analysis", bind=True, max_retries=3)
def run_similarity_analysis_task(self, classroom_id: str):
    from ..core.database import SessionLocal
    from ..services.analysis_service import AnalysisService

    db = SessionLocal()
    try:
        service = AnalysisService()
        job = service.run_classroom_analysis(db, classroom_id)
        return {"status": "success", "classroom_id": classroom_id, "job_id": job.id if job else None}
    except Exception as exc:
        db.close()
        raise self.retry(exc=exc, countdown=10)
    finally:
        db.close()
