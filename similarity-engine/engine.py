"""
Stanford MOSS-grade Similarity Engine Orchestrator for Pledge Fighter.
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Set

try:
    from tokenizer.cpp_tokenizer import CppTokenizer, Token
    from normalizer.normalizer import TokenNormalizer
    from fingerprint.winnowing import WinnowingEngine, Fingerprint
    from comparison.matcher import SimilarityMatcher, MatchRegion
    from scoring.metrics import ComparisonMetrics, calculate_metrics
except ImportError:
    from .tokenizer.cpp_tokenizer import CppTokenizer, Token
    from .normalizer.normalizer import TokenNormalizer
    from .fingerprint.winnowing import WinnowingEngine, Fingerprint
    from .comparison.matcher import SimilarityMatcher, MatchRegion
    from .scoring.metrics import ComparisonMetrics, calculate_metrics

ENGINE_VERSION = "1.0.0"


@dataclass
class ProcessedSubmission:
    submission_id: str
    tokens: List[Token]
    fingerprints: List[Fingerprint]
    source_code: str


@dataclass
class ComparisonResult:
    engine_version: str
    submission_a_id: str
    submission_b_id: str
    similarity_a_to_b: float
    similarity_b_to_a: float
    symmetric_similarity: float
    shared_fingerprint_count: int
    matched_token_count: int
    regions: List[Dict[str, Any]]
    explanation: str
    matched_functions: List[Dict[str, Any]] = None
    starter_fingerprints_ignored: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SimilarityEngine:
    def __init__(self, k: int = 10, w: int = 5, min_matching_tokens: int = 8):
        self.k = k
        self.w = w
        self.min_matching_tokens = min_matching_tokens
        self.tokenizer = CppTokenizer()
        self.normalizer = TokenNormalizer(normalize_identifiers=True, normalize_literals=True)
        self.winnowing = WinnowingEngine(k=self.k, w=self.w)
        self.matcher = SimilarityMatcher(min_matching_tokens=self.min_matching_tokens)

    def process_source(self, submission_id: str, source_code: str) -> ProcessedSubmission:
        raw_tokens = self.tokenizer.tokenize(source_code)
        normalized_tokens = self.normalizer.normalize(raw_tokens)
        fingerprints = self.winnowing.fingerprint(normalized_tokens)
        return ProcessedSubmission(
            submission_id=submission_id,
            tokens=normalized_tokens,
            fingerprints=fingerprints,
            source_code=source_code,
        )

    def starter_fingerprint_hashes(self, starter_code: str) -> Set[int]:
        """Fingerprint hashes from shared assignment starter/boilerplate code."""
        processed = self.process_source("starter", starter_code)
        return {fp.hash_value for fp in processed.fingerprints}

    def compare_submissions(
        self,
        sub_a: ProcessedSubmission,
        sub_b: ProcessedSubmission,
        ignore_fingerprint_hashes: Optional[Set[int]] = None,
    ) -> ComparisonResult:
        fps_a = sub_a.fingerprints
        fps_b = sub_b.fingerprints
        starter_ignored = 0
        if ignore_fingerprint_hashes:
            fps_a = [fp for fp in fps_a if fp.hash_value not in ignore_fingerprint_hashes]
            fps_b = [fp for fp in fps_b if fp.hash_value not in ignore_fingerprint_hashes]
            starter_ignored = (
                (len(sub_a.fingerprints) - len(fps_a))
                + (len(sub_b.fingerprints) - len(fps_b))
            )

        regions, shared_fp_count, matched_toks_a, matched_toks_b, func_summaries = self.matcher.find_matches(
            fps_a,
            fps_b,
            sub_a.tokens,
            sub_b.tokens,
        )

        metrics = calculate_metrics(
            total_tokens_a=len(sub_a.tokens),
            total_tokens_b=len(sub_b.tokens),
            matched_tokens_a=matched_toks_a,
            matched_tokens_b=matched_toks_b,
            shared_fingerprint_count=shared_fp_count,
            regions=regions,
        )

        region_dicts = [
            {
                "a_start_line": r.a_start_line,
                "a_end_line": r.a_end_line,
                "b_start_line": r.b_start_line,
                "b_end_line": r.b_end_line,
                "a_start_token": r.a_start_token,
                "a_end_token": r.a_end_token,
                "b_start_token": r.b_start_token,
                "b_end_token": r.b_end_token,
                "matched_token_count": r.matched_token_count,
                "region_score": r.region_score,
                "match_type": r.match_type,
                "exact_token_ratio": r.exact_token_ratio,
                "function_name": r.function_name,
                "peer_function_name": r.peer_function_name,
            }
            for r in regions
        ]

        func_dicts = [asdict(f) for f in func_summaries]

        return ComparisonResult(
            engine_version=ENGINE_VERSION,
            submission_a_id=sub_a.submission_id,
            submission_b_id=sub_b.submission_id,
            similarity_a_to_b=metrics.similarity_a_to_b,
            similarity_b_to_a=metrics.similarity_b_to_a,
            symmetric_similarity=metrics.symmetric_similarity,
            shared_fingerprint_count=metrics.shared_fingerprint_count,
            matched_token_count=len(matched_toks_a),
            regions=region_dicts,
            explanation=(
                f"{metrics.explanation} Shared starter/boilerplate fingerprints were excluded from matching."
                if starter_ignored
                else metrics.explanation
            ),
            matched_functions=func_dicts,
            starter_fingerprints_ignored=starter_ignored,
        )
