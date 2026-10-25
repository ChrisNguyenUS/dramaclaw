import type { CanvasChatCommandApplyStep } from "@/features/freezone/canvasChatCommands";

const CANVAS_PROTOCOL_DETAIL_PATTERN =
  /\b(?:semanticOutputRole|planning_text|input_text|context_text|prompt_for|context_for|link_type|node_type|node_id|schema|envelopes\[\d+\]|commands\[\d+\])\b/;

function rawText(errors: string[] | undefined, commandResults: Array<Partial<CanvasChatCommandApplyStep>> | undefined): string {
  return [
    ...(errors ?? []),
    ...(commandResults ?? []).map((step) => step.error).filter((item): item is string => typeof item === "string"),
  ].join("\n");
}

function isUnavailableModelError(text: string): boolean {
  return /field model value|not a valid option.*model|模型|model/i.test(text) && /not a valid option|不可用|invalid/i.test(text); // i18n-exempt: matches Chinese input
}

export function canvasCommandUserMessageFromResult(
  errors: string[] | undefined,
  commandResults: Array<Partial<CanvasChatCommandApplyStep>> | undefined,
): string {
  const text = rawText(errors, commandResults);
  if (!text.trim()) return "The canvas action did not complete. I will try another way.";
  if (/Recipe\s*文本生成超时|Recipe text generation.*(?:timed out|timeout)|Request timed out/i.test(text)) { // i18n-exempt -- backend error matching
    return "Recipe 文本生成超时：模型在规定时间内未返回结果，请稍后重试。本轮未继续执行下游节点。"; // i18n-exempt -- transport fallback
  }
  if (/cancel|timed out|取消|超时/i.test(text)) return "The canvas action was cancelled and was not applied to the canvas."; // i18n-exempt: matches Chinese input
  // Switching models changes the output and billing, so the user picks it; the agent must not swap and rerun.
  if (isUnavailableModelError(text)) {
    return "The selected generation model is unavailable. Pick one of the models this canvas supports and I will update it with your choice.";
  }
  if (/planning_text|input_text|semanticOutputRole|prompt_for/.test(text)) {
    return "This text must first be connected to the image node as a generation prompt. I will use a valid prompt source.";
  }
  if (/link_type .*not valid|not valid for .*->|cannot connect|不支持.*连接/i.test(text)) { // i18n-exempt: matches Chinese input
    return "These two nodes cannot be connected that way. I will use a link type the canvas supports.";
  }
  if (/(source node not found|target node not found|node not found|节点.*不存在|没找到.*节点)/i.test(text)) { // i18n-exempt: matches Chinese input
    return "I could not find the node to act on. Select a node first, or tell me which one.";
  }
  if (/fields are not editable|not editable|不能编辑/i.test(text)) { // i18n-exempt: matches Chinese input
    return "Some content of this node cannot be edited directly. I will use an editing method it supports.";
  }
  if (CANVAS_PROTOCOL_DETAIL_PATTERN.test(text)) {
    return "The canvas action did not complete. I will try another way that follows the current canvas rules.";
  }
  return text.length > 140 ? `${text.slice(0, 140)}...` : text;
}

export function canvasCommandAgentHintFromResult(
  errors: string[] | undefined,
  commandResults: Array<Partial<CanvasChatCommandApplyStep>> | undefined,
): string {
  const userMessage = canvasCommandUserMessageFromResult(errors, commandResults);
  const nextStep = isUnavailableModelError(rawText(errors, commandResults))
    ? "Do not change the node's model or rerun the generation yourself; list the models this canvas supports and ask the user which one to use, then wait for their choice."
    : "The raw errors and command_results remain available for diagnosis; fix the command and retry only when it is safe.";
  return [
    "Do not mention raw canvas protocol details to the user, including semanticOutputRole, planning_text, input_text, prompt_for, context_for, schema names, command paths, or node ids unless the user explicitly asks for implementation details.",
    `Use this user-facing summary if you need to explain the failure: ${userMessage}`,
    nextStep,
  ].join(" ");
}
