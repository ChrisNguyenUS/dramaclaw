from novelvideo.manna_ext.chat_text import english_chat_text
from novelvideo.chat import director_auto
from novelvideo.chat.director_auto import DirectorAutoCoordinator
import pytest


def test_episode_auto_notice_translates_and_keeps_character(monkeypatch):
    monkeypatch.setenv("MANNA_ASSET_LANGUAGE", "en")
    text = '本集自动已暂停：未能启动「Mira」肖像生成，请检查角色肖像配置。'
    assert english_chat_text(text) == "Episode automation paused: could not start portrait generation for ‘Mira’. Check the character portrait settings."


def test_failure_notice_preserves_dynamic_error(monkeypatch):
    monkeypatch.setenv("MANNA_ASSET_LANGUAGE", "en")
    assert english_chat_text("本轮处理失败：socket timeout\n\n请根据错误提示处理后重试。") == (
        "This turn failed: socket timeout\n\nReview the error and try again."
    )


def test_skill_studio_status_uses_frontend_copy(monkeypatch):
    monkeypatch.setenv("MANNA_ASSET_LANGUAGE", "en")
    assert english_chat_text("正在整理 Skill 方向...") == "Organizing the Skill direction..."


def test_switch_off_and_unknown_text_are_unchanged(monkeypatch):
    monkeypatch.delenv("MANNA_ASSET_LANGUAGE", raising=False)
    text = "本轮处理失败：socket timeout\n\n请根据错误提示处理后重试。"
    assert english_chat_text(text) == text
    monkeypatch.setenv("MANNA_ASSET_LANGUAGE", "en")
    assert english_chat_text("unknown text") == "unknown text"


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("本集自动已暂停：当前用户已无权继续修改该项目。", "Episode automation paused: you no longer have permission to edit this project."),
        ("本集自动已暂停：虾导长时间处于忙碌状态。", "Episode automation paused: the director remained busy for too long."),
        ("本集自动已暂停：虾导继续执行失败，请检查服务状态后重试。", "Episode automation paused: the director could not continue. Check the service and try again."),
        ("检测到角色身份图缺少前置肖像，正在自动补生成「Mira」肖像。", "Character identity image is missing a required portrait. Generating a portrait for ‘Mira’ automatically."),
        ("本集自动已暂停：角色身份图已取消，provider timeout。", "Episode automation paused: Character identity image was cancelled. provider timeout."),
        ("✅ 本批 3 个任务已完成。", "✅ 3 tasks completed."),
        ("✅ 角色身份图已完成。", "✅ Character identity image completed."),
        ("✅ 角色身份图已完成。本集自动正在继续下一步。", "✅ Character identity image completed. Episode automation is continuing with the next step."),
        ("✅ 成片合成已完成。正在展示第 2 集成片。", "✅ Episode composition completed. Showing the final cut for episode 2."),
        ("本集自动已暂停：当前步骤没有产生新的生成任务，请检查前置条件。", "Episode automation paused: the current step did not create a new generation task. Check its prerequisites."),
        ("本集自动已暂停：虾导没有启动新的生成步骤，请检查当前前置条件。", "Episode automation paused: the director did not start a new generation step. Check the current prerequisites."),
        ("项目不存在或已删除，已切回首页聊天。", "This project no longer exists or was deleted. Switched back to home chat."),
    ],
)
def test_known_templates_are_english_and_keep_dynamic_fields(monkeypatch, source, expected):
    monkeypatch.setenv("MANNA_ASSET_LANGUAGE", "en")
    translated = english_chat_text(source)
    assert translated == expected
    assert not any("\u4e00" <= char <= "\u9fff" for char in translated)


def test_error_detail_is_preserved_verbatim(monkeypatch):
    monkeypatch.setenv("MANNA_ASSET_LANGUAGE", "en")
    assert "provider timeout" in english_chat_text(
        "本轮处理失败：provider timeout\n\n请根据错误提示处理后重试。"
    )


@pytest.mark.asyncio
async def test_director_auto_notice_is_translated_before_persistence(monkeypatch, tmp_path):
    monkeypatch.setenv("MANNA_ASSET_LANGUAGE", "en")
    saved: list[str] = []
    broadcast: list[dict] = []

    def add_message(_username, _project, text, _media, **_kwargs):
        saved.append(text)
        return {"content": text}

    async def send_event(**kwargs):
        broadcast.append(kwargs["payload"])

    monkeypatch.setattr(director_auto.chat_service, "add_assistant_message", add_message)
    monkeypatch.setattr(director_auto, "broadcast_project_chat_event", send_event)

    run = director_auto.DirectorAutoRun(
        run_id="run-1",
        username="alice",
        project_id="project-1",
        episode=1,
        status="running",
        activated_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
        context_json=director_auto._serialize_context(
            director_auto.ProjectContext(
                project_id="project-1", project_name="demo", owner_type="user", owner_id="1",
                owner_username="alice", requester_user_id="1", requester_username="alice",
                requester_principals=(("user", "1"),), effective_role="owner", home_node_id="local",
                output_dir=tmp_path, state_dir=tmp_path, runtime_dir=tmp_path, is_home_node=True,
            )
        ),
        baseline_task_ids=(),
        handled_task_ids=(),
    )
    await DirectorAutoCoordinator()._notify(run, "本集自动已暂停：当前用户已无权继续修改该项目。")

    assert saved == ["Episode automation paused: you no longer have permission to edit this project."]
    assert broadcast[0]["message"]["content"] == saved[0]
