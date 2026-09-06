"""Create a typed DOP simulation network and solver."""

from __future__ import annotations

from _simulation_common import (  # noqa: E402
    SOLVER_TYPES,
    get_node,
    hou_missing_error,
    set_parameters,
    validate_simulation_type,
)
from dcc_mcp_core.skill import skill_entry, skill_exception, skill_success


def create_simulation_network(
    parent_path: str,
    simulation_type: str,
    network_name: str = "dopnet1",
    solver_name: str = None,
    parameters=None,
) -> dict:
    try:
        import hou  # noqa: PLC0415
    except ImportError:
        return hou_missing_error()
    try:
        kind = validate_simulation_type(simulation_type)
        parent = get_node(hou, parent_path)
        network_path = "{}/{}".format(parent.path().rstrip("/"), network_name)
        network = hou.node(network_path)
        created_network = False
        if network is None:
            network = parent.createNode("dopnet", node_name=network_name)
            created_network = True
        solver_name = solver_name or "{}solver1".format(kind)
        solver = network.node(solver_name) if hasattr(network, "node") else None
        created_solver = False
        if solver is None:
            solver = network.createNode(SOLVER_TYPES[kind], node_name=solver_name)
            created_solver = True
        applied, skipped = set_parameters(solver, parameters)
        try:
            network.layoutChildren()
        except Exception:  # noqa: BLE001
            pass
        return skill_success(
            "Created simulation setup",
            simulation_type=kind,
            solver_type=SOLVER_TYPES[kind],
            network_path=network.path(),
            solver_path=solver.path(),
            created_network=created_network,
            created_solver=created_solver,
            applied_parameters=applied,
            skipped_parameters=skipped,
        )
    except Exception as exc:
        return skill_exception(exc, message="Failed to create simulation network")


@skill_entry
def main(**kwargs) -> dict:
    return create_simulation_network(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
