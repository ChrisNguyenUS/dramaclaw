import { describe, expect, it } from "vitest";
import source from "../server-text.source.json";
import { SERVER_TEXT_EXACT, SERVER_TEXT_TEMPLATES } from "../server-text.data";
import { translateServerText } from "../server-text";

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
    // The generic one still handles other prefixes.
    expect(translateServerText("音频生成失败: boom")).toBe("音频 generation failed: boom");
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
});
