"""Thin wrapper: compile Sigil AST to bytecode, execute in Rust VM."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sigil.vm.compiler import VMCompiler

if TYPE_CHECKING:
    from sigil.ast import Program
    from sigil.interpreter.values import Value


def compile_and_run(
    program: Program,
    input_data: dict[str, Value] | None = None,
) -> tuple[Value, list[str], dict[str, Value]]:
    """Compile a Sigil program and execute it in the Rust VM.

    Returns (result, output_lines, bindings).
    """
    from sigil._sigil_core import SigilVM
    from sigil.interpreter.values import Record, Symbol

    # Compile AST to bytecode chunk
    compiler = VMCompiler()
    chunk = compiler.compile(program)

    # Marshal input data to simple Python types for PyO3
    raw_input: dict[str, object] = {}
    if input_data:
        for key, val in input_data.items():
            raw_input[key] = _marshal_value(val)

    # Execute in Rust VM
    vm = SigilVM()
    result = vm.execute(chunk, raw_input)

    # Extract results
    output_lines: list[str] = list(result.get("output_lines", []))
    vm_result = result.get("result")
    bindings: dict[str, object] = dict(result.get("bindings", {}))

    # Unmarshal result
    final_result = _unmarshal_value(vm_result)

    return final_result, output_lines, bindings


def _marshal_value(val: Value) -> object:
    """Convert a Sigil Value to a simple Python type for PyO3."""
    from sigil.interpreter.values import Closure, Record, Symbol, Variant

    if val is None:
        return None
    if isinstance(val, (int, float, str, bool)):
        return val
    if isinstance(val, Symbol):
        return {"name": val.name}
    if isinstance(val, Record):
        result: dict[str, object] = {}
        if val.type_name:
            result["_type"] = val.type_name
        for k, v in val.fields.items():
            result[k] = _marshal_value(v)
        return result
    if isinstance(val, Variant):
        return {
            "_type": "variant",
            "type_name": val.type_name,
            "variant_name": val.variant_name,
            "fields": {k: _marshal_value(v) for k, v in val.fields.items()},
        }
    if isinstance(val, list):
        return [_marshal_value(v) for v in val]
    return val


def _unmarshal_value(val: object) -> Value:
    """Convert a PyO3 result back to a Sigil Value."""
    from sigil.interpreter.values import Record, Symbol, Variant

    if val is None:
        return None
    if isinstance(val, (int, float, str, bool)):
        return val
    if isinstance(val, dict):
        if val.get("_type") == "symbol":
            return Symbol(val["name"])
        if val.get("_type") == "variant":
            return Variant(
                type_name=val["type_name"],
                variant_name=val["variant_name"],
                fields={k: _unmarshal_value(v) for k, v in val.get("fields", {}).items()},
            )
        # Regular record or dict
        fields = {k: _unmarshal_value(v) for k, v in val.items() if k != "_type"}
        type_name = val.get("_type")
        if type_name and type_name not in ("symbol", "variant"):
            return Record(type_name=type_name, fields=fields)
        if not type_name:
            return Record(type_name=None, fields=fields)
        return val
    if isinstance(val, list):
        return [_unmarshal_value(v) for v in val]
    return val
