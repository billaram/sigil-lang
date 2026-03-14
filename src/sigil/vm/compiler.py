"""Sigil AST -> bytecode compiler.

Walks the AST and emits a flat list of opcodes for the Rust VM.
"""

from __future__ import annotations

from sigil import ast
from sigil.ast.nodes import (
    BecomeStmt,
    BlockAction,
    BooleanCond,
    ComparisonCond,
    CompoundCond,
    ConstructorExpr,
    ContainsCond,
    EmptyExpr,
    EvaluateStmt,
    ExprStmt,
    FieldAccess,
    ForStmt,
    FuncCall,
    GivenStmt,
    HasCountCond,
    IfStmt,
    IndexAccess,
    IsAssignedCond,
    IsEmptyCond,
    LambdaExpr,
    ListExpr,
    MatchExpr,
    MembershipCond,
    NotCond,
    PipelineExpr,
    QuantifiedCond,
    QueryStmt,
    RecordExpr,
    ReturnStmt,
    StringCond,
    UnaryOp,
)


# Builtin function IDs — must match vm/builtins.rs constants.
BUILTIN_IDS: dict[str, int] = {
    "print": 0,
    "max": 1,
    "min": 2,
    "len": 3,
    "type_of": 4,
    "abs": 5,
    "round": 6,
    "sqrt": 7,
    "floor": 8,
    "ceil": 9,
    "append": 10,
    "range": 11,
    "sum": 12,
    "to_text": 13,
    "to_number": 14,
}

# Binary operator mapping.
_BINOP_MAP: dict[str, str] = {
    "+": "Add",
    "-": "Sub",
    "*": "Mul",
    "/": "Div",
    "%": "Mod",
    "==": "Eq",
    "!=": "Neq",
    ">": "Gt",
    "<": "Lt",
    ">=": "Gte",
    "<=": "Lte",
    "and": "And",
    "or": "Or",
}

# Condition operator mapping.
_COND_OP_MAP: dict[str, str] = {
    "exceeds": "CmpExceeds",
    "is above": "CmpExceeds",
    "is below": "CmpBelow",
    "below": "CmpBelow",
    "is at least": "CmpAtLeast",
    "at least": "CmpAtLeast",
    "is at most": "CmpAtMost",
    "at most": "CmpAtMost",
    "is between": "CmpBetween",
    "between": "CmpBetween",
    "is": "CmpIs",
    "equals": "CmpIs",
    "is not": "CmpIsNot",
}

# String condition operators.
_STRING_OP_MAP: dict[str, int] = {
    "starts with": 0,
    "starts_with": 0,
    "ends with": 1,
    "ends_with": 1,
    "contains": 2,
    "matches": 3,
}


class VMCompiler:
    """Compiles a Sigil AST Program into a bytecode chunk dict."""

    def __init__(self) -> None:
        self._code: list[list] = []  # list of [opname, ...args]
        self._strings: list[str] = []
        self._string_index: dict[str, int] = {}
        self._functions: dict[str, dict] = {}
        self._rules: list[dict] = []
        self._main_offset: int | None = None
        self._init_offset: int | None = None

    def compile(self, program: ast.Program) -> dict:
        """Compile a full program into a chunk dict for the Rust VM."""
        # Phase 1: Constants → init block at the start
        has_consts = any(isinstance(d, ast.ConstDecl) for d in program.declarations)
        if has_consts:
            self._init_offset = 0
            for decl in program.declarations:
                if isinstance(decl, ast.ConstDecl):
                    self._compile_const(decl)
            self._emit("Halt")  # End of init block

        # Phase 2: Register compute functions (compile bodies)
        for decl in program.declarations:
            if isinstance(decl, ast.ComputeDecl):
                self._compile_compute(decl)

        # Phase 3: Compile rules
        for decl in program.declarations:
            if isinstance(decl, ast.RuleDecl):
                self._compile_rule(decl)

        # Phase 4: Compile main block
        for decl in program.declarations:
            if isinstance(decl, ast.MainDecl):
                self._main_offset = len(self._code)
                self._compile_main(decl)

        # Emit final halt
        self._emit("Halt")

        return self._to_dict()

    def _to_dict(self) -> dict:
        """Serialize chunk to a dict for PyO3 transfer."""
        return {
            "code": self._code,
            "strings": self._strings,
            "functions": self._functions,
            "rules": self._rules,
            "main_offset": self._main_offset,
            "init_offset": self._init_offset,
        }

    # --- String interning ---

    def _intern(self, s: str) -> int:
        """Intern a string, return its index."""
        if s in self._string_index:
            return self._string_index[s]
        idx = len(self._strings)
        self._strings.append(s)
        self._string_index[s] = idx
        return idx

    # --- Emit helpers ---

    def _emit(self, op: str, *args: object) -> int:
        """Emit an opcode, return its offset."""
        offset = len(self._code)
        self._code.append([op, *args])
        return offset

    def _patch_jump(self, offset: int) -> None:
        """Patch a jump instruction to point to the current offset."""
        target = len(self._code)
        self._code[offset][1] = target

    # --- Constants ---

    def _compile_const(self, decl: ast.ConstDecl) -> None:
        """Compile a constant definition: `define X as <expr>`."""
        self._compile_expr(decl.value)
        name_idx = self._intern(decl.name)
        self._emit("Store", name_idx)

    # --- Compute Functions ---

    def _compile_compute(self, decl: ast.ComputeDecl) -> None:
        """Compile a compute function declaration."""
        # Jump over the function body (it's not executed inline)
        jump_offset = self._emit("Jump", 0)

        func_offset = len(self._code)
        param_names = [p.name for p in decl.params]

        # Compile body statements
        for stmt in decl.body:
            self._compile_statement(stmt)

        # Implicit return None if no explicit return
        self._emit("PushNone")
        self._emit("Return")

        # Patch the jump to skip over the function body
        self._patch_jump(jump_offset)

        # Register function info
        self._functions[decl.name] = {
            "offset": func_offset,
            "param_count": len(decl.params),
            "param_names": param_names,
        }

    # --- Rules ---

    def _compile_rule(self, rule: ast.RuleDecl) -> None:
        """Compile a rule: conditions + action blocks."""
        # Jump over the rule's condition and action code
        jump_offset = self._emit("Jump", 0)

        # Compile condition block — pushes a single bool
        cond_offset = len(self._code)
        self._compile_rule_conditions(rule.conditions)
        self._emit("Halt")  # End of condition block

        # Compile action block
        action_offset = len(self._code)
        self._compile_action(rule.action)
        self._emit("Halt")  # End of action block

        # Patch the jump
        self._patch_jump(jump_offset)

        # Handle explain string
        explain_idx = None
        if rule.explain:
            explain_idx = self._intern(rule.explain)

        # Register rule
        self._rules.append({
            "name": rule.name,
            "priority": rule.priority,
            "cond_offset": cond_offset,
            "action_offset": action_offset,
            "explain_idx": explain_idx,
        })

    def _compile_rule_conditions(self, conditions: tuple[ast.Condition, ...]) -> None:
        """Compile rule conditions into a single bool result on stack."""
        if not conditions:
            self._emit("PushBool", True)
            return

        # Flatten compound AND conditions
        flat_conds = self._flatten_conditions(conditions)

        # Short-circuit AND: jump to false_label if any condition is false
        false_jumps = []
        for cond in flat_conds:
            self._compile_condition(cond)
            false_jumps.append(self._emit("JumpIfFalse", 0))

        # All conditions passed
        self._emit("PushBool", True)
        end_jump = self._emit("Jump", 0)

        # Any condition failed
        for j in false_jumps:
            self._patch_jump(j)
        self._emit("PushBool", False)

        self._patch_jump(end_jump)

    def _flatten_conditions(
        self, conditions: tuple[ast.Condition, ...]
    ) -> list[ast.Condition]:
        """Flatten compound AND conditions into a flat list."""
        result: list[ast.Condition] = []
        for cond in conditions:
            if isinstance(cond, CompoundCond) and cond.operator == "and":
                result.extend(self._flatten_conditions((cond.left, cond.right)))
            else:
                result.append(cond)
        return result

    # --- Conditions ---

    def _compile_condition(self, cond: ast.Condition) -> None:
        """Compile a single condition — pushes a bool onto the stack."""
        if isinstance(cond, ComparisonCond):
            self._compile_comparison_cond(cond)
        elif isinstance(cond, CompoundCond):
            self._compile_compound_cond(cond)
        elif isinstance(cond, BooleanCond):
            self._compile_expr(cond.expression)
            if not cond.value:
                self._emit("Not")
        elif isinstance(cond, NotCond):
            self._compile_condition(cond.condition)
            self._emit("Not")
        elif isinstance(cond, MembershipCond):
            self._compile_expr(cond.element)
            self._compile_expr(cond.collection)
            self._emit("InList")
            if cond.negated:
                self._emit("Not")
        elif isinstance(cond, IsAssignedCond):
            self._compile_expr(cond.expression)
            self._emit("IsAssigned")
            if cond.negated:
                self._emit("Not")
        elif isinstance(cond, IsEmptyCond):
            self._compile_expr(cond.expression)
            self._emit("IsEmpty")
            if cond.negated:
                self._emit("Not")
        elif isinstance(cond, ContainsCond):
            self._compile_expr(cond.collection)
            self._compile_expr(cond.element)
            self._emit("Contains")
        elif isinstance(cond, HasCountCond):
            self._compile_expr(cond.collection)
            self._compile_expr(cond.count)
            self._emit("HasCount")
        elif isinstance(cond, StringCond):
            self._compile_expr(cond.string)
            self._compile_expr(cond.pattern)
            op_id = _STRING_OP_MAP.get(cond.operator, 2)
            self._emit("StringOp", op_id)
        elif isinstance(cond, QuantifiedCond):
            self._compile_quantified_cond(cond)
        else:
            # Fallback: push true
            self._emit("PushBool", True)

    def _compile_comparison_cond(self, cond: ComparisonCond) -> None:
        """Compile a comparison condition."""
        op = cond.operator

        if op in ("is between", "between"):
            # Three-operand: a between low and high
            self._compile_expr(cond.left)
            self._compile_expr(cond.right)
            if cond.right2:
                self._compile_expr(cond.right2)
            else:
                self._emit("PushNone")
            self._emit("CmpBetween")
        elif op in _COND_OP_MAP:
            self._compile_expr(cond.left)
            self._compile_expr(cond.right)
            self._emit(_COND_OP_MAP[op])
        else:
            # Fallback to generic comparison
            self._compile_expr(cond.left)
            self._compile_expr(cond.right)
            self._emit("Eq")

    def _compile_compound_cond(self, cond: CompoundCond) -> None:
        """Compile a compound condition (and/or)."""
        self._compile_condition(cond.left)
        if cond.operator == "and":
            jump_false = self._emit("JumpIfFalse", 0)
            self._compile_condition(cond.right)
            end_jump = self._emit("Jump", 0)
            self._patch_jump(jump_false)
            self._emit("PushBool", False)
            self._patch_jump(end_jump)
        elif cond.operator == "or":
            jump_true = self._emit("JumpIfTrue", 0)
            self._compile_condition(cond.right)
            end_jump = self._emit("Jump", 0)
            self._patch_jump(jump_true)
            self._emit("PushBool", True)
            self._patch_jump(end_jump)

    def _compile_quantified_cond(self, cond: QuantifiedCond) -> None:
        """Compile any/all/none over a collection."""
        # Evaluate collection
        self._compile_expr(cond.collection)

        # For now, implement as a loop with a result accumulator
        # This is simplified — full implementation in sprint 3
        if cond.quantifier == "any":
            self._emit("PushBool", False)  # accumulator
        elif cond.quantifier == "all":
            self._emit("PushBool", True)
        else:  # none
            self._emit("PushBool", True)
        # Pop the collection (simplified — actual loop in sprint 3)
        # For now just leave the accumulator
        # The collection is on stack below accumulator, swap and pop
        # We'll implement the full loop version in sprint 3
        self._emit("Pop")  # pop accumulator, leave collection result
        self._emit("PushBool", cond.quantifier != "none")

    # --- Actions ---

    def _compile_action(self, action: ast.Action) -> None:
        """Compile a rule action."""
        if isinstance(action, ast.SetAction):
            self._compile_expr(action.value)
            if isinstance(action.target, ast.Identifier):
                name_idx = self._intern(action.target.name)
                self._emit("Store", name_idx)
            elif isinstance(action.target, ast.FieldAccess):
                self._compile_expr(action.target.object)
                field_idx = self._intern(action.target.field)
                self._emit("StoreField", field_idx)
        elif isinstance(action, ast.SimpleAction):
            self._compile_simple_action(action)
        elif isinstance(action, BlockAction):
            for stmt in action.body:
                self._compile_statement(stmt)

    def _compile_simple_action(self, action: ast.SimpleAction) -> None:
        """Compile a simple action like 'trigger alert with severity :critical'."""
        # Check if action name is a builtin
        if action.name in BUILTIN_IDS:
            for param in action.params:
                self._compile_expr(param.value)
            self._emit("CallBuiltin", BUILTIN_IDS[action.name], len(action.params))
        elif action.name == "print":
            for param in action.params:
                self._compile_expr(param.value)
            self._emit("CallBuiltin", BUILTIN_IDS["print"], len(action.params))
        else:
            # Store action result as a symbol
            name_idx = self._intern(action.name)
            self._emit("PushSymbol", name_idx)
            if action.target:
                target_idx = self._intern(action.target)
                self._emit("Store", target_idx)

    # --- Statements ---

    def _compile_statement(self, stmt: ast.Statement) -> None:
        """Compile a statement."""
        if isinstance(stmt, GivenStmt):
            self._compile_given(stmt)
        elif isinstance(stmt, ReturnStmt):
            self._compile_expr(stmt.value)
            self._emit("Return")
        elif isinstance(stmt, IfStmt):
            self._compile_if(stmt)
        elif isinstance(stmt, ForStmt):
            self._compile_for(stmt)
        elif isinstance(stmt, BecomeStmt):
            self._compile_expr(stmt.value)
            if isinstance(stmt.target, ast.Identifier):
                name_idx = self._intern(stmt.target.name)
                self._emit("Mutate", name_idx)
        elif isinstance(stmt, ExprStmt):
            self._compile_expr_stmt(stmt)
        elif isinstance(stmt, EvaluateStmt):
            # `evaluate all rules` — in VM, rules are already evaluated
            pass
        elif isinstance(stmt, QueryStmt):
            # Backward chaining — callback to Python in sprint 4
            pass

    def _compile_expr_stmt(self, stmt: ExprStmt) -> None:
        """Compile an expression statement (e.g. print(x))."""
        expr = stmt.expression
        # Check if it's a function call to a builtin like print
        if isinstance(expr, ast.FuncCall):
            func_name = None
            if isinstance(expr.function, ast.Identifier):
                func_name = expr.function.name
            if func_name and func_name in BUILTIN_IDS:
                for arg in expr.args:
                    self._compile_expr(arg)
                self._emit("CallBuiltin", BUILTIN_IDS[func_name], len(expr.args))
                return
            elif func_name:
                for arg in expr.args:
                    self._compile_expr(arg)
                name_idx = self._intern(func_name)
                self._emit("Call", name_idx, len(expr.args))
                return
        self._compile_expr(expr)
        self._emit("Pop")

    def _compile_given(self, stmt: GivenStmt) -> None:
        """Compile a given statement."""
        name_idx = self._intern(stmt.name)
        if stmt.kind == "from":
            # `given X from input` — keep existing value if bound
            # The variable name itself is what we want — input data is pre-loaded
            # Just check if already bound, if so keep it
            self._emit("Load", name_idx)
            jump_bound = self._emit("JumpIfUnbound", 0)
            # Already bound — pop and skip
            self._emit("Pop")
            end_jump = self._emit("Jump", 0)
            self._patch_jump(jump_bound)
            # Unbound — pop the unbound value, keep as-is (input should have set it)
            self._emit("Pop")
            self._patch_jump(end_jump)
        else:
            # `given X as expr` — always evaluate and bind
            self._compile_expr(stmt.value)
            self._emit("Store", name_idx)

    def _compile_if(self, stmt: IfStmt) -> None:
        """Compile if/elif/else."""
        # Evaluate condition
        self._compile_condition(stmt.condition)
        jump_false = self._emit("JumpIfFalse", 0)

        # Then body
        for s in stmt.body:
            self._compile_statement(s)
        jump_end = self._emit("Jump", 0)

        # Elif clauses
        elif_end_jumps = []
        self._patch_jump(jump_false)
        for elif_clause in stmt.elif_clauses:
            self._compile_condition(elif_clause.condition)
            elif_false = self._emit("JumpIfFalse", 0)
            for s in elif_clause.body:
                self._compile_statement(s)
            elif_end_jumps.append(self._emit("Jump", 0))
            self._patch_jump(elif_false)

        # Else body
        if stmt.else_body:
            for s in stmt.else_body:
                self._compile_statement(s)

        # Patch all end jumps
        self._patch_jump(jump_end)
        for j in elif_end_jumps:
            self._patch_jump(j)

    def _compile_for(self, stmt: ForStmt) -> None:
        """Compile a for loop."""
        # Evaluate iterable
        self._compile_expr(stmt.iterable)

        var_idx = self._intern(stmt.variable)

        # Store the list, then iterate
        list_idx = self._intern(f"__for_list_{stmt.variable}")
        self._emit("Store", list_idx)

        # Counter
        counter_idx = self._intern(f"__for_i_{stmt.variable}")
        self._emit("PushInt", 0)
        self._emit("Store", counter_idx)

        # Loop start
        loop_start = len(self._code)

        # Check counter >= len(list) → exit loop
        self._emit("Load", counter_idx)
        self._emit("Load", list_idx)
        self._emit("CallBuiltin", BUILTIN_IDS["len"], 1)
        self._emit("Gte")
        jump_end = self._emit("JumpIfTrue", 0)

        # Load element: list[counter]
        self._emit("Load", list_idx)
        self._emit("Load", counter_idx)
        self._emit("IndexAccess")
        self._emit("Store", var_idx)

        # Loop body
        for s in stmt.body:
            self._compile_statement(s)

        # Increment counter
        self._emit("Load", counter_idx)
        self._emit("PushInt", 1)
        self._emit("Add")
        self._emit("Store", counter_idx)

        # Jump back to loop start
        self._emit("Jump", loop_start)
        self._patch_jump(jump_end)

    # --- Main Block ---

    def _compile_main(self, decl: ast.MainDecl) -> None:
        """Compile the main block."""
        for stmt in decl.body:
            self._compile_statement(stmt)

    # --- Expressions ---

    def _compile_expr(self, expr: ast.Expression) -> None:
        """Compile an expression — pushes one value onto the stack."""
        if isinstance(expr, ast.Literal):
            self._compile_literal(expr)
        elif isinstance(expr, ast.SymbolLit):
            idx = self._intern(expr.name)
            self._emit("PushSymbol", idx)
        elif isinstance(expr, ast.Identifier):
            idx = self._intern(expr.name)
            self._emit("Load", idx)
        elif isinstance(expr, ast.BinaryOp):
            self._compile_binop(expr)
        elif isinstance(expr, UnaryOp):
            self._compile_expr(expr.operand)
            if expr.operator == "-":
                self._emit("Neg")
            elif expr.operator == "not":
                self._emit("Not")
        elif isinstance(expr, FieldAccess):
            self._compile_expr(expr.object)
            field_idx = self._intern(expr.field)
            self._emit("LoadField", field_idx)
        elif isinstance(expr, FuncCall):
            self._compile_func_call(expr)
        elif isinstance(expr, IndexAccess):
            self._compile_expr(expr.object)
            self._compile_expr(expr.index)
            self._emit("IndexAccess")
        elif isinstance(expr, ListExpr):
            for elem in expr.elements:
                self._compile_expr(elem)
            self._emit("PushList", len(expr.elements))
        elif isinstance(expr, RecordExpr):
            for field in expr.fields:
                key_idx = self._intern(field.name)
                self._emit("PushString", key_idx)
                self._compile_expr(field.value)
            self._emit("PushRecord", len(expr.fields))
        elif isinstance(expr, MatchExpr):
            self._compile_match(expr)
        elif isinstance(expr, PipelineExpr):
            self._compile_pipeline(expr)
        elif isinstance(expr, LambdaExpr):
            self._compile_lambda(expr)
        elif isinstance(expr, ConstructorExpr):
            self._compile_constructor(expr)
        elif isinstance(expr, EmptyExpr):
            if expr.kind == "list":
                self._emit("PushList", 0)
            else:
                self._emit("PushNone")
        else:
            self._emit("PushNone")

    def _compile_literal(self, lit: ast.Literal) -> None:
        """Compile a literal value."""
        if lit.kind == "number":
            if isinstance(lit.value, int):
                self._emit("PushInt", lit.value)
            elif isinstance(lit.value, float):
                self._emit("PushFloat", lit.value)
            else:
                self._emit("PushNone")
        elif lit.kind == "string":
            idx = self._intern(str(lit.value))
            self._emit("PushString", idx)
        elif lit.kind == "bool":
            self._emit("PushBool", bool(lit.value))
        elif lit.kind == "none":
            self._emit("PushNone")
        else:
            self._emit("PushNone")

    def _compile_binop(self, expr: ast.BinaryOp) -> None:
        """Compile a binary operation."""
        self._compile_expr(expr.left)
        self._compile_expr(expr.right)
        op = _BINOP_MAP.get(expr.operator)
        if op:
            self._emit(op)
        else:
            self._emit("Eq")

    def _compile_func_call(self, expr: ast.FuncCall) -> None:
        """Compile a function call."""
        # Check if it's a builtin
        func_name = None
        if isinstance(expr.function, ast.Identifier):
            func_name = expr.function.name
        elif isinstance(expr.function, ast.FieldAccess):
            # Module function call like math.sqrt
            func_name = expr.function.field

        if func_name and func_name in BUILTIN_IDS:
            # Compile arguments
            for arg in expr.args:
                self._compile_expr(arg)
            self._emit("CallBuiltin", BUILTIN_IDS[func_name], len(expr.args))
        elif func_name:
            # User-defined function or variable holding closure
            for arg in expr.args:
                self._compile_expr(arg)
            name_idx = self._intern(func_name)
            self._emit("Call", name_idx, len(expr.args))
        else:
            # Complex expression call — evaluate function expression
            self._compile_expr(expr.function)
            for arg in expr.args:
                self._compile_expr(arg)
            self._emit("PushNone")  # Fallback

    def _compile_match(self, expr: MatchExpr) -> None:
        """Compile a match expression."""
        self._compile_expr(expr.subject)
        subject_idx = self._intern("__match_subject")
        self._emit("Store", subject_idx)

        end_jumps = []
        for arm in expr.arms:
            # Check for wildcard pattern `_`
            is_wildcard = (
                isinstance(arm.pattern, ast.Identifier) and arm.pattern.name == "_"
            )

            if is_wildcard:
                # Always matches
                self._compile_expr(arm.body)
                end_jumps.append(self._emit("Jump", 0))
            else:
                # Load subject, compare with pattern
                self._emit("Load", subject_idx)
                self._compile_expr(arm.pattern)
                self._emit("Eq")
                jump_next = self._emit("JumpIfFalse", 0)

                # Match body
                self._compile_expr(arm.body)
                end_jumps.append(self._emit("Jump", 0))

                self._patch_jump(jump_next)

        # Default: push None (if no wildcard arm matched)
        self._emit("PushNone")

        for j in end_jumps:
            self._patch_jump(j)

    def _compile_pipeline(self, expr: ast.PipelineExpr) -> None:
        """Compile a pipeline expression."""
        self._compile_expr(expr.source)

        for pipe_op in expr.operations:
            if pipe_op.kind == "filter":
                self._compile_pipeline_filter(pipe_op)
            elif pipe_op.kind == "transform":
                self._compile_pipeline_transform(pipe_op)
            elif pipe_op.kind == "sort":
                # Sort is complex — leave on stack for now
                pass
            elif pipe_op.kind == "count":
                self._emit("CallBuiltin", BUILTIN_IDS["len"], 1)
            elif pipe_op.kind == "sum":
                self._emit("CallBuiltin", BUILTIN_IDS["sum"], 1)
            elif pipe_op.kind == "first":
                self._emit("PushInt", 0)
                self._emit("IndexAccess")
            elif pipe_op.kind == "last":
                self._emit("PushInt", -1)
                self._emit("IndexAccess")
            else:
                # Generic pipeline op — treat as function call
                if pipe_op.args:
                    for arg in pipe_op.args:
                        self._compile_expr(arg)
                    if isinstance(pipe_op.args[0], ast.Identifier):
                        fname = pipe_op.args[0].name
                        if fname in BUILTIN_IDS:
                            self._emit("CallBuiltin", BUILTIN_IDS[fname], 1)

    def _compile_pipeline_filter(self, pipe_op: ast.PipeOp) -> None:
        """Compile a pipeline filter operation."""
        # Store source list
        src_idx = self._intern("__pipe_src")
        self._emit("Store", src_idx)

        # Create result list
        self._emit("PushList", 0)
        result_idx = self._intern("__pipe_result")
        self._emit("Store", result_idx)

        # Counter
        counter_idx = self._intern("__pipe_i")
        self._emit("PushInt", 0)
        self._emit("Store", counter_idx)

        # Loop
        loop_start = len(self._code)
        self._emit("Load", src_idx)
        self._emit("CallBuiltin", BUILTIN_IDS["len"], 1)
        self._emit("Load", counter_idx)
        self._emit("Gte")
        jump_end = self._emit("JumpIfTrue", 0)

        # Get element
        item_idx = self._intern("__pipe_item")
        self._emit("Load", src_idx)
        self._emit("Load", counter_idx)
        self._emit("IndexAccess")
        self._emit("Store", item_idx)

        # Evaluate filter condition
        if pipe_op.condition:
            self._compile_condition(pipe_op.condition)
        elif pipe_op.args:
            self._compile_expr(pipe_op.args[0])
        else:
            self._emit("PushBool", True)

        jump_skip = self._emit("JumpIfFalse", 0)

        # Append to result
        self._emit("Load", result_idx)
        self._emit("Load", item_idx)
        self._emit("CallBuiltin", BUILTIN_IDS["append"], 2)
        self._emit("Store", result_idx)

        self._patch_jump(jump_skip)

        # Increment counter
        self._emit("Load", counter_idx)
        self._emit("PushInt", 1)
        self._emit("Add")
        self._emit("Store", counter_idx)
        self._emit("Jump", loop_start)

        self._patch_jump(jump_end)
        self._emit("Load", result_idx)

    def _compile_pipeline_transform(self, pipe_op: ast.PipeOp) -> None:
        """Compile a pipeline transform operation."""
        src_idx = self._intern("__pipe_tsrc")
        self._emit("Store", src_idx)

        self._emit("PushList", 0)
        result_idx = self._intern("__pipe_tresult")
        self._emit("Store", result_idx)

        counter_idx = self._intern("__pipe_ti")
        self._emit("PushInt", 0)
        self._emit("Store", counter_idx)

        loop_start = len(self._code)
        self._emit("Load", src_idx)
        self._emit("CallBuiltin", BUILTIN_IDS["len"], 1)
        self._emit("Load", counter_idx)
        self._emit("Gte")
        jump_end = self._emit("JumpIfTrue", 0)

        item_idx = self._intern("__pipe_titem")
        self._emit("Load", src_idx)
        self._emit("Load", counter_idx)
        self._emit("IndexAccess")
        self._emit("Store", item_idx)

        # Apply transform
        if pipe_op.args:
            self._emit("Load", item_idx)
            for arg in pipe_op.args:
                self._compile_expr(arg)
        else:
            self._emit("Load", item_idx)

        # Append to result
        self._emit("Load", result_idx)
        # Swap: result is below the transformed value
        # Use append builtin
        result2_idx = self._intern("__pipe_tresult")
        self._emit("CallBuiltin", BUILTIN_IDS["append"], 2)
        self._emit("Store", result2_idx)

        # Increment
        self._emit("Load", counter_idx)
        self._emit("PushInt", 1)
        self._emit("Add")
        self._emit("Store", counter_idx)
        self._emit("Jump", loop_start)

        self._patch_jump(jump_end)
        self._emit("Load", result_idx)

    def _compile_lambda(self, expr: ast.LambdaExpr) -> None:
        """Compile a lambda expression."""
        # Generate unique function name
        func_name = f"__lambda_{len(self._functions)}"

        # Jump over body
        jump_offset = self._emit("Jump", 0)

        func_offset = len(self._code)
        param_names = [p.name for p in expr.params]

        # Compile body
        for stmt in expr.body:
            self._compile_statement(stmt)

        # Lambda body is a single expression wrapped as return
        self._emit("Return")
        self._patch_jump(jump_offset)

        self._functions[func_name] = {
            "offset": func_offset,
            "param_count": len(expr.params),
            "param_names": param_names,
        }

        # Push closure
        name_idx = self._intern(func_name)
        self._emit("MakeClosure", name_idx, 0)

    def _compile_constructor(self, expr: ast.ConstructorExpr) -> None:
        """Compile a constructor expression like `Person with name: "Alice"`."""
        for field in expr.fields:
            key_idx = self._intern(field.name)
            self._emit("PushString", key_idx)
            self._compile_expr(field.value)
        self._emit("PushRecord", len(expr.fields))
