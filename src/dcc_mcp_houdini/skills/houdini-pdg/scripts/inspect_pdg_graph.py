"""Inspect PDG graph structure and work-item states."""

from __future__ import annotations

from _pdg_common import get_node, graph_snapshot, hou_missing_error  # noqa: E402
from dcc_mcp_core.skill import skill_entry, skill_exception, skill_success


def inspect_pdg_graph(node_path: str) -> dict:
    try:
        import hou  # noqa: PLC0415
    except ImportError:
        return hou_missing_error()
    try:
        node = get_node(hou, node_path)
        snapshot = graph_snapshot(node)
        return skill_success("Inspected PDG graph", node_path=node.path(), **snapshot)
    except Exception as exc:
        return skill_exception(exc, message="Failed to inspect PDG graph")


@skill_entry
def main(**kwargs) -> dict:
    return inspect_pdg_graph(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
