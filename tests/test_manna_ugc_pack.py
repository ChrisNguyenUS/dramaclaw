"""P2b Task 9: Manna's English UGC recipe pack (10 recipes + 1 skill), served with the switch on."""

from __future__ import annotations

import re

import pytest

from novelvideo.freezone import agent_config_store as store

RECIPE_IDS = {
    "manna-ugc-hook",
    "manna-ugc-unboxing",
    "manna-ugc-testimonial",
    "manna-ugc-before-after",
    "manna-ugc-pov",
    "manna-ugc-problem-solution",
    "manna-ugc-grwm",
    "manna-ugc-street-interview",
    "manna-ugc-three-reasons",
    "manna-ugc-a-vs-b",
}
SKILL_ID = "manna-ugc-ad-video"
SECTIONS = ("Beat structure", "Shot list", "Transitions", "Music cue", "Caption style", "Shot type tags")
TOKEN = re.compile(r"@?(图片|视频|音频|文本)N?\d*")  # i18n-exempt: protocol reference tokens
CJK = re.compile(r"[㐀-鿿　-〿＀-￯]")


def _walk(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for v in value:
            yield from _walk(v)
    elif isinstance(value, dict):
        for v in value.values():
            yield from _walk(v)


@pytest.fixture
def catalog(tmp_path, monkeypatch):
    monkeypatch.setenv("MANNA_ASSET_LANGUAGE", "en")
    monkeypatch.setattr(store, "OUTPUT_DIR", str(tmp_path / "output"))
    monkeypatch.setattr(store, "PROJECT_AGENT_CATALOG_DIR", tmp_path / "no-project-catalog")
    store._CATALOG_CACHE.clear()
    yield lambda kind: {item["id"]: item for item in store.list_user_agent_config_items("ugc-test", kind)}
    store._CATALOG_CACHE.clear()


def test_pack_loads_schema_valid(catalog):
    recipes, skills = catalog("recipes"), catalog("skills")
    assert RECIPE_IDS <= set(recipes), sorted(RECIPE_IDS - set(recipes))
    assert SKILL_ID in skills


def test_pack_is_english(catalog):
    items = [catalog("recipes")[i] for i in RECIPE_IDS] + [catalog("skills")[SKILL_ID]]
    for item in items:
        for text in _walk(item):
            assert not CJK.search(TOKEN.sub("", text)), (item["id"], text[:160])


@pytest.mark.parametrize("recipe_id", sorted(RECIPE_IDS))
def test_recipe_prompt_contract(catalog, recipe_id):
    prompt = catalog("recipes")[recipe_id]["system_prompt"]
    for section in SECTIONS:
        assert section in prompt, (recipe_id, section)
    for tag in ("ai_video", "footage", "graphic"):
        assert tag in prompt, (recipe_id, tag)
    assert "9:16" in prompt
    assert len(prompt) < 4000, (recipe_id, len(prompt))


def test_skill_allows_every_pack_recipe(catalog):
    skill = catalog("skills")[SKILL_ID]
    assert RECIPE_IDS <= set(skill["allowed_recipe_ids"])
    recipes = catalog("recipes")
    assert set(skill["allowed_recipe_ids"]) <= set(recipes)  # every allowed id resolves


def test_pack_hidden_without_switch(tmp_path, monkeypatch):
    monkeypatch.delenv("MANNA_ASSET_LANGUAGE", raising=False)
    monkeypatch.setattr(store, "OUTPUT_DIR", str(tmp_path / "output"))
    monkeypatch.setattr(store, "PROJECT_AGENT_CATALOG_DIR", tmp_path / "no-project-catalog")
    store._CATALOG_CACHE.clear()
    ids = {item["id"] for item in store.list_user_agent_config_items("ugc-test", "recipes")}
    store._CATALOG_CACHE.clear()
    assert not ids & RECIPE_IDS
