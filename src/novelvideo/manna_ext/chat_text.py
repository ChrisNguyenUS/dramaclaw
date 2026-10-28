"""English translations for fixed backend chat-stream copy."""

from __future__ import annotations

import os
import re

_TEMPLATES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"本轮处理失败：(?P<detail>.*?)\n\n请根据错误提示处理后重试。", re.S), "This turn failed: {detail}\n\nReview the error and try again."),
    (re.compile(r"本轮处理失败：服务未返回可识别的错误原因，请稍后重试。"), "This turn failed: the service returned no recognizable error. Please try again later."),
    (re.compile(r"项目不存在或已删除，已切回首页聊天。"), "This project no longer exists or was deleted. Switched back to home chat."),
    (re.compile(r"正在整理 Skill 方向\.\.\."), "Organizing the Skill direction..."),
    (re.compile(r"本集自动已暂停：当前用户已无权继续修改该项目。"), "Episode automation paused: you no longer have permission to edit this project."),
    (re.compile(r"本集自动已暂停：虾导长时间处于忙碌状态。"), "Episode automation paused: the director remained busy for too long."),
    (re.compile(r"本集自动已暂停：虾导继续执行失败，请检查服务状态后重试。"), "Episode automation paused: the director could not continue. Check the service and try again."),
    (re.compile(r"本集自动已暂停：未能启动「(?P<character>.+?)」肖像生成，请检查角色肖像配置。"), "Episode automation paused: could not start portrait generation for ‘{character}’. Check the character portrait settings."),
    (re.compile(r"本集自动已暂停：(?P<label>.+?)(?P<state>已取消|失败)，(?P<reason>.+)。"), "Episode automation paused: {label} {state}. {reason}."),
    (re.compile(r"检测到(?P<label>.+)缺少前置肖像，正在自动补生成「(?P<character>.+)」肖像。"), "{label} is missing a required portrait. Generating a portrait for ‘{character}’ automatically."),
    (re.compile(r"✅ 本批 (?P<count>\d+) 个任务已完成。"), "✅ {count} tasks completed."),
    (re.compile(r"✅ (?P<label>.+)已完成。"), "✅ {label} completed."),
    (re.compile(r"(?P<summary>✅ .+?)已完成。正在展示第 (?P<episode>\d+) 集成片。"), "{summary} completed. Showing the final cut for episode {episode}."),
    (re.compile(r"(?P<summary>.+)正在展示第 (?P<episode>\d+) 集成片。"), "{summary} Showing the final cut for episode {episode}."),
    (re.compile(r"(?P<summary>.+)本集自动正在继续下一步。"), "{summary} Episode automation is continuing with the next step."),
    (re.compile(r"本集自动已暂停：当前步骤没有产生新的生成任务，请检查前置条件。"), "Episode automation paused: the current step did not create a new generation task. Check its prerequisites."),
    (re.compile(r"本集自动已暂停：虾导没有启动新的生成步骤，请检查当前前置条件。"), "Episode automation paused: the director did not start a new generation step. Check the current prerequisites."),
)

_TASK_LABELS = {
    "角色身份图": "Character identity image",
    "角色身份": "Character identity",
    "身份图": "identity image",
    "本批 ": "Batch ",
    " 个任务": " tasks",
    "角色肖像": "Character portrait",
    "肖像": "portrait",
    "身份图生成": "Identity image generation",
    "视频生成": "Video generation",
    "成片合成": "Episode composition",
    "项目摄入": "Project import",
    "角色构建": "Character setup",
    "道具构建": "Prop setup",
    "剧集规划": "Episode planning",
    "身份规划": "Identity planning",
    "剧本生成": "Script writing",
    "解说改写": "Narration rewrite",
    "解说稿生成": "Narration writing",
    "导演说明": "Director notes",
    "场景规划": "Scene planning",
    "本集场景规划": "Episode scene planning",
    "本集道具规划": "Episode prop planning",
    "场景参考图": "Scene reference image",
    "道具参考图": "Prop reference image",
    "草图网格": "Sketch grid generation",
    "草图生成": "Sketch generation",
    "草图重生成": "Sketch regeneration",
    "草图网格重生成": "Sketch grid regeneration",
    "首帧生成": "First-frame generation",
    "身份检测": "Identity detection",
    "全局优化": "Global optimization",
    "渲染规划": "Render planning",
    "系统声线准备": "System voice setup",
    "音频生成": "Audio generation",
}


def english_chat_text(text: str) -> str:
    if os.environ.get("MANNA_ASSET_LANGUAGE", "").strip().lower() != "en":
        return text
    for pattern, template in _TEMPLATES:
        match = pattern.fullmatch(text)
        if match:
            values = match.groupdict()
            if values.get("state"):
                values["state"] = "was cancelled" if values["state"] == "已取消" else "failed"
            if values.get("label"):
                for source, target in _TASK_LABELS.items():
                    values["label"] = values["label"].replace(source, target)
            if values.get("summary"):
                values["summary"] = values["summary"].replace("已完成。", " completed.")
                for source, target in _TASK_LABELS.items():
                    values["summary"] = values["summary"].replace(source, target)
            return template.format(**values)
    return text
