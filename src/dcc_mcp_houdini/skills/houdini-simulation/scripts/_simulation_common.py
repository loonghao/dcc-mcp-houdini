"""DOP skeleton authoring and cached diagnostics."""

from dcc_mcp_houdini._domain_graph import node_summary

SOLVER_TYPES = {"pyro": "pyrosolver", "flip": "flipsolver", "rbd": "rbdsolver", "vellum": "vellumsolver"}


def solver_base_type(type_name):
    parts = type_name.split("::")
    if len(parts) > 1 and parts[-1][:1].isdigit():
        parts.pop()
    return parts[-1]


def validate_simulation_type(simulation_type):
    if simulation_type not in SOLVER_TYPES:
        raise ValueError("Unsupported simulation_type: {!r}".format(simulation_type))
    return simulation_type


def children_summary(node):
    return [node_summary(child) for child in node.children()]
