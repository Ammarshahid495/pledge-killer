"""
Similarity Analysis Scheduling and Execution Service.
Implements Stanford MOSS-grade comparisons, incremental analysis, and private report generation.
"""

from datetime import datetime, timezone
import json
import os
import sys
from typing import Dict, List, Optional, Set, Tuple
from sqlalchemy.orm import Session

# Ensure similarity-engine is importable
engine_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "similarity-engine"))
if engine_path not in sys.path:
    sys.path.insert(0, engine_path)

from engine import SimilarityEngine, ProcessedSubmission, ComparisonResult

from ..core.config import settings
from ..models.classroom import Classroom, ClassroomMember
from ..models.submission import Submission, SubmissionVersion
from ..models.analysis import AnalysisJob, SimilarityMatch, MatchRegion
from ..models.report import PrivateReport
from ..storage.storage_driver import StorageDriver
from ..storage.local_storage import get_storage_driver


class AnalysisService:
    def __init__(self, storage: Optional[StorageDriver] = None):
        self.storage = storage or get_storage_driver()
        self.engine = SimilarityEngine(k=8, w=4, min_matching_tokens=8)

    def run_classroom_analysis(self, db: Session, classroom_id: str) -> Optional[AnalysisJob]:
        """
        Runs or updates similarity analysis for a classroom with >= 5 valid submissions.
        Supports both initial analysis and incremental updates.
        """
        classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
        if not classroom:
            return None

        # Fetch active submissions with valid current versions
        active_submissions = (
            db.query(Submission)
            .filter(
                Submission.classroom_id == classroom_id,
                Submission.status == "ACTIVE",
                Submission.current_version_id.isnot(None),
            )
            .all()
        )

        min_required = classroom.min_submissions if classroom.min_submissions else settings.MIN_SUBMISSION_THRESHOLD
        if len(active_submissions) < min_required:
            classroom.status = "WAITING_FOR_SUBMISSIONS"
            db.commit()
            return None

        # Create or update analysis job record
        job = AnalysisJob(
            classroom_id=classroom_id,
            status="PROCESSING",
            job_type="INITIAL" if classroom.status != "COMPLETED" else "INCREMENTAL",
            engine_version="1.0.0",
            started_at=datetime.now(timezone.utc),
        )
        db.add(job)
        classroom.status = "ANALYZING"
        db.commit()
        db.refresh(job)

        try:
            ignore_hashes: Set[int] = set()
            starter_filename = classroom.starter_filename
            if classroom.starter_storage_key:
                starter_bytes = self.storage.get_file_content(classroom.starter_storage_key)
                if starter_bytes:
                    starter_code = starter_bytes.decode("utf-8", errors="replace")
                    ignore_hashes = self.engine.starter_fingerprint_hashes(starter_code)

            # 1. Load and process all active submissions
            processed_map: Dict[str, Tuple[ProcessedSubmission, SubmissionVersion, str]] = {}
            # submission_id -> (ProcessedSubmission, SubmissionVersion, user_id)

            for sub in active_submissions:
                version = (
                    db.query(SubmissionVersion)
                    .filter(SubmissionVersion.id == sub.current_version_id)
                    .first()
                )
                if not version:
                    continue

                content_bytes = self.storage.get_file_content(version.storage_key)
                if not content_bytes:
                    continue

                source_code = content_bytes.decode("utf-8", errors="replace")
                processed = self.engine.process_source(sub.id, source_code)

                # Get user_id from member
                member = db.query(ClassroomMember).filter(ClassroomMember.id == sub.member_id).first()
                user_id = member.user_id if member else ""

                processed_map[sub.id] = (processed, version, user_id)

            # 2. Pairwise comparison of all active submissions
            sub_ids = sorted(list(processed_map.keys()))
            n = len(sub_ids)

            for i in range(n):
                for j in range(i + 1, n):
                    sub_a_id = sub_ids[i]
                    sub_b_id = sub_ids[j]

                    processed_a, ver_a, _ = processed_map[sub_a_id]
                    processed_b, ver_b, _ = processed_map[sub_b_id]

                    # Deterministic ordering: a_id < b_id
                    if sub_a_id > sub_b_id:
                        sub_a_id, sub_b_id = sub_b_id, sub_a_id
                        processed_a, processed_b = processed_b, processed_a
                        ver_a, ver_b = ver_b, ver_a

                    # Check if match already computed for this exact version pair (incremental reuse)
                    existing_match = (
                        db.query(SimilarityMatch)
                        .filter(
                            SimilarityMatch.version_a_id == ver_a.id,
                            SimilarityMatch.version_b_id == ver_b.id,
                        )
                        .first()
                    )

                    if existing_match:
                        continue  # Re-use unchanged pair result

                    # Perform comparison, excluding shared starter/boilerplate fingerprints
                    result: ComparisonResult = self.engine.compare_submissions(
                        processed_a,
                        processed_b,
                        ignore_fingerprint_hashes=ignore_hashes or None,
                    )

                    # Persist similarity match
                    match_record = SimilarityMatch(
                        classroom_id=classroom_id,
                        submission_a_id=sub_a_id,
                        submission_b_id=sub_b_id,
                        version_a_id=ver_a.id,
                        version_b_id=ver_b.id,
                        similarity_a_to_b=result.similarity_a_to_b,
                        similarity_b_to_a=result.similarity_b_to_a,
                        shared_fingerprint_count=result.shared_fingerprint_count,
                        engine_version=result.engine_version,
                        matched_functions_json=json.dumps(result.matched_functions) if result.matched_functions else None,
                    )
                    db.add(match_record)
                    db.flush()

                    # Persist match regions
                    for r in result.regions:
                        region_record = MatchRegion(
                            similarity_match_id=match_record.id,
                            version_a_start_line=r["a_start_line"],
                            version_a_end_line=r["a_end_line"],
                            version_b_start_line=r["b_start_line"],
                            version_b_end_line=r["b_end_line"],
                            matched_token_count=r["matched_token_count"],
                            region_score=r["region_score"],
                            match_type=r.get("match_type", "EXACT"),
                            function_name=r.get("function_name"),
                            peer_function_name=r.get("peer_function_name"),
                        )
                        db.add(region_record)

            db.commit()

            # 3. Generate or update private report for each participant
            self._generate_private_reports(
                db,
                classroom_id,
                processed_map,
                starter_ignored=bool(ignore_hashes),
                starter_filename=starter_filename,
            )

            # Mark job completed
            job.status = "COMPLETED"
            job.completed_at = datetime.now(timezone.utc)
            classroom.status = "COMPLETED"
            db.commit()
            return job

        except Exception as e:
            db.rollback()
            job.status = "FAILED"
            job.error_code = str(e)[:50]
            classroom.status = "ACTIVE"
            db.commit()
            raise e

    def _generate_private_reports(
        self,
        db: Session,
        classroom_id: str,
        processed_map: Dict[str, Tuple[ProcessedSubmission, SubmissionVersion, str]],
        starter_ignored: bool = False,
        starter_filename: Optional[str] = None,
    ):
        """
        Builds private reports for each participant.
        Reports contain strictly the user's own metrics and anonymous peer labels.
        """
        # Fetch anonymous labels for all members in the classroom
        members = db.query(ClassroomMember).filter(ClassroomMember.classroom_id == classroom_id).all()
        # map submission_id -> anonymous_label
        sub_to_label: Dict[str, str] = {}
        for m in members:
            for s in m.submissions:
                sub_to_label[s.id] = m.anonymous_label

        for sub_id, (proc, ver, user_id) in processed_map.items():
            if not user_id:
                continue

            # Find all matches involving sub_id with active versions
            matches_as_a = (
                db.query(SimilarityMatch)
                .filter(SimilarityMatch.submission_a_id == sub_id, SimilarityMatch.version_a_id == ver.id)
                .all()
            )
            matches_as_b = (
                db.query(SimilarityMatch)
                .filter(SimilarityMatch.submission_b_id == sub_id, SimilarityMatch.version_b_id == ver.id)
                .all()
            )

            highest_sim = 0.0
            comparisons_count = len(matches_as_a) + len(matches_as_b)
            total_matching_regions = 0

            for m in matches_as_a:
                highest_sim = max(highest_sim, m.similarity_a_to_b)
                total_matching_regions += len(m.regions)

            for m in matches_as_b:
                highest_sim = max(highest_sim, m.similarity_b_to_a)
                total_matching_regions += len(m.regions)

            summary = {
                "highest_similarity": round(highest_sim, 2),
                "comparisons_count": comparisons_count,
                "total_matching_regions": total_matching_regions,
                "engine_version": "1.0.0",
                "starter_ignored": starter_ignored,
                "starter_filename": starter_filename,
            }

            # Check if report already exists for this user in this classroom
            report = (
                db.query(PrivateReport)
                .filter(
                    PrivateReport.classroom_id == classroom_id,
                    PrivateReport.user_id == user_id,
                )
                .first()
            )

            if report:
                report.submission_id = sub_id
                report.report_version += 1
                report.status = "UPDATED"
                report.summary_metrics = json.dumps(summary)
                report.generated_at = datetime.now(timezone.utc)
            else:
                report = PrivateReport(
                    classroom_id=classroom_id,
                    user_id=user_id,
                    submission_id=sub_id,
                    report_version=1,
                    status="GENERATED",
                    summary_metrics=json.dumps(summary),
                    generated_at=datetime.now(timezone.utc),
                )
                db.add(report)

        db.commit()
