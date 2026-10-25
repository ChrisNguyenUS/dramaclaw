import { describe, expect, it } from "vitest";
import type { TFunction } from "i18next";
import { taskResponseToastMessage } from "@/lib/api-errors";

const t = ((key: string, opts?: { defaultValue?: string }) =>
  key === "known.code" ? "Known copy" : (opts?.defaultValue ?? key)) as unknown as TFunction;

describe("taskResponseToastMessage", () => {
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
});
