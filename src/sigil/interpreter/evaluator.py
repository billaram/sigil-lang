"""Tree-walking evaluator for the Sigil interpreter.

Takes an AST (from the parser) and evaluates it, producing a result + trace.
"""

from __future__ import annotations

import re

from sigil.ast import nodes as ast
from sigil.errors import SigilRuntimeError
from sigil.interpreter.builtins import BUILTINS, DOTTED_BUILTINS
from sigil.interpreter.environment import Environment
from sigil.interpreter.trace import (
    ConditionTrace,
    ProgramTrace,
    RuleTrace,
    TraceTimer,
)
from sigil.interpreter.values import (
    _UNBOUND,
    Closure,
    Record,
    Symbol,
    Value,
    Variant,
    format_value,
    values_equal,
)


class ReturnSignal(Exception):  # noqa: N818 — not an error, it's a control flow signal
    """Signal a return statement — unwind the call stack."""

    def __init__(self, value: Value) -> None:
        super().__init__()
        self.value = value


class Evaluator:
    """Tree-walking interpreter for Sigil programs."""

    def __init__(self) -> None:
        self.trace = ProgramTrace()
        self._compute_funcs: dict[str, ast.ComputeDecl] = {}
        self._neural_funcs: dict[str, ast.NeuralDecl] = {}
        self._type_defs: dict[str, ast.TypeDecl] = {}
        self._exports: set[str] = set()
        self._module_env: Environment = Environment()
        self.module_loader: object | None = None  # ModuleLoader, set externally
        self.filename: str = "<stdin>"

    def eval_program_repl(
        self,
        program: ast.Program,
        env: Environment,
        rules: list[ast.RuleDecl],
    ) -> tuple[Value, ProgramTrace, Environment]:
        """Evaluate a program fragment for REPL mode.

        Accepts existing environment and rule list; returns updated environment.
        Fresh ProgramTrace per input.
        """
        self.trace = ProgramTrace()

        # Register new declarations
        for decl in program.declarations:
            if isinstance(decl, ast.ConstDecl):
                val = self.eval_expression(decl.value, env)
                env = env.set(decl.name, val)
            elif isinstance(decl, ast.TypeDecl):
                self._type_defs[decl.name] = decl
            elif isinstance(decl, ast.ComputeDecl):
                self._compute_funcs[decl.name] = decl
            elif isinstance(decl, ast.NeuralDecl):
                self._neural_funcs[decl.name] = decl

        # Collect new rules
        for decl in program.declarations:
            if isinstance(decl, ast.RuleDecl):
                rules.append(decl)

        # Execute main block if present
        result: Value = None
        for decl in program.declarations:
            if isinstance(decl, ast.MainDecl):
                result, env = self._eval_main(decl, rules, env)

        self.trace.final_result = result
        return result, self.trace, env

    def eval_program(
        self, program: ast.Program, input_data: dict[str, Value] | None = None,
    ) -> tuple[Value, ProgramTrace]:
        """Evaluate a full Sigil program."""
        with TraceTimer() as timer:
            env = Environment(input_data or {})

            # Process imports
            for imp in program.imports:
                env = self._eval_import(imp, env)

            # Process export declarations
            for decl in program.declarations:
                if isinstance(decl, ast.ExportDecl):
                    self._exports.update(decl.names)

            # Phase 1: Register declarations
            for decl in program.declarations:
                if isinstance(decl, ast.ConstDecl):
                    val = self.eval_expression(decl.value, env)
                    env = env.set(decl.name, val)
                elif isinstance(decl, ast.TypeDecl):
                    self._type_defs[decl.name] = decl
                elif isinstance(decl, ast.ComputeDecl):
                    self._compute_funcs[decl.name] = decl
                elif isinstance(decl, ast.NeuralDecl):
                    self._neural_funcs[decl.name] = decl

            # Save module environment (for module loading)
            self._module_env = env

            # Phase 2: Find and run main block, or run all rules
            main_decl = None
            rules: list[ast.RuleDecl] = []
            for decl in program.declarations:
                if isinstance(decl, ast.MainDecl):
                    main_decl = decl
                elif isinstance(decl, ast.RuleDecl):
                    rules.append(decl)

            result: Value = None
            if main_decl is not None:
                result, env = self._eval_main(main_decl, rules, env)
            elif rules:
                result, env = self._eval_rules(rules, env)

        self.trace.final_result = result
        self.trace.total_duration_ms = timer.duration_ms
        return result, self.trace

    # ------------------------------------------------------------------
    # Imports
    # ------------------------------------------------------------------

    def _eval_import(
        self, decl: ast.ImportDecl, env: Environment,
    ) -> Environment:
        """Evaluate an import declaration."""
        from pathlib import Path

        # Python FFI imports
        if decl.kind == "python":
            return self._eval_python_import(decl, env)

        # Rust imports — not yet implemented (Sprint 3)
        if decl.kind == "rust":
            return env

        if self.module_loader is None:
            # No module loader configured — try stdlib builtins directly
            if decl.source.startswith("sigil."):
                from sigil.stdlib import get_stdlib_module
                try:
                    module = get_stdlib_module(
                        decl.source.removeprefix("sigil."),
                    )
                except Exception:
                    return env
            else:
                return env
        else:
            from sigil.modules.loader import ModuleLoader
            assert isinstance(self.module_loader, ModuleLoader)
            module = self.module_loader.load(decl.source, Path(self.filename))

        if decl.names:
            # Selective import: from X import a, b, c
            for name in decl.names:
                if name not in module.exports:
                    msg = f"'{name}' is not exported from module '{decl.source}'"
                    raise SigilRuntimeError(msg)
                val = module.env.get(name)
                env = env.set(name, val)
                # Also register compute funcs if available
                if name in module.compute_funcs:
                    self._compute_funcs[name] = module.compute_funcs[name]
        elif decl.alias:
            # Aliased import: import X as Y
            module_record = Record(
                type_name=decl.alias,
                fields=dict(module.env.all_bindings()),
            )
            env = env.set(decl.alias, module_record)
        else:
            # Full import: import X — bind exported names directly
            for name in module.exports:
                val = module.env.get(name)
                if val is not _UNBOUND:
                    env = env.set(name, val)
                # Also register compute funcs
                if name in module.compute_funcs:
                    self._compute_funcs[name] = module.compute_funcs[name]

        return env

    def _eval_python_import(
        self, decl: ast.ImportDecl, env: Environment,
    ) -> Environment:
        """Evaluate a Python FFI import."""
        from sigil.ffi.python_interop import import_python_module, import_python_names

        source = decl.source

        try:
            if decl.names:
                # from python X import a, b
                bindings = import_python_names(source, decl.names)
                for name, val in bindings.items():
                    env = env.set(name, val)
            elif decl.alias:
                # import python X as Y
                bindings = import_python_module(source)
                module_record = Record(type_name=decl.alias, fields=bindings)
                env = env.set(decl.alias, module_record)
            else:
                # import python X — bind as record with module name
                bindings = import_python_module(source)
                bind_name = source.rsplit(".", maxsplit=1)[-1]
                module_record = Record(type_name=bind_name, fields=bindings)
                env = env.set(bind_name, module_record)
        except SigilRuntimeError:
            # Module not available — bind empty record so neural stubs still work.
            # Actual calls to missing module functions will fail at call time.
            bind_name = decl.alias or source.rsplit(".", maxsplit=1)[-1]
            if not decl.names:
                env = env.set(bind_name, Record(type_name=bind_name, fields={}))

        return env

    # ------------------------------------------------------------------
    # Main block
    # ------------------------------------------------------------------

    def _eval_main(
        self, main: ast.MainDecl, rules: list[ast.RuleDecl], env: Environment,
    ) -> tuple[Value, Environment]:
        """Evaluate a main block."""
        result: Value = None
        for stmt in main.body:
            result, env = self._eval_statement(stmt, rules, env)
        return result, env

    # ------------------------------------------------------------------
    # Rules
    # ------------------------------------------------------------------

    def _eval_rules(
        self, rules: list[ast.RuleDecl], env: Environment,
    ) -> tuple[Value, Environment]:
        """Evaluate all rules with forward chaining.

        Iterates until no new rules fire (fixed point) or max iterations reached.
        Rules that already fired don't re-fire.
        """
        max_iterations = 100
        fired_rules: set[str] = set()
        result: Value = None
        sorted_rules = sorted(rules, key=lambda r: r.priority, reverse=True)

        for _ in range(max_iterations):
            any_new_fired = False

            for rule in sorted_rules:
                if rule.name in fired_rules:
                    continue

                fired, action_result, env = self._eval_single_rule(rule, env)
                if fired:
                    fired_rules.add(rule.name)
                    any_new_fired = True
                    if action_result is not None:
                        result = action_result

            if not any_new_fired:
                break

        return result, env

    def _eval_single_rule(
        self, rule: ast.RuleDecl, env: Environment,
    ) -> tuple[bool, Value, Environment]:
        """Evaluate a single rule. Returns (fired, action_result, updated_env)."""
        with TraceTimer() as timer:
            rule_trace = RuleTrace(
                rule_name=rule.name,
                priority=rule.priority,
                fired=False,
            )

            # Evaluate conditions
            all_true = True
            conditions = self._flatten_conditions(rule.conditions)

            for _i, cond in enumerate(conditions):
                if not all_true:
                    # Short-circuit: skip remaining conditions
                    rule_trace.conditions.append(ConditionTrace(
                        description=self._describe_condition(cond),
                        result=False,
                        skipped=True,
                    ))
                    continue

                result, bindings = self._eval_condition(cond, env)
                rule_trace.conditions.append(ConditionTrace(
                    description=self._describe_condition(cond),
                    result=result,
                    bindings=bindings,
                ))
                if not result:
                    all_true = False

            # Execute action if all conditions are true
            action_result: Value = None
            if all_true:
                rule_trace.fired = True
                action_result, env = self._eval_action(rule.action, env)
                rule_trace.action_result = action_result
                rule_trace.action_description = self._describe_action(rule.action)

                # Interpolate explain string
                if rule.explain:
                    rule_trace.explain = self._interpolate_string(rule.explain, env)

                # Process trace metadata
                for tf in rule.trace:
                    val = self.eval_expression(tf.value, env)
                    rule_trace.metadata[tf.name] = val

                # Temporal awareness: record constraint info (not enforced yet)
                if rule.temporal is not None:
                    dur = self.eval_expression(rule.temporal.duration, env)
                    rule_trace.metadata["_temporal_constraint"] = (
                        f"within {dur} {rule.temporal.unit}"
                    )

            rule_trace.duration_ms = timer.duration_ms

        self.trace.add_rule_trace(rule_trace)
        return all_true, action_result, env

    def _flatten_conditions(
        self, conditions: tuple[ast.Condition, ...],
    ) -> list[ast.Condition]:
        """Flatten CompoundCond(and) into a flat list for top-level rule conditions."""
        result: list[ast.Condition] = []
        for cond in conditions:
            if isinstance(cond, ast.CompoundCond) and cond.operator == "and":
                result.extend(self._flatten_compound_and(cond))
            else:
                result.append(cond)
        return result

    def _flatten_compound_and(self, cond: ast.CompoundCond) -> list[ast.Condition]:
        """Recursively flatten nested AND conditions."""
        parts: list[ast.Condition] = []
        if isinstance(cond.left, ast.CompoundCond) and cond.left.operator == "and":
            parts.extend(self._flatten_compound_and(cond.left))
        else:
            parts.append(cond.left)
        if isinstance(cond.right, ast.CompoundCond) and cond.right.operator == "and":
            parts.extend(self._flatten_compound_and(cond.right))
        else:
            parts.append(cond.right)
        return parts

    # ------------------------------------------------------------------
    # Conditions
    # ------------------------------------------------------------------

    def _eval_condition(
        self, cond: ast.Condition, env: Environment,
    ) -> tuple[bool, dict[str, Value]]:
        """Evaluate a condition. Returns (result, relevant_bindings)."""
        if isinstance(cond, ast.ComparisonCond):
            return self._eval_comparison(cond, env)
        if isinstance(cond, ast.MembershipCond):
            return self._eval_membership(cond, env)
        if isinstance(cond, ast.BooleanCond):
            return self._eval_boolean_cond(cond, env)
        if isinstance(cond, ast.CompoundCond):
            return self._eval_compound(cond, env)
        if isinstance(cond, ast.NotCond):
            result, bindings = self._eval_condition(cond.condition, env)
            return not result, bindings
        if isinstance(cond, ast.QuantifiedCond):
            return self._eval_quantified(cond, env)
        if isinstance(cond, ast.IsAssignedCond):
            return self._eval_is_assigned(cond, env)
        if isinstance(cond, ast.IsEmptyCond):
            return self._eval_is_empty(cond, env)
        if isinstance(cond, ast.ContainsCond):
            return self._eval_contains(cond, env)
        if isinstance(cond, ast.HasCountCond):
            return self._eval_has_count(cond, env)
        if isinstance(cond, ast.StringCond):
            return self._eval_string_cond(cond, env)
        msg = f"Unknown condition type: {type(cond).__name__}"
        raise SigilRuntimeError(msg)

    def _eval_comparison(
        self, cond: ast.ComparisonCond, env: Environment,
    ) -> tuple[bool, dict[str, Value]]:
        left = self.eval_expression(cond.left, env)
        right = self.eval_expression(cond.right, env)
        op = cond.operator

        # If either side is unbound, comparison fails (except "is not")
        if left is _UNBOUND or right is _UNBOUND:
            result = op == "is not"
            return result, {"left": left, "right": right}

        if op == "exceeds":
            result = left > right  # type: ignore[operator]
        elif op == "is below":
            result = left < right  # type: ignore[operator]
        elif op == "is between":
            right2 = self.eval_expression(cond.right2, env) if cond.right2 else right
            result = right <= left <= right2  # type: ignore[operator]
        elif op == "is at least":
            result = left >= right  # type: ignore[operator]
        elif op == "is at most":
            result = left <= right  # type: ignore[operator]
        elif op in ("is", "equals"):
            result = values_equal(left, right)
        elif op == "is not":
            result = not values_equal(left, right)
        else:
            msg = f"Unknown comparison operator: {op}"
            raise SigilRuntimeError(msg)

        return result, {"left": left, "right": right}

    def _eval_membership(
        self, cond: ast.MembershipCond, env: Environment,
    ) -> tuple[bool, dict[str, Value]]:
        element = self.eval_expression(cond.element, env)
        collection = self.eval_expression(cond.collection, env)
        if element is _UNBOUND or collection is _UNBOUND:
            return cond.negated, {"element": element}
        if not isinstance(collection, list):
            msg = f"Membership check requires a list, got {type(collection).__name__}"
            raise SigilRuntimeError(msg)
        found = any(values_equal(element, item) for item in collection)
        result = not found if cond.negated else found
        return result, {"element": element}

    def _eval_boolean_cond(
        self, cond: ast.BooleanCond, env: Environment,
    ) -> tuple[bool, dict[str, Value]]:
        val = self.eval_expression(cond.expression, env)
        # If the value is _UNBOUND (variable not assigned), treat as not-true
        if val is _UNBOUND:
            result = not cond.value  # "is true" → false, "is not true" → true
        elif isinstance(val, bool):
            result = val == cond.value
        else:
            result = bool(val) == cond.value
        return result, {"value": val}

    def _eval_compound(
        self, cond: ast.CompoundCond, env: Environment,
    ) -> tuple[bool, dict[str, Value]]:
        left_result, left_bindings = self._eval_condition(cond.left, env)

        if cond.operator == "and":
            if not left_result:
                return False, left_bindings
            right_result, right_bindings = self._eval_condition(cond.right, env)
            return right_result, {**left_bindings, **right_bindings}

        if cond.operator == "or":
            if left_result:
                return True, left_bindings
            right_result, right_bindings = self._eval_condition(cond.right, env)
            return right_result, {**left_bindings, **right_bindings}

        msg = f"Unknown compound operator: {cond.operator}"
        raise SigilRuntimeError(msg)

    def _eval_quantified(
        self, cond: ast.QuantifiedCond, env: Environment,
    ) -> tuple[bool, dict[str, Value]]:
        collection = self.eval_expression(cond.collection, env)
        if not isinstance(collection, list):
            msg = f"Quantifier requires a list, got {type(collection).__name__}"
            raise SigilRuntimeError(msg)

        if cond.quantifier == "any":
            for item in collection:
                child_env = env.set(cond.variable, item)
                result, _ = self._eval_condition(cond.condition, child_env)
                if result:
                    return True, {cond.variable: item}
            return False, {}

        if cond.quantifier == "all":
            for item in collection:
                child_env = env.set(cond.variable, item)
                result, _ = self._eval_condition(cond.condition, child_env)
                if not result:
                    return False, {cond.variable: item}
            return True, {}

        if cond.quantifier == "none":
            for item in collection:
                child_env = env.set(cond.variable, item)
                result, _ = self._eval_condition(cond.condition, child_env)
                if result:
                    return False, {cond.variable: item}
            return True, {}

        msg = f"Unknown quantifier: {cond.quantifier}"
        raise SigilRuntimeError(msg)

    def _eval_is_assigned(
        self, cond: ast.IsAssignedCond, env: Environment,
    ) -> tuple[bool, dict[str, Value]]:
        val = self.eval_expression(cond.expression, env)
        is_assigned = val is not _UNBOUND and val is not None
        result = not is_assigned if cond.negated else is_assigned
        return result, {}

    def _eval_is_empty(
        self, cond: ast.IsEmptyCond, env: Environment,
    ) -> tuple[bool, dict[str, Value]]:
        val = self.eval_expression(cond.expression, env)
        is_empty = len(val) == 0 if isinstance(val, list) else (val is None or val is _UNBOUND)
        result = not is_empty if cond.negated else is_empty
        return result, {}

    def _eval_contains(
        self, cond: ast.ContainsCond, env: Environment,
    ) -> tuple[bool, dict[str, Value]]:
        collection = self.eval_expression(cond.collection, env)
        element = self.eval_expression(cond.element, env)
        if not isinstance(collection, list):
            msg = f"Contains requires a list, got {type(collection).__name__}"
            raise SigilRuntimeError(msg)
        return any(values_equal(element, item) for item in collection), {}

    def _eval_has_count(
        self, cond: ast.HasCountCond, env: Environment,
    ) -> tuple[bool, dict[str, Value]]:
        collection = self.eval_expression(cond.collection, env)
        count = self.eval_expression(cond.count, env)
        if not isinstance(collection, list):
            msg = "has count requires a list"
            raise SigilRuntimeError(msg)
        return len(collection) == count, {}

    def _eval_string_cond(
        self, cond: ast.StringCond, env: Environment,
    ) -> tuple[bool, dict[str, Value]]:
        string = self.eval_expression(cond.string, env)
        pattern = self.eval_expression(cond.pattern, env)
        if not isinstance(string, str) or not isinstance(pattern, str):
            msg = "String condition requires text values"
            raise SigilRuntimeError(msg)

        if cond.operator == "starts with":
            return string.startswith(pattern), {}
        if cond.operator == "ends with":
            return string.endswith(pattern), {}
        if cond.operator == "contains":
            return pattern in string, {}
        if cond.operator == "matches pattern":
            return bool(re.match(pattern, string)), {}

        msg = f"Unknown string operator: {cond.operator}"
        raise SigilRuntimeError(msg)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _eval_action(
        self, action: ast.Action, env: Environment,
    ) -> tuple[Value, Environment]:
        """Evaluate a rule action."""
        if isinstance(action, ast.SetAction):
            value = self.eval_expression(action.value, env)
            target = self._resolve_target_name(action.target)
            env = env.set(target, value)
            return value, env

        if isinstance(action, ast.SimpleAction):
            return self._eval_simple_action(action, env)

        if isinstance(action, ast.BlockAction):
            return self._eval_block_action(action, env)

        msg = f"Unknown action type: {type(action).__name__}"
        raise SigilRuntimeError(msg)

    def _eval_simple_action(
        self, action: ast.SimpleAction, env: Environment,
    ) -> tuple[Value, Environment]:
        """Evaluate a simple action like 'print greeting' or 'trigger alert with severity :high'."""
        # Resolve the function name
        func_name = action.target if action.target else action.name

        # Evaluate action parameters
        param_values: dict[str, Value] = {}
        for param in action.params:
            param_values[param.name] = self.eval_expression(param.value, env)

        # Look up the function
        if func_name == "print":
            # Special: print takes its argument from action.name (the target of print)
            args = [self.eval_expression(ast.Identifier(
                location=action.location, name=action.name,
            ), env)]
            result = BUILTINS["print"](args, self.trace)
            return result, env

        # For other actions (trigger, log, shutdown_system, etc.) — record in trace
        return Symbol(func_name), env

    def _eval_block_action(
        self, action: ast.BlockAction, env: Environment,
    ) -> tuple[Value, Environment]:
        """Evaluate a block action (then: with indented body)."""
        result: Value = None
        for stmt in action.body:
            try:
                result, env = self._eval_statement(stmt, [], env)
            except ReturnSignal as ret:
                return ret.value, env
        return result, env

    def _resolve_target_name(self, expr: ast.Expression) -> str:
        """Extract the variable name from a set action target."""
        if isinstance(expr, ast.Identifier):
            return expr.name
        if isinstance(expr, ast.FieldAccess):
            # For now just use the field name
            return self._resolve_target_name(expr.object) + "." + expr.field
        msg = f"Cannot resolve set action target: {type(expr).__name__}"
        raise SigilRuntimeError(msg)

    # ------------------------------------------------------------------
    # Statements
    # ------------------------------------------------------------------

    def _eval_statement(
        self, stmt: ast.Statement, rules: list[ast.RuleDecl], env: Environment,
    ) -> tuple[Value, Environment]:
        """Evaluate a statement."""
        if isinstance(stmt, ast.GivenStmt):
            return self._eval_given(stmt, env)
        if isinstance(stmt, ast.ReturnStmt):
            value = self.eval_expression(stmt.value, env)
            raise ReturnSignal(value)
        if isinstance(stmt, ast.IfStmt):
            return self._eval_if(stmt, rules, env)
        if isinstance(stmt, ast.ForStmt):
            return self._eval_for(stmt, rules, env)
        if isinstance(stmt, ast.BecomeStmt):
            return self._eval_become(stmt, env)
        if isinstance(stmt, ast.EvaluateStmt):
            return self._eval_evaluate(stmt, rules, env)
        if isinstance(stmt, ast.QueryStmt):
            return self._eval_query(stmt, rules, env)
        if isinstance(stmt, ast.ExprStmt):
            val = self.eval_expression(stmt.expression, env)
            return val, env
        msg = f"Unknown statement type: {type(stmt).__name__}"
        raise SigilRuntimeError(msg)

    def _eval_given(
        self, stmt: ast.GivenStmt, env: Environment,
    ) -> tuple[Value, Environment]:
        """Evaluate a given statement (local binding)."""
        # If the variable is already bound (e.g. from input data), keep it
        existing = env.get(stmt.name)
        if existing is not _UNBOUND and stmt.kind == "from":
            return existing, env

        # If the expression is a neural stub call and variable is already bound,
        # prefer the existing value (neural stubs return fallback defaults)
        if existing is not _UNBOUND and self._is_neural_call(stmt.value):
            return existing, env

        try:
            value = self.eval_expression(stmt.value, env)
        except SigilRuntimeError:
            # If evaluation fails (e.g. undefined external function) and
            # the variable is already bound, keep the existing value
            if existing is not _UNBOUND:
                return existing, env
            raise
        env = env.set(stmt.name, value)
        return value, env

    def _is_neural_call(self, expr: ast.Expression) -> bool:
        """Check if an expression is a call to a registered neural function."""
        if isinstance(expr, ast.FuncCall) and isinstance(expr.function, ast.Identifier):
            return expr.function.name in self._neural_funcs
        return False

    def _eval_if(
        self, stmt: ast.IfStmt, rules: list[ast.RuleDecl], env: Environment,
    ) -> tuple[Value, Environment]:
        """Evaluate an if/elif/else statement."""
        result, _ = self._eval_condition(stmt.condition, env)
        if result:
            return self._eval_body(stmt.body, rules, env)

        for elif_clause in stmt.elif_clauses:
            result, _ = self._eval_condition(elif_clause.condition, env)
            if result:
                return self._eval_body(elif_clause.body, rules, env)

        if stmt.else_body:
            return self._eval_body(stmt.else_body, rules, env)

        return None, env

    def _eval_for(
        self, stmt: ast.ForStmt, rules: list[ast.RuleDecl], env: Environment,
    ) -> tuple[Value, Environment]:
        """Evaluate a for-each loop."""
        iterable = self.eval_expression(stmt.iterable, env)
        if not isinstance(iterable, list):
            msg = f"for-each requires a list, got {type(iterable).__name__}"
            raise SigilRuntimeError(msg)

        result: Value = None
        for item in iterable:
            child_env = env.set(stmt.variable, item)
            try:
                result, child_env = self._eval_body(stmt.body, rules, child_env)
            except ReturnSignal:
                raise
        return result, env

    def _eval_become(
        self, stmt: ast.BecomeStmt, env: Environment,
    ) -> tuple[Value, Environment]:
        """Evaluate a becomes statement (controlled mutation)."""
        value = self.eval_expression(stmt.value, env)
        target = self._resolve_target_name(stmt.target)
        env.mutate(target, value)
        return value, env

    def _eval_evaluate(
        self, stmt: ast.EvaluateStmt, rules: list[ast.RuleDecl], env: Environment,
    ) -> tuple[Value, Environment]:
        """Evaluate 'evaluate all rules with X'."""
        arg = self.eval_expression(stmt.argument, env)

        # If arg is a record, spread its fields into the env
        if isinstance(arg, Record):
            for field_name, field_val in arg.fields.items():
                env = env.set(field_name, field_val)

        result, env = self._eval_rules(rules, env)
        return result, env

    def _eval_query(
        self, stmt: ast.QueryStmt, rules: list[ast.RuleDecl], env: Environment,
    ) -> tuple[Value, Environment]:
        """Evaluate a backward chaining query statement."""
        from sigil.interpreter.backward import BackwardChainer

        chainer = BackwardChainer(rules, env, self)
        proof = chainer.query(stmt.goal)
        self.trace.proof_trees.append(proof)

        # Update environment with proved bindings
        env = chainer.env
        result = env.get(stmt.goal)
        if result is _UNBOUND:
            # Query failed — bind goal to None so print() shows "none"
            result = None
            env = env.set(stmt.goal, None)
        return result, env

    def _eval_body(
        self, body: tuple[ast.Statement, ...], rules: list[ast.RuleDecl],
        env: Environment,
    ) -> tuple[Value, Environment]:
        """Evaluate a sequence of statements."""
        result: Value = None
        for stmt in body:
            result, env = self._eval_statement(stmt, rules, env)
        return result, env

    # ------------------------------------------------------------------
    # Expressions
    # ------------------------------------------------------------------

    def eval_expression(self, expr: ast.Expression, env: Environment) -> Value:
        """Evaluate an expression to a value."""
        if isinstance(expr, ast.Literal):
            return expr.value
        if isinstance(expr, ast.SymbolLit):
            return Symbol(expr.name)
        if isinstance(expr, ast.Identifier):
            return self._eval_identifier(expr, env)
        if isinstance(expr, ast.FieldAccess):
            return self._eval_field_access(expr, env)
        if isinstance(expr, ast.BinaryOp):
            return self._eval_binary_op(expr, env)
        if isinstance(expr, ast.UnaryOp):
            return self._eval_unary_op(expr, env)
        if isinstance(expr, ast.FuncCall):
            return self._eval_func_call(expr, env)
        if isinstance(expr, ast.ListExpr):
            return [self.eval_expression(e, env) for e in expr.elements]
        if isinstance(expr, ast.RecordExpr):
            fields = {f.name: self.eval_expression(f.value, env) for f in expr.fields}
            return Record(type_name=None, fields=fields)
        if isinstance(expr, ast.EmptyExpr):
            return []
        if isinstance(expr, ast.ConstructorExpr):
            return self._eval_constructor(expr, env)
        if isinstance(expr, ast.IndexAccess):
            return self._eval_index_access(expr, env)
        if isinstance(expr, ast.MatchExpr):
            return self._eval_match(expr, env)
        if isinstance(expr, ast.PipelineExpr):
            return self._eval_pipeline(expr, env)
        if isinstance(expr, ast.LambdaExpr):
            return self._eval_lambda(expr, env)
        msg = f"Unknown expression type: {type(expr).__name__}"
        raise SigilRuntimeError(msg)

    def _eval_identifier(self, expr: ast.Identifier, env: Environment) -> Value:
        """Look up an identifier in the environment."""
        val = env.get(expr.name)
        if val is _UNBOUND:
            # Check for compute functions — return as Closure for higher-order use
            if expr.name in self._compute_funcs:
                decl = self._compute_funcs[expr.name]
                return Closure(
                    params=tuple(p.name for p in decl.params),
                    body=decl.body,
                    env=env,
                    name=expr.name,
                )
            # Check for neural functions (resolved at call time)
            if expr.name in self._neural_funcs:
                return _UNBOUND  # type: ignore[return-value]
            # Check for enum variant names (no-field variants like 'clear')
            if expr.name in self._get_variant_names():
                return Variant(type_name="", variant_name=expr.name, fields={})
            # Return _UNBOUND so conditions like "is not assigned" can work
            return _UNBOUND  # type: ignore[return-value]
        return val

    def _get_variant_names(self) -> set[str]:
        """Collect all enum variant names from type declarations."""
        names: set[str] = set()
        for td in self._type_defs.values():
            if isinstance(td.body, ast.EnumBody):
                for v in td.body.variants:
                    names.add(v.name)
        return names

    def _eval_field_access(self, expr: ast.FieldAccess, env: Environment) -> Value:
        """Evaluate field access on a record."""
        obj = self.eval_expression(expr.object, env)
        if isinstance(obj, Record):
            if expr.field in obj.fields:
                return obj.fields[expr.field]
            # Missing fields return _UNBOUND so conditions like "is not assigned" work
            return _UNBOUND  # type: ignore[return-value]
        if isinstance(obj, Variant):
            if expr.field in obj.fields:
                return obj.fields[expr.field]
            msg = f"Variant '{obj.variant_name}' has no field '{expr.field}'"
            raise SigilRuntimeError(msg)
        # If obj is _UNBOUND, try to look up the whole dotted name
        if obj is _UNBOUND:
            # Try dotted lookup: e.g. "math.max"
            if isinstance(expr.object, ast.Identifier):
                dotted = f"{expr.object.name}.{expr.field}"
                if dotted in DOTTED_BUILTINS:
                    return DOTTED_BUILTINS[dotted]  # type: ignore[return-value]
                # Try as environment lookup
                val = env.get(dotted)
                if val is not _UNBOUND:
                    return val
            return _UNBOUND  # type: ignore[return-value]
        msg = f"Cannot access field '{expr.field}' on {type(obj).__name__}"
        raise SigilRuntimeError(msg)

    def _eval_binary_op(self, expr: ast.BinaryOp, env: Environment) -> Value:
        """Evaluate a binary operation."""
        left = self.eval_expression(expr.left, env)
        right = self.eval_expression(expr.right, env)
        op = expr.operator

        if op == "+":
            if isinstance(left, list) and isinstance(right, list):
                return left + right
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            return left + right  # type: ignore[operator]
        if op == "-":
            return left - right  # type: ignore[operator]
        if op == "*":
            return left * right  # type: ignore[operator]
        if op == "/":
            if right == 0:
                msg = "Division by zero"
                raise SigilRuntimeError(msg)
            return left / right  # type: ignore[operator]
        if op == "and":
            return bool(left) and bool(right)
        if op == "or":
            return bool(left) or bool(right)
        msg = f"Unknown binary operator: {op}"
        raise SigilRuntimeError(msg)

    def _eval_unary_op(self, expr: ast.UnaryOp, env: Environment) -> Value:
        """Evaluate a unary operation."""
        operand = self.eval_expression(expr.operand, env)
        if expr.operator == "-":
            return -operand  # type: ignore[operator]
        if expr.operator == "not":
            return not operand
        msg = f"Unknown unary operator: {expr.operator}"
        raise SigilRuntimeError(msg)

    def _eval_func_call(self, expr: ast.FuncCall, env: Environment) -> Value:
        """Evaluate a function call."""
        args = [self.eval_expression(a, env) for a in expr.args]

        # Resolve the function
        func_name = self._resolve_func_name(expr.function, env)

        # Check compute functions first
        if func_name in self._compute_funcs:
            return self._call_compute(func_name, args, env)

        # Check neural functions (model registry with fallback)
        if func_name in self._neural_funcs:
            return self._call_neural(func_name, args)

        # Check built-in functions
        if func_name in BUILTINS:
            return BUILTINS[func_name](args, self.trace)

        if func_name in DOTTED_BUILTINS:
            return DOTTED_BUILTINS[func_name](args, self.trace)

        # Check if the function expression resolves to a Closure
        func_val = self.eval_expression(expr.function, env)
        if isinstance(func_val, Closure):
            return self._call_closure(func_val, args)

        # Check if the function value is a callable from the environment
        if callable(func_val):
            return func_val(args, self.trace)

        msg = f"Undefined function: {func_name}"
        raise SigilRuntimeError(msg)

    def _resolve_func_name(self, expr: ast.Expression, env: Environment) -> str:
        """Resolve a function expression to its name."""
        if isinstance(expr, ast.Identifier):
            return expr.name
        if isinstance(expr, ast.FieldAccess):
            obj_name = self._resolve_func_name(expr.object, env)
            return f"{obj_name}.{expr.field}"
        return ""

    def _call_compute(
        self, name: str, args: list[Value], env: Environment,
    ) -> Value:
        """Call a user-defined compute function."""
        decl = self._compute_funcs[name]

        # Bind parameters
        if len(args) != len(decl.params):
            msg = f"{name} expects {len(decl.params)} args, got {len(args)}"
            raise SigilRuntimeError(msg)

        bindings: dict[str, Value] = {}
        for param, arg in zip(decl.params, args, strict=True):
            bindings[param.name] = arg

        # Create a new scope with the bindings
        func_env = env.extend(bindings)

        # Execute body
        try:
            for stmt in decl.body:
                _, func_env = self._eval_statement(stmt, [], func_env)
        except ReturnSignal as ret:
            return ret.value

        return None

    def _call_neural(self, name: str, args: list[Value]) -> Value:
        """Call a neural function via the model registry, with fallback."""
        from sigil.interpreter.trace import NeuralTrace
        from sigil.neural.registry import get_registry

        decl = self._neural_funcs[name]

        # Extract neural declaration fields
        model_id = ""
        threshold = 0.5
        fallback_value: Value = None
        for f in decl.fields:
            if f.name == "model" and isinstance(f.value, ast.Expression):
                model_id = str(self.eval_expression(f.value, Environment()))
            elif f.name == "confidence_threshold" and isinstance(f.value, ast.Expression):
                threshold = float(self.eval_expression(f.value, Environment()))
            elif f.name == "fallback" and isinstance(f.value, ast.Expression):
                fallback_value = self.eval_expression(f.value, Environment())

        # Get input data from args
        input_data: Value = args[0] if args else None

        # Try the model registry
        registry = get_registry()
        if model_id and registry.has_backend(model_id):
            try:
                result = registry.predict(model_id, input_data)
                if result.confidence >= threshold:
                    self.trace.add_neural_trace(NeuralTrace(
                        function_name=name,
                        model_id=model_id,
                        confidence=result.confidence,
                        threshold=threshold,
                        used_fallback=False,
                        result=result.value,
                        latency_ms=result.latency_ms,
                    ))
                    return result.value
                # Below threshold — use fallback
                self.trace.add_neural_trace(NeuralTrace(
                    function_name=name,
                    model_id=model_id,
                    confidence=result.confidence,
                    threshold=threshold,
                    used_fallback=True,
                    result=fallback_value,
                    latency_ms=result.latency_ms,
                ))
                return fallback_value
            except Exception as exc:
                self.trace.add_neural_trace(NeuralTrace(
                    function_name=name,
                    model_id=model_id,
                    confidence=0.0,
                    threshold=threshold,
                    used_fallback=True,
                    result=fallback_value,
                    error=str(exc),
                ))
                return fallback_value

        # No backend available — return fallback (stub behavior)
        self.trace.add_neural_trace(NeuralTrace(
            function_name=name,
            model_id=model_id,
            confidence=0.0,
            threshold=threshold,
            used_fallback=True,
            result=fallback_value,
        ))
        return fallback_value

    def _eval_constructor(self, expr: ast.ConstructorExpr, env: Environment) -> Value:
        """Evaluate a constructor expression like 'approved with rate: value'."""
        fields: dict[str, Value] = {}
        for param in expr.fields:
            fields[param.name] = self.eval_expression(param.value, env)
        return Variant(type_name="", variant_name=expr.name, fields=fields)

    def _eval_index_access(self, expr: ast.IndexAccess, env: Environment) -> Value:
        """Evaluate index access on a list."""
        obj = self.eval_expression(expr.object, env)
        index = self.eval_expression(expr.index, env)
        if isinstance(obj, list) and isinstance(index, int):
            if 0 <= index < len(obj):
                result: Value = obj[index]
                return result
            msg = f"Index {index} out of range for list of length {len(obj)}"
            raise SigilRuntimeError(msg)
        msg = f"Cannot index {type(obj).__name__} with {type(index).__name__}"
        raise SigilRuntimeError(msg)

    # ------------------------------------------------------------------
    # Match expression
    # ------------------------------------------------------------------

    def _eval_match(self, expr: ast.MatchExpr, env: Environment) -> Value:
        """Evaluate a match expression."""
        subject_val = self.eval_expression(expr.subject, env)

        for arm in expr.arms:
            matched, bindings = self._match_pattern(arm.pattern, subject_val)
            if matched:
                body_env = env.extend(bindings) if bindings else env
                return self.eval_expression(arm.body, body_env)

        msg = "No matching pattern in match expression"
        raise SigilRuntimeError(msg)

    def _match_pattern(
        self, pattern: ast.Expression, value: Value,
    ) -> tuple[bool, dict[str, Value]]:
        """Check if a pattern matches a value. Returns (matched, bindings)."""
        # Wildcard: _ always matches, no binding
        if isinstance(pattern, ast.Identifier) and pattern.name == "_":
            return True, {}

        # Literal pattern: compare values
        if isinstance(pattern, ast.Literal):
            return values_equal(value, pattern.value), {}

        # Symbol pattern: compare symbol names
        if isinstance(pattern, ast.SymbolLit):
            if isinstance(value, Symbol) and value.name == pattern.name:
                return True, {}
            return False, {}

        # Identifier pattern: always matches, binds the value
        if isinstance(pattern, ast.Identifier):
            return True, {pattern.name: value}

        return False, {}

    # ------------------------------------------------------------------
    # Pipeline expression
    # ------------------------------------------------------------------

    def _eval_pipeline(self, expr: ast.PipelineExpr, env: Environment) -> Value:
        """Evaluate a pipeline expression."""
        source = self.eval_expression(expr.source, env)
        if not isinstance(source, list):
            msg = f"Pipeline source must be a list, got {type(source).__name__}"
            raise SigilRuntimeError(msg)

        result: list[Value] = source
        for op in expr.operations:
            result = self._eval_pipe_op(op, result, env)
        return result

    def _eval_pipe_op(
        self, op: ast.PipeOp, items: list[Value], env: Environment,
    ) -> list[Value]:
        """Evaluate a single pipeline operation."""
        if op.kind == "filter":
            assert op.condition is not None
            filtered: list[Value] = []
            for item in items:
                item_env = self._pipeline_item_env(item, env)
                cond_result, _ = self._eval_condition(op.condition, item_env)
                if cond_result:
                    filtered.append(item)
            return filtered

        if op.kind == "sort":
            field_name = op.args[0] if op.args else None
            reverse = op.direction == "descending"
            if isinstance(field_name, ast.Identifier):
                fname = field_name.name
                return sorted(
                    items,
                    key=lambda r: r.fields.get(fname, 0) if isinstance(r, Record) else r,  # type: ignore[arg-type,return-value]
                    reverse=reverse,
                )
            if isinstance(field_name, ast.Literal) and isinstance(field_name.value, str):
                fname_s = field_name.value
                return sorted(
                    items,
                    key=lambda r: r.fields.get(fname_s, 0) if isinstance(r, Record) else r,  # type: ignore[arg-type,return-value]
                    reverse=reverse,
                )
            return sorted(
                items,
                key=lambda x: x if isinstance(x, (int, float)) else 0,
                reverse=reverse,
            )

        if op.kind == "take_first":
            count = self.eval_expression(op.args[0], env) if op.args else 1
            return items[:int(count)]  # type: ignore[arg-type]

        if op.kind == "take_last":
            count = self.eval_expression(op.args[0], env) if op.args else 1
            return items[-int(count):]  # type: ignore[arg-type]

        if op.kind == "map":
            mapped: list[Value] = []
            for item in items:
                item_env = self._pipeline_item_env(item, env)
                val = self.eval_expression(op.args[0], item_env)
                mapped.append(val)
            return mapped

        msg = f"Unknown pipeline operation: {op.kind}"
        raise SigilRuntimeError(msg)

    def _pipeline_item_env(self, item: Value, env: Environment) -> Environment:
        """Create environment for a pipeline item."""
        if isinstance(item, Record):
            bindings = dict(item.fields)
            bindings["it"] = item
            return env.extend(bindings)
        return env.set("it", item)

    # ------------------------------------------------------------------
    # Closures and lambda
    # ------------------------------------------------------------------

    def _eval_lambda(self, expr: ast.LambdaExpr, env: Environment) -> Value:
        """Evaluate a lambda expression to a Closure value."""
        return Closure(
            params=tuple(p.name for p in expr.params),
            body=expr.body,
            env=env,
            name=None,
        )

    def _call_closure(
        self, closure: Closure, args: list[Value],
    ) -> Value:
        """Call a closure with arguments."""
        if len(args) != len(closure.params):
            name = closure.name or "<anonymous>"
            msg = f"{name} expects {len(closure.params)} args, got {len(args)}"
            raise SigilRuntimeError(msg)

        bindings = dict(zip(closure.params, args, strict=True))
        func_env = closure.env.extend(bindings)

        try:
            for stmt in closure.body:
                _, func_env = self._eval_statement(stmt, [], func_env)
        except ReturnSignal as ret:
            return ret.value

        return None

    # ------------------------------------------------------------------
    # String interpolation
    # ------------------------------------------------------------------

    def _interpolate_string(self, template: str, env: Environment) -> str:
        """Interpolate {expr} placeholders in a string."""
        def replacer(match: re.Match[str]) -> str:
            expr_str = match.group(1)
            # Handle dotted access like "reading.temperature"
            parts = expr_str.split(".")
            val: Value = env.get(parts[0])
            for part in parts[1:]:
                if isinstance(val, Record) and part in val.fields:
                    val = val.fields[part]
                elif val is _UNBOUND:
                    return f"{{{expr_str}}}"
                else:
                    return f"{{{expr_str}}}"
            if val is _UNBOUND:
                return f"{{{expr_str}}}"
            return format_value(val) if not isinstance(val, str) else val

        return re.sub(r"\{([^}]+)\}", replacer, template)

    # ------------------------------------------------------------------
    # Description helpers (for trace)
    # ------------------------------------------------------------------

    def _describe_condition(self, cond: ast.Condition) -> str:
        """Generate a human-readable description of a condition."""
        if isinstance(cond, ast.ComparisonCond):
            left = self._describe_expr(cond.left)
            right = self._describe_expr(cond.right)
            if cond.right2:
                right2 = self._describe_expr(cond.right2)
                return f"{left} {cond.operator} {right} and {right2}"
            return f"{left} {cond.operator} {right}"
        if isinstance(cond, ast.BooleanCond):
            expr = self._describe_expr(cond.expression)
            val = "true" if cond.value else "false"
            return f"{expr} is {val}"
        if isinstance(cond, ast.MembershipCond):
            elem = self._describe_expr(cond.element)
            coll = self._describe_expr(cond.collection)
            neg = "not in" if cond.negated else "in"
            return f"{elem} {neg} {coll}"
        if isinstance(cond, ast.IsAssignedCond):
            expr = self._describe_expr(cond.expression)
            neg = "is not assigned" if cond.negated else "is assigned"
            return f"{expr} {neg}"
        if isinstance(cond, ast.IsEmptyCond):
            expr = self._describe_expr(cond.expression)
            neg = "is not empty" if cond.negated else "is empty"
            return f"{expr} {neg}"
        if isinstance(cond, ast.QuantifiedCond):
            coll = self._describe_expr(cond.collection)
            inner = self._describe_condition(cond.condition)
            return f"{cond.quantifier} {cond.variable} in {coll} has {inner}"
        if isinstance(cond, ast.CompoundCond):
            left = self._describe_condition(cond.left)
            right = self._describe_condition(cond.right)
            return f"{left} {cond.operator} {right}"
        return type(cond).__name__

    def _describe_expr(self, expr: ast.Expression) -> str:
        """Generate a short description of an expression."""
        if isinstance(expr, ast.Identifier):
            return expr.name
        if isinstance(expr, ast.Literal):
            return repr(expr.value)
        if isinstance(expr, ast.SymbolLit):
            return f":{expr.name}"
        if isinstance(expr, ast.FieldAccess):
            return f"{self._describe_expr(expr.object)}.{expr.field}"
        if isinstance(expr, ast.BinaryOp):
            left = self._describe_expr(expr.left)
            right = self._describe_expr(expr.right)
            return f"{left} {expr.operator} {right}"
        if isinstance(expr, ast.FuncCall):
            return f"{self._describe_expr(expr.function)}(...)"
        return type(expr).__name__

    def _describe_action(self, action: ast.Action) -> str:
        """Generate a short description of an action."""
        if isinstance(action, ast.SetAction):
            return f"{self._describe_expr(action.target)} = {self._describe_expr(action.value)}"
        if isinstance(action, ast.SimpleAction):
            parts = []
            if action.target:
                parts.append(action.target)
            parts.append(action.name)
            for p in action.params:
                parts.append(f"{p.name}: {self._describe_expr(p.value)}")
            return " ".join(parts)
        if isinstance(action, ast.BlockAction):
            return f"block ({len(action.body)} statements)"
        return type(action).__name__


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def evaluate(
    program: ast.Program, input_data: dict[str, Value] | None = None,
) -> tuple[Value, ProgramTrace]:
    """Evaluate a Sigil program and return (result, trace)."""
    evaluator = Evaluator()
    return evaluator.eval_program(program, input_data)
