"""Unit tests for the Sigil lexer."""

import pytest

from sigil.errors import SigilLexError
from sigil.lexer import Token, TokenType, tokenize

# --- Helper ---

def token_types(source: str) -> list[TokenType]:
    """Return just the token types (excluding EOF)."""
    return [t.type for t in tokenize(source) if t.type != TokenType.EOF]


def token_values(source: str) -> list[str]:
    """Return just the token values (excluding EOF)."""
    return [t.value for t in tokenize(source) if t.type != TokenType.EOF]


# ============================================================
# Number Literals
# ============================================================

class TestNumbers:
    def test_integer(self):
        tokens = tokenize("42")
        assert tokens[0] == Token(TokenType.NUMBER, "42", 1, 1)

    def test_float(self):
        tokens = tokenize("3.14")
        assert tokens[0] == Token(TokenType.NUMBER, "3.14", 1, 1)

    def test_underscore_separator(self):
        tokens = tokenize("1_000_000")
        assert tokens[0] == Token(TokenType.NUMBER, "1_000_000", 1, 1)

    def test_float_with_underscores(self):
        tokens = tokenize("1_000.50")
        assert tokens[0] == Token(TokenType.NUMBER, "1_000.50", 1, 1)

    def test_zero(self):
        tokens = tokenize("0")
        assert tokens[0] == Token(TokenType.NUMBER, "0", 1, 1)

    def test_number_with_unit(self):
        types = token_types("100 degrees")
        assert types == [TokenType.NUMBER, TokenType.UNIT]

    def test_number_with_percent_unit(self):
        tokens = tokenize("50 percent")
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "50"
        assert tokens[1].type == TokenType.UNIT
        assert tokens[1].value == "percent"

    def test_number_with_seconds_unit(self):
        types = token_types("3.5 seconds")
        assert types == [TokenType.NUMBER, TokenType.UNIT]

    def test_number_with_years_unit(self):
        types = token_types("7 years")
        assert types == [TokenType.NUMBER, TokenType.UNIT]

    def test_number_followed_by_non_unit(self):
        types = token_types("100 apples")
        assert types == [TokenType.NUMBER, TokenType.IDENTIFIER]


# ============================================================
# String Literals
# ============================================================

class TestStrings:
    def test_simple_string(self):
        tokens = tokenize('"hello world"')
        assert tokens[0] == Token(TokenType.STRING, "hello world", 1, 1)

    def test_empty_string(self):
        tokens = tokenize('""')
        assert tokens[0] == Token(TokenType.STRING, "", 1, 1)

    def test_string_with_interpolation_braces(self):
        tokens = tokenize('"temperature is {temp} degrees"')
        assert tokens[0].type == TokenType.STRING
        assert "{temp}" in tokens[0].value

    def test_escape_newline(self):
        tokens = tokenize('"line1\\nline2"')
        assert tokens[0].value == "line1\nline2"

    def test_escape_tab(self):
        tokens = tokenize('"col1\\tcol2"')
        assert tokens[0].value == "col1\tcol2"

    def test_escape_quote(self):
        tokens = tokenize('"say \\"hello\\""')
        assert tokens[0].value == 'say "hello"'

    def test_escape_backslash(self):
        tokens = tokenize('"path\\\\file"')
        assert tokens[0].value == "path\\file"

    def test_unterminated_string(self):
        with pytest.raises(SigilLexError, match="Unterminated string"):
            tokenize('"hello')

    def test_newline_in_string(self):
        with pytest.raises(SigilLexError, match="Unterminated string"):
            tokenize('"hello\nworld"')

    def test_triple_quoted_string(self):
        tokens = tokenize('"""multi\nline\nstring"""')
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "multi\nline\nstring"

    def test_unterminated_triple_string(self):
        with pytest.raises(SigilLexError, match="Unterminated triple-quoted"):
            tokenize('"""hello')


# ============================================================
# Symbol Literals
# ============================================================

class TestSymbols:
    def test_simple_symbol(self):
        tokens = tokenize(":active")
        assert tokens[0] == Token(TokenType.SYMBOL, "active", 1, 1)

    def test_symbol_critical(self):
        tokens = tokenize(":critical")
        assert tokens[0] == Token(TokenType.SYMBOL, "critical", 1, 1)

    def test_symbol_with_underscore(self):
        tokens = tokenize(":north_korea")
        assert tokens[0] == Token(TokenType.SYMBOL, "north_korea", 1, 1)

    def test_colon_not_symbol(self):
        """Colon followed by space is just a colon, not a symbol."""
        tokens = tokenize(": Text")
        assert tokens[0].type == TokenType.COLON


# ============================================================
# Keywords
# ============================================================

class TestKeywords:
    def test_rule_keyword(self):
        assert token_types("rule") == [TokenType.RULE]

    def test_when_keyword(self):
        assert token_types("when") == [TokenType.WHEN]

    def test_then_keyword(self):
        assert token_types("then") == [TokenType.THEN]

    def test_and_or_not(self):
        assert token_types("and or not") == [TokenType.AND, TokenType.OR, TokenType.NOT]

    def test_define_as(self):
        assert token_types("define as") == [TokenType.DEFINE, TokenType.AS]

    def test_compute_from_returns(self):
        assert token_types("compute from returns") == [
            TokenType.COMPUTE, TokenType.FROM, TokenType.RETURNS
        ]

    def test_is_keyword(self):
        assert token_types("is") == [TokenType.IS]

    def test_exceeds_keyword(self):
        assert token_types("exceeds") == [TokenType.EXCEEDS]

    def test_between_keyword(self):
        assert token_types("between") == [TokenType.BETWEEN]

    def test_true_false(self):
        assert token_types("true false") == [TokenType.TRUE, TokenType.FALSE]

    def test_none_keyword(self):
        assert token_types("none") == [TokenType.NONE_]

    def test_neural_keyword(self):
        assert token_types("neural") == [TokenType.NEURAL]

    def test_becomes_keyword(self):
        assert token_types("becomes") == [TokenType.BECOMES]

    def test_query_keyword(self):
        tokens = tokenize("query")
        assert tokens[0].type == TokenType.QUERY

    def test_within_keyword(self):
        tokens = tokenize("within")
        assert tokens[0].type == TokenType.WITHIN

    def test_all_keywords_recognized(self):
        """Ensure all keywords from the grammar are recognized."""
        keywords_to_test = [
            "rule", "when", "then", "and", "or", "not", "if", "else",
            "given", "define", "as", "is", "exceeds", "below", "between",
            "any", "all", "none", "in", "import", "export", "from",
            "module", "type", "neural", "explain", "with", "true", "false",
            "using", "compute", "return", "trace", "match", "for", "each",
            "evaluate", "main", "has", "have", "returns", "record", "one", "of",
            "query", "within",
        ]
        for kw in keywords_to_test:
            tokens = tokenize(kw)
            assert tokens[0].type != TokenType.IDENTIFIER, f"{kw} should be a keyword"


# ============================================================
# Identifiers
# ============================================================

class TestIdentifiers:
    def test_simple_identifier(self):
        tokens = tokenize("hello")
        assert tokens[0] == Token(TokenType.IDENTIFIER, "hello", 1, 1)

    def test_identifier_with_underscore(self):
        tokens = tokenize("my_variable")
        assert tokens[0].value == "my_variable"

    def test_identifier_with_digits(self):
        tokens = tokenize("sensor1")
        assert tokens[0].value == "sensor1"

    def test_identifier_leading_underscore(self):
        tokens = tokenize("_private")
        assert tokens[0].value == "_private"

    def test_type_names_are_identifiers(self):
        """Text, Number, Boolean, etc. are identifiers, not keywords."""
        for name in ["Text", "Number", "Boolean", "Symbol", "Confidence", "Trace"]:
            tokens = tokenize(name)
            assert tokens[0].type == TokenType.IDENTIFIER, f"{name} should be IDENTIFIER"


# ============================================================
# Operators
# ============================================================

class TestOperators:
    def test_arithmetic(self):
        types = token_types("+ - * /")
        assert types == [TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH]

    def test_comparison(self):
        types = token_types("> < >= <= = !=")
        assert types == [
            TokenType.GT, TokenType.LT, TokenType.GTE, TokenType.LTE,
            TokenType.EQ, TokenType.NEQ,
        ]

    def test_pipe_operator(self):
        types = token_types("|>")
        assert types == [TokenType.PIPE]

    def test_arrow_operator(self):
        types = token_types("->")
        assert types == [TokenType.ARROW]

    def test_dot(self):
        types = token_types("a.b")
        assert types == [TokenType.IDENTIFIER, TokenType.DOT, TokenType.IDENTIFIER]

    def test_double_colon(self):
        types = token_types("::")
        assert types == [TokenType.DOUBLE_COLON]

    def test_invalid_exclamation(self):
        with pytest.raises(SigilLexError, match="Unexpected character"):
            tokenize("! x")

    def test_invalid_pipe(self):
        with pytest.raises(SigilLexError, match="did you mean"):
            tokenize("| x")


# ============================================================
# Delimiters
# ============================================================

class TestDelimiters:
    def test_parens(self):
        types = token_types("()")
        assert types == [TokenType.LPAREN, TokenType.RPAREN]

    def test_brackets(self):
        types = token_types("[1, 2, 3]")
        assert types == [
            TokenType.LBRACKET, TokenType.NUMBER, TokenType.COMMA,
            TokenType.NUMBER, TokenType.COMMA, TokenType.NUMBER, TokenType.RBRACKET,
        ]

    def test_braces(self):
        types = token_types("{name: x}")
        assert types == [TokenType.LBRACE, TokenType.IDENTIFIER, TokenType.COLON,
                TokenType.IDENTIFIER, TokenType.RBRACE]

    def test_colon(self):
        types = token_types("record:")
        assert types == [TokenType.RECORD, TokenType.COLON]

    def test_comma(self):
        types = token_types("a, b, c")
        assert types == [
            TokenType.IDENTIFIER, TokenType.COMMA,
            TokenType.IDENTIFIER, TokenType.COMMA,
            TokenType.IDENTIFIER,
        ]


# ============================================================
# Comments
# ============================================================

class TestComments:
    def test_single_line_comment(self):
        tokens = tokenize("x -- this is a comment\ny")
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert TokenType.IDENTIFIER in types
        assert TokenType.NEWLINE in types

    def test_comment_only_line_skipped(self):
        """Comment-only lines don't produce INDENT/DEDENT."""
        tokens = tokenize("x\n-- comment\ny")
        types = [t.type for t in tokens if t.type not in (TokenType.EOF, TokenType.NEWLINE)]
        assert types == [TokenType.IDENTIFIER, TokenType.IDENTIFIER]

    def test_multiline_comment(self):
        tokens = tokenize("x {- comment -} y")
        values = [t.value for t in tokens if t.type == TokenType.IDENTIFIER]
        assert values == ["x", "y"]

    def test_nested_multiline_comment(self):
        tokens = tokenize("x {- outer {- inner -} still -} y")
        values = [t.value for t in tokens if t.type == TokenType.IDENTIFIER]
        assert values == ["x", "y"]

    def test_unterminated_multiline_comment(self):
        with pytest.raises(SigilLexError, match="Unterminated multi-line"):
            tokenize("{- hello")

    def test_doc_comment(self):
        tokens = tokenize("--- This is a doc comment")
        assert tokens[0].type == TokenType.DOC_COMMENT
        assert tokens[0].value == "This is a doc comment"


# ============================================================
# Indentation
# ============================================================

class TestIndentation:
    def test_simple_indent(self):
        source = "rule:\n  when"
        types = token_types(source)
        assert TokenType.INDENT in types
        assert TokenType.DEDENT in types

    def test_indent_dedent_sequence(self):
        source = "rule x:\n  when y\n  then z\ndefine a"
        types = token_types(source)
        indent_count = types.count(TokenType.INDENT)
        dedent_count = types.count(TokenType.DEDENT)
        assert indent_count == 1
        assert dedent_count == 1

    def test_nested_indentation(self):
        source = "a:\n  b:\n    c\n  d\ne"
        types = token_types(source)
        indent_count = types.count(TokenType.INDENT)
        dedent_count = types.count(TokenType.DEDENT)
        assert indent_count == 2
        assert dedent_count == 2

    def test_multiple_dedents(self):
        source = "a:\n  b:\n    c\nd"
        types = token_types(source)
        # Should have 2 dedents when going from indent 4 back to 0
        dedent_count = types.count(TokenType.DEDENT)
        assert dedent_count == 2

    def test_blank_lines_ignored(self):
        source = "x\n\n\ny"
        skip = (TokenType.EOF, TokenType.NEWLINE)
        types = [t.type for t in tokenize(source) if t.type not in skip]
        assert types == [TokenType.IDENTIFIER, TokenType.IDENTIFIER]

    def test_tab_rejected(self):
        with pytest.raises(SigilLexError, match="Tabs"):
            tokenize("rule:\n\twhen")

    def test_inconsistent_indent(self):
        with pytest.raises(SigilLexError, match="Inconsistent indentation"):
            tokenize("a:\n    b\n  c")

    def test_eof_emits_remaining_dedents(self):
        source = "a:\n  b"
        tokens = tokenize(source)
        types = [t.type for t in tokens]
        # Should end with DEDENT then EOF
        assert types[-1] == TokenType.EOF
        assert types[-2] == TokenType.DEDENT


# ============================================================
# Newlines
# ============================================================

class TestNewlines:
    def test_newline_emitted(self):
        types = token_types("x\ny")
        assert TokenType.NEWLINE in types

    def test_crlf_handling(self):
        types = token_types("x\r\ny")
        assert TokenType.NEWLINE in types
        # Only one newline for \r\n
        assert types.count(TokenType.NEWLINE) == 1


# ============================================================
# Line and Column Tracking
# ============================================================

class TestLineColumn:
    def test_first_token_position(self):
        tokens = tokenize("hello")
        assert tokens[0].line == 1
        assert tokens[0].column == 1

    def test_second_line_position(self):
        tokens = tokenize("x\ny")
        y_token = [t for t in tokens if t.value == "y"][0]
        assert y_token.line == 2
        assert y_token.column == 1

    def test_column_after_spaces(self):
        tokens = tokenize("  hello")
        # At top level, 2 spaces = indent, then hello
        hello = [t for t in tokens if t.value == "hello"][0]
        assert hello.column == 3


# ============================================================
# Edge Cases
# ============================================================

class TestEdgeCases:
    def test_empty_source(self):
        tokens = tokenize("")
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EOF

    def test_only_whitespace(self):
        tokens = tokenize("   \n   \n  ")
        assert tokens[-1].type == TokenType.EOF

    def test_only_comments(self):
        tokens = tokenize("-- comment 1\n-- comment 2\n")
        assert tokens[-1].type == TokenType.EOF

    def test_symbol_list(self):
        types = token_types("[:active, :critical, :pending]")
        assert types == [
            TokenType.LBRACKET,
            TokenType.SYMBOL, TokenType.COMMA,
            TokenType.SYMBOL, TokenType.COMMA,
            TokenType.SYMBOL,
            TokenType.RBRACKET,
        ]

    def test_field_access_chain(self):
        types = token_types("patient.vital_signs.heart_rate")
        assert types == [
            TokenType.IDENTIFIER, TokenType.DOT,
            TokenType.IDENTIFIER, TokenType.DOT,
            TokenType.IDENTIFIER,
        ]

    def test_function_call(self):
        types = token_types("calculate_rate(applicant)")
        assert types == [
            TokenType.IDENTIFIER, TokenType.LPAREN,
            TokenType.IDENTIFIER, TokenType.RPAREN,
        ]

    def test_arithmetic_expression(self):
        types = token_types("a + b * c")
        assert types == [
            TokenType.IDENTIFIER, TokenType.PLUS,
            TokenType.IDENTIFIER, TokenType.STAR,
            TokenType.IDENTIFIER,
        ]

    def test_complex_expression(self):
        types = token_types("(applicant.credit_score - 680) * 0.01")
        assert types == [
            TokenType.LPAREN, TokenType.IDENTIFIER, TokenType.DOT,
            TokenType.IDENTIFIER, TokenType.MINUS, TokenType.NUMBER,
            TokenType.RPAREN, TokenType.STAR, TokenType.NUMBER,
        ]

    def test_invalid_character(self):
        with pytest.raises(SigilLexError, match="Unexpected character"):
            tokenize("x @ y")


# ============================================================
# Full Tokenization of Example Files
# ============================================================

class TestExampleFiles:
    def test_hello_sigil(self, hello_source):
        tokens = tokenize(hello_source, "hello.sigil")
        types = [t.type for t in tokens]
        assert types[-1] == TokenType.EOF
        assert TokenType.DEFINE in types
        assert TokenType.RULE in types
        assert TokenType.WHEN in types
        assert TokenType.THEN in types
        assert TokenType.EXPLAIN in types

    def test_temperature_sigil(self, temperature_source):
        tokens = tokenize(temperature_source, "temperature.sigil")
        types = [t.type for t in tokens]
        assert types[-1] == TokenType.EOF
        assert TokenType.MODULE in types
        assert TokenType.TYPE in types
        assert TokenType.RECORD in types
        assert types.count(TokenType.RULE) == 4
        assert TokenType.SYMBOL in types
        assert TokenType.BETWEEN in types
        assert TokenType.BELOW in types
        assert TokenType.EXCEEDS in types

    def test_loan_eligibility_sigil(self, loan_source):
        tokens = tokenize(loan_source, "loan_eligibility.sigil")
        types = [t.type for t in tokens]
        assert types[-1] == TokenType.EOF
        assert TokenType.IMPORT in types
        assert TokenType.ONE in types
        assert TokenType.COMPUTE in types
        assert TokenType.TRACE in types

    def test_medical_triage_sigil(self, triage_source):
        tokens = tokenize(triage_source, "medical_triage.sigil")
        types = [t.type for t in tokens]
        assert types[-1] == TokenType.EOF
        assert TokenType.NEURAL in types
        assert TokenType.ANY in types
        assert TokenType.MAIN in types

    def test_compliance_checker_sigil(self, compliance_source):
        tokens = tokenize(compliance_source, "compliance_checker.sigil")
        types = [t.type for t in tokens]
        assert types[-1] == TokenType.EOF
        assert TokenType.NEURAL in types
        assert types.count(TokenType.RULE) >= 5

    def test_all_examples_no_errors(self, hello_source, temperature_source,
                                     loan_source, triage_source, compliance_source):
        """All 5 example files tokenize without errors."""
        for name, source in [
            ("hello", hello_source),
            ("temperature", temperature_source),
            ("loan", loan_source),
            ("triage", triage_source),
            ("compliance", compliance_source),
        ]:
            tokens = tokenize(source, f"{name}.sigil")
            assert tokens[-1].type == TokenType.EOF, f"{name} should end with EOF"
            # Verify balanced INDENT/DEDENT
            indents = sum(1 for t in tokens if t.type == TokenType.INDENT)
            dedents = sum(1 for t in tokens if t.type == TokenType.DEDENT)
            assert indents == dedents, f"{name}: {indents} INDENTs but {dedents} DEDENTs"
