"""Tests for the Rust Rete-lite pattern matcher."""


from sigil._sigil_core import ReteNetwork


def test_create_network():
    net = ReteNetwork()
    assert net.rule_count() == 0


def test_add_rule():
    net = ReteNetwork()
    net.add_rule("rule1", 10, [("temperature", "exceeds", 100)])
    assert net.rule_count() == 1


def test_match_simple_exceeds():
    net = ReteNetwork()
    net.add_rule("high_temp", 10, [("temperature", "exceeds", 100)])
    matches = net.match_facts({"temperature": 150})
    assert len(matches) == 1
    assert matches[0] == ("high_temp", 10)


def test_no_match():
    net = ReteNetwork()
    net.add_rule("high_temp", 10, [("temperature", "exceeds", 100)])
    matches = net.match_facts({"temperature": 50})
    assert len(matches) == 0


def test_match_equality():
    net = ReteNetwork()
    net.add_rule("active", 5, [("status", "is", "active")])
    matches = net.match_facts({"status": "active"})
    assert len(matches) == 1


def test_match_multiple_conditions():
    net = ReteNetwork()
    net.add_rule(
        "alert",
        10,
        [("temperature", "exceeds", 100), ("status", "is", "active")],
    )
    matches = net.match_facts({"temperature": 150, "status": "active"})
    assert len(matches) == 1

    matches = net.match_facts({"temperature": 150, "status": "inactive"})
    assert len(matches) == 0


def test_match_multiple_rules():
    net = ReteNetwork()
    net.add_rule("rule_a", 5, [("x", "exceeds", 10)])
    net.add_rule("rule_b", 10, [("x", "exceeds", 20)])
    matches = net.match_facts({"x": 25})
    # Both match, sorted by priority (highest first)
    assert len(matches) == 2
    assert matches[0] == ("rule_b", 10)
    assert matches[1] == ("rule_a", 5)


def test_priority_sorting():
    net = ReteNetwork()
    net.add_rule("low", 1, [("x", "is", 1)])
    net.add_rule("high", 100, [("x", "is", 1)])
    net.add_rule("mid", 50, [("x", "is", 1)])
    matches = net.match_facts({"x": 1})
    assert [m[0] for m in matches] == ["high", "mid", "low"]


def test_match_less_than():
    net = ReteNetwork()
    net.add_rule("cold", 5, [("temperature", "below", 32)])
    matches = net.match_facts({"temperature": 20})
    assert len(matches) == 1


def test_match_not_equals():
    net = ReteNetwork()
    net.add_rule("not_idle", 5, [("status", "is_not", "idle")])
    matches = net.match_facts({"status": "active"})
    assert len(matches) == 1
    matches = net.match_facts({"status": "idle"})
    assert len(matches) == 0


def test_missing_fact_no_match():
    net = ReteNetwork()
    net.add_rule("rule1", 5, [("nonexistent", "is", "value")])
    matches = net.match_facts({"other": "value"})
    assert len(matches) == 0


def test_float_comparison():
    net = ReteNetwork()
    net.add_rule("rule1", 5, [("score", "exceeds", 0.5)])
    matches = net.match_facts({"score": 0.9})
    assert len(matches) == 1


def test_mixed_int_float_comparison():
    net = ReteNetwork()
    net.add_rule("rule1", 5, [("x", "exceeds", 10)])
    matches = net.match_facts({"x": 10.5})
    assert len(matches) == 1
