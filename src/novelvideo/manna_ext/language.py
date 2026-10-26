"""Manna Studio language policy: English content everywhere, film language per project.

Upstream hook points: utils/source_language.py, task_backend/run_core.py, chat/service.py,
api/routes/freezone.py (see Manna Studio docs/upstream-patches.md).
"""

from __future__ import annotations

import contextvars
import json
import os
from pathlib import Path
from typing import Literal

FilmLanguage = Literal["en", "vi"]

VIETNAMESE_FILM_RULE = (
    "This is a Vietnamese-language film. Write all spoken dialogue, narration, "
    "captions/subtitles, on-screen text and character names in Vietnamese with full "
    "diacritics. Keep every other field (descriptions, shot plans, camera, lighting, "
    "image and video prompts) in English. Quote dialogue verbatim."
)

_FILM_LANGUAGE: contextvars.ContextVar[FilmLanguage] = contextvars.ContextVar(
    "manna_film_language", default="en"
)


def manna_asset_language() -> Literal["en"] | None:
    return "en" if os.environ.get("MANNA_ASSET_LANGUAGE", "").strip().lower() == "en" else None


def normalize_film_language(value: object) -> FilmLanguage:
    return "vi" if str(value or "").strip().lower() == "vi" else "en"


def film_language_rule(lang: FilmLanguage) -> str:
    return VIETNAMESE_FILM_RULE if lang == "vi" else ""


def current_film_language() -> FilmLanguage:
    return _FILM_LANGUAGE.get()


def bind_film_language(lang: object) -> contextvars.Token:
    return _FILM_LANGUAGE.set(normalize_film_language(lang))


def reset_film_language(token: contextvars.Token) -> None:
    _FILM_LANGUAGE.reset(token)


def load_film_language_from_state_dir(state_dir: str | Path | None) -> FilmLanguage:
    if not state_dir:
        return "en"
    try:
        data = json.loads((Path(state_dir) / "project_config.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "en"
    return normalize_film_language(data.get("film_language") if isinstance(data, dict) else None)


def bind_film_language_from_state_dir(state_dir: str | Path | None) -> contextvars.Token:
    return bind_film_language(load_film_language_from_state_dir(state_dir))


def instruction_suffix() -> str:
    """Film rule appended to upstream's English asset-language instruction."""
    if manna_asset_language() is None:
        return ""
    rule = film_language_rule(current_film_language())
    return f" {rule}" if rule else ""
