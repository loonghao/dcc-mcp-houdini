"""Validate COP node errors and input references."""

from __future__ import annotations

from _cop_common import require_cop_network
from dcc_mcp_core.skill import skill_entry, skill_exception, skill_success

from dcc_mcp_houdini._domain_graph import hou_missing_error, input_connections, node_summary


def validate_cop_network(network_path: str) -> dict:
    try:
        import hou  # noqa: PLC0415
    except ImportError:
        return hou_missing_error()
    try:
        network = require_cop_network(hou, network_path)
        errors = []
        warnings = []
        nodes = []
        for child in network.children():
            summary = node_summary(child)
            summary["inputs"] = input_connections(child)
            nodes.append(summary)
            errors.extend("{}: {}".format(summary["path"], message) for message in summary["errors"])
            warnings.extend("{}: {}".format(summary["path"], message) for message in summary["warnings"])
        if not nodes:
            warnings.append("COP network has no nodes")
        return skill_success(
            "Validated COP network",
            network_path=network.path(),
            valid=not errors and bool(nodes),
            validation_scope="cached_diagnostics",
            cooked=False,
            errors=errors,
            warnings=warnings,
            node_count=len(nodes),
            nodes=nodes,
        )
    except Exception as exc:
        return skill_exception(exc, message="Failed to validate COP network")


@skill_entry
def main(**kwargs) -> dict:
    return validate_cop_network(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
