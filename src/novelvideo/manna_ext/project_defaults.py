"""Manna defaults for newly created projects (hook: api/routes/projects.py create)."""

from __future__ import annotations

from novelvideo.manna_ext.language import manna_asset_language, normalize_film_language

# Empty ethnicity adds no default-ethnicity rule (upstream's default would force "Chinese").
_ETHNICITY_BY_FILM_LANGUAGE = {"en": "", "vi": "Vietnamese"}


def manna_create_config(film_language: object) -> dict:
    if manna_asset_language() is None:
        return {}
    lang = normalize_film_language(film_language)
    return {
        "film_language": lang,
        "ethnicity": _ETHNICITY_BY_FILM_LANGUAGE[lang],
        "visual_style": "realistic",
        "aspect_ratio": "9:16",
    }
