"""Deterministic executor for the FinQA reasoning-program DSL.

Reads only a program string and the model-visible table (never gold). Returns
a numeric value and a machine-readable reason code; never raises for a
malformed program so the B/C validators can reason about failures explicitly.
"""
from __future__ import annotations

import re
from typing import Any

_ARITH_OPS = {
    "add": lambda a, b: a + b,
    "subtract": lambda a, b: a - b,
    "multiply": lambda a, b: a * b,
    "divide": lambda a, b: a / b if b != 0 else None,
    "greater": lambda a, b: (1.0 if a > b else 0.0),
    "exp": lambda a, b: a ** b,
}
_REDUCE_OPS = {
    "table_sum": lambda xs: sum(xs),
    "table_average": lambda xs: sum(xs) / len(xs),
    "table_max": lambda xs: max(xs),
    "table_min": lambda xs: min(xs),
}


def parse_number(text: Any) -> float | None:
    if isinstance(text, (int, float)) and not isinstance(text, bool):
        return float(text)
    if not isinstance(text, str):
        return None
    s = text.strip().replace("$", "").replace(",", "").replace(" ", "")
    if not s:
        return None
    percent = s.endswith("%")
    if percent:
        s = s[:-1]
    if not re.fullmatch(r"-?\d*\.?\d+", s):
        return None
    try:
        value = float(s)
    except ValueError:
        return None
    return value / 100.0 if percent else value


def parse_program(program: str) -> list[dict]:
    """Split a program into steps, splitting on top-level commas only."""
    steps: list[dict] = []
    if not isinstance(program, str) or not program.strip():
        return steps
    depth = 0
    current: list[str] = []
    parts: list[str] = []
    for ch in program:
        if ch == "(":
            depth += 1
            current.append(ch)
        elif ch == ")":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current))
    for part in parts:
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^([a-zA-Z_]+)\((.*)\)$", part)
        if not m:
            return []
        op = m.group(1)
        args_str = m.group(2)
        args = _split_top_level(args_str) if args_str.strip() else []
        steps.append({"op": op, "args": [a.strip() for a in args]})
    return steps


def _split_top_level(s: str) -> list[str]:
    out: list[str] = []
    depth = 0
    current: list[str] = []
    for ch in s:
        if ch == "(":
            depth += 1
            current.append(ch)
        elif ch == ")":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            out.append("".join(current))
            current = []
        else:
            current.append(ch)
    if current:
        out.append("".join(current))
    return [a.strip() for a in out]


def _resolve_arg(arg: str, results: list[float], table: list | None) -> float | None | str:
    if arg.startswith("#"):
        idx = arg[1:]
        if not idx.isdigit():
            return f"bad_reference:{arg}"
        i = int(idx)
        if i < 0 or i >= len(results):
            return f"bad_reference:{arg}"
        return results[i]
    if arg.startswith("const_"):
        return parse_number(arg[len("const_"):])
    val = parse_number(arg)
    if val is not None:
        return val
    return f"unresolved_arg:{arg}"


def execute_program(program: str, table: list | None = None) -> tuple[float | None, str]:
    steps = parse_program(program)
    if not steps:
        return (None, "parse_error")
    results: list[float] = []
    for step in steps:
        op = step["op"]
        resolved: list[float] = []
        for arg in step["args"]:
            r = _resolve_arg(arg, results, table)
            if isinstance(r, str):
                return (None, r)
            if r is None:
                return (None, f"unresolved_arg:{arg}")
            resolved.append(r)
        if op in _ARITH_OPS:
            if len(resolved) != 2:
                return (None, f"bad_arity:{op}")
            val = _ARITH_OPS[op](resolved[0], resolved[1])
            if val is None:
                return (None, "div_by_zero")
        elif op in _REDUCE_OPS:
            if not resolved:
                return (None, f"unresolved_arg:{op}")
            val = _REDUCE_OPS[op](resolved)
        else:
            return (None, f"unknown_op:{op}")
        results.append(float(val))
    return (results[-1], "ok")
