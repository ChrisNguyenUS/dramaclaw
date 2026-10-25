import { beforeEach, describe, expect, it, vi } from "vitest";

import type { TaskState } from "@/task-center/types";
import {
  activateDirectorEpisodeAuto,
  awaitDirectorEpisodeAutoConfirmation,
  confirmDirectorEpisodeAuto,
  decideDirectorAutoTask,
  defaultDirectorRunState,
  directorAutoConfirmationTransportText,
  directorAutoInterventionTransportText,
  directorAutoRunTransportText,
  directorAutoUserMessageTransportText,
  directorAutoVoiceChoiceTransportText,
  emphasizeDirectorVoiceChoiceLabels,
  isDirectorEpisodeAutoSession,
  isDirectorEpisodeAutoStartIntent,
  loadDirectorRunState,
  markDirectorAutoHandled,
  resolveDirectorVoicePolicy,
  saveDirectorRunState,
} from "./director-run-mode";

function task(overrides: Partial<TaskState> = {}): TaskState {
  return {
    task_key: "single_video/project/8/1",
    task_id: "task-1",
    task_type: "single_video",
    username: "alice",
    project: "demo",
    episode: 8,
    beat_num: 1,
    scope: null,
    status: "completed",
    progress: 1,
    current_task: "完成",
    result: null,
    error: null,
    logs: [],
    created_at: "2026-08-13T10:00:00Z",
    updated_at: "2026-08-13T10:05:00Z",
    completed_at: "2026-08-13T10:05:00Z",
    ...overrides,
  };
}

describe("director episode auto mode", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.spyOn(Date, "now").mockReturnValue(Date.parse("2026-08-13T10:01:00Z"));
  });

  it("persists auto mode per project and removes manual mode", () => {
    const active = activateDirectorEpisodeAuto();
    saveDirectorRunState("project-a", active);
    expect(loadDirectorRunState("project-a").mode).toBe("episode_auto");
    expect(loadDirectorRunState("project-b").mode).toBe("manual_confirm");

    saveDirectorRunState("project-a", defaultDirectorRunState());
    expect(loadDirectorRunState("project-a").mode).toBe("manual_confirm");
  });

  it("continues a completed mainline task and binds its episode", () => {
    const state = confirmDirectorEpisodeAuto(activateDirectorEpisodeAuto());
    const decision = decideDirectorAutoTask(state, task());
    expect(decision.action).toBe("continue");
    if (decision.action !== "continue") return;
    const next = markDirectorAutoHandled(state, decision.key, decision.episode);
    expect(next.episode).toBe(8);
    expect(decideDirectorAutoTask(next, task()).action).toBe("ignore");
  });

  it("continues from project-level episode planning into episode one", () => {
    const state = confirmDirectorEpisodeAuto(activateDirectorEpisodeAuto());
    const decision = decideDirectorAutoTask(state, task({
      task_type: "build_episodes",
      episode: 0,
      task_key: "build_eps/project/0/0",
    }));
    expect(decision).toMatchObject({ action: "continue", episode: 1 });
  });

  it("pauses on failure and completes after episode composition", () => {
    const state = confirmDirectorEpisodeAuto(activateDirectorEpisodeAuto());
    expect(decideDirectorAutoTask(state, task({ status: "failed" })).action).toBe("pause");
    expect(decideDirectorAutoTask(
      state,
      task({ task_type: "compose_episode" }),
    ).action).toBe("complete");
  });

  it("ignores stale, unrelated, and different-episode tasks", () => {
    const state = {
      ...confirmDirectorEpisodeAuto(activateDirectorEpisodeAuto()),
      episode: 8,
    };
    expect(decideDirectorAutoTask(state, task({ task_type: "stage_asset" })).action).toBe("ignore");
    expect(decideDirectorAutoTask(state, task({ episode: 9 })).action).toBe("ignore");
    expect(decideDirectorAutoTask(
      state,
      task({ updated_at: "2026-08-13T09:59:00Z" }),
    ).action).toBe("ignore");
  });

  it("accepts episode-zero asset tasks only after the auto run is bound to an episode", () => {
    const unbound = confirmDirectorEpisodeAuto(activateDirectorEpisodeAuto());
    const assetTask = task({ task_type: "identity_image", episode: 0 });
    expect(decideDirectorAutoTask(unbound, assetTask).action).toBe("ignore");

    const bound = { ...unbound, episode: 8 };
    const decision = decideDirectorAutoTask(bound, assetTask);
    expect(decision).toMatchObject({ action: "continue", episode: 8 });
  });

  it("continues after a character portrait finishes for the bound episode", () => {
    const state = {
      ...confirmDirectorEpisodeAuto(activateDirectorEpisodeAuto()),
      episode: 1,
    };
    const decision = decideDirectorAutoTask(state, task({
      task_type: "character_portrait",
      episode: 0,
      scope: "character:苏糖:portrait",
      task_key: "character_portrait/project/0/苏糖",
    }));
    expect(decision).toMatchObject({ action: "continue", episode: 1 });
  });

  it("marks UI auto approval without mentioning Agent credits", () => {
    const text = directorAutoRunTransportText("继续下一步");
    expect(text).toContain("mode=episode_auto");
    expect(text).toContain("one-write-per-turn");
    expect(text).toContain("never applies Agent-credit billing");
    expect(text).toContain("already running now");
    expect(text).toContain("do not merely describe");
  });

  it("requires a start request and then a second confirmation before running", () => {
    const selected = activateDirectorEpisodeAuto();
    expect(selected.confirmationStage).toBe("awaiting_start");
    expect(decideDirectorAutoTask(selected, task()).action).toBe("ignore");

    const awaitingConfirmation = awaitDirectorEpisodeAutoConfirmation(selected);
    expect(awaitingConfirmation.confirmationStage).toBe("awaiting_confirmation");
    expect(decideDirectorAutoTask(awaitingConfirmation, task()).action).toBe("ignore");

    const confirmed = confirmDirectorEpisodeAuto(awaitingConfirmation);
    expect(confirmed.confirmationStage).toBe("confirmed");
    expect(decideDirectorAutoTask(confirmed, task()).action).toBe("continue");
  });

  it("recognizes positive start phrases but rejects negated ones", () => {
    expect(isDirectorEpisodeAutoStartIntent("开始生成第 1 集")).toBe(true);
    expect(isDirectorEpisodeAutoStartIntent("确认")).toBe(true);
    expect(isDirectorEpisodeAutoStartIntent("继续吧")).toBe(true);
    expect(isDirectorEpisodeAutoStartIntent("先不要开始")).toBe(false);
    expect(isDirectorEpisodeAutoStartIntent("看看当前状态")).toBe(false);
  });

  it("rejects English negations with smart apostrophes, wide gaps, and deferrals", () => {
    for (const text of [
      "don\u2019t start yet",
      "Don\u2019t continue",
      "I don't want you to start this yet",
      "not now, start later",
      "wait, don't continue",
      "Won\u2019t be ready, hold on",
      "can\u2019t proceed right now",
    ]) {
      expect(isDirectorEpisodeAutoStartIntent(text), text).toBe(false);
    }
    expect(isDirectorEpisodeAutoStartIntent("start now")).toBe(true);
    expect(isDirectorEpisodeAutoStartIntent("go ahead and start")).toBe(true);
    expect(isDirectorEpisodeAutoStartIntent("Yes. Wait is over. Start the episode")).toBe(true);
  });

  it("recognizes English start phrases but rejects negated ones", () => {
    expect(isDirectorEpisodeAutoStartIntent("Start episode 1")).toBe(true);
    expect(isDirectorEpisodeAutoStartIntent("Confirm")).toBe(true);
    expect(isDirectorEpisodeAutoStartIntent("go ahead")).toBe(true);
    expect(isDirectorEpisodeAutoStartIntent("don't start yet")).toBe(false);
    expect(isDirectorEpisodeAutoStartIntent("Please cancel, do not continue")).toBe(false);
    expect(isDirectorEpisodeAutoStartIntent("What is the current status?")).toBe(false);
  });

  it("uses a confirmation-only transport instruction before activation", () => {
    const text = directorAutoConfirmationTransportText("开始");
    expect(text).toContain("required second confirmation");
    expect(text).toContain("Do not call any write, generation, or mutation tool");
    expect(text).toContain("reply Continue or Confirm");
    expect(text).toContain("Episode Auto");
  });

  it("keeps a suspended intervention inside the same auto session", () => {
    const suspended = {
      ...confirmDirectorEpisodeAuto(activateDirectorEpisodeAuto()),
      confirmationStage: "awaiting_intervention" as const,
    };
    saveDirectorRunState("project-a", suspended);

    expect(loadDirectorRunState("project-a").confirmationStage).toBe("awaiting_intervention");
    expect(isDirectorEpisodeAutoSession(suspended)).toBe(true);
    expect(decideDirectorAutoTask(suspended, task()).action).toBe("ignore");
  });

  it("asks the agent to resume after a declined modification without cancelling tasks", () => {
    const text = directorAutoInterventionTransportText("不改了，继续自动");
    expect(text).toContain("action='resume'");
    expect(text).toContain("action='pause'");
    expect(text).toContain("must not be cancelled");
  });

  it("requires the agent to suspend before asking about a possible modification", () => {
    const text = directorAutoRunTransportText("这个镜头换成夜景呢");
    expect(text).toContain("action='suspend'");
    expect(text).toContain("do not perform that mutation yet");
  });

  it("does not treat ordinary user messages as automatic next-step commands", () => {
    const text = directorAutoUserMessageTransportText("现在做到哪了");
    expect(text).toContain("do not start the next mainline task merely because this message arrived");
    expect(text).toContain("read only");
    expect(text).toContain("action='suspend'");
  });

  it("requires an explicit voice policy when preflight finds missing voices", () => {
    const text = directorAutoConfirmationTransportText("开始", {
      voiceChoiceRequired: true,
      voiceErrors: ["解说声线缺失"],
    });
    expect(text).toContain("System voice");
    expect(text).toContain("Custom voice");
    expect(text).toContain("解说声线缺失");
    expect(directorAutoVoiceChoiceTransportText("确认")).toContain("Do not start episode auto");
  });

  it("recognizes an explicit system or custom voice choice", () => {
    expect(resolveDirectorVoicePolicy("使用系统声线继续")).toBe("system");
    expect(resolveDirectorVoicePolicy("系统声一")).toBe("system");
    expect(resolveDirectorVoicePolicy("使用系统声音")).toBe("system");
    expect(resolveDirectorVoicePolicy("我去虾塘上传或录制")).toBe("custom");
    expect(resolveDirectorVoicePolicy("使用自定义声音")).toBe("custom");
    expect(resolveDirectorVoicePolicy("你说系统还是自定义？")).toBeNull();
  });

  it("recognizes an English system or custom voice choice", () => {
    expect(resolveDirectorVoicePolicy("Use the system voice")).toBe("system");
    expect(resolveDirectorVoicePolicy("Custom voice please")).toBe("custom");
    expect(resolveDirectorVoicePolicy("I will upload my own")).toBe("custom");
    expect(resolveDirectorVoicePolicy("Which is better, system or custom?")).toBeNull();
  });

  it("emphasizes only the two labels inside a voice-choice prompt", () => {
    expect(emphasizeDirectorVoiceChoiceLabels(
      "1）系统声线；2）自定义声线。请回复 系统声线 或 自定义声线。",
    )).toBe(
      "1）**系统声线**；2）**自定义声线**。请回复 **系统声线** 或 **自定义声线**。",
    );
    expect(emphasizeDirectorVoiceChoiceLabels("当前使用系统声线。"))
      .toBe("当前使用系统声线。");
  });

  it("emphasizes the English voice labels inside an English voice-choice prompt", () => {
    expect(emphasizeDirectorVoiceChoiceLabels(
      "1) System voice; 2) Custom voice. Please reply System voice or Custom voice.",
    )).toBe(
      "1) **System voice**; 2) **Custom voice**. Please reply **System voice** or **Custom voice**.",
    );
    expect(emphasizeDirectorVoiceChoiceLabels("Currently using System voice."))
      .toBe("Currently using System voice.");
  });
});
