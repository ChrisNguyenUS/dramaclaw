"""English display names for the builtin catalogs (styles, recipes, skills)."""

import copy
import json
import re

import pytest

from novelvideo.freezone import agent_config_store as store
from novelvideo.freezone.agent_catalog_schema import validate_agent_config_item
from novelvideo.manna_ext.catalog_en import apply_catalog_en

CJK = re.compile(r"[　-〿㐀-鿿豈-﫿＀-￯]")
STYLE_JSON = store.Path(__file__).parents[1] / "src/novelvideo/freezone/style_templates.json"
BUILTINS = store.BUILTIN_AGENT_CATALOG_DIR


def _raw(kind):
    items = []
    for path in sorted((BUILTINS / kind).glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        items.extend(payload if isinstance(payload, list) else [payload])
    return items


@pytest.fixture
def loader(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "OUTPUT_DIR", str(tmp_path))
    monkeypatch.setattr(store, "PROJECT_AGENT_CATALOG_DIR", tmp_path / "no-overlay")
    store._CATALOG_CACHE.clear()
    yield lambda kind, user="u1": store.list_user_agent_config_items(user, kind)
    store._CATALOG_CACHE.clear()


def test_style_labels_become_english_and_prompts_stay():
    items = [{"id": "period_idol", "label": "古装偶像", "category": "古装", "style_prompt": "古偶唯美柔光风格"}]
    out = apply_catalog_en("styles", items)
    assert out[0]["label"] == "Period Idol"
    assert out[0]["category"] == "Period"
    assert out[0]["style_prompt"] == "古偶唯美柔光风格"
    assert items[0]["label"] == "古装偶像"  # input not mutated


@pytest.mark.parametrize("kind,source", [("styles", None), ("recipes", "recipes"), ("skills", "skills")])
def test_overlay_ids_match_builtin_ids(kind, source):
    """A builtin removed or renamed upstream must not leave a dead overlay entry."""
    from novelvideo.manna_ext.catalog_en import _overlay

    if source is None:
        ids = {i["id"] for i in json.loads(STYLE_JSON.read_text(encoding="utf-8"))["templates"]}
    else:
        ids = {i["id"] for i in _raw(source)}
    assert set(_overlay(kind)) == ids


def test_unknown_ids_pass_through():
    assert apply_catalog_en("recipes", [{"id": "x", "name": "未知"}]) == [{"id": "x", "name": "未知"}]


def test_only_keys_present_are_replaced_and_hidden_overlays_pass_through():
    out = apply_catalog_en("recipes", [{"id": "general-text", "hidden": True}])
    assert out == [{"id": "general-text", "hidden": True}]
    out = apply_catalog_en("recipes", [{"id": "general-text", "name": "x"}])
    assert "description" not in out[0]


def test_every_builtin_style_is_english_through_the_real_route_helper():
    import novelvideo.api.routes.freezone  # noqa: F401  (route_helpers has an upstream import cycle when loaded alone)
    from novelvideo.freezone.route_helpers import get_freezone_image_style_templates

    served = get_freezone_image_style_templates()
    raw = json.loads(STYLE_JSON.read_text(encoding="utf-8"))["templates"]
    assert len(served) == len(raw) == 45
    for item in served:
        assert not CJK.search(item["label"]), item["id"]
        assert not CJK.search(item["category"]), item["id"]
    for before, after in zip(raw, served):
        for key in ("id", "cover", "samples", "style_prompt"):
            assert before[key] == after[key]
    # the prompt sent to the model keeps the original label
    from novelvideo.freezone.style_templates import load_style_templates

    assert load_style_templates()[0]["label"] == raw[0]["label"]


def test_style_categories_stay_consistent_for_grouping():
    import novelvideo.api.routes.freezone  # noqa: F401
    from novelvideo.freezone.route_helpers import get_freezone_image_style_templates

    cats = [i["category"] for i in get_freezone_image_style_templates()]
    # one English string per original Chinese category, order of first appearance preserved
    raw = [i["category"] for i in json.loads(STYLE_JSON.read_text(encoding="utf-8"))["templates"]]
    assert len(set(cats)) == len(set(raw))
    assert all(cats)


@pytest.mark.parametrize("kind", ["recipes", "skills"])
def test_every_builtin_is_english_through_the_real_loader(loader, kind):
    loaded = loader(kind)
    raw = {i["id"]: i for i in _raw(kind)}
    assert len(loaded) == len(raw) == {"recipes": 60, "skills": 12}[kind]
    for item in loaded:
        assert item["id"] in raw
        for key in ("name", "description", "category"):
            if key in item:
                assert not CJK.search(item[key]), (item["id"], key)
        for param in item.get("input_parameters", []):
            assert not CJK.search(param["label"]), (item["id"], param["id"])
        # schema still valid after the overlay
        validate_agent_config_item(kind, {k: v for k, v in item.items() if not k.startswith("_")})
        # nothing but display fields changed
        original = raw[item["id"]]
        for key, value in original.items():
            if key in ("name", "description", "category"):
                continue
            if key == "input_parameters":
                for a, b in zip(value, item[key]):
                    assert {k: v for k, v in a.items() if k != "label"} == {
                        k: b[k] for k in a if k != "label"
                    }
                continue
            assert item[key] == value, (item["id"], key)


def test_option_values_are_not_translated(loader):
    for item in loader("skills"):
        raw = next(i for i in _raw("skills") if i["id"] == item["id"])
        for a, b in zip(raw.get("input_parameters", []), item.get("input_parameters", [])):
            assert a["options"] == b["options"] if "options" in a else True
            assert a.get("default") == b.get("default")


def test_overlay_and_user_layers_win_over_english_builtin(loader, tmp_path, monkeypatch):
    overlay = tmp_path / "overlay"
    (overlay / "recipes").mkdir(parents=True)
    original = next(i for i in _raw("recipes") if i["id"] == "general-text")
    (overlay / "recipes" / "general-text.json").write_text(
        json.dumps({**original, "name": "Project Text"}), encoding="utf-8"
    )
    monkeypatch.setattr(store, "PROJECT_AGENT_CATALOG_DIR", overlay)
    store._CATALOG_CACHE.clear()
    by_id = {i["id"]: i for i in loader("recipes")}
    assert by_id["general-text"]["name"] == "Project Text"

    user_dir = store.user_agent_config_dir("u2", "recipes")
    user_dir.mkdir(parents=True)
    (user_dir / "general-image.json").write_text(
        json.dumps({**next(i for i in _raw("recipes") if i["id"] == "general-image"), "name": "我的图片"}),
        encoding="utf-8",
    )
    store._CATALOG_CACHE.clear()
    by_id = {i["id"]: i for i in loader("recipes", "u2")}
    assert by_id["general-image"]["name"] == "我的图片"
    assert by_id["general-video"]["name"] == "General Video Enhancement"


def test_user_created_items_keep_their_names(loader):
    store.save_user_agent_config_item(
        username="u3",
        kind="recipes",
        payload={**next(i for i in _raw("recipes") if i["id"] == "general-text"), "id": "my-own", "name": "我的配方"},
    )
    store._CATALOG_CACHE.clear()
    by_id = {i["id"]: i for i in loader("recipes", "u3")}
    assert by_id["my-own"]["name"] == "我的配方"


@pytest.mark.parametrize("kind", ["recipes", "skills"])
def test_fallback_loader_also_serves_english(monkeypatch, kind):
    from novelvideo.freezone.agent_workflows import catalog

    monkeypatch.setattr(catalog, "list_user_agent_config_items", None)
    monkeypatch.setattr(catalog, "_PLUGIN_RECIPES_DIR", catalog.Path("/nonexistent"))
    monkeypatch.setattr(catalog, "_PLUGIN_SKILLS_DIR", catalog.Path("/nonexistent"))
    directory = catalog._RECIPES_DIR if kind == "recipes" else catalog._SKILLS_DIR
    items = catalog._load_agent_config_items(kind, directory)
    assert items
    for item in items:
        assert not CJK.search(item["name"]), item["id"]


def test_audio_kind_detection_is_unchanged_by_english_names():
    """Recipe names feed keyword sniffing in the workflow catalog; English names must not flip it."""
    from novelvideo.freezone.agent_workflows import catalog

    for before in (r for r in _raw("recipes") if r["output_kind"] == "audio"):
        after = apply_catalog_en("recipes", [copy.deepcopy(before)])[0]
        assert catalog._dynamic_default_model(before) == catalog._dynamic_default_model(after), before["id"]
        assert catalog._intent_audio_kind({}, before) == catalog._intent_audio_kind({}, after), before["id"]


def _quick_drama_plan(catalog, style):
    compiled = catalog.compile_workflow_intent({
        "skill_id": "short-drama-quick", "user_goal": "two shot drama",
        "inputs": {"visual_style": style},
        "planner": {"mode": "standard", "deliverable": "video", "item_count": 2,
                    "include_audio": False, "units": [
                        {"title": "Opening", "prompt": "hero enters"},
                        {"title": "Ending", "prompt": "hero stays"},
                    ]},
    })
    assert compiled["ok"] is True, compiled
    return compiled["plan"]


@pytest.mark.parametrize("sentinel", ["Unspecified", "unspecified", "未指定"])
def test_unspecified_visual_style_counts_as_unset_in_both_languages(monkeypatch, sentinel):
    """The English visual_style label tells users to write "Unspecified"; it must mean "not confirmed"."""
    from novelvideo.freezone.agent_workflows import catalog

    monkeypatch.setattr(catalog, "list_user_agent_config_items", None)
    plan = _quick_drama_plan(catalog, sentinel)
    assert "已确认视觉风格" not in json.dumps(plan, ensure_ascii=False)
    assert catalog._confirmed_input_guidance("short-drama-quick", {"visual_style": sentinel}) == ""
    assert catalog._quick_drama_visual_style_blockers(plan, sentinel) == []
    assert catalog.validate_agent_workflow_plan(plan, allow_template_reroute=False)["ok"] is True


def test_a_real_visual_style_is_still_confirmed():
    from novelvideo.freezone.agent_workflows import catalog

    assert "Anime" in catalog._confirmed_input_guidance("short-drama-quick", {"visual_style": "Anime"})
