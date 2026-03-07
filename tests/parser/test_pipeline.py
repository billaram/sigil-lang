"""Tests for pipeline expression parsing."""

from __future__ import annotations

from sigil.ast import nodes as ast
from sigil.lexer import tokenize
from sigil.parser import parse


def parse_source(source: str) -> ast.Program:
    tokens = tokenize(source, "<test>")
    return parse(tokens, "<test>")


def get_main_expr(source: str) -> ast.Expression:
    """Parse source with a main block and return the expression from the first given stmt."""
    program = parse_source(source)
    for decl in program.declarations:
        if isinstance(decl, ast.MainDecl):
            for stmt in decl.body:
                if isinstance(stmt, ast.GivenStmt):
                    return stmt.value
    raise AssertionError("No given statement found in main block")


class TestPipelineParsing:
    """Test pipeline operator parsing."""

    def test_parse_filter_where(self):
        src = """\
main:
  given result as items |> filter where it exceeds 10
"""
        expr = get_main_expr(src)
        assert isinstance(expr, ast.PipelineExpr)
        assert len(expr.operations) == 1
        assert expr.operations[0].kind == "filter"
        assert expr.operations[0].condition is not None

    def test_parse_sort_by_ascending(self):
        src = """\
main:
  given result as items |> sort by name ascending
"""
        expr = get_main_expr(src)
        assert isinstance(expr, ast.PipelineExpr)
        assert len(expr.operations) == 1
        assert expr.operations[0].kind == "sort"
        assert expr.operations[0].direction == "ascending"

    def test_parse_sort_by_descending(self):
        src = """\
main:
  given result as items |> sort by name descending
"""
        expr = get_main_expr(src)
        assert isinstance(expr, ast.PipelineExpr)
        assert expr.operations[0].kind == "sort"
        assert expr.operations[0].direction == "descending"

    def test_parse_sort_by_default_ascending(self):
        src = """\
main:
  given result as items |> sort by name
"""
        expr = get_main_expr(src)
        assert isinstance(expr, ast.PipelineExpr)
        assert expr.operations[0].kind == "sort"
        assert expr.operations[0].direction == "ascending"

    def test_parse_take_first(self):
        src = """\
main:
  given result as items |> take first 5
"""
        expr = get_main_expr(src)
        assert isinstance(expr, ast.PipelineExpr)
        assert expr.operations[0].kind == "take_first"
        assert len(expr.operations[0].args) == 1

    def test_parse_take_last(self):
        src = """\
main:
  given result as items |> take last 3
"""
        expr = get_main_expr(src)
        assert isinstance(expr, ast.PipelineExpr)
        assert expr.operations[0].kind == "take_last"

    def test_parse_map_to(self):
        src = """\
main:
  given result as items |> map to it + 1
"""
        expr = get_main_expr(src)
        assert isinstance(expr, ast.PipelineExpr)
        assert expr.operations[0].kind == "map"
        assert len(expr.operations[0].args) == 1

    def test_parse_chained_pipeline(self):
        src = """\
main:
  given result as items |> filter where it exceeds 10 |> sort by it descending |> take first 3
"""
        expr = get_main_expr(src)
        assert isinstance(expr, ast.PipelineExpr)
        assert len(expr.operations) == 3
        assert expr.operations[0].kind == "filter"
        assert expr.operations[1].kind == "sort"
        assert expr.operations[2].kind == "take_first"

    def test_parse_pipeline_source_is_identifier(self):
        src = """\
main:
  given result as scores |> filter where it exceeds 80
"""
        expr = get_main_expr(src)
        assert isinstance(expr, ast.PipelineExpr)
        assert isinstance(expr.source, ast.Identifier)
        assert expr.source.name == "scores"

    def test_parse_pipeline_source_is_list(self):
        src = """\
main:
  given result as [1, 2, 3] |> filter where it exceeds 1
"""
        expr = get_main_expr(src)
        assert isinstance(expr, ast.PipelineExpr)
        assert isinstance(expr.source, ast.ListExpr)

    def test_parse_pipeline_map_to_expression(self):
        src = """\
main:
  given result as items |> map to it * 2
"""
        expr = get_main_expr(src)
        assert isinstance(expr, ast.PipelineExpr)
        op = expr.operations[0]
        assert op.kind == "map"
        assert isinstance(op.args[0], ast.BinaryOp)

    def test_parse_pipeline_filter_with_is(self):
        src = """\
main:
  given result as items |> filter where status is :active
"""
        expr = get_main_expr(src)
        assert isinstance(expr, ast.PipelineExpr)
        assert expr.operations[0].kind == "filter"
