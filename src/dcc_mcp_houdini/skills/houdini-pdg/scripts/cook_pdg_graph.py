"""Cook a PDG graph and return explicit work-item readback."""

from __future__ import annotations

from _pdg_common import get_node, graph_snapshot, hou_missing_error  # noqa: E402
from dcc_mcp_core.skill import skill_entry, skill_exception, skill_success


def cook_pdg_graph(node_path: str, block: bool = True) -> dict:
    try:
        import hou  # noqa: PLC0415
    except ImportError:
        return hou_missing_error()
    try:
        node = get_node(hou, node_path)
        cook = getattr(node, "cookWorkItems", None)
        if not callable(cook):
            raise ValueError("Node does not expose cookWorkItems: {}".format(node_path))
        try:
            cook(block=bool(block))
        except TypeError:
            cook()
        snapshot = graph_snapshot(node)
        errors = list(snapshot.get("node", {}).get("errors", []))
        return skill_success(
            "Cooked PDG graph", node_path=node.path(), block=bool(block), valid=not errors, errors=errors, **snapshot
        )
    except Exception as exc:
        return skill_exception(exc, message="Failed to cook PDG graph")


@skill_entry
def main(**kwargs) -> dict:
    return cook_pdg_graph(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
