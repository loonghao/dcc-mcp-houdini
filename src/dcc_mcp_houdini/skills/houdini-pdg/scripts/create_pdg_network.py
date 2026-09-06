"""Create or reuse a TOP network container."""

from __future__ import annotations

from _pdg_common import get_node, hou_missing_error  # noqa: E402
from dcc_mcp_core.skill import skill_entry, skill_exception, skill_success


def create_pdg_network(parent_path: str, network_name: str = "topnet1") -> dict:
    try:
        import hou  # noqa: PLC0415
    except ImportError:
        return hou_missing_error()
    try:
        parent = get_node(hou, parent_path)
        network_path = "{}/{}".format(parent.path().rstrip("/"), network_name)
        network = hou.node(network_path)
        created = False
        if network is None:
            network = parent.createNode("topnet", node_name=network_name)
            created = True
        return skill_success(
            "Created PDG network",
            network_path=network.path(),
            network_name=network.name(),
            created=created,
        )
    except Exception as exc:
        return skill_exception(exc, message="Failed to create PDG network")


@skill_entry
def main(**kwargs) -> dict:
    return create_pdg_network(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
