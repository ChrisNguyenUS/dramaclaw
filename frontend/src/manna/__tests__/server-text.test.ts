import i18next from "i18next";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import source from "../server-text.source.json";
import { SERVER_TEXT_EXACT, SERVER_TEXT_TEMPLATES } from "../server-text.data";
import { matchServerTemplate, translateServerText } from "../server-text";

const CJK = /[\u3000-\u303f\u3400-\u9fff\uff00-\uffef]/;

// The test setup boots i18next in zh, where translation is switched off. These tests are about English.
beforeAll(() => i18next.changeLanguage("en"));
afterAll(() => i18next.changeLanguage("zh"));

describe("translateServerText", () => {
  it("translates exact backend strings", () => {
    const [zh, en] = Object.entries(SERVER_TEXT_EXACT)[0];
    expect(translateServerText(zh)).toBe(en);
  });
  it("translates every exact entry to its English", () => {
    for (const [zh, en] of Object.entries(SERVER_TEXT_EXACT)) {
      expect(translateServerText(zh)).toBe(en);
    }
  });
  it("translates templated progress with parameters", () => {
    const sample = SERVER_TEXT_TEMPLATES[0];
    expect(translateServerText(sample.example.zh)).toBe(sample.example.en);
  });
  it("round-trips every template example (no template is shadowed by another)", () => {
    for (const t of SERVER_TEXT_TEMPLATES) {
      expect(translateServerText(t.example.zh), t.zh).toBe(t.example.en);
    }
  });
  it("re-inserts captured parameters in the English template", () => {
    expect(translateServerText("第 3 集 Beat 12 视频生成已入队")).toBe(
      "Episode 3 beat 12 video generation queued",
    );
    expect(translateServerText("Beat 4 合成失败: 磁盘已满")).toBe(
      "Beat 4 composition failed: 磁盘已满",
    );
  });
  it("prefers the most specific template over a generic one that also matches", () => {
    // Both "视频生成失败: {0}" and the generic "{0}生成失败: {1}" match this text.
    expect(translateServerText("视频生成失败: timeout")).toBe("Video generation failed: timeout");
    // "场景「{0}」360 全景生成任务已启动" is longer than "场景「{0}」{1} ..." variants.
    expect(translateServerText("场景「Cafe」360 全景生成任务已启动")).toBe(
      'Scene "Cafe" 360 panorama generation task started',
    );
    // The generic "第 {0} 集{1}规划已进入队列" appears earlier in the data than this one.
    expect(translateServerText("第 3 集身份规划已进入队列")).toBe(
      "Episode 3 identity planning queued",
    );
    // Concrete templates cover the fixed values that feed the generic "{0}生成失败: {1}".
    expect(translateServerText("网格生成失败: boom")).toBe("Grid generation failed: boom");
    // A wrapper ("错误: {0}") is not outranked by an inner pattern that starts with a field.
    expect(translateServerText("错误: 视频生成失败: timeout")).toBe(
      "Error: Video generation failed: timeout",
    );
  });
  it("keeps multi-line parameters intact", () => {
    expect(translateServerText("视频生成失败: a\nb")).toBe("Video generation failed: a\nb");
  });
  it("translates backend text captured inside a template field", () => {
    expect(translateServerText("Agent 规划失败: 解析规划结果...")).toBe(
      "Agent planning failed: Parsing the planning result...",
    );
  });
  it("ignores inherited object keys", () => {
    expect(translateServerText("constructor")).toBe("constructor");
    expect(translateServerText("toString")).toBe("toString");
  });
  it("falls back to the original text", () => {
    expect(translateServerText("完全未知的消息")).toBe("完全未知的消息");
    expect(translateServerText("")).toBe("");
  });
  it("covers every extracted backend string", () => {
    const missing = (source as { zh: string }[])
      .map((s) => s.zh)
      .filter((zh) => !(zh in SERVER_TEXT_EXACT) && !SERVER_TEXT_TEMPLATES.some((t) => t.zh === zh));
    expect(missing).toEqual([]);
  });
  it("keeps placeholders aligned between zh and en", () => {
    const fields = (s: string) => (s.match(/\{\d+\}/g) ?? []).sort().join(",");
    for (const t of SERVER_TEXT_TEMPLATES) expect(fields(t.en), t.zh).toBe(fields(t.zh));
  });
  it("has no template whose literal part is shorter than 2 characters", () => {
    for (const t of SERVER_TEXT_TEMPLATES) {
      expect(t.zh.replace(/\{\d+\}/g, "").trim().length, t.zh).toBeGreaterThanOrEqual(2);
    }
  });

  it("does not leak Chinese through f-string field values", () => {
    const cases: [string, string][] = [
      ["已生成 2/4 张草图", "Generated 2/4 sketches"],
      ["已生成 1/3 张网格", "Generated 1/3 grids"],
      ["生成 2x2 网格...", "Generating 2x2 grid..."],
      ["生成 mode_a 草图...", "Generating mode_a sketch..."],
      ["草图生成失败: boom", "Sketch generation failed: boom"],
      ["✅ 草图再生完成！更新了 3 个 beats", "Sketch regeneration complete: updated 3 beats"],
      ["✅ Render 再生完成！更新了 3 个 beats", "Render regeneration complete: updated 3 beats"],
      ["第 3 集场景规划已进入队列", "Episode 3 scene planning queued"],
      ["第 3 集道具规划已进入队列", "Episode 3 prop planning queued"],
      ["  场景: 咖啡馆 (3 派生场景)", "  Scene: 咖啡馆 (3 derived scenes)"],
      ["  道具[1]: 钥匙 [复用]", "  Prop [1]: 钥匙 [reused]"],
      ["  道具[1]: 钥匙 [本集复用]", "  Prop [1]: 钥匙 [reused in this episode]"],
      ["  道具[1]: 钥匙 [本集局部]", "  Prop [1]: 钥匙 [local to this episode]"],
      ["原文导入失败，准备重试(1/1): e", "Source import failed, retrying (1/1): e"],
      ["知识图谱构建失败，准备重试(1/1): e", "Knowledge graph build failed, retrying (1/1): e"],
      ["向量索引创建失败，准备重试(1/1): e", "Vector index creation failed, retrying (1/1): e"],
      [
        "⚠️ AI normalizer 返回空，回退到程序定位 + 本地规范化",
        "Warning: AI normalizer returned nothing. Falling back to rule-based locating and local normalization",
      ],
      [
        "⚠️ AI normalizer 失败 (boom)，回退到程序定位 + 本地规范化",
        "Warning: AI normalizer failed (boom). Falling back to rule-based locating and local normalization",
      ],
      [
        "开始生成视频 | 模式: 首尾帧模式 | 时长: 5s",
        "Starting video generation | mode: first/last frame mode | duration: 5s",
      ],
      [
        "开始生成视频 | 模式: FLF (首尾帧过渡) | 固定帧数: 81 (~5s)",
        "Starting video generation | mode: FLF (first/last frame transition) | fixed frames: 81 (~5s)",
      ],
      [
        "正在提交 Seedance 2.0 视频生成任务 (1图+0视频+0音频, model=m, 5s, audio=True)...",
        "Submitting Seedance 2.0 video generation task (1 images+0 videos+0 audio, model=m, 5s, audio=True)...",
      ],
      ["首帧已上传/复用 OSS URL", "First frame uploaded or reused OSS URL"],
      ["image参考已转换为 data URL", "image reference converted to a data URL"],
      ["音频参考已上传到媒体中转", "Audio reference uploaded to media relay"],
      ["生成调度区域（粗略精度）...", "Generating dispatch regions (coarse precision)..."],
      ["生成调度区域（超粗略精度）...", "Generating dispatch regions (very coarse precision)..."],
      ["场景头“X”缺少地点、时间。", 'Scene heading "X" is missing location, time.'],
      ["检测到重复章节序号 3：未命名章节。", "Duplicate chapter number 3 detected: Untitled chapter."],
      [
        "  拒绝归并 a → b：证据 1 条，且出现在场次人物栏",
        "  Rejected merge a -> b: 1 pieces of evidence, and listed in the scene cast",
      ],
    ];
    for (const [zh, en] of cases) {
      const out = translateServerText(zh);
      expect(out, zh).toBe(en);
    }
    // Only user-chosen names (scene "咖啡馆", prop "钥匙") may stay as they are.
    for (const [zh] of cases) {
      const out = translateServerText(zh).replace(/咖啡馆|钥匙/g, "");
      expect(CJK.test(out), zh).toBe(false);
    }
  });
  it("has no Chinese in any exact or template English", () => {
    for (const [zh, en] of Object.entries(SERVER_TEXT_EXACT)) expect(CJK.test(en), zh).toBe(false);
    for (const t of SERVER_TEXT_TEMPLATES) {
      expect(CJK.test(t.en), t.zh).toBe(false);
      expect(CJK.test(t.example.en), t.zh).toBe(false);
      // A template rendered with ASCII field values must be fully English.
      const ascii = t.zh.replace(/\{(\d+)\}/g, (_, i: string) => `x${i}`);
      expect(CJK.test(translateServerText(ascii)), t.zh).toBe(false);
    }
  });
  it("maps a template instantiated with awkward field values to its own English (no shadowing)", () => {
    const fill = (text: string, value: (i: number) => string) =>
      text.replace(/\{(\d+)\}/g, (_, i: string) => value(Number(i)));
    const valueSets: ((i: number) => string)[] = [
      (i) => `视频${i}`,
      (i) => `a: b${i}`,
      (i) => `${i}0`,
      (i) => `x${i}`,
    ];
    for (const t of SERVER_TEXT_TEMPLATES) {
      for (const value of valueSets) {
        const zh = fill(t.zh, value);
        expect(translateServerText(zh), zh).toBe(fill(t.en, value));
      }
    }
  });
  it("breaks ties between templates with the same literal by fewer fields", () => {
    expect(matchServerTemplate("  场景: 咖啡馆")?.zh).toBe("  场景: {0}");
  });
  it("translates the coded-message defaults that have no catalog entry", () => {
    const zhs = [
      "开始逐帧拉片...",
      "ffmpeg 抽取关键帧（目标 24 帧）...",
      "Vision 拉片解析 24 帧...",
      "模型输出无法解析，重试一次...",
      "切分镜图 12 张...",
      "切运镜参考片段...",
      "截取 BGM 参考片段...",
      "拉片结果写入完成",
    ];
    for (const zh of zhs) {
      const out = translateServerText(zh);
      expect(out, zh).not.toBe(zh);
      expect(CJK.test(out), zh).toBe(false);
    }
  });
  it("leaves the text alone when the UI language is Chinese", async () => {
    await i18next.changeLanguage("zh");
    try {
      expect(translateServerText("原文导入完成")).toBe("原文导入完成");
      expect(translateServerText("第 3 集剧本生成任务已进入队列")).toBe(
        "第 3 集剧本生成任务已进入队列",
      );
    } finally {
      await i18next.changeLanguage("en");
    }
    await i18next.changeLanguage("zh-CN");
    try {
      expect(translateServerText("原文导入完成")).toBe("原文导入完成");
    } finally {
      await i18next.changeLanguage("en");
    }
    expect(translateServerText("原文导入完成")).toBe("Source text imported");
  });
});
