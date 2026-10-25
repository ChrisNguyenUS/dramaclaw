from novelvideo.newapi_provisioner import PROVIDER_PRESETS


def test_lumixai_preset_matches_gateway_reserved_channel_type():
    assert PROVIDER_PRESETS["lumixai"] == {
        "label": "LumixAI",
        "type": 1001,
        "base_url": "https://api.lumixai.live",
    }


def test_upstream_presets_are_untouched():
    assert PROVIDER_PRESETS["openrouter"]["type"] == 20
