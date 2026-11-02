"""
Comparison and Region Matcher for Pledge Fighter Similarity Engine.
Uses Greedy String Tiling (Wise 1996, MOSS) to extract maximal contiguous
matching blocks of normalized tokens, classify match types (EXACT vs LOGICAL),
and identify function-level structural similarities.
"""

from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Set, Tuple

try:
    from fingerprint.winnowing import Fingerprint
    from tokenizer.cpp_tokenizer import Token
    from tokenizer.function_extractor import CppFunction, CppFunctionExtractor
except ImportError:
    from ..fingerprint.winnowing import Fingerprint
    from ..tokenizer.cpp_tokenizer import Token
    from ..tokenizer.function_extractor import CppFunction, CppFunctionExtractor


@dataclass
class MatchRegion:
    a_start_line: int
    a_end_line: int
    b_start_line: int
    b_end_line: int
    a_start_token: int
    a_end_token: int
    b_start_token: int
    b_end_token: int
    matched_token_count: int
    region_score: float = 1.0
    match_type: str = "EXACT"  # "EXACT" (Green) or "LOGICAL" (Red)
    exact_token_ratio: float = 1.0
    function_name: Optional[str] = None
    peer_function_name: Optional[str] = None


@dataclass
class FunctionMatchSummary:
    function_name: str
    peer_function_name: str
    my_start_line: int
    my_end_line: int
    peer_start_line: int
    peer_end_line: int
    similarity_percentage: float
    matched_tokens: int
    total_function_tokens: int
    match_type: str  # "EXACT" or "LOGICAL"
    verdict: str


class SimilarityMatcher:
    def __init__(self, min_matching_tokens: int = 8):
        self.min_matching_tokens = min_matching_tokens

    def find_matches(
        self,
        fps_a: List[Fingerprint],
        fps_b: List[Fingerprint],
        tokens_a: List[Token],
        tokens_b: List[Token],
    ) -> Tuple[List[MatchRegion], int, Set[int], Set[int], List[FunctionMatchSummary]]:
        len_a = len(tokens_a)
        len_b = len(tokens_b)

        if len_a < self.min_matching_tokens or len_b < self.min_matching_tokens:
            return [], 0, set(), set(), []

        vals_a = [t.normalized_value for t in tokens_a]
        vals_b = [t.normalized_value for t in tokens_b]

        candidates: List[Tuple[int, int, int]] = []  # (length, start_a, start_b)

        if len_a >= 3 and len_b >= 3:
            b_3grams = defaultdict(list)
            for j in range(len_b - 2):
                key = (vals_b[j], vals_b[j + 1], vals_b[j + 2])
                b_3grams[key].append(j)

            visited_pairs: Set[Tuple[int, int]] = set()

            for i in range(len_a - 2):
                key = (vals_a[i], vals_a[i + 1], vals_a[i + 2])
                for j in b_3grams.get(key, []):
                    if (i, j) in visited_pairs:
                        continue

                    match_len = 3
                    while (
                        i + match_len < len_a
                        and j + match_len < len_b
                        and vals_a[i + match_len] == vals_b[j + match_len]
                    ):
                        visited_pairs.add((i + match_len, j + match_len))
                        match_len += 1

                    if match_len >= self.min_matching_tokens:
                        candidates.append((match_len, i, j))
        else:
            b_pos = defaultdict(list)
            for j, val in enumerate(vals_b):
                b_pos[val].append(j)

            visited_pairs = set()
            for i in range(len_a):
                val_a = vals_a[i]
                for j in b_pos.get(val_a, []):
                    if (i, j) in visited_pairs:
                        continue
                    match_len = 0
                    while (
                        i + match_len < len_a
                        and j + match_len < len_b
                        and vals_a[i + match_len] == vals_b[j + match_len]
                    ):
                        visited_pairs.add((i + match_len, j + match_len))
                        match_len += 1
                    if match_len >= self.min_matching_tokens:
                        candidates.append((match_len, i, j))

        if not candidates:
            return [], 0, set(), set(), []

        # Greedy String Tiling: Pick longest contiguous matches first
        candidates.sort(key=lambda x: -x[0])

        chosen_tiles: List[Tuple[int, int, int, int, int]] = []
        matched_tokens_a: Set[int] = set()
        matched_tokens_b: Set[int] = set()

        for match_len, i, j in candidates:
            range_a = range(i, i + match_len)
            range_b = range(j, j + match_len)

            overlap_a = any(idx in matched_tokens_a for idx in range_a)
            overlap_b = any(idx in matched_tokens_b for idx in range_b)

            if not overlap_a and not overlap_b:
                matched_tokens_a.update(range_a)
                matched_tokens_b.update(range_b)
                chosen_tiles.append((i, i + match_len - 1, j, j + match_len - 1, match_len))

        chosen_tiles.sort(key=lambda x: x[0])

        # Extract functions for both submissions
        funcs_a = CppFunctionExtractor.extract_functions(tokens_a)
        funcs_b = CppFunctionExtractor.extract_functions(tokens_b)

        regions: List[MatchRegion] = []
        for a_s, a_e, b_s, b_e, m_len in chosen_tiles:
            a_s_bounded = max(0, min(a_s, len_a - 1))
            a_e_bounded = max(0, min(a_e, len_a - 1))
            b_s_bounded = max(0, min(b_s, len_b - 1))
            b_e_bounded = max(0, min(b_e, len_b - 1))

            # Calculate exact verbatim match ratio
            exact_matches = sum(
                1
                for off in range(m_len)
                if tokens_a[a_s_bounded + off].value == tokens_b[b_s_bounded + off].value
            )
            exact_ratio = round(exact_matches / m_len, 3) if m_len > 0 else 1.0

            # Match type: EXACT (Green) if verbatim tokens >= 85%, else LOGICAL (Red)
            match_type = "EXACT" if exact_ratio >= 0.85 else "LOGICAL"

            # Identify enclosing functions
            fn_a = self._find_enclosing_function(funcs_a, a_s_bounded, a_e_bounded)
            fn_b = self._find_enclosing_function(funcs_b, b_s_bounded, b_e_bounded)

            regions.append(
                MatchRegion(
                    a_start_line=tokens_a[a_s_bounded].start.line,
                    a_end_line=tokens_a[a_e_bounded].end.line,
                    b_start_line=tokens_b[b_s_bounded].start.line,
                    b_end_line=tokens_b[b_e_bounded].end.line,
                    a_start_token=a_s_bounded,
                    a_end_token=a_e_bounded,
                    b_start_token=b_s_bounded,
                    b_end_token=b_e_bounded,
                    matched_token_count=m_len,
                    region_score=float(m_len),
                    match_type=match_type,
                    exact_token_ratio=exact_ratio,
                    function_name=fn_a.name if fn_a else None,
                    peer_function_name=fn_b.name if fn_b else None,
                )
            )

        # Count shared winnowing fingerprints within matched regions
        fp_hashes_b = {fb.hash_value for fb in fps_b}
        shared_fingerprint_count = sum(
            1 for fa in fps_a if fa.hash_value in fp_hashes_b and fa.token_index in matched_tokens_a
        )

        # Compute Function-Level Similarity Summaries
        function_summaries = self._compute_function_summaries(
            funcs_a, funcs_b, matched_tokens_a, regions
        )

        return regions, shared_fingerprint_count, matched_tokens_a, matched_tokens_b, function_summaries

    @staticmethod
    def _find_enclosing_function(
        funcs: List[CppFunction], start_tok: int, end_tok: int
    ) -> Optional[CppFunction]:
        for fn in funcs:
            # Overlap check
            if fn.start_token_index <= start_tok and end_tok <= fn.end_token_index:
                return fn
            # Partial overlap (majority of tokens)
            overlap = max(0, min(end_tok, fn.end_token_index) - max(start_tok, fn.start_token_index) + 1)
            if overlap >= 0.5 * fn.token_count:
                return fn
        return None

    @staticmethod
    def _compute_function_summaries(
        funcs_a: List[CppFunction],
        funcs_b: List[CppFunction],
        matched_tokens_a: Set[int],
        regions: List[MatchRegion],
    ) -> List[FunctionMatchSummary]:
        summaries: List[FunctionMatchSummary] = []

        for fn_a in funcs_a:
            fn_tokens_set = set(range(fn_a.start_token_index, fn_a.end_token_index + 1))
            matched_in_fn = fn_tokens_set & matched_tokens_a

            if not matched_in_fn:
                continue

            sim_pct = round(len(matched_in_fn) / fn_a.token_count * 100.0, 1) if fn_a.token_count > 0 else 0.0

            if sim_pct < 25.0:
                continue  # Skip insignificant function overlaps

            # Find matching region and peer function
            overlapping_regions = [
                r for r in regions
                if r.a_start_line <= fn_a.end_line and r.a_end_line >= fn_a.start_line
            ]

            peer_fn_name = "Anonymous Function"
            peer_start_l = fn_a.start_line
            peer_end_l = fn_a.end_line
            match_type = "EXACT"

            if overlapping_regions:
                # Majority match type
                logical_count = sum(1 for r in overlapping_regions if r.match_type == "LOGICAL")
                match_type = "LOGICAL" if logical_count > len(overlapping_regions) / 2 else "EXACT"
                first_r = overlapping_regions[0]
                if first_r.peer_function_name:
                    peer_fn_name = first_r.peer_function_name
                elif first_r.function_name:
                    peer_fn_name = first_r.function_name
                peer_start_l = first_r.b_start_line
                peer_end_l = first_r.b_end_line
            else:
                # Fallback to direct name matching
                matching_b = [fb for fb in funcs_b if fb.name == fn_a.name]
                if matching_b:
                    peer_fn_name = matching_b[0].name
                    peer_start_l = matching_b[0].start_line
                    peer_end_l = matching_b[0].end_line

            if match_type == "LOGICAL":
                verdict = f"Logical clone detected ({sim_pct}%): same algorithmic logic & control flow with renamed identifiers."
            else:
                verdict = f"Verbatim duplicate detected ({sim_pct}%): identical code statements and variable names."

            summaries.append(
                FunctionMatchSummary(
                    function_name=fn_a.name,
                    peer_function_name=peer_fn_name,
                    my_start_line=fn_a.start_line,
                    my_end_line=fn_a.end_line,
                    peer_start_line=peer_start_l,
                    peer_end_line=peer_end_l,
                    similarity_percentage=min(100.0, sim_pct),
                    matched_tokens=len(matched_in_fn),
                    total_function_tokens=fn_a.token_count,
                    match_type=match_type,
                    verdict=verdict,
                )
            )

        return summaries
