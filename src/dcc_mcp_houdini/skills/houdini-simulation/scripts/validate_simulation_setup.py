"""Validate a DOP network before a long simulation cook."""

from __future__ import annotations

from _simulation_common import (  # noqa: E402
    SOLVER_TYPES,
    get_node,
    hou_missing_error,
    node_summary,
    validate_simulation_type,
)
from dcc_mcp_core.skill import skill_entry, skill_exception, skill_success


def validate_simulation_setup(network_path: str, simulation_type: str = None) -> dict:
    try:
        import hou  # noqa: PLC0415
    except ImportError:
        return hou_missing_error()
    try:
        network = get_node(hou, network_path)
        expected = validate_simulation_type(simulation_type) if simulation_type else None
        children = list(network.children())
        solver_children = []
        for child in children:
            summary = node_summary(child)
            if str(summary.get("type", "")).lower().endswith("solver"):
                solver_children.append(summary)
        errors = list(node_summary(network).get("errors", []))
        warnings = list(node_summary(network).get("warnings", []))
        if not solver_children:
            errors.append("No simulation solver found in DOP network")
        if expected and not any(item.get("type") == SOLVER_TYPES[expected] for item in solver_children):
            errors.append("Expected {} solver ({}) was not found".format(expected, SOLVER_TYPES[expected]))
        return skill_success(
            "Validated simulation setup",
            network_path=network.path(),
            simulation_type=expected,
            valid=not errors,
            errors=errors,
            warnings=warnings,
            solver_count=len(solver_children),
            solvers=solver_children,
        )
    except Exception as exc:
        return skill_exception(exc, message="Failed to validate simulation setup")


@skill_entry
def main(**kwargs) -> dict:
    return validate_simulation_setup(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
