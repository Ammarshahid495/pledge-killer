"""
Private Reports API Endpoints.
Guarantees strict data isolation: participants can only access their own reports and highlighted code.
"""

import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...models.user import User
from ...schemas.common import ApiResponse
from ...schemas.report import (
    MatchDetailResponse,
    MatchRegionResponse,
    PrivateReportDetailResponse,
    PrivateReportSummaryResponse,
)
from ...services.report_service import ReportService
from ..deps import get_current_user

router = APIRouter(prefix="/reports", tags=["Private Reports"])


@router.get("/me", response_model=ApiResponse[List[PrivateReportSummaryResponse]])
def get_my_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    summaries = ReportService.get_user_reports_summary(db, current_user.id)
    return ApiResponse(success=True, data=summaries, message="User reports")


@router.get("/me/{report_id}", response_model=ApiResponse[PrivateReportDetailResponse])
def get_my_report_detail(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        report = ReportService.get_report_detail(db, report_id, current_user.id)
        return ApiResponse(success=True, data=report, message="Report details")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "REPORT_NOT_FOUND", "message": "Report does not exist"},
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "You are not authorized to view this report"},
        )


@router.get("/me/{report_id}/matches", response_model=ApiResponse[List[MatchDetailResponse]])
def get_my_report_matches(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        report = ReportService.get_report_detail(db, report_id, current_user.id)
        return ApiResponse(success=True, data=report.matches, message="Report matches")
    except (ValueError, PermissionError) as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "UNAUTHORIZED", "message": str(e)},
        )


@router.get("/me/{report_id}/regions", response_model=ApiResponse[List[MatchRegionResponse]])
def get_my_report_regions(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        report = ReportService.get_report_detail(db, report_id, current_user.id)
        return ApiResponse(success=True, data=report.all_regions, message="Matching regions")
    except (ValueError, PermissionError) as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "UNAUTHORIZED", "message": str(e)},
        )


@router.get("/me/{report_id}/download")
def download_my_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        report = ReportService.get_report_detail(db, report_id, current_user.id)

        # Generate a structured JSON report
        payload = report.model_dump()
        json_content = json.dumps(payload, indent=2, default=str)

        return Response(
            content=json_content,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=report_{report_id}.json"},
        )
    except (ValueError, PermissionError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Cannot download this report"},
        )
