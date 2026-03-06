"""Tests for Sigil interpreter environment."""

from sigil.interpreter.environment import Environment
from sigil.interpreter.values import _UNBOUND


class TestEnvironment:
    def test_empty_env(self):
        env = Environment()
        assert env.get("x") is _UNBOUND

    def test_set_and_get(self):
        env = Environment()
        env2 = env.set("x", 42)
        assert env2.get("x") == 42
        assert env.get("x") is _UNBOUND  # original unchanged

    def test_has(self):
        env = Environment({"x": 1})
        assert env.has("x")
        assert not env.has("y")

    def test_parent_lookup(self):
        parent = Environment({"x": 1})
        child = parent.extend({"y": 2})
        assert child.get("x") == 1
        assert child.get("y") == 2

    def test_child_shadows_parent(self):
        parent = Environment({"x": 1})
        child = parent.extend({"x": 99})
        assert child.get("x") == 99
        assert parent.get("x") == 1

    def test_set_returns_new_env(self):
        env = Environment({"x": 1})
        env2 = env.set("y", 2)
        assert env2 is not env
        assert env2.get("y") == 2

    def test_extend_creates_child(self):
        parent = Environment({"a": 1})
        child = parent.extend({"b": 2})
        assert child.has("a")
        assert child.has("b")

    def test_mutate_in_place(self):
        env = Environment({"x": 1})
        env.mutate("x", 99)
        assert env.get("x") == 99

    def test_mutate_walks_parent(self):
        parent = Environment({"x": 1})
        child = parent.extend({"y": 2})
        child.mutate("x", 99)
        assert parent.get("x") == 99

    def test_mutate_creates_binding(self):
        env = Environment()
        env.mutate("z", 42)
        assert env.get("z") == 42

    def test_all_bindings(self):
        parent = Environment({"a": 1})
        child = parent.extend({"b": 2, "a": 3})
        bindings = child.all_bindings()
        assert bindings == {"a": 3, "b": 2}

    def test_deep_scope_chain(self):
        env = Environment({"level": 0})
        for i in range(1, 5):
            env = env.extend({f"level{i}": i})
        assert env.get("level") == 0
        assert env.get("level4") == 4
