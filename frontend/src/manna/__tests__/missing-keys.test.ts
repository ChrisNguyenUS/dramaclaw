import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

import { applyLocaleOverrides } from "../brand";

// Permanent guard for "raw key shown in the UI": every literal translation key used in source
// must resolve to an English value, either from public/locales/en (after Manna's English
// overrides, which may add keys) or from an English defaultValue passed at the call site.

// vitest runs from the frontend package root (vitest.config.ts lives there).
const FRONTEND_ROOT = process.cwd();
const SRC_ROOT = path.join(FRONTEND_ROOT, "src");

const PLURAL_SUFFIXES = ["_zero", "_one", "_two", "_few", "_many", "_other", "_plural"];
const KEY_SHAPE = /^[A-Za-z][\w-]*(\.[\w-]+)+$/;
const CJK = /[぀-ヿ㐀-鿿가-힯]/;

function walk(dir: string, out: string[] = []): string[] {
  for (const name of readdirSync(dir)) {
    if (name === "node_modules" || name === "__tests__") continue;
    const full = path.join(dir, name);
    if (statSync(full).isDirectory()) {
      walk(full, out);
    } else if (/\.(ts|tsx)$/.test(name) && !/\.(test|d)\.(ts|tsx)$|\.d\.ts$/.test(name)) {
      out.push(full);
    }
  }
  return out;
}

/** Text of the call from just after the key literal to its closing paren (or tag end). */
function callTail(source: string, from: number): string {
  let depth = 0;
  let quote: string | null = null;
  const limit = Math.min(source.length, from + 2000);
  for (let i = from; i < limit; i += 1) {
    const ch = source[i];
    if (quote) {
      if (ch === "\\") i += 1;
      else if (ch === quote) quote = null;
      continue;
    }
    if (ch === '"' || ch === "'" || ch === "`") quote = ch;
    else if (ch === "(" || ch === "[" || ch === "{") depth += 1;
    else if (ch === ")" || ch === "]" || ch === "}") {
      if (depth === 0) return source.slice(from, i);
      depth -= 1;
    }
  }
  return source.slice(from, limit);
}

function hasEnglishDefault(tail: string): boolean {
  const literal =
    /defaultValue\s*:\s*(["'`])((?:\\.|(?!\1).)*)\1/s.exec(tail)?.[2] ??
    // t("key", "Default text") form
    /^\s*,\s*(["'`])((?:\\.|(?!\1).)*)\1\s*(?:,|$)/s.exec(tail)?.[2];
  return Boolean(literal && /[A-Za-z]/.test(literal) && !CJK.test(literal));
}

type Use = { key: string; where: string; english: boolean };

function collectUses(): Use[] {
  const uses: Use[] = [];
  const callPattern = /(?<![\w$])(?:[\w$]+\.)*t\(\s*(["'`])([^"'`$\\\s{}]+)\1/g;
  const tagPattern = /i18nKey=(["'])([^"'$\s{}]+)\1/g;
  for (const file of walk(SRC_ROOT)) {
    const source = readFileSync(file, "utf8");
    const rel = path.relative(FRONTEND_ROOT, file);
    for (const pattern of [callPattern, tagPattern]) {
      pattern.lastIndex = 0;
      for (let m = pattern.exec(source); m; m = pattern.exec(source)) {
        const key = m[2];
        if (!KEY_SHAPE.test(key)) continue;
        const line = source.slice(0, m.index).split("\n").length;
        const tail =
          pattern === callPattern
            ? callTail(source, m.index + m[0].length)
            : source.slice(m.index, source.indexOf(">", m.index));
        uses.push({
          key,
          where: `${rel}:${line}`,
          english: hasEnglishDefault(tail) || (pattern === tagPattern && /\bdefaults=/.test(tail)),
        });
      }
    }
  }
  return uses;
}

function indexResource(resource: unknown): { leaves: Set<string>; nodes: Set<string> } {
  const leaves = new Set<string>();
  const nodes = new Set<string>();
  const visit = (value: unknown, prefix: string) => {
    if (typeof value === "string") {
      // An empty string is a deliberate value (e.g. auth.stage.subtitleSuffix), not a miss.
      leaves.add(prefix);
    } else if (value && typeof value === "object") {
      if (prefix) nodes.add(prefix);
      for (const [k, v] of Object.entries(value as Record<string, unknown>)) {
        visit(v, prefix ? `${prefix}.${k}` : k);
      }
    }
  };
  visit(resource, "");
  return { leaves, nodes };
}

describe("English translation coverage", () => {
  const en = JSON.parse(
    readFileSync(path.join(FRONTEND_ROOT, "public/locales/en/translation.json"), "utf8"),
  );
  const { leaves, nodes } = indexResource(applyLocaleOverrides(en, "en"));
  const resolves = (key: string) =>
    leaves.has(key) || nodes.has(key) || PLURAL_SUFFIXES.some((s) => leaves.has(`${key}${s}`));

  it("finds a realistic number of literal keys (scanner sanity)", () => {
    expect(collectUses().length).toBeGreaterThan(1000);
  });

  it("has an English value, or an English defaultValue, for every literal t() key", () => {
    const missing = collectUses()
      .filter((use) => !use.english && !resolves(use.key))
      .map((use) => `${use.key}  (${use.where})`);
    expect([...new Set(missing)]).toEqual([]);
  });

  it("adds the Manna-owned English values for keys upstream never shipped", () => {
    for (const key of [
      "nodeToolbar.nodeId",
      "nodeToolbar.copyNodeId",
      "common.processing",
      "freezone.chat.canvasCommandsCancelled",
      "settings.modelConfig.featureModels.addChannel",
    ]) {
      expect(leaves.has(key), key).toBe(true);
    }
  });
});
