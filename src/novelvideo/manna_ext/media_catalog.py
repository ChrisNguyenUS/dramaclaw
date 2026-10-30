"""English labels for media-model request parameters (Canvas model controls).

The catalog comes from the bundled official_media_models.json or a gateway sync, so labels are
translated where it is served, not in the file. Hook point: api/routes/freezone.py
_public_media_model_catalog. Only active when MANNA_ASSET_LANGUAGE=en.
"""

from __future__ import annotations

import copy
import re
from typing import Any

from novelvideo.manna_ext.language import manna_asset_language

_CJK = re.compile(r"[一-鿿]")
_LABELS = {  # i18n-exempt: source labels from the upstream model catalog
    "生成水印": "Watermark",
    "智能改写": "Smart prompt rewrite",
    "随机种子": "Random seed",
    "输出格式": "Output format",
    "负向提示词": "Negative prompt",
    "反向提示词": "Negative prompt",
    "提示词": "Prompt",
    "时长": "Duration",
    "分辨率": "Resolution",
    "画面比例": "Aspect ratio",
    "宽高比": "Aspect ratio",
    "质量": "Quality",
    "清晰度": "Resolution",
    "帧率": "Frame rate",
    "镜头运动": "Camera motion",
    "运动强度": "Motion strength",
    "生成音频": "Generate audio",
    "音频": "Audio",
    "数量": "Count",
    "风格": "Style",
    "开启": "On",
    "关闭": "Off",
    "自动": "Auto",
}


def _english(label: str, key: str) -> str:
    if not _CJK.search(label):
        return label
    if label in _LABELS:
        return _LABELS[label]
    # Unknown label from a newer catalog: show the parameter key rather than Chinese.
    return key.replace("_", " ").replace(".", " ").strip().capitalize() or label


def _walk(value: Any, key: str = "") -> None:
    if isinstance(value, dict):
        own_key = str(value.get("key") or value.get("value") or key)
        for name, item in value.items():
            if name == "label" and isinstance(item, str):
                value[name] = _english(item, own_key)
            else:
                _walk(item, own_key)
    elif isinstance(value, list):
        for item in value:
            _walk(item, key)


def english_catalog(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Copy of the catalog with Chinese parameter/option labels in English; identity when off."""
    if manna_asset_language() is None:
        return entries
    out = copy.deepcopy(entries)
    for entry in out:
        for name in ("request", "config"):
            if isinstance(entry, dict) and isinstance(entry.get(name), dict):
                _walk(entry[name])
    return out
