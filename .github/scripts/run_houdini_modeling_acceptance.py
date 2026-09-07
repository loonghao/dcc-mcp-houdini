"""Live MCP acceptance for the three modeling operations in issue 266.

Run in a fresh hython process with this checkout installed. This focused
fixture is not a replay of the full reference asset evaluation.
"""

from __future__ import annotations

import json
import uuid

import hou
from run_houdini_e2e import _call_tool, _find_tool, _post, _serve_with_client_worker, _tool_names

import dcc_mcp_houdini


def _run_client(server):
    url = server.mcp_url
    _post(
        url,
        "initialize",
        {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "houdini-modeling-acceptance", "version": "1"},
        },
    )
    for skill in ("houdini-nodes", "houdini-geometry", "houdini-mesh-ops"):
        _call_tool(url, "load_skill", {"skill_name": skill})
    names, seen, cursor = [], set(), None
    for _ in range(256):
        payload = _post(url, "tools/list", {"cursor": cursor} if cursor else None)
        names.extend(_tool_names(payload))
        cursor = payload.get("result", {}).get("nextCursor")
        if not cursor:
            break
        assert cursor not in seen, "repeated tools/list cursor"
        seen.add(cursor)
    else:
        raise AssertionError("tools/list exceeded 256 pages")
    calls = []

    def call(name, **arguments):
        assert name != "execute_python"
        payload = _call_tool(url, _find_tool(names, name), arguments)
        calls.append({"tool": name, "success": payload.get("success") is True})
        print(json.dumps(calls[-1]), flush=True)
        assert payload.get("success") is True, payload
        return payload.get("context", {})

    name = "modeling_acceptance_" + uuid.uuid4().hex[:8]
    geo_path = "/obj/" + name
    call("create_node", parent_path="/obj", node_type="geo", node_name=name)
    try:
        sections = []
        for index, (length, radius) in enumerate(((-2, 0.3), (0, 0.8), (2, 0.5))):
            section_name = "fuselage_section_{}".format(index)
            path = geo_path + "/" + section_name
            call("create_node", parent_path=geo_path, node_type="circle", node_name=section_name)
            call(
                "set_node_parms",
                node_path=path,
                parameters={"type": "poly", "divs": 8, "rad": [radius, radius], "t": [0, 0, length]},
            )
            sections.append(path)
        hull = call("loft_sections", sections=sections, node_name="fuselage")
        assert hull["readback"]["verified"] and hull["readback"]["primitive_count"] > 0
        call("create_primitive", parent_path=geo_path, primitive="box", node_name="rim")
        rim = call("bevel_edges", input_path=geo_path + "/rim", group="*", distance=0.05, divisions=2)
        assert rim["readback"]["verified"]
        assert rim["readback"]["point_count"] > rim["readback"]["before"]["point_count"]
        call("create_primitive", parent_path=geo_path, primitive="box", node_name="rotor_blade")
        call(
            "set_node_parms", node_path=geo_path + "/rotor_blade", parameters={"size": [2, 0.08, 0.25], "t": [1, 0, 0]}
        )
        rotor = call(
            "array_instances",
            input_path=geo_path + "/rotor_blade",
            count=4,
            radius=0.15,
            axis="y",
            source_forward="+x",
            node_name="rotor_array",
        )
        assert rotor["readback"]["orientation"]["verified"]
        assert rotor["readback"]["orientation"]["point_count"] == 4
        assert rotor["readback"]["point_count"] == 4 * rotor["readback"]["before"]["point_count"]
        print(
            "Houdini modeling acceptance passed: "
            + json.dumps(
                {
                    "scope": "focused loft, bevel and rotor fixture",
                    "typed_calls": len(calls),
                    "raw_scripting_calls": 0,
                    "raw_scripting_share": 0.0,
                    "hull_primitives": hull["readback"]["primitive_count"],
                    "bevel_points": rim["readback"]["point_count"],
                    "rotor_points": rotor["readback"]["point_count"],
                }
            ),
            flush=True,
        )
    finally:
        call("delete_node", node_path=geo_path)


def main():
    print("Houdini:", hou.applicationVersionString(), flush=True)
    _serve_with_client_worker(
        dcc_mcp_houdini.serve_headless, _run_client, join_timeout=30, port=0, gateway_port=0, register_builtins=True
    )


if __name__ == "__main__":
    main()
