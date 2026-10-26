"""P2b Task 5: English overlays for every builtin recipe and skill, layered only when the
English switch is on (upstream sees the original catalog otherwise)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from novelvideo.freezone import agent_config_store as store
from novelvideo.manna_ext import catalog_overlay

BUILTINS = Path("src/novelvideo/freezone/agent_catalog/builtins")
OVERLAY = Path("src/novelvideo/manna_ext/catalog_overlay")
TOKEN = re.compile(r"@?(图片|视频|音频|文本)N?\d*")  # i18n-exempt: protocol reference tokens
CJK = re.compile(r"[㐀-鿿　-〿＀-￯]")
# Option values agent_workflows/catalog.py compares against code-injected Chinese values
# (_SOCIAL_IMAGE_RECIPE_PLATFORMS, character_input_method), plus the legacy last-frame node
# title older canvases still carry (P2a renamed new ones "Previous shot last frame"): protocol, not copy.
PROTECTED = re.compile("小红书|抖音|微博/微信|自定义角色|上一镜尾帧|尾帧")  # i18n-exempt: protocol values


def _walk(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for v in value:
            yield from _walk(v)
    elif isinstance(value, dict):
        for v in value.values():
            yield from _walk(v)


def _ids(root: Path) -> set[str]:
    return {json.loads(p.read_text(encoding="utf-8"))["id"] for p in root.glob("*.json")}


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "OUTPUT_DIR", str(tmp_path / "output"))
    monkeypatch.setattr(store, "PROJECT_AGENT_CATALOG_DIR", tmp_path / "no-project-catalog")
    store._CATALOG_CACHE.clear()
    yield
    store._CATALOG_CACHE.clear()


@pytest.mark.parametrize("kind", ["recipes", "skills"])
def test_every_builtin_has_an_overlay(kind):
    missing = _ids(BUILTINS / kind) - _ids(OVERLAY / kind)
    assert not missing, sorted(missing)


@pytest.mark.parametrize("kind", ["recipes", "skills"])
def test_overlays_load_through_real_loader_with_switch_on(kind, monkeypatch):
    monkeypatch.setenv("MANNA_ASSET_LANGUAGE", "en")
    overlay_ids = _ids(OVERLAY / kind)
    items = {item["id"]: item for item in store.list_user_agent_config_items("overlay-test", kind)}
    assert overlay_ids <= set(items), sorted(overlay_ids - set(items))  # none dropped by validation
    for item_id in overlay_ids:
        for text in _walk(items[item_id]):
            assert not CJK.search(PROTECTED.sub("", TOKEN.sub("", text))), (item_id, text[:160])


@pytest.mark.parametrize("kind", ["recipes", "skills"])
def test_switch_off_keeps_upstream_catalog(kind, monkeypatch):
    monkeypatch.delenv("MANNA_ASSET_LANGUAGE", raising=False)
    items = {item["id"]: item for item in store.list_user_agent_config_items("overlay-test", kind)}
    builtin = {
        json.loads(p.read_text(encoding="utf-8"))["id"]: json.loads(p.read_text(encoding="utf-8"))
        for p in (BUILTINS / kind).glob("*.json")
    }
    sample = sorted(builtin)[0]
    prompt_key = "system_prompt" if kind == "recipes" else "planning"
    assert items[sample][prompt_key] == builtin[sample][prompt_key]


def test_overlay_keeps_ids_and_contract_fields():
    for kind, keys in (
        ("recipes", ("id", "version", "enabled", "output_kind", "action_keys", "requires_source_media")),
        ("skills", ("id", "version", "enabled", "allowed_recipe_ids")),
    ):
        builtin = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in (BUILTINS / kind).glob("*.json")}
        for name, src in builtin.items():
            dst = json.loads((OVERLAY / kind / name).read_text(encoding="utf-8"))
            for key in keys:
                assert dst.get(key) == src.get(key), (kind, name, key)


def test_reference_tokens_survive():
    for p in (BUILTINS / "recipes").glob("*.json"):
        src = p.read_text(encoding="utf-8")
        dst = (OVERLAY / "recipes" / p.name).read_text(encoding="utf-8")
        for token in ("@图片N", "@视频N", "@音频N"):  # i18n-exempt: protocol reference tokens
            if token in src:
                assert token in dst, (p.name, token)


def test_overlay_dir_is_off_without_switch(monkeypatch):
    monkeypatch.delenv("MANNA_ASSET_LANGUAGE", raising=False)
    assert catalog_overlay.overlay_dir("recipes") is None
    monkeypatch.setenv("MANNA_ASSET_LANGUAGE", "en")
    assert catalog_overlay.overlay_dir("recipes") == OVERLAY.resolve() / "recipes"


def test_overlays_are_not_stale_against_upstream_builtins():
    """An upstream change to a builtin must be re-translated (scripts/manna-catalog-sheet.py stale)."""
    import hashlib

    sources = json.loads((OVERLAY / "SOURCES.json").read_text(encoding="utf-8"))
    stale = [
        key
        for key, sha in sources.items()
        if hashlib.sha256((BUILTINS / key).read_bytes()).hexdigest() != sha
    ]
    assert not stale, f"re-translate: {stale} (run scripts/manna-catalog-sheet.py extract/apply)"
    tracked = {f"{kind}/{p.name}" for kind in ("recipes", "skills") for p in (BUILTINS / kind).glob("*.json")}
    assert tracked <= set(sources), sorted(tracked - set(sources))
