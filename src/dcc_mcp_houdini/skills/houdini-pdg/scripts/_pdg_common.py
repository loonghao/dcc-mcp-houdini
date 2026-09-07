"""TOP graph inspection using documented PDG work-item properties."""

from dcc_mcp_houdini._domain_graph import input_connections, node_summary, require_category


def graph_snapshot(node):
    category = node.childTypeCategory()
    targets = list(node.children()) if category is not None and category.name() == "Top" else [node]
    result = {
        "node": node_summary(node),
        "children": [],
        "work_item_count": 0,
        "work_item_states": {},
        "work_items_available": bool(targets),
    }
    for target in targets:
        require_category(target, "Top")
        summary = node_summary(target)
        summary["inputs"] = input_connections(target)
        result["children"].append(summary)
        if target.isScheduler():
            continue
        pdg_node = target.getPDGNode()
        if pdg_node is None:
            result["work_items_available"] = False
            continue
        for item in pdg_node.workItems:
            state = item.state
            name = getattr(state, "name", None)
            name = name() if callable(name) else name
            key = str(name or state).rsplit(".", 1)[-1]
            result["work_item_states"][key] = result["work_item_states"].get(key, 0) + 1
            result["work_item_count"] += 1
    if not result["work_items_available"]:
        result["work_item_count"] = None
    return result
