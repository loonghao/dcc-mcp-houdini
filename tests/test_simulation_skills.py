"""Mock-hou tests for the typed DOP simulation skill."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

from skill_loader import skill_script_import_context

_ROOT = Path(__file__).parents[1] / "src" / "dcc_mcp_houdini" / "skills" / "houdini-simulation"


def _load(name: str) -> ModuleType:
    path = _ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location("simulation_{}".format(path.stem), path)
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


def test_create_simulation_network_builds_typed_solver_and_applies_parameters() -> None:
    mod = _load("create_simulation_network.py")
    parent = _node("/obj", "obj", "obj")
    network = _node("/obj/dopnet1", "dopnet1", "dopnet")
    solver = _node("/obj/dopnet1/pyrosolver1", "pyrosolver1", "pyrosolver")
    parm = MagicMock()
    solver.parm.side_effect = lambda name: parm if name == "timescale" else None
    solver.parmTuple.return_value = None
    network.node.return_value = None
    network.createNode.return_value = solver
    parent.createNode.return_value = network
    mock_hou = MagicMock()
    mock_hou.node.side_effect = lambda path: parent if path == "/obj" else None

    with patch.dict(sys.modules, {"hou": mock_hou}):
        result = mod.create_simulation_network("/obj", "pyro", parameters={"timescale": 0.5, "missing": 1})

    assert result["success"] is True
    assert result["context"]["solver_type"] == "pyrosolver"
    assert result["context"]["applied_parameters"] == {"timescale": 0.5}
    assert result["context"]["skipped_parameters"] == [{"name": "missing", "reason": "parameter not found"}]
    parent.createNode.assert_called_once_with("dopnet", node_name="dopnet1")
    network.createNode.assert_called_once_with("pyrosolver", node_name="pyrosolver1")
    parm.set.assert_called_once_with(0.5)


def test_configure_simulation_solver_rejects_invalid_parameter_names() -> None:
    mod = _load("configure_simulation_solver.py")
    solver = _node("/obj/dopnet1/rbdsolver1", "rbdsolver1", "rbdsolver")
    mock_hou = MagicMock()
    mock_hou.node.return_value = solver

    with patch.dict(sys.modules, {"hou": mock_hou}):
        result = mod.configure_simulation_solver("/obj/dopnet1/rbdsolver1", {"bad-name": 1})

    assert result["success"] is False
    assert "Invalid Houdini parameter name" in str(result)


def test_validate_simulation_setup_reports_expected_solver() -> None:
    mod = _load("validate_simulation_setup.py")
    network = _node("/obj/dopnet1", "dopnet1", "dopnet")
    solver = _node("/obj/dopnet1/flipsolver1", "flipsolver1", "flipsolver")
    network.children.return_value = [solver]
    mock_hou = MagicMock()
    mock_hou.node.return_value = network

    with patch.dict(sys.modules, {"hou": mock_hou}):
        result = mod.validate_simulation_setup("/obj/dopnet1", "flip")

    assert result["success"] is True
    assert result["context"]["valid"] is True
    assert result["context"]["solver_count"] == 1


def test_validate_simulation_setup_fails_for_wrong_solver_family() -> None:
    mod = _load("validate_simulation_setup.py")
    network = _node("/obj/dopnet1", "dopnet1", "dopnet")
    solver = _node("/obj/dopnet1/rbdsolver1", "rbdsolver1", "rbdsolver")
    network.children.return_value = [solver]
    mock_hou = MagicMock()
    mock_hou.node.return_value = network

    with patch.dict(sys.modules, {"hou": mock_hou}):
        result = mod.validate_simulation_setup("/obj/dopnet1", "vellum")

    assert result["success"] is True
    assert result["context"]["valid"] is False
    assert "vellum" in result["context"]["errors"][0]
