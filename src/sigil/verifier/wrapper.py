"""Python wrapper for the Rust BDD-based verifier.

Extracts rule information from the Sigil AST and passes it to the
Rust `verify_program()` function, then parses the JSON report.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from sigil.ast import nodes as ast


@dataclass
class VerificationReport:
    """Parsed verification report."""

    completeness_ok: bool
    coverage_percent: float
    completeness_witness: str | None
    dead_rules: list[str]
    conflicts: list[dict[str, str]]
    terminates: bool
    cycles: list[list[str]]
    rule_count: int
    variable_count: int
    bdd_variable_count: int

    @property
    def is_sound(self) -> bool:
        return (
            self.completeness_ok
            and not self.dead_rules
            and not self.conflicts
            and self.terminates
        )


def verify_file(path: Path) -> VerificationReport:
    """Verify a .sigil file."""
    from sigil.lexer import tokenize
    from sigil.parser import parse

    source = path.read_text()
    tokens = tokenize(source, str(path))
    program = parse(tokens, str(path))
    return verify_program(program)


def verify_program(program: ast.Program) -> VerificationReport:
    """Verify an AST Program's rules."""
    rules = _extract_rules(program)
    if not rules:
        return VerificationReport(
            completeness_ok=True,
            coverage_percent=100.0,
            completeness_witness=None,
            dead_rules=[],
            conflicts=[],
            terminates=True,
            cycles=[],
            rule_count=0,
            variable_count=0,
            bdd_variable_count=0,
        )

    try:
        from sigil._sigil_core import verify_program as _rust_verify
    except ImportError:
        raise RuntimeError(
            "Rust core not built. Run: maturin develop"
        )

    report_json = _rust_verify(rules)
    return _parse_report(json.loads(report_json))


def _extract_rules(program: ast.Program) -> list[dict]:
    """Extract rule declarations from the AST into dicts for Rust."""
    rules = []
    for decl in program.declarations:
        if isinstance(decl, ast.RuleDecl):
            conditions = [_condition_to_dict(c) for c in decl.conditions]
            action = _action_to_dict(decl.action)
            read_vars = _collect_read_vars(decl.conditions)
            write_vars = _collect_write_vars(decl.action)
            rules.append({
                "name": decl.name,
                "priority": decl.priority,
                "conditions": conditions,
                "action": action,
                "read_vars": read_vars,
                "write_vars": write_vars,
            })
    return rules


def _condition_to_dict(cond: ast.Condition) -> dict:
    """Convert an AST Condition to a dict for the Rust verifier."""
    if isinstance(cond, ast.ComparisonCond):
        var_name = _expr_to_var(cond.left)
        value = _expr_to_number(cond.right)
        value2 = _expr_to_number(cond.right2) if cond.right2 else None
        symbol = _expr_to_symbol(cond.right)
        return {
            "kind": "comparison",
            "variable": var_name,
            "operator": cond.operator,
            "value": value,
            "value2": value2,
            "symbol": symbol,
        }

    if isinstance(cond, ast.BooleanCond):
        return {
            "kind": "boolean",
            "variable": _expr_to_var(cond.expression),
            "bool_value": cond.value,
        }

    if isinstance(cond, ast.MembershipCond):
        elements = _expr_to_number_list(cond.collection)
        return {
            "kind": "membership",
            "variable": _expr_to_var(cond.element),
            "elements": elements,
            "negated": cond.negated,
        }

    if isinstance(cond, ast.IsAssignedCond):
        return {
            "kind": "is_assigned",
            "variable": _expr_to_var(cond.expression),
            "negated": cond.negated,
        }

    if isinstance(cond, ast.IsEmptyCond):
        return {
            "kind": "is_empty",
            "variable": _expr_to_var(cond.expression),
            "negated": cond.negated,
        }

    if isinstance(cond, ast.NotCond):
        return {
            "kind": "not",
            "left": _condition_to_dict(cond.condition),
        }

    if isinstance(cond, ast.CompoundCond):
        return {
            "kind": "compound",
            "operator": cond.operator,
            "left": _condition_to_dict(cond.left),
            "right": _condition_to_dict(cond.right),
        }

    if isinstance(cond, ast.ContainsCond):
        return {
            "kind": "contains",
            "variable": _expr_to_var(cond.collection),
        }

    if isinstance(cond, ast.HasCountCond):
        return {
            "kind": "has_count",
            "variable": _expr_to_var(cond.collection),
            "value": _expr_to_number(cond.count),
        }

    if isinstance(cond, ast.StringCond):
        return {
            "kind": "string",
            "variable": _expr_to_var(cond.string),
            "operator": cond.operator,
        }

    if isinstance(cond, ast.QuantifiedCond):
        return {
            "kind": "quantified",
            "variable": cond.variable,
        }

    # Unknown condition type — return a generic entry
    return {"kind": "unknown"}


def _action_to_dict(action: ast.Action) -> dict:
    """Convert an AST Action to a dict for the Rust verifier."""
    if isinstance(action, ast.SetAction):
        return {
            "kind": "set",
            "target": _expr_to_var(action.target),
            "value": _expr_to_var(action.value) or str(action.value),
        }
    if isinstance(action, ast.SimpleAction):
        return {
            "kind": "trigger",
            "target": action.name,
            "value": action.target,
        }
    if isinstance(action, ast.BlockAction):
        # Extract write targets from block body
        targets = []
        for stmt in action.body:
            if isinstance(stmt, ast.GivenClause):
                targets.append(stmt.name)
        return {
            "kind": "block",
            "target": ",".join(targets) if targets else None,
            "value": None,
        }
    return {"kind": "unknown"}


# --- AST expression helpers ---

def _expr_to_var(expr: ast.Expression | None) -> str | None:
    """Extract a variable name from an expression."""
    if expr is None:
        return None
    if isinstance(expr, ast.Identifier):
        return expr.name
    if isinstance(expr, ast.FieldAccess):
        obj_name = _expr_to_var(expr.object)
        if obj_name:
            return f"{obj_name}.{expr.field}"
    return None


def _expr_to_number(expr: ast.Expression | None) -> float | None:
    """Extract a numeric value from an expression."""
    if expr is None:
        return None
    if isinstance(expr, ast.Literal) and isinstance(expr.value, (int, float)):
        return float(expr.value)
    return None


def _expr_to_symbol(expr: ast.Expression | None) -> str | None:
    """Extract a symbol name from an expression."""
    if expr is None:
        return None
    if isinstance(expr, ast.SymbolLit):
        return expr.name
    return None


def _expr_to_number_list(expr: ast.Expression | None) -> list[float] | None:
    """Extract a list of numbers from a list expression."""
    if expr is None:
        return None
    if isinstance(expr, ast.ListExpr):
        numbers = []
        for elem in expr.elements:
            val = _expr_to_number(elem)
            if val is not None:
                numbers.append(val)
        return numbers if numbers else None
    return None


def _collect_read_vars(conditions: tuple[ast.Condition, ...]) -> list[str]:
    """Collect all variable names read in conditions."""
    names: set[str] = set()
    for cond in conditions:
        _walk_cond_vars(cond, names)
    return sorted(names)


def _walk_cond_vars(cond: ast.Condition, names: set[str]) -> None:
    """Recursively collect variable names from a condition."""
    if isinstance(cond, ast.ComparisonCond):
        v = _expr_to_var(cond.left)
        if v:
            names.add(v)
    elif isinstance(cond, ast.BooleanCond):
        v = _expr_to_var(cond.expression)
        if v:
            names.add(v)
    elif isinstance(cond, ast.MembershipCond):
        v = _expr_to_var(cond.element)
        if v:
            names.add(v)
    elif isinstance(cond, ast.IsAssignedCond):
        v = _expr_to_var(cond.expression)
        if v:
            names.add(v)
    elif isinstance(cond, ast.IsEmptyCond):
        v = _expr_to_var(cond.expression)
        if v:
            names.add(v)
    elif isinstance(cond, ast.NotCond):
        _walk_cond_vars(cond.condition, names)
    elif isinstance(cond, ast.CompoundCond):
        _walk_cond_vars(cond.left, names)
        _walk_cond_vars(cond.right, names)
    elif isinstance(cond, ast.ContainsCond):
        v = _expr_to_var(cond.collection)
        if v:
            names.add(v)
    elif isinstance(cond, ast.StringCond):
        v = _expr_to_var(cond.string)
        if v:
            names.add(v)


def _collect_write_vars(action: ast.Action) -> list[str]:
    """Collect all variable names written by an action."""
    names: set[str] = set()
    if isinstance(action, ast.SetAction):
        v = _expr_to_var(action.target)
        if v:
            names.add(v)
    elif isinstance(action, ast.BlockAction):
        for stmt in action.body:
            if isinstance(stmt, ast.GivenClause):
                names.add(stmt.name)
    return sorted(names)


def _parse_report(data: dict) -> VerificationReport:
    """Parse JSON report from Rust into a VerificationReport."""
    comp = data.get("completeness", {})
    dead = data.get("dead_rules", [])
    conflicts = data.get("conflicts", [])
    term = data.get("termination", {})

    return VerificationReport(
        completeness_ok=comp.get("is_complete", True),
        coverage_percent=comp.get("coverage_percent", 100.0),
        completeness_witness=comp.get("witness"),
        dead_rules=[d["rule_name"] for d in dead if d.get("is_dead")],
        conflicts=[
            {
                "rule_a": c["rule_a"],
                "rule_b": c["rule_b"],
                "witness": c.get("witness"),
            }
            for c in conflicts
        ],
        terminates=term.get("terminates", True),
        cycles=term.get("cycles", []),
        rule_count=data.get("rule_count", 0),
        variable_count=data.get("variable_count", 0),
        bdd_variable_count=data.get("bdd_variable_count", 0),
    )
