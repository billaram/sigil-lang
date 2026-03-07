"""Python-implemented standard library functions for Sigil."""

from __future__ import annotations

import math as _math
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
