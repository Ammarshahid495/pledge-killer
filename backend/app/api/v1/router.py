"""
API v1 Router Aggregator.
"""

from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .classrooms import router as classrooms_router
from .submissions import router as submissions_router
from .analysis import router as analysis_router
from .reports import router as reports_router

api_router = APIRouter(prefix="/v1")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(classrooms_router)
api_router.include_router(submissions_router)
api_router.include_router(analysis_router)
api_router.include_router(reports_router)
