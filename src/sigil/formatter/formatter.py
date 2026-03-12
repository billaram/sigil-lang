"""AST → source code formatter for Sigil programs."""

from __future__ import annotations

from sigil.ast import nodes as ast


def format_program(program: ast.Program) -> str:
    """Format an AST back to well-formatted Sigil source code."""
    f = _Formatter()
    return f.format(program)


class _Formatter:
    """Stateful formatter that walks the AST and emits source text."""

    def __init__(self) -> None:
        self._lines: list[str] = []
        self._indent = 0

    def format(self, program: ast.Program) -> str:
        if program.module:
            self._line(f"module {program.module.path}")
            self._blank()

        for imp in program.imports:
            self._format_import(imp)
        if program.imports:
            self._blank()

        first = True
        for decl in program.declarations:
            if not first:
                self._blank()
            self._format_declaration(decl)
            first = False

        # Ensure trailing newline
        text = "\n".join(self._lines)
        if text and not text.endswith("\n"):
            text += "\n"
        return text

    # --- Helpers ---

    def _line(self, text: str) -> None:
        self._lines.append("  " * self._indent + text)

    def _blank(self) -> None:
        self._lines.append("")

    def _push(self) -> None:
        self._indent += 1

    def _pop(self) -> None:
        self._indent -= 1

    # --- Imports ---

    def _format_import(self, imp: ast.ImportDecl) -> None:
        if imp.names:
            names = ", ".join(imp.names)
            if imp.kind == "sigil":
                self._line(f"from {imp.source} import {names}")
            else:
                self._line(
                    f"from {imp.kind} {imp.source} import {names}",
                )
        elif imp.alias:
            if imp.kind == "sigil":
                self._line(f"import {imp.source} as {imp.alias}")
            else:
                self._line(
                    f"import {imp.kind} {imp.source} as {imp.alias}",
                )
        elif imp.kind == "sigil":
            self._line(f"import {imp.source}")
        else:
            self._line(f"import {imp.kind} {imp.source}")

    # --- Declarations ---

    def _format_declaration(self, decl: ast.Declaration) -> None:
        if isinstance(decl, ast.ConstDecl):
            self._format_const(decl)
        elif isinstance(decl, ast.TypeDecl):
            self._format_type(decl)
        elif isinstance(decl, ast.RuleDecl):
            self._format_rule(decl)
        elif isinstance(decl, ast.ComputeDecl):
            self._format_compute(decl)
        elif isinstance(decl, ast.NeuralDecl):
            self._format_neural(decl)
        elif isinstance(decl, ast.MainDecl):
            self._format_main(decl)
        elif isinstance(decl, ast.ExportDecl):
            self._format_export(decl)

    def _format_const(self, decl: ast.ConstDecl) -> None:
        self._line(f"define {decl.name} as {self._expr(decl.value)}")

    def _format_export(self, decl: ast.ExportDecl) -> None:
        self._line(f"export {', '.join(decl.names)}")

    def _format_type(self, decl: ast.TypeDecl) -> None:
        if isinstance(decl.body, ast.RecordBody):
            self._line(f"type {decl.name} is record:")
            self._push()
            for field in decl.body.fields:
                self._line(
                    f"{field.name}: {self._type_ref(field.type_ref)}",
                )
            self._pop()
        elif isinstance(decl.body, ast.EnumBody):
            self._line(f"type {decl.name} is enum:")
            self._push()
            for variant in decl.body.variants:
                if variant.fields:
                    fields = ", ".join(
                        f"{f.name}: {self._type_ref(f.type_ref)}"
                        for f in variant.fields
                    )
                    self._line(f"{variant.name} with {fields}")
                else:
                    self._line(variant.name)
            self._pop()
        elif isinstance(decl.body, ast.AliasType):
            self._line(
                f"type {decl.name} is"
                f" {self._type_ref(decl.body.target)}",
            )

    def _format_rule(self, decl: ast.RuleDecl) -> None:
        header = f"rule {decl.name}"
        if decl.priority:
            header += f" with priority {decl.priority}"
        header += ":"
        self._line(header)
        self._push()

        for gc in decl.given_clauses:
            self._line(
                f"given {gc.name} {gc.kind} {self._expr(gc.source)}",
            )

        for i, cond in enumerate(decl.conditions):
            prefix = "when " if i == 0 else "and "
            self._line(prefix + self._condition(cond))

        self._format_action(decl.action)

        if decl.explain:
            self._line(f'explain "{decl.explain}"')

        if decl.temporal:
            unit = decl.temporal.unit
            dur = self._expr(decl.temporal.duration)
            self._line(f"within {dur} {unit}")

        for tf in decl.trace:
            self._line(f"trace {tf.name} {self._expr(tf.value)}")

        self._pop()

    def _format_action(self, action: ast.Action) -> None:
        if isinstance(action, ast.SetAction):
            target = self._expr(action.target)
            value = self._expr(action.value)
            self._line(f"then {target} is {value}")
        elif isinstance(action, ast.SimpleAction):
            parts = ["then", action.name]
            if action.target:
                parts.append(action.target)
            for p in action.params:
                parts.append(f"with {p.name} {self._expr(p.value)}")
            self._line(" ".join(parts))
        elif isinstance(action, ast.BlockAction):
            self._line("then:")
            self._push()
            for stmt in action.body:
                self._format_statement(stmt)
            self._pop()

    def _format_compute(self, decl: ast.ComputeDecl) -> None:
        params = ", ".join(self._param(p) for p in decl.params)
        header = f"compute {decl.name}"
        if params:
            header += f" from {params}"
        if decl.return_type:
            header += f" returns {self._type_ref(decl.return_type)}"
        header += ":"
        self._line(header)
        self._push()
        for stmt in decl.body:
            self._format_statement(stmt)
        self._pop()

    def _format_neural(self, decl: ast.NeuralDecl) -> None:
        ptype = self._type_ref(decl.param_type)
        self._line(
            f"neural {decl.name} from"
            f" {decl.param_name}: {ptype}:",
        )
        self._push()
        for field in decl.fields:
            self._format_neural_field(field)
        self._pop()

    def _format_neural_field(self, field: ast.NeuralField) -> None:
        if field.name == "fallback":
            self._line(f"fallback to {self._expr_or_type(field.value)}")
        elif field.name == "returns":
            self._line(f"returns {self._type_ref(field.value)}")
        else:
            self._line(
                f"{field.name} {self._expr_or_type(field.value)}",
            )

    def _format_main(self, decl: ast.MainDecl) -> None:
        self._line("main:")
        self._push()
        for stmt in decl.body:
            self._format_statement(stmt)
        self._pop()

    # --- Statements ---

    def _format_statement(self, stmt: ast.Statement) -> None:
        if isinstance(stmt, ast.GivenStmt):
            self._line(
                f"given {stmt.name} {stmt.kind}"
                f" {self._expr(stmt.value)}",
            )
        elif isinstance(stmt, ast.ReturnStmt):
            self._line(f"return {self._expr(stmt.value)}")
        elif isinstance(stmt, ast.IfStmt):
            self._format_if(stmt)
        elif isinstance(stmt, ast.ForStmt):
            self._line(
                f"for each {stmt.variable}"
                f" in {self._expr(stmt.iterable)}:",
            )
            self._push()
            for s in stmt.body:
                self._format_statement(s)
            self._pop()
        elif isinstance(stmt, ast.ExprStmt):
            self._line(self._expr(stmt.expression))
        elif isinstance(stmt, ast.EvaluateStmt):
            self._line(
                f"evaluate {stmt.target}"
                f" {self._expr(stmt.argument)}",
            )
        elif isinstance(stmt, ast.BecomeStmt):
            self._line(
                f"{self._expr(stmt.target)} becomes"
                f" {self._expr(stmt.value)}",
            )
        elif isinstance(stmt, ast.QueryStmt):
            if stmt.argument:
                self._line(
                    f"query {stmt.goal}"
                    f" with {self._expr(stmt.argument)}",
                )
            else:
                self._line(f"query {stmt.goal}")

    def _format_if(self, stmt: ast.IfStmt) -> None:
        self._line(f"if {self._condition(stmt.condition)}:")
        self._push()
        for s in stmt.body:
            self._format_statement(s)
        self._pop()
        for elif_clause in stmt.elif_clauses:
            self._line(
                f"else if {self._condition(elif_clause.condition)}:",
            )
            self._push()
            for s in elif_clause.body:
                self._format_statement(s)
            self._pop()
        if stmt.else_body:
            self._line("else:")
            self._push()
            for s in stmt.else_body:
                self._format_statement(s)
            self._pop()

    # --- Conditions ---

    def _condition(self, cond: ast.Condition) -> str:
        if isinstance(cond, ast.ComparisonCond):
            left = self._expr(cond.left)
            right = self._expr(cond.right)
            if cond.right2:
                right2 = self._expr(cond.right2)
                return f"{left} {cond.operator} {right} and {right2}"
            return f"{left} {cond.operator} {right}"
        if isinstance(cond, ast.MembershipCond):
            elem = self._expr(cond.element)
            coll = self._expr(cond.collection)
            op = "not in" if cond.negated else "in"
            return f"{elem} {op} {coll}"
        if isinstance(cond, ast.BooleanCond):
            expr = self._expr(cond.expression)
            val = "true" if cond.value else "false"
            return f"{expr} is {val}"
        if isinstance(cond, ast.NotCond):
            return f"not {self._condition(cond.condition)}"
        if isinstance(cond, ast.CompoundCond):
            left = self._condition(cond.left)
            right = self._condition(cond.right)
            return f"{left} {cond.operator} {right}"
        if isinstance(cond, ast.IsAssignedCond):
            expr = self._expr(cond.expression)
            neg = " not" if cond.negated else ""
            return f"{expr} is{neg} assigned"
        if isinstance(cond, ast.IsEmptyCond):
            expr = self._expr(cond.expression)
            neg = " not" if cond.negated else ""
            return f"{expr} is{neg} empty"
        if isinstance(cond, ast.ContainsCond):
            coll = self._expr(cond.collection)
            elem = self._expr(cond.element)
            return f"{coll} contains {elem}"
        if isinstance(cond, ast.HasCountCond):
            coll = self._expr(cond.collection)
            count = self._expr(cond.count)
            return f"{coll} has count {count}"
        if isinstance(cond, ast.StringCond):
            s = self._expr(cond.string)
            p = self._expr(cond.pattern)
            return f"{s} {cond.operator} {p}"
        if isinstance(cond, ast.QuantifiedCond):
            coll = self._expr(cond.collection)
            inner = self._condition(cond.condition)
            return (
                f"{cond.quantifier} {cond.variable}"
                f" in {coll}: {inner}"
            )
        return "<unknown-condition>"

    # --- Expressions ---

    def _expr(self, expr: ast.Expression | object) -> str:
        if isinstance(expr, ast.Literal):
            return self._literal(expr)
        if isinstance(expr, ast.SymbolLit):
            return f":{expr.name}"
        if isinstance(expr, ast.Identifier):
            return expr.name
        if isinstance(expr, ast.BinaryOp):
            left = self._expr(expr.left)
            right = self._expr(expr.right)
            return f"{left} {expr.operator} {right}"
        if isinstance(expr, ast.UnaryOp):
            operand = self._expr(expr.operand)
            if expr.operator == "-":
                return f"-{operand}"
            return f"{expr.operator} {operand}"
        if isinstance(expr, ast.FieldAccess):
            obj = self._expr(expr.object)
            return f"{obj}.{expr.field}"
        if isinstance(expr, ast.FuncCall):
            func = self._expr(expr.function)
            args = ", ".join(self._expr(a) for a in expr.args)
            named = ", ".join(
                f"{na.name}: {self._expr(na.value)}"
                for na in expr.named_args
            )
            all_args = ", ".join(
                filter(None, [args, named]),
            )
            return f"{func}({all_args})"
        if isinstance(expr, ast.IndexAccess):
            obj = self._expr(expr.object)
            idx = self._expr(expr.index)
            return f"{obj}[{idx}]"
        if isinstance(expr, ast.ListExpr):
            elems = ", ".join(self._expr(e) for e in expr.elements)
            return f"[{elems}]"
        if isinstance(expr, ast.RecordExpr):
            fields = ", ".join(
                f"{f.name}: {self._expr(f.value)}"
                for f in expr.fields
            )
            return "{" + fields + "}"
        if isinstance(expr, ast.MatchExpr):
            return self._match_expr(expr)
        if isinstance(expr, ast.PipelineExpr):
            return self._pipeline_expr(expr)
        if isinstance(expr, ast.LambdaExpr):
            return self._lambda_expr(expr)
        if isinstance(expr, ast.ConstructorExpr):
            if expr.fields:
                fields = ", ".join(
                    f"{f.name}: {self._expr(f.value)}"
                    for f in expr.fields
                )
                return f"{expr.name} with {fields}"
            return expr.name
        if isinstance(expr, ast.EmptyExpr):
            return f"empty {expr.kind}"
        return str(expr)

    def _literal(self, lit: ast.Literal) -> str:
        if lit.kind == "string":
            escaped = str(lit.value).replace('"', '\\"')
            s = f'"{escaped}"'
        elif lit.kind == "bool":
            s = "true" if lit.value else "false"
        elif lit.kind == "none":
            s = "none"
        elif isinstance(lit.value, float) and lit.value == int(lit.value):
            s = f"{lit.value:.1f}"
        else:
            s = str(lit.value)
        if lit.unit:
            s += f" {lit.unit}"
        return s

    def _match_expr(self, expr: ast.MatchExpr) -> str:
        subject = self._expr(expr.subject)
        arms = ", ".join(
            f"when {self._expr(a.pattern)} then {self._expr(a.body)}"
            for a in expr.arms
        )
        return f"match {subject}: {arms}"

    def _pipeline_expr(self, expr: ast.PipelineExpr) -> str:
        source = self._expr(expr.source)
        ops = []
        for op in expr.operations:
            if op.condition:
                ops.append(f"|> {op.kind} {self._condition(op.condition)}")
            elif op.args:
                args = ", ".join(self._expr(a) for a in op.args)
                ops.append(f"|> {op.kind} {args}")
            else:
                part = f"|> {op.kind}"
                if op.direction:
                    part += f" {op.direction}"
                ops.append(part)
        return source + " " + " ".join(ops)

    def _lambda_expr(self, expr: ast.LambdaExpr) -> str:
        params = ", ".join(self._param(p) for p in expr.params)
        # Simple single-return lambda
        if (
            len(expr.body) == 1
            and isinstance(expr.body[0], ast.ReturnStmt)
        ):
            body = self._expr(expr.body[0].value)
            return f"({params}) => {body}"
        return f"({params}) => ..."

    # --- Type references ---

    def _type_ref(self, ref: object) -> str:
        if isinstance(ref, ast.NamedType):
            if ref.params:
                params = ", ".join(
                    self._type_ref(p) for p in ref.params
                )
                return f"{ref.name}[{params}]"
            return ref.name
        if isinstance(ref, ast.ListType):
            return f"list of {self._type_ref(ref.element_type)}"
        if isinstance(ref, ast.OptionType):
            return f"Option[{self._type_ref(ref.inner_type)}]"
        if isinstance(ref, ast.InlineRecordType):
            fields = ", ".join(
                f"{f.name}: {self._type_ref(f.type_ref)}"
                for f in ref.fields
            )
            return "{" + fields + "}"
        return str(ref)

    def _expr_or_type(self, val: object) -> str:
        if isinstance(val, ast.TypeRef):
            return self._type_ref(val)
        return self._expr(val)

    def _param(self, p: ast.Param) -> str:
        if p.type_ref:
            return f"{p.name}: {self._type_ref(p.type_ref)}"
        return p.name
