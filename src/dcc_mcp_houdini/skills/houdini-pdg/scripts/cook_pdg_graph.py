"""Cook TOP work items once, reporting failures and incomplete state explicitly."""

from _pdg_common import graph_snapshot
from dcc_mcp_core.skill import skill_entry, skill_exception, skill_success

from dcc_mcp_houdini._domain_graph import get_node, hou_missing_error


def cook_pdg_graph(node_path: str, block: bool = True) -> dict:
    try:
        import hou
    except ImportError:
        return hou_missing_error()
    try:
        if not isinstance(block, bool):
            raise ValueError("block must be boolean")
        node = get_node(hou, node_path)
        category = node.childTypeCategory()
        network = category is not None and category.name() == "Top"
        # A container cooks its output node, a task cooks its own branch.
        cook = getattr(node, "cookOutputWorkItems" if network else "cookWorkItems", None)
        if not callable(cook):
            raise ValueError("Node does not support TOP cooking")
        cook(block=block)
        snapshot = graph_snapshot(node)
        errors = list(snapshot["node"]["errors"])
        for child in snapshot["children"]:
            errors.extend("{}: {}".format(child["path"], error) for error in child["errors"])
        states = snapshot["work_item_states"]
        failed = any(states.get(key, 0) for key in ("CookedFail", "CookedCancel"))
        completed = (
            block
            and snapshot["work_items_available"]
            and bool(snapshot["work_item_count"])
            and all(key in ("CookedSuccess", "CookedCache") for key in states)
            and not errors
        )
        outcome = "failed" if failed or errors else "completed" if completed else "incomplete" if block else "submitted"
        return skill_success(
            "PDG cook inspected",
            node_path=node.path(),
            block=block,
            valid=completed,
            outcome=outcome,
            errors=errors,
            **snapshot,
        )
    except Exception as exc:
        return skill_exception(exc, message="Failed to cook PDG graph")


@skill_entry
def main(**kwargs):
    return cook_pdg_graph(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
