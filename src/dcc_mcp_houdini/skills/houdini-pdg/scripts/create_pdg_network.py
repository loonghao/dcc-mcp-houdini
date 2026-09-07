"""Create or reuse a category-checked Top network."""

from dcc_mcp_core.skill import skill_entry, skill_exception, skill_success

from dcc_mcp_houdini._domain_graph import get_node, hou_missing_error, owned_node, require_category, validate_identifier


def create_pdg_network(parent_path: str, network_name: str = "topnet1") -> dict:
    try:
        import hou
    except ImportError:
        return hou_missing_error()
    try:
        validate_identifier(network_name)
        parent = get_node(hou, parent_path)
        existing = parent.node(network_name)
        if existing is not None:
            require_category(existing, "Top", children=True)
            return skill_success(
                "Reused Top network", network_path=existing.path(), network_name=existing.name(), created=False
            )
        with owned_node(parent, "topnet", network_name) as network:
            require_category(network, "Top", children=True)
            return skill_success(
                "Created Top network", network_path=network.path(), network_name=network.name(), created=True
            )
    except Exception as exc:
        return skill_exception(exc, message="Failed to create Top network")


@skill_entry
def main(**kwargs):
    return create_pdg_network(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
