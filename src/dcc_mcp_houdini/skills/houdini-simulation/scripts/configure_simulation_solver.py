"""Apply bounded parameters to an existing simulation solver."""

from __future__ import annotations

from _simulation_common import get_node, hou_missing_error, node_summary, set_parameters  # noqa: E402
from dcc_mcp_core.skill import skill_entry, skill_exception, skill_success


def configure_simulation_solver(solver_path: str, parameters, cook: bool = False) -> dict:
    try:
        import hou  # noqa: PLC0415
    except ImportError:
        return hou_missing_error()
    try:
        solver = get_node(hou, solver_path)
        applied, skipped = set_parameters(solver, parameters)
        if cook:
            solver.cook(force=True)
        summary = node_summary(solver)
        return skill_success(
            "Configured simulation solver",
            solver=summary,
            solver_path=solver.path(),
            applied_parameters=applied,
            skipped_parameters=skipped,
            cooked=bool(cook),
            valid=not summary["errors"],
        )
    except Exception as exc:
        return skill_exception(exc, message="Failed to configure simulation solver")


@skill_entry
def main(**kwargs) -> dict:
    return configure_simulation_solver(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
