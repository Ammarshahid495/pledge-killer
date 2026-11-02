"""
Private Similarity Report Retrieval Service.
Enforces strict privacy: users can only view their own report and highlights on their own source code.
"""

import json
from typing import List, Optional
from sqlalchemy.orm import Session
from ..models.classroom import Classroom, ClassroomMember
from ..models.submission import Submission, SubmissionVersion
from ..models.analysis import SimilarityMatch, MatchRegion
from ..models.report import PrivateReport
from ..schemas.report import (
    FunctionMatchDetailResponse,
    MatchDetailResponse,
    MatchRegionResponse,
    PrivateReportDetailResponse,
    PrivateReportSummaryResponse,
)
from ..storage.storage_driver import StorageDriver
from ..storage.local_storage import get_storage_driver


class ReportService:
    @staticmethod
    def get_user_reports_summary(db: Session, user_id: str) -> List[PrivateReportSummaryResponse]:
        reports = (
            db.query(PrivateReport)
            .filter(PrivateReport.user_id == user_id)
            .order_by(PrivateReport.generated_at.desc())
            .all()
        )

        summaries: List[PrivateReportSummaryResponse] = []
        for r in reports:
            classroom = db.query(Classroom).filter(Classroom.id == r.classroom_id).first()
            metrics = json.loads(r.summary_metrics) if r.summary_metrics else {}

            summaries.append(
                PrivateReportSummaryResponse(
                    report_id=r.id,
                    classroom_id=r.classroom_id,
                    classroom_title=classroom.title if classroom else "Classroom",
                    submission_id=r.submission_id,
                    report_version=r.report_version,
                    status=r.status,
                    highest_similarity=metrics.get("highest_similarity", 0.0),
                    comparisons_count=metrics.get("comparisons_count", 0),
                    total_matching_regions=metrics.get("total_matching_regions", 0),
                    generated_at=r.generated_at,
                    engine_version=metrics.get("engine_version", "1.0.0"),
                    starter_ignored=bool(metrics.get("starter_ignored", False)),
                    starter_filename=metrics.get("starter_filename"),
                )
            )
        return summaries

    @staticmethod
    def get_report_detail(
        db: Session,
        report_id: str,
        user_id: str,
        storage: Optional[StorageDriver] = None,
    ) -> PrivateReportDetailResponse:
        storage = storage or get_storage_driver()

        report = db.query(PrivateReport).filter(PrivateReport.id == report_id).first()
        if not report:
            raise ValueError("Report not found")

        # Strict ownership check
        if report.user_id != user_id:
            raise PermissionError("Access denied: You do not own this report")

        classroom = db.query(Classroom).filter(Classroom.id == report.classroom_id).first()
        metrics = json.loads(report.summary_metrics) if report.summary_metrics else {}

        # Fetch user's active submission version and source code
        submission = db.query(Submission).filter(Submission.id == report.submission_id).first()
        my_source_code = ""
        current_version_id = submission.current_version_id if submission else None

        if current_version_id:
            version = db.query(SubmissionVersion).filter(SubmissionVersion.id == current_version_id).first()
            if version:
                raw_bytes = storage.get_file_content(version.storage_key)
                if raw_bytes:
                    my_source_code = raw_bytes.decode("utf-8", errors="replace")

        # Map submission_id to anonymous label in this classroom
        members = db.query(ClassroomMember).filter(ClassroomMember.classroom_id == report.classroom_id).all()
        sub_to_label = {}
        for m in members:
            for s in m.submissions:
                sub_to_label[s.id] = m.anonymous_label

        # Fetch matches
        matches_as_a = (
            db.query(SimilarityMatch)
            .filter(
                SimilarityMatch.submission_a_id == report.submission_id,
                SimilarityMatch.version_a_id == current_version_id,
            )
            .all()
        )
        matches_as_b = (
            db.query(SimilarityMatch)
            .filter(
                SimilarityMatch.submission_b_id == report.submission_id,
                SimilarityMatch.version_b_id == current_version_id,
            )
            .all()
        )

        match_details: List[MatchDetailResponse] = []
        all_my_regions: List[MatchRegionResponse] = []

        for m in matches_as_a:
            peer_label = sub_to_label.get(m.submission_b_id, "Anonymous Peer")
            regions_resp: List[MatchRegionResponse] = []
            for r in m.regions:
                reg = MatchRegionResponse(
                    my_start_line=r.version_a_start_line,
                    my_end_line=r.version_a_end_line,
                    peer_start_line=r.version_b_start_line,
                    peer_end_line=r.version_b_end_line,
                    matched_token_count=r.matched_token_count,
                    region_score=r.region_score,
                    match_type=getattr(r, "match_type", "EXACT") or "EXACT",
                    function_name=getattr(r, "function_name", None),
                    peer_function_name=getattr(r, "peer_function_name", None),
                )
                regions_resp.append(reg)
                all_my_regions.append(reg)

            func_list = json.loads(m.matched_functions_json) if getattr(m, "matched_functions_json", None) else []
            matched_funcs = [
                FunctionMatchDetailResponse(
                    function_name=f.get("function_name", "Function"),
                    peer_function_name=f.get("peer_function_name", "Function"),
                    my_start_line=f.get("my_start_line", 1),
                    my_end_line=f.get("my_end_line", 1),
                    peer_start_line=f.get("peer_start_line", 1),
                    peer_end_line=f.get("peer_end_line", 1),
                    similarity_percentage=f.get("similarity_percentage", 100.0),
                    matched_tokens=f.get("matched_tokens", 0),
                    total_function_tokens=f.get("total_function_tokens", 0),
                    match_type=f.get("match_type", "EXACT"),
                    verdict=f.get("verdict", "Matching function"),
                )
                for f in func_list
            ]

            match_details.append(
                MatchDetailResponse(
                    match_id=m.id,
                    peer_label=peer_label,
                    similarity_score=m.similarity_a_to_b,
                    directional_coverage_to_peer=m.similarity_a_to_b,
                    directional_coverage_from_peer=m.similarity_b_to_a,
                    shared_fingerprint_count=m.shared_fingerprint_count,
                    matched_token_count=sum(r.matched_token_count for r in regions_resp),
                    regions=regions_resp,
                    matched_functions=matched_funcs,
                    explanation=(
                        f"{m.similarity_a_to_b}% of your code matches structural token patterns in {peer_label}'s submission. "
                        "Matching regions indicate syntactic similarity and shared algorithmic structure."
                    ),
                )
            )

        for m in matches_as_b:
            peer_label = sub_to_label.get(m.submission_a_id, "Anonymous Peer")
            regions_resp: List[MatchRegionResponse] = []
            for r in m.regions:
                reg = MatchRegionResponse(
                    my_start_line=r.version_b_start_line,
                    my_end_line=r.version_b_end_line,
                    peer_start_line=r.version_a_start_line,
                    peer_end_line=r.version_a_end_line,
                    matched_token_count=r.matched_token_count,
                    region_score=r.region_score,
                    match_type=getattr(r, "match_type", "EXACT") or "EXACT",
                    function_name=getattr(r, "peer_function_name", None),
                    peer_function_name=getattr(r, "function_name", None),
                )
                regions_resp.append(reg)
                all_my_regions.append(reg)

            func_list = json.loads(m.matched_functions_json) if getattr(m, "matched_functions_json", None) else []
            matched_funcs = [
                FunctionMatchDetailResponse(
                    function_name=f.get("peer_function_name", "Function"),
                    peer_function_name=f.get("function_name", "Function"),
                    my_start_line=f.get("peer_start_line", 1),
                    my_end_line=f.get("peer_end_line", 1),
                    peer_start_line=f.get("my_start_line", 1),
                    peer_end_line=f.get("my_end_line", 1),
                    similarity_percentage=f.get("similarity_percentage", 100.0),
                    matched_tokens=f.get("matched_tokens", 0),
                    total_function_tokens=f.get("total_function_tokens", 0),
                    match_type=f.get("match_type", "EXACT"),
                    verdict=f.get("verdict", "Matching function"),
                )
                for f in func_list
            ]

            match_details.append(
                MatchDetailResponse(
                    match_id=m.id,
                    peer_label=peer_label,
                    similarity_score=m.similarity_b_to_a,
                    directional_coverage_to_peer=m.similarity_b_to_a,
                    directional_coverage_from_peer=m.similarity_a_to_b,
                    shared_fingerprint_count=m.shared_fingerprint_count,
                    matched_token_count=sum(r.matched_token_count for r in regions_resp),
                    regions=regions_resp,
                    matched_functions=matched_funcs,
                    explanation=(
                        f"{m.similarity_b_to_a}% of your code matches structural token patterns in {peer_label}'s submission. "
                        "Matching regions indicate syntactic similarity and shared algorithmic structure."
                    ),
                )
            )

        # Sort matches by similarity descending
        match_details.sort(key=lambda x: x.similarity_score, reverse=True)

        return PrivateReportDetailResponse(
            report_id=report.id,
            classroom_id=report.classroom_id,
            classroom_title=classroom.title if classroom else "Classroom",
            submission_id=report.submission_id,
            report_version=report.report_version,
            status=report.status,
            highest_similarity=metrics.get("highest_similarity", 0.0),
            comparisons_count=len(match_details),
            total_matching_regions=len(all_my_regions),
            generated_at=report.generated_at,
            engine_version=metrics.get("engine_version", "1.0.0"),
            starter_ignored=bool(metrics.get("starter_ignored", False)),
            starter_filename=metrics.get("starter_filename"),
            my_source_code=my_source_code,
            matches=match_details,
            all_regions=all_my_regions,
        )
