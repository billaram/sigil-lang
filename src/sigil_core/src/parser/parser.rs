//! Recursive descent parser for the Sigil language.
//!
//! Converts a `Vec<Token>` (from the lexer) into a `Program` AST.
//! Ported from the Python reference implementation.

use super::ast::*;
use crate::lexer::tokens::{Token, TokenType};

/// Token types that start a top-level declaration (used for error recovery).
const DECLARATION_STARTS: &[TokenType] = &[
    TokenType::Rule,
    TokenType::Compute,
    TokenType::Neural,
    TokenType::Type,
    TokenType::Define,
    TokenType::Import,
    TokenType::From,
    TokenType::Export,
    TokenType::Main,
    TokenType::Module,
];

// ============================================================
// Public entry point
// ============================================================

/// Parse a token stream into a Program AST.
pub fn parse(tokens: Vec<Token>) -> Result<Program, String> {
    let mut parser = Parser::new(tokens);
    parser.parse_program()
}

// ============================================================
// Parser struct
// ============================================================

struct Parser {
    tokens: Vec<Token>,
    pos: usize,
}

impl Parser {
    fn new(tokens: Vec<Token>) -> Self {
        Parser { tokens, pos: 0 }
    }

    // --------------------------------------------------------
    // Token access helpers
    // --------------------------------------------------------

    fn current(&self) -> &Token {
        if self.pos >= self.tokens.len() {
            self.tokens.last().unwrap() // EOF sentinel
        } else {
            &self.tokens[self.pos]
        }
    }

    fn peek(&self) -> TokenType {
        self.current().token_type
    }

    fn peek_value(&self) -> &str {
        &self.current().value
    }

    fn at_end(&self) -> bool {
        self.peek() == TokenType::Eof
    }

    fn advance(&mut self) -> Token {
        let tok = self.current().clone();
        if !self.at_end() {
            self.pos += 1;
        }
        tok
    }

    fn expect(&mut self, tt: TokenType) -> Result<Token, String> {
        if self.peek() != tt {
            let tok = self.current();
            return Err(format!(
                "Expected {:?}, got {:?} ({:?}) at line {} col {}",
                tt, tok.token_type, tok.value, tok.line, tok.column,
            ));
        }
        Ok(self.advance())
    }

    fn match_token(&mut self, types: &[TokenType]) -> Option<Token> {
        if types.contains(&self.peek()) {
            Some(self.advance())
        } else {
            None
        }
    }

    fn check(&self, types: &[TokenType]) -> bool {
        types.contains(&self.peek())
    }

    fn skip_newlines(&mut self) {
        while self.match_token(&[TokenType::Newline]).is_some() {}
    }

    fn peek_ahead_type(&self, offset: usize) -> TokenType {
        let idx = self.pos + offset;
        if idx >= self.tokens.len() {
            TokenType::Eof
        } else {
            self.tokens[idx].token_type
        }
    }

    /// Accept IDENTIFIER or keywords valid in module paths.
    fn expect_identifier_or_keyword(&mut self) -> Result<Token, String> {
        if self.peek() == TokenType::Identifier {
            return self.expect(TokenType::Identifier);
        }
        let keyword_types = [
            TokenType::List,
            TokenType::Match,
            TokenType::Type,
            TokenType::Rule,
            TokenType::Import,
            TokenType::Export,
            TokenType::Module,
        ];
        if keyword_types.contains(&self.peek()) {
            Ok(self.advance())
        } else {
            let tok = self.current();
            Err(format!(
                "Expected identifier, got {:?} ({:?}) at line {} col {}",
                tok.token_type, tok.value, tok.line, tok.column,
            ))
        }
    }

    // --------------------------------------------------------
    // Error recovery
    // --------------------------------------------------------

    fn synchronize(&mut self) {
        while !self.at_end() {
            if DECLARATION_STARTS.contains(&self.peek()) {
                return;
            }
            if self.peek() == TokenType::Dedent || self.peek() == TokenType::Newline {
                self.advance();
                continue;
            }
            self.advance();
        }
    }

    // --------------------------------------------------------
    // Top-level parsing
    // --------------------------------------------------------

    fn parse_program(&mut self) -> Result<Program, String> {
        self.skip_newlines();

        let module = if self.check(&[TokenType::Module]) {
            Some(self.parse_module_decl()?)
        } else {
            None
        };

        let mut imports: Vec<ImportDecl> = Vec::new();
        let mut declarations: Vec<Declaration> = Vec::new();
        let mut errors: Vec<String> = Vec::new();

        while !self.at_end() {
            self.skip_newlines();
            if self.at_end() {
                break;
            }

            let result: Result<(), String> = (|| {
                match self.peek() {
                    TokenType::Import => {
                        imports.push(self.parse_import_decl()?);
                    }
                    TokenType::From => {
                        imports.push(self.parse_from_import()?);
                    }
                    TokenType::Type => {
                        declarations.push(self.parse_type_decl()?);
                    }
                    TokenType::Define => {
                        declarations.push(self.parse_const_decl()?);
                    }
                    TokenType::Rule => {
                        declarations.push(self.parse_rule_decl()?);
                    }
                    TokenType::Compute => {
                        declarations.push(self.parse_compute_decl()?);
                    }
                    TokenType::Neural => {
                        declarations.push(self.parse_neural_decl()?);
                    }
                    TokenType::Main => {
                        declarations.push(self.parse_main_decl()?);
                    }
                    TokenType::Export => {
                        declarations.push(self.parse_export_decl()?);
                    }
                    TokenType::DocComment => {
                        self.advance(); // skip doc comments
                    }
                    _ => {
                        let tok = self.current();
                        return Err(format!(
                            "Unexpected token at top level: {:?} at line {} col {}. \
                             Declarations must start with 'rule', 'compute', 'neural', \
                             'type', 'define', 'import', 'export', or 'main'",
                            tok.token_type, tok.line, tok.column,
                        ));
                    }
                }
                Ok(())
            })();

            if let Err(e) = result {
                errors.push(e);
                self.synchronize();
            }
        }

        if !errors.is_empty() {
            return Err(errors.join("\n"));
        }

        Ok(Program {
            module,
            imports,
            declarations,
        })
    }

    // --------------------------------------------------------
    // Module declaration
    // --------------------------------------------------------

    fn parse_module_decl(&mut self) -> Result<ModuleDecl, String> {
        self.expect(TokenType::Module)?;
        let path = self.parse_dotted_name()?;
        self.skip_newlines();
        Ok(ModuleDecl { path })
    }

    fn parse_dotted_name(&mut self) -> Result<String, String> {
        let mut parts = vec![self.expect_identifier_or_keyword()?.value];
        while self.match_token(&[TokenType::Dot]).is_some() {
            parts.push(self.expect_identifier_or_keyword()?.value);
        }
        Ok(parts.join("."))
    }

    fn parse_rust_path(&mut self) -> Result<String, String> {
        let mut parts = vec![self.expect(TokenType::Identifier)?.value];
        while self.match_token(&[TokenType::DoubleColon]).is_some() {
            parts.push(self.expect(TokenType::Identifier)?.value);
        }
        Ok(parts.join("::"))
    }

    // --------------------------------------------------------
    // Import declarations
    // --------------------------------------------------------

    fn parse_import_decl(&mut self) -> Result<ImportDecl, String> {
        self.expect(TokenType::Import)?;

        let mut kind = "sigil".to_string();
        if self.match_token(&[TokenType::Python]).is_some() {
            kind = "python".to_string();
        } else if self.match_token(&[TokenType::Rust]).is_some() {
            kind = "rust".to_string();
        }

        let source = if kind == "rust" {
            self.parse_rust_path()?
        } else {
            self.parse_dotted_name()?
        };

        let alias = if self.match_token(&[TokenType::As]).is_some() {
            Some(self.expect(TokenType::Identifier)?.value)
        } else {
            None
        };

        self.skip_newlines();
        Ok(ImportDecl {
            source,
            kind,
            alias,
            names: Vec::new(),
        })
    }

    fn parse_from_import(&mut self) -> Result<ImportDecl, String> {
        self.expect(TokenType::From)?;

        let mut kind = "sigil".to_string();
        if self.match_token(&[TokenType::Python]).is_some() {
            kind = "python".to_string();
        } else if self.match_token(&[TokenType::Rust]).is_some() {
            kind = "rust".to_string();
        }

        let source = self.parse_dotted_name()?;
        self.expect(TokenType::Import)?;

        let mut names = vec![self.expect(TokenType::Identifier)?.value];
        while self.match_token(&[TokenType::Comma]).is_some() {
            names.push(self.expect(TokenType::Identifier)?.value);
        }

        self.skip_newlines();
        Ok(ImportDecl {
            source,
            kind,
            alias: None,
            names,
        })
    }

    fn parse_export_decl(&mut self) -> Result<Declaration, String> {
        self.expect(TokenType::Export)?;
        let mut names = vec![self.expect(TokenType::Identifier)?.value];
        while self.match_token(&[TokenType::Comma]).is_some() {
            names.push(self.expect(TokenType::Identifier)?.value);
        }
        self.skip_newlines();
        Ok(Declaration::Export(ExportDecl { names }))
    }

    // --------------------------------------------------------
    // Type declarations
    // --------------------------------------------------------

    fn parse_type_decl(&mut self) -> Result<Declaration, String> {
        self.expect(TokenType::Type)?;
        let name = self.expect(TokenType::Identifier)?.value;

        let mut params: Vec<String> = Vec::new();
        if self.match_token(&[TokenType::LBracket]).is_some() {
            params.push(self.expect(TokenType::Identifier)?.value);
            while self.match_token(&[TokenType::Comma]).is_some() {
                params.push(self.expect(TokenType::Identifier)?.value);
            }
            self.expect(TokenType::RBracket)?;
        }

        self.expect(TokenType::Is)?;
        let body = self.parse_type_body()?;
        self.skip_newlines();
        Ok(Declaration::Type(TypeDecl { name, params, body }))
    }

    fn parse_type_body(&mut self) -> Result<TypeBody, String> {
        if self.check(&[TokenType::Record]) {
            return self.parse_record_body().map(TypeBody::Record);
        }
        if self.check(&[TokenType::One]) {
            return self.parse_enum_body().map(TypeBody::Enum);
        }
        // Alias or unit type
        let type_ref = self.parse_type_ref()?;
        if self.check(&[TokenType::With]) {
            self.advance();
            self.expect(TokenType::Identifier)?; // "unit"
            let unit = self.expect(TokenType::Identifier)?.value;
            return Ok(TypeBody::Unit {
                base_type: type_ref,
                unit,
            });
        }
        Ok(TypeBody::Alias(type_ref))
    }

    fn parse_record_body(&mut self) -> Result<RecordBody, String> {
        self.expect(TokenType::Record)?;
        self.expect(TokenType::Colon)?;
        self.skip_newlines();
        self.expect(TokenType::Indent)?;

        let mut fields: Vec<FieldDef> = Vec::new();
        while !self.check(&[TokenType::Dedent]) && !self.at_end() {
            self.skip_newlines();
            if self.check(&[TokenType::Dedent]) {
                break;
            }
            fields.push(self.parse_field_def()?);
            self.skip_newlines();
        }

        self.expect(TokenType::Dedent)?;
        Ok(RecordBody { fields })
    }

    fn parse_field_def(&mut self) -> Result<FieldDef, String> {
        let name = self.expect(TokenType::Identifier)?.value;
        self.expect(TokenType::Colon)?;
        let type_ref = self.parse_type_ref()?;
        Ok(FieldDef { name, type_ref })
    }

    fn parse_enum_body(&mut self) -> Result<EnumBody, String> {
        self.expect(TokenType::One)?;
        self.expect(TokenType::Of)?;
        self.expect(TokenType::Colon)?;
        self.skip_newlines();
        self.expect(TokenType::Indent)?;

        let mut variants: Vec<EnumVariant> = Vec::new();
        while !self.check(&[TokenType::Dedent]) && !self.at_end() {
            self.skip_newlines();
            if self.check(&[TokenType::Dedent]) {
                break;
            }
            variants.push(self.parse_enum_variant()?);
            self.skip_newlines();
        }

        self.expect(TokenType::Dedent)?;
        Ok(EnumBody { variants })
    }

    fn parse_enum_variant(&mut self) -> Result<EnumVariant, String> {
        let name = self.expect(TokenType::Identifier)?.value;
        let mut fields: Vec<FieldDef> = Vec::new();
        if self.match_token(&[TokenType::With]).is_some() {
            fields.push(self.parse_field_def()?);
            while self.match_token(&[TokenType::Comma]).is_some() {
                fields.push(self.parse_field_def()?);
            }
        }
        Ok(EnumVariant { name, fields })
    }

    fn parse_type_ref(&mut self) -> Result<TypeRef, String> {
        // list of X
        if self.check(&[TokenType::List]) {
            self.advance();
            self.expect(TokenType::Of)?;
            let element = self.parse_type_ref()?;
            return Ok(TypeRef::List(Box::new(element)));
        }

        // Option[X]
        if self.check(&[TokenType::Option_]) {
            self.advance();
            self.expect(TokenType::LBracket)?;
            let inner = self.parse_type_ref()?;
            self.expect(TokenType::RBracket)?;
            return Ok(TypeRef::Option(Box::new(inner)));
        }

        // Inline record type
        if self.check(&[TokenType::Record]) {
            return self.parse_inline_record_type();
        }

        // Named type with optional params
        let name = self.expect(TokenType::Identifier)?.value;
        let mut params: Vec<TypeRef> = Vec::new();
        if self.match_token(&[TokenType::LBracket]).is_some() {
            params.push(self.parse_type_ref()?);
            while self.match_token(&[TokenType::Comma]).is_some() {
                params.push(self.parse_type_ref()?);
            }
            self.expect(TokenType::RBracket)?;
        }

        Ok(TypeRef::Named { name, params })
    }

    fn parse_inline_record_type(&mut self) -> Result<TypeRef, String> {
        self.expect(TokenType::Record)?;
        self.expect(TokenType::Colon)?;
        self.skip_newlines();
        self.expect(TokenType::Indent)?;

        let mut fields: Vec<FieldDef> = Vec::new();
        while !self.check(&[TokenType::Dedent]) && !self.at_end() {
            self.skip_newlines();
            if self.check(&[TokenType::Dedent]) {
                break;
            }
            fields.push(self.parse_field_def()?);
            self.skip_newlines();
        }

        self.expect(TokenType::Dedent)?;
        Ok(TypeRef::InlineRecord(fields))
    }

    // --------------------------------------------------------
    // Constant declarations
    // --------------------------------------------------------

    fn parse_const_decl(&mut self) -> Result<Declaration, String> {
        self.expect(TokenType::Define)?;
        let name = self.expect(TokenType::Identifier)?.value;
        self.expect(TokenType::As)?;
        let value = self.parse_expression()?;
        self.skip_newlines();
        Ok(Declaration::Const(ConstDecl { name, value }))
    }

    // --------------------------------------------------------
    // Rule declarations
    // --------------------------------------------------------

    fn parse_rule_decl(&mut self) -> Result<Declaration, String> {
        self.expect(TokenType::Rule)?;
        let name = self.expect(TokenType::Identifier)?.value;

        let mut priority: i64 = 0;
        if self.match_token(&[TokenType::With]).is_some() {
            self.expect(TokenType::Priority)?;
            let num_tok = self.expect(TokenType::Number)?;
            priority = num_tok
                .value
                .parse::<i64>()
                .map_err(|e| format!("Invalid priority number: {}", e))?;
        }

        self.expect(TokenType::Colon)?;
        self.skip_newlines();
        self.expect(TokenType::Indent)?;

        // Metadata fields (version, author, tags)
        let mut metadata: Vec<MetaField> = Vec::new();
        while self.check(&[TokenType::Identifier])
            && matches!(self.peek_value(), "version" | "author" | "tags")
        {
            let meta_name = self.advance().value;
            let meta_value = self.parse_expression()?;
            metadata.push(MetaField {
                name: meta_name,
                value: meta_value,
            });
            self.skip_newlines();
        }

        // Given clauses
        let mut given_clauses: Vec<GivenClause> = Vec::new();
        while self.check(&[TokenType::Given]) {
            given_clauses.push(self.parse_given_clause()?);
            self.skip_newlines();
        }

        // When + conditions
        self.expect(TokenType::When)?;
        let first_cond = self.parse_condition()?;
        let mut conditions = vec![first_cond];
        self.skip_newlines();

        // And/Or conditions — build compound tree
        while self.check(&[TokenType::And, TokenType::Or]) {
            let op_tok = self.advance();
            let negate = self.match_token(&[TokenType::Not]).is_some();
            let mut cond = self.parse_condition()?;
            if negate {
                cond = Condition::Not(Box::new(cond));
            }
            // Build compound: left = accumulated, right = new cond
            let left = conditions.pop().unwrap();
            let compound = Condition::Compound {
                operator: op_tok.value.clone(),
                left: Box::new(left),
                right: Box::new(cond),
            };
            conditions.push(compound);
            self.skip_newlines();
        }

        // Optional temporal constraint: within <expr> <unit>
        let temporal = if self.check(&[TokenType::Within]) {
            self.advance();
            let duration = self.parse_expression()?;
            // The unit may have been captured on the literal or be a standalone token
            let unit = if let Expression::Literal { unit: Some(ref u), .. } = duration {
                u.clone()
            } else if self.check(&[TokenType::Unit]) {
                self.advance().value
            } else {
                self.expect_identifier_or_keyword()?.value
            };
            self.skip_newlines();
            Some(TemporalConstraint { duration, unit })
        } else {
            None
        };

        // Then action
        self.expect(TokenType::Then)?;
        let action = self.parse_action()?;
        self.skip_newlines();

        // Explain
        let explain = if self.match_token(&[TokenType::Explain]).is_some() {
            let s = self.expect(TokenType::String)?.value;
            self.skip_newlines();
            Some(s)
        } else {
            None
        };

        // Trace
        let trace = if self.check(&[TokenType::Trace]) {
            let t = self.parse_trace_block()?;
            self.skip_newlines();
            t
        } else {
            Vec::new()
        };

        self.expect(TokenType::Dedent)?;

        Ok(Declaration::Rule(RuleDecl {
            name,
            conditions,
            action,
            priority,
            given_clauses,
            explain,
            trace,
            metadata,
            temporal,
        }))
    }

    fn parse_given_clause(&mut self) -> Result<GivenClause, String> {
        self.expect(TokenType::Given)?;
        let name = self.expect(TokenType::Identifier)?.value;
        if self.match_token(&[TokenType::As]).is_some() {
            let value = self.parse_expression()?;
            return Ok(GivenClause {
                name,
                source: value,
                kind: "as".to_string(),
            });
        }
        self.expect(TokenType::From)?;
        let value = self.parse_expression()?;
        Ok(GivenClause {
            name,
            source: value,
            kind: "from".to_string(),
        })
    }

    fn parse_trace_block(&mut self) -> Result<Vec<TraceField>, String> {
        self.expect(TokenType::Trace)?;
        self.expect(TokenType::Colon)?;
        self.skip_newlines();
        self.expect(TokenType::Indent)?;

        let mut fields: Vec<TraceField> = Vec::new();
        while !self.check(&[TokenType::Dedent]) && !self.at_end() {
            self.skip_newlines();
            if self.check(&[TokenType::Dedent]) {
                break;
            }
            let name = self.expect(TokenType::Identifier)?.value;
            let value = self.parse_expression()?;
            fields.push(TraceField { name, value });
            self.skip_newlines();
        }

        self.expect(TokenType::Dedent)?;
        Ok(fields)
    }

    // --------------------------------------------------------
    // Conditions
    // --------------------------------------------------------

    fn parse_condition(&mut self) -> Result<Condition, String> {
        // Quantified: any/all/none X in Y has/have <cond>
        if self.check(&[TokenType::Any, TokenType::All, TokenType::None_]) {
            return self.parse_quantified_condition();
        }

        // Parse left-hand expression (additive, NOT full expression — avoid consuming |>)
        let left = self.parse_additive()?;

        // Determine condition type from what follows
        if self.check(&[TokenType::Exceeds]) {
            self.advance();
            let right = self.parse_additive()?;
            return Ok(Condition::Comparison {
                left,
                operator: "exceeds".to_string(),
                right,
                right2: None,
            });
        }

        if self.check(&[TokenType::Equals]) {
            self.advance();
            let right = self.parse_additive()?;
            return Ok(Condition::Comparison {
                left,
                operator: "equals".to_string(),
                right,
                right2: None,
            });
        }

        if self.check(&[TokenType::Is]) {
            return self.parse_is_condition(left);
        }

        if self.check(&[TokenType::In]) {
            self.advance();
            let collection = self.parse_additive()?;
            return Ok(Condition::Membership {
                element: left,
                collection,
                negated: false,
            });
        }

        if self.check(&[TokenType::Not]) && self.peek_ahead_type(1) == TokenType::In {
            self.advance(); // not
            self.advance(); // in
            let collection = self.parse_additive()?;
            return Ok(Condition::Membership {
                element: left,
                collection,
                negated: true,
            });
        }

        if self.check(&[TokenType::Contains]) {
            self.advance();
            let element = self.parse_additive()?;
            return Ok(Condition::Contains {
                collection: left,
                element,
            });
        }

        if self.check(&[TokenType::Starts]) {
            self.advance();
            self.expect(TokenType::With)?;
            let pattern = self.parse_additive()?;
            return Ok(Condition::StringCond {
                string: left,
                operator: "starts with".to_string(),
                pattern,
            });
        }

        if self.check(&[TokenType::Ends]) {
            self.advance();
            self.expect(TokenType::With)?;
            let pattern = self.parse_additive()?;
            return Ok(Condition::StringCond {
                string: left,
                operator: "ends with".to_string(),
                pattern,
            });
        }

        if self.check(&[TokenType::Matches]) {
            self.advance();
            self.expect(TokenType::Pattern)?;
            let pattern = self.parse_additive()?;
            return Ok(Condition::StringCond {
                string: left,
                operator: "matches pattern".to_string(),
                pattern,
            });
        }

        if self.check(&[TokenType::Has]) {
            self.advance();
            if self.match_token(&[TokenType::Count]).is_some() {
                let count = self.parse_additive()?;
                return Ok(Condition::HasCount {
                    collection: left,
                    count,
                });
            }
        }

        // Comparison operators: > < >= <= = !=
        if self.check(&[
            TokenType::Gt,
            TokenType::Lt,
            TokenType::Gte,
            TokenType::Lte,
            TokenType::Eq,
            TokenType::Neq,
        ]) {
            let op = self.advance().value;
            let right = self.parse_additive()?;
            return Ok(Condition::Comparison {
                left,
                operator: op,
                right,
                right2: None,
            });
        }

        // Fallback: treat expression as boolean condition (value=true)
        Ok(Condition::Boolean {
            expression: left,
            value: true,
        })
    }

    fn parse_is_condition(&mut self, left: Expression) -> Result<Condition, String> {
        self.expect(TokenType::Is)?;

        // is not ...
        if self.check(&[TokenType::Not]) {
            self.advance();

            if self.check(&[TokenType::True]) {
                self.advance();
                return Ok(Condition::Boolean {
                    expression: left,
                    value: false,
                });
            }
            if self.check(&[TokenType::Assigned]) {
                self.advance();
                return Ok(Condition::IsAssigned {
                    expression: left,
                    negated: true,
                });
            }
            if self.check(&[TokenType::Empty]) {
                self.advance();
                return Ok(Condition::IsEmpty {
                    expression: left,
                    negated: true,
                });
            }
            if self.check(&[TokenType::In]) {
                self.advance();
                let collection = self.parse_additive()?;
                return Ok(Condition::Membership {
                    element: left,
                    collection,
                    negated: true,
                });
            }
            // "is not <value>"
            let right = self.parse_additive()?;
            return Ok(Condition::Comparison {
                left,
                operator: "is not".to_string(),
                right,
                right2: None,
            });
        }

        // is below
        if self.check(&[TokenType::Below]) {
            self.advance();
            let right = self.parse_additive()?;
            return Ok(Condition::Comparison {
                left,
                operator: "is below".to_string(),
                right,
                right2: None,
            });
        }

        // is between X and Y
        if self.check(&[TokenType::Between]) {
            self.advance();
            let low = self.parse_additive()?;
            self.expect(TokenType::And)?;
            let high = self.parse_additive()?;
            return Ok(Condition::Comparison {
                left,
                operator: "is between".to_string(),
                right: low,
                right2: Some(high),
            });
        }

        // is at least / is at most
        if self.check(&[TokenType::At]) {
            self.advance();
            if self.match_token(&[TokenType::Least]).is_some() {
                let right = self.parse_additive()?;
                return Ok(Condition::Comparison {
                    left,
                    operator: "is at least".to_string(),
                    right,
                    right2: None,
                });
            }
            if self.match_token(&[TokenType::Most]).is_some() {
                let right = self.parse_additive()?;
                return Ok(Condition::Comparison {
                    left,
                    operator: "is at most".to_string(),
                    right,
                    right2: None,
                });
            }
        }

        // is empty
        if self.check(&[TokenType::Empty]) {
            self.advance();
            return Ok(Condition::IsEmpty {
                expression: left,
                negated: false,
            });
        }

        // is true / is false
        if self.check(&[TokenType::True]) {
            self.advance();
            return Ok(Condition::Boolean {
                expression: left,
                value: true,
            });
        }
        if self.check(&[TokenType::False]) {
            self.advance();
            return Ok(Condition::Boolean {
                expression: left,
                value: false,
            });
        }

        // is assigned
        if self.check(&[TokenType::Assigned]) {
            self.advance();
            return Ok(Condition::IsAssigned {
                expression: left,
                negated: false,
            });
        }

        // is in
        if self.check(&[TokenType::In]) {
            self.advance();
            let collection = self.parse_additive()?;
            return Ok(Condition::Membership {
                element: left,
                collection,
                negated: false,
            });
        }

        // is <value> (equality comparison)
        let right = self.parse_additive()?;
        Ok(Condition::Comparison {
            left,
            operator: "is".to_string(),
            right,
            right2: None,
        })
    }

    fn parse_quantified_condition(&mut self) -> Result<Condition, String> {
        let quantifier = self.advance().value; // any, all, none

        let variable = self.expect(TokenType::Identifier)?.value;
        self.expect(TokenType::In)?;
        let collection = self.parse_additive()?;

        // Accept has/have as explicit bridge
        self.match_token(&[TokenType::Has, TokenType::Have]);

        // Build condition with the variable as implicit left
        let var_expr = Expression::Identifier(variable.clone());
        let condition = self.parse_condition_with_left(var_expr)?;

        Ok(Condition::Quantified {
            quantifier,
            variable,
            collection,
            condition: Box::new(condition),
        })
    }

    fn parse_condition_with_left(&mut self, left: Expression) -> Result<Condition, String> {
        if self.check(&[TokenType::Exceeds]) {
            self.advance();
            let right = self.parse_additive()?;
            return Ok(Condition::Comparison {
                left,
                operator: "exceeds".to_string(),
                right,
                right2: None,
            });
        }

        if self.check(&[TokenType::Is]) {
            return self.parse_is_condition(left);
        }

        if self.check(&[TokenType::In]) {
            self.advance();
            let collection = self.parse_additive()?;
            return Ok(Condition::Membership {
                element: left,
                collection,
                negated: false,
            });
        }

        // Fallback: parse a full condition
        self.parse_condition()
    }

    // --------------------------------------------------------
    // Actions
    // --------------------------------------------------------

    fn parse_action(&mut self) -> Result<Action, String> {
        // Block action: then: (with NEWLINE + INDENT)
        if self.check(&[TokenType::Colon]) {
            return self.parse_block_action();
        }

        // Simple or set action
        let name_tok = self.advance();
        let name = name_tok.value.clone();

        // Check for "X is Y" (set action)
        if self.check(&[TokenType::Is]) {
            self.advance();
            let value = self.parse_action_value()?;
            let target_id = Expression::Identifier(name);
            return Ok(Action::Set {
                target: target_id,
                value,
            });
        }

        // Check if next is an identifier (e.g. "trigger alert", "log status")
        if self.check(&[TokenType::Identifier]) {
            let target = Some(name.clone());
            let name_tok2 = self.advance();
            let name2 = name_tok2.value.clone();

            // "field is value" (set action with dotted target)
            if self.check(&[TokenType::Is]) {
                self.advance();
                let value = self.parse_action_value()?;
                let target_name = target.unwrap();
                let target_expr = Expression::FieldAccess {
                    object: Box::new(Expression::Identifier(target_name)),
                    field: name2,
                };
                return Ok(Action::Set {
                    target: target_expr,
                    value,
                });
            }

            // Params or simple action with name2
            let mut params: Vec<ActionParam> = Vec::new();
            if self.match_token(&[TokenType::With]).is_some() {
                params = self.parse_action_params()?;
            } else if !self.check(&[
                TokenType::Newline,
                TokenType::Explain,
                TokenType::Trace,
                TokenType::Dedent,
                TokenType::Eof,
                TokenType::And,
                TokenType::Or,
            ]) {
                // Positional argument without "with"
                let value = self.parse_expression()?;
                params.push(ActionParam {
                    name: name2.clone(),
                    value,
                });
            }

            return Ok(Action::Simple {
                name: name2,
                target,
                params,
            });
        }

        // No identifier following — check for params
        let mut params: Vec<ActionParam> = Vec::new();
        if self.match_token(&[TokenType::With]).is_some() {
            params = self.parse_action_params()?;
        } else if !self.check(&[
            TokenType::Newline,
            TokenType::Explain,
            TokenType::Trace,
            TokenType::Dedent,
            TokenType::Eof,
            TokenType::And,
            TokenType::Or,
        ]) {
            let value = self.parse_expression()?;
            params.push(ActionParam {
                name: name.clone(),
                value,
            });
        }

        Ok(Action::Simple {
            name,
            target: None,
            params,
        })
    }

    fn parse_action_value(&mut self) -> Result<Expression, String> {
        let expr = self.parse_expression()?;

        // Constructor: "block with reason: ..."
        if self.match_token(&[TokenType::With]).is_some() {
            if let Expression::Identifier(ref ident_name) = expr {
                let params = self.parse_action_params()?;
                return Ok(Expression::Constructor {
                    name: ident_name.clone(),
                    fields: params,
                });
            }
        }
        Ok(expr)
    }

    fn parse_action_params(&mut self) -> Result<Vec<ActionParam>, String> {
        let mut params: Vec<ActionParam> = Vec::new();

        let name = self.expect(TokenType::Identifier)?.value;
        self.match_token(&[TokenType::Colon]); // colon is optional
        let value = self.parse_expression()?;
        params.push(ActionParam { name, value });

        while self.match_token(&[TokenType::Comma]).is_some() {
            let name = self.expect(TokenType::Identifier)?.value;
            self.match_token(&[TokenType::Colon]);
            let value = self.parse_expression()?;
            params.push(ActionParam { name, value });
        }

        Ok(params)
    }

    fn parse_block_action(&mut self) -> Result<Action, String> {
        self.expect(TokenType::Colon)?;
        self.skip_newlines();
        self.expect(TokenType::Indent)?;
        let body = self.parse_statement_block()?;
        self.expect(TokenType::Dedent)?;
        Ok(Action::Block { body })
    }

    // --------------------------------------------------------
    // Compute declarations
    // --------------------------------------------------------

    fn parse_compute_decl(&mut self) -> Result<Declaration, String> {
        self.expect(TokenType::Compute)?;
        let name = self.expect(TokenType::Identifier)?.value;

        let mut params: Vec<Param> = Vec::new();
        if self.match_token(&[TokenType::From]).is_some() {
            params = self.parse_param_list()?;
        }

        let return_type = if self.match_token(&[TokenType::Returns]).is_some() {
            Some(self.parse_type_ref()?)
        } else {
            None
        };

        self.expect(TokenType::Colon)?;
        self.skip_newlines();
        self.expect(TokenType::Indent)?;
        let body = self.parse_statement_block()?;
        self.expect(TokenType::Dedent)?;
        self.skip_newlines();

        Ok(Declaration::Compute(ComputeDecl {
            name,
            params,
            body,
            return_type,
        }))
    }

    fn parse_param_list(&mut self) -> Result<Vec<Param>, String> {
        let mut params = vec![self.parse_param()?];
        while self.match_token(&[TokenType::Comma]).is_some() {
            params.push(self.parse_param()?);
        }
        Ok(params)
    }

    fn parse_param(&mut self) -> Result<Param, String> {
        let name = self.expect(TokenType::Identifier)?.value;
        let type_ref = if self.match_token(&[TokenType::Colon]).is_some() {
            Some(self.parse_type_ref()?)
        } else {
            None
        };
        Ok(Param { name, type_ref })
    }

    // --------------------------------------------------------
    // Neural declarations
    // --------------------------------------------------------

    fn parse_neural_decl(&mut self) -> Result<Declaration, String> {
        self.expect(TokenType::Neural)?;
        let name = self.expect(TokenType::Identifier)?.value;
        self.expect(TokenType::From)?;
        let param_name = self.expect(TokenType::Identifier)?.value;
        self.expect(TokenType::Colon)?;
        let param_type = self.parse_type_ref()?;
        self.expect(TokenType::Colon)?;
        self.skip_newlines();
        self.expect(TokenType::Indent)?;

        let mut fields: Vec<NeuralField> = Vec::new();
        while !self.check(&[TokenType::Dedent]) && !self.at_end() {
            self.skip_newlines();
            if self.check(&[TokenType::Dedent]) {
                break;
            }
            fields.push(self.parse_neural_field()?);
            self.skip_newlines();
        }

        self.expect(TokenType::Dedent)?;
        self.skip_newlines();

        Ok(Declaration::Neural(NeuralDecl {
            name,
            param_name,
            param_type,
            fields,
        }))
    }

    fn parse_neural_field(&mut self) -> Result<NeuralField, String> {
        // "model <string>", "confidence_threshold <number>", etc.
        if self.check(&[TokenType::Identifier]) {
            let name = self.advance().value;
            let value = self.parse_expression()?;
            return Ok(NeuralField {
                name,
                value: NeuralFieldValue::Expr(value),
            });
        }

        // "returns <type>"
        if self.match_token(&[TokenType::Returns]).is_some() {
            let type_ref = self.parse_type_ref()?;
            return Ok(NeuralField {
                name: "returns".to_string(),
                value: NeuralFieldValue::Type(type_ref),
            });
        }

        // "using python <dotted.path>"
        if self.match_token(&[TokenType::Using]).is_some() {
            self.expect(TokenType::Python)?;
            let path = self.parse_dotted_name()?;
            return Ok(NeuralField {
                name: "using".to_string(),
                value: NeuralFieldValue::Expr(Expression::Identifier(path)),
            });
        }

        // "fallback to <expr>"
        if self.match_token(&[TokenType::Fallback]).is_some() {
            self.expect(TokenType::To)?;
            let value = self.parse_expression()?;
            return Ok(NeuralField {
                name: "fallback".to_string(),
                value: NeuralFieldValue::Expr(value),
            });
        }

        let tok = self.current();
        Err(format!(
            "Unexpected token in neural block: {:?} at line {} col {}",
            tok.token_type, tok.line, tok.column,
        ))
    }

    // --------------------------------------------------------
    // Main declaration
    // --------------------------------------------------------

    fn parse_main_decl(&mut self) -> Result<Declaration, String> {
        self.expect(TokenType::Main)?;
        self.expect(TokenType::Colon)?;
        self.skip_newlines();
        self.expect(TokenType::Indent)?;

        let body = self.parse_statement_block()?;

        // Optional trace block at end of main
        let trace = if self.check(&[TokenType::Trace]) {
            let t = self.parse_trace_block()?;
            self.skip_newlines();
            t
        } else {
            Vec::new()
        };

        self.expect(TokenType::Dedent)?;
        self.skip_newlines();

        Ok(Declaration::Main(MainDecl { body, trace }))
    }

    // --------------------------------------------------------
    // Statements
    // --------------------------------------------------------

    fn parse_statement_block(&mut self) -> Result<Vec<Statement>, String> {
        let mut stmts: Vec<Statement> = Vec::new();
        while !self.check(&[TokenType::Dedent, TokenType::Trace]) && !self.at_end() {
            self.skip_newlines();
            if self.check(&[TokenType::Dedent, TokenType::Trace]) {
                break;
            }
            stmts.push(self.parse_statement()?);
            self.skip_newlines();
        }
        Ok(stmts)
    }

    fn parse_statement(&mut self) -> Result<Statement, String> {
        if self.check(&[TokenType::Given]) {
            return self.parse_given_stmt();
        }

        if self.check(&[TokenType::Return]) {
            return self.parse_return_stmt();
        }

        if self.check(&[TokenType::If]) {
            return self.parse_if_stmt();
        }

        if self.check(&[TokenType::For]) {
            return self.parse_for_stmt();
        }

        if self.check(&[TokenType::Evaluate]) {
            return self.parse_evaluate_stmt();
        }

        if self.check(&[TokenType::Query]) {
            return self.parse_query_stmt();
        }

        // Expression statement or becomes
        let expr = self.parse_expression()?;

        if self.match_token(&[TokenType::Becomes]).is_some() {
            let value = self.parse_expression()?;
            return Ok(Statement::Become {
                target: expr,
                value,
            });
        }

        Ok(Statement::Expr(expr))
    }

    fn parse_given_stmt(&mut self) -> Result<Statement, String> {
        self.expect(TokenType::Given)?;
        let name = self.expect(TokenType::Identifier)?.value;
        if self.match_token(&[TokenType::As]).is_some() {
            let value = self.parse_expression()?;
            return Ok(Statement::Given {
                name,
                value,
                kind: "as".to_string(),
            });
        }
        self.expect(TokenType::From)?;
        let value = self.parse_expression()?;
        Ok(Statement::Given {
            name,
            value,
            kind: "from".to_string(),
        })
    }

    fn parse_return_stmt(&mut self) -> Result<Statement, String> {
        self.expect(TokenType::Return)?;
        let value = self.parse_expression()?;

        // Constructor: "return approved with rate: ..."
        if self.match_token(&[TokenType::With]).is_some() {
            if let Expression::Identifier(ref ident_name) = value {
                let params = self.parse_action_params()?;
                let constructor = Expression::Constructor {
                    name: ident_name.clone(),
                    fields: params,
                };
                return Ok(Statement::Return(constructor));
            }
        }

        Ok(Statement::Return(value))
    }

    fn parse_if_stmt(&mut self) -> Result<Statement, String> {
        self.expect(TokenType::If)?;
        let condition = self.parse_condition()?;
        self.expect(TokenType::Colon)?;
        self.skip_newlines();
        self.expect(TokenType::Indent)?;
        let body = self.parse_statement_block()?;
        self.expect(TokenType::Dedent)?;

        let mut elif_clauses: Vec<ElifClause> = Vec::new();
        while self.check(&[TokenType::Else]) {
            let saved = self.pos;
            self.advance(); // else
            if self.match_token(&[TokenType::If]).is_some() {
                let elif_cond = self.parse_condition()?;
                self.expect(TokenType::Colon)?;
                self.skip_newlines();
                self.expect(TokenType::Indent)?;
                let elif_body = self.parse_statement_block()?;
                self.expect(TokenType::Dedent)?;
                elif_clauses.push(ElifClause {
                    condition: elif_cond,
                    body: elif_body,
                });
            } else {
                // Plain else — backtrack and break
                self.pos = saved;
                break;
            }
        }

        let else_body = if self.match_token(&[TokenType::Else]).is_some() {
            self.expect(TokenType::Colon)?;
            self.skip_newlines();
            self.expect(TokenType::Indent)?;
            let body = self.parse_statement_block()?;
            self.expect(TokenType::Dedent)?;
            body
        } else {
            Vec::new()
        };

        Ok(Statement::If {
            condition,
            body,
            elif_clauses,
            else_body,
        })
    }

    fn parse_for_stmt(&mut self) -> Result<Statement, String> {
        self.expect(TokenType::For)?;
        self.expect(TokenType::Each)?;
        let variable = self.expect(TokenType::Identifier)?.value;
        self.expect(TokenType::In)?;
        let iterable = self.parse_expression()?;
        self.expect(TokenType::Colon)?;
        self.skip_newlines();
        self.expect(TokenType::Indent)?;
        let body = self.parse_statement_block()?;
        self.expect(TokenType::Dedent)?;
        Ok(Statement::For {
            variable,
            iterable,
            body,
        })
    }

    fn parse_evaluate_stmt(&mut self) -> Result<Statement, String> {
        self.expect(TokenType::Evaluate)?;

        let target = if self.match_token(&[TokenType::All]).is_some() {
            // Skip optional "rules" identifier
            if self.check(&[TokenType::Identifier]) && self.peek_value() == "rules" {
                self.advance();
            }
            "all rules".to_string()
        } else {
            self.expect(TokenType::Identifier)?.value
        };

        self.expect(TokenType::With)?;
        let argument = self.parse_expression()?;
        Ok(Statement::Evaluate { target, argument })
    }

    fn parse_query_stmt(&mut self) -> Result<Statement, String> {
        self.expect(TokenType::Query)?;
        let goal = self.expect(TokenType::Identifier)?.value;
        let argument = if self.match_token(&[TokenType::With]).is_some() {
            Some(self.parse_expression()?)
        } else {
            None
        };
        Ok(Statement::Query { goal, argument })
    }

    // --------------------------------------------------------
    // Expressions (precedence climbing)
    // --------------------------------------------------------

    fn parse_expression(&mut self) -> Result<Expression, String> {
        self.parse_pipeline()
    }

    fn parse_pipeline(&mut self) -> Result<Expression, String> {
        let expr = self.parse_additive()?;

        if !self.check(&[TokenType::Pipe]) {
            return Ok(expr);
        }

        let mut ops: Vec<PipeOp> = Vec::new();
        while self.match_token(&[TokenType::Pipe]).is_some() {
            ops.push(self.parse_pipe_op()?);
        }

        Ok(Expression::Pipeline {
            source: Box::new(expr),
            operations: ops,
        })
    }

    fn parse_pipe_op(&mut self) -> Result<PipeOp, String> {
        if self.check(&[TokenType::Filter]) {
            self.advance();
            self.expect(TokenType::Where)?;
            let condition = self.parse_condition()?;
            return Ok(PipeOp {
                kind: "filter".to_string(),
                args: Vec::new(),
                condition: Some(condition),
                direction: None,
            });
        }

        if self.check(&[TokenType::Sort]) {
            self.advance();
            self.expect(TokenType::By)?;
            let field_expr = self.parse_primary()?;
            let direction = if self.match_token(&[TokenType::Ascending]).is_some() {
                Some("ascending".to_string())
            } else if self.match_token(&[TokenType::Descending]).is_some() {
                Some("descending".to_string())
            } else {
                Some("ascending".to_string())
            };
            return Ok(PipeOp {
                kind: "sort".to_string(),
                args: vec![field_expr],
                condition: None,
                direction,
            });
        }

        if self.check(&[TokenType::Take]) {
            self.advance();
            if self.match_token(&[TokenType::First]).is_some() {
                let count = self.parse_additive()?;
                return Ok(PipeOp {
                    kind: "take_first".to_string(),
                    args: vec![count],
                    condition: None,
                    direction: None,
                });
            }
            if self.match_token(&[TokenType::Last]).is_some() {
                let count = self.parse_additive()?;
                return Ok(PipeOp {
                    kind: "take_last".to_string(),
                    args: vec![count],
                    condition: None,
                    direction: None,
                });
            }
            return Err("Expected 'first' or 'last' after 'take'".to_string());
        }

        if self.check(&[TokenType::Map]) {
            self.advance();
            self.expect(TokenType::To)?;
            let expr = self.parse_additive()?;
            return Ok(PipeOp {
                kind: "map".to_string(),
                args: vec![expr],
                condition: None,
                direction: None,
            });
        }

        let tok = self.current();
        Err(format!(
            "Expected pipeline operation (filter, sort, take, map), got {:?} at line {} col {}",
            tok.token_type, tok.line, tok.column,
        ))
    }

    fn parse_additive(&mut self) -> Result<Expression, String> {
        let mut left = self.parse_multiplicative()?;
        while self.check(&[TokenType::Plus, TokenType::Minus]) {
            let op = self.advance().value;
            let right = self.parse_multiplicative()?;
            left = Expression::BinaryOp {
                left: Box::new(left),
                operator: op,
                right: Box::new(right),
            };
        }
        Ok(left)
    }

    fn parse_multiplicative(&mut self) -> Result<Expression, String> {
        let mut left = self.parse_unary()?;
        while self.check(&[TokenType::Star, TokenType::Slash]) {
            let op = self.advance().value;
            let right = self.parse_unary()?;
            left = Expression::BinaryOp {
                left: Box::new(left),
                operator: op,
                right: Box::new(right),
            };
        }
        Ok(left)
    }

    fn parse_unary(&mut self) -> Result<Expression, String> {
        if self.check(&[TokenType::Minus]) {
            self.advance();
            let operand = self.parse_unary()?;
            return Ok(Expression::UnaryOp {
                operator: "-".to_string(),
                operand: Box::new(operand),
            });
        }
        if self.check(&[TokenType::Not]) {
            self.advance();
            let operand = self.parse_unary()?;
            return Ok(Expression::UnaryOp {
                operator: "not".to_string(),
                operand: Box::new(operand),
            });
        }
        self.parse_postfix()
    }

    fn parse_postfix(&mut self) -> Result<Expression, String> {
        let mut expr = self.parse_primary()?;
        loop {
            if self.match_token(&[TokenType::Dot]).is_some() {
                let field = self.expect(TokenType::Identifier)?.value;
                expr = Expression::FieldAccess {
                    object: Box::new(expr),
                    field,
                };
            } else if self.check(&[TokenType::LParen]) {
                self.advance();
                let mut args: Vec<Expression> = Vec::new();
                if !self.check(&[TokenType::RParen]) {
                    args = self.parse_arg_list()?;
                }
                self.expect(TokenType::RParen)?;
                expr = Expression::FuncCall {
                    function: Box::new(expr),
                    args,
                };
            } else if self.check(&[TokenType::LBracket]) {
                self.advance();
                let index = self.parse_expression()?;
                self.expect(TokenType::RBracket)?;
                expr = Expression::IndexAccess {
                    object: Box::new(expr),
                    index: Box::new(index),
                };
            } else if matches!(&expr, Expression::Identifier(_))
                && self.check(&[TokenType::Identifier])
            {
                // Space-based field access: "reading temperature"
                let field_tok = self.advance();
                expr = Expression::FieldAccess {
                    object: Box::new(expr),
                    field: field_tok.value,
                };
            } else {
                break;
            }
        }
        Ok(expr)
    }

    fn parse_arg_list(&mut self) -> Result<Vec<Expression>, String> {
        let mut args = vec![self.parse_expression()?];
        while self.match_token(&[TokenType::Comma]).is_some() {
            args.push(self.parse_expression()?);
        }
        Ok(args)
    }

    fn parse_primary(&mut self) -> Result<Expression, String> {
        // Number literal
        if self.check(&[TokenType::Number]) {
            let tok = self.advance();
            // Capture optional unit token
            let unit = if self.check(&[TokenType::Unit]) {
                Some(self.advance().value)
            } else {
                None
            };
            let cleaned = tok.value.replace('_', "");
            if cleaned.contains('.') {
                let f: f64 = cleaned
                    .parse()
                    .map_err(|e| format!("Invalid float: {}", e))?;
                return Ok(Expression::Literal {
                    value: LiteralValue::Float(f),
                    kind: "number".to_string(),
                    unit,
                });
            } else {
                let i: i64 = cleaned
                    .parse()
                    .map_err(|e| format!("Invalid integer: {}", e))?;
                return Ok(Expression::Literal {
                    value: LiteralValue::Int(i),
                    kind: "number".to_string(),
                    unit,
                });
            }
        }

        // String literal
        if self.check(&[TokenType::String]) {
            let tok = self.advance();
            return Ok(Expression::Literal {
                value: LiteralValue::Str(tok.value),
                kind: "string".to_string(),
                unit: None,
            });
        }

        // Boolean true
        if self.match_token(&[TokenType::True]).is_some() {
            return Ok(Expression::Literal {
                value: LiteralValue::Bool(true),
                kind: "bool".to_string(),
                unit: None,
            });
        }

        // Boolean false
        if self.match_token(&[TokenType::False]).is_some() {
            return Ok(Expression::Literal {
                value: LiteralValue::Bool(false),
                kind: "bool".to_string(),
                unit: None,
            });
        }

        // None
        if self.match_token(&[TokenType::None_]).is_some() {
            return Ok(Expression::Literal {
                value: LiteralValue::None,
                kind: "none".to_string(),
                unit: None,
            });
        }

        // Symbol
        if self.check(&[TokenType::Symbol]) {
            let tok = self.advance();
            return Ok(Expression::Symbol(tok.value));
        }

        // Empty expression: "empty list", "empty"
        if self.check(&[TokenType::Empty]) {
            self.advance();
            let kind = if self.check(&[TokenType::List]) {
                self.advance();
                "list"
            } else {
                "list"
            };
            return Ok(Expression::Empty {
                kind: kind.to_string(),
            });
        }

        // List literal
        if self.check(&[TokenType::LBracket]) {
            return self.parse_list_literal();
        }

        // Record literal
        if self.check(&[TokenType::LBrace]) {
            return self.parse_record_literal();
        }

        // Parenthesized expression
        if self.match_token(&[TokenType::LParen]).is_some() {
            let expr = self.parse_expression()?;
            self.expect(TokenType::RParen)?;
            return Ok(expr);
        }

        // Match expression
        if self.check(&[TokenType::Match]) {
            return self.parse_match_expr();
        }

        // Lambda: compute from x: Number returns Number: return x + 1
        if self.check(&[TokenType::Compute])
            && matches!(
                self.peek_ahead_type(1),
                TokenType::From | TokenType::Returns | TokenType::Colon
            )
        {
            return self.parse_lambda_expr();
        }

        // Map keyword used as identifier
        if self.check(&[TokenType::Map]) {
            let tok = self.advance();
            return Ok(Expression::Identifier(tok.value));
        }

        // Filter keyword used as identifier
        if self.check(&[TokenType::Filter]) {
            let tok = self.advance();
            return Ok(Expression::Identifier(tok.value));
        }

        // Identifier
        if self.check(&[TokenType::Identifier]) {
            let tok = self.advance();
            return Ok(Expression::Identifier(tok.value));
        }

        // Some keywords can appear as identifiers in certain contexts
        if self.check(&[TokenType::Import, TokenType::Type, TokenType::Module]) {
            let tok = self.advance();
            return Ok(Expression::Identifier(tok.value));
        }

        let tok = self.current();
        Err(format!(
            "Expected expression, got {:?} ({:?}) at line {} col {}",
            tok.token_type, tok.value, tok.line, tok.column,
        ))
    }

    fn skip_whitespace_tokens(&mut self) {
        while self.check(&[TokenType::Newline, TokenType::Indent, TokenType::Dedent]) {
            self.advance();
        }
    }

    fn parse_list_literal(&mut self) -> Result<Expression, String> {
        self.expect(TokenType::LBracket)?;
        let mut elements: Vec<Expression> = Vec::new();

        self.skip_whitespace_tokens();
        if !self.check(&[TokenType::RBracket]) {
            elements.push(self.parse_expression()?);
            while self.match_token(&[TokenType::Comma]).is_some() {
                self.skip_whitespace_tokens();
                if self.check(&[TokenType::RBracket]) {
                    break; // trailing comma
                }
                elements.push(self.parse_expression()?);
            }
            self.skip_whitespace_tokens();
        }

        self.expect(TokenType::RBracket)?;
        Ok(Expression::List(elements))
    }

    fn parse_record_literal(&mut self) -> Result<Expression, String> {
        self.expect(TokenType::LBrace)?;
        let mut fields: Vec<RecordFieldExpr> = Vec::new();

        if !self.check(&[TokenType::RBrace]) {
            let name = self.expect(TokenType::Identifier)?.value;
            self.expect(TokenType::Colon)?;
            let value = self.parse_expression()?;
            fields.push(RecordFieldExpr { name, value });

            while self.match_token(&[TokenType::Comma]).is_some() {
                let name = self.expect(TokenType::Identifier)?.value;
                self.expect(TokenType::Colon)?;
                let value = self.parse_expression()?;
                fields.push(RecordFieldExpr { name, value });
            }
        }

        self.expect(TokenType::RBrace)?;
        Ok(Expression::Record(fields))
    }

    fn parse_match_expr(&mut self) -> Result<Expression, String> {
        self.expect(TokenType::Match)?;
        let subject = self.parse_expression()?;
        self.expect(TokenType::Colon)?;
        self.skip_newlines();
        self.expect(TokenType::Indent)?;

        let mut arms: Vec<MatchArm> = Vec::new();
        while !self.check(&[TokenType::Dedent]) && !self.at_end() {
            self.skip_newlines();
            if self.check(&[TokenType::Dedent]) {
                break;
            }
            let pattern = self.parse_primary()?;
            self.expect(TokenType::Arrow)?;
            let body = self.parse_expression()?;
            arms.push(MatchArm { pattern, body });
            self.skip_newlines();
        }

        self.expect(TokenType::Dedent)?;
        Ok(Expression::Match {
            subject: Box::new(subject),
            arms,
        })
    }

    fn parse_lambda_expr(&mut self) -> Result<Expression, String> {
        self.expect(TokenType::Compute)?;

        let mut params: Vec<Param> = Vec::new();
        if self.match_token(&[TokenType::From]).is_some() {
            params = self.parse_param_list()?;
        }

        let return_type = if self.match_token(&[TokenType::Returns]).is_some() {
            Some(self.parse_type_ref()?)
        } else {
            None
        };

        self.expect(TokenType::Colon)?;

        // Check if body is indented block or inline expression
        let body = if self.check(&[TokenType::Newline]) {
            self.skip_newlines();
            self.expect(TokenType::Indent)?;
            let stmts = self.parse_statement_block()?;
            self.expect(TokenType::Dedent)?;
            stmts
        } else {
            // Single expression body (inline)
            let body_expr = if self.match_token(&[TokenType::Return]).is_some() {
                self.parse_expression()?
            } else {
                self.parse_expression()?
            };
            vec![Statement::Return(body_expr)]
        };

        Ok(Expression::Lambda {
            params,
            return_type,
            body,
        })
    }
}

// ============================================================
// Tests
// ============================================================

#[cfg(test)]
mod parser_tests {
    use super::*;
    use crate::lexer::tokens::{Token, TokenType};

    /// Helper: build a minimal token stream with EOF.
    fn tokens(toks: Vec<Token>) -> Vec<Token> {
        let mut v = toks;
        v.push(Token::new(TokenType::Eof, "", 999, 0));
        v
    }

    fn tok(tt: TokenType, val: &str, line: usize) -> Token {
        Token::new(tt, val, line, 0)
    }

    #[test]
    fn test_parse_empty_program() {
        let result = parse(tokens(vec![]));
        assert!(result.is_ok());
        let prog = result.unwrap();
        assert!(prog.module.is_none());
        assert!(prog.imports.is_empty());
        assert!(prog.declarations.is_empty());
    }

    #[test]
    fn test_parse_module_decl() {
        let result = parse(tokens(vec![
            tok(TokenType::Module, "module", 1),
            tok(TokenType::Identifier, "my_module", 1),
            tok(TokenType::Newline, "\n", 1),
        ]));
        assert!(result.is_ok());
        let prog = result.unwrap();
        assert_eq!(prog.module.unwrap().path, "my_module");
    }

    #[test]
    fn test_parse_dotted_module() {
        let result = parse(tokens(vec![
            tok(TokenType::Module, "module", 1),
            tok(TokenType::Identifier, "sigil", 1),
            tok(TokenType::Dot, ".", 1),
            tok(TokenType::Identifier, "math", 1),
            tok(TokenType::Newline, "\n", 1),
        ]));
        assert!(result.is_ok());
        assert_eq!(result.unwrap().module.unwrap().path, "sigil.math");
    }

    #[test]
    fn test_parse_import() {
        let result = parse(tokens(vec![
            tok(TokenType::Import, "import", 1),
            tok(TokenType::Identifier, "sigil", 1),
            tok(TokenType::Dot, ".", 1),
            tok(TokenType::Identifier, "math", 1),
            tok(TokenType::Newline, "\n", 1),
        ]));
        assert!(result.is_ok());
        let prog = result.unwrap();
        assert_eq!(prog.imports.len(), 1);
        assert_eq!(prog.imports[0].source, "sigil.math");
        assert_eq!(prog.imports[0].kind, "sigil");
    }

    #[test]
    fn test_parse_const_decl() {
        let result = parse(tokens(vec![
            tok(TokenType::Define, "define", 1),
            tok(TokenType::Identifier, "MAX_TEMP", 1),
            tok(TokenType::As, "as", 1),
            tok(TokenType::Number, "100", 1),
            tok(TokenType::Newline, "\n", 1),
        ]));
        assert!(result.is_ok());
        let prog = result.unwrap();
        assert_eq!(prog.declarations.len(), 1);
    }

    #[test]
    fn test_parse_error_recovery() {
        // Unknown token at top level, followed by a valid define
        let result = parse(tokens(vec![
            tok(TokenType::Number, "42", 1),
            tok(TokenType::Newline, "\n", 1),
            tok(TokenType::Define, "define", 2),
            tok(TokenType::Identifier, "X", 2),
            tok(TokenType::As, "as", 2),
            tok(TokenType::Number, "1", 2),
            tok(TokenType::Newline, "\n", 2),
        ]));
        // Should produce an error (collected via synchronize)
        assert!(result.is_err());
    }
}
