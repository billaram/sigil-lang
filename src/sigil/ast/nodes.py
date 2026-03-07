"""AST node definitions for the Sigil language.

All nodes are frozen dataclasses (immutable after creation).
Uses tuples instead of lists for immutable sequences.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sigil.errors import SourceLocation

# ============================================================
# Base
# ============================================================

@dataclass(frozen=True)
class Node:
    """Base class for all AST nodes."""

    location: SourceLocation


# ============================================================
# Program (top-level)
# ============================================================

@dataclass(frozen=True)
class Program(Node):
    module: ModuleDecl | None
    imports: tuple[ImportDecl, ...]
    declarations: tuple[Declaration, ...]


# ============================================================
# Module & Imports
# ============================================================

@dataclass(frozen=True)
class ModuleDecl(Node):
    path: str  # e.g. "examples.temperature"


@dataclass(frozen=True)
class ImportDecl(Node):
    source: str           # e.g. "sigil.math", "python pandas"
    kind: str             # "sigil", "python", "rust"
    alias: str | None = None
    names: tuple[str, ...] = ()  # for "from X import a, b"


# ============================================================
# Declarations
# ============================================================

@dataclass(frozen=True)
class TypeDecl(Node):
    name: str
    params: tuple[str, ...] = ()  # generic type params e.g. [T]
    body: TypeBody = field(default_factory=lambda: AliasType.__new__(AliasType))


@dataclass(frozen=True)
class RecordBody(Node):
    fields: tuple[FieldDef, ...]


@dataclass(frozen=True)
class FieldDef(Node):
    name: str
    type_ref: TypeRef


@dataclass(frozen=True)
class EnumBody(Node):
    variants: tuple[EnumVariant, ...]


@dataclass(frozen=True)
class EnumVariant(Node):
    name: str
    fields: tuple[FieldDef, ...] = ()


@dataclass(frozen=True)
class AliasType(Node):
    target: TypeRef = field(default_factory=lambda: NamedType.__new__(NamedType))


@dataclass(frozen=True)
class UnitType(Node):
    base_type: TypeRef
    unit: str


# --- Type references ---

@dataclass(frozen=True)
class TypeRef(Node):
    """Base for type references."""


@dataclass(frozen=True)
class NamedType(TypeRef):
    name: str
    params: tuple[TypeRef, ...] = ()


@dataclass(frozen=True)
class ListType(TypeRef):
    element_type: TypeRef


@dataclass(frozen=True)
class OptionType(TypeRef):
    inner_type: TypeRef


@dataclass(frozen=True)
class InlineRecordType(TypeRef):
    fields: tuple[FieldDef, ...]


TypeBody = RecordBody | EnumBody | AliasType | UnitType


# ============================================================
# Constants
# ============================================================

@dataclass(frozen=True)
class ConstDecl(Node):
    name: str
    value: Expression


# ============================================================
# Rule Declarations
# ============================================================

@dataclass(frozen=True)
class RuleDecl(Node):
    name: str
    conditions: tuple[Condition, ...]
    action: Action
    priority: int = 0
    given_clauses: tuple[GivenClause, ...] = ()
    explain: str | None = None
    trace: tuple[TraceField, ...] = ()
    metadata: tuple[MetaField, ...] = ()


@dataclass(frozen=True)
class GivenClause(Node):
    name: str
    source: Expression
    kind: str = "from"  # "from" or "as"


@dataclass(frozen=True)
class TraceField(Node):
    name: str
    value: Expression


@dataclass(frozen=True)
class MetaField(Node):
    name: str
    value: Expression


# ============================================================
# Conditions
# ============================================================

@dataclass(frozen=True)
class Condition(Node):
    """Base for conditions."""


@dataclass(frozen=True)
class ComparisonCond(Condition):
    left: Expression
    operator: str  # "exceeds", "is below", "is between", "is", "is not", "equals", etc.
    right: Expression
    right2: Expression | None = None  # for "is between X and Y"


@dataclass(frozen=True)
class MembershipCond(Condition):
    element: Expression
    collection: Expression
    negated: bool = False  # "not in" vs "in"


@dataclass(frozen=True)
class QuantifiedCond(Condition):
    quantifier: str  # "any", "all", "none"
    variable: str
    collection: Expression
    condition: Condition


@dataclass(frozen=True)
class BooleanCond(Condition):
    expression: Expression
    value: bool  # "is true" or "is false"


@dataclass(frozen=True)
class NotCond(Condition):
    condition: Condition


@dataclass(frozen=True)
class CompoundCond(Condition):
    operator: str  # "and" or "or"
    left: Condition
    right: Condition


@dataclass(frozen=True)
class IsAssignedCond(Condition):
    expression: Expression
    negated: bool = False  # "is not assigned"


@dataclass(frozen=True)
class IsEmptyCond(Condition):
    expression: Expression
    negated: bool = False  # "is not empty"


@dataclass(frozen=True)
class ContainsCond(Condition):
    collection: Expression
    element: Expression


@dataclass(frozen=True)
class HasCountCond(Condition):
    collection: Expression
    count: Expression


@dataclass(frozen=True)
class StringCond(Condition):
    string: Expression
    operator: str  # "starts with", "ends with", "contains", "matches pattern"
    pattern: Expression


# ============================================================
# Actions
# ============================================================

@dataclass(frozen=True)
class Action(Node):
    """Base for actions."""


@dataclass(frozen=True)
class SimpleAction(Action):
    """Simple action like 'alert' or 'trigger alert with severity :critical'."""
    name: str
    target: str | None = None  # e.g. "alert" in "trigger alert"
    params: tuple[ActionParam, ...] = ()


@dataclass(frozen=True)
class ActionParam(Node):
    name: str
    value: Expression


@dataclass(frozen=True)
class SetAction(Action):
    """Action that sets a value: 'age_eligible is true'."""
    target: Expression
    value: Expression


@dataclass(frozen=True)
class BlockAction(Action):
    """Block action (then: with indented body)."""
    body: tuple[Statement, ...]


# ============================================================
# Compute Declarations
# ============================================================

@dataclass(frozen=True)
class ComputeDecl(Node):
    name: str
    params: tuple[Param, ...]
    body: tuple[Statement, ...]
    return_type: TypeRef | None = None


@dataclass(frozen=True)
class Param(Node):
    name: str
    type_ref: TypeRef | None = None


# ============================================================
# Neural Declarations
# ============================================================

@dataclass(frozen=True)
class NeuralDecl(Node):
    name: str
    param_name: str
    param_type: TypeRef
    fields: tuple[NeuralField, ...]


@dataclass(frozen=True)
class NeuralField(Node):
    name: str  # "model", "returns", "confidence_threshold", "fallback", etc.
    value: Expression | TypeRef


# ============================================================
# Main Declaration
# ============================================================

@dataclass(frozen=True)
class MainDecl(Node):
    body: tuple[Statement, ...]
    trace: tuple[TraceField, ...] = ()


# ============================================================
# Statements
# ============================================================

@dataclass(frozen=True)
class Statement(Node):
    """Base for statements."""


@dataclass(frozen=True)
class GivenStmt(Statement):
    name: str
    value: Expression
    kind: str = "as"  # "as" or "from"


@dataclass(frozen=True)
class ReturnStmt(Statement):
    value: Expression


@dataclass(frozen=True)
class IfStmt(Statement):
    condition: Condition
    body: tuple[Statement, ...]
    elif_clauses: tuple[ElifClause, ...] = ()
    else_body: tuple[Statement, ...] = ()


@dataclass(frozen=True)
class ElifClause(Node):
    condition: Condition
    body: tuple[Statement, ...]


@dataclass(frozen=True)
class ForStmt(Statement):
    variable: str
    iterable: Expression
    body: tuple[Statement, ...]


@dataclass(frozen=True)
class EvaluateStmt(Statement):
    target: str  # "all rules" or a rule name
    argument: Expression


@dataclass(frozen=True)
class BecomeStmt(Statement):
    target: Expression
    value: Expression


@dataclass(frozen=True)
class ExprStmt(Statement):
    expression: Expression


# ============================================================
# Expressions
# ============================================================

@dataclass(frozen=True)
class Expression(Node):
    """Base for expressions."""


@dataclass(frozen=True)
class Literal(Expression):
    value: int | float | str | bool | None
    kind: str = "number"  # "number", "string", "bool", "none"


@dataclass(frozen=True)
class SymbolLit(Expression):
    name: str


@dataclass(frozen=True)
class Identifier(Expression):
    name: str


@dataclass(frozen=True)
class BinaryOp(Expression):
    left: Expression
    operator: str  # "+", "-", "*", "/", "and", "or"
    right: Expression


@dataclass(frozen=True)
class UnaryOp(Expression):
    operator: str  # "not", "-"
    operand: Expression


@dataclass(frozen=True)
class FieldAccess(Expression):
    object: Expression
    field: str


@dataclass(frozen=True)
class FuncCall(Expression):
    function: Expression
    args: tuple[Expression, ...]
    named_args: tuple[NamedArg, ...] = ()


@dataclass(frozen=True)
class NamedArg(Node):
    name: str
    value: Expression


@dataclass(frozen=True)
class IndexAccess(Expression):
    object: Expression
    index: Expression


@dataclass(frozen=True)
class ListExpr(Expression):
    elements: tuple[Expression, ...]


@dataclass(frozen=True)
class RecordExpr(Expression):
    fields: tuple[RecordFieldExpr, ...]


@dataclass(frozen=True)
class RecordFieldExpr(Node):
    name: str
    value: Expression


@dataclass(frozen=True)
class MatchExpr(Expression):
    subject: Expression
    arms: tuple[MatchArm, ...]


@dataclass(frozen=True)
class MatchArm(Node):
    pattern: Expression  # Literal, Identifier, or wildcard
    body: Expression


@dataclass(frozen=True)
class PipelineExpr(Expression):
    source: Expression
    operations: tuple[PipeOp, ...]


@dataclass(frozen=True)
class PipeOp(Node):
    kind: str  # "filter", "sort", "take", "map", or identifier
    args: tuple[Expression, ...] = ()
    condition: Condition | None = None
    direction: str | None = None  # "ascending" / "descending" for sort


@dataclass(frozen=True)
class LambdaExpr(Expression):
    """Inline anonymous compute expression."""
    params: tuple[Param, ...]
    return_type: TypeRef | None
    body: tuple[Statement, ...]


@dataclass(frozen=True)
class ConstructorExpr(Expression):
    """Enum constructor like 'approved with rate: value'."""
    name: str
    fields: tuple[ActionParam, ...] = ()


@dataclass(frozen=True)
class EmptyExpr(Expression):
    """'empty list' or 'empty' expression."""
    kind: str = "list"  # what's empty


# ============================================================
# Union types for use in other nodes
# ============================================================

@dataclass(frozen=True)
class ExportDecl(Node):
    """Export declaration: export name1, name2, ..."""
    names: tuple[str, ...]


Declaration = TypeDecl | ConstDecl | RuleDecl | ComputeDecl | NeuralDecl | MainDecl | ExportDecl


# ============================================================
# AST Pretty Printer
# ============================================================

def dump(node: object, indent: int = 0) -> str:
    """Pretty-print an AST node as an indented tree."""
    prefix = "  " * indent
    if node is None:
        return f"{prefix}None"

    if isinstance(node, (str, int, float, bool)):
        return f"{prefix}{node!r}"

    if isinstance(node, tuple):
        if not node:
            return f"{prefix}()"
        lines = [f"{prefix}("]
        for item in node:
            lines.append(dump(item, indent + 1))
        lines.append(f"{prefix})")
        return "\n".join(lines)

    if not hasattr(node, "__dataclass_fields__"):
        return f"{prefix}{node!r}"

    class_name = type(node).__name__
    fields = node.__dataclass_fields__  # type: ignore[attr-defined]

    if not fields:
        return f"{prefix}{class_name}()"

    # Skip location field for readability
    field_items = [(k, getattr(node, k)) for k in fields if k != "location"]

    if not field_items:
        return f"{prefix}{class_name}()"

    # Single simple field — inline
    if len(field_items) == 1:
        k, v = field_items[0]
        if isinstance(v, (str, int, float, bool, type(None))):
            return f"{prefix}{class_name}({k}={v!r})"

    lines = [f"{prefix}{class_name}("]
    for k, v in field_items:
        if isinstance(v, (str, int, float, bool, type(None))):
            lines.append(f"{prefix}  {k}={v!r}")
        elif isinstance(v, tuple) and not v:
            lines.append(f"{prefix}  {k}=()")
        else:
            lines.append(f"{prefix}  {k}=")
            lines.append(dump(v, indent + 2))
    lines.append(f"{prefix})")
    return "\n".join(lines)
