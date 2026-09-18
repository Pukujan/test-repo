"""Optional-backend capability detection.

Z3 and SymbolicAI/SyMAI are OPTIONAL. Their absence must be typed `unavailable`
and never silently substituted with another arm or upgraded to a pass.
"""
from __future__ import annotations

from . import schemas as S


def detect_z3() -> str:
    try:
        import z3  # noqa: F401
    except Exception:
        return S.UNAVAILABLE
    return S.AVAILABLE


def detect_symai() -> str:
    try:
        import symai  # noqa: F401
    except Exception:
        return S.UNAVAILABLE
    return S.AVAILABLE


def detect_all() -> dict:
    return {"z3": detect_z3(), "symai": detect_symai()}
