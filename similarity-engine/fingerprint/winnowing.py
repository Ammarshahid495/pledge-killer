"""
Stanford MOSS-style Winnowing Algorithm for Code Fingerprinting.
Reference: Schleimer, Wilkerson, Aiken (SIGMOD 2003).
"""

from dataclasses import dataclass
from typing import List, Sequence, Tuple

try:
    from tokenizer.cpp_tokenizer import Token, SourceLocation
except ImportError:
    from ..tokenizer.cpp_tokenizer import Token, SourceLocation


@dataclass(frozen=True)
class Fingerprint:
    hash_value: int
    token_index: int  # Starting token index in the token sequence
    token_count: int  # Number of tokens in this k-gram (k)
    start_line: int
    start_col: int
    end_line: int
    end_col: int


# Base and modulo for Karp-Rabin rolling hash
PRIME_BASE = 257
PRIME_MOD = 1_000_000_007


def compute_k_gram_hashes(token_values: Sequence[str], k: int) -> List[int]:
    n = len(token_values)
    if n < k:
        return []

    token_ids = [abs(hash(val)) % PRIME_MOD for val in token_values]
    b_k_minus_1 = pow(PRIME_BASE, k - 1, PRIME_MOD)
    hashes: List[int] = []

    current_hash = 0
    for j in range(k):
        current_hash = (current_hash * PRIME_BASE + token_ids[j]) % PRIME_MOD
    hashes.append(current_hash)

    for i in range(1, n - k + 1):
        leading = (token_ids[i - 1] * b_k_minus_1) % PRIME_MOD
        trailing = token_ids[i + k - 1]
        current_hash = ((current_hash - leading) * PRIME_BASE + trailing) % PRIME_MOD
        hashes.append(current_hash)

    return hashes


class WinnowingEngine:
    def __init__(self, k: int = 10, w: int = 5):
        if k < 1:
            raise ValueError("k must be >= 1")
        if w < 1:
            raise ValueError("w must be >= 1")
        self.k = k
        self.w = w

    def fingerprint(self, tokens: List[Token]) -> List[Fingerprint]:
        n = len(tokens)
        if n < self.k:
            return []

        token_values = [tok.normalized_value for tok in tokens]
        hashes = compute_k_gram_hashes(token_values, self.k)
        num_hashes = len(hashes)

        if num_hashes == 0:
            return []

        if num_hashes < self.w:
            min_idx = 0
            min_val = hashes[0]
            for idx in range(1, num_hashes):
                if hashes[idx] <= min_val:
                    min_val = hashes[idx]
                    min_idx = idx

            start_tok = tokens[min_idx]
            end_tok = tokens[min_idx + self.k - 1]
            return [
                Fingerprint(
                    hash_value=min_val,
                    token_index=min_idx,
                    token_count=self.k,
                    start_line=start_tok.start.line,
                    start_col=start_tok.start.column,
                    end_line=end_tok.end.line,
                    end_col=end_tok.end.column,
                )
            ]

        selected_fingerprints: List[Fingerprint] = []
        last_selected_pos = -1

        for i in range(num_hashes - self.w + 1):
            window = hashes[i : i + self.w]
            min_val = min(window)
            rel_idx = len(window) - 1 - window[::-1].index(min_val)
            abs_pos = i + rel_idx

            if abs_pos != last_selected_pos:
                last_selected_pos = abs_pos
                start_tok = tokens[abs_pos]
                end_tok = tokens[abs_pos + self.k - 1]
                selected_fingerprints.append(
                    Fingerprint(
                        hash_value=min_val,
                        token_index=abs_pos,
                        token_count=self.k,
                        start_line=start_tok.start.line,
                        start_col=start_tok.start.column,
                        end_line=end_tok.end.line,
                        end_col=end_tok.end.column,
                    )
                )

        return selected_fingerprints
