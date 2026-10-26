from pathlib import Path
from types import SimpleNamespace

import pytest

from novelvideo import config as nv_config
from novelvideo.manna_ext.project_defaults import manna_create_config
from novelvideo.ports.project import ProjectRecord


def test_defaults_off(monkeypatch):
    monkeypatch.delenv("MANNA_ASSET_LANGUAGE", raising=False)
    assert manna_create_config("vi") == {}


def test_defaults_en(monkeypatch):
    monkeypatch.setenv("MANNA_ASSET_LANGUAGE", "en")
    assert manna_create_config(None) == {
        "film_language": "en",
        "ethnicity": "",
        "visual_style": "realistic",
        "aspect_ratio": "9:16",
    }


def test_defaults_vi(monkeypatch):
    monkeypatch.setenv("MANNA_ASSET_LANGUAGE", "en")
    assert manna_create_config("vi")["ethnicity"] == "Vietnamese"
    assert manna_create_config("vi")["film_language"] == "vi"


def test_schema_fields():
    from novelvideo.api.schemas import ProjectCreate, ProjectUpdate

    assert ProjectCreate(name="a", film_language="vi").film_language == "vi"
    assert ProjectCreate(name="a").film_language is None
    assert ProjectUpdate(film_language="en").model_dump(exclude_none=True) == {"film_language": "en"}
    with pytest.raises(Exception):
        ProjectUpdate(film_language="fr")


def test_realistic_is_a_valid_style_preset():
    preset = Path(nv_config.__file__).parent / "styles" / "presets" / "realistic.json"
    assert preset.exists()


async def _create(monkeypatch, tmp_path, body):
    """Run the real create route with storage collaborators stubbed; return the saved config."""
    from novelvideo.api.routes import projects

    monkeypatch.setattr(nv_config, "OUTPUT_DIR", tmp_path / "output")
    monkeypatch.setattr(nv_config, "STATE_DIR", tmp_path / "state")
    monkeypatch.setattr(nv_config, "RUNTIME_DIR", tmp_path / "runtime")
    record = ProjectRecord(
        id="01PROJECT",
        owner_type="user",
        owner_id="local",
        owner_username="alice",
        name="demo",
        home_node_id="local",
        output_dir=str(tmp_path / "output" / "alice" / "demo"),
        state_dir=str(tmp_path / "state" / "alice" / "demo"),
        runtime_dir=str(tmp_path / "runtime" / "alice" / "demo"),
        status="active",
    )
    saved: dict = {}

    class Registry:
        async def create_project(self, **_kwargs):
            return record

        async def delete_uncommitted_project(self, _project_id):
            raise AssertionError("successful creation must not be compensated")

    async def fake_user_id(_user):
        return "local"

    def ensure_dirs(*, output_dir, state_dir, runtime_dir):
        for path in (output_dir, state_dir, runtime_dir):
            Path(path).mkdir(parents=True, exist_ok=True)

    def save_config(_state_dir, *, config):
        saved.update(config)

    monkeypatch.setattr(projects, "validate_project_name", lambda _name: None)
    monkeypatch.setattr(projects, "user_id_from_api_user", fake_user_id)
    monkeypatch.setattr(projects, "get_project_registry", lambda: Registry())
    monkeypatch.setattr(projects, "ensure_project_dirs_at_paths", ensure_dirs)
    monkeypatch.setattr(projects, "save_project_config_in_state_dir", save_config)
    monkeypatch.setattr(
        projects,
        "embedding_model_binding_for_new_project",
        lambda: SimpleNamespace(internal_model="embed", dimensions=1024),
    )
    result = await projects.create_project(body, user={"id": "local", "username": "alice"})
    assert result["ok"] is True
    return saved


async def test_create_route_persists_film_language_and_defaults(monkeypatch, tmp_path):
    from novelvideo.api.schemas import ProjectCreate

    monkeypatch.setenv("MANNA_ASSET_LANGUAGE", "en")
    saved = await _create(monkeypatch, tmp_path, ProjectCreate(name="demo", film_language="vi"))
    assert saved["film_language"] == "vi"
    assert saved["ethnicity"] == "Vietnamese"
    assert saved["visual_style"] == "realistic"
    assert saved["aspect_ratio"] == "9:16"
    assert saved["user"] == "alice"


async def test_create_route_unchanged_when_switch_off(monkeypatch, tmp_path):
    from novelvideo.api.schemas import ProjectCreate

    monkeypatch.delenv("MANNA_ASSET_LANGUAGE", raising=False)
    saved = await _create(monkeypatch, tmp_path, ProjectCreate(name="demo", film_language="vi"))
    assert "film_language" not in saved
    assert "visual_style" not in saved
