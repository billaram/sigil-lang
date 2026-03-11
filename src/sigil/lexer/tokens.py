"""Token type definitions for the Sigil lexer."""

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    """All token types in the Sigil language."""

    # --- Keywords ---
    RULE = auto()
    WHEN = auto()
    THEN = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    IF = auto()
    ELSE = auto()
    GIVEN = auto()
    DEFINE = auto()
    AS = auto()
    IS = auto()
    EXCEEDS = auto()
    BELOW = auto()
    BETWEEN = auto()
    ANY = auto()
    ALL = auto()
    NONE_ = auto()
    IN = auto()
    IMPORT = auto()
    EXPORT = auto()
    FROM = auto()
    MODULE = auto()
    TYPE = auto()
    NEURAL = auto()
    EXPLAIN = auto()
    WITH = auto()
    TRUE = auto()
    FALSE = auto()
    USING = auto()
    COMPUTE = auto()
    RETURN = auto()
    TRACE = auto()
    MATCH = auto()
    FOR = auto()
    EACH = auto()
    EVALUATE = auto()
    MAIN = auto()
    HAS = auto()
    HAVE = auto()
    PRIVATE = auto()
    MUTABLE = auto()
    TRY = auto()
    ON = auto()
    ERROR = auto()
    FALLBACK = auto()
    TO = auto()
    RETURNS = auto()
    RECORD = auto()
    ONE = auto()
    OF = auto()
    PRIORITY = auto()
    AT = auto()
    LEAST = auto()
    MOST = auto()
    BECOMES = auto()
    EMPTY = auto()
    CONTAINS = auto()
    STARTS = auto()
    ENDS = auto()
    MATCHES = auto()
    PATTERN = auto()
    EQUALS = auto()
    PYTHON = auto()
    RUST = auto()
    LIST = auto()
    OPTION = auto()
    FILTER = auto()
    WHERE = auto()
    SORT = auto()
    BY = auto()
    TAKE = auto()
    FIRST = auto()
    LAST = auto()
    MAP = auto()
    ASCENDING = auto()
    DESCENDING = auto()
    ASSIGNED = auto()
    COUNT = auto()
    QUERY = auto()
    WITHIN = auto()

    # --- Literals ---
    NUMBER = auto()
    STRING = auto()
    SYMBOL = auto()

    # --- Identifiers ---
    IDENTIFIER = auto()

    # --- Unit suffix ---
    UNIT = auto()

    # --- Operators ---
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    GT = auto()
    LT = auto()
    GTE = auto()
    LTE = auto()
    EQ = auto()
    NEQ = auto()
    PIPE = auto()
    ARROW = auto()
    DOT = auto()
    DOUBLE_COLON = auto()

    # --- Delimiters ---
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    LBRACE = auto()
    RBRACE = auto()
    COLON = auto()
    COMMA = auto()

    # --- Structure ---
    INDENT = auto()
    DEDENT = auto()
    NEWLINE = auto()
    EOF = auto()

    # --- Special ---
    DOC_COMMENT = auto()


# Map keyword strings to their TokenType
KEYWORDS: dict[str, TokenType] = {
    "rule": TokenType.RULE,
    "when": TokenType.WHEN,
    "then": TokenType.THEN,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "given": TokenType.GIVEN,
    "define": TokenType.DEFINE,
    "as": TokenType.AS,
    "is": TokenType.IS,
    "exceeds": TokenType.EXCEEDS,
    "below": TokenType.BELOW,
    "between": TokenType.BETWEEN,
    "any": TokenType.ANY,
    "all": TokenType.ALL,
    "none": TokenType.NONE_,
    "in": TokenType.IN,
    "import": TokenType.IMPORT,
    "export": TokenType.EXPORT,
    "from": TokenType.FROM,
    "module": TokenType.MODULE,
    "type": TokenType.TYPE,
    "neural": TokenType.NEURAL,
    "explain": TokenType.EXPLAIN,
    "with": TokenType.WITH,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "using": TokenType.USING,
    "compute": TokenType.COMPUTE,
    "return": TokenType.RETURN,
    "trace": TokenType.TRACE,
    "match": TokenType.MATCH,
    "for": TokenType.FOR,
    "each": TokenType.EACH,
    "evaluate": TokenType.EVALUATE,
    "main": TokenType.MAIN,
    "has": TokenType.HAS,
    "have": TokenType.HAVE,
    "private": TokenType.PRIVATE,
    "mutable": TokenType.MUTABLE,
    "try": TokenType.TRY,
    "on": TokenType.ON,
    "error": TokenType.ERROR,
    "fallback": TokenType.FALLBACK,
    "to": TokenType.TO,
    "returns": TokenType.RETURNS,
    "record": TokenType.RECORD,
    "one": TokenType.ONE,
    "of": TokenType.OF,
    "priority": TokenType.PRIORITY,
    "at": TokenType.AT,
    "least": TokenType.LEAST,
    "most": TokenType.MOST,
    "becomes": TokenType.BECOMES,
    "empty": TokenType.EMPTY,
    "contains": TokenType.CONTAINS,
    "starts": TokenType.STARTS,
    "ends": TokenType.ENDS,
    "matches": TokenType.MATCHES,
    "pattern": TokenType.PATTERN,
    "equals": TokenType.EQUALS,
    "python": TokenType.PYTHON,
    "rust": TokenType.RUST,
    "list": TokenType.LIST,
    "Option": TokenType.OPTION,
    "filter": TokenType.FILTER,
    "where": TokenType.WHERE,
    "sort": TokenType.SORT,
    "by": TokenType.BY,
    "take": TokenType.TAKE,
    "first": TokenType.FIRST,
    "last": TokenType.LAST,
    "map": TokenType.MAP,
    "ascending": TokenType.ASCENDING,
    "descending": TokenType.DESCENDING,
    "assigned": TokenType.ASSIGNED,
    "count": TokenType.COUNT,
    "query": TokenType.QUERY,
    "within": TokenType.WITHIN,
}

# Known unit suffixes (lexer emits UNIT token for these after a NUMBER)
UNIT_SUFFIXES: frozenset[str] = frozenset({
    "degrees", "percent", "seconds", "milliseconds",
    "dollars", "confidence", "years",
})


@dataclass(frozen=True)
class Token:
    """A single token from Sigil source code."""

    type: TokenType
    value: str
    line: int
    column: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.column})"
