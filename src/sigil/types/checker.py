"""Basic type checker for Sigil — static analysis on the AST.

Two-phase single pass:
  Phase 1: Scan declarations, build symbol table, collect settable names
  Phase 2: Walk bodies checking for errors
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from sigil.ast import nodes as ast
from sigil.errors import SourceLocation


class Severity(Enum):
    ERROR = auto()
    WARNING = auto()


@dataclass(frozen=True)
class Diagnostic:
    """A single type-check diagnostic."""

    location: SourceLocation
    severity: Severity
    message: str
    suggestion: str | None = None


@dataclass
class CheckResult:
    """Result of type-checking a program."""

    diagnostics: list[Diagnostic] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(d.severity == Severity.ERROR for d in self.diagnostics)

    @property
    def error_count(self) -> int:
        return sum(1 for d in self.diagnostics if d.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for d in self.diagnostics if d.severity == Severity.WARNING)


# Names that are always in scope
_BUILTIN_NAMES = {"print", "max", "min", "len", "true", "false", "input", "empty"}

# Built-in function arities
_BUILTIN_ARITIES: dict[str, int] = {
    "print": 1,
    "max": 2,
    "min": 2,
    "len": 1,
    "math.max": 2,
    "math.min": 2,
    "math.len": 1,
}

# Numeric comparison operators
_NUMERIC_OPS = frozenset({
    "exceeds", "is below", "is between", "is at least", "is at most",
})


class TypeChecker:
    """Two-phase type checker for Sigil programs."""

    def __init__(self) -> None:
        self._diagnostics: list[Diagnostic] = []
        self._declared_names: dict[str, SourceLocation] = {}
        self._record_fields: dict[str, set[str]] = {}
        self._compute_arity: dict[str, int] = {}
        self._compute_return_types: dict[str, str] = {}
        self._neural_arity: dict[str, int] = {}
        self._settable_names: set[str] = set()
        self._field_access_bases: set[str] = set()
        self._const_units: dict[str, str] = {}  # name → unit suffix from define
        # Track referenced names for unused-declaration warnings
        self._referenced_names: set[str] = set()
        # Track declaration kinds for targeted warnings
        self._compute_names: dict[str, SourceLocation] = {}
        self._rule_names: dict[str, SourceLocation] = {}
        self._const_names: dict[str, SourceLocation] = {}

    def check(self, program: ast.Program) -> CheckResult:
        """Type-check a program and return diagnostics."""
        self._phase1_scan(program)
        self._phase2_walk(program)
        return CheckResult(self._diagnostics)

    def _error(
        self, loc: SourceLocation, message: str, suggestion: str | None = None,
    ) -> None:
        self._diagnostics.append(Diagnostic(loc, Severity.ERROR, message, suggestion))

    def _warning(
        self, loc: SourceLocation, message: str, suggestion: str | None = None,
    ) -> None:
        self._diagnostics.append(Diagnostic(loc, Severity.WARNING, message, suggestion))

    # ----------------------------------------------------------------
    # Phase 1: Scan declarations
    # ----------------------------------------------------------------

    def _phase1_scan(self, program: ast.Program) -> None:
        for decl in program.declarations:
            self._register_decl(decl)
        # Collect settable names and field-access bases from entire AST
        self._collect_from_ast(program)

    def _register_decl(self, decl: ast.Declaration) -> None:
        if isinstance(decl, ast.TypeDecl):
            self._register_name(decl.name, decl.location)
            if isinstance(decl.body, ast.RecordBody):
                self._record_fields[decl.name] = {f.name for f in decl.body.fields}
            elif isinstance(decl.body, ast.EnumBody):
                for variant in decl.body.variants:
                    self._register_name(variant.name, variant.location)
        elif isinstance(decl, ast.ConstDecl):
            self._register_name(decl.name, decl.location)
            self._const_names[decl.name] = decl.location
        elif isinstance(decl, ast.RuleDecl):
            self._register_name(decl.name, decl.location)
            self._rule_names[decl.name] = decl.location
        elif isinstance(decl, ast.ComputeDecl):
            self._register_name(decl.name, decl.location)
            self._compute_arity[decl.name] = len(decl.params)
            self._compute_names[decl.name] = decl.location
            if decl.return_type and isinstance(decl.return_type, ast.NamedType):
                self._compute_return_types[decl.name] = decl.return_type.name
        elif isinstance(decl, ast.NeuralDecl):
            self._register_name(decl.name, decl.location)
            self._neural_arity[decl.name] = 1

    def _register_name(self, name: str, location: SourceLocation) -> None:
        if name in self._declared_names:
            prev = self._declared_names[name]
            self._error(
                location,
                f"Duplicate declaration: '{name}' already declared at line {prev.line}",
            )
        else:
            self._declared_names[name] = location

    def _collect_from_ast(self, node: object) -> None:
        """Walk entire AST collecting settable names, field-access bases, units, and refs."""
        if (
            isinstance(node, ast.ConstDecl)
            and isinstance(node.value, ast.Literal)
            and node.value.unit
        ):
            self._const_units[node.name] = node.value.unit
        if isinstance(node, ast.SetAction) and isinstance(node.target, ast.Identifier):
            self._settable_names.add(node.target.name)
        elif isinstance(node, (ast.GivenStmt, ast.GivenClause)):
            self._settable_names.add(node.name)
        elif isinstance(node, ast.BecomeStmt) and isinstance(node.target, ast.Identifier):
            self._settable_names.add(node.target.name)
        elif isinstance(node, (ast.ForStmt, ast.QuantifiedCond)):
            self._settable_names.add(node.variable)

        if isinstance(node, ast.FieldAccess):
            base = self._get_fa_base(node)
            if base:
                self._field_access_bases.add(base)

        # Track identifier references (for unused-declaration detection)
        if isinstance(node, ast.Identifier):
            self._referenced_names.add(node.name)
        elif isinstance(node, ast.FuncCall) and isinstance(
            node.function, ast.Identifier,
        ):
            self._referenced_names.add(node.function.name)

        # Recurse into dataclass fields
        if hasattr(node, "__dataclass_fields__"):
            for fname in node.__dataclass_fields__:
                child = getattr(node, fname)
                if isinstance(child, tuple):
                    for item in child:
                        self._collect_from_ast(item)
                elif hasattr(child, "__dataclass_fields__"):
                    self._collect_from_ast(child)

    @staticmethod
    def _get_fa_base(expr: ast.FieldAccess) -> str | None:
        """Get the root identifier name from a FieldAccess chain."""
        if isinstance(expr.object, ast.Identifier):
            return expr.object.name
        if isinstance(expr.object, ast.FieldAccess):
            return TypeChecker._get_fa_base(expr.object)
        return None

    # ----------------------------------------------------------------
    # Phase 2: Walk bodies
    # ----------------------------------------------------------------

    def _phase2_walk(self, program: ast.Program) -> None:
        base_scope = self._build_base_scope()

        for decl in program.declarations:
            if isinstance(decl, ast.RuleDecl):
                self._check_rule(decl, base_scope)
            elif isinstance(decl, ast.ComputeDecl):
                self._check_compute(decl, base_scope)
            elif isinstance(decl, ast.MainDecl):
                self._check_main(decl, base_scope)

        self._check_unused_declarations()

    def _build_base_scope(self) -> set[str]:
        scope = set(_BUILTIN_NAMES)
        scope.update(self._declared_names)
        scope.update(self._settable_names)
        scope.update(self._field_access_bases)
        return scope

    # --- Declaration walkers ---

    def _check_rule(self, rule: ast.RuleDecl, base_scope: set[str]) -> None:
        scope = set(base_scope)
        for gc in rule.given_clauses:
            scope.add(gc.name)
        for cond in rule.conditions:
            self._check_condition(cond, scope)
        self._check_action(rule.action, scope)

    def _check_compute(self, compute: ast.ComputeDecl, base_scope: set[str]) -> None:
        scope = set(base_scope)
        param_types: dict[str, str] = {}
        for param in compute.params:
            scope.add(param.name)
            if param.type_ref and isinstance(param.type_ref, ast.NamedType):
                param_types[param.name] = param.type_ref.name
        # Track inferred types for gradual inference (Check #10)
        inferred: dict[str, str] = {}
        for stmt in compute.body:
            scope = self._check_statement(stmt, scope, param_types)
            self._infer_from_stmt(stmt, inferred)
        # Check #9: return type consistency
        if compute.return_type and isinstance(compute.return_type, ast.NamedType):
            declared = compute.return_type.name
            self._check_return_types(compute.body, declared, compute.location)

    def _check_main(self, main: ast.MainDecl, base_scope: set[str]) -> None:
        scope = set(base_scope)
        for stmt in main.body:
            scope = self._check_statement(stmt, scope, {})

    # --- Condition checking ---

    def _check_condition(self, cond: ast.Condition, scope: set[str]) -> None:
        if isinstance(cond, ast.ComparisonCond):
            self._check_expr(cond.left, scope)
            self._check_expr(cond.right, scope)
            if cond.right2:
                self._check_expr(cond.right2, scope)
            # Check #3: numeric comparison type mismatch
            if cond.operator in _NUMERIC_OPS:
                self._check_numeric_operand(cond.left, cond.operator)
                self._check_numeric_operand(cond.right, cond.operator)
            # Check #11: unit mismatch
            self._check_unit_comparison(cond)
        elif isinstance(cond, ast.MembershipCond):
            self._check_expr(cond.element, scope)
            self._check_expr(cond.collection, scope)
        elif isinstance(cond, ast.BooleanCond):
            self._check_expr(cond.expression, scope)
        elif isinstance(cond, ast.CompoundCond):
            self._check_condition(cond.left, scope)
            self._check_condition(cond.right, scope)
        elif isinstance(cond, ast.NotCond):
            self._check_condition(cond.condition, scope)
        elif isinstance(cond, ast.QuantifiedCond):
            self._check_expr(cond.collection, scope)
            inner_scope = scope | {cond.variable}
            self._check_condition(cond.condition, inner_scope)
        elif isinstance(cond, (ast.IsAssignedCond, ast.IsEmptyCond)):
            self._check_expr(cond.expression, scope)
        elif isinstance(cond, ast.ContainsCond):
            self._check_expr(cond.collection, scope)
            self._check_expr(cond.element, scope)
        elif isinstance(cond, ast.HasCountCond):
            self._check_expr(cond.collection, scope)
            self._check_expr(cond.count, scope)
        elif isinstance(cond, ast.StringCond):
            self._check_expr(cond.string, scope)
            self._check_expr(cond.pattern, scope)

    # --- Action checking ---

    def _check_action(self, action: ast.Action, scope: set[str]) -> None:
        if isinstance(action, ast.SetAction):
            self._check_expr(action.value, scope)
        elif isinstance(action, ast.SimpleAction):
            for param in action.params:
                self._check_expr(param.value, scope)
        elif isinstance(action, ast.BlockAction):
            block_scope = set(scope)
            for stmt in action.body:
                block_scope = self._check_statement(stmt, block_scope, {})

    # --- Statement checking ---

    def _check_statement(
        self, stmt: ast.Statement, scope: set[str], param_types: dict[str, str],
    ) -> set[str]:
        """Check a statement and return updated scope (for sequential given stmts)."""
        if isinstance(stmt, ast.GivenStmt):
            self._check_expr(stmt.value, scope, param_types)
            return scope | {stmt.name}
        if isinstance(stmt, ast.ReturnStmt):
            self._check_expr(stmt.value, scope, param_types)
            return scope
        if isinstance(stmt, ast.IfStmt):
            self._check_condition(stmt.condition, scope)
            for s in stmt.body:
                self._check_statement(s, scope, param_types)
            for elif_clause in stmt.elif_clauses:
                self._check_condition(elif_clause.condition, scope)
                for s in elif_clause.body:
                    self._check_statement(s, scope, param_types)
            for s in stmt.else_body:
                self._check_statement(s, scope, param_types)
            return scope
        if isinstance(stmt, ast.ForStmt):
            self._check_expr(stmt.iterable, scope, param_types)
            inner_scope = scope | {stmt.variable}
            for s in stmt.body:
                self._check_statement(s, inner_scope, param_types)
            return scope
        if isinstance(stmt, ast.EvaluateStmt):
            self._check_expr(stmt.argument, scope, param_types)
            return scope
        if isinstance(stmt, ast.BecomeStmt):
            self._check_expr(stmt.value, scope, param_types)
            return scope
        if isinstance(stmt, ast.ExprStmt):
            self._check_expr(stmt.expression, scope, param_types)
            return scope
        if isinstance(stmt, ast.QueryStmt):
            if stmt.argument:
                self._check_expr(stmt.argument, scope, param_types)
            return scope | {stmt.goal}
        return scope

    # --- Expression checking ---

    def _check_expr(
        self,
        expr: ast.Expression,
        scope: set[str],
        param_types: dict[str, str] | None = None,
    ) -> None:
        if param_types is None:
            param_types = {}

        if isinstance(expr, (ast.Literal, ast.SymbolLit, ast.EmptyExpr)):
            return

        if isinstance(expr, ast.Identifier):
            # Check #1: undefined variable
            if expr.name not in scope:
                self._error(expr.location, f"Undefined variable: '{expr.name}'")
            return

        if isinstance(expr, ast.FieldAccess):
            # Check #2: undefined field (only when type is statically known)
            base_name = self._get_fa_base(expr) if isinstance(expr, ast.FieldAccess) else None
            if (
                base_name
                and isinstance(expr.object, ast.Identifier)
                and base_name in param_types
            ):
                type_name = param_types[base_name]
                if (
                    type_name in self._record_fields
                    and expr.field not in self._record_fields[type_name]
                ):
                    available = ", ".join(sorted(self._record_fields[type_name]))
                    self._error(
                        expr.location,
                        f"Undefined field: '{expr.field}' on type '{type_name}'",
                        suggestion=f"Available fields: {available}",
                    )
            # Recurse into nested field access (but don't check the base identifier)
            if isinstance(expr.object, ast.FieldAccess):
                self._check_expr(expr.object, scope, param_types)
            # Don't check base Identifier — it may be an input variable
            return

        if isinstance(expr, ast.BinaryOp):
            self._check_expr(expr.left, scope, param_types)
            self._check_expr(expr.right, scope, param_types)
            return

        if isinstance(expr, ast.UnaryOp):
            self._check_expr(expr.operand, scope, param_types)
            return

        if isinstance(expr, ast.FuncCall):
            # Check #4: function arity
            func_name = self._resolve_func_name(expr.function)
            if func_name:
                expected = self._get_expected_arity(func_name)
                if expected is not None:
                    actual = len(expr.args)
                    if actual != expected:
                        self._error(
                            expr.location,
                            f"Wrong number of arguments: '{func_name}' expects "
                            f"{expected}, got {actual}",
                        )
            # Check arguments (but NOT the function expression itself)
            for arg in expr.args:
                self._check_expr(arg, scope, param_types)
            return

        if isinstance(expr, ast.ListExpr):
            for elem in expr.elements:
                self._check_expr(elem, scope, param_types)
            return

        if isinstance(expr, ast.RecordExpr):
            for f in expr.fields:
                self._check_expr(f.value, scope, param_types)
            return

        if isinstance(expr, ast.ConstructorExpr):
            for af in expr.fields:
                self._check_expr(af.value, scope, param_types)
            return

        if isinstance(expr, ast.IndexAccess):
            self._check_expr(expr.object, scope, param_types)
            self._check_expr(expr.index, scope, param_types)
            return

        if isinstance(expr, ast.MatchExpr):
            self._check_expr(expr.subject, scope, param_types)
            for arm in expr.arms:
                # Identifier patterns (non-wildcard) introduce bindings
                arm_scope = set(scope)
                if isinstance(arm.pattern, ast.Identifier) and arm.pattern.name != "_":
                    arm_scope.add(arm.pattern.name)
                self._check_expr(arm.body, arm_scope, param_types)
            # Check #6: match exhaustiveness warning
            self._check_match_exhaustiveness(expr)
            return

        if isinstance(expr, ast.PipelineExpr):
            self._check_expr(expr.source, scope, param_types)
            # Check #7: pipeline operations
            self._check_pipeline(expr, scope, param_types)
            return

        if isinstance(expr, ast.LambdaExpr):
            lambda_scope = set(scope)
            for p in expr.params:
                lambda_scope.add(p.name)
            for stmt in expr.body:
                lambda_scope = self._check_statement(stmt, lambda_scope, param_types)
            return

    # --- Check #6: Match exhaustiveness ---

    def _check_match_exhaustiveness(self, expr: ast.MatchExpr) -> None:
        """Warn if match expression might not be exhaustive."""
        has_wildcard = any(
            isinstance(arm.pattern, ast.Identifier) and arm.pattern.name == "_"
            for arm in expr.arms
        )
        has_catchall_identifier = any(
            isinstance(arm.pattern, ast.Identifier) and arm.pattern.name != "_"
            for arm in expr.arms
        )
        if not has_wildcard and not has_catchall_identifier:
            self._warning(
                expr.location,
                "Match expression may not be exhaustive — consider adding a wildcard '_' arm",
            )

    # --- Check #7: Pipeline type checking ---

    def _check_pipeline(
        self,
        expr: ast.PipelineExpr,
        scope: set[str],
        param_types: dict[str, str] | None = None,
    ) -> None:
        """Check pipeline source and operations."""
        if param_types is None:
            param_types = {}
        # Check source is not a scalar literal
        if isinstance(expr.source, ast.Literal) and not isinstance(expr.source.value, list):
            self._error(expr.source.location, "Pipeline source must be a list")
        # Check conditions/expressions in pipe ops
        pipe_scope = scope | {"it"}
        for op in expr.operations:
            if op.condition:
                self._check_condition(op.condition, pipe_scope)
            for arg in op.args:
                if isinstance(arg, ast.Expression):
                    self._check_expr(arg, pipe_scope, param_types)

    # --- Check #3 helper ---

    def _check_numeric_operand(self, expr: ast.Expression, operator: str) -> None:
        """Flag definitely non-numeric operands in numeric comparisons."""
        if isinstance(expr, ast.Literal):
            if isinstance(expr.value, str):
                self._error(
                    expr.location,
                    f"Type mismatch: string literal in numeric comparison '{operator}'",
                )
            elif isinstance(expr.value, bool):
                self._error(
                    expr.location,
                    f"Type mismatch: boolean in numeric comparison '{operator}'",
                )
        elif isinstance(expr, ast.SymbolLit):
            self._error(
                expr.location,
                f"Type mismatch: symbol in numeric comparison '{operator}'",
            )
        elif isinstance(expr, ast.ListExpr):
            self._error(
                expr.location,
                f"Type mismatch: list in numeric comparison '{operator}'",
            )

    # --- Check #9: Return type consistency ---

    def _check_return_types(
        self, stmts: tuple[ast.Statement, ...], declared: str, compute_loc: SourceLocation,
    ) -> None:
        """Warn if return expressions have a different inferred type than declared."""
        for stmt in stmts:
            if isinstance(stmt, ast.ReturnStmt):
                inferred = self._infer_expr_type(stmt.value)
                if inferred and inferred != declared:
                    self._warning(
                        stmt.location,
                        f"Return type mismatch: function declares '{declared}' "
                        f"but returns '{inferred}'",
                    )
            elif isinstance(stmt, ast.IfStmt):
                self._check_return_types(stmt.body, declared, compute_loc)
                for elif_clause in stmt.elif_clauses:
                    self._check_return_types(elif_clause.body, declared, compute_loc)
                self._check_return_types(stmt.else_body, declared, compute_loc)

    def _infer_expr_type(self, expr: ast.Expression) -> str | None:
        """Infer a simple type name from an expression, or None if unknown."""
        if isinstance(expr, ast.Literal):
            if isinstance(expr.value, bool):
                return "Boolean"
            if isinstance(expr.value, int):
                return "Number"
            if isinstance(expr.value, float):
                return "Number"
            if isinstance(expr.value, str):
                return "Text"
        if isinstance(expr, ast.SymbolLit):
            return "Symbol"
        if isinstance(expr, ast.ListExpr):
            return "List"
        return None

    # --- Check #10: Gradual type inference ---

    def _infer_from_stmt(self, stmt: ast.Statement, inferred: dict[str, str]) -> None:
        """Infer types from given statements with literal values."""
        if isinstance(stmt, ast.GivenStmt):
            t = self._infer_expr_type(stmt.value)
            if t:
                inferred[stmt.name] = t

    # --- Check #11: Unit awareness ---

    def _check_unit_comparison(self, cond: ast.ComparisonCond) -> None:
        """Warn when comparing values with different unit suffixes."""
        left_unit = self._get_unit(cond.left)
        right_unit = self._get_unit(cond.right)
        if left_unit and right_unit and left_unit != right_unit:
            self._warning(
                cond.location,
                f"Unit mismatch in comparison: '{left_unit}' vs '{right_unit}'",
                suggestion="Ensure both sides use the same unit",
            )

    def _get_unit(self, expr: ast.Expression) -> str | None:
        """Get the unit suffix of an expression, if any."""
        if isinstance(expr, ast.Literal) and expr.unit:
            return expr.unit
        if isinstance(expr, ast.Identifier) and expr.name in self._const_units:
            return self._const_units[expr.name]
        return None

    # --- Helpers ---

    def _resolve_func_name(self, expr: ast.Expression) -> str:
        """Resolve a function call target to a name string."""
        if isinstance(expr, ast.Identifier):
            return expr.name
        if isinstance(expr, ast.FieldAccess) and isinstance(expr.object, ast.Identifier):
            return f"{expr.object.name}.{expr.field}"
        return ""

    def _get_expected_arity(self, func_name: str) -> int | None:
        """Get expected arg count for a known function, or None if unknown."""
        if func_name in self._compute_arity:
            return self._compute_arity[func_name]
        if func_name in self._neural_arity:
            return self._neural_arity[func_name]
        if func_name in _BUILTIN_ARITIES:
            return _BUILTIN_ARITIES[func_name]
        return None

    # --- Unused declaration warnings ---

    def _check_unused_declarations(self) -> None:
        """Warn about declared names that are never referenced."""
        for name, loc in self._compute_names.items():
            if name not in self._referenced_names:
                self._warning(
                    loc,
                    f"Unused compute function: '{name}' is declared"
                    " but never called",
                    suggestion=f"remove '{name}' or call it from a rule"
                    " or main block",
                )
        for name, loc in self._const_names.items():
            if name not in self._referenced_names:
                self._warning(
                    loc,
                    f"Unused constant: '{name}' is defined but never"
                    " referenced",
                    suggestion=f"remove the definition of '{name}' if"
                    " it is no longer needed",
                )


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def check(program: ast.Program) -> CheckResult:
    """Type-check a Sigil program and return diagnostics."""
    checker = TypeChecker()
    return checker.check(program)
