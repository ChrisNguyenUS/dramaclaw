"""Manna English prompt texts: model-facing text that upstream writes in Chinese.

Every lookup happens at call time and only applies when MANNA_ASSET_LANGUAGE=en, so upstream
behaviour (and upstream tests) are unchanged with the switch off. English builders that replace
whole upstream prompt builders live in manna_ext/prompts_en.py.
"""

from __future__ import annotations

import functools
import json
import re
from pathlib import Path
from typing import Any, Callable

from novelvideo.manna_ext.language import manna_asset_language

_CJK = re.compile(r"[㐀-鿿　-〿＀-￯]")


@functools.lru_cache(maxsize=1)
def _data() -> dict[str, Any]:
    return json.loads((Path(__file__).with_name("prompt_texts.json")).read_text(encoding="utf-8"))


def english_on() -> bool:
    return manna_asset_language() is not None


def text(key: str, default: Any) -> Any:
    """English overlay for ``key`` when the switch is on, else ``default``."""
    if not english_on():
        return default
    return _data()["texts"].get(key, default)


def style_prompt(style_id: str, default: str) -> str:
    if not english_on():
        return default
    return _data()["styles"].get(style_id, default)


@functools.lru_cache(maxsize=1)
def _plan_patterns() -> list[tuple[re.Pattern[str], str]]:
    return [(re.compile(pattern), repl) for pattern, repl in _data()["plan_patterns"]]


def plan_text(value: str) -> str:
    """Translate Manna-known planner fragments; user text and unknown text pass through."""
    if not english_on() or not isinstance(value, str) or not _CJK.search(value):
        return value
    exact = _data()["plan_exact"].get(value)
    if exact is not None:
        return exact
    for pattern, repl in _plan_patterns():
        value = pattern.sub(repl, value)
    return value


def translate_items(items: Any) -> Any:
    """Translate planner-generated item titles/prompts in place (standard planner output only)."""
    if not english_on() or not isinstance(items, list):
        return items
    for item in items:
        if isinstance(item, dict):
            for field in ("title", "prompt", "name", "description"):
                if isinstance(item.get(field), str):
                    item[field] = plan_text(item[field])
    return items


_PLAN_NODE_FIELDS = ("name", "description", "title", "displayName", "prompt", "content", "label")


def translate_plan(plan: Any) -> Any:
    """Translate generated node/phase/layout text in a compiled workflow plan, in place."""
    if not english_on() or not isinstance(plan, dict):
        return plan
    for node in plan.get("nodes") or []:
        if not isinstance(node, dict):
            continue
        for field in _PLAN_NODE_FIELDS:
            if isinstance(node.get(field), str):
                node[field] = plan_text(node[field])
        data = node.get("data")
        if isinstance(data, dict):
            for field in _PLAN_NODE_FIELDS:
                if isinstance(data.get(field), str):
                    data[field] = plan_text(data[field])
    for phase in plan.get("phases") or []:
        if isinstance(phase, dict):
            for field in ("title", "name", "description", "label"):
                if isinstance(phase.get(field), str):
                    phase[field] = plan_text(phase[field])
    layout = plan.get("layout")
    if isinstance(layout, dict):
        for group in layout.get("groups") or []:
            if isinstance(group, dict) and isinstance(group.get("label"), str):
                group["label"] = plan_text(group["label"])
    return plan


def english_plan_results(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Wrap compile_workflow_intent: translate the returned plan for callers outside the planner.

    Internal planner calls (``_include_unit_facts=False``) keep the raw plan so template
    isomorphism and routing compare untranslated text.
    """

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        result = fn(*args, **kwargs)
        if kwargs.get("_include_unit_facts", True) and isinstance(result, dict):
            translate_plan(result.get("plan"))
        return result

    return wrapper
