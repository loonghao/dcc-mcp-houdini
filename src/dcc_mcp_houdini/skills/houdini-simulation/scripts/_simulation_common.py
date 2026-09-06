"""Shared, Houdini-version-tolerant helpers for DOP simulation skills."""

from __future__ import annotations

import re
from typing import Any, Dict, Tuple

from dcc_mcp_core.skill import skill_error

SOLVER_TYPES = {
    "pyro": "pyrosolver",
    "flip": "flipsolver",
    "rbd": "rbdsolver",
    "vellum": "vellumsolver",
}
_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_MAX_PARAMETERS = 32


def get_node(hou: Any, node_path: str) -> Any:
    node = hou.node(node_path)
    if node is None:
        raise ValueError("Houdini node not found: {}".format(node_path))
    return node


def validate_simulation_type(simulation_type: str) -> str:
    value = str(simulation_type or "").strip().lower()
    if value not in SOLVER_TYPES:
        raise ValueError("Unsupported simulation_type {!r}; expected one of {}".format(value, ", ".join(SOLVER_TYPES)))
    return value


def validate_parameters(parameters: Any) -> Dict[str, Any]:
    if parameters is None:
        return {}
    if not isinstance(parameters, dict):
        raise ValueError("parameters must be an object")
    if len(parameters) > _MAX_PARAMETERS:
        raise ValueError("parameters may contain at most {} entries".format(_MAX_PARAMETERS))
    normalized: Dict[str, Any] = {}
    for name, value in parameters.items():
        if not isinstance(name, str) or not _IDENTIFIER.match(name):
            raise ValueError("Invalid Houdini parameter name: {!r}".format(name))
        if isinstance(value, (str, int, float, bool)) or value is None:
            normalized[name] = value
        elif isinstance(value, (list, tuple)) and len(value) <= 16:
            normalized[name] = tuple(value)
        else:
            raise ValueError("Unsupported value for parameter {!r}".format(name))
    return normalized


def set_parameters(node: Any, parameters: Any) -> Tuple[Dict[str, Any], list]:
    normalized = validate_parameters(parameters)
    applied: Dict[str, Any] = {}
    skipped = []
    for name, value in normalized.items():
        parm = None
        try:
            parm = node.parm(name)
        except Exception:  # noqa: BLE001
            parm = None
        if parm is None:
            try:
                parm = node.parmTuple(name)
            except Exception:  # noqa: BLE001
                parm = None
        if parm is None:
            skipped.append({"name": name, "reason": "parameter not found"})
            continue
        parm.set(value)
        applied[name] = value
    return applied, skipped


def node_summary(node: Any) -> Dict[str, Any]:
    summary: Dict[str, Any] = {"path": node.path(), "name": node.name()}
    try:
        summary["type"] = node.type().name()
    except Exception:  # noqa: BLE001
        summary["type"] = None
    try:
        summary["errors"] = list(node.errors())
    except Exception:  # noqa: BLE001
        summary["errors"] = []
    try:
        summary["warnings"] = list(node.warnings())
    except Exception:  # noqa: BLE001
        summary["warnings"] = []
    return summary


def children_summary(node: Any) -> list:
    try:
        return [node_summary(child) for child in node.children()]
    except Exception:  # noqa: BLE001
        return []


def hou_missing_error():
    return skill_error("Houdini not available", "hou could not be imported")
