"""Local real-HOM acceptance probe; creates only transient headless nodes."""

import importlib.util
import json
import sys
from pathlib import Path

import hou

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "src"))
sys.path.insert(0, str(root / "tests"))
from skill_loader import skill_script_import_context  # noqa: E402 - checkout bootstrap

import dcc_mcp_houdini  # noqa: E402 - checkout bootstrap

assert root in Path(dcc_mcp_houdini.__file__).resolve().parents


def call(skill, name, **kwargs):
    script = root / "src/dcc_mcp_houdini/skills" / skill / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location("live_" + name, script)
    mod = importlib.util.module_from_spec(spec)
    with skill_script_import_context(spec):
        spec.loader.exec_module(mod)
    result = getattr(mod, name)(**kwargs)
    print(json.dumps({"tool": name, "success": result["success"]}), flush=True)
    assert result["success"], result
    return result["context"]


print(json.dumps({"houdini": hou.applicationVersionString(), "license": str(hou.licenseCategory())}), flush=True)
geo = hou.node("/obj").createNode("geo", "capability_probe")
cop = call("houdini-copernicus", "create_cop_network", parent_path=geo.path())
constant = call("houdini-copernicus", "create_cop_node", network_path=cop["network_path"], filter_type="constant")
blur = call(
    "houdini-copernicus",
    "create_cop_node",
    network_path=cop["network_path"],
    filter_type="blur",
    input_nodes=[constant["node_path"]],
)
call("houdini-copernicus", "inspect_cop_network", network_path=cop["network_path"])
for family in ("pyro", "flip", "rbd", "vellum"):
    setup = call(
        "houdini-simulation",
        "create_simulation_network",
        parent_path="/obj",
        simulation_type=family,
        network_name=family + "_probe",
    )
    validation = call(
        "houdini-simulation", "validate_simulation_setup", network_path=setup["network_path"], simulation_type=family
    )
    assert not validation["valid"] and not setup["simulation_verified"]
    assert not any("was not found" in error for error in validation["errors"])
box = geo.createNode("box", "box_probe")
call("houdini-geometry", "get_attribute_values", node_path=box.path(), attribute_name="P", limit=2)
call("houdini-geometry", "get_primitive_intrinsics", node_path=box.path(), primitive_index=0, names=["measuredarea"])
top = call("houdini-pdg", "create_pdg_network", parent_path="/obj", network_name="top_probe")
task = call(
    "houdini-pdg", "create_pdg_node", network_path=top["network_path"], node_type="wedge", parameters={"wedgecount": 2}
)
snapshot = call("houdini-pdg", "inspect_pdg_graph", node_path=task["node_path"])
cook = call("houdini-pdg", "cook_pdg_graph", node_path=task["node_path"], block=True)
assert cook["outcome"] == "completed" and cook["work_item_count"] == 2, cook
print("HOUDINI_CAPABILITY_PROBE_PASSED", flush=True)
