import { SERVER_TEXT_EXACT, SERVER_TEXT_TEMPLATES } from "./server-text.data";

// Backend progress/log/toast strings that upstream has not moved to i18n codes yet.
// Exact matches first, then templates whose {0},{1}... fields are captured and re-inserted.
//
// Call this where text is DISPLAYED, never before code that matches on the raw backend text
// (retry markers, error classifiers): those matchers still look for the Chinese originals.

const PLACEHOLDER = /\{(\d+)\}/g;

const literalLength = (zh: string): number => zh.replace(PLACEHOLDER, "").length;

// Longest literal first so a specific template ("视频生成失败: {0}") wins over a generic one
// ("{0}生成失败: {1}") that also matches. Ties keep source order.
const compiled = SERVER_TEXT_TEMPLATES.map((t, index) => ({
  index,
  en: t.en,
  literal: literalLength(t.zh),
  pattern: new RegExp(
    "^" +
      t.zh
        .replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
        .replace(/\\\{(\d+)\\\}/g, "([\\s\\S]+?)") +
      "$",
  ),
}))
  .sort((a, b) => b.literal - a.literal || a.index - b.index);

const hasOwn = (obj: object, key: string): boolean =>
  Object.prototype.hasOwnProperty.call(obj, key);

export function translateServerText(text: string): string {
  if (!text) return text;
  if (hasOwn(SERVER_TEXT_EXACT, text)) return SERVER_TEXT_EXACT[text];
  for (const { pattern, en } of compiled) {
    const match = pattern.exec(text);
    if (match) {
      // Captured fields may themselves be backend text (e.g. an error message); translate
      // them too. Captures are strictly shorter than the input, so this terminates.
      return en.replace(/\{(\d+)\}/g, (_, i: string) => {
        const field = match[Number(i) + 1] ?? "";
        return field === text ? field : translateServerText(field);
      });
    }
  }
  return text;
}
