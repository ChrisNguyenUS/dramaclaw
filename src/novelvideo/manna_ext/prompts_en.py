"""English versions of upstream prompt builders (used when MANNA_ASSET_LANGUAGE=en).

Each function mirrors the upstream builder's signature and output shape; upstream calls it from
a one-line ``# Manna hook`` at the top of the original function.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import yaml

from novelvideo.manna_ext.language import current_film_language, film_language_rule
from novelvideo.manna_ext.prompts import text


def _t(key: str) -> Any:
    return text(key, None)


# --- freezone/image_node.py ----------------------------------------------------------------


def image_reverse_prompt_task(instruction: str = "") -> str:
    lines = list(_t("image_node.reverse_prompt_lines"))
    clean = str(instruction or "").strip()
    if clean:
        lines.extend([_t("image_node.user_extra_label"), clean])
    return "\n".join(lines)


# --- freezone/text_node.py -----------------------------------------------------------------


def _character_ref_block(character_refs: Sequence[Mapping[str, Any]] | None) -> str | None:
    if not character_refs:
        return None
    lines: list[str] = []
    for index, ref in enumerate(character_refs, start=1):
        name = str(ref.get("name") or "").strip() or _t("text_node.character_ref_default_name").format(index=index)
        description = str(ref.get("description") or "").strip()
        role = str(ref.get("role") or "").strip()
        detail = ", ".join(part for part in (role, description) if part)
        lines.append(f"{index}. {name}" + (f" ({detail})" if detail else ""))
    return (
        _t("text_node.character_ref_header") + "\n" + "\n".join(lines) + "\n" + _t("text_node.character_ref_footer")
    )


def story_script_task(*, source_text: str, prompt: str, character_refs=None) -> str:
    parts = [_t("text_node.story_script_intro"), *_t("text_node.story_script_rules")]
    if prompt.strip():
        parts.append(f"{_t('text_node.user_requirements_label')}\n{prompt.strip()}")
    block = _character_ref_block(character_refs)
    if block:
        parts.append(block)
    parts.append(_t("text_node.story_script_style_hint"))
    parts.append(f"{_t('text_node.source_script_label')}\n{source_text.strip()}")
    if rule := film_language_rule(current_film_language()):
        parts.append(rule)  # the agent is a cached singleton: the vi rule rides on the task text
    return "\n\n".join(parts)


def video_story_script_task(*, frame_count: int, prompt: str, duration_sec=None, character_refs=None) -> str:
    duration_hint = (
        _t("text_node.video_duration_known").format(seconds=f"{duration_sec:.2f}")
        if duration_sec and duration_sec > 0
        else _t("text_node.video_duration_unknown")
    )
    parts = [
        _t("text_node.video_intro").format(frame_count=frame_count),
        *_t("text_node.video_rules"),
        duration_hint,
        _t("text_node.video_grouping_rule"),
        _t("text_node.video_keyframe_rule").format(frame_count=frame_count),
        *_t("text_node.story_script_rules"),
    ]
    if prompt.strip():
        parts.append(f"{_t('text_node.user_extra_requirements_label')}\n{prompt.strip()}")
    block = _character_ref_block(character_refs)
    if block:
        parts.append(block)
    parts.append(_t("text_node.story_script_style_hint"))
    if rule := film_language_rule(current_film_language()):
        parts.append(rule)  # the agent is a cached singleton: the vi rule rides on the task text
    return "\n\n".join(parts)


def character_story_script_task(*, image_count: int, prompt: str, source_text: str = "", character_refs=None) -> str:
    parts = [
        _t("text_node.character_mode_intro").format(image_count=image_count),
        *_t("text_node.character_mode_rules"),
        *_t("text_node.story_script_rules"),
    ]
    if prompt.strip():
        parts.append(f"{_t('text_node.user_requirements_label')}\n{prompt.strip()}")
    else:
        parts.append(_t("text_node.character_mode_no_prompt"))
    block = _character_ref_block(character_refs)
    if block:
        parts.append(block)
    parts.append(_t("text_node.story_script_style_hint"))
    if source_text.strip():
        parts.append(f"{_t('text_node.source_script_label')}\n{source_text.strip()}")
    if rule := film_language_rule(current_film_language()):
        parts.append(rule)  # the agent is a cached singleton: the vi rule rides on the task text
    return "\n\n".join(parts)


def video_story_script_system() -> str:
    return _t("text_node.story_script_system") + _t("text_node.video_story_script_vision_section")


# --- freezone/video_node.py ----------------------------------------------------------------


def camera_templates(upstream: list[dict[str, str]]) -> list[dict[str, str]]:
    english = _t("video_node.camera_templates") or {}
    out = []
    for template in upstream:
        en = english.get(template.get("id"), {})
        out.append({**template, **{k: v for k, v in en.items() if k in ("name", "prompt")}})
    return out


def _camera_line(template: dict[str, str] | None) -> str | None:
    if not template:
        return None
    return _t("video_node.camera_template").format(name=template["name"], prompt=template["prompt"])


def _coarse_mark_region(mark: dict[str, Any]) -> str:
    regions = _t("video_node.mark_regions")
    px, py = mark.get("point_x"), mark.get("point_y")
    if not isinstance(px, (int, float)) or not isinstance(py, (int, float)):
        box = [mark.get(k) for k in ("box_x", "box_y", "box_width", "box_height")]
        if all(isinstance(value, (int, float)) for value in box):
            px = float(box[0]) + float(box[2]) / 2.0
            py = float(box[1]) + float(box[3]) / 2.0
    if isinstance(px, (int, float)) and isinstance(py, (int, float)):
        horizontal = regions["left"] if px < 0.33 else regions["right"] if px > 0.66 else regions["middle_h"]
        vertical = regions["top"] if py < 0.33 else regions["bottom"] if py > 0.66 else regions["middle_v"]
        return f"{vertical} {horizontal}"
    return ""


def format_video_marks(marks: list[dict[str, Any]] | None) -> str:
    clean = [mark for mark in (marks or []) if str(mark.get("label") or "").strip()]
    if not clean:
        return ""
    lines = []
    for mark in clean:
        label = str(mark.get("label") or "").strip()
        suffix_parts = [part for part in [_coarse_mark_region(mark), str(mark.get("note") or "").strip()] if part]
        lines.append(f"- {label}" + (f" ({', '.join(suffix_parts)})" if suffix_parts else ""))
    return _t("video_node.marks_header") + "\n" + "\n".join(lines)


def video_prompt(*, user_prompt, template, character_names=None, marks=None) -> str:
    parts = [str(user_prompt or "").strip(), _camera_line(template)]
    joined = ", ".join(name for name in (character_names or []) if name)
    if joined:
        parts.append(_t("video_node.character_consistency").format(names=joined))
    parts.append(format_video_marks(marks))
    parts.append(_t("video_node.output_requirement"))
    return "\n".join(part for part in parts if part)


def image_to_video_prompt(*, user_prompt="", template=None, marks=None, reference_image_count=1) -> str:
    parts = [user_prompt.strip() if user_prompt else "", _camera_line(template), format_video_marks(marks)]
    image_count = 1 if reference_image_count is None else int(reference_image_count)
    if image_count > 1:
        parts.append(_t("video_node.multi_image_reference"))
    elif image_count == 1:
        parts.append(_t("video_node.single_image_reference"))
    parts.append(_t("video_node.output_requirement"))
    return "\n".join(part for part in parts if part)


def video_extend_prompt(*, user_prompt, template=None) -> str:
    parts = [str(user_prompt or "").strip(), _camera_line(template), _t("video_node.extend_requirement")]
    return "\n".join(part for part in parts if part)


def keyframe_video_prompt(*, user_prompt="", template=None, marks=None, has_first_frame=True, has_last_frame=True) -> str:
    parts = [user_prompt.strip() if user_prompt else "", _camera_line(template), format_video_marks(marks)]
    if has_first_frame and has_last_frame:
        parts.append(_t("video_node.first_last_constraint"))
    elif has_first_frame:
        parts.append(_t("video_node.first_only_constraint"))
    elif has_last_frame:
        parts.append(_t("video_node.last_only_constraint"))
    parts.append(_t("video_node.output_requirement_keyframe"))
    return "\n".join(part for part in parts if part)


def omni_video_prompt(*, user_prompt, theme="", template=None, marks=None, counts=None, continuation=False) -> str:
    parts = [str(user_prompt or "").strip()]
    if theme and theme.strip():
        parts.append(_t("video_node.theme").format(theme=theme.strip()))
    parts.extend([_camera_line(template), format_video_marks(marks)])
    if continuation:
        parts.append(_t("video_node.extend_requirement"))
        return "\n".join(part for part in parts if part)
    parts.append(_t("video_node.omni_requirement"))
    counts = counts or {}
    if (
        counts.get("video_count") == 1
        and not any(counts.get(k) for k in ("image_count", "audio_count", "file_count", "link_count"))
    ):
        parts.append(_t("video_node.single_video_reference"))
    parts.append(_t("video_node.output_requirement"))
    return "\n".join(part for part in parts if part)


# --- chat/hermes_workspace.py ---------------------------------------------------------------


def workflow_skill_description(item: dict) -> str:
    description = str(item.get("description") or "").strip()
    triggers = item.get("triggers") if isinstance(item.get("triggers"), dict) else {}
    keywords = triggers.get("keywords") if isinstance(triggers, dict) else []
    keyword_text = (
        ", ".join(str(value).strip() for value in keywords[:10] if str(value).strip())
        if isinstance(keywords, list)
        else ""
    )
    parts = [description]
    if keyword_text:
        parts.append(_t("hermes.applies_to").format(keywords=keyword_text))
    parts.append(_t("hermes.selection_note"))
    return " ".join(part for part in parts if part)[:1024]


def render_workflow_skill(item: dict) -> tuple[str, dict[str, object]]:
    skill_id = str(item.get("id") or "").strip()
    display_name = str(
        item.get("name") or item.get("display_name") or item.get("displayName") or item.get("title") or skill_id
    ).strip()
    description = workflow_skill_description(item)
    frontmatter = yaml.safe_dump(
        {"name": skill_id, "description": description}, allow_unicode=True, sort_keys=False
    ).strip()
    body = _t("hermes.wrapper_body").format(skill_id=skill_id, description=description)
    content = f"---\n{frontmatter}\n---\n\n# {display_name}\n\n{body}"
    summary: dict[str, object] = {
        "id": skill_id,
        "name": display_name,
        "description": description,
        "category": str(item.get("category") or "").strip(),
        "source": "hermes_native_workflow_skill",
        "allowed_recipe_ids": list(item.get("allowed_recipe_ids") or item.get("allowedRecipeIds") or []),
    }
    return content, summary


# --- freezone/agent_workflows/catalog.py ------------------------------------------------------


def confirmed_input_guidance(skill_id: str, resolved_inputs: dict[str, Any], visual_style_rule: bool) -> list[str]:
    """Return the English guidance parts; ``visual_style_rule`` mirrors upstream's style condition."""
    parts: list[str] = []
    visual_style = str(resolved_inputs.get("visual_style") or "").strip()
    if visual_style_rule and visual_style:
        parts.append(_t("catalog.confirmed_visual_style").format(style=visual_style))
    method = str(resolved_inputs.get("character_input_method") or "").strip()
    if method and skill_id == "pixar-ip-ad-video":
        parts.append(_t("catalog.confirmed_character_source").format(method=method))
    return parts
