import i18next from "i18next";
import { SERVER_TEXT_EXACT, SERVER_TEXT_TEMPLATES } from "./server-text.data";

// Backend progress/log/toast strings that upstream has not moved to i18n codes yet.
// Exact matches first, then templates whose {0},{1}... fields are captured and re-inserted.
//
// Call this where text is DISPLAYED, never before code that matches on the raw backend text
// (retry markers, error classifiers): those matchers still look for the Chinese originals.
//
// Chinese is a supported UI language upstream, so nothing is translated while it is active.

const PLACEHOLDER = /\{(\d+)\}/g;

interface CompiledTemplate {
  index: number;
  zh: string;
  en: string;
  pattern: RegExp;
  startsWithField: boolean;
  literal: number;
  fields: number;
}

const compile = (zh: string, en: string, index: number): CompiledTemplate => ({
  index,
  zh,
  en,
  startsWithField: zh.startsWith("{"),
  literal: zh.replace(PLACEHOLDER, "").length,
  fields: (zh.match(PLACEHOLDER) ?? []).length,
  pattern: new RegExp(
    "^" +
      zh.replace(/[.*+?^${}()|[\]\\]/g, "\\$&").replace(/\\\{(\d+)\\\}/g, "([\\s\\S]+?)") +
      "$",
  ),
});

// Order matters, because a broad template can swallow a more specific string:
//  1. Templates that open with literal text come before templates that open with a field,
//     so a wrapper ("错误: {0}") is not outranked by an inner pattern ("{0}生成失败: {1}").
//  2. Then the longest literal first, so "视频生成失败: {0}" beats "{0}生成失败: {1}".
//  3. Then fewer fields, so "  场景: {0}" beats "  场景: {0}{1}" (adjacent fields split badly).
//  4. Then source order.
const compiled = SERVER_TEXT_TEMPLATES.map((t, index) => compile(t.zh, t.en, index)).sort(
  (a, b) =>
    Number(a.startsWithField) - Number(b.startsWithField) ||
    b.literal - a.literal ||
    a.fields - b.fields ||
    a.index - b.index,
);

const hasOwn = (obj: object, key: string): boolean =>
  Object.prototype.hasOwnProperty.call(obj, key);

const isChineseUi = (): boolean => (i18next.language ?? "").toLowerCase().startsWith("zh");

/** The template that `text` would be translated with, if any (exposed for tests). */
export function matchServerTemplate(text: string): { zh: string; en: string } | null {
  for (const t of compiled) if (t.pattern.test(text)) return { zh: t.zh, en: t.en };
  return null;
}

export function translateServerText(text: string): string {
  if (!text || isChineseUi()) return text;
  return translate(text);
}

function translate(text: string): string {
  if (hasOwn(SERVER_TEXT_EXACT, text)) return SERVER_TEXT_EXACT[text];
  for (const { pattern, en } of compiled) {
    const match = pattern.exec(text);
    if (match) {
      // Captured fields may themselves be backend text (a fixed label, an error message);
      // translate them too. Captures are strictly shorter than the input, so this terminates.
      return en.replace(/\{(\d+)\}/g, (_, i: string) => translate(match[Number(i) + 1] ?? ""));
    }
  }
  return text;
}
