"""Sigil lexer — tokenizes source code into a stream of tokens.

Handles indentation tracking, string interpolation markers, unit literals,
single-line comments (--), multi-line comments ({- ... -}), and doc comments (---).
"""

from sigil.errors import SigilLexError, SourceLocation
from sigil.lexer.tokens import KEYWORDS, UNIT_SUFFIXES, Token, TokenType


def tokenize(source: str, filename: str = "<stdin>") -> list[Token]:
    """Tokenize Sigil source code into a list of tokens.

    Handles indentation tracking, string interpolation, and unit literals.
    Raises SigilLexError on invalid input with source location.
    """
    lexer = _Lexer(source, filename)
    return lexer.tokenize()


class _Lexer:
    """Internal lexer state. Not part of the public API."""

    def __init__(self, source: str, filename: str) -> None:
        self.source = source
        self.filename = filename
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: list[Token] = []
        self.indent_stack: list[int] = [0]
        # Track whether we're at the start of a line (for indentation)
        self.at_line_start = True

    def tokenize(self) -> list[Token]:
        """Run the lexer and return the complete token list."""
        while not self._at_end():
            if self.at_line_start:
                self._handle_line_start()
            else:
                self._scan_token()

        # Emit DEDENTs for remaining indentation levels
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self._emit(TokenType.DEDENT, "", self.line, self.column)

        self._emit(TokenType.EOF, "", self.line, self.column)
        return self.tokens

    # --- Character access ---

    def _at_end(self) -> bool:
        return self.pos >= len(self.source)

    def _peek(self) -> str:
        if self._at_end():
            return "\0"
        return self.source[self.pos]

    def _peek_ahead(self, offset: int = 1) -> str:
        pos = self.pos + offset
        if pos >= len(self.source):
            return "\0"
        return self.source[pos]

    def _advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _match(self, expected: str) -> bool:
        if self._at_end() or self.source[self.pos] != expected:
            return False
        self._advance()
        return True

    # --- Token emission ---

    def _emit(self, token_type: TokenType, value: str, line: int, column: int) -> None:
        self.tokens.append(Token(token_type, value, line, column))

    def _error(self, message: str) -> SigilLexError:
        loc = SourceLocation(self.filename, self.line, self.column)
        return SigilLexError(message, loc)

    # --- Line start / indentation ---

    def _handle_line_start(self) -> None:
        """Process the beginning of a line: measure indentation, emit INDENT/DEDENT."""
        self.at_line_start = False

        # Skip blank lines and comment-only lines
        while not self._at_end():
            # Check for blank line
            if self._peek() == "\n":
                self._advance()
                continue
            if self._peek() == "\r":
                self._advance()
                if not self._at_end() and self._peek() == "\n":
                    self._advance()
                continue

            # Measure indentation
            indent = 0
            while not self._at_end() and self._peek() == " ":
                self._advance()
                indent += 1

            # Reject tabs
            if not self._at_end() and self._peek() == "\t":
                raise self._error("Tabs are not allowed in Sigil. Use spaces for indentation.")

            # Check if rest of line is blank or comment-only
            if self._at_end() or self._peek() == "\n" or self._peek() == "\r":
                # Blank line after spaces — skip it
                continue
            if self._peek() == "-" and self._peek_ahead() == "-":
                if self._peek_ahead(2) == "-":
                    # Doc comment — emit as token, don't skip
                    break
                # Comment-only line — skip it but consume the line
                self._skip_single_line_comment()
                continue
            if self._peek() == "{" and self._peek_ahead() == "-":
                # Multi-line comment at line start — scan it, then re-check
                self._scan_multiline_comment()
                continue

            # Real content — emit indentation tokens
            current_indent = self.indent_stack[-1]
            if indent > current_indent:
                self.indent_stack.append(indent)
                self._emit(TokenType.INDENT, "", self.line, 1)
            elif indent < current_indent:
                while len(self.indent_stack) > 1 and self.indent_stack[-1] > indent:
                    self.indent_stack.pop()
                    self._emit(TokenType.DEDENT, "", self.line, 1)
                if self.indent_stack[-1] != indent:
                    raise self._error(
                        f"Inconsistent indentation: got {indent} spaces, "
                        f"but expected {self.indent_stack[-1]} spaces"
                    )
            break

    # --- Main token scanner ---

    def _scan_token(self) -> None:
        """Scan a single token from the current position."""
        ch = self._peek()

        # Whitespace (not newlines — those are significant)
        if ch == " " or ch == "\t":
            self._advance()
            return

        # Newlines
        if ch == "\n" or ch == "\r":
            line, col = self.line, self.column
            self._advance()
            if ch == "\r" and not self._at_end() and self._peek() == "\n":
                self._advance()
            self._emit(TokenType.NEWLINE, "\\n", line, col)
            self.at_line_start = True
            return

        # Comments
        if ch == "-" and self._peek_ahead() == "-":
            if self._peek_ahead(2) == "-":
                self._scan_doc_comment()
            else:
                self._skip_single_line_comment()
            return

        if ch == "{" and self._peek_ahead() == "-":
            self._scan_multiline_comment()
            return

        # String literals
        if ch == '"':
            self._scan_string()
            return

        # Numbers
        if ch.isdigit():
            self._scan_number()
            return

        # Symbol literals (:identifier)
        if ch == ":" and self._peek_ahead().isalpha():
            self._scan_symbol()
            return

        # Identifiers and keywords
        if ch.isalpha() or ch == "_":
            self._scan_identifier()
            return

        # Operators and delimiters
        self._scan_operator()

    # --- Comment scanning ---

    def _skip_single_line_comment(self) -> None:
        """Skip a -- comment to end of line (don't consume the newline)."""
        while not self._at_end() and self._peek() != "\n" and self._peek() != "\r":
            self._advance()

    def _scan_doc_comment(self) -> None:
        """Scan a --- doc comment and emit a DOC_COMMENT token."""
        line, col = self.line, self.column
        # Skip the ---
        self._advance()
        self._advance()
        self._advance()
        # Skip leading space
        if not self._at_end() and self._peek() == " ":
            self._advance()
        start = self.pos
        while not self._at_end() and self._peek() != "\n" and self._peek() != "\r":
            self._advance()
        text = self.source[start:self.pos]
        self._emit(TokenType.DOC_COMMENT, text, line, col)

    def _scan_multiline_comment(self) -> None:
        """Scan a {- ... -} comment (supports nesting)."""
        # Skip {-
        self._advance()
        self._advance()
        depth = 1
        while not self._at_end() and depth > 0:
            if self._peek() == "{" and self._peek_ahead() == "-":
                self._advance()
                self._advance()
                depth += 1
            elif self._peek() == "-" and self._peek_ahead() == "}":
                self._advance()
                self._advance()
                depth -= 1
            else:
                self._advance()
        if depth > 0:
            raise self._error("Unterminated multi-line comment")

    # --- String scanning ---

    def _scan_string(self) -> None:
        """Scan a string literal, handling triple-quoted and interpolation."""
        line, col = self.line, self.column

        # Check for triple-quoted string
        if self._peek_ahead() == '"' and self._peek_ahead(2) == '"':
            self._scan_triple_string(line, col)
            return

        # Regular string
        self._advance()  # skip opening "
        chars: list[str] = []
        while not self._at_end() and self._peek() != '"':
            if self._peek() == "\n" or self._peek() == "\r":
                raise self._error("Unterminated string literal")
            if self._peek() == "\\":
                chars.append(self._scan_escape())
            else:
                chars.append(self._advance())

        if self._at_end():
            raise self._error("Unterminated string literal")

        self._advance()  # skip closing "
        self._emit(TokenType.STRING, "".join(chars), line, col)

    def _scan_triple_string(self, line: int, col: int) -> None:
        """Scan a triple-quoted string literal."""
        # Skip opening """
        self._advance()
        self._advance()
        self._advance()

        chars: list[str] = []
        while not self._at_end():
            if self._peek() == '"' and self._peek_ahead() == '"' and self._peek_ahead(2) == '"':
                # Skip closing """
                self._advance()
                self._advance()
                self._advance()
                self._emit(TokenType.STRING, "".join(chars), line, col)
                return
            chars.append(self._advance())

        raise self._error("Unterminated triple-quoted string")

    def _scan_escape(self) -> str:
        """Scan an escape sequence in a string."""
        self._advance()  # skip backslash
        if self._at_end():
            raise self._error("Unterminated escape sequence")
        ch = self._advance()
        match ch:
            case "n":
                return "\n"
            case "t":
                return "\t"
            case "r":
                return "\r"
            case "\\":
                return "\\"
            case '"':
                return '"'
            case "{":
                return "{"
            case "}":
                return "}"
            case _:
                raise self._error(f"Invalid escape sequence: \\{ch}")

    # --- Number scanning ---

    def _scan_number(self) -> None:
        """Scan a number literal (int or float, with optional underscore separators)."""
        line, col = self.line, self.column
        start = self.pos

        # Integer part
        while not self._at_end() and (self._peek().isdigit() or self._peek() == "_"):
            self._advance()

        # Float?
        if not self._at_end() and self._peek() == "." and self._peek_ahead().isdigit():
            self._advance()  # skip .
            while not self._at_end() and (self._peek().isdigit() or self._peek() == "_"):
                self._advance()

        value = self.source[start:self.pos]
        self._emit(TokenType.NUMBER, value, line, col)

        # Check for unit suffix
        self._try_scan_unit()

    def _try_scan_unit(self) -> None:
        """After a NUMBER, check if the next word is a known unit suffix."""
        # Need at least one space, then an identifier that is a unit
        saved_pos = self.pos
        saved_line = self.line
        saved_col = self.column

        # Skip spaces (not newlines)
        spaces = 0
        while not self._at_end() and self._peek() == " ":
            self._advance()
            spaces += 1

        if spaces == 0 or self._at_end() or not self._peek().isalpha():
            # No unit — restore position
            self.pos = saved_pos
            self.line = saved_line
            self.column = saved_col
            return

        # Read the word
        word_start = self.pos
        word_line = self.line
        word_col = self.column
        while not self._at_end() and (self._peek().isalnum() or self._peek() == "_"):
            self._advance()
        word = self.source[word_start:self.pos]

        if word in UNIT_SUFFIXES:
            self._emit(TokenType.UNIT, word, word_line, word_col)
        else:
            # Not a unit — restore position
            self.pos = saved_pos
            self.line = saved_line
            self.column = saved_col

    # --- Symbol scanning ---

    def _scan_symbol(self) -> None:
        """Scan a symbol literal like :active, :critical."""
        line, col = self.line, self.column
        self._advance()  # skip :
        start = self.pos
        while not self._at_end() and (self._peek().isalnum() or self._peek() == "_"):
            self._advance()
        name = self.source[start:self.pos]
        self._emit(TokenType.SYMBOL, name, line, col)

    # --- Identifier / keyword scanning ---

    def _scan_identifier(self) -> None:
        """Scan an identifier or keyword."""
        line, col = self.line, self.column
        start = self.pos
        while not self._at_end() and (self._peek().isalnum() or self._peek() == "_"):
            self._advance()
        word = self.source[start:self.pos]

        # Check if it's a keyword
        if word in KEYWORDS:
            self._emit(KEYWORDS[word], word, line, col)
        else:
            self._emit(TokenType.IDENTIFIER, word, line, col)

    # --- Operator / delimiter scanning ---

    def _scan_operator(self) -> None:
        """Scan an operator or delimiter."""
        line, col = self.line, self.column
        ch = self._advance()

        match ch:
            case "+":
                self._emit(TokenType.PLUS, "+", line, col)
            case "*":
                self._emit(TokenType.STAR, "*", line, col)
            case "/":
                self._emit(TokenType.SLASH, "/", line, col)
            case ".":
                self._emit(TokenType.DOT, ".", line, col)
            case ",":
                self._emit(TokenType.COMMA, ",", line, col)
            case "(":
                self._emit(TokenType.LPAREN, "(", line, col)
            case ")":
                self._emit(TokenType.RPAREN, ")", line, col)
            case "[":
                self._emit(TokenType.LBRACKET, "[", line, col)
            case "]":
                self._emit(TokenType.RBRACKET, "]", line, col)
            case "{":
                self._emit(TokenType.LBRACE, "{", line, col)
            case "}":
                self._emit(TokenType.RBRACE, "}", line, col)
            case ":":
                if self._match(":"):
                    self._emit(TokenType.DOUBLE_COLON, "::", line, col)
                else:
                    self._emit(TokenType.COLON, ":", line, col)
            case "-":
                if self._match(">"):
                    self._emit(TokenType.ARROW, "->", line, col)
                else:
                    self._emit(TokenType.MINUS, "-", line, col)
            case ">":
                if self._match("="):
                    self._emit(TokenType.GTE, ">=", line, col)
                else:
                    self._emit(TokenType.GT, ">", line, col)
            case "<":
                if self._match("="):
                    self._emit(TokenType.LTE, "<=", line, col)
                else:
                    self._emit(TokenType.LT, "<", line, col)
            case "=":
                self._emit(TokenType.EQ, "=", line, col)
            case "!":
                if self._match("="):
                    self._emit(TokenType.NEQ, "!=", line, col)
                else:
                    raise self._error("Unexpected character: '!'")
            case "|":
                if self._match(">"):
                    self._emit(TokenType.PIPE, "|>", line, col)
                else:
                    raise self._error("Unexpected character: '|' (did you mean '|>'?)")
            case _:
                raise self._error(f"Unexpected character: {ch!r}")
