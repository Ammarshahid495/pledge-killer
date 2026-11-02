"""
Token Stream Normalizer for Pledge Fighter Similarity Engine.
"""

from typing import List

try:
    from tokenizer.cpp_tokenizer import Token, TokenType
except ImportError:
    from ..tokenizer.cpp_tokenizer import Token, TokenType


class TokenNormalizer:
    def __init__(self, normalize_identifiers: bool = True, normalize_literals: bool = True):
        self.normalize_identifiers = normalize_identifiers
        self.normalize_literals = normalize_literals

    def normalize(self, tokens: List[Token]) -> List[Token]:
        normalized_tokens: List[Token] = []

        for tok in tokens:
            norm_val = tok.value

            if tok.type == TokenType.IDENTIFIER:
                norm_val = "ID" if self.normalize_identifiers else tok.value
            elif tok.type == TokenType.LITERAL_NUMBER:
                norm_val = "NUM" if self.normalize_literals else tok.value
            elif tok.type == TokenType.LITERAL_STRING:
                norm_val = "STR" if self.normalize_literals else tok.value
            elif tok.type == TokenType.LITERAL_CHAR:
                norm_val = "CHAR" if self.normalize_literals else tok.value
            elif tok.type == TokenType.PREPROCESSOR:
                norm_val = "PREPROC"

            normalized_tokens.append(
                Token(
                    type=tok.type,
                    value=tok.value,
                    normalized_value=norm_val,
                    start=tok.start,
                    end=tok.end,
                )
            )

        return normalized_tokens
