"""Public domain tool contracts with explicit HOM doubles."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from domain_graph_fakes import Node, scene
from skill_loader import skill_script_import_context

_ROOT = Path(__file__).parents[1] / "src" / "dcc_mcp_houdini" / "skills" / "houdini-copernicus"


def _load(name):
    spec = importlib.util.spec_from_file_location("copernicus_" + name[:-3], _ROOT / "scripts" / name)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    with skill_script_import_context(spec):
        spec.loader.exec_module(module)
    return module


def test_create_cop_network_is_idempotent_and_modern():
    root, geo, hou = scene()
    mod = _load("create_cop_network.py")
    with patch.dict(sys.modules, {"hou": hou}):
        first = mod.create_cop_network(geo.path())
        second = mod.create_cop_network(geo.path())
    assert first["success"] and second["success"]
    assert first["context"]["created"] and not second["context"]["created"]
    assert geo.node("copnet1").type().name() == "copnet"


def test_reuse_rejects_legacy_cop2():
    root, geo, hou = scene()
    old = Node(geo.path() + "/copnet1", "cop2net", geo, "Cop2")
    with patch.dict(sys.modules, {"hou": hou}):
        result = _load("create_cop_network.py").create_cop_network(geo.path())
    assert not result["success"]
    assert not old.destroyed


def test_create_cop_node_wires_and_reads_parameters():
    root, geo, hou = scene()
    network = geo.createNode("copnet")
    source = network.createNode("file")
    with patch.dict(sys.modules, {"hou": hou}):
        result = _load("create_cop_node.py").create_cop_node(
            network.path(), "blur", input_nodes=[source.path()], parameters={"size": 4}
        )
    assert result["success"]
    assert result["context"]["applied_parameters"] == {"size": 4}
    assert result["context"]["wired_inputs"] == [
        {"input_index": 0, "source_path": source.path(), "source_output_index": 0}
    ]


@pytest.mark.parametrize("parameters", [{"missing": 1}, {"size": float("nan")}, {"size": [[1]]}])
def test_failed_authoring_does_not_leave_nodes(parameters):
    root, geo, hou = scene()
    network = geo.createNode("copnet")
    with patch.dict(sys.modules, {"hou": hou}):
        result = _load("create_cop_node.py").create_cop_node(network.path(), "blur", parameters=parameters)
    assert not result["success"]
    assert not network.children()


def test_cross_network_input_rejected_before_creation():
    root, geo, hou = scene()
    network = geo.createNode("copnet")
    other = geo.createNode("copnet", "other")
    source = other.createNode("file")
    with patch.dict(sys.modules, {"hou": hou}):
        result = _load("create_cop_node.py").create_cop_node(network.path(), "blur", input_nodes=[source.path()])
    assert not result["success"]
    assert not network.children()


def test_cached_validation_propagates_read_failures():
    root, geo, hou = scene()
    network = geo.createNode("copnet")
    broken = network.createNode("blur")
    broken.error_messages = ["missing input"]
    mod = _load("validate_cop_network.py")
    with patch.dict(sys.modules, {"hou": hou}):
        result = mod.validate_cop_network(network.path())
        assert result["success"] and not result["context"]["valid"]
        assert result["context"]["validation_scope"] == "cached_diagnostics"

        def unreadable():
            raise RuntimeError("cannot read errors")

        broken.errors = unreadable
        assert not mod.validate_cop_network(network.path())["success"]
