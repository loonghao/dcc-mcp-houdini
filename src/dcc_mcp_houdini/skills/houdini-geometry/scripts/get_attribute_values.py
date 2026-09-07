"""Read a bounded page of geometry attribute values."""

from _geo_common import cooked_geometry, get_node
from dcc_mcp_core.skill import skill_entry, skill_error, skill_exception, skill_success

from dcc_mcp_houdini._bounded_values import bounded_value, require_range


def get_attribute_values(
    node_path: str, attribute_name: str, attribute_class: str = "point", offset: int = 0, limit: int = 32
) -> dict:
    try:
        import hou
    except ImportError:
        return skill_error("Houdini not available", "hou could not be imported")
    try:
        require_range(offset, "offset", 0, 2147483647)
        require_range(limit, "limit", 1, 128)
        if not isinstance(attribute_name, str) or not 1 <= len(attribute_name) <= 256:
            raise ValueError("attribute_name must contain 1 to 256 characters")
        methods = {
            "point": ("findPointAttrib", "pointCount", "point"),
            "primitive": ("findPrimAttrib", "primCount", "prim"),
            "vertex": ("findVertexAttrib", "vertexCount", "vertex"),
            "detail": ("findGlobalAttrib", None, None),
        }
        if attribute_class not in methods:
            raise ValueError("attribute_class must be point, primitive, vertex or detail")
        node = get_node(hou, node_path)
        geo = cooked_geometry(node)
        lookup, count, accessor = methods[attribute_class]
        attribute = getattr(geo, lookup)(attribute_name)
        if attribute is None:
            raise ValueError("Attribute not found in requested class: {}".format(attribute_name))
        total = getattr(geo, count)() if count else 1
        rows = []
        for index in range(offset, min(total, offset + limit)):
            element = getattr(geo, accessor)(index) if accessor else geo
            if element is None:
                raise RuntimeError("Geometry changed during attribute inspection")
            rows.append(dict(index=index, **bounded_value(element.attribValue(attribute), 64, 1024)))
        next_offset = offset + len(rows)
        return skill_success(
            "Read geometry attributes",
            node_path=node.path(),
            attribute_name=attribute_name,
            attribute_class=attribute_class,
            data_type=str(attribute.dataType()),
            tuple_size=attribute.size(),
            total_count=total,
            offset=offset,
            count=len(rows),
            values=rows,
            next_offset=next_offset if next_offset < total else None,
            values_truncated=any(row["truncated"] for row in rows),
        )
    except Exception as exc:
        return skill_exception(exc, message="Failed to read geometry attributes")


@skill_entry
def main(**kwargs):
    return get_attribute_values(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
