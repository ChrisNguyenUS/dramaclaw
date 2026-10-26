"""P2b Task 3: the film language reaches agents, recipes and task runners, scoped per run."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from novelvideo.manna_ext import language as ml
from novelvideo.ports.authz import AdmissionContext, BillingPrincipal
from novelvideo.ports.model_credentials import CredentialReference
from novelvideo.project_context import ProjectContext
from novelvideo.task_backend import registry as registry_module
from novelvideo.task_backend.consumer import VerifiedTaskDelivery
from novelvideo.task_backend.registry import register_project_task_runner


# --- helpers -------------------------------------------------------------------------


def test_agent_language_block(monkeypatch):
    monkeypatch.setenv("MANNA_ASSET_LANGUAGE", "en")
    block = ml.agent_language_block("vi")
    assert block.startswith("[MANNA_LANGUAGE]\n")
    assert ml.VIETNAMESE_FILM_RULE in block
    assert ml.VIETNAMESE_FILM_RULE not in ml.agent_language_block("en")
    monkeypatch.delenv("MANNA_ASSET_LANGUAGE")
    assert ml.agent_language_block("vi") == ""


def test_recipe_language_line(monkeypatch):
    monkeypatch.setenv("MANNA_ASSET_LANGUAGE", "en")
    token = ml.bind_film_language("vi")
    try:
        assert ml.recipe_language_line().endswith(ml.VIETNAMESE_FILM_RULE)
    finally:
        ml.reset_film_language(token)
    assert ml.recipe_language_line() == "\n\nLanguage: write the output in English."
    monkeypatch.delenv("MANNA_ASSET_LANGUAGE")
    assert ml.recipe_language_line() == ""


async def test_binding_is_scoped_and_reset():
    async def worker(lang: str) -> str:
        token = ml.bind_film_language(lang)
        try:
            await asyncio.sleep(0)
            return ml.current_film_language()
        finally:
            ml.reset_film_language(token)

    results = await asyncio.gather(worker("en"), worker("vi"), worker("vi"), worker("en"))
    assert results == ["en", "vi", "vi", "en"]
    assert ml.current_film_language() == "en"


def test_load_film_language_for_project_falls_back(monkeypatch):
    import novelvideo.project_config as pc

    monkeypatch.setattr(pc, "load_project_config", lambda _u, _p: {"film_language": "vi"})
    assert ml.load_film_language_for_project("u", "p") == "vi"

    def boom(_u, _p):
        raise RuntimeError("no project")

    monkeypatch.setattr(pc, "load_project_config", boom)
    assert ml.load_film_language_for_project("u", "p") == "en"


# --- agent envelope ------------------------------------------------------------------


def test_agent_envelope_carries_language_block(monkeypatch):
    from novelvideo.chat import service as chat_service

    monkeypatch.setenv("MANNA_ASSET_LANGUAGE", "en")
    monkeypatch.setattr(ml, "load_film_language_for_project", lambda _u, _p: "vi")
    prompt = chat_service._prompt_with_user_context("alice", "demo", "make a hook ad")
    assert "[MANNA_LANGUAGE]" in prompt
    assert ml.VIETNAMESE_FILM_RULE in prompt
    # The block sits after the surface instructions, right before the user message.
    assert prompt.index("[MANNA_LANGUAGE]") < prompt.index("[USER_MESSAGE]")

    monkeypatch.delenv("MANNA_ASSET_LANGUAGE")
    assert "[MANNA_LANGUAGE]" not in chat_service._prompt_with_user_context("alice", "demo", "hi")


# --- recipe compile task ---------------------------------------------------------------


def test_recipe_compiler_task_gets_language_line(monkeypatch):
    from novelvideo.freezone.recipe_runtime import build_recipe_compiler_task

    monkeypatch.setenv("MANNA_ASSET_LANGUAGE", "en")
    token = ml.bind_film_language("vi")
    try:
        task = build_recipe_compiler_task(
            recipe={"output_kind": "", "system_prompt": "Write a storyboard."},
            node_kind="textGeneration",
            node_prompt="serum hook ad",
        )
    finally:
        ml.reset_film_language(token)
    recipe_block = task.split("Trusted Recipe instructions:\n", 1)[1].split("\n\nUpstream text context:", 1)[0]
    assert recipe_block.startswith("Write a storyboard.")
    assert recipe_block.endswith(ml.VIETNAMESE_FILM_RULE)


# --- task runner boundary --------------------------------------------------------------


class _FakeTaskManager:
    def __init__(self) -> None:
        self.completed: list[dict] = []
        self.failed: list[dict] = []

    def update_progress_for_project(self, *_args, **_kwargs) -> None:
        pass

    def begin_task_execution_for_project(self, *_args, **_kwargs) -> bool:
        return True

    def complete_task_for_project(self, *_args, **kwargs) -> None:
        self.completed.append(kwargs)

    def fail_task_for_project(self, *_args, **kwargs) -> None:
        self.failed.append(kwargs)


def _delivery(task_type: str) -> VerifiedTaskDelivery:
    admission = AdmissionContext(
        requester_user_id="usr_1",
        billing_principal=BillingPrincipal(kind="local", id="usr_1"),
        credential=CredentialReference("local", "local-newapi", 1),
        admission_id="admission-1",
        root_task_id="task_1",
        admitted_at="2026-08-03T04:05:00Z",
        authz_version=1,
    )
    return VerifiedTaskDelivery(
        envelope_id="envelope-1",
        admission=admission,
        task_type=task_type,
        project_id="proj_lang",
        requester_user_id="usr_1",
        episode=0,
        beat_num=None,
        scope=None,
        queue_kind="default",
        payload={},
    )


def _ctx(tmp_path: Path) -> ProjectContext:
    return ProjectContext(
        project_id="proj_lang",
        project_name="demo",
        owner_type="user",
        owner_id="owner_1",
        owner_username="alice",
        requester_user_id="usr_1",
        requester_username="alice",
        requester_principals=(("user", "usr_1"),),
        effective_role="editor",
        home_node_id="node_a",
        output_dir=tmp_path / "output",
        state_dir=tmp_path / "state",
        runtime_dir=tmp_path / "runtime",
        is_home_node=True,
    )


@pytest.fixture
def quiet_run_core(monkeypatch):
    from novelvideo.task_backend import run_core

    async def fake_is_cancel_requested(**_kwargs):
        return False

    async def fake_emit(*_args, **_kwargs):
        return None

    monkeypatch.setattr(registry_module, "_PROJECT_TASK_RUNNERS", dict(registry_module._PROJECT_TASK_RUNNERS))
    monkeypatch.setattr(registry_module, "_PROJECT_TASK_PLACEMENTS", dict(registry_module._PROJECT_TASK_PLACEMENTS))
    monkeypatch.setattr(run_core, "_ensure_builtin_runners_registered", lambda: None)
    monkeypatch.setattr(run_core, "is_cancel_requested", fake_is_cancel_requested)
    monkeypatch.setattr(run_core, "_emit_project_task_metrics", fake_emit)
    monkeypatch.setattr(run_core, "_set_project_task_metrics_context", lambda *_a, **_k: None)
    monkeypatch.setattr(run_core, "_clear_project_task_metrics_context", lambda: None)
    monkeypatch.setattr(run_core, "_project_task_timeout_seconds", lambda: 30 * 60)
    return run_core


def test_run_core_binds_film_language(tmp_path, quiet_run_core):
    ctx = _ctx(tmp_path)
    Path(ctx.state_dir).mkdir(parents=True)
    (Path(ctx.state_dir) / "project_config.json").write_text(json.dumps({"film_language": "vi"}))
    seen: list[str] = []

    def runner(_envelope, _ctx):
        seen.append(ml.current_film_language())
        return {"ok": True}

    register_project_task_runner("manna_lang_probe", runner)
    quiet_run_core.run_project_task_core_sync(
        _delivery("manna_lang_probe"), ctx, _FakeTaskManager(), run_task_id="task_1"
    )
    assert seen == ["vi"]
    assert ml.current_film_language() == "en"


# --- freezone recipe compile route -----------------------------------------------------


async def test_recipe_compile_route_binds_project_film_language(monkeypatch, tmp_path):
    from types import SimpleNamespace

    from novelvideo.api.routes import freezone

    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "project_config.json").write_text(json.dumps({"film_language": "vi"}))
    seen: list[str] = []

    async def fake_admission(**_kwargs):
        return None

    async def fake_resolve(_project_id, _user):
        return SimpleNamespace(state_dir=str(state_dir)), "alice", "demo", tmp_path, tmp_path

    async def fake_compile(**_kwargs):
        seen.append(ml.current_film_language())
        return SimpleNamespace(prompt="ok")

    async def fake_evidence(**_kwargs):
        return None

    monkeypatch.setattr(freezone, "_require_recipe_compile_product_admission", fake_admission)
    monkeypatch.setattr(freezone, "_resolve_freezone_project", fake_resolve)
    monkeypatch.setattr(freezone, "compile_recipe_prompt_result", fake_compile)
    monkeypatch.setattr(freezone, "_recipe_compile_args", lambda _body, _user: {})
    monkeypatch.setattr(freezone, "_record_recipe_compile_product_evidence", fake_evidence)
    monkeypatch.setattr(freezone, "_recipe_compile_response", lambda compiled: {"prompt": compiled.prompt})

    body = SimpleNamespace(project_id="proj", product_operation_id="")
    result = await freezone.compile_freezone_recipe(body, user={"username": "alice"})
    assert result == {"prompt": "ok"}
    assert seen == ["vi"]
    assert ml.current_film_language() == "en"


async def test_recipe_state_dir_helper_tolerates_missing_project():
    from types import SimpleNamespace

    from novelvideo.api.routes import freezone

    assert await freezone._manna_recipe_state_dir(SimpleNamespace(project_id=""), {}) is None


def test_recipe_compile_route_still_points_at_the_route_handler():
    from novelvideo.api.routes import freezone

    endpoints = {
        route.path: route.endpoint.__name__
        for route in freezone.router.routes
        if getattr(route, "path", "").endswith("/freezone/recipes/compile")
    }
    assert set(endpoints.values()) == {"compile_freezone_recipe"}, endpoints


# --- placement-free tasks carry the language in the payload ----------------------------


def test_payload_with_film_language(monkeypatch, tmp_path):
    (tmp_path / "project_config.json").write_text(json.dumps({"film_language": "vi"}))
    monkeypatch.delenv("MANNA_ASSET_LANGUAGE", raising=False)
    original = {"a": 1}
    assert ml.payload_with_film_language(tmp_path, original) is original
    monkeypatch.setenv("MANNA_ASSET_LANGUAGE", "en")
    out = ml.payload_with_film_language(tmp_path, original)
    assert out == {"a": 1, "manna_film_language": "vi"}
    assert original == {"a": 1}
    assert ml.payload_with_film_language(tmp_path, None) == {"manna_film_language": "vi"}


def test_task_film_language_prefers_payload_and_never_reads_state_when_placement_free(tmp_path):
    (tmp_path / "project_config.json").write_text(json.dumps({"film_language": "vi"}))
    assert ml.task_film_language({"manna_film_language": "vi"}, None, may_read_state=False) == "vi"
    assert ml.task_film_language({}, tmp_path, may_read_state=True) == "vi"
    assert ml.task_film_language({}, tmp_path, may_read_state=False) == "en"


async def test_enqueue_facade_adds_film_language(monkeypatch, tmp_path):
    from types import SimpleNamespace

    from novelvideo.task_backend import client

    (tmp_path / "project_config.json").write_text(json.dumps({"film_language": "vi"}))
    monkeypatch.setenv("MANNA_ASSET_LANGUAGE", "en")
    captured: dict = {}

    class Backend:
        async def enqueue_project_task(self, _ctx, **kwargs):
            captured.update(kwargs)
            return "queued"

    monkeypatch.setattr(client, "get_task_backend", lambda: Backend())
    ctx = SimpleNamespace(state_dir=str(tmp_path))
    await client.enqueue_project_task(ctx, task_type="t", product_surface="s", payload={"x": 1})
    assert captured["payload"] == {"x": 1, "manna_film_language": "vi"}


def test_placement_free_task_takes_language_from_payload(tmp_path, quiet_run_core):
    ctx = _ctx(tmp_path)
    seen: list[str] = []

    def runner(_envelope, _ctx):
        seen.append(ml.current_film_language())
        return {"ok": True}

    register_project_task_runner("manna_lang_free", runner, requires_home_node=False)
    delivery = _delivery("manna_lang_free")
    delivery = VerifiedTaskDelivery(**{**delivery.__dict__, "payload": {"manna_film_language": "vi"}})
    quiet_run_core.run_project_task_core_sync(delivery, ctx, _FakeTaskManager(), run_task_id="task_1")
    assert seen == ["vi"]
