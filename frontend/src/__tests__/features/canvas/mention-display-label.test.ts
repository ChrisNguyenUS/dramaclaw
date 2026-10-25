// SPDX-License-Identifier: Elastic-2.0
// Copyright (c) 2026 ClaymoreLab
import { describe, expect, it } from "vitest";

import { localizeMentionLabel } from "@/features/canvas/nodes/mentionLabels";
import { mentionDisplayLabel } from "@/features/canvas/nodes/PromptMentionEditor";

// Display only: the protocol names (图片N / 视频N / 音频N) are what reach the backend.
describe("mentionDisplayLabel", () => {
  it("strips the trailing number and shows the English kind for image mentions", () => {
    expect(mentionDisplayLabel("图片1")).toBe("Image");
    expect(mentionDisplayLabel("图片2")).toBe("Image");
    expect(mentionDisplayLabel("图片10")).toBe("Image");
    expect(mentionDisplayLabel("图1")).toBe("Image");
  });

  it("does the same for video and audio mentions", () => {
    expect(mentionDisplayLabel("视频1")).toBe("Video");
    expect(mentionDisplayLabel("音频1")).toBe("Audio");
    expect(mentionDisplayLabel("音频3")).toBe("Audio");
    expect(mentionDisplayLabel("文本2")).toBe("Text");
  });

  it("localizes names without a trailing number too", () => {
    expect(mentionDisplayLabel("图片")).toBe("Image");
    expect(mentionDisplayLabel("音频")).toBe("Audio");
  });

  it("leaves names that are not a protocol token unchanged", () => {
    expect(mentionDisplayLabel("图腾")).toBe("图腾");
    expect(mentionDisplayLabel("Hero shot 2")).toBe("Hero shot");
  });

  it("falls back to the original name when stripping would empty it", () => {
    expect(mentionDisplayLabel("123")).toBe("123");
    expect(mentionDisplayLabel("")).toBe("");
  });
});

describe("localizeMentionLabel (keeps the number)", () => {
  it("maps protocol labels to English display text", () => {
    expect(localizeMentionLabel("图片1")).toBe("Image 1");
    expect(localizeMentionLabel("图2")).toBe("Image 2");
    expect(localizeMentionLabel("视频3")).toBe("Video 3");
    expect(localizeMentionLabel("音频1")).toBe("Audio 1");
  });
  it("does not touch other text", () => {
    expect(localizeMentionLabel("图腾1")).toBe("图腾1");
    expect(localizeMentionLabel("Reference")).toBe("Reference");
  });
});
