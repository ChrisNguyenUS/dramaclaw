"""Manna English agent catalog: full replacements for builtin recipes/skills plus Manna's own
(UGC pack). Layered over the builtins only when MANNA_ASSET_LANGUAGE=en.

Hook point: freezone/agent_config_store.py list_user_agent_config_items.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from novelvideo.manna_ext.language import manna_asset_language

_ROOT = Path(__file__).resolve().parent


def overlay_dir(kind: str) -> Path | None:
    if manna_asset_language() is None:
        return None
    return _ROOT / kind


def overlay_items(kind: str, reader: Callable[[Path], list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Read the overlay with the upstream reader (same schema validation)."""
    root = overlay_dir(kind)
    return reader(root) if root is not None and root.is_dir() else []


def overlay_signature(kind: str, signature: Callable[[Path], Any]) -> Any:
    root = overlay_dir(kind)
    return ("manna-en", signature(root)) if root is not None else None
