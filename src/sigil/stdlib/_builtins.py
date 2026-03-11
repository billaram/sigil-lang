"""Python-implemented standard library functions for Sigil."""

from __future__ import annotations

import json as _json
import math as _math
import time as _time
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from sigil.interpreter.values import Record, Symbol, Value, values_equal

if TYPE_CHECKING:
    from sigil.interpreter.trace import ProgramTrace

# ============================================================
# Math module
# ============================================================


def stdlib_sqrt(args: list[Value], _trace: ProgramTrace) -> Value:
    return _math.sqrt(args[0])  # type: ignore[arg-type]


def stdlib_abs(args: list[Value], _trace: ProgramTrace) -> Value:
    return abs(args[0])  # type: ignore[arg-type]


def stdlib_floor(args: list[Value], _trace: ProgramTrace) -> Value:
    return _math.floor(args[0])  # type: ignore[arg-type]


def stdlib_ceil(args: list[Value], _trace: ProgramTrace) -> Value:
    return _math.ceil(args[0])  # type: ignore[arg-type]


def stdlib_round(args: list[Value], _trace: ProgramTrace) -> Value:
    if len(args) == 2:
        return round(args[0], int(args[1]))  # type: ignore[arg-type]
    return round(args[0])  # type: ignore[arg-type]


def stdlib_pow(args: list[Value], _trace: ProgramTrace) -> Value:
    return args[0] ** args[1]  # type: ignore[operator]


def stdlib_log(args: list[Value], _trace: ProgramTrace) -> Value:
    return _math.log(args[0])  # type: ignore[arg-type]


def stdlib_sin(args: list[Value], _trace: ProgramTrace) -> Value:
    return _math.sin(args[0])  # type: ignore[arg-type]


def stdlib_cos(args: list[Value], _trace: ProgramTrace) -> Value:
    return _math.cos(args[0])  # type: ignore[arg-type]


STDLIB_MATH: dict[str, Any] = {
    "sqrt": stdlib_sqrt,
    "abs": stdlib_abs,
    "floor": stdlib_floor,
    "ceil": stdlib_ceil,
    "round": stdlib_round,
    "pow": stdlib_pow,
    "log": stdlib_log,
    "sin": stdlib_sin,
    "cos": stdlib_cos,
    "PI": _math.pi,
    "E": _math.e,
}

# ============================================================
# Text module
# ============================================================


def stdlib_length(args: list[Value], _trace: ProgramTrace) -> Value:
    return len(args[0])  # type: ignore[arg-type]


def stdlib_substring(args: list[Value], _trace: ProgramTrace) -> Value:
    s, start, end = args[0], int(args[1]), int(args[2])  # type: ignore[arg-type]
    return s[start:end]  # type: ignore[index]


def stdlib_split(args: list[Value], _trace: ProgramTrace) -> Value:
    if len(args) > 1:
        return args[0].split(args[1])  # type: ignore[union-attr, arg-type]
    return args[0].split()  # type: ignore[union-attr]


def stdlib_join(args: list[Value], _trace: ProgramTrace) -> Value:
    sep = str(args[1]) if len(args) > 1 else ""
    return sep.join(str(x) for x in args[0])  # type: ignore[union-attr]


def stdlib_lowercase(args: list[Value], _trace: ProgramTrace) -> Value:
    return args[0].lower()  # type: ignore[union-attr]


def stdlib_uppercase(args: list[Value], _trace: ProgramTrace) -> Value:
    return args[0].upper()  # type: ignore[union-attr]


def stdlib_trim(args: list[Value], _trace: ProgramTrace) -> Value:
    return args[0].strip()  # type: ignore[union-attr]


def stdlib_replace(args: list[Value], _trace: ProgramTrace) -> Value:
    return args[0].replace(args[1], args[2])  # type: ignore[union-attr, arg-type]


def stdlib_starts_with(args: list[Value], _trace: ProgramTrace) -> Value:
    return args[0].startswith(args[1])  # type: ignore[union-attr, arg-type]


def stdlib_ends_with(args: list[Value], _trace: ProgramTrace) -> Value:
    return args[0].endswith(args[1])  # type: ignore[union-attr, arg-type]


STDLIB_TEXT: dict[str, Any] = {
    "length": stdlib_length,
    "substring": stdlib_substring,
    "split": stdlib_split,
    "join": stdlib_join,
    "lowercase": stdlib_lowercase,
    "uppercase": stdlib_uppercase,
    "trim": stdlib_trim,
    "replace": stdlib_replace,
    "starts_with": stdlib_starts_with,
    "ends_with": stdlib_ends_with,
}

# ============================================================
# List module
# ============================================================


def stdlib_range(args: list[Value], _trace: ProgramTrace) -> Value:
    if len(args) == 1:
        return list(range(int(args[0])))  # type: ignore[arg-type]
    if len(args) == 2:
        return list(range(int(args[0]), int(args[1])))  # type: ignore[arg-type]
    return list(range(int(args[0]), int(args[1]), int(args[2])))  # type: ignore[arg-type]


def stdlib_reverse(args: list[Value], _trace: ProgramTrace) -> Value:
    return list(reversed(args[0]))  # type: ignore[arg-type]


def stdlib_flatten(args: list[Value], _trace: ProgramTrace) -> Value:
    result: list[Value] = []
    for item in args[0]:  # type: ignore[union-attr]
        if isinstance(item, list):
            result.extend(item)
        else:
            result.append(item)
    return result


def stdlib_unique(args: list[Value], _trace: ProgramTrace) -> Value:
    seen: list[Value] = []
    result: list[Value] = []
    for item in args[0]:  # type: ignore[union-attr]
        if not any(values_equal(item, s) for s in seen):
            seen.append(item)
            result.append(item)
    return result


def stdlib_zip_lists(args: list[Value], _trace: ProgramTrace) -> Value:
    return [
        Record(None, {"first": a, "second": b})
        for a, b in zip(args[0], args[1], strict=False)  # type: ignore[arg-type]
    ]


def stdlib_sum(args: list[Value], _trace: ProgramTrace) -> Value:
    return sum(args[0])  # type: ignore[arg-type]


def stdlib_count(args: list[Value], _trace: ProgramTrace) -> Value:
    return len(args[0])  # type: ignore[arg-type]


STDLIB_LIST: dict[str, Any] = {
    "range": stdlib_range,
    "reverse": stdlib_reverse,
    "flatten": stdlib_flatten,
    "unique": stdlib_unique,
    "zip": stdlib_zip_lists,
    "sum": stdlib_sum,
    "count": stdlib_count,
    "length": stdlib_length,
}

# ============================================================
# Logic module
# ============================================================


def stdlib_xor(args: list[Value], _trace: ProgramTrace) -> Value:
    return bool(args[0]) != bool(args[1])


def stdlib_implies(args: list[Value], _trace: ProgramTrace) -> Value:
    return not bool(args[0]) or bool(args[1])


def stdlib_nand(args: list[Value], _trace: ProgramTrace) -> Value:
    return not (bool(args[0]) and bool(args[1]))


def stdlib_type_of(args: list[Value], _trace: ProgramTrace) -> Value:
    v = args[0]
    if isinstance(v, bool):
        return Symbol("Boolean")
    if isinstance(v, int):
        return Symbol("Number")
    if isinstance(v, float):
        return Symbol("Number")
    if isinstance(v, str):
        return Symbol("Text")
    if isinstance(v, Symbol):
        return Symbol("Symbol")
    if isinstance(v, Record):
        return Symbol("Record")
    if isinstance(v, list):
        return Symbol("List")
    if v is None:
        return Symbol("None")
    return Symbol("Unknown")


def stdlib_is_number(args: list[Value], _trace: ProgramTrace) -> Value:
    return isinstance(args[0], (int, float))


def stdlib_is_text(args: list[Value], _trace: ProgramTrace) -> Value:
    return isinstance(args[0], str)


def stdlib_is_list(args: list[Value], _trace: ProgramTrace) -> Value:
    return isinstance(args[0], list)


STDLIB_LOGIC: dict[str, Any] = {
    "xor": stdlib_xor,
    "implies": stdlib_implies,
    "nand": stdlib_nand,
    "type_of": stdlib_type_of,
    "is_number": stdlib_is_number,
    "is_text": stdlib_is_text,
    "is_list": stdlib_is_list,
}

# ============================================================
# Time module
# ============================================================


def stdlib_now(args: list[Value], _trace: ProgramTrace) -> Value:
    return _time.time()


def stdlib_now_ms(args: list[Value], _trace: ProgramTrace) -> Value:
    return _time.time() * 1000


def stdlib_format_timestamp(args: list[Value], _trace: ProgramTrace) -> Value:
    ts = float(args[0])  # type: ignore[arg-type]
    dt = datetime.fromtimestamp(ts, tz=UTC)
    return dt.isoformat()


def stdlib_elapsed(args: list[Value], _trace: ProgramTrace) -> Value:
    start = float(args[0])  # type: ignore[arg-type]
    end = float(args[1])  # type: ignore[arg-type]
    return end - start


def stdlib_duration_seconds(args: list[Value], _trace: ProgramTrace) -> Value:
    return float(args[0])  # type: ignore[arg-type]


STDLIB_TIME: dict[str, Any] = {
    "now": stdlib_now,
    "now_ms": stdlib_now_ms,
    "format_timestamp": stdlib_format_timestamp,
    "elapsed": stdlib_elapsed,
    "duration_seconds": stdlib_duration_seconds,
}

# ============================================================
# Trace module
# ============================================================


def stdlib_trace_to_json(args: list[Value], _trace: ProgramTrace) -> Value:
    """Convert the current program trace to JSON."""
    data = {
        "rules": [
            {
                "name": rt.rule_name,
                "priority": rt.priority,
                "fired": rt.fired,
                "duration_ms": rt.duration_ms,
            }
            for rt in _trace.rule_traces
        ],
        "total_duration_ms": _trace.total_duration_ms,
    }
    return _json.dumps(data)


def stdlib_fired_rules(args: list[Value], _trace: ProgramTrace) -> Value:
    return [rt.rule_name for rt in _trace.rule_traces if rt.fired]


def stdlib_rule_count(args: list[Value], _trace: ProgramTrace) -> Value:
    return len(_trace.rule_traces)


def stdlib_trace_duration_ms(args: list[Value], _trace: ProgramTrace) -> Value:
    return _trace.total_duration_ms


STDLIB_TRACE: dict[str, Any] = {
    "to_json": stdlib_trace_to_json,
    "fired_rules": stdlib_fired_rules,
    "rule_count": stdlib_rule_count,
    "duration_ms": stdlib_trace_duration_ms,
}

# ============================================================
# IO module
# ============================================================


def stdlib_read_file(args: list[Value], _trace: ProgramTrace) -> Value:
    path = Path(str(args[0]))
    return path.read_text(encoding="utf-8")


def stdlib_write_file(args: list[Value], _trace: ProgramTrace) -> Value:
    path = Path(str(args[0]))
    path.write_text(str(args[1]), encoding="utf-8")
    return None


def stdlib_file_exists(args: list[Value], _trace: ProgramTrace) -> Value:
    return Path(str(args[0])).exists()


def _sigil_value_to_python(val: Value) -> object:
    """Convert a Sigil value to a Python-serializable object."""
    if isinstance(val, Symbol):
        return val.name
    if isinstance(val, Record):
        return {k: _sigil_value_to_python(v) for k, v in val.fields.items()}
    if isinstance(val, list):
        return [_sigil_value_to_python(item) for item in val]
    return val


def _python_to_sigil_value(obj: object) -> Value:
    """Convert a Python object to a Sigil value."""
    if isinstance(obj, dict):
        fields = {k: _python_to_sigil_value(v) for k, v in obj.items()}
        return Record(None, fields)
    if isinstance(obj, list):
        return [_python_to_sigil_value(item) for item in obj]
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, (int, float)):
        return obj
    if isinstance(obj, str):
        return obj
    if obj is None:
        return None
    return str(obj)


def stdlib_parse_json(args: list[Value], _trace: ProgramTrace) -> Value:
    data = _json.loads(str(args[0]))
    return _python_to_sigil_value(data)


def stdlib_to_json(args: list[Value], _trace: ProgramTrace) -> Value:
    return _json.dumps(_sigil_value_to_python(args[0]))


STDLIB_IO: dict[str, Any] = {
    "read_file": stdlib_read_file,
    "write_file": stdlib_write_file,
    "file_exists": stdlib_file_exists,
    "parse_json": stdlib_parse_json,
    "to_json": stdlib_to_json,
}
