"""P2b Task 8: the default TTS voice follows the project's film language."""

from types import SimpleNamespace

import pytest

from novelvideo.manna_ext import language as ml
from novelvideo.manna_ext import voices


@pytest.fixture
def bound(monkeypatch):
    monkeypatch.setenv("MANNA_ASSET_LANGUAGE", "en")
    tokens = []

    def bind(lang):
        tokens.append(ml.bind_film_language(lang))

    yield bind
    for token in reversed(tokens):
        ml.reset_film_language(token)


def test_english_defaults(bound):
    bound("en")
    assert voices.default_edge_voice() == "en-US-JennyNeural"
    assert voices.default_edge_voice("male") == "en-US-GuyNeural"
    assert voices.voice_locale() == "en-US"


def test_vietnamese_defaults(bound):
    bound("vi")
    assert voices.default_edge_voice() == "vi-VN-HoaiMyNeural"
    assert voices.default_edge_voice("male") == "vi-VN-NamMinhNeural"
    assert voices.voice_locale() == "vi-VN"


def test_off_returns_none(monkeypatch):
    monkeypatch.delenv("MANNA_ASSET_LANGUAGE", raising=False)
    assert voices.default_edge_voice() is None
    assert voices.voice_locale() is None
    assert voices.system_voice_overrides() is None


def test_preset_alias_follows_film_language(bound):
    bound("vi")
    assert voices.resolve_preset_voice("Serena", {"Serena": "zh-CN-XiaoxiaoNeural"}) == "vi-VN-HoaiMyNeural"  # i18n-exempt: upstream voice id
    assert voices.resolve_preset_voice("en-GB-SoniaNeural", {}) == "en-GB-SoniaNeural"


def test_system_voice_setup_uses_film_language(bound):
    from novelvideo.audio import system_voice_setup as svs

    bound("vi")
    assert svs._system_voice_for_character(SimpleNamespace(gender="female", age_group="", name="Lan")) == "vi-VN-HoaiMyNeural"
    assert svs._system_voice_for_character(SimpleNamespace(gender="male", age_group="", name="Minh")) == "vi-VN-NamMinhNeural"
    assert voices.system_voice_overrides()["sample_text"].startswith("Xin chào")


def test_system_voice_setup_english(bound):
    from novelvideo.audio import system_voice_setup as svs

    bound("en")
    voice = svs._system_voice_for_character(SimpleNamespace(gender="Female", age_group="", name="Mia"))
    assert voice in ("en-US-JennyNeural", "en-US-AriaNeural", "en-US-MichelleNeural")
    assert voices.system_voice_overrides()["sample_text"] == "Hello, this is a system-generated reference voice."
