"""JSON-safe bounded values shared by USD and geometry inspection."""

from __future__ import annotations

import json
import math
from typing import Any, Dict, Tuple


def require_range(value: int, label: str, minimum: int, maximum: int) -> int:
    """Validate an integer bound for callers that bypass JSON Schema."""
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ValueError("{} must be an integer from {} to {}".format(label, minimum, maximum))
    return value


def _json_safe(value: Any, budget: Dict[str, int]) -> Tuple[Any, bool]:
    if value is None or isinstance(value, (bool, int, str)):
        return value, False
    if isinstance(value, float):
        return (value, False) if math.isfinite(value) else (str(value), False)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace"), False

    if isinstance(value, dict):
        output: Dict[str, Any] = {}
        truncated = False
        for key, item in value.items():
            if budget["remaining"] <= 0:
                truncated = True
                break
            budget["remaining"] -= 1
            output[str(key)], child_truncated = _json_safe(item, budget)
            truncated = truncated or child_truncated
        return output, truncated

    if not isinstance(value, (str, bytes)):
        try:
            iterator = iter(value)
        except TypeError:
            iterator = None
        if iterator is not None:
            output = []
            truncated = False
            while budget["remaining"] > 0:
                try:
                    item = next(iterator)
                except StopIteration:
                    break
                budget["remaining"] -= 1
                converted, child_truncated = _json_safe(item, budget)
                output.append(converted)
                truncated = truncated or child_truncated
            else:
                try:
                    next(iterator)
                except StopIteration:
                    pass
                else:
                    truncated = True
            return output, truncated

    path = getattr(value, "path", None)
    if isinstance(path, str):
        return path, False
    return str(value), False


def bounded_value(value: Any, max_items: int, max_chars: int) -> dict:
    """Return a JSON-safe value with explicit item and serialized-size bounds."""
    require_range(max_items, "max_value_items", 1, 256)
    require_range(max_chars, "max_value_chars", 64, 4096)
    converted, item_truncated = _json_safe(value, {"remaining": max_items})
    serialized = json.dumps(converted, ensure_ascii=False, separators=(",", ":"))
    if len(serialized) > max_chars:
        return {
            "value": None,
            "value_preview": serialized[:max_chars],
            "truncated": True,
            "truncation_reasons": ["characters"] + (["items"] if item_truncated else []),
        }
    return {
        "value": converted,
        "truncated": item_truncated,
        "truncation_reasons": ["items"] if item_truncated else [],
    }
