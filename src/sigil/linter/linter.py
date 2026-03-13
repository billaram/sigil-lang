"""Sigil semantic linter — additional checks beyond the type checker."""

from __future__ import annotations

from sigil.ast import nodes as ast
from sigil.types.checker import CheckResult, Diagnostic, Severity, TypeChecker


def lint(program: ast.Program) -> CheckResult:
    """Run type checker + linter on a program."""
    checker = TypeChecker()
    result = checker.check(program)

    linter = _Linter(result)
    linter.lint(program)
    return result


class _Linter:
    """Semantic linter that builds on type checker results."""

    def __init__(self, result: CheckResult) -> None:
        self._result = result

    def _warning(
        self, loc: ast.Node, message: str, suggestion: str | None = None,
    ) -> None:
        self._result.diagnostics.append(
            Diagnostic(loc.location, Severity.WARNING, message, suggestion),
        )

    def lint(self, program: ast.Program) -> None:
        for decl in program.declarations:
            if isinstance(decl, ast.RuleDecl):
                self._lint_rule(decl)
            elif isinstance(decl, ast.NeuralDecl):
                self._lint_neural(decl)

    def _lint_rule(self, rule: ast.RuleDecl) -> None:
        # Check for empty rule body (conditions but no meaningful action)
        if isinstance(rule.action, ast.BlockAction) and not rule.action.body:
            self._warning(
                rule,
                f"Rule '{rule.name}' has an empty action block",
                suggestion="add actions to the 'then:' block"
                " or remove the rule",
            )

        # Check for duplicate conditions
        seen: list[str] = []
        for cond in rule.conditions:
            desc = self._describe_cond(cond)
            if desc in seen:
                self._warning(
                    rule,
                    f"Duplicate condition in rule '{rule.name}':"
                    f" '{desc}'",
                    suggestion="remove the duplicate condition",
                )
            seen.append(desc)

    def _lint_neural(self, decl: ast.NeuralDecl) -> None:
        for field in decl.fields:
            if (
                field.name == "confidence_threshold"
                and isinstance(field.value, ast.Literal)
                and isinstance(field.value.value, (int, float))
                and (field.value.value < 0 or field.value.value > 1)
            ):
                self._warning(
                    decl,
                    f"confidence_threshold {field.value.value} is"
                    " out of range [0.0, 1.0]",
                    suggestion="set confidence_threshold between"
                    " 0.0 and 1.0",
                )

    @staticmethod
    def _describe_cond(cond: ast.Condition) -> str:
        """Simple string description for duplicate detection."""
        if isinstance(cond, ast.ComparisonCond):
            return f"{_expr_str(cond.left)} {cond.operator} {_expr_str(cond.right)}"
        if isinstance(cond, ast.MembershipCond):
            return f"{_expr_str(cond.element)} in {_expr_str(cond.collection)}"
        if isinstance(cond, ast.BooleanCond):
            return f"{_expr_str(cond.expression)} is {cond.value}"
        return str(type(cond).__name__)


def _expr_str(expr: ast.Expression) -> str:
    """Simple string representation of an expression for comparison."""
    if isinstance(expr, ast.Identifier):
        return expr.name
    if isinstance(expr, ast.Literal):
        return str(expr.value)
    if isinstance(expr, ast.SymbolLit):
        return f":{expr.name}"
    if isinstance(expr, ast.FieldAccess):
        return f"{_expr_str(expr.object)}.{expr.field}"
    return str(type(expr).__name__)
