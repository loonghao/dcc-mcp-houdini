"""Mock-hou tests for the typed PDG/TOP skill."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

from skill_loader import skill_script_import_context

_ROOT = Path(__file__).parents[1] / "src" / "dcc_mcp_houdini" / "skills" / "houdini-pdg"


def _load(name: str) -> ModuleType:
    path = _ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location("pdg_{}".format(path.stem), path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    with skill_script_import_context(spec):
        spec.loader.exec_module(module)
    return module


def _node(path: str, name: str, type_name: str) -> MagicMock:
    node = MagicMock()
    node.path.return_value = path
    node.name.return_value = name
    node.type.return_value.name.return_value = type_name
    node.errors.return_value = []
    node.warnings.return_value = []
    return node


def test_create_pdg_node_rejects_unsafe_type() -> None:
    mod = _load("create_pdg_node.py")
    network = _node("/obj/topnet1", "topnet1", "topnet")
    mock_hou = MagicMock()
    mock_hou.node.return_value = network

    with patch.dict(sys.modules, {"hou": mock_hou}):
        result = mod.create_pdg_node("/obj/topnet1", "ropfetch;bad")

    assert result["success"] is False
    assert "Invalid PDG node type" in str(result)


def test_create_and_connect_pdg_nodes() -> None:
    create_mod = _load("create_pdg_node.py")
    connect_mod = _load("connect_pdg_nodes.py")
    network = _node("/obj/topnet1", "topnet1", "topnet")
    source = _node("/obj/topnet1/generator1", "generator1", "genericgenerator")
    sink = _node("/obj/topnet1/ropfetch1", "ropfetch1", "ropfetch")
    network.createNode.return_value = sink
    mock_hou = MagicMock()
    mock_hou.node.side_effect = lambda path: {
        network.path(): network,
        source.path(): source,
        sink.path(): sink,
    }.get(path)

    with patch.dict(sys.modules, {"hou": mock_hou}):
        created = create_mod.create_pdg_node(
            network.path(), "ropfetch", input_nodes=[source.path()], parameters={"service": "local"}
        )
        connected = connect_mod.connect_pdg_nodes(sink.path(), source.path(), input_index=1)

    assert created["success"] is True
    assert connected["success"] is True
    sink.setInput.assert_called_with(1, source, 0)


def test_inspect_and_cook_pdg_graph_reports_work_items() -> None:
    inspect_mod = _load("inspect_pdg_graph.py")
    cook_mod = _load("cook_pdg_graph.py")
    node = _node("/obj/topnet1", "topnet1", "topnet")
    item_a = MagicMock(state="cooked")
    item_b = MagicMock(state="failed")
    graph = MagicMock()
    graph.workItems.return_value = [item_a, item_b]
    context = MagicMock(graph=graph)
    node.getPDGGraphContext.return_value = context
    mock_hou = MagicMock()
    mock_hou.node.return_value = node

    with patch.dict(sys.modules, {"hou": mock_hou}):
        inspected = inspect_mod.inspect_pdg_graph(node.path())
        cooked = cook_mod.cook_pdg_graph(node.path(), block=False)

    assert inspected["success"] is True
    assert inspected["context"]["work_item_count"] == 2
    assert inspected["context"]["work_item_states"] == {"cooked": 1, "failed": 1}
    assert cooked["success"] is True
    node.cookWorkItems.assert_called_once_with(block=False)
