"""Tests for the Sigil interactive REPL."""

from sigil.interpreter.repl import ReplSession, needs_continuation

# ============================================================
# ReplSession — core processing
# ============================================================


class TestReplSessionBasics:
    def test_empty_input(self):
        session = ReplSession()
        out = session.process_input("")
        assert out.lines == []
        assert not out.show_result

    def test_define_constant(self):
        session = ReplSession()
        out = session.process_input("define X as 42")
        assert not out.show_result
        bindings = session.env.all_bindings()
        assert bindings["X"] == 42

    def test_expression_shows_result(self):
        session = ReplSession()
        session.process_input("define X as 42")
        out = session.process_input("X + 10")
        assert out.show_result
        assert out.result == 52

    def test_given_statement_no_result(self):
        session = ReplSession()
        out = session.process_input("given x as 42")
        assert not out.show_result
        bindings = session.env.all_bindings()
        assert bindings["x"] == 42

    def test_persistent_env(self):
        """Bindings persist across inputs."""
        session = ReplSession()
        session.process_input("define A as 10")
        session.process_input("define B as 20")
        out = session.process_input("A + B")
        assert out.result == 30

    def test_arithmetic_expression(self):
        session = ReplSession()
        out = session.process_input("2 + 3")
        assert out.show_result
        assert out.result == 5

    def test_string_expression(self):
        session = ReplSession()
        out = session.process_input('"hello"')
        assert out.show_result
        assert out.result == "hello"

    def test_list_expression(self):
        session = ReplSession()
        out = session.process_input("[1, 2, 3]")
        assert out.show_result
        assert out.result == [1, 2, 3]

    def test_print_output(self):
        session = ReplSession()
        session.process_input("define msg as \"hello world\"")
        out = session.process_input("print(msg)")
        assert "hello world" in out.lines


# ============================================================
# Declarations
# ============================================================


class TestReplDeclarations:
    def test_type_declaration(self):
        session = ReplSession()
        out = session.process_input("type Person is record:\n  name: Text\n  age: Number")
        assert not out.show_result
        assert "Person" in session.type_defs

    def test_compute_declaration(self):
        session = ReplSession()
        session.process_input(
            "compute double from x: Number returns Number:\n  return x * 2"
        )
        assert "double" in session.compute_funcs

    def test_compute_call(self):
        session = ReplSession()
        session.process_input(
            "compute double from x: Number returns Number:\n  return x * 2"
        )
        out = session.process_input("double(21)")
        assert out.result == 42

    def test_rule_declaration(self):
        session = ReplSession()
        session.process_input(
            "rule greet:\n  when true\n  then greeting is \"hello\""
        )
        assert len(session.rules) == 1
        assert session.rules[0].name == "greet"


# ============================================================
# Special commands
# ============================================================


class TestReplCommands:
    def test_env_empty(self):
        session = ReplSession()
        out = session.process_input(":env")
        assert any("empty" in line for line in out.lines)

    def test_env_with_bindings(self):
        session = ReplSession()
        session.process_input("define X as 42")
        out = session.process_input(":env")
        assert any("X" in line and "42" in line for line in out.lines)

    def test_rules_empty(self):
        session = ReplSession()
        out = session.process_input(":rules")
        assert any("no rules" in line for line in out.lines)

    def test_funcs_empty(self):
        session = ReplSession()
        out = session.process_input(":funcs")
        assert any("no functions" in line for line in out.lines)

    def test_types_empty(self):
        session = ReplSession()
        out = session.process_input(":types")
        assert any("no types" in line for line in out.lines)

    def test_trace_toggle(self):
        session = ReplSession()
        assert not session.trace_on
        out = session.process_input(":trace")
        assert session.trace_on
        assert any("on" in line for line in out.lines)
        out = session.process_input(":trace")
        assert not session.trace_on
        assert any("off" in line for line in out.lines)

    def test_reset(self):
        session = ReplSession()
        session.process_input("define X as 42")
        session.process_input(":reset")
        bindings = session.env.all_bindings()
        assert not bindings

    def test_help(self):
        session = ReplSession()
        out = session.process_input(":help")
        assert len(out.lines) > 3
        assert any(":env" in line for line in out.lines)

    def test_unknown_command(self):
        session = ReplSession()
        out = session.process_input(":foobar")
        assert any("Unknown command" in line for line in out.lines)


# ============================================================
# Error handling
# ============================================================


class TestReplErrors:
    def test_lex_error_caught(self):
        session = ReplSession()
        out = session.process_input("@@@")
        assert any("Error" in line for line in out.lines)

    def test_parse_error_caught(self):
        session = ReplSession()
        out = session.process_input("define")
        assert any("Error" in line for line in out.lines)

    def test_error_does_not_corrupt_state(self):
        """After an error, previous state should be intact."""
        session = ReplSession()
        session.process_input("define X as 42")
        session.process_input("@@@")  # error
        out = session.process_input("X + 1")
        assert out.result == 43


# ============================================================
# Multi-line detection
# ============================================================


class TestMultiLineDetection:
    def test_colon_needs_continuation(self):
        assert needs_continuation("rule foo:")

    def test_unbalanced_brackets(self):
        assert needs_continuation("define X as [1, 2,")

    def test_unbalanced_parens(self):
        assert needs_continuation("add(1,")

    def test_complete_input(self):
        assert not needs_continuation("define X as 42")

    def test_balanced_brackets(self):
        assert not needs_continuation("[1, 2, 3]")

    def test_empty_input(self):
        assert not needs_continuation("")
