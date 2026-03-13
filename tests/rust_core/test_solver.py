"""Tests for the Rust constraint solver."""


from sigil._sigil_core import ConstraintSolver


def test_create_solver():
    solver = ConstraintSolver()
    assert solver.constraint_count() == 0


def test_equals_satisfied():
    solver = ConstraintSolver()
    solver.add_equals("x", 42)
    assert solver.is_satisfied({"x": 42})


def test_equals_not_satisfied():
    solver = ConstraintSolver()
    solver.add_equals("x", 42)
    assert not solver.is_satisfied({"x": 10})


def test_greater_than():
    solver = ConstraintSolver()
    solver.add_greater_than("temp", 100.0)
    assert solver.is_satisfied({"temp": 150})
    assert not solver.is_satisfied({"temp": 50})


def test_less_than():
    solver = ConstraintSolver()
    solver.add_less_than("score", 0.5)
    assert solver.is_satisfied({"score": 0.3})
    assert not solver.is_satisfied({"score": 0.8})


def test_between():
    solver = ConstraintSolver()
    solver.add_between("age", 18.0, 65.0)
    assert solver.is_satisfied({"age": 30})
    assert solver.is_satisfied({"age": 18})
    assert solver.is_satisfied({"age": 65})
    assert not solver.is_satisfied({"age": 10})
    assert not solver.is_satisfied({"age": 70})


def test_not_equals():
    solver = ConstraintSolver()
    solver.add_not_equals("status", "idle")
    assert solver.is_satisfied({"status": "active"})
    assert not solver.is_satisfied({"status": "idle"})


def test_one_of():
    solver = ConstraintSolver()
    solver.add_one_of("color", ["red", "green", "blue"])
    assert solver.is_satisfied({"color": "red"})
    assert not solver.is_satisfied({"color": "yellow"})


def test_multiple_constraints():
    solver = ConstraintSolver()
    solver.add_greater_than("age", 18.0)
    solver.add_less_than("age", 65.0)
    solver.add_equals("active", True)
    assert solver.is_satisfied({"age": 30, "active": True})
    assert not solver.is_satisfied({"age": 30, "active": False})
    assert not solver.is_satisfied({"age": 10, "active": True})


def test_check_returns_violations():
    solver = ConstraintSolver()
    solver.add_greater_than("x", 10.0)
    solver.add_equals("y", "hello")
    violations = solver.check({"x": 5, "y": "hello"})
    assert len(violations) == 1
    assert violations[0][0] == "x"


def test_unbound_variable():
    solver = ConstraintSolver()
    solver.add_equals("x", 42)
    violations = solver.check({})
    assert len(violations) == 1
    assert "not bound" in violations[0][1]


def test_constraint_count():
    solver = ConstraintSolver()
    solver.add_equals("x", 1)
    solver.add_greater_than("y", 0.0)
    solver.add_between("z", 0.0, 100.0)
    assert solver.constraint_count() == 3
