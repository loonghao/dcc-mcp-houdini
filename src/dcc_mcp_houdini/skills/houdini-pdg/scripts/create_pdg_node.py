"""Create and wire a bounded TOP node."""

from __future__ import annotations

from _pdg_common import get_node, hou_missing_error, set_parameters, validate_identifier  # noqa: E402
from dcc_mcp_core.skill import skill_entry, skill_exception, skill_success


def create_pdg_node(
    network_path: str,
    node_type: str,
    node_name: str = None,
    input_nodes=None,
    parameters=None,
) -> dict:
    try:
        import hou  # noqa: PLC0415
    except ImportError:
        return hou_missing_error()
    try:
        network = get_node(hou, network_path)
        node_type = validate_identifier(node_type, "PDG node type")
        node = network.createNode(node_type, node_name=node_name)
        applied, skipped = set_parameters(node, parameters)
        wired = []
        for index, input_path in enumerate(input_nodes or []):
            source = hou.node(input_path)
            if source is None and not str(input_path).startswith("/"):
                source = network.node(str(input_path))
            if source is None:
                raise ValueError("PDG input node not found: {}".format(input_path))
            node.setInput(index, source)
            wired.append({"input_index": index, "source_path": source.path()})
        try:
            network.layoutChildren()
        except Exception:  # noqa: BLE001
            pass
        return skill_success(
            "Created PDG node",
            network_path=network.path(),
            node_path=node.path(),
            node_type=node_type,
            applied_parameters=applied,
            skipped_parameters=skipped,
            wired_inputs=wired,
        )
    except Exception as exc:
        return skill_exception(exc, message="Failed to create PDG node")


@skill_entry
def main(**kwargs) -> dict:
    return create_pdg_node(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
