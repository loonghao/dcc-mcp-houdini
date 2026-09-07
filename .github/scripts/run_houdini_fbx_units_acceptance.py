"""Check a real Filmbox export's physical size in a fresh licensed Hython.

This fixture reads the native ASCII FBX representation produced by Houdini 22.
It does not substitute for an engine import and world-bounds readback.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

import hou

import dcc_mcp_houdini

ROOT = Path(__file__).resolve().parents[2]
assert ROOT in Path(dcc_mcp_houdini.__file__).resolve().parents, "Install this checkout first"
sys.path.insert(0, str(ROOT / "tests"))
from skill_loader import skill_script_import_context  # noqa: E402


def main():
    path = ROOT / "src/dcc_mcp_houdini/skills/houdini-interchange/scripts/export_fbx.py"
    spec = importlib.util.spec_from_file_location("fbx_units_acceptance", path)
    module = importlib.util.module_from_spec(spec)
    with skill_script_import_context(spec):
        spec.loader.exec_module(module)
    parent = hou.node("/obj").createNode("geo", "unit_card", run_init_scripts=False)
    try:
        grid = parent.createNode("grid")
        grid.setParms({"orient": 0, "sizex": 2.8, "sizey": 4.2, "ty": 2.1, "rows": 2, "cols": 2})
        grid.setRenderFlag(True)
        directory = Path(tempfile.mkdtemp(prefix="houdini-fbx-units-"))
        measured = []
        for enabled in (True, False):
            output = directory / ("converted.fbx" if enabled else "numeric.fbx")
            kwargs = {} if enabled else {"convert_units": False}
            result = module.export_fbx(str(output), root_node=parent.path(), **kwargs)
            assert result["success"], result
            context = result["context"]
            assert context["unit_conversion_enabled"] is enabled
            assert context["written_files"] == [str(output)] and not context["warnings"]
            content = output.read_text(encoding="utf-8")
            vertices = re.search(r"Vertices:\s*\*\d+\s*\{\s*a:\s*([^}]+)", content)
            assert vertices, "Expected ASCII FBX geometry"
            coordinates = [float(value) for value in vertices.group(1).strip().split(",")]
            mesh_model = re.search(r'Model:\s*\d+,\s*"Model::[^"]+",\s*"Mesh"\s*\{(.*?)\n\t\}', content, re.S)
            assert mesh_model, "Expected FBX mesh model"
            scale = re.search(r'"Lcl Scaling"[^\n]*?,\s*"A",([^\n]+)', mesh_model.group(1))
            scale_x = float(scale.group(1).split(",")[0]) if scale else 1.0
            unit = re.search(r'"UnitScaleFactor"[^\n]*?,\s*"",([^\n]+)', content)
            assert unit, "Expected FBX unit declaration"
            unit_cm = float(unit.group(1))
            width_m = (max(coordinates[::3]) - min(coordinates[::3])) * scale_x * unit_cm / 100
            expected = 2.8 if enabled else 0.028
            assert abs(width_m - expected) < 1e-5, (enabled, width_m)
            measured.append({"convert_units": enabled, "physical_width_m": width_m})
            hou.node(context["rop"]["path"]).destroy()
        print(json.dumps({"houdini": hou.applicationVersionString(), "measurements": measured}))
        print("HOUDINI_FBX_UNITS_ACCEPTANCE_PASSED", flush=True)
    finally:
        parent.destroy()


if __name__ == "__main__":
    main()
