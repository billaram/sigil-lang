"""Unit tests for the Sigil parser."""

import pytest

from sigil.ast import nodes as ast
from sigil.errors import SigilParseError
from sigil.lexer import tokenize
from sigil.parser import parse

# --- Helper ---

def parse_source(source: str) -> ast.Program:
    tokens = tokenize(source)
    return parse(tokens)


def first_decl(source: str) -> ast.Declaration:
    program = parse_source(source)
    return program.declarations[0]


# ============================================================
# Module Declarations
# ============================================================

class TestModuleDecl:
    def test_simple_module(self):
        program = parse_source("module my_module")
        assert program.module is not None
        assert program.module.path == "my_module"

    def test_dotted_module(self):
        program = parse_source("module examples.temperature")
        assert program.module is not None
        assert program.module.path == "examples.temperature"

    def test_no_module(self):
        program = parse_source("define x as 42")
        assert program.module is None


# ============================================================
# Import Declarations
# ============================================================

class TestImports:
    def test_sigil_import(self):
        program = parse_source("import sigil.math")
        assert len(program.imports) == 1
        imp = program.imports[0]
        assert imp.kind == "sigil"
        assert imp.source == "sigil.math"

    def test_python_import(self):
        program = parse_source("import python numpy as np")
        imp = program.imports[0]
        assert imp.kind == "python"
        assert imp.source == "numpy"
        assert imp.alias == "np"

    def test_rust_import(self):
        program = parse_source("import rust sigil_core::solver")
        imp = program.imports[0]
        assert imp.kind == "rust"
        assert imp.source == "sigil_core::solver"

    def test_from_import(self):
        program = parse_source("from sigil.math import mean, median")
        imp = program.imports[0]
        assert imp.kind == "sigil"
        assert imp.source == "sigil.math"
        assert imp.names == ("mean", "median")


# ============================================================
# Type Declarations
# ============================================================

class TestTypeDecl:
    def test_record_type(self):
        decl = first_decl("type Person is record:\n  name: Text\n  age: Number")
        assert isinstance(decl, ast.TypeDecl)
        assert decl.name == "Person"
        body = decl.body
        assert isinstance(body, ast.RecordBody)
        assert len(body.fields) == 2
        assert body.fields[0].name == "name"
        assert body.fields[1].name == "age"

    def test_enum_type(self):
        decl = first_decl("type Decision is one of:\n  approved with rate: Number\n  denied\n")
        assert isinstance(decl, ast.TypeDecl)
        body = decl.body
        assert isinstance(body, ast.EnumBody)
        assert len(body.variants) == 2
        assert body.variants[0].name == "approved"
        assert len(body.variants[0].fields) == 1
        assert body.variants[1].name == "denied"
        assert len(body.variants[1].fields) == 0

    def test_alias_type(self):
        decl = first_decl("type Age is Number")
        assert isinstance(decl, ast.TypeDecl)
        body = decl.body
        assert isinstance(body, ast.AliasType)

    def test_generic_type(self):
        decl = first_decl(
            "type Result[T] is one of:\n  success with value: Text\n  failure\n"
        )
        assert isinstance(decl, ast.TypeDecl)
        assert decl.params == ("T",)

    def test_list_type_ref(self):
        decl = first_decl("type Names is list of Text")
        assert isinstance(decl, ast.TypeDecl)
        body = decl.body
        assert isinstance(body, ast.AliasType)
        assert isinstance(body.target, ast.ListType)


# ============================================================
# Constant Declarations
# ============================================================

class TestConstDecl:
    def test_number_constant(self):
        decl = first_decl("define MAX_TEMP as 100")
        assert isinstance(decl, ast.ConstDecl)
        assert decl.name == "MAX_TEMP"
        assert isinstance(decl.value, ast.Literal)
        assert decl.value.value == 100

    def test_string_constant(self):
        decl = first_decl('define MSG as "hello"')
        assert isinstance(decl, ast.ConstDecl)
        assert decl.value.value == "hello"

    def test_list_constant(self):
        decl = first_decl("define ITEMS as [1, 2, 3]")
        assert isinstance(decl, ast.ConstDecl)
        assert isinstance(decl.value, ast.ListExpr)
        assert len(decl.value.elements) == 3

    def test_float_constant(self):
        decl = first_decl("define PI as 3.14")
        assert isinstance(decl, ast.ConstDecl)
        assert decl.value.value == 3.14


# ============================================================
# Rule Declarations
# ============================================================

class TestRuleDecl:
    def test_simple_rule(self):
        decl = first_decl("rule my_rule:\n  when true\n  then alert\n")
        assert isinstance(decl, ast.RuleDecl)
        assert decl.name == "my_rule"

    def test_rule_with_priority(self):
        decl = first_decl("rule my_rule with priority 10:\n  when true\n  then alert\n")
        assert isinstance(decl, ast.RuleDecl)
        assert decl.priority == 10

    def test_rule_with_explain(self):
        decl = first_decl(
            'rule my_rule:\n  when true\n  then alert\n  explain "reason"\n'
        )
        assert isinstance(decl, ast.RuleDecl)
        assert decl.explain == "reason"

    def test_rule_exceeds_condition(self):
        decl = first_decl("rule r:\n  when x exceeds 100\n  then alert\n")
        assert isinstance(decl, ast.RuleDecl)
        cond = decl.conditions[0]
        assert isinstance(cond, ast.ComparisonCond)
        assert cond.operator == "exceeds"

    def test_rule_is_below_condition(self):
        decl = first_decl("rule r:\n  when x is below 50\n  then alert\n")
        cond = decl.conditions[0]
        assert isinstance(cond, ast.ComparisonCond)
        assert cond.operator == "is below"

    def test_rule_is_between_condition(self):
        decl = first_decl("rule r:\n  when x is between 10 and 50\n  then alert\n")
        cond = decl.conditions[0]
        assert isinstance(cond, ast.ComparisonCond)
        assert cond.operator == "is between"
        assert cond.right2 is not None

    def test_rule_is_at_least_condition(self):
        decl = first_decl("rule r:\n  when x is at least 100\n  then alert\n")
        cond = decl.conditions[0]
        assert isinstance(cond, ast.ComparisonCond)
        assert cond.operator == "is at least"

    def test_rule_is_at_most_condition(self):
        decl = first_decl("rule r:\n  when x is at most 100\n  then alert\n")
        cond = decl.conditions[0]
        assert isinstance(cond, ast.ComparisonCond)
        assert cond.operator == "is at most"

    def test_rule_is_symbol(self):
        decl = first_decl("rule r:\n  when status is :active\n  then alert\n")
        cond = decl.conditions[0]
        assert isinstance(cond, ast.ComparisonCond)
        assert cond.operator == "is"

    def test_rule_is_true(self):
        decl = first_decl("rule r:\n  when flag is true\n  then alert\n")
        cond = decl.conditions[0]
        assert isinstance(cond, ast.BooleanCond)
        assert cond.value is True

    def test_rule_is_not_true(self):
        decl = first_decl("rule r:\n  when flag is not true\n  then alert\n")
        cond = decl.conditions[0]
        assert isinstance(cond, ast.BooleanCond)
        assert cond.value is False

    def test_rule_membership_in(self):
        decl = first_decl("rule r:\n  when x in items\n  then alert\n")
        cond = decl.conditions[0]
        assert isinstance(cond, ast.MembershipCond)
        assert cond.negated is False

    def test_rule_is_in(self):
        decl = first_decl("rule r:\n  when x is in items\n  then alert\n")
        cond = decl.conditions[0]
        assert isinstance(cond, ast.MembershipCond)

    def test_rule_and_conditions(self):
        decl = first_decl(
            "rule r:\n  when x exceeds 10\n  and y is true\n  then alert\n"
        )
        assert isinstance(decl, ast.RuleDecl)
        cond = decl.conditions[0]
        assert isinstance(cond, ast.CompoundCond)
        assert cond.operator == "and"

    def test_rule_or_conditions(self):
        decl = first_decl(
            "rule r:\n  when x exceeds 10\n  or y is true\n  then alert\n"
        )
        cond = decl.conditions[0]
        assert isinstance(cond, ast.CompoundCond)
        assert cond.operator == "or"

    def test_rule_simple_action(self):
        decl = first_decl("rule r:\n  when true\n  then alert\n")
        assert isinstance(decl.action, ast.SimpleAction)
        assert decl.action.name == "alert"

    def test_rule_set_action(self):
        decl = first_decl("rule r:\n  when true\n  then flag is true\n")
        assert isinstance(decl.action, ast.SetAction)

    def test_rule_block_action(self):
        decl = first_decl(
            "rule r:\n  when true\n  then:\n    return 42\n"
        )
        assert isinstance(decl.action, ast.BlockAction)
        assert len(decl.action.body) == 1

    def test_rule_with_trace(self):
        decl = first_decl(
            'rule r:\n  when true\n  then alert\n  trace:\n    category :lending\n'
        )
        assert isinstance(decl, ast.RuleDecl)
        assert len(decl.trace) == 1
        assert decl.trace[0].name == "category"

    def test_space_based_field_access(self):
        decl = first_decl(
            "rule r:\n  when reading temperature exceeds 100\n  then alert\n"
        )
        cond = decl.conditions[0]
        assert isinstance(cond, ast.ComparisonCond)
        left = cond.left
        assert isinstance(left, ast.FieldAccess)
        assert left.field == "temperature"
        assert isinstance(left.object, ast.Identifier)
        assert left.object.name == "reading"

    def test_is_not_assigned(self):
        decl = first_decl(
            "rule r:\n  when status is not assigned\n  then alert\n"
        )
        cond = decl.conditions[0]
        assert isinstance(cond, ast.IsAssignedCond)
        assert cond.negated is True


# ============================================================
# Compute Declarations
# ============================================================

class TestComputeDecl:
    def test_simple_compute(self):
        decl = first_decl(
            "compute add from a: Number, b: Number returns Number:\n  return a + b\n"
        )
        assert isinstance(decl, ast.ComputeDecl)
        assert decl.name == "add"
        assert len(decl.params) == 2
        assert decl.params[0].name == "a"
        assert decl.return_type is not None

    def test_parameterless_compute(self):
        decl = first_decl(
            "compute get_items returns list of Text:\n  return []\n"
        )
        assert isinstance(decl, ast.ComputeDecl)
        assert len(decl.params) == 0

    def test_compute_with_given(self):
        decl = first_decl(
            "compute calc from x: Number:\n  given y as x * 2\n  return y\n"
        )
        assert isinstance(decl, ast.ComputeDecl)
        body = decl.body
        assert isinstance(body[0], ast.GivenStmt)

    def test_compute_with_if(self):
        source = (
            "compute categorize from v: Number:\n"
            "  if v exceeds 100:\n"
            "    return :high\n"
            "  else:\n"
            "    return :low\n"
        )
        decl = first_decl(source)
        assert isinstance(decl, ast.ComputeDecl)
        assert isinstance(decl.body[0], ast.IfStmt)


# ============================================================
# Neural Declarations
# ============================================================

class TestNeuralDecl:
    def test_neural_declaration(self):
        source = (
            "neural classify from text: Text:\n"
            '  model "classifier-v2"\n'
            "  returns Symbol\n"
            "  confidence_threshold 0.85\n"
            "  fallback to :unknown\n"
        )
        decl = first_decl(source)
        assert isinstance(decl, ast.NeuralDecl)
        assert decl.name == "classify"
        assert decl.param_name == "text"
        assert len(decl.fields) == 4

    def test_neural_with_using(self):
        source = (
            "neural predict from x: Number:\n"
            "  using python model.predict\n"
            "  returns Number\n"
        )
        decl = first_decl(source)
        assert isinstance(decl, ast.NeuralDecl)
        field_names = [f.name for f in decl.fields]
        assert "using" in field_names


# ============================================================
# Main Declaration
# ============================================================

class TestMainDecl:
    def test_simple_main(self):
        source = "main:\n  given x from input\n  evaluate all rules with x\n"
        decl = first_decl(source)
        assert isinstance(decl, ast.MainDecl)
        assert len(decl.body) == 2

    def test_main_with_trace(self):
        source = (
            "main:\n"
            "  given x from input\n"
            "  trace:\n"
            "    category :test\n"
        )
        decl = first_decl(source)
        assert isinstance(decl, ast.MainDecl)
        assert len(decl.trace) == 1


# ============================================================
# Expressions
# ============================================================

class TestExpressions:
    def test_number_literal(self):
        decl = first_decl("define x as 42")
        assert isinstance(decl.value, ast.Literal)
        assert decl.value.value == 42

    def test_float_literal(self):
        decl = first_decl("define x as 3.14")
        assert decl.value.value == 3.14

    def test_string_literal(self):
        decl = first_decl('define x as "hello"')
        assert decl.value.value == "hello"

    def test_bool_literal(self):
        decl = first_decl("define x as true")
        assert decl.value.value is True

    def test_none_literal(self):
        decl = first_decl("define x as none")
        assert decl.value.value is None

    def test_symbol_literal(self):
        decl = first_decl("define x as :active")
        assert isinstance(decl.value, ast.SymbolLit)
        assert decl.value.name == "active"

    def test_list_literal(self):
        decl = first_decl("define x as [1, 2, 3]")
        assert isinstance(decl.value, ast.ListExpr)
        assert len(decl.value.elements) == 3

    def test_symbol_list(self):
        decl = first_decl("define x as [:a, :b, :c]")
        assert isinstance(decl.value, ast.ListExpr)
        assert all(isinstance(e, ast.SymbolLit) for e in decl.value.elements)

    def test_arithmetic(self):
        decl = first_decl("define x as 1 + 2 * 3")
        assert isinstance(decl.value, ast.BinaryOp)
        assert decl.value.operator == "+"
        # Right should be 2*3 (higher precedence)
        assert isinstance(decl.value.right, ast.BinaryOp)
        assert decl.value.right.operator == "*"

    def test_parenthesized_expression(self):
        decl = first_decl("define x as (1 + 2) * 3")
        assert isinstance(decl.value, ast.BinaryOp)
        assert decl.value.operator == "*"

    def test_field_access(self):
        decl = first_decl("define x as obj.field")
        assert isinstance(decl.value, ast.FieldAccess)
        assert decl.value.field == "field"

    def test_function_call(self):
        decl = first_decl("define x as foo(1, 2)")
        assert isinstance(decl.value, ast.FuncCall)
        assert len(decl.value.args) == 2

    def test_method_call(self):
        decl = first_decl("define x as math.max(a, b)")
        assert isinstance(decl.value, ast.FuncCall)
        assert isinstance(decl.value.function, ast.FieldAccess)

    def test_unary_minus(self):
        decl = first_decl("define x as -42")
        assert isinstance(decl.value, ast.UnaryOp)
        assert decl.value.operator == "-"

    def test_empty_list_expr(self):
        decl = first_decl("define x as []")
        assert isinstance(decl.value, ast.ListExpr)
        assert len(decl.value.elements) == 0


# ============================================================
# Statements
# ============================================================

class TestStatements:
    def test_given_as(self):
        decl = first_decl("compute f from x: Number:\n  given y as x + 1\n  return y\n")
        stmt = decl.body[0]
        assert isinstance(stmt, ast.GivenStmt)
        assert stmt.kind == "as"

    def test_given_from(self):
        decl = first_decl("compute f from x: Number:\n  given y from load()\n  return y\n")
        stmt = decl.body[0]
        assert isinstance(stmt, ast.GivenStmt)
        assert stmt.kind == "from"

    def test_return_statement(self):
        decl = first_decl("compute f from x: Number:\n  return x + 1\n")
        stmt = decl.body[0]
        assert isinstance(stmt, ast.ReturnStmt)

    def test_becomes_statement(self):
        source = (
            "compute f from x: Number:\n"
            "  given y as 0\n"
            '  y becomes y + ["item"]\n'
            "  return y\n"
        )
        decl = first_decl(source)
        assert isinstance(decl.body[1], ast.BecomeStmt)

    def test_for_each_statement(self):
        source = (
            "compute f from items: List:\n"
            "  for each item in items:\n"
            "    return item\n"
        )
        decl = first_decl(source)
        stmt = decl.body[0]
        assert isinstance(stmt, ast.ForStmt)
        assert stmt.variable == "item"

    def test_evaluate_statement(self):
        source = "main:\n  evaluate all rules with data\n"
        decl = first_decl(source)
        stmt = decl.body[0]
        assert isinstance(stmt, ast.EvaluateStmt)
        assert stmt.target == "all rules"


# ============================================================
# Error Cases
# ============================================================

class TestParserErrors:
    def test_missing_colon_after_rule(self):
        with pytest.raises(SigilParseError, match="Expected COLON"):
            parse_source("rule my_rule\n  when true\n  then alert\n")

    def test_missing_when_in_rule(self):
        with pytest.raises(SigilParseError, match="Expected WHEN"):
            parse_source("rule my_rule:\n  then alert\n")

    def test_unexpected_top_level(self):
        with pytest.raises(SigilParseError, match="Unexpected token"):
            parse_source("42")


# ============================================================
# Integration: Parse Full Example Files
# ============================================================

class TestExampleFiles:
    def test_hello_sigil(self, hello_source):
        tokens = tokenize(hello_source, "hello.sigil")
        program = parse(tokens, "hello.sigil")
        assert program.module is None
        assert len(program.declarations) == 2
        assert isinstance(program.declarations[0], ast.ConstDecl)
        assert isinstance(program.declarations[1], ast.RuleDecl)

    def test_temperature_sigil(self, temperature_source):
        tokens = tokenize(temperature_source, "temperature.sigil")
        program = parse(tokens, "temperature.sigil")
        assert program.module is not None
        assert program.module.path == "examples.temperature"
        # 1 type + 3 constants + 4 rules = 8
        assert len(program.declarations) == 8
        rules = [d for d in program.declarations if isinstance(d, ast.RuleDecl)]
        assert len(rules) == 4
        assert rules[0].priority == 100  # emergency_shutdown

    def test_loan_eligibility_sigil(self, loan_source):
        tokens = tokenize(loan_source, "loan_eligibility.sigil")
        program = parse(tokens, "loan_eligibility.sigil")
        assert program.module is not None
        assert len(program.imports) == 1
        # Has types, constants, rules, compute blocks
        types = [d for d in program.declarations if isinstance(d, ast.TypeDecl)]
        rules = [d for d in program.declarations if isinstance(d, ast.RuleDecl)]
        computes = [d for d in program.declarations if isinstance(d, ast.ComputeDecl)]
        assert len(types) == 2  # Applicant, Decision
        assert len(rules) >= 7
        assert len(computes) >= 1

    def test_medical_triage_sigil(self, triage_source):
        tokens = tokenize(triage_source, "medical_triage.sigil")
        program = parse(tokens, "medical_triage.sigil")
        assert program.module is not None
        neurals = [d for d in program.declarations if isinstance(d, ast.NeuralDecl)]
        assert len(neurals) == 1
        mains = [d for d in program.declarations if isinstance(d, ast.MainDecl)]
        assert len(mains) == 1

    def test_compliance_checker_sigil(self, compliance_source):
        tokens = tokenize(compliance_source, "compliance_checker.sigil")
        program = parse(tokens, "compliance_checker.sigil")
        assert program.module is not None
        rules = [d for d in program.declarations if isinstance(d, ast.RuleDecl)]
        assert len(rules) >= 5
        # Verify trace blocks on some rules
        rules_with_trace = [r for r in rules if r.trace]
        assert len(rules_with_trace) >= 1

    def test_all_examples_parse(
        self, hello_source, temperature_source, loan_source,
        triage_source, compliance_source,
    ):
        """All 5 example files parse without errors."""
        for name, source in [
            ("hello", hello_source),
            ("temperature", temperature_source),
            ("loan", loan_source),
            ("triage", triage_source),
            ("compliance", compliance_source),
        ]:
            tokens = tokenize(source, f"{name}.sigil")
            program = parse(tokens, f"{name}.sigil")
            assert isinstance(program, ast.Program), f"{name} should produce a Program"
            assert len(program.declarations) > 0, f"{name} should have declarations"


# ============================================================
# Query Statements
# ============================================================

class TestQueryStmt:
    def test_simple_query(self):
        decl = first_decl("""
main:
  query eligible
""")
        assert isinstance(decl, ast.MainDecl)
        stmt = decl.body[0]
        assert isinstance(stmt, ast.QueryStmt)
        assert stmt.goal == "eligible"
        assert stmt.argument is None

    def test_query_with_argument(self):
        decl = first_decl("""
main:
  query eligible with "test"
""")
        stmt = decl.body[0]
        assert isinstance(stmt, ast.QueryStmt)
        assert stmt.goal == "eligible"
        assert isinstance(stmt.argument, ast.Literal)
        assert stmt.argument.value == "test"

    def test_query_with_expression_argument(self):
        decl = first_decl("""
main:
  query result with x + 1
""")
        stmt = decl.body[0]
        assert isinstance(stmt, ast.QueryStmt)
        assert isinstance(stmt.argument, ast.BinaryOp)

    def test_query_in_compute(self):
        decl = first_decl("""
compute check from x: Number returns Number:
  query eligible
  return x
""")
        assert isinstance(decl, ast.ComputeDecl)
        assert isinstance(decl.body[0], ast.QueryStmt)


# ============================================================
# Temporal Constraints
# ============================================================

class TestTemporalConstraint:
    def test_rule_with_temporal(self):
        decl = first_decl("""
rule temp_check with priority 5:
  when temperature exceeds 100
  within 30 seconds
  then alert is true
""")
        assert isinstance(decl, ast.RuleDecl)
        assert decl.temporal is not None
        assert isinstance(decl.temporal, ast.TemporalConstraint)
        assert isinstance(decl.temporal.duration, ast.Literal)
        assert decl.temporal.duration.value == 30
        assert decl.temporal.unit == "seconds"

    def test_rule_without_temporal(self):
        decl = first_decl("""
rule basic:
  when x is true
  then y is true
""")
        assert isinstance(decl, ast.RuleDecl)
        assert decl.temporal is None

    def test_temporal_with_minutes(self):
        decl = first_decl("""
rule monitor:
  when status is :active
  within 5 minutes
  then checked is true
""")
        assert decl.temporal is not None
        assert decl.temporal.duration.value == 5
        assert decl.temporal.unit == "minutes"

    def test_number_literal_with_unit(self):
        decl = first_decl("define MAX_TEMP as 100 degrees")
        assert isinstance(decl, ast.ConstDecl)
        assert isinstance(decl.value, ast.Literal)
        assert decl.value.value == 100
        assert decl.value.unit == "degrees"
