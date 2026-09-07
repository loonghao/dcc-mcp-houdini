"""Connect TOP dependencies with category checks and rollback on failed readback."""

from dcc_mcp_core.skill import skill_entry, skill_exception, skill_success

from dcc_mcp_houdini._domain_graph import get_node, hou_missing_error, input_connections, require_category


def connect_pdg_nodes(output_node_path: str, input_node_path: str, input_index: int = 0, output_index: int = 0) -> dict:
    try:
        import hou
    except ImportError:
        return hou_missing_error()
    try:
        for value in (input_index, output_index):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 1024:
                raise ValueError("connection indices must be integers from 0 to 1024")
        sink = require_category(get_node(hou, output_node_path), "Top")
        source = require_category(get_node(hou, input_node_path), "Top")
        if sink.parent() != source.parent():
            raise ValueError("TOP nodes must share a parent network")
        previous = next((c for c in sink.inputConnections() if c.inputIndex() == input_index), None)
        old_source = previous.inputItem() if previous else None
        old_output = previous.inputItemOutputIndex() if previous else 0
        try:
            sink.setInput(input_index, source, output_index)
            expected = {"input_index": input_index, "source_path": source.path(), "source_output_index": output_index}
            if expected not in input_connections(sink):
                raise RuntimeError("TOP connection readback mismatch")
            return skill_success(
                "Connected PDG nodes",
                output_node_path=sink.path(),
                input_node_path=source.path(),
                input_index=input_index,
                output_index=output_index,
            )
        except BaseException:
            sink.setInput(input_index, old_source, old_output)
            raise
    except Exception as exc:
        return skill_exception(exc, message="Failed to connect PDG nodes")


@skill_entry
def main(**kwargs):
    return connect_pdg_nodes(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
