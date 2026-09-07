"""Create a Cop node with parameter and input readback."""

from _cop_common import resolve_filter_type
from dcc_mcp_core.skill import skill_entry, skill_exception, skill_success

from dcc_mcp_houdini._domain_graph import (
    get_node,
    hou_missing_error,
    input_connections,
    owned_node,
    require_category,
    resolve_inputs,
    set_parameters,
    validate_parameters,
)


def create_cop_node(
    network_path: str, filter_type: str, node_name: str = None, input_nodes=None, parameters=None
) -> dict:
    try:
        import hou
    except ImportError:
        return hou_missing_error()
    try:
        network = require_category(get_node(hou, network_path), "Cop", children=True)
        node_type = resolve_filter_type(filter_type)
        validate_parameters(parameters)
        sources = resolve_inputs(hou, network, input_nodes)
        with owned_node(network, node_type, node_name) as node:
            applied, skipped = set_parameters(node, parameters)
            for index, source in enumerate(sources):
                node.setInput(index, source)
            wired = input_connections(node)
            if [(item["input_index"], item["source_path"]) for item in wired] != list(
                enumerate(s.path() for s in sources)
            ):
                raise RuntimeError("Input wiring readback mismatch")
            return skill_success(
                "Created Cop node",
                network_path=network.path(),
                node_path=node.path(),
                node_type=node.type().name(),
                applied_parameters=applied,
                skipped_parameters=skipped,
                wired_inputs=wired,
            )
    except Exception as exc:
        return skill_exception(exc, message="Failed to create Cop node")


@skill_entry
def main(**kwargs):
    return create_cop_node(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
