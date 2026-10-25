import { describe, expect, it } from "vitest";

import { NODE_ACTION_TIMEOUT_MESSAGE } from "@/features/freezone/canvasChatCommands";
import {
  canvasCommandAgentHintFromResult,
  canvasCommandUserMessageFromResult,
} from "@/features/freezone/canvasCommandUserMessages";

describe("canvasCommandUserMessageFromResult", () => {
  it("returns one explicit message for duplicate Recipe text timeouts", () => {
    expect(canvasCommandUserMessageFromResult(
      [
        "Recipe 文本生成超时：模型在规定时间内未返回结果，请稍后重试。",
        "Recipe 文本生成超时：模型在规定时间内未返回结果，请稍后重试。",
      ],
      [
        {
          error: "Recipe 文本生成超时：模型在规定时间内未返回结果，请稍后重试。",
        },
      ],
    )).toBe(
      "Recipe text generation timed out: the model did not respond in time. Try again later. Downstream nodes were not run.",
    );
  });

  it("does not misreport a Recipe timeout as user cancellation", () => {
    expect(canvasCommandUserMessageFromResult(
      ["Request timed out."],
      [],
    )).toContain("Recipe text generation timed out");
  });
});

describe("node-action producer strings", () => {
  it("maps the AudioNode 'Audio node not found' error to the node-not-found message", () => {
    expect(canvasCommandUserMessageFromResult(["Audio node not found"], [])).toContain(
      "could not find the node",
    );
  });
});

describe("timeout handling", () => {
  const CANCEL_MESSAGE = "The canvas action was cancelled and was not applied to the canvas.";

  it("maps the frontend's own node action timeout to the cancel message", () => {
    expect(NODE_ACTION_TIMEOUT_MESSAGE).toBe("Node action timed out");
    expect(canvasCommandUserMessageFromResult([NODE_ACTION_TIMEOUT_MESSAGE], [])).toBe(CANCEL_MESSAGE);
    expect(canvasCommandUserMessageFromResult([], [{ error: NODE_ACTION_TIMEOUT_MESSAGE }])).toBe(CANCEL_MESSAGE);
  });

  it("keeps matching the Chinese timeout and cancel markers", () => {
    expect(canvasCommandUserMessageFromResult(["节点动作执行超时"], [])).toBe(CANCEL_MESSAGE);
    expect(canvasCommandUserMessageFromResult(["用户取消"], [])).toBe(CANCEL_MESSAGE);
  });

  it("does not report an unrelated provider timeout as a cancellation", () => {
    expect(canvasCommandUserMessageFromResult(["provider request timed out after 600s"], []))
      .not.toBe(CANCEL_MESSAGE);
    expect(canvasCommandUserMessageFromResult(["upstream provider call timed out after 600s"], []))
      .toBe("upstream provider call timed out after 600s");
  });
});

describe("unavailable model failures", () => {
  const errors = ["field model value 'LingShan-G2' is not a valid option"];

  it("asks the user to pick a model instead of promising to switch it", () => {
    const message = canvasCommandUserMessageFromResult(errors, []);
    expect(message).toContain("generation model is unavailable");
    expect(message).toContain("Pick one");
    expect(message).not.toContain("I will switch");
  });

  it("tells the agent not to change the model or rerun without the user's choice", () => {
    const hint = canvasCommandAgentHintFromResult(errors, []);
    expect(hint).toMatch(/do not change the node's model/i);
    expect(hint).toMatch(/ask the user/i);
    expect(hint).not.toMatch(/fix the command and retry/i);
  });

  it("keeps the generic retry hint for other failures", () => {
    const hint = canvasCommandAgentHintFromResult(["source node not found: n1"], []);
    expect(hint).toMatch(/fix the command and retry only when it is safe/i);
  });
});
