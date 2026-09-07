"""Copernicus-only helpers; legacy COP2 networks are rejected."""

from dcc_mcp_houdini._domain_graph import get_node, require_category, validate_node_type

FILTER_TYPES = {"comp": "blend", "composite": "blend", "color_correct": "colorcorrect", "output": "rop_image"}


def require_cop_network(hou, node_path):
    return require_category(get_node(hou, node_path), "Cop", children=True)


def resolve_filter_type(filter_type):
    value = validate_node_type(filter_type)
    return FILTER_TYPES.get(value, value)
