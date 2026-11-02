"""
Private Similarity Report Schemas.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class MatchRegionResponse(BaseModel):
    my_start_line: int
    my_end_line: int
    peer_start_line: Optional[int] = None
    peer_end_line: Optional[int] = None
    matched_token_count: int
    region_score: float
    match_type: str = "EXACT"  # "EXACT" (Green) or "LOGICAL" (Red)
    function_name: Optional[str] = None
    peer_function_name: Optional[str] = None


class FunctionMatchDetailResponse(BaseModel):
    function_name: str
    peer_function_name: str
    my_start_line: int
    my_end_line: int
    peer_start_line: int
    peer_end_line: int
    similarity_percentage: float
    matched_tokens: int
    total_function_tokens: int
    match_type: str  # "EXACT" (Green) or "LOGICAL" (Red)
    verdict: str


class MatchDetailResponse(BaseModel):
    match_id: str
    peer_label: str  # e.g. "Peer A", "Peer B" (NEVER name or email)
    similarity_score: float
    directional_coverage_to_peer: float
    directional_coverage_from_peer: float
    shared_fingerprint_count: int
    matched_token_count: int
    regions: List[MatchRegionResponse]
    matched_functions: List[FunctionMatchDetailResponse] = []
    explanation: str


class PrivateReportSummaryResponse(BaseModel):
    report_id: str
    classroom_id: str
    classroom_title: str
    submission_id: str
    report_version: int
    status: str
    highest_similarity: float
    comparisons_count: int
    total_matching_regions: int
    generated_at: datetime
    engine_version: str
    starter_ignored: bool = False
    starter_filename: Optional[str] = None


class PrivateReportDetailResponse(PrivateReportSummaryResponse):
    my_source_code: str
    matches: List[MatchDetailResponse]
    all_regions: List[MatchRegionResponse]
