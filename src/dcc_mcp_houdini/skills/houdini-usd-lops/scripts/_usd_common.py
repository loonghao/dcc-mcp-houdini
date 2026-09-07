"""Shared, dependency-free helpers for read-only USD inspection."""

from __future__ import annotations

import math
from typing import Any, Tuple

from dcc_mcp_houdini._bounded_values import bounded_value as bounded_value
from dcc_mcp_houdini._bounded_values import require_range as require_range


def require_absolute_path(value: str, label: str) -> str:
    """Validate and return an absolute Houdini or USD path."""
    path = str(value or "").strip()
    if not path.startswith("/"):
        raise ValueError("{} must be an absolute path".format(label))
    return path


def resolve_stage(hou: Any, lop_node_path: str) -> Tuple[Any, Any]:
    """Resolve a Houdini LOP node and its composed USD Stage."""
    node_path = require_absolute_path(lop_node_path, "lop_node_path")
    node = hou.node(node_path)
    if node is None:
        raise ValueError("Houdini node not found: {}".format(node_path))
    stage_method = getattr(node, "stage", None)
    if not callable(stage_method):
        raise ValueError("Houdini node is not a LOP node: {}".format(node_path))
    stage = stage_method()
    if stage is None:
        raise RuntimeError("LOP node returned no composed USD Stage: {}".format(node_path))
    return node, stage


def resolve_prim(stage: Any, prim_path: str) -> Any:
    """Resolve a valid prim from *stage*."""
    path = require_absolute_path(prim_path, "prim_path")
    prim = stage.GetPrimAtPath(path)
    if not prim:
        raise ValueError("USD prim not found: {}".format(path))
    return prim


def make_time_code(Usd: Any, value: Any) -> Any:
    """Create default or numeric ``Usd.TimeCode`` with finite-number validation."""
    if value is None:
        return Usd.TimeCode.Default()
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("time_code must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("time_code must be a finite number")
    return Usd.TimeCode(number)
