"""Mock-hou tests for the typed COP/Copernicus skill."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

from skill_loader import skill_script_import_context

_ROOT = Path(__file__).parents[1] / "src" / "dcc_mcp_houdini" / "skills" / "houdini-copernicus"


def _load(name: str) -> ModuleType:
    path = _ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location("copernicus_{}".format(path.stem), path)
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


def test_create_cop_network_is_idempotent() -> None:
    mod = _load("create_cop_network.py")
    parent = _node("/img", "img", "img")
    existing = _node("/img/copnet1", "copnet1", "cop2net")
    mock_hou = MagicMock()
    mock_hou.node.return_value = existing

    with patch.dict(sys.modules, {"hou": mock_hou}):
        result = mod.create_cop_network("/img")

    assert result["success"] is True
    assert result["context"]["created"] is False
    parent.createNode.assert_not_called()


def test_create_cop_node_wires_filter_and_parameters() -> None:
    mod = _load("create_cop_node.py")
    network = _node("/img/copnet1", "copnet1", "cop2net")
    blur = _node("/img/copnet1/blur1", "blur1", "blur")
    parm = MagicMock()
    blur.parm.side_effect = lambda name: parm if name == "size" else None
    source = _node("/img/copnet1/file1", "file1", "file")
    network.createNode.return_value = blur
    mock_hou = MagicMock()
    mock_hou.node.side_effect = lambda path: {network.path(): network, source.path(): source}.get(path)

    with patch.dict(sys.modules, {"hou": mock_hou}):
        result = mod.create_cop_node("/img/copnet1", "blur", input_nodes=["/img/copnet1/file1"], parameters={"size": 4})

    assert result["success"] is True
    assert result["context"]["node_type"] == "blur"
    assert result["context"]["wired_inputs"] == [{"input_index": 0, "source_path": source.path()}]
    parm.set.assert_called_once_with(4)
    blur.setInput.assert_called_once_with(0, source)


def test_validate_cop_network_reports_node_errors() -> None:
    mod = _load("validate_cop_network.py")
    network = _node("/img/copnet1", "copnet1", "cop2net")
    broken = _node("/img/copnet1/blur1", "blur1", "blur")
    broken.errors.return_value = ["missing input"]
    network.children.return_value = [broken]
    mock_hou = MagicMock()
    mock_hou.node.return_value = network

    with patch.dict(sys.modules, {"hou": mock_hou}):
        result = mod.validate_cop_network("/img/copnet1")

    assert result["success"] is True
    assert result["context"]["valid"] is False
    assert "/img/copnet1/blur1: missing input" in result["context"]["errors"]
