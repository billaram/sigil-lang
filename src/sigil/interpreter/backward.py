"""Backward chaining engine for Sigil.

Given a goal variable, works backward through rules to find a chain
of rule firings that can establish a value for that variable.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sigil.ast import nodes as ast
from sigil.errors import SigilRuntimeError
from sigil.interpreter.environment import Environment
from sigil.interpreter.values import _UNBOUND, Value


@dataclass
class ProofNode:
    """A node in the backward chaining proof tree."""

    goal: str
    rule: str | None = None
    subgoals: list[ProofNode] = field(default_factory=list)
    result: bool = False
    bindings: dict[str, Value] = field(default_factory=dict)


class BackwardChainer:
    """Backward chaining engine — goal-driven rule evaluation.

    Given a set of rules, builds an index mapping target variable names
    to the rules that can set them. Then, given a goal variable, recursively
    tries to prove it by finding rules that set that variable, checking their
    conditions, and recursively proving any unbound condition variables.
    """

    MAX_DEPTH = 50

    def __init__(
        self,
        rules: list[ast.RuleDecl],
        env: Environment,
        evaluator: object,
    ) -> None:
        self._rules = rules
        self._env = env
        self._evaluator = evaluator
        self._proving: set[str] = set()
        self._index: dict[str, list[ast.RuleDecl]] = self._build_index(rules)

    @staticmethod
    def _build_index(rules: list[ast.RuleDecl]) -> dict[str, list[ast.RuleDecl]]:
        """Build a mapping from target variable names to rules that set them."""
        index: dict[str, list[ast.RuleDecl]] = {}
        for rule in rules:
            targets = BackwardChainer._extract_targets(rule.action)
            for target in targets:
                index.setdefault(target, []).append(rule)
        return index

    @staticmethod
    def _extract_targets(action: ast.Action) -> list[str]:
        """Extract variable names that an action sets."""
        if isinstance(action, ast.SetAction):
            if isinstance(action.target, ast.Identifier):
                return [action.target.name]
        elif isinstance(action, ast.BlockAction):
            targets: list[str] = []
            for stmt in action.body:
                if isinstance(stmt, ast.GivenStmt):
                    targets.append(stmt.name)
                elif isinstance(stmt, ast.BecomeStmt) and isinstance(stmt.target, ast.Identifier):
                    targets.append(stmt.target.name)
            return targets
        return []

    def query(self, goal: str, depth: int = 0) -> ProofNode:
        """Try to prove a goal variable by backward chaining."""
        node = ProofNode(goal=goal)

        # Base case: variable already has a value in the environment
        existing = self._env.get(goal)
        if existing is not _UNBOUND:
            node.result = True
            node.bindings = {goal: existing}
            return node

        # Depth limit
        if depth >= self.MAX_DEPTH:
            return node

        # Cycle detection
        if goal in self._proving:
            return node

        self._proving.add(goal)
        try:
            # Find rules that can set this goal
            candidates = self._index.get(goal, [])
            # Sort by priority (higher first)
            candidates = sorted(candidates, key=lambda r: r.priority, reverse=True)

            for rule in candidates:
                proof = self._try_rule(rule, goal, depth)
                if proof.result:
                    # Rule succeeded — update environment with proved bindings
                    for name, value in proof.bindings.items():
                        self._env = self._env.set(name, value)
                    node.rule = rule.name
                    node.subgoals = proof.subgoals
                    node.result = True
                    node.bindings = proof.bindings
                    return node

        finally:
            self._proving.discard(goal)

        return node

    def _try_rule(
        self, rule: ast.RuleDecl, goal: str, depth: int,
    ) -> ProofNode:
        """Try to prove a goal using a specific rule."""
        from sigil.interpreter.evaluator import Evaluator

        assert isinstance(self._evaluator, Evaluator)

        node = ProofNode(goal=goal, rule=rule.name)

        # Process given clauses first
        env = self._env
        for gc in rule.given_clauses:
            existing = env.get(gc.name)
            if existing is not _UNBOUND and gc.kind == "from":
                continue
            try:
                val = self._evaluator.eval_expression(gc.source, env)
                env = env.set(gc.name, val)
            except SigilRuntimeError:
                if existing is not _UNBOUND:
                    continue
                return node

        # Try to evaluate all conditions
        conditions = self._evaluator._flatten_conditions(rule.conditions)
        for cond in conditions:
            # Find unbound variables in this condition
            unbound = self._find_unbound_vars(cond, env)

            # Try to prove unbound variables first
            for var in unbound:
                subproof = self.query(var, depth + 1)
                node.subgoals.append(subproof)
                if subproof.result:
                    # Update env with proved bindings
                    for name, value in subproof.bindings.items():
                        env = env.set(name, value)
                    self._env = env

            # Now evaluate the condition
            try:
                result, _ = self._evaluator._eval_condition(cond, env)
            except SigilRuntimeError:
                return node

            if not result:
                return node

        # All conditions passed — execute the action
        try:
            action_result, env = self._evaluator._eval_action(rule.action, env)
        except Exception:
            return node

        # Collect bindings from the action
        bindings: dict[str, Value] = {}
        targets = self._extract_targets(rule.action)
        for target in targets:
            val = env.get(target)
            if val is not _UNBOUND:
                bindings[target] = val

        self._env = env
        node.result = True
        node.bindings = bindings
        return node

    def _find_unbound_vars(
        self, cond: ast.Condition, env: Environment,
    ) -> list[str]:
        """Find variable names referenced in a condition that are unbound."""
        names = self._collect_identifiers(cond)
        return [n for n in names if env.get(n) is _UNBOUND and n in self._index]

    def _collect_identifiers(self, node: object) -> list[str]:
        """Collect all Identifier names from an AST subtree."""
        names: list[str] = []
        if isinstance(node, ast.Identifier):
            names.append(node.name)
        if hasattr(node, "__dataclass_fields__"):
            for fname in node.__dataclass_fields__:
                child = getattr(node, fname)
                if isinstance(child, tuple):
                    for item in child:
                        names.extend(self._collect_identifiers(item))
                elif hasattr(child, "__dataclass_fields__"):
                    names.extend(self._collect_identifiers(child))
        return names

    @property
    def env(self) -> Environment:
        """Return the current environment (updated with proved bindings)."""
        return self._env
