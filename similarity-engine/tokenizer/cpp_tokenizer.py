"""
C++ Lexical Tokenizer for Pledge Fighter Similarity Engine.
Tokenizes C++ source code preserving exact line, column, and character offsets.
"""

from dataclasses import dataclass
from enum import Enum, auto
import re
from typing import List, Optional, Tuple


class TokenType(Enum):
    KEYWORD = auto()
    IDENTIFIER = auto()
    LITERAL_NUMBER = auto()
    LITERAL_STRING = auto()
    LITERAL_CHAR = auto()
    OPERATOR = auto()
    PUNCTUATION = auto()
    PREPROCESSOR = auto()
    COMMENT = auto()
    WHITESPACE = auto()
    UNKNOWN = auto()


@dataclass(frozen=True)
class SourceLocation:
    line: int
    column: int
    offset: int


@dataclass
class Token:
    type: TokenType
    value: str
    normalized_value: str
    start: SourceLocation
    end: SourceLocation

    @property
    def start_line(self) -> int:
        return self.start.line

    @property
    def end_line(self) -> int:
        return self.end.line


CPP_KEYWORDS = {
    "alignas", "alignof", "and", "and_eq", "asm", "atomic_cancel", "atomic_commit",
    "atomic_noexcept", "auto", "bitand", "bitor", "bool", "break", "case", "catch",
    "char", "char8_t", "char16_t", "char32_t", "class", "compl", "concept", "const",
    "consteval", "constexpr", "constinit", "const_cast", "continue", "co_await",
    "co_return", "co_yield", "decltype", "default", "delete", "do", "double",
    "dynamic_cast", "else", "enum", "explicit", "export", "extern", "false", "float",
    "for", "friend", "goto", "if", "inline", "int", "long", "mutable", "namespace",
    "new", "noexcept", "not", "not_eq", "nullptr", "operator", "or", "or_eq",
    "private", "protected", "public", "reflexpr", "register", "reinterpret_cast",
    "requires", "return", "short", "signed", "sizeof", "static", "static_assert",
    "static_cast", "struct", "switch", "synchronized", "template", "this",
    "thread_local", "throw", "true", "try", "typedef", "typeid", "typename",
    "union", "unsigned", "using", "virtual", "void", "volatile", "wchar_t",
    "while", "xor", "xor_eq"
}

# Compiled regex patterns for C++ lexical elements
TOKEN_SPECIFICATION = [
    ("COMMENT_MULTI", r"/\*[\s\S]*?\*/"),
    ("COMMENT_SINGLE", r"//[^\n]*"),
    ("PREPROCESSOR", r"#[ \t]*[a-zA-Z_]\w*(?:[ \t]+[^\n\\]*(?:\\.[^\n\\]*)*)?"),
    ("LITERAL_STRING", r'"(?:\\.|[^"\\])*"'),
    ("LITERAL_CHAR", r"'(?:\\.|[^'\\])*'"),
    ("LITERAL_NUMBER", r"\b0[xX][0-9a-fA-F]+(?:[uU]?[lL]{0,2}|[fF])?\b|\b\d+(?:\.\d*)?(?:[eE][+-]?\d+)?(?:[uU]?[lL]{0,2}|[fF])?\b|\b\.\d+(?:[eE][+-]?\d+)?(?:[fF])?\b"),
    ("OPERATOR_MULTI", r"::|->\*|->|\+\+|--|<<=|>>=|<=|>=|==|!=|&&|\|\||\+=|-=|\*=|/=|%=|&=|\|=|\^=|<<|>>"),
    ("OPERATOR_SINGLE", r"[+\-*/%&|^~!=<>?:.]"),
    ("PUNCTUATION", r"[(){}\[\];,]"),
    ("IDENTIFIER", r"\b[a-zA-Z_]\w*\b"),
    ("WHITESPACE", r"\s+"),
    ("UNKNOWN", r"."),
]

MASTER_REGEX = re.compile("|".join(f"(?P<{pair[0]}>{pair[1]})" for pair in TOKEN_SPECIFICATION))


class CppTokenizer:
    """
    Tokenizer for C++ source files.
    Extracts tokens and tracks exact line, column, and offset for each token.
    """

    def __init__(self, strip_comments: bool = True, strip_whitespace: bool = True):
        self.strip_comments = strip_comments
        self.strip_whitespace = strip_whitespace

    def tokenize(self, source_code: str) -> List[Token]:
        tokens: List[Token] = []
        line_num = 1
        line_start = 0

        for match in MASTER_REGEX.finditer(source_code):
            kind = match.lastgroup
            value = match.group(0)
            start_offset = match.start()
            end_offset = match.end()

            start_col = start_offset - line_start + 1
            start_loc = SourceLocation(line=line_num, column=start_col, offset=start_offset)

            # Update line counts for newlines within the matched text
            newline_count = value.count("\n")
            if newline_count > 0:
                line_num += newline_count
                last_newline_pos = value.rfind("\n")
                line_start = start_offset + last_newline_pos + 1
                end_col = end_offset - line_start + 1
            else:
                end_col = start_col + len(value)

            end_loc = SourceLocation(line=line_num, column=end_col, offset=end_offset)

            if kind in ("COMMENT_MULTI", "COMMENT_SINGLE"):
                if not self.strip_comments:
                    tokens.append(Token(TokenType.COMMENT, value, value, start_loc, end_loc))
                continue

            if kind == "WHITESPACE":
                if not self.strip_whitespace:
                    tokens.append(Token(TokenType.WHITESPACE, value, value, start_loc, end_loc))
                continue

            if kind == "PREPROCESSOR":
                # Preprocessor directives (#include <iostream>, #define MAX 100)
                tokens.append(Token(TokenType.PREPROCESSOR, value, value, start_loc, end_loc))
            elif kind == "IDENTIFIER":
                if value in CPP_KEYWORDS:
                    tokens.append(Token(TokenType.KEYWORD, value, value, start_loc, end_loc))
                else:
                    tokens.append(Token(TokenType.IDENTIFIER, value, "ID", start_loc, end_loc))
            elif kind == "LITERAL_NUMBER":
                tokens.append(Token(TokenType.LITERAL_NUMBER, value, "NUM", start_loc, end_loc))
            elif kind == "LITERAL_STRING":
                tokens.append(Token(TokenType.LITERAL_STRING, value, "STR", start_loc, end_loc))
            elif kind == "LITERAL_CHAR":
                tokens.append(Token(TokenType.LITERAL_CHAR, value, "CHAR", start_loc, end_loc))
            elif kind in ("OPERATOR_MULTI", "OPERATOR_SINGLE"):
                tokens.append(Token(TokenType.OPERATOR, value, value, start_loc, end_loc))
            elif kind == "PUNCTUATION":
                tokens.append(Token(TokenType.PUNCTUATION, value, value, start_loc, end_loc))
            else:
                tokens.append(Token(TokenType.UNKNOWN, value, value, start_loc, end_loc))

        return tokens
