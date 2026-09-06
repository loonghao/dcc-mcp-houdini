"""Connect a downstream TOP node to an upstream dependency."""

from __future__ import annotations

from _pdg_common import get_node, hou_missing_error  # noqa: E402
from dcc_mcp_core.skill import skill_entry, skill_exception, skill_success


def connect_pdg_nodes(
    output_node_path: str,
    input_node_path: str,
    input_index: int = 0,
    output_index: int = 0,
) -> dict:
    try:
        import hou  # noqa: PLC0415
    except ImportError:
        return hou_missing_error()
    try:
        if not isinstance(input_index, int) or input_index < 0:
            raise ValueError("input_index must be a non-negative integer")
        if not isinstance(output_index, int) or output_index < 0:
            raise ValueError("output_index must be a non-negative integer")
        output_node = get_node(hou, output_node_path)
        input_node = get_node(hou, input_node_path)
        output_node.setInput(input_index, input_node, output_index)
        return skill_success(
            "Connected PDG nodes",
            output_node_path=output_node.path(),
            input_node_path=input_node.path(),
            input_index=input_index,
            output_index=output_index,
        )
    except Exception as exc:
        return skill_exception(exc, message="Failed to connect PDG nodes")


@skill_entry
def main(**kwargs) -> dict:
    return connect_pdg_nodes(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
