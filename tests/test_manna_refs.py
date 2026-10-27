"""P2b Task 7: English reference aliases written by LLMs map to the canonical Chinese tokens."""

import pytest

from novelvideo.manna_ext.refs import normalize_reference_aliases as n


@pytest.fixture(autouse=True)
def english(monkeypatch):
    monkeypatch.setenv("MANNA_ASSET_LANGUAGE", "en")


def test_aliases():
    assert n("Use @Image1 as the opening frame") == "Use @图片1 as the opening frame"  # i18n-exempt: protocol token
    assert n("@image 2 and @Video3, @audio1, @Text4") == "@图片2 and @视频3, @音频1, @文本4"  # i18n-exempt: protocol tokens
    assert n("Image1 holds the bottle") == "@图片1 holds the bottle"  # i18n-exempt: protocol token
    assert n("@IMG5") == "@图片5"  # i18n-exempt: protocol token


def test_untouched():
    for s in ["MyImage1", "image-to-video", "Image 1080p", "@图片1 stays", "imagery1", "the image is bright", "", "video1 call"]:  # i18n-exempt: protocol token
        assert n(s) == s


def test_idempotent():
    s = "Use @Image1 then @视频2"  # i18n-exempt: protocol token
    assert n(n(s)) == n(s)


def test_off_without_switch(monkeypatch):
    monkeypatch.delenv("MANNA_ASSET_LANGUAGE")
    assert n("Use @Image1") == "Use @Image1"


def test_seedance_wire_prompt_resolves_alias():
    from novelvideo.seedance2_i2v.request import normalize_seedance2_prompt

    assert normalize_seedance2_prompt("@Image1 walks") == normalize_seedance2_prompt("@图片1 walks")  # i18n-exempt: protocol token


def test_seedance_editor_prompt_resolves_alias():
    from novelvideo.seedance2_i2v.prompt import normalize_seedance2_editor_prompt

    assert normalize_seedance2_editor_prompt("Use @Video 2 for motion") == "Use 视频2 for motion"  # i18n-exempt: protocol token


def test_newapi_video_payload_resolves_alias():
    from novelvideo.generators.video_generator import NewApiVideoGenerator

    payload = {"prompt": "Use @Image1 as the first frame", "model": "x"}
    NewApiVideoGenerator._canonicalize_video_payload(payload, {})
    assert payload["prompt"] == "Use @图片1 as the first frame"  # i18n-exempt: protocol token


def test_image_prompt_merge_resolves_alias():
    from novelvideo.api import routes  # noqa: F401  (import order avoids a circular import)
    from novelvideo.freezone.route_helpers import merge_prompt_with_style_and_camera

    assert merge_prompt_with_style_and_camera("@Image2 in rain", None, None) == "@图片2 in rain"  # i18n-exempt: protocol token
