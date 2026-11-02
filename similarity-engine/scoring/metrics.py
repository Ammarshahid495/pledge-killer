"""
Similarity Scoring and Honest Metrics Calculation for Pledge Fighter.
"""

from dataclasses import dataclass
from typing import List, Set

try:
    from comparison.matcher import MatchRegion
except ImportError:
    from ..comparison.matcher import MatchRegion


@dataclass
class ComparisonMetrics:
    similarity_a_to_b: float
    similarity_b_to_a: float
    symmetric_similarity: float
    shared_fingerprint_count: int
    matched_tokens_a: int
    matched_tokens_b: int
    total_tokens_a: int
    total_tokens_b: int
    regions: List[MatchRegion]
    explanation: str


def calculate_metrics(
    total_tokens_a: int,
    total_tokens_b: int,
    matched_tokens_a: Set[int],
    matched_tokens_b: Set[int],
    shared_fingerprint_count: int,
    regions: List[MatchRegion],
) -> ComparisonMetrics:
    count_a = len(matched_tokens_a)
    count_b = len(matched_tokens_b)

    cov_a_to_b = (count_a / total_tokens_a * 100.0) if total_tokens_a > 0 else 0.0
    cov_b_to_a = (count_b / total_tokens_b * 100.0) if total_tokens_b > 0 else 0.0

    denom = total_tokens_a + total_tokens_b
    if denom > 0:
        sym_score = ((count_a + count_b) / denom) * 100.0
    else:
        sym_score = 0.0

    cov_a_to_b = round(min(100.0, max(0.0, cov_a_to_b)), 2)
    cov_b_to_a = round(min(100.0, max(0.0, cov_b_to_a)), 2)
    sym_score = round(min(100.0, max(0.0, sym_score)), 2)

    explanation = (
        f"Similarity detected based on token alignment: {count_a}/{total_tokens_a} tokens in this submission "
        f"match structural patterns in the peer submission ({cov_a_to_b}% coverage). "
        "Scores reflect structural and syntactic similarity and do not constitute proof of plagiarism."
    )

    return ComparisonMetrics(
        similarity_a_to_b=cov_a_to_b,
        similarity_b_to_a=cov_b_to_a,
        symmetric_similarity=sym_score,
        shared_fingerprint_count=shared_fingerprint_count,
        matched_tokens_a=count_a,
        matched_tokens_b=count_b,
        total_tokens_a=total_tokens_a,
        total_tokens_b=total_tokens_b,
        regions=regions,
        explanation=explanation,
    )
