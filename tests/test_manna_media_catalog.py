"""English labels for media-model request parameters (bundled + gateway-synced catalog)."""

import json
import re
from pathlib import Path

from novelvideo.manna_ext.media_catalog import english_catalog

CJK = re.compile(r"[一-鿿]")
BUNDLED = Path("src/novelvideo/official_media_models.json")


def _entries():
    data = json.loads(BUNDLED.read_text(encoding="utf-8"))
    return list(data["mediaModels"].values())


def _params(entries):
    out = []

    def walk(v):
        if isinstance(v, dict):
            if isinstance(v.get("parameters"), list):
                out.extend(p for p in v["parameters"] if isinstance(p, dict))
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)

    walk(entries)
    return out


def _cjk(value):
    return CJK.search(json.dumps(value, ensure_ascii=False))


def test_bundled_catalog_has_no_chinese_with_switch(monkeypatch):
    monkeypatch.setenv("MANNA_ASSET_LANGUAGE", "en")
    out = english_catalog(_entries())
    assert not _cjk(out)
    seed = next(p for p in _params(out) if p.get("key") == "seed")
    assert seed["label"] == "Random seed"


def test_keys_and_paths_unchanged(monkeypatch):
    monkeypatch.setenv("MANNA_ASSET_LANGUAGE", "en")
    src = _entries()
    out = english_catalog(src)
    strip = lambda ms: [{k: v for k, v in p.items() if k != "label"} for p in _params(ms)]
    assert strip(out) == strip(src)
    assert _cjk(src)  # input not mutated


def test_switch_off_is_identity(monkeypatch):
    monkeypatch.delenv("MANNA_ASSET_LANGUAGE", raising=False)
    src = _entries()
    assert english_catalog(src) is src


def test_option_labels_and_unknown_labels(monkeypatch):
    monkeypatch.setenv("MANNA_ASSET_LANGUAGE", "en")
    entry = {"id": "m", "request": {"parameters": [
        {"key": "x", "label": "未知标签", "options": [{"value": "a", "label": "生成水印"}]}]}}
    p = english_catalog([entry])[0]["request"]["parameters"][0]
    assert p["options"][0]["label"] == "Watermark"
    assert p["label"] == "X"  # unknown Chinese label falls back to the humanized key


def test_served_catalog_is_english(monkeypatch):
    from novelvideo.api import routes  # noqa: F401  (import order avoids a circular import)
    from novelvideo.api.routes.freezone import _public_media_model_catalog

    monkeypatch.setenv("MANNA_ASSET_LANGUAGE", "en")
    served = [{"id": "m", "request": {"endpoint": "video/generations", "parameters": [{"key": "seed", "label": "随机种子"}]}}]  # i18n-exempt: upstream label
    assert _public_media_model_catalog(served)[0]["request"]["parameters"][0]["label"] == "Random seed"
