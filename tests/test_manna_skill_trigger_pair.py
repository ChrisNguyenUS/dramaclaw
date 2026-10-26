"""Manna: the English Skill Studio quick actions must still trip the backend trigger.

The prompts live in the frontend (freezone-skill-suggestions.ts) and the matcher in
chat/service.py; P2a translated the producer, so pin the pair across the boundary.
"""

import re
from pathlib import Path

from novelvideo.chat.service import _freezone_skill_studio_requested

_SUGGESTIONS = Path("frontend/src/features/superchat/freezone-skill-suggestions.ts")


def _empty_action_prompts() -> list[str]:
    source = _SUGGESTIONS.read_text(encoding="utf-8")
    block = source.split("FREEZONE_SKILL_EMPTY_ACTIONS", 1)[1].split("];", 1)[0]
    return re.findall(r'prompt:\s*"([^"]*)"', block)


def test_every_quick_action_prompt_enters_skill_studio():
    prompts = _empty_action_prompts()
    assert len(prompts) == 2
    for prompt in prompts:
        # create-with-agent ends with ": " for the user to finish; test with a typical tail.
        text = prompt + "make shorts" if prompt.endswith(": ") else prompt
        assert _freezone_skill_studio_requested(text), prompt
