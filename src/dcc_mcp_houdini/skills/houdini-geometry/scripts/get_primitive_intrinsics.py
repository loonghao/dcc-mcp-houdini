"""Inspect named primitive intrinsics without copying all geometry."""

from _geo_common import cooked_geometry, get_node
from dcc_mcp_core.skill import skill_entry, skill_error, skill_exception, skill_success

from dcc_mcp_houdini._bounded_values import bounded_value, require_range


def get_primitive_intrinsics(node_path: str, primitive_index: int, names=None) -> dict:
    try:
        import hou
    except ImportError:
        return skill_error("Houdini not available", "hou could not be imported")
    try:
        require_range(primitive_index, "primitive_index", 0, 2147483647)
        if names is not None and (
            not isinstance(names, list)
            or not 1 <= len(names) <= 32
            or any(not isinstance(name, str) or not 1 <= len(name) <= 256 for name in names)
        ):
            raise ValueError("names must contain 1 to 32 intrinsic names")
        node = get_node(hou, node_path)
        prim = cooked_geometry(node).prim(primitive_index)
        if prim is None:
            raise ValueError("Primitive not found: {}".format(primitive_index))
        available = prim.intrinsicNames()
        selected = list(dict.fromkeys(names)) if names else list(available[:32])
        missing = [name for name in selected if name not in available]
        if missing:
            raise ValueError("Intrinsic not available on this primitive: {}".format(", ".join(missing)))
        values = {name: bounded_value(prim.intrinsicValue(name), 64, 1024) for name in selected}
        return skill_success(
            "Read primitive intrinsics",
            node_path=node.path(),
            primitive_index=primitive_index,
            primitive_type=str(prim.type()),
            available_names=list(available[:256]),
            available_names_truncated=len(available) > 256,
            intrinsics=values,
            values_truncated=any(value["truncated"] for value in values.values()),
            selection_truncated=names is None and len(available) > 32,
        )
    except Exception as exc:
        return skill_exception(exc, message="Failed to read primitive intrinsics")


@skill_entry
def main(**kwargs):
    return get_primitive_intrinsics(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
