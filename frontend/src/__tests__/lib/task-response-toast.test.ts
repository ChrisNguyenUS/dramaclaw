import i18next from "i18next";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import type { TFunction } from "i18next";
import { humanizeTaskError, taskResponseToastMessage } from "@/lib/api-errors";

// Mimics i18next: the catalog knows "known.code"; any other key returns its defaultValue.
const t = ((key: string, opts?: { defaultValue?: string }) =>
  key === "known.code" ? "Known copy" : (opts?.defaultValue ?? key)) as unknown as TFunction;

describe("taskResponseToastMessage", () => {
  beforeEach(() => i18next.changeLanguage("en"));
  afterEach(() => i18next.changeLanguage("zh"));

  it("translates untagged backend queue messages to English (Manna hook)", () => {
    expect(taskResponseToastMessage({ message: "第 2 集剧本生成任务已进入队列" }, t)).toBe(
      "Episode 2 script generation task queued",
    );
  });
  it("leaves unknown untagged text unchanged", () => {
    expect(taskResponseToastMessage({ message: "没人认识这句" }, t)).toBe("没人认识这句");
    expect(taskResponseToastMessage({}, t)).toBe("");
  });
  it("still prefers the i18n code when present", () => {
    expect(
      taskResponseToastMessage({ message: "风格已创建", message_code: "known.code" }, t),
    ).toBe("Known copy");
  });
  it("translates the default of a coded message whose catalog key is missing", () => {
    expect(
      taskResponseToastMessage({ message: "风格已创建", message_code: "missing.code" }, t),
    ).toBe("Style created");
  });
  it("translates backend error text that reaches humanizeTaskError unclassified", () => {
    expect(humanizeTaskError("视频生成超时", t)).toBe("Video generation timed out");
    expect(humanizeTaskError("没人认识这句", t)).toBe("没人认识这句");
    expect(humanizeTaskError("视频下载失败", t)).toBe("Video download failed");
  });
});

describe("taskResponseToastMessage with a Chinese UI", () => {
  it("passes the backend text through", () => {
    expect(taskResponseToastMessage({ message: "第 2 集剧本生成任务已进入队列" }, t)).toBe(
      "第 2 集剧本生成任务已进入队列",
    );
  });
});
