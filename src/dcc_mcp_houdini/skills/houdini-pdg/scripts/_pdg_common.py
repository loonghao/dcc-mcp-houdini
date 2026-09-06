"""Shared helpers for PDG/TOP graph skills."""

from __future__ import annotations

import re
from typing import Any, Dict, Tuple

from dcc_mcp_core.skill import skill_error

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_MAX_PARAMETERS = 32


def get_node(hou: Any, node_path: str) -> Any:
    node = hou.node(node_path)
    if node is None:
        raise ValueError("Houdini node not found: {}".format(node_path))
    return node


def validate_identifier(value: str, label: str) -> str:
    result = str(value or "").strip()
    if not _IDENTIFIER.match(result):
        raise ValueError("Invalid {}: {!r}".format(label, value))
    return result


def validate_parameters(parameters: Any) -> Dict[str, Any]:
    if parameters is None:
        return {}
    if not isinstance(parameters, dict):
        raise ValueError("parameters must be an object")
    if len(parameters) > _MAX_PARAMETERS:
        raise ValueError("parameters may contain at most {} entries".format(_MAX_PARAMETERS))
    result: Dict[str, Any] = {}
    for name, value in parameters.items():
        validate_identifier(name, "parameter name")
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


def connection_summary(node: Any) -> list:
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


def graph_snapshot(node: Any) -> Dict[str, Any]:
    result: Dict[str, Any] = {"node": node_summary(node)}
    try:
        result["children"] = []
        for child in node.children():
            child_data = node_summary(child)
            child_data["inputs"] = connection_summary(child)
            result["children"].append(child_data)
    except Exception:  # noqa: BLE001
        result["children"] = []
    graph = None
    try:
        context = node.getPDGGraphContext()
        graph = context.graph
    except Exception:  # noqa: BLE001
        pass
    result.update(work_item_snapshot(graph))
    return result


def work_item_snapshot(graph: Any) -> Dict[str, Any]:
    if graph is None:
        return {"work_item_count": None, "work_item_states": {}}
    try:
        items = list(graph.workItems())
    except Exception:  # noqa: BLE001
        return {"work_item_count": None, "work_item_states": {}}
    states: Dict[str, int] = {}
    for item in items:
        try:
            state = item.state
            if callable(state):
                state = state()
            state_name = getattr(state, "name", None)
            state_name = state_name() if callable(state_name) else state_name
            key = str(state_name or state)
        except Exception:  # noqa: BLE001
            key = "unknown"
        states[key] = states.get(key, 0) + 1
    return {"work_item_count": len(items), "work_item_states": states}


def hou_missing_error():
    return skill_error("Houdini not available", "hou could not be imported")
