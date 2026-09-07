"""Inspect COP nodes and their graph connections."""

from __future__ import annotations

from _cop_common import require_cop_network
from dcc_mcp_core.skill import skill_entry, skill_exception, skill_success

from dcc_mcp_houdini._domain_graph import hou_missing_error, input_connections, node_summary


def inspect_cop_network(network_path: str) -> dict:
    try:
        import hou  # noqa: PLC0415
    except ImportError:
        return hou_missing_error()
    try:
        network = require_cop_network(hou, network_path)
        nodes = []
        for child in network.children():
            summary = node_summary(child)
            summary["inputs"] = input_connections(child)
            nodes.append(summary)
        return skill_success(
            "Inspected COP network",
            network_path=network.path(),
            node_count=len(nodes),
            nodes=nodes,
        )
    except Exception as exc:
        return skill_exception(exc, message="Failed to inspect COP network")


@skill_entry
def main(**kwargs) -> dict:
    return inspect_cop_network(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
