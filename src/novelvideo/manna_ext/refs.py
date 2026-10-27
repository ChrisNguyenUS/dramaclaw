"""Map English reference-token aliases written by LLMs to the canonical Chinese tokens.

Hook points: seedance2_i2v/prompt.py, seedance2_i2v/request.py, generators/video_generator.py.
Only active when MANNA_ASSET_LANGUAGE=en.
"""

from __future__ import annotations

import re

from novelvideo.manna_ext.language import manna_asset_language

_PREFIX = {"image": "图片", "img": "图片", "video": "视频", "audio": "音频", "text": "文本"}  # i18n-exempt: protocol tokens
_ALIAS = re.compile(
    r"(?<![A-Za-z0-9])(@?)(image|img|video|audio|text)\s?(\d{1,2})(?![0-9A-Za-z])",
    re.IGNORECASE,
)


def normalize_reference_aliases(text: str) -> str:
    if not text or manna_asset_language() is None:
        return text

    def _sub(m: re.Match[str]) -> str:
        at, word, num = m.groups()
        if not at and word.lower() != "image":
            return m.group(0)
        return f"@{_PREFIX[word.lower()]}{num}"

    return _ALIAS.sub(_sub, text)
