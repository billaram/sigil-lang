"""Sigil recursive descent parser.

Converts a token stream into an AST. Hand-written for maximum control,
clarity, and debuggability.
"""

from __future__ import annotations

from sigil.ast import nodes as ast
from sigil.errors import SigilParseError, SourceLocation
from sigil.lexer.tokens import Token, TokenType


def parse(tokens: list[Token], filename: str = "<stdin>") -> ast.Program:
    """Parse a list of tokens into a Program AST node."""
    parser = Parser(tokens, filename)
    return parser.parse_program()


class Parser:
    """Recursive descent parser for Sigil."""

    def __init__(self, tokens: list[Token], filename: str = "<stdin>") -> None:
        self.tokens = tokens
        self.filename = filename
        self.pos = 0

    # --- Token access ---

    def _current(self) -> Token:
        if self.pos >= len(self.tokens):
            return self.tokens[-1]  # EOF
        return self.tokens[self.pos]

    def _peek(self) -> TokenType:
        return self._current().type

    def _peek_value(self) -> str:
        return self._current().value

    def _at_end(self) -> bool:
        return self._peek() == TokenType.EOF

    def _advance(self) -> Token:
        tok = self._current()
        if not self._at_end():
            self.pos += 1
        return tok

    def _expect(self, token_type: TokenType) -> Token:
        if self._peek() != token_type:
            tok = self._current()
            raise self._error(
                f"Expected {token_type.name}, got {tok.type.name} ({tok.value!r})"
            )
        return self._advance()

    def _match(self, *types: TokenType) -> Token | None:
        if self._peek() in types:
            return self._advance()
        return None

    def _check(self, *types: TokenType) -> bool:
        return self._peek() in types

    def _loc(self) -> SourceLocation:
        tok = self._current()
        return SourceLocation(self.filename, tok.line, tok.column)

    def _error(self, message: str) -> SigilParseError:
        return SigilParseError(message, self._loc())

    # --- Skip newlines ---

    def _skip_newlines(self) -> None:
        while self._match(TokenType.NEWLINE):
            pass

    # --- Top-level parsing ---

    def parse_program(self) -> ast.Program:
        loc = self._loc()
        self._skip_newlines()

        module = None
        if self._check(TokenType.MODULE):
            module = self._parse_module_decl()

        imports: list[ast.ImportDecl] = []
        declarations: list[ast.Declaration] = []

        while not self._at_end():
            self._skip_newlines()
            if self._at_end():
                break

            match self._peek():
                case TokenType.IMPORT:
                    imports.append(self._parse_import_decl())
                case TokenType.FROM:
                    imports.append(self._parse_from_import())
                case TokenType.TYPE:
                    declarations.append(self._parse_type_decl())
                case TokenType.DEFINE:
                    declarations.append(self._parse_const_decl())
                case TokenType.RULE:
                    declarations.append(self._parse_rule_decl())
                case TokenType.COMPUTE:
                    declarations.append(self._parse_compute_decl())
                case TokenType.NEURAL:
                    declarations.append(self._parse_neural_decl())
                case TokenType.MAIN:
                    declarations.append(self._parse_main_decl())
                case TokenType.EXPORT:
                    declarations.append(self._parse_export_decl())
                case TokenType.DOC_COMMENT:
                    self._advance()  # skip doc comments for now
                case _:
                    raise self._error(
                        f"Unexpected token at top level: {self._current().type.name}"
                    )

        return ast.Program(
            location=loc,
            module=module,
            imports=tuple(imports),
            declarations=tuple(declarations),
        )

    # --- Module declaration ---

    def _parse_module_decl(self) -> ast.ModuleDecl:
        loc = self._loc()
        self._expect(TokenType.MODULE)
        path = self._parse_dotted_name()
        self._skip_newlines()
        return ast.ModuleDecl(location=loc, path=path)

    def _parse_dotted_name(self) -> str:
        parts = [self._expect_identifier_or_keyword().value]
        while self._match(TokenType.DOT):
            parts.append(self._expect_identifier_or_keyword().value)
        return ".".join(parts)

    def _expect_identifier_or_keyword(self) -> Token:
        """Accept an IDENTIFIER or a keyword token as a name (for module paths)."""
        tok = self._current()
        if self._peek() == TokenType.IDENTIFIER:
            return self._expect(TokenType.IDENTIFIER)
        # Keywords that are valid as module path segments
        keyword_types = {
            TokenType.LIST, TokenType.MATCH, TokenType.TYPE, TokenType.RULE,
            TokenType.IMPORT, TokenType.EXPORT, TokenType.MODULE,
        }
        if self._peek() in keyword_types:
            self._advance()
            return tok
        raise self._error(
            f"Expected identifier, got {tok.type.name} ({tok.value!r})"
        )

    # --- Import declarations ---

    def _parse_import_decl(self) -> ast.ImportDecl:
        loc = self._loc()
        self._expect(TokenType.IMPORT)

        kind = "sigil"
        if self._match(TokenType.PYTHON):
            kind = "python"
        elif self._match(TokenType.RUST):
            kind = "rust"

        source = self._parse_rust_path() if kind == "rust" else self._parse_dotted_name()

        alias = None
        if self._match(TokenType.AS):
            alias = self._expect(TokenType.IDENTIFIER).value

        self._skip_newlines()
        return ast.ImportDecl(location=loc, source=source, kind=kind, alias=alias)

    def _parse_from_import(self) -> ast.ImportDecl:
        loc = self._loc()
        self._expect(TokenType.FROM)

        kind = "sigil"
        if self._match(TokenType.PYTHON):
            kind = "python"
        elif self._match(TokenType.RUST):
            kind = "rust"

        source = self._parse_dotted_name()
        self._expect(TokenType.IMPORT)

        names = [self._expect(TokenType.IDENTIFIER).value]
        while self._match(TokenType.COMMA):
            names.append(self._expect(TokenType.IDENTIFIER).value)

        self._skip_newlines()
        return ast.ImportDecl(
            location=loc, source=source, kind=kind, names=tuple(names)
        )

    def _parse_export_decl(self) -> ast.ExportDecl:
        loc = self._loc()
        self._expect(TokenType.EXPORT)
        names = [self._expect(TokenType.IDENTIFIER).value]
        while self._match(TokenType.COMMA):
            names.append(self._expect(TokenType.IDENTIFIER).value)
        self._skip_newlines()
        return ast.ExportDecl(location=loc, names=tuple(names))

    def _parse_rust_path(self) -> str:
        parts = [self._expect(TokenType.IDENTIFIER).value]
        while self._match(TokenType.DOUBLE_COLON):
            parts.append(self._expect(TokenType.IDENTIFIER).value)
        return "::".join(parts)

    # --- Type declarations ---

    def _parse_type_decl(self) -> ast.TypeDecl:
        loc = self._loc()
        self._expect(TokenType.TYPE)
        name = self._expect(TokenType.IDENTIFIER).value

        params: tuple[str, ...] = ()
        if self._match(TokenType.LBRACKET):
            param_list = [self._expect(TokenType.IDENTIFIER).value]
            while self._match(TokenType.COMMA):
                param_list.append(self._expect(TokenType.IDENTIFIER).value)
            self._expect(TokenType.RBRACKET)
            params = tuple(param_list)

        self._expect(TokenType.IS)
        body = self._parse_type_body(loc)
        self._skip_newlines()
        return ast.TypeDecl(location=loc, name=name, params=params, body=body)

    def _parse_type_body(self, parent_loc: SourceLocation) -> ast.TypeBody:
        if self._check(TokenType.RECORD):
            return self._parse_record_body()
        if self._check(TokenType.ONE):
            return self._parse_enum_body()
        # Check for unit type: "Number with unit degrees"
        type_ref = self._parse_type_ref()
        if self._check(TokenType.WITH):
            self._advance()
            self._expect(TokenType.IDENTIFIER)  # "unit"
            unit = self._expect(TokenType.IDENTIFIER).value
            return ast.UnitType(location=parent_loc, base_type=type_ref, unit=unit)
        # Check for constrained type (for now treat as alias)
        return ast.AliasType(location=parent_loc, target=type_ref)

    def _parse_record_body(self) -> ast.RecordBody:
        loc = self._loc()
        self._expect(TokenType.RECORD)
        self._expect(TokenType.COLON)
        self._skip_newlines()
        self._expect(TokenType.INDENT)

        fields: list[ast.FieldDef] = []
        while not self._check(TokenType.DEDENT) and not self._at_end():
            self._skip_newlines()
            if self._check(TokenType.DEDENT):
                break
            fields.append(self._parse_field_def())
            self._skip_newlines()

        self._expect(TokenType.DEDENT)
        return ast.RecordBody(location=loc, fields=tuple(fields))

    def _parse_field_def(self) -> ast.FieldDef:
        loc = self._loc()
        name = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.COLON)
        type_ref = self._parse_type_ref()
        return ast.FieldDef(location=loc, name=name, type_ref=type_ref)

    def _parse_enum_body(self) -> ast.EnumBody:
        loc = self._loc()
        self._expect(TokenType.ONE)
        self._expect(TokenType.OF)
        self._expect(TokenType.COLON)
        self._skip_newlines()
        self._expect(TokenType.INDENT)

        variants: list[ast.EnumVariant] = []
        while not self._check(TokenType.DEDENT) and not self._at_end():
            self._skip_newlines()
            if self._check(TokenType.DEDENT):
                break
            variants.append(self._parse_enum_variant())
            self._skip_newlines()

        self._expect(TokenType.DEDENT)
        return ast.EnumBody(location=loc, variants=tuple(variants))

    def _parse_enum_variant(self) -> ast.EnumVariant:
        loc = self._loc()
        name = self._expect(TokenType.IDENTIFIER).value
        fields: list[ast.FieldDef] = []
        if self._match(TokenType.WITH):
            fields.append(self._parse_field_def())
            while self._match(TokenType.COMMA):
                fields.append(self._parse_field_def())
        return ast.EnumVariant(location=loc, name=name, fields=tuple(fields))

    def _parse_type_ref(self) -> ast.TypeRef:
        """Parse a type reference like Number, Text, list of X, Option[X]."""
        loc = self._loc()

        if self._check(TokenType.LIST):
            self._advance()
            self._expect(TokenType.OF)
            element = self._parse_type_ref()
            return ast.ListType(location=loc, element_type=element)

        if self._check(TokenType.OPTION):
            self._advance()
            self._expect(TokenType.LBRACKET)
            inner = self._parse_type_ref()
            self._expect(TokenType.RBRACKET)
            return ast.OptionType(location=loc, inner_type=inner)

        if self._check(TokenType.RECORD):
            # Inline record type
            return self._parse_inline_record_type()

        name = self._expect(TokenType.IDENTIFIER).value
        params: list[ast.TypeRef] = []
        if self._match(TokenType.LBRACKET):
            params.append(self._parse_type_ref())
            while self._match(TokenType.COMMA):
                params.append(self._parse_type_ref())
            self._expect(TokenType.RBRACKET)

        return ast.NamedType(location=loc, name=name, params=tuple(params))

    def _parse_inline_record_type(self) -> ast.InlineRecordType:
        loc = self._loc()
        self._expect(TokenType.RECORD)
        self._expect(TokenType.COLON)
        self._skip_newlines()
        self._expect(TokenType.INDENT)

        fields: list[ast.FieldDef] = []
        while not self._check(TokenType.DEDENT) and not self._at_end():
            self._skip_newlines()
            if self._check(TokenType.DEDENT):
                break
            fields.append(self._parse_field_def())
            self._skip_newlines()

        self._expect(TokenType.DEDENT)
        return ast.InlineRecordType(location=loc, fields=tuple(fields))

    # --- Constant declarations ---

    def _parse_const_decl(self) -> ast.ConstDecl:
        loc = self._loc()
        self._expect(TokenType.DEFINE)
        name = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.AS)
        value = self._parse_expression()
        self._skip_newlines()
        return ast.ConstDecl(location=loc, name=name, value=value)

    # --- Rule declarations ---

    def _parse_rule_decl(self) -> ast.RuleDecl:
        loc = self._loc()
        self._expect(TokenType.RULE)
        name = self._expect(TokenType.IDENTIFIER).value

        priority = 0
        if self._match(TokenType.WITH):
            self._expect(TokenType.PRIORITY)
            priority = int(self._expect(TokenType.NUMBER).value)

        self._expect(TokenType.COLON)
        self._skip_newlines()
        self._expect(TokenType.INDENT)

        # Parse rule body: optional metadata, optional given, when/and/or, then, explain, trace
        metadata: list[ast.MetaField] = []
        given_clauses: list[ast.GivenClause] = []

        # Metadata fields (version, author, tags)
        while self._check(TokenType.IDENTIFIER) and self._peek_value() in (
            "version", "author", "tags"
        ):
            meta_loc = self._loc()
            meta_name = self._advance().value
            meta_value = self._parse_expression()
            metadata.append(ast.MetaField(location=meta_loc, name=meta_name, value=meta_value))
            self._skip_newlines()

        # Given clauses
        while self._check(TokenType.GIVEN):
            given_clauses.append(self._parse_given_clause())
            self._skip_newlines()

        # When + conditions
        self._expect(TokenType.WHEN)
        conditions = [self._parse_condition()]
        self._skip_newlines()

        # And/Or conditions
        while self._check(TokenType.AND, TokenType.OR):
            op_tok = self._advance()
            negate = bool(self._match(TokenType.NOT))
            cond = self._parse_condition()
            if negate:
                cond = ast.NotCond(location=cond.location, condition=cond)
            # Wrap in compound condition
            conditions.append(cond)
            conditions[-1] = ast.CompoundCond(
                location=SourceLocation(
                    self.filename, op_tok.line, op_tok.column
                ),
                operator=op_tok.value,
                left=conditions[-2] if len(conditions) > 1 else conditions[0],
                right=conditions[-1],
            )
            # Replace the two conditions with the compound one
            if len(conditions) > 1:
                compound = conditions.pop()
                conditions.pop()
                conditions.append(compound)
            self._skip_newlines()

        # Then action
        self._expect(TokenType.THEN)
        action = self._parse_action()
        self._skip_newlines()

        # Explain
        explain = None
        if self._match(TokenType.EXPLAIN):
            explain = self._expect(TokenType.STRING).value
            self._skip_newlines()

        # Trace
        trace: list[ast.TraceField] = []
        if self._check(TokenType.TRACE):
            trace = self._parse_trace_block()
            self._skip_newlines()

        self._expect(TokenType.DEDENT)

        return ast.RuleDecl(
            location=loc,
            name=name,
            priority=priority,
            metadata=tuple(metadata),
            given_clauses=tuple(given_clauses),
            conditions=tuple(conditions),
            action=action,
            explain=explain,
            trace=tuple(trace),
        )

    def _parse_given_clause(self) -> ast.GivenClause:
        loc = self._loc()
        self._expect(TokenType.GIVEN)
        name = self._expect(TokenType.IDENTIFIER).value
        if self._match(TokenType.AS):
            value = self._parse_expression()
            return ast.GivenClause(location=loc, name=name, source=value, kind="as")
        self._expect(TokenType.FROM)
        value = self._parse_expression()
        return ast.GivenClause(location=loc, name=name, source=value, kind="from")

    def _parse_trace_block(self) -> list[ast.TraceField]:
        self._expect(TokenType.TRACE)
        self._expect(TokenType.COLON)
        self._skip_newlines()
        self._expect(TokenType.INDENT)

        fields: list[ast.TraceField] = []
        while not self._check(TokenType.DEDENT) and not self._at_end():
            self._skip_newlines()
            if self._check(TokenType.DEDENT):
                break
            field_loc = self._loc()
            name = self._expect(TokenType.IDENTIFIER).value
            value = self._parse_expression()
            fields.append(ast.TraceField(location=field_loc, name=name, value=value))
            self._skip_newlines()

        self._expect(TokenType.DEDENT)
        return fields

    # --- Conditions ---

    def _parse_condition(self) -> ast.Condition:
        """Parse a condition (comparison, membership, quantifier, etc.)."""
        loc = self._loc()

        # Quantified: any/all/none X in Y has/have Z
        if self._check(TokenType.ANY, TokenType.ALL, TokenType.NONE_):
            return self._parse_quantified_condition()

        # Parse left-hand expression (use _parse_additive to avoid consuming |>)
        left = self._parse_additive()

        # Now determine the condition type based on what follows
        if self._check(TokenType.EXCEEDS):
            self._advance()
            right = self._parse_additive()
            return ast.ComparisonCond(
                location=loc, left=left, operator="exceeds", right=right
            )

        if self._check(TokenType.EQUALS):
            self._advance()
            right = self._parse_additive()
            return ast.ComparisonCond(
                location=loc, left=left, operator="equals", right=right
            )

        if self._check(TokenType.IS):
            return self._parse_is_condition(loc, left)

        if self._check(TokenType.IN):
            self._advance()
            collection = self._parse_additive()
            return ast.MembershipCond(
                location=loc, element=left, collection=collection
            )

        if self._check(TokenType.NOT) and self._peek_ahead_type(1) == TokenType.IN:
            self._advance()  # not
            self._advance()  # in
            collection = self._parse_additive()
            return ast.MembershipCond(
                location=loc, element=left, collection=collection, negated=True
            )

        if self._check(TokenType.CONTAINS):
            self._advance()
            element = self._parse_additive()
            return ast.ContainsCond(
                location=loc, collection=left, element=element
            )

        if self._check(TokenType.STARTS):
            self._advance()
            self._expect(TokenType.WITH)
            pattern = self._parse_additive()
            return ast.StringCond(
                location=loc, string=left, operator="starts with", pattern=pattern
            )

        if self._check(TokenType.ENDS):
            self._advance()
            self._expect(TokenType.WITH)
            pattern = self._parse_additive()
            return ast.StringCond(
                location=loc, string=left, operator="ends with", pattern=pattern
            )

        if self._check(TokenType.MATCHES):
            self._advance()
            self._expect(TokenType.PATTERN)
            pattern = self._parse_additive()
            return ast.StringCond(
                location=loc, string=left, operator="matches pattern", pattern=pattern
            )

        if self._check(TokenType.HAS):
            self._advance()
            if self._match(TokenType.COUNT):
                count = self._parse_additive()
                return ast.HasCountCond(
                    location=loc, collection=left, count=count
                )

        # Comparison operators
        if self._check(TokenType.GT, TokenType.LT, TokenType.GTE,
                        TokenType.LTE, TokenType.EQ, TokenType.NEQ):
            op = self._advance().value
            right = self._parse_additive()
            return ast.ComparisonCond(
                location=loc, left=left, operator=op, right=right
            )

        # If nothing matched, treat the expression itself as a boolean condition
        return ast.BooleanCond(location=loc, expression=left, value=True)

    def _parse_is_condition(
        self, loc: SourceLocation, left: ast.Expression
    ) -> ast.Condition:
        """Parse conditions starting with 'is': is X, is below, is between, etc."""
        self._expect(TokenType.IS)

        # is not ...
        if self._check(TokenType.NOT):
            self._advance()
            if self._check(TokenType.TRUE):
                self._advance()
                return ast.BooleanCond(location=loc, expression=left, value=False)
            if self._check(TokenType.ASSIGNED):
                self._advance()
                return ast.IsAssignedCond(location=loc, expression=left, negated=True)
            if self._check(TokenType.EMPTY):
                self._advance()
                return ast.IsEmptyCond(location=loc, expression=left, negated=True)
            if self._check(TokenType.IN):
                self._advance()
                collection = self._parse_additive()
                return ast.MembershipCond(
                    location=loc, element=left, collection=collection, negated=True
                )
            # "is not <value>"
            right = self._parse_additive()
            return ast.ComparisonCond(
                location=loc, left=left, operator="is not", right=right
            )

        # is below
        if self._check(TokenType.BELOW):
            self._advance()
            right = self._parse_additive()
            return ast.ComparisonCond(
                location=loc, left=left, operator="is below", right=right
            )

        # is between X and Y
        if self._check(TokenType.BETWEEN):
            self._advance()
            low = self._parse_additive()
            self._expect(TokenType.AND)
            high = self._parse_additive()
            return ast.ComparisonCond(
                location=loc, left=left, operator="is between",
                right=low, right2=high,
            )

        # is at least / is at most
        if self._check(TokenType.AT):
            self._advance()
            if self._match(TokenType.LEAST):
                right = self._parse_additive()
                return ast.ComparisonCond(
                    location=loc, left=left, operator="is at least", right=right
                )
            if self._match(TokenType.MOST):
                right = self._parse_additive()
                return ast.ComparisonCond(
                    location=loc, left=left, operator="is at most", right=right
                )

        # is empty
        if self._check(TokenType.EMPTY):
            self._advance()
            return ast.IsEmptyCond(location=loc, expression=left)

        # is true / is false
        if self._check(TokenType.TRUE):
            self._advance()
            return ast.BooleanCond(location=loc, expression=left, value=True)
        if self._check(TokenType.FALSE):
            self._advance()
            return ast.BooleanCond(location=loc, expression=left, value=False)

        # is in
        if self._check(TokenType.IN):
            self._advance()
            collection = self._parse_additive()
            return ast.MembershipCond(
                location=loc, element=left, collection=collection
            )

        # is <value> (equality comparison)
        right = self._parse_additive()
        return ast.ComparisonCond(
            location=loc, left=left, operator="is", right=right
        )

    def _parse_quantified_condition(self) -> ast.QuantifiedCond:
        loc = self._loc()
        quantifier = self._advance().value  # any, all, none

        variable = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.IN)
        collection = self._parse_additive()

        # Accept has/have as explicit bridge, or parse condition directly
        # (e.g. "any symptom in X is in Y" where condition starts with "is")
        self._match(TokenType.HAS, TokenType.HAVE)

        # Build a condition with the variable as implicit left-hand side
        var_expr = ast.Identifier(
            location=SourceLocation(self.filename, loc.line, loc.column),
            name=variable,
        )
        condition = self._parse_condition_with_left(var_expr)
        return ast.QuantifiedCond(
            location=loc,
            quantifier=quantifier,
            variable=variable,
            collection=collection,
            condition=condition,
        )

    def _parse_condition_with_left(self, left: ast.Expression) -> ast.Condition:
        """Parse a condition where the left-hand expression is already known."""
        loc = SourceLocation(self.filename, left.location.line, left.location.column)

        if self._check(TokenType.EXCEEDS):
            self._advance()
            right = self._parse_additive()
            return ast.ComparisonCond(location=loc, left=left, operator="exceeds", right=right)

        if self._check(TokenType.IS):
            return self._parse_is_condition(loc, left)

        if self._check(TokenType.IN):
            self._advance()
            collection = self._parse_additive()
            return ast.MembershipCond(location=loc, element=left, collection=collection)

        # Fallback: parse a full condition
        return self._parse_condition()

    def _expect_any(self, *types: TokenType) -> Token:
        if self._peek() in types:
            return self._advance()
        names = " or ".join(t.name for t in types)
        raise self._error(f"Expected {names}, got {self._current().type.name}")

    def _peek_ahead_type(self, offset: int) -> TokenType:
        pos = self.pos + offset
        if pos >= len(self.tokens):
            return TokenType.EOF
        return self.tokens[pos].type

    # --- Actions ---

    def _parse_action(self) -> ast.SimpleAction | ast.SetAction | ast.BlockAction:
        """Parse the action after 'then'."""
        loc = self._loc()

        # Block action: then: (with NEWLINE + INDENT)
        if self._check(TokenType.COLON):
            return self._parse_block_action(loc)

        # Simple or set action
        # Try to parse as: name [target] [is value | with params]
        name_tok = self._advance()
        name = name_tok.value

        # Check for "X is Y" (set action)
        if self._check(TokenType.IS):
            self._advance()
            # Could be "X is <constructor> with ..." or "X is <value>"
            value = self._parse_action_value()
            target_id = ast.Identifier(
                location=SourceLocation(self.filename, name_tok.line, name_tok.column),
                name=name,
            )
            return ast.SetAction(location=loc, target=target_id, value=value)

        target: str | None = None
        # Check if next is an identifier (e.g. "trigger alert", "log status")
        if self._check(TokenType.IDENTIFIER):
            # Peek further: if followed by "with" or "is" or newline, it's a target
            target = name
            name_tok2 = self._advance()
            name = name_tok2.value

            # Now check for "is" (set action with dotted target like "risk is block")
            if self._check(TokenType.IS):
                self._advance()
                value = self._parse_action_value()
                assert target is not None
                target_expr = ast.FieldAccess(
                    location=SourceLocation(
                        self.filename, name_tok.line, name_tok.column
                    ),
                    object=ast.Identifier(
                        location=SourceLocation(
                            self.filename, name_tok.line, name_tok.column
                        ),
                        name=target,
                    ),
                    field=name,
                )
                return ast.SetAction(location=loc, target=target_expr, value=value)

        params: list[ast.ActionParam] = []
        if self._match(TokenType.WITH):
            params = self._parse_action_params()
        elif not self._check(
            TokenType.NEWLINE, TokenType.EXPLAIN, TokenType.TRACE,
            TokenType.DEDENT, TokenType.EOF, TokenType.AND, TokenType.OR,
        ):
            # Positional argument without "with": e.g. "log status :normal"
            value = self._parse_expression()
            params.append(ast.ActionParam(
                location=value.location, name=name, value=value
            ))

        return ast.SimpleAction(
            location=loc, name=name if target else name, target=target,
            params=tuple(params),
        )

    def _parse_action_value(self) -> ast.Expression:
        """Parse value in set action: could be expression or constructor."""
        loc = self._loc()
        expr = self._parse_expression()

        # Check for constructor: "block with reason: ..."
        if self._match(TokenType.WITH) and isinstance(expr, ast.Identifier):  # noqa: SIM102
            params = self._parse_action_params()
            return ast.ConstructorExpr(
                location=loc, name=expr.name, fields=tuple(params)
            )
        return expr

    def _parse_action_params(self) -> list[ast.ActionParam]:
        params: list[ast.ActionParam] = []
        param_loc = self._loc()
        name = self._expect(TokenType.IDENTIFIER).value
        self._match(TokenType.COLON)  # colon is optional (e.g. "severity :high")
        value = self._parse_expression()
        params.append(ast.ActionParam(location=param_loc, name=name, value=value))
        while self._match(TokenType.COMMA):
            param_loc = self._loc()
            name = self._expect(TokenType.IDENTIFIER).value
            self._match(TokenType.COLON)
            value = self._parse_expression()
            params.append(ast.ActionParam(location=param_loc, name=name, value=value))
        return params

    def _parse_block_action(self, loc: SourceLocation) -> ast.BlockAction:
        self._expect(TokenType.COLON)
        self._skip_newlines()
        self._expect(TokenType.INDENT)
        body = self._parse_statement_block()
        self._expect(TokenType.DEDENT)
        return ast.BlockAction(location=loc, body=tuple(body))

    # --- Compute declarations ---

    def _parse_compute_decl(self) -> ast.ComputeDecl:
        loc = self._loc()
        self._expect(TokenType.COMPUTE)
        name = self._expect(TokenType.IDENTIFIER).value

        params: list[ast.Param] = []
        if self._match(TokenType.FROM):
            params = self._parse_param_list()

        return_type = None
        if self._match(TokenType.RETURNS):
            return_type = self._parse_type_ref()

        self._expect(TokenType.COLON)
        self._skip_newlines()
        self._expect(TokenType.INDENT)
        body = self._parse_statement_block()
        self._expect(TokenType.DEDENT)
        self._skip_newlines()

        return ast.ComputeDecl(
            location=loc, name=name, params=tuple(params),
            body=tuple(body), return_type=return_type,
        )

    def _parse_param_list(self) -> list[ast.Param]:
        params = [self._parse_param()]
        while self._match(TokenType.COMMA):
            params.append(self._parse_param())
        return params

    def _parse_param(self) -> ast.Param:
        loc = self._loc()
        name = self._expect(TokenType.IDENTIFIER).value
        type_ref = None
        if self._match(TokenType.COLON):
            type_ref = self._parse_type_ref()
        return ast.Param(location=loc, name=name, type_ref=type_ref)

    # --- Neural declarations ---

    def _parse_neural_decl(self) -> ast.NeuralDecl:
        loc = self._loc()
        self._expect(TokenType.NEURAL)
        name = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.FROM)
        param_name = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.COLON)
        param_type = self._parse_type_ref()
        self._expect(TokenType.COLON)
        self._skip_newlines()
        self._expect(TokenType.INDENT)

        fields: list[ast.NeuralField] = []
        while not self._check(TokenType.DEDENT) and not self._at_end():
            self._skip_newlines()
            if self._check(TokenType.DEDENT):
                break
            fields.append(self._parse_neural_field())
            self._skip_newlines()

        self._expect(TokenType.DEDENT)
        self._skip_newlines()
        return ast.NeuralDecl(
            location=loc, name=name, param_name=param_name,
            param_type=param_type, fields=tuple(fields),
        )

    def _parse_neural_field(self) -> ast.NeuralField:
        loc = self._loc()
        tok = self._current()

        if self._match(TokenType.IDENTIFIER):
            # "model", "confidence_threshold", "threshold", "candidates"
            name = tok.value
            value = self._parse_expression()
            return ast.NeuralField(location=loc, name=name, value=value)

        if self._match(TokenType.RETURNS):
            type_ref = self._parse_type_ref()
            return ast.NeuralField(location=loc, name="returns", value=type_ref)

        if self._match(TokenType.USING):
            self._expect(TokenType.PYTHON)
            path = self._parse_dotted_name()
            return ast.NeuralField(
                location=loc, name="using",
                value=ast.Identifier(location=loc, name=path),
            )

        if self._match(TokenType.FALLBACK):
            self._expect(TokenType.TO)
            value = self._parse_expression()
            return ast.NeuralField(location=loc, name="fallback", value=value)

        raise self._error(f"Unexpected token in neural block: {tok.type.name}")

    # --- Main declaration ---

    def _parse_main_decl(self) -> ast.MainDecl:
        loc = self._loc()
        self._expect(TokenType.MAIN)
        self._expect(TokenType.COLON)
        self._skip_newlines()
        self._expect(TokenType.INDENT)

        body = self._parse_statement_block()

        # Optional trace block at end of main
        trace: list[ast.TraceField] = []
        if self._check(TokenType.TRACE):
            trace = self._parse_trace_block()
            self._skip_newlines()

        self._expect(TokenType.DEDENT)
        self._skip_newlines()
        return ast.MainDecl(location=loc, body=tuple(body), trace=tuple(trace))

    # --- Statements ---

    def _parse_statement_block(self) -> list[ast.Statement]:
        stmts: list[ast.Statement] = []
        while not self._check(TokenType.DEDENT, TokenType.TRACE) and not self._at_end():
            self._skip_newlines()
            if self._check(TokenType.DEDENT, TokenType.TRACE):
                break
            stmts.append(self._parse_statement())
            self._skip_newlines()
        return stmts

    def _parse_statement(self) -> ast.Statement:
        loc = self._loc()

        if self._check(TokenType.GIVEN):
            return self._parse_given_stmt()

        if self._check(TokenType.RETURN):
            return self._parse_return_stmt()

        if self._check(TokenType.IF):
            return self._parse_if_stmt()

        if self._check(TokenType.FOR):
            return self._parse_for_stmt()

        if self._check(TokenType.EVALUATE):
            return self._parse_evaluate_stmt()

        # Expression statement or becomes statement
        expr = self._parse_expression()

        if self._match(TokenType.BECOMES):
            value = self._parse_expression()
            return ast.BecomeStmt(location=loc, target=expr, value=value)

        return ast.ExprStmt(location=loc, expression=expr)

    def _parse_given_stmt(self) -> ast.GivenStmt:
        loc = self._loc()
        self._expect(TokenType.GIVEN)
        name = self._expect(TokenType.IDENTIFIER).value
        if self._match(TokenType.AS):
            value = self._parse_expression()
            return ast.GivenStmt(location=loc, name=name, value=value, kind="as")
        self._expect(TokenType.FROM)
        value = self._parse_expression()
        return ast.GivenStmt(location=loc, name=name, value=value, kind="from")

    def _parse_return_stmt(self) -> ast.ReturnStmt:
        loc = self._loc()
        self._expect(TokenType.RETURN)
        value = self._parse_expression()

        # Check for constructor: "return approved with rate: ..."
        if self._match(TokenType.WITH) and isinstance(value, ast.Identifier):  # noqa: SIM102
            params = self._parse_action_params()
            value = ast.ConstructorExpr(
                location=value.location, name=value.name, fields=tuple(params)
            )

        return ast.ReturnStmt(location=loc, value=value)

    def _parse_if_stmt(self) -> ast.IfStmt:
        loc = self._loc()
        self._expect(TokenType.IF)
        condition = self._parse_condition()
        self._expect(TokenType.COLON)
        self._skip_newlines()
        self._expect(TokenType.INDENT)
        body = self._parse_statement_block()
        self._expect(TokenType.DEDENT)

        elif_clauses: list[ast.ElifClause] = []
        while self._check(TokenType.ELSE):
            # Check for "else if"
            saved = self.pos
            self._advance()  # else
            if self._match(TokenType.IF):
                elif_loc = self._loc()
                elif_cond = self._parse_condition()
                self._expect(TokenType.COLON)
                self._skip_newlines()
                self._expect(TokenType.INDENT)
                elif_body = self._parse_statement_block()
                self._expect(TokenType.DEDENT)
                elif_clauses.append(ast.ElifClause(
                    location=elif_loc, condition=elif_cond, body=tuple(elif_body)
                ))
            else:
                # Plain else
                self.pos = saved
                break

        else_body: list[ast.Statement] = []
        if self._match(TokenType.ELSE):
            self._expect(TokenType.COLON)
            self._skip_newlines()
            self._expect(TokenType.INDENT)
            else_body = self._parse_statement_block()
            self._expect(TokenType.DEDENT)

        return ast.IfStmt(
            location=loc, condition=condition, body=tuple(body),
            elif_clauses=tuple(elif_clauses), else_body=tuple(else_body),
        )

    def _parse_for_stmt(self) -> ast.ForStmt:
        loc = self._loc()
        self._expect(TokenType.FOR)
        self._expect(TokenType.EACH)
        variable = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.IN)
        iterable = self._parse_expression()
        self._expect(TokenType.COLON)
        self._skip_newlines()
        self._expect(TokenType.INDENT)
        body = self._parse_statement_block()
        self._expect(TokenType.DEDENT)
        return ast.ForStmt(
            location=loc, variable=variable, iterable=iterable, body=tuple(body)
        )

    def _parse_evaluate_stmt(self) -> ast.EvaluateStmt:
        loc = self._loc()
        self._expect(TokenType.EVALUATE)

        if self._match(TokenType.ALL):
            # "evaluate all rules with ..."
            # Skip 'rules' if it's there (it's an identifier, not keyword)
            if self._check(TokenType.IDENTIFIER) and self._peek_value() == "rules":
                self._advance()
            target = "all rules"
        else:
            target = self._expect(TokenType.IDENTIFIER).value

        self._expect(TokenType.WITH)
        argument = self._parse_expression()
        return ast.EvaluateStmt(location=loc, target=target, argument=argument)

    # --- Expressions (precedence climbing) ---

    def _parse_expression(self) -> ast.Expression:
        return self._parse_pipeline()

    def _parse_pipeline(self) -> ast.Expression:
        """Parse pipeline expressions: expr |> op |> op ..."""
        expr = self._parse_additive()

        if not self._check(TokenType.PIPE):
            return expr

        ops: list[ast.PipeOp] = []
        while self._match(TokenType.PIPE):
            op = self._parse_pipe_op()
            ops.append(op)

        return ast.PipelineExpr(
            location=expr.location,
            source=expr,
            operations=tuple(ops),
        )

    def _parse_pipe_op(self) -> ast.PipeOp:
        """Parse a single pipeline operation after |>."""
        loc = self._loc()

        if self._check(TokenType.FILTER):
            self._advance()
            self._expect(TokenType.WHERE)
            condition = self._parse_condition()
            return ast.PipeOp(location=loc, kind="filter", condition=condition)

        if self._check(TokenType.SORT):
            self._advance()
            self._expect(TokenType.BY)
            field_expr = self._parse_primary()
            direction = "ascending"
            if self._match(TokenType.ASCENDING):
                direction = "ascending"
            elif self._match(TokenType.DESCENDING):
                direction = "descending"
            return ast.PipeOp(
                location=loc, kind="sort", args=(field_expr,), direction=direction,
            )

        if self._check(TokenType.TAKE):
            self._advance()
            if self._match(TokenType.FIRST):
                count = self._parse_additive()
                return ast.PipeOp(location=loc, kind="take_first", args=(count,))
            if self._match(TokenType.LAST):
                count = self._parse_additive()
                return ast.PipeOp(location=loc, kind="take_last", args=(count,))
            raise self._error("Expected 'first' or 'last' after 'take'")

        if self._check(TokenType.MAP):
            self._advance()
            self._expect(TokenType.TO)
            expr = self._parse_additive()
            return ast.PipeOp(location=loc, kind="map", args=(expr,))

        raise self._error(
            f"Expected pipeline operation (filter, sort, take, map), "
            f"got {self._current().type.name}"
        )

    def _parse_additive(self) -> ast.Expression:
        left = self._parse_multiplicative()
        while self._check(TokenType.PLUS, TokenType.MINUS):
            loc = self._loc()
            op = self._advance().value
            right = self._parse_multiplicative()
            left = ast.BinaryOp(location=loc, left=left, operator=op, right=right)
        return left

    def _parse_multiplicative(self) -> ast.Expression:
        left = self._parse_unary()
        while self._check(TokenType.STAR, TokenType.SLASH):
            loc = self._loc()
            op = self._advance().value
            right = self._parse_unary()
            left = ast.BinaryOp(location=loc, left=left, operator=op, right=right)
        return left

    def _parse_unary(self) -> ast.Expression:
        if self._check(TokenType.MINUS):
            loc = self._loc()
            self._advance()
            operand = self._parse_unary()
            return ast.UnaryOp(location=loc, operator="-", operand=operand)
        if self._check(TokenType.NOT):
            loc = self._loc()
            self._advance()
            operand = self._parse_unary()
            return ast.UnaryOp(location=loc, operator="not", operand=operand)
        return self._parse_postfix()

    def _parse_postfix(self) -> ast.Expression:
        expr = self._parse_primary()
        while True:
            if self._match(TokenType.DOT):
                field = self._expect(TokenType.IDENTIFIER).value
                expr = ast.FieldAccess(location=expr.location, object=expr, field=field)
            elif self._check(TokenType.LPAREN):
                self._advance()
                args: list[ast.Expression] = []
                named: list[ast.NamedArg] = []
                if not self._check(TokenType.RPAREN):
                    args, named = self._parse_arg_list()
                self._expect(TokenType.RPAREN)
                expr = ast.FuncCall(
                    location=expr.location, function=expr,
                    args=tuple(args), named_args=tuple(named),
                )
            elif self._check(TokenType.LBRACKET):
                self._advance()
                index = self._parse_expression()
                self._expect(TokenType.RBRACKET)
                expr = ast.IndexAccess(location=expr.location, object=expr, index=index)
            elif (isinstance(expr, ast.Identifier)
                  and self._check(TokenType.IDENTIFIER)):
                # Space-based field access: "reading temperature" → reading.temperature
                field_tok = self._advance()
                expr = ast.FieldAccess(
                    location=expr.location, object=expr, field=field_tok.value
                )
            else:
                break
        return expr

    def _parse_arg_list(self) -> tuple[list[ast.Expression], list[ast.NamedArg]]:
        args: list[ast.Expression] = []
        named: list[ast.NamedArg] = []

        # First arg — check if named
        first = self._parse_expression()
        if isinstance(first, ast.Identifier) and self._match(TokenType.COLON):
            val = self._parse_expression()
            named.append(ast.NamedArg(location=first.location, name=first.name, value=val))
            while self._match(TokenType.COMMA):
                name_tok = self._expect(TokenType.IDENTIFIER)
                self._expect(TokenType.COLON)
                val = self._parse_expression()
                named.append(ast.NamedArg(
                    location=SourceLocation(self.filename, name_tok.line, name_tok.column),
                    name=name_tok.value, value=val,
                ))
        else:
            args.append(first)
            while self._match(TokenType.COMMA):
                args.append(self._parse_expression())

        return args, named

    def _parse_primary(self) -> ast.Expression:
        loc = self._loc()

        # Number literal
        if self._check(TokenType.NUMBER):
            tok = self._advance()
            value = tok.value
            # Skip unit token if present (already lexed as separate token)
            if self._match(TokenType.UNIT):
                pass  # Unit info is in the following UNIT token; we keep it simple
            if "." in value:
                return ast.Literal(location=loc, value=float(value.replace("_", "")), kind="number")
            return ast.Literal(location=loc, value=int(value.replace("_", "")), kind="number")

        # String literal
        if self._check(TokenType.STRING):
            tok = self._advance()
            return ast.Literal(location=loc, value=tok.value, kind="string")

        # Boolean
        if self._match(TokenType.TRUE):
            return ast.Literal(location=loc, value=True, kind="bool")
        if self._match(TokenType.FALSE):
            return ast.Literal(location=loc, value=False, kind="bool")

        # None
        if self._match(TokenType.NONE_):
            return ast.Literal(location=loc, value=None, kind="none")

        # Symbol
        if self._check(TokenType.SYMBOL):
            tok = self._advance()
            return ast.SymbolLit(location=loc, name=tok.value)

        # Empty expression: "empty list", "empty"
        if self._check(TokenType.EMPTY):
            self._advance()
            kind = "list"
            if self._check(TokenType.LIST):
                self._advance()
            return ast.EmptyExpr(location=loc, kind=kind)

        # List literal
        if self._check(TokenType.LBRACKET):
            return self._parse_list_literal()

        # Record literal
        if self._check(TokenType.LBRACE):
            return self._parse_record_literal()

        # Parenthesized expression
        if self._match(TokenType.LPAREN):
            expr = self._parse_expression()
            self._expect(TokenType.RPAREN)
            return expr

        # Match expression
        if self._check(TokenType.MATCH):
            return self._parse_match_expr()

        # Lambda expression: compute from x: Number returns Number: return x + 1
        # Also: compute from: expr (no params)
        if self._check(TokenType.COMPUTE) and self._peek_ahead_type(1) in (
            TokenType.FROM, TokenType.RETURNS, TokenType.COLON,
        ):
            return self._parse_lambda_expr()

        # Map keyword used as identifier in certain contexts
        if self._check(TokenType.MAP):
            tok = self._advance()
            return ast.Identifier(location=loc, name=tok.value)

        # Filter keyword used as identifier
        if self._check(TokenType.FILTER):
            tok = self._advance()
            return ast.Identifier(location=loc, name=tok.value)

        # Identifier
        if self._check(TokenType.IDENTIFIER):
            tok = self._advance()
            return ast.Identifier(location=loc, name=tok.value)

        # Some keywords can appear as identifiers in certain contexts
        if self._check(TokenType.IDENTIFIER, TokenType.IMPORT, TokenType.TYPE,
                        TokenType.MODULE):
            tok = self._advance()
            return ast.Identifier(location=loc, name=tok.value)

        raise self._error(
            f"Expected expression, got {self._current().type.name} ({self._current().value!r})"
        )

    def _skip_whitespace_tokens(self) -> None:
        """Skip NEWLINE, INDENT, and DEDENT tokens (for multi-line literals)."""
        while self._check(TokenType.NEWLINE, TokenType.INDENT, TokenType.DEDENT):
            self._advance()

    def _parse_list_literal(self) -> ast.ListExpr:
        loc = self._loc()
        self._expect(TokenType.LBRACKET)
        elements: list[ast.Expression] = []

        self._skip_whitespace_tokens()
        if not self._check(TokenType.RBRACKET):
            elements.append(self._parse_expression())
            while self._match(TokenType.COMMA):
                self._skip_whitespace_tokens()
                if self._check(TokenType.RBRACKET):
                    break  # trailing comma
                elements.append(self._parse_expression())
            self._skip_whitespace_tokens()

        self._expect(TokenType.RBRACKET)
        return ast.ListExpr(location=loc, elements=tuple(elements))

    def _parse_record_literal(self) -> ast.RecordExpr:
        loc = self._loc()
        self._expect(TokenType.LBRACE)
        fields: list[ast.RecordFieldExpr] = []

        if not self._check(TokenType.RBRACE):
            field_loc = self._loc()
            name = self._expect(TokenType.IDENTIFIER).value
            self._expect(TokenType.COLON)
            value = self._parse_expression()
            fields.append(ast.RecordFieldExpr(location=field_loc, name=name, value=value))
            while self._match(TokenType.COMMA):
                field_loc = self._loc()
                name = self._expect(TokenType.IDENTIFIER).value
                self._expect(TokenType.COLON)
                value = self._parse_expression()
                fields.append(ast.RecordFieldExpr(location=field_loc, name=name, value=value))

        self._expect(TokenType.RBRACE)
        return ast.RecordExpr(location=loc, fields=tuple(fields))

    def _parse_match_expr(self) -> ast.MatchExpr:
        loc = self._loc()
        self._expect(TokenType.MATCH)
        subject = self._parse_expression()
        self._expect(TokenType.COLON)
        self._skip_newlines()
        self._expect(TokenType.INDENT)

        arms: list[ast.MatchArm] = []
        while not self._check(TokenType.DEDENT) and not self._at_end():
            self._skip_newlines()
            if self._check(TokenType.DEDENT):
                break
            arm_loc = self._loc()
            pattern = self._parse_primary()
            self._expect(TokenType.ARROW)
            body = self._parse_expression()
            arms.append(ast.MatchArm(location=arm_loc, pattern=pattern, body=body))
            self._skip_newlines()

        self._expect(TokenType.DEDENT)
        return ast.MatchExpr(location=loc, subject=subject, arms=tuple(arms))

    def _parse_lambda_expr(self) -> ast.LambdaExpr:
        """Parse an inline anonymous compute expression.

        Syntax: compute from x: Number returns Number: return x + 1
        """
        loc = self._loc()
        self._expect(TokenType.COMPUTE)

        params: list[ast.Param] = []
        if self._match(TokenType.FROM):
            params = self._parse_param_list()

        return_type = None
        if self._match(TokenType.RETURNS):
            return_type = self._parse_type_ref()

        self._expect(TokenType.COLON)

        # Check if body is indented block or inline expression
        if self._check(TokenType.NEWLINE):
            self._skip_newlines()
            self._expect(TokenType.INDENT)
            body = tuple(self._parse_statement_block())
            self._expect(TokenType.DEDENT)
        else:
            # Single expression body (inline): "return x + 1"
            if self._match(TokenType.RETURN):
                body_expr = self._parse_expression()
            else:
                body_expr = self._parse_expression()
            body = (ast.ReturnStmt(location=loc, value=body_expr),)

        return ast.LambdaExpr(
            location=loc,
            params=tuple(params),
            return_type=return_type,
            body=body,
        )
