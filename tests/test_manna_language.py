import json

import pytest

from novelvideo.manna_ext import language as ml
from novelvideo.utils.source_language import (
    asset_language_instruction,
    detect_asset_language,
    detect_episode_asset_language,
)


def test_switch_unset_keeps_upstream(monkeypatch):
    monkeypatch.delenv("MANNA_ASSET_LANGUAGE", raising=False)
    assert ml.manna_asset_language() is None
    assert detect_asset_language("这是一个中文故事，主角在雨夜回家。") == "zh"


def test_switch_forces_english(monkeypatch):
    monkeypatch.setenv("MANNA_ASSET_LANGUAGE", "en")
    assert detect_asset_language("这是一个中文故事，主角在雨夜回家。") == "en"
    assert detect_asset_language("Chị ơi, da em đỡ khô hẳn luôn!") == "en"


async def test_episode_detection_forced(monkeypatch):
    monkeypatch.setenv("MANNA_ASSET_LANGUAGE", "en")
    assert await detect_episode_asset_language(object(), 1, fallback_text="中文") == "en"


def test_normalize():
    assert ml.normalize_film_language("vi") == "vi"
    assert ml.normalize_film_language("VI") == "vi"
    assert ml.normalize_film_language(None) == "en"
    assert ml.normalize_film_language("zh") == "en"


def test_rule_text():
    assert ml.film_language_rule("en") == ""
    assert ml.film_language_rule("vi") == ml.VIETNAMESE_FILM_RULE
    assert "Vietnamese-language film" in ml.VIETNAMESE_FILM_RULE


def test_instruction_appends_rule_only_when_switch_on_and_vi(monkeypatch):
    monkeypatch.setenv("MANNA_ASSET_LANGUAGE", "en")
    token = ml.bind_film_language("vi")
    try:
        text = asset_language_instruction("en")
        assert text.startswith("Write every user-visible prose field in English.")
        assert text.endswith(ml.VIETNAMESE_FILM_RULE)
    finally:
        ml.reset_film_language(token)
    assert asset_language_instruction("en").endswith("rewrite a name.")
    monkeypatch.delenv("MANNA_ASSET_LANGUAGE")
    token = ml.bind_film_language("vi")
    try:
        assert ml.VIETNAMESE_FILM_RULE not in asset_language_instruction("en")
    finally:
        ml.reset_film_language(token)


def test_state_dir_loading(tmp_path):
    assert ml.load_film_language_from_state_dir(tmp_path) == "en"
    (tmp_path / "project_config.json").write_text(json.dumps({"film_language": "vi"}))
    assert ml.load_film_language_from_state_dir(tmp_path) == "vi"
    (tmp_path / "project_config.json").write_text("{not json")
    assert ml.load_film_language_from_state_dir(tmp_path) == "en"
    assert ml.load_film_language_from_state_dir(None) == "en"
