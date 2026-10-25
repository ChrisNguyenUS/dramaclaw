"""English display names for the builtin catalogs (styles, recipes, skills).

Only display fields are replaced, by item id. Prompts, triggers, option values
and ids are never touched, and items without an overlay entry pass through.
Hooked at the builtin layer only, so project overlay and per-user items keep
whatever names they carry.
"""

import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

CatalogKind = Literal["styles", "recipes", "skills"]

_DATA_DIR = Path(__file__).with_name("catalog_en")
_DISPLAY_FIELDS = ("label", "name", "category", "description")


@lru_cache(maxsize=None)
def _overlay(kind: str) -> dict[str, dict[str, Any]]:
    path = _DATA_DIR / f"{kind}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def apply_catalog_en(kind: CatalogKind, items: list[dict]) -> list[dict]:
    """Return copies of ``items`` with English display fields from the overlay."""
    overlay = _overlay(kind)
    out: list[dict] = []
    for item in items:
        copied = deepcopy(item)
        entry = overlay.get(str(copied.get("id"))) if isinstance(copied, dict) else None
        if entry:
            for field in _DISPLAY_FIELDS:
                if field in entry and field in copied:
                    copied[field] = entry[field]
            labels = entry.get("input_parameters")
            if labels and isinstance(copied.get("input_parameters"), list):
                for param in copied["input_parameters"]:
                    if isinstance(param, dict) and param.get("id") in labels:
                        param["label"] = labels[param["id"]]
        out.append(copied)
    return out
