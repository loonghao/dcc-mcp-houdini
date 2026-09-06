"""Shared helpers for COP/Copernicus node skills."""

from __future__ import annotations

import re
from typing import Any, Dict, Tuple

from dcc_mcp_core.skill import skill_error

FILTER_TYPES = {
    "file": "file",
    "blur": "blur",
    "composite": "composite",
    "comp": "composite",
    "colorcorrect": "colorcorrect",
    "color_correct": "colorcorrect",
    "ramp": "ramp",
    "null": "null",
    "output": "rop_comp",
}
_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_MAX_PARAMETERS = 32


def get_node(hou: Any, node_path: str) -> Any:
    node = hou.node(node_path)
    if node is None:
        raise ValueError("Houdini node not found: {}".format(node_path))
    return node


def resolve_filter_type(filter_type: str) -> str:
    value = str(filter_type or "").strip().lower()
    if value in FILTER_TYPES:
        return FILTER_TYPES[value]
    if not _IDENTIFIER.match(value):
        raise ValueError("Invalid COP filter type: {!r}".format(filter_type))
    return value


def validate_parameters(parameters: Any) -> Dict[str, Any]:
    if parameters is None:
        return {}
    if not isinstance(parameters, dict):
        raise ValueError("parameters must be an object")
    if len(parameters) > _MAX_PARAMETERS:
        raise ValueError("parameters may contain at most {} entries".format(_MAX_PARAMETERS))
    result: Dict[str, Any] = {}
    for name, value in parameters.items():
        if not isinstance(name, str) or not _IDENTIFIER.match(name):
            raise ValueError("Invalid Houdini parameter name: {!r}".format(name))
        if isinstance(value, (str, int, float, bool)) or value is None:
            result[name] = value
        elif isinstance(value, (list, tuple)) and len(value) <= 16:
            result[name] = tuple(value)
        else:
            raise ValueError("Unsupported value for parameter {!r}".format(name))
    return result


def set_parameters(node: Any, parameters: Any) -> Tuple[Dict[str, Any], list]:
    applied: Dict[str, Any] = {}
    skipped = []
    for name, value in validate_parameters(parameters).items():
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
    result: Dict[str, Any] = {"path": node.path(), "name": node.name()}
    try:
        result["type"] = node.type().name()
    except Exception:  # noqa: BLE001
        result["type"] = None
    try:
        result["errors"] = list(node.errors())
    except Exception:  # noqa: BLE001
        result["errors"] = []
    try:
        result["warnings"] = list(node.warnings())
    except Exception:  # noqa: BLE001
        result["warnings"] = []
    return result


def input_connections(node: Any) -> list:
    connections = []
    try:
        for connection in node.inputConnections():
            source = connection.inputItem()
            connections.append(
                {
                    "input_index": connection.inputIndex(),
                    "source_path": source.path(),
                    "source_output_index": connection.inputItemOutputIndex(),
                }
            )
    except Exception:  # noqa: BLE001
        pass
    return connections


def hou_missing_error():
    return skill_error("Houdini not available", "hou could not be imported")
