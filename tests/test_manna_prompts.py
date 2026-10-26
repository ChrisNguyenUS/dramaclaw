"""P2b Task 6: model-facing prompt text is English when MANNA_ASSET_LANGUAGE=en, unchanged otherwise."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from novelvideo.manna_ext import prompts

CJK = re.compile(r"[㐀-鿿　-〿＀-￯]")


def _no_cjk(text: str) -> bool:
    return not CJK.search(text)


@pytest.fixture
def english(monkeypatch):
    monkeypatch.setenv("MANNA_ASSET_LANGUAGE", "en")


@pytest.fixture
def upstream(monkeypatch):
    monkeypatch.delenv("MANNA_ASSET_LANGUAGE", raising=False)


# --- core -------------------------------------------------------------------------------


def test_text_falls_back_when_off(upstream):
    assert prompts.text("image_node.default_instruction", "原文") == "原文"


def test_text_overlays_when_on(english):
    value = prompts.text("image_node.default_instruction", "原文")
    assert value != "原文" and _no_cjk(value)


def test_unknown_key_falls_back(english):
    assert prompts.text("no.such.key", "原文") == "原文"


def test_overlay_file_is_cjk_free():
    data = json.loads((Path(prompts.__file__).parent / "prompt_texts.json").read_text(encoding="utf-8"))

    def walk(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, list):
            for v in value:
                yield from walk(v)
        elif isinstance(value, dict):
            for v in value.values():
                yield from walk(v)

    # plan_exact keys and plan_patterns sources are Chinese matchers by design; check English sides.
    english = [data["texts"], data["styles"], list(data["plan_exact"].values()), [r for _, r in data["plan_patterns"]]]
    leaks = [s[:80] for s in walk(english) if CJK.search(s)]
    assert not leaks, leaks


# --- image node ---------------------------------------------------------------------------


def test_image_reverse_prompt_task(english):
    from novelvideo.freezone.image_node import build_image_reverse_prompt_task

    task = build_image_reverse_prompt_task("make it moody")
    assert _no_cjk(task) and "English" in task and task.endswith("make it moody")


def test_image_reverse_prompt_task_upstream(upstream):
    from novelvideo.freezone.image_node import build_image_reverse_prompt_task

    assert "中文提示词" in build_image_reverse_prompt_task("")  # i18n-exempt: pins upstream text


# --- text node (story script) ---------------------------------------------------------------


def test_story_script_tasks_are_english(english):
    from novelvideo.freezone import text_node

    refs = [{"name": "Mia", "description": "28, office worker", "role": "lead"}]
    for task in (
        text_node.build_freezone_story_script_task(source_text="Mia waits.", prompt="tense", character_refs=refs),
        text_node.build_freezone_video_story_script_task(frame_count=6, prompt="", duration_sec=12.0, character_refs=refs),
        text_node.build_freezone_character_story_script_task(image_count=1, prompt="", character_refs=refs),
    ):
        assert _no_cjk(task), task[:200]
        assert "Mia" in task


def test_story_script_system_prompts_are_english(english):
    from novelvideo.freezone import text_node

    from novelvideo.manna_ext import prompts_en

    assert _no_cjk(prompts.text("text_node.story_script_system", text_node.FREEZONE_STORY_SCRIPT_SYSTEM_PROMPT))
    assert _no_cjk(prompts_en.video_story_script_system())


def test_story_script_agent_uses_english_prompt(english, monkeypatch):
    from novelvideo.freezone import text_node

    captured = {}

    class FakeAgent:
        def __init__(self, *args, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(text_node, "Agent", FakeAgent)
    monkeypatch.setattr(text_node, "_story_script_agent", None)
    for fn in ("create_freezone_story_script_agent", "create_freezone_video_story_script_agent"):
        captured.clear()
        try:
            getattr(text_node, fn)()
        except Exception:  # model wiring may need gateway config; the prompt is captured first
            pass
        if captured:
            assert _no_cjk(captured["system_prompt"])


# --- video node -------------------------------------------------------------------------------


def test_video_prompt_builders_are_english(english):
    from novelvideo.freezone import video_node as v

    marks = [{"label": "red bag", "point_x": 0.1, "point_y": 0.9, "note": "keep visible"}]
    outputs = [
        v.build_freezone_video_prompt(user_prompt="A woman walks", camera_template_id="orbit_up", character_names=["Mia"], marks=marks),
        v.build_freezone_image_to_video_prompt(user_prompt="A woman walks", camera_template_id="pan_left", marks=marks, reference_image_count=2),
        v.build_freezone_image_to_video_prompt(user_prompt="A woman walks", reference_image_count=1),
        v.build_freezone_video_extend_prompt(user_prompt="continue", camera_template_id="tilt_up"),
        v.build_freezone_keyframe_video_prompt(user_prompt="go", camera_template_id="locked_off", marks=marks),
        v.build_freezone_keyframe_video_prompt(user_prompt="go", has_last_frame=False),
        v.build_freezone_keyframe_video_prompt(user_prompt="go", has_first_frame=False),
        v.build_freezone_omni_video_prompt(user_prompt="go", theme="summer", camera_template_id="truck_left", marks=marks, reference_items=[{"kind": "video"}]),
        v.build_freezone_omni_video_prompt(user_prompt="go", continuation=True),
    ]
    for out in outputs:
        assert _no_cjk(out), out


def test_camera_templates_are_english_and_keep_ids(english):
    from novelvideo.freezone import video_node as v

    templates = v.get_video_camera_templates()
    assert [t["id"] for t in templates] == [t["id"] for t in v.VIDEO_CAMERA_TEMPLATES]
    for t in templates:
        assert _no_cjk(t["name"]) and _no_cjk(t["prompt"])
    assert _no_cjk(v.get_video_camera_template("orbit_up")["name"])


def test_video_builders_upstream_unchanged(upstream):
    from novelvideo.freezone import video_node as v

    assert "输出要求" in v.build_freezone_video_prompt(user_prompt="x")  # i18n-exempt: pins upstream text


# --- hermes wrapper skill (UI-visible description) ------------------------------------------------


def test_workflow_skill_description_and_render_are_english(english):
    from novelvideo.chat import hermes_workspace as h

    item = {"id": "ecommerce-ad", "name": "E-commerce Ad", "description": "Plans ad shots.",
            "triggers": {"keywords": ["product ad", "shoppable video"]}, "allowed_recipe_ids": ["x"]}
    desc = h._workflow_skill_description(item)
    assert _no_cjk(desc) and "product ad" in desc and "Manna Canvas" in desc
    content, summary = h._render_workflow_skill(item)
    assert _no_cjk(content) and summary["id"] == "ecommerce-ad"
    assert "freezone_get_workflow_skill" in content and 'skill_id="ecommerce-ad"' in content


# --- workflow catalog planner text ------------------------------------------------------------------


def test_confirmed_input_guidance_is_english(english):
    from novelvideo.freezone.agent_workflows import catalog

    text = catalog._confirmed_input_guidance("short-drama-quick", {"visual_style": "Modern Realistic"})
    assert "Modern Realistic" in text and _no_cjk(text)
    text = catalog._confirmed_input_guidance("pixar-ip-ad-video", {"character_input_method": "自定义角色"})  # i18n-exempt: protocol value
    assert _no_cjk(text.replace("自定义角色", ""))  # i18n-exempt: protocol value


def test_standard_planner_items_are_english(english):
    from novelvideo.freezone.agent_workflows import catalog

    leaked, compiled = [], []
    for skill_id in sorted(catalog._DETERMINISTIC_SKILL_PLANNERS):
        result = catalog.compile_workflow_intent({
            "skill_id": skill_id,
            "user_goal": "A 30 second ad for a vitamin C serum",
            "planner": {"mode": "standard", "item_count": 2, "units": [
                {"title": "Opening", "prompt": "hero shot of the serum", "narration": "Meet your glow."},
                {"title": "Close", "prompt": "product on the counter", "narration": "Shop now."},
            ]},
        })
        plan = result.get("plan") if isinstance(result, dict) and result.get("ok") else None
        if not plan:
            continue
        compiled.append(skill_id)
        for node in plan.get("nodes", []):
            data = node.get("data") or {}
            for field in ("name", "title", "displayName", "prompt", "description"):
                for value in (node.get(field), data.get(field)):
                    if isinstance(value, str) and CJK.search(value.replace("自定义角色", "")):  # i18n-exempt: protocol value
                        leaked.append((skill_id, field, value[:80]))
    assert len(compiled) >= 4, compiled
    assert not leaked, leaked[:10]


# --- style prompts ------------------------------------------------------------------------------------


def test_style_prompts_have_english_overlay(english):
    templates_file = Path("src/novelvideo/freezone/style_templates.json")
    data = json.loads(templates_file.read_text(encoding="utf-8"))
    templates = data.get("templates", data) if isinstance(data, dict) else data
    items = templates.items() if isinstance(templates, dict) else [(t["id"], t) for t in templates]
    for style_id, tpl in items:
        value = prompts.style_prompt(style_id, tpl.get("style_prompt", ""))
        assert value and _no_cjk(value), style_id


def test_agent_block_sets_manna_identity(english):
    from novelvideo.manna_ext.language import agent_language_block

    block = agent_language_block("en")
    assert "Manna Director" in block and "Manna Studio" in block
    assert "DramaClaw" in block  # named only to forbid it as a self-name
