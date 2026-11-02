"""
C++ Function and Method Extractor for Pledge Fighter Similarity Engine.
Extracts top-level functions, class methods, and constructors with their exact line boundaries.
"""

from dataclasses import dataclass
from typing import List, Optional

try:
    from tokenizer.cpp_tokenizer import CppTokenizer, Token, TokenType
except ImportError:
    from .cpp_tokenizer import CppTokenizer, Token, TokenType


@dataclass
class CppFunction:
    name: str
    start_line: int
    end_line: int
    start_token_index: int
    end_token_index: int
    token_count: int


class CppFunctionExtractor:
    NON_FUNCTION_KEYWORDS = {
        "if", "for", "while", "switch", "catch", "return", "sizeof",
        "case", "default", "else", "do", "goto", "new", "delete",
    }

    @classmethod
    def extract_functions(cls, tokens: List[Token]) -> List[CppFunction]:
        functions: List[CppFunction] = []
        n = len(tokens)
        i = 0

        while i < n:
            tok = tokens[i]

            # Look for function identifier or destructor ~ClassName
            is_destructor = False
            fn_name = ""
            fn_start_tok = i

            if tok.value == "~" and i + 1 < n and tokens[i + 1].type == TokenType.IDENTIFIER:
                is_destructor = True
                fn_name = f"~{tokens[i + 1].value}"
                fn_start_tok = i
                i += 1
            elif (
                tok.type in (TokenType.IDENTIFIER, TokenType.KEYWORD)
                and tok.value not in cls.NON_FUNCTION_KEYWORDS
            ):
                fn_name = tok.value
                fn_start_tok = i
                # Check for ClassName::methodName
                if i >= 2 and tokens[i - 1].value == "::" and tokens[i - 2].type == TokenType.IDENTIFIER:
                    fn_name = f"{tokens[i - 2].value}::{fn_name}"
                    fn_start_tok = i - 2
            else:
                i += 1
                continue

            # Function must be followed by '('
            if i + 1 < n and tokens[i + 1].value == "(":
                # Match parameter parentheses
                depth = 1
                j = i + 2
                while j < n and depth > 0:
                    if tokens[j].value == "(":
                        depth += 1
                    elif tokens[j].value == ")":
                        depth -= 1
                    j += 1

                # Skip modifiers: const, noexcept, override, final, or constructor initializers (: member(x))
                while j < n and tokens[j].value not in ("{", ";"):
                    j += 1

                if j < n and tokens[j].value == "{":
                    # Found function definition body! Find closing '}'
                    brace_depth = 1
                    body_start = j
                    start_line = tokens[fn_start_tok].start.line
                    k = j + 1
                    while k < n and brace_depth > 0:
                        if tokens[k].value == "{":
                            brace_depth += 1
                        elif tokens[k].value == "}":
                            brace_depth -= 1
                        k += 1

                    if brace_depth == 0:
                        end_line = tokens[k - 1].end.line
                        tok_count = (k - 1) - fn_start_tok + 1
                        functions.append(
                            CppFunction(
                                name=fn_name,
                                start_line=start_line,
                                end_line=end_line,
                                start_token_index=fn_start_tok,
                                end_token_index=k - 1,
                                token_count=tok_count,
                            )
                        )
                        i = k
                        continue

            i += 1

        return functions
