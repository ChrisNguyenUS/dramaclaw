"""Provider presets for Manna Studio gateway channels.

Channel type ids are reserved in dramaclaw-gateway constant/channel_manna.go
(see Manna Studio docs/adr/0002-reserved-channel-ids.md).
"""

from typing import Any

MANNA_PROVIDER_PRESETS: dict[str, dict[str, Any]] = {
    "lumixai": {"label": "LumixAI", "type": 1001, "base_url": "https://api.lumixai.live"},
}
