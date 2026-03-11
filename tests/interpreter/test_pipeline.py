"""Tests for pipeline expression evaluation."""

from __future__ import annotations

import pytest

from sigil.errors import SigilRuntimeError
from sigil.interpreter.evaluator import evaluate
from sigil.lexer import tokenize
from sigil.parser import parse


def run(source: str, input_data=None):
    tokens = tokenize(source, "<test>")
    program = parse(tokens, "<test>")
    return evaluate(program, input_data)


class TestPipelineEvaluation:
    """Test pipeline operator evaluation."""

    def test_filter_numbers(self):
        src = """\
main:
  given nums as [1, 5, 10, 15, 20]
  given big as nums |> filter where it exceeds 8
  print(len(big))
"""
        result, trace = run(src)
        assert trace.output_lines == ["3"]

    def test_filter_empty_result(self):
        src = """\
main:
  given nums as [1, 2, 3]
  given big as nums |> filter where it exceeds 100
  print(len(big))
"""
        result, trace = run(src)
        assert trace.output_lines == ["0"]

    def test_filter_records(self):
        src = """\
main:
  given people as [{name: "Alice", age: 30}, {name: "Bob", age: 20}]
  given adults as people |> filter where age exceeds 25
  print(len(adults))
"""
        result, trace = run(src)
        assert trace.output_lines == ["1"]

    def test_sort_ascending(self):
        src = """\
main:
  given nums as [3, 1, 4, 1, 5]
  given sorted_nums as nums |> sort by it ascending
  print(sorted_nums)
"""
        result, trace = run(src)
        assert trace.output_lines == ["[1, 1, 3, 4, 5]"]

    def test_sort_descending(self):
        src = """\
main:
  given nums as [3, 1, 4, 1, 5]
  given sorted_nums as nums |> sort by it descending
  print(sorted_nums)
"""
        result, trace = run(src)
        assert trace.output_lines == ["[5, 4, 3, 1, 1]"]

    def test_sort_records_by_field(self):
        src = """\
main:
  given people as [{name: "Charlie", age: 25}, {name: "Alice", age: 30}, {name: "Bob", age: 20}]
  given by_age as people |> sort by age ascending
  print(len(by_age))
"""
        result, trace = run(src)
        assert trace.output_lines == ["3"]

    def test_take_first(self):
        src = """\
main:
  given nums as [10, 20, 30, 40, 50]
  given first3 as nums |> take first 3
  print(first3)
"""
        result, trace = run(src)
        assert trace.output_lines == ["[10, 20, 30]"]

    def test_take_last(self):
        src = """\
main:
  given nums as [10, 20, 30, 40, 50]
  given last2 as nums |> take last 2
  print(last2)
"""
        result, trace = run(src)
        assert trace.output_lines == ["[40, 50]"]

    def test_map_to_expression(self):
        src = """\
main:
  given nums as [1, 2, 3, 4, 5]
  given doubled as nums |> map to it * 2
  print(doubled)
"""
        result, trace = run(src)
        assert trace.output_lines == ["[2, 4, 6, 8, 10]"]

    def test_map_to_field(self):
        src = """\
main:
  given people as [{name: "Alice", age: 30}, {name: "Bob", age: 20}]
  given ages as people |> map to age
  print(ages)
"""
        result, trace = run(src)
        assert trace.output_lines == ["[30, 20]"]

    def test_chained_pipeline(self):
        src = """\
main:
  given nums as [1, 5, 10, 15, 20, 25]
  given result as nums |> filter where it exceeds 8 |> sort by it descending |> take first 3
  print(result)
"""
        result, trace = run(src)
        assert trace.output_lines == ["[25, 20, 15]"]

    def test_pipeline_empty_list(self):
        src = """\
main:
  given nums as []
  given result as nums |> filter where it exceeds 0
  print(len(result))
"""
        result, trace = run(src)
        assert trace.output_lines == ["0"]

    def test_pipeline_non_list_source_error(self):
        src = """\
main:
  given x as 42
  given result as x |> filter where it exceeds 0
"""
        with pytest.raises(SigilRuntimeError, match="Pipeline source must be a list"):
            run(src)

    def test_pipeline_in_compute(self):
        src = """\
compute top_scores from scores, n: Number returns Number:
  given result as scores |> filter where it exceeds 80 |> sort by it descending |> take first n
  return result

main:
  given scores as [75, 92, 88, 64, 95, 71, 83]
  given top as top_scores(scores, 3)
  print(top)
"""
        result, trace = run(src)
        assert trace.output_lines == ["[95, 92, 88]"]

    def test_pipeline_filter_with_symbol(self):
        src = """\
main:
  given items as [{name: "A", status: :active}, {name: "B", status: :inactive}]
  given active as items |> filter where status is :active
  print(len(active))
"""
        result, trace = run(src)
        assert trace.output_lines == ["1"]

    def test_pipeline_map_arithmetic(self):
        src = """\
main:
  given nums as [10, 20, 30]
  given result as nums |> map to it + 5
  print(result)
"""
        result, trace = run(src)
        assert trace.output_lines == ["[15, 25, 35]"]

    def test_pipeline_take_more_than_available(self):
        src = """\
main:
  given nums as [1, 2, 3]
  given result as nums |> take first 10
  print(result)
"""
        result, trace = run(src)
        assert trace.output_lines == ["[1, 2, 3]"]
