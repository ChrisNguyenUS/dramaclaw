"""Manna TTS defaults: EdgeTTS voices follow the project's film language (P2b).

Hook points: freezone/audio_node.py (preset voice), audio/system_voice_setup.py,
generators/tts_generator.py (list_voices locale). A voice the user picks explicitly always wins.
Only active when MANNA_ASSET_LANGUAGE=en.
"""

from __future__ import annotations

from typing import Literal

from novelvideo.manna_ext.language import current_film_language, manna_asset_language

_VOICES = {
    "en": {
        "female": "en-US-JennyNeural", "male": "en-US-GuyNeural", "narrator": "en-US-AriaNeural", "locale": "en-US",
        "sample": "Hello, this is a system-generated reference voice.",
        "female_list": ("en-US-JennyNeural", "en-US-AriaNeural", "en-US-MichelleNeural"),
        "male_list": ("en-US-GuyNeural", "en-US-DavisNeural", "en-US-TonyNeural"),
    },
    "vi": {
        "female": "vi-VN-HoaiMyNeural", "male": "vi-VN-NamMinhNeural", "narrator": "vi-VN-HoaiMyNeural", "locale": "vi-VN",
        "sample": "Xin chào, đây là giọng tham chiếu do hệ thống tạo.",
        "female_list": ("vi-VN-HoaiMyNeural",),
        "male_list": ("vi-VN-NamMinhNeural",),
    },
}

# The upstream preset name that means "the default voice", not a user choice.
_DEFAULT_PRESETS = {"Serena"}


def _table() -> dict | None:
    if manna_asset_language() is None:
        return None
    return _VOICES[current_film_language()]


def default_edge_voice(gender: Literal["female", "male"] = "female") -> str | None:
    table = _table()
    return table[gender] if table else None


def voice_locale() -> str | None:
    table = _table()
    return table["locale"] if table else None


def system_voice_overrides() -> dict | None:
    table = _table()
    if not table:
        return None
    return {"sample_text": table["sample"], "narrator": table["narrator"],
            "female": table["female_list"], "male": table["male_list"]}


def resolve_preset_voice(voice_name: str, aliases: dict[str, str]) -> str:
    """Upstream default preset → film-language voice; anything else is the user's choice."""
    if voice_name in _DEFAULT_PRESETS and (voice := default_edge_voice()):
        return voice
    return aliases.get(voice_name, voice_name)


def system_voice_for_gender(gender: str, name: str) -> str | None:
    overrides = system_voice_overrides()
    if overrides is None:
        return None
    g = str(gender or "").strip().lower()
    female = "女" in g or g.startswith("f") or g in {"woman", "girl"}  # i18n-exempt: matches stored gender values
    pool = overrides["female"] if female else overrides["male"]
    return pool[sum(ord(char) for char in str(name or "")) % len(pool)]
