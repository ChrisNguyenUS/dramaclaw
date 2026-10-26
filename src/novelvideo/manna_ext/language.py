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


def load_film_language_for_project(username: str, project: str) -> FilmLanguage:
    try:
        from novelvideo.project_config import load_project_config

        return normalize_film_language(load_project_config(username, project).get("film_language"))
    except Exception:
        return "en"


def agent_language_block(film_language: str) -> str:
    if manna_asset_language() is None:
        return ""
    rule = film_language_rule(normalize_film_language(film_language))
    body = (
        "You are Manna Director, the Manna Studio assistant; never call yourself DramaClaw, "
        "虾导 or 虾画 (Manna Canvas is the canvas). "  # i18n-exempt: names the assistant must not use
        "Write every script, storyboard, shot plan and image/video prompt in English."
    )
    return f"[MANNA_LANGUAGE]\n{body}{(' ' + rule) if rule else ''}\n[/MANNA_LANGUAGE]\n\n"


def recipe_language_line() -> str:
    if manna_asset_language() is None:
        return ""
    rule = film_language_rule(current_film_language())
    return "\n\nLanguage: write the output in English." + (f" {rule}" if rule else "")


# Placement-free tasks may run on a node without the project's state, so the API side copies
# the film language into the task payload (hook: task_backend/client.py enqueue_project_task).
PAYLOAD_KEY = "manna_film_language"


def payload_with_film_language(state_dir: str | Path | None, payload: dict | None) -> dict | None:
    if manna_asset_language() is None:
        return payload
    return {**(payload or {}), PAYLOAD_KEY: load_film_language_from_state_dir(state_dir)}


def task_film_language(
    payload: object, state_dir: str | Path | None, *, may_read_state: bool
) -> FilmLanguage:
    """Worker side: payload first; project state only for home-node-bound tasks."""
    if isinstance(payload, dict) and PAYLOAD_KEY in payload:
        return normalize_film_language(payload[PAYLOAD_KEY])
    return load_film_language_from_state_dir(state_dir) if may_read_state else "en"
