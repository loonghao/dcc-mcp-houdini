"""Public domain tool contracts with explicit HOM doubles."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from domain_graph_fakes import scene
from skill_loader import skill_script_import_context

_ROOT = Path(__file__).parents[1] / "src" / "dcc_mcp_houdini" / "skills" / "houdini-simulation"


def _load(name):
    spec = importlib.util.spec_from_file_location("simulation_" + name[:-3], _ROOT / "scripts" / name)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    with skill_script_import_context(spec):
        spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("family", ["pyro", "flip", "rbd", "vellum"])
def test_create_simulation_network_is_explicit_skeleton(family):
    root, geo, hou = scene()
    with patch.dict(sys.modules, {"hou": hou}):
        result = _load("create_simulation_network.py").create_simulation_network(
            root.path(), family, parameters={"timescale": 0.5}
        )
    assert result["success"]
    assert result["context"]["setup_state"] == "skeleton"
    assert result["context"]["simulation_verified"] is False
    assert result["context"]["applied_parameters"] == {"timescale": 0.5}
    assert hou.node(result["context"]["solver_path"]).type().name() == family + "solver"


def test_failed_creation_preserves_existing_network():
    root, geo, hou = scene()
    network = root.createNode("dopnet")
    preserved = network.createNode("null")
    with patch.dict(sys.modules, {"hou": hou}):
        result = _load("create_simulation_network.py").create_simulation_network(
            root.path(), "pyro", parameters={"missing": 1}
        )
    assert not result["success"]
    assert network.children() == (preserved,) and not network.destroyed


def test_failed_creation_cleans_new_network():
    root, geo, hou = scene()
    with patch.dict(sys.modules, {"hou": hou}):
        result = _load("create_simulation_network.py").create_simulation_network(
            root.path(), "pyro", parameters={"missing": 1}
        )
    assert not result["success"]
    assert root.node("dopnet1") is None


def test_configuration_rolls_back_parameters_on_cook_failure():
    root, geo, hou = scene()
    solver = root.createNode("dopnet").createNode("pyrosolver")
    solver.parm("timescale").keys = ("animated expression",)
    solver.error_messages = ["bad source"]
    with patch.dict(sys.modules, {"hou": hou}):
        result = _load("configure_simulation_solver.py").configure_simulation_solver(
            solver.path(), {"timescale": 0.5}, cook=True
        )
    assert not result["success"]
    assert solver.parm("timescale").keys == ("animated expression",)


def test_validation_rejects_disconnected_solver_and_child_errors():
    root, geo, hou = scene()
    network = root.createNode("dopnet")
    solver = network.createNode("flipsolver")
    solver._type = "flipsolver::2.0"
    mod = _load("validate_simulation_setup.py")
    with patch.dict(sys.modules, {"hou": hou}):
        result = mod.validate_simulation_setup(network.path(), "flip")
        assert not result["context"]["valid"]
        source = network.createNode("flipobject")
        solver.setInput(0, source)
        source.error_messages = ["missing particles"]
        assert not mod.validate_simulation_setup(network.path(), "flip")["context"]["valid"]
        source.error_messages = []
        result = mod.validate_simulation_setup(network.path(), "flip")
        assert result["context"]["valid"] and not result["context"]["simulation_verified"]


def test_configuration_preflights_all_parameter_names():
    root, geo, hou = scene()
    solver = root.createNode("dopnet").createNode("rbdsolver")
    with patch.dict(sys.modules, {"hou": hou}):
        result = _load("configure_simulation_solver.py").configure_simulation_solver(
            solver.path(), {"timescale": 0.5, "bad-name": 1}
        )
    assert not result["success"]
    assert solver.parm("timescale").eval() == 1
