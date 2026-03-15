//! Sigil lexer scanner — tokenizes source code.

use super::tokens::{Token, TokenType, KEYWORDS, UNIT_SUFFIXES};

/// Tokenize Sigil source code into a list of tokens.
pub fn tokenize(source: &str) -> Result<Vec<Token>, String> {
    let mut scanner = Scanner::new(source);
    scanner.tokenize()
}

struct Scanner {
    source: Vec<char>,
    pos: usize,
    line: usize,
    column: usize,
    tokens: Vec<Token>,
    indent_stack: Vec<usize>,
    at_line_start: bool,
}

impl Scanner {
    fn new(source: &str) -> Self {
        Scanner {
            source: source.chars().collect(),
            pos: 0,
            line: 1,
            column: 1,
            tokens: Vec::new(),
            indent_stack: vec![0],
            at_line_start: true,
        }
    }

    fn tokenize(&mut self) -> Result<Vec<Token>, String> {
        while !self.at_end() {
            if self.at_line_start {
                self.handle_line_start()?;
            } else {
                self.scan_token()?;
            }
        }

        // Emit DEDENTs for remaining indentation levels
        while self.indent_stack.len() > 1 {
            self.indent_stack.pop();
            self.emit(TokenType::Dedent, "", self.line, self.column);
        }

        self.emit(TokenType::Eof, "", self.line, self.column);
        Ok(std::mem::take(&mut self.tokens))
    }

    // --- Character access ---

    fn at_end(&self) -> bool {
        self.pos >= self.source.len()
    }

    fn peek(&self) -> char {
        if self.at_end() { '\0' } else { self.source[self.pos] }
    }

    fn peek_ahead(&self, offset: usize) -> char {
        let p = self.pos + offset;
        if p >= self.source.len() { '\0' } else { self.source[p] }
    }

    fn advance(&mut self) -> char {
        let ch = self.source[self.pos];
        self.pos += 1;
        if ch == '\n' {
            self.line += 1;
            self.column = 1;
        } else {
            self.column += 1;
        }
        ch
    }

    fn match_char(&mut self, expected: char) -> bool {
        if self.at_end() || self.source[self.pos] != expected {
            return false;
        }
        self.advance();
        true
    }

    // --- Token emission ---

    fn emit(&mut self, token_type: TokenType, value: &str, line: usize, column: usize) {
        self.tokens.push(Token::new(token_type, value, line, column));
    }

    fn error(&self, message: &str) -> String {
        format!("Lexer error at {}:{}: {}", self.line, self.column, message)
    }

    // --- Line start / indentation ---

    fn handle_line_start(&mut self) -> Result<(), String> {
        self.at_line_start = false;

        loop {
            if self.at_end() { break; }

            // Blank line
            if self.peek() == '\n' { self.advance(); continue; }
            if self.peek() == '\r' {
                self.advance();
                if !self.at_end() && self.peek() == '\n' { self.advance(); }
                continue;
            }

            // Measure indentation
            let mut indent = 0;
            while !self.at_end() && self.peek() == ' ' {
                self.advance();
                indent += 1;
            }

            // Reject tabs
            if !self.at_end() && self.peek() == '\t' {
                return Err(self.error("Tabs are not allowed in Sigil; use spaces (2 per level)"));
            }

            // Blank or comment-only line after spaces
            if self.at_end() || self.peek() == '\n' || self.peek() == '\r' {
                continue;
            }
            if self.peek() == '-' && self.peek_ahead(1) == '-' {
                if self.peek_ahead(2) == '-' {
                    // Doc comment — break to emit
                    break;
                }
                self.skip_single_line_comment();
                continue;
            }
            if self.peek() == '{' && self.peek_ahead(1) == '-' {
                self.scan_multiline_comment()?;
                continue;
            }

            // Real content — emit indentation tokens
            let current_indent = *self.indent_stack.last().unwrap();
            if indent > current_indent {
                self.indent_stack.push(indent);
                self.emit(TokenType::Indent, "", self.line, 1);
            } else if indent < current_indent {
                while self.indent_stack.len() > 1 && *self.indent_stack.last().unwrap() > indent {
                    self.indent_stack.pop();
                    self.emit(TokenType::Dedent, "", self.line, 1);
                }
                if *self.indent_stack.last().unwrap() != indent {
                    return Err(self.error(&format!(
                        "Inconsistent indentation: got {} spaces, expected {}",
                        indent, self.indent_stack.last().unwrap()
                    )));
                }
            }
            break;
        }
        Ok(())
    }

    // --- Main token scanner ---

    fn scan_token(&mut self) -> Result<(), String> {
        let ch = self.peek();

        // Whitespace
        if ch == ' ' || ch == '\t' {
            self.advance();
            return Ok(());
        }

        // Newlines
        if ch == '\n' || ch == '\r' {
            let (line, col) = (self.line, self.column);
            self.advance();
            if ch == '\r' && !self.at_end() && self.peek() == '\n' {
                self.advance();
            }
            self.emit(TokenType::Newline, "\\n", line, col);
            self.at_line_start = true;
            return Ok(());
        }

        // Comments
        if ch == '-' && self.peek_ahead(1) == '-' {
            if self.peek_ahead(2) == '-' {
                self.scan_doc_comment();
            } else {
                self.skip_single_line_comment();
            }
            return Ok(());
        }
        if ch == '{' && self.peek_ahead(1) == '-' {
            self.scan_multiline_comment()?;
            return Ok(());
        }

        // String literals
        if ch == '"' {
            self.scan_string()?;
            return Ok(());
        }

        // Numbers
        if ch.is_ascii_digit() {
            self.scan_number();
            return Ok(());
        }

        // Symbol literals
        if ch == ':' && self.peek_ahead(1).is_alphabetic() {
            self.scan_symbol();
            return Ok(());
        }

        // Identifiers / keywords
        if ch.is_alphabetic() || ch == '_' {
            self.scan_identifier();
            return Ok(());
        }

        // Operators / delimiters
        self.scan_operator()
    }

    // --- Comments ---

    fn skip_single_line_comment(&mut self) {
        while !self.at_end() && self.peek() != '\n' && self.peek() != '\r' {
            self.advance();
        }
    }

    fn scan_doc_comment(&mut self) {
        let (line, col) = (self.line, self.column);
        self.advance(); self.advance(); self.advance(); // skip ---
        if !self.at_end() && self.peek() == ' ' { self.advance(); }
        let start = self.pos;
        while !self.at_end() && self.peek() != '\n' && self.peek() != '\r' {
            self.advance();
        }
        let text: String = self.source[start..self.pos].iter().collect();
        self.emit(TokenType::DocComment, &text, line, col);
    }

    fn scan_multiline_comment(&mut self) -> Result<(), String> {
        self.advance(); self.advance(); // skip {-
        let mut depth = 1;
        while !self.at_end() && depth > 0 {
            if self.peek() == '{' && self.peek_ahead(1) == '-' {
                self.advance(); self.advance();
                depth += 1;
            } else if self.peek() == '-' && self.peek_ahead(1) == '}' {
                self.advance(); self.advance();
                depth -= 1;
            } else {
                self.advance();
            }
        }
        if depth > 0 {
            return Err(self.error("Unterminated multi-line comment"));
        }
        Ok(())
    }

    // --- Strings ---

    fn scan_string(&mut self) -> Result<(), String> {
        let (line, col) = (self.line, self.column);

        // Triple-quoted?
        if self.peek_ahead(1) == '"' && self.peek_ahead(2) == '"' {
            return self.scan_triple_string(line, col);
        }

        self.advance(); // skip opening "
        let mut chars = String::new();
        while !self.at_end() && self.peek() != '"' {
            if self.peek() == '\n' || self.peek() == '\r' {
                return Err(self.error("Unterminated string literal"));
            }
            if self.peek() == '\\' {
                chars.push(self.scan_escape()?);
            } else {
                chars.push(self.advance());
            }
        }

        if self.at_end() {
            return Err(self.error("Unterminated string literal"));
        }

        self.advance(); // skip closing "
        self.emit(TokenType::String, &chars, line, col);
        Ok(())
    }

    fn scan_triple_string(&mut self, line: usize, col: usize) -> Result<(), String> {
        self.advance(); self.advance(); self.advance(); // skip """
        let mut chars = String::new();
        while !self.at_end() {
            if self.peek() == '"' && self.peek_ahead(1) == '"' && self.peek_ahead(2) == '"' {
                self.advance(); self.advance(); self.advance();
                self.emit(TokenType::String, &chars, line, col);
                return Ok(());
            }
            chars.push(self.advance());
        }
        Err(self.error("Unterminated triple-quoted string"))
    }

    fn scan_escape(&mut self) -> Result<char, String> {
        self.advance(); // skip backslash
        if self.at_end() {
            return Err(self.error("Unterminated escape sequence"));
        }
        let ch = self.advance();
        match ch {
            'n' => Ok('\n'),
            't' => Ok('\t'),
            'r' => Ok('\r'),
            '\\' => Ok('\\'),
            '"' => Ok('"'),
            '{' => Ok('{'),
            '}' => Ok('}'),
            _ => Err(self.error(&format!("Invalid escape sequence: \\{}", ch))),
        }
    }

    // --- Numbers ---

    fn scan_number(&mut self) {
        let (line, col) = (self.line, self.column);
        let start = self.pos;

        while !self.at_end() && (self.peek().is_ascii_digit() || self.peek() == '_') {
            self.advance();
        }

        // Float?
        if !self.at_end() && self.peek() == '.' && self.peek_ahead(1).is_ascii_digit() {
            self.advance(); // skip .
            while !self.at_end() && (self.peek().is_ascii_digit() || self.peek() == '_') {
                self.advance();
            }
        }

        let value: String = self.source[start..self.pos].iter().collect();
        self.emit(TokenType::Number, &value, line, col);

        // Check for unit suffix
        self.try_scan_unit();
    }

    fn try_scan_unit(&mut self) {
        let saved_pos = self.pos;
        let saved_line = self.line;
        let saved_col = self.column;

        let mut spaces = 0;
        while !self.at_end() && self.peek() == ' ' {
            self.advance();
            spaces += 1;
        }

        if spaces == 0 || self.at_end() || !self.peek().is_alphabetic() {
            self.pos = saved_pos;
            self.line = saved_line;
            self.column = saved_col;
            return;
        }

        let word_start = self.pos;
        let word_line = self.line;
        let word_col = self.column;
        while !self.at_end() && (self.peek().is_alphanumeric() || self.peek() == '_') {
            self.advance();
        }
        let word: String = self.source[word_start..self.pos].iter().collect();

        if UNIT_SUFFIXES.contains(word.as_str()) {
            self.emit(TokenType::Unit, &word, word_line, word_col);
        } else {
            self.pos = saved_pos;
            self.line = saved_line;
            self.column = saved_col;
        }
    }

    // --- Symbols ---

    fn scan_symbol(&mut self) {
        let (line, col) = (self.line, self.column);
        self.advance(); // skip :
        let start = self.pos;
        while !self.at_end() && (self.peek().is_alphanumeric() || self.peek() == '_') {
            self.advance();
        }
        let name: String = self.source[start..self.pos].iter().collect();
        self.emit(TokenType::Symbol, &name, line, col);
    }

    // --- Identifiers / keywords ---

    fn scan_identifier(&mut self) {
        let (line, col) = (self.line, self.column);
        let start = self.pos;
        while !self.at_end() && (self.peek().is_alphanumeric() || self.peek() == '_') {
            self.advance();
        }
        let word: String = self.source[start..self.pos].iter().collect();

        if let Some(&kw) = KEYWORDS.get(word.as_str()) {
            self.emit(kw, &word, line, col);
        } else {
            self.emit(TokenType::Identifier, &word, line, col);
        }
    }

    // --- Operators / delimiters ---

    fn scan_operator(&mut self) -> Result<(), String> {
        let (line, col) = (self.line, self.column);
        let ch = self.advance();

        match ch {
            '+' => self.emit(TokenType::Plus, "+", line, col),
            '*' => self.emit(TokenType::Star, "*", line, col),
            '/' => self.emit(TokenType::Slash, "/", line, col),
            '.' => self.emit(TokenType::Dot, ".", line, col),
            ',' => self.emit(TokenType::Comma, ",", line, col),
            '(' => self.emit(TokenType::LParen, "(", line, col),
            ')' => self.emit(TokenType::RParen, ")", line, col),
            '[' => self.emit(TokenType::LBracket, "[", line, col),
            ']' => self.emit(TokenType::RBracket, "]", line, col),
            '{' => self.emit(TokenType::LBrace, "{", line, col),
            '}' => self.emit(TokenType::RBrace, "}", line, col),
            ':' => {
                if self.match_char(':') {
                    self.emit(TokenType::DoubleColon, "::", line, col);
                } else {
                    self.emit(TokenType::Colon, ":", line, col);
                }
            }
            '-' => {
                if self.match_char('>') {
                    self.emit(TokenType::Arrow, "->", line, col);
                } else {
                    self.emit(TokenType::Minus, "-", line, col);
                }
            }
            '>' => {
                if self.match_char('=') {
                    self.emit(TokenType::Gte, ">=", line, col);
                } else {
                    self.emit(TokenType::Gt, ">", line, col);
                }
            }
            '<' => {
                if self.match_char('=') {
                    self.emit(TokenType::Lte, "<=", line, col);
                } else {
                    self.emit(TokenType::Lt, "<", line, col);
                }
            }
            '=' => self.emit(TokenType::Eq, "=", line, col),
            '!' => {
                if self.match_char('=') {
                    self.emit(TokenType::Neq, "!=", line, col);
                } else {
                    return Err(self.error("Unexpected character: '!'"));
                }
            }
            '|' => {
                if self.match_char('>') {
                    self.emit(TokenType::Pipe, "|>", line, col);
                } else {
                    return Err(self.error("Unexpected character: '|'"));
                }
            }
            _ => {
                return Err(self.error(&format!("Unexpected character: {:?}", ch)));
            }
        }
        Ok(())
    }
}
