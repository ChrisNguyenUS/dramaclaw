// Manna Studio brand settings. Manna-owned file: upstream files only import from here at
// hook points listed in Manna Studio docs/upstream-patches.md.

export const MANNA_BRAND = {
  productName: "Manna Studio",
  wordmarkSrc: "/brand/manna-wordmark.svg",
  faviconSrc: "/brand/manna-mark.svg",
  // ELv2 attribution requested by DramaClaw: keep a small "Powered by DramaClaw" in the UI.
  poweredByLabel: "Powered by DramaClaw",
  poweredByUrl: "https://github.com/dramaclaw/dramaclaw",
  defaultLanguage: "en",
} as const;

// Name replacements applied to every loaded translation file. Order matters: longest first so
// the combined "DramaClaw 虾导" form collapses to one name instead of two. RelayClaw (a real
// third-party service) and SuperTale (the upstream copyright holder) are deliberately kept.
const NAME_REPLACEMENTS: [RegExp, string][] = [
  [/DramaClaw\s*虾导/g, MANNA_BRAND.productName], // i18n-exempt: matches upstream Chinese name
  [/DramaClaw/g, MANNA_BRAND.productName],
  [/虾导/g, MANNA_BRAND.productName], // i18n-exempt: matches upstream Chinese name
  [/Xia Director|XiaDao/g, "Manna Director"],
  [/Xia Draw/g, "Manna Draw"],
  [/XiaHua/g, "Manna Canvas"],
  [/XiaTang/g, "Manna Library"],
  [/XiaLiao/g, "Manna Chat"],
  [/XiaJing/g, "Manna World"],
  [/XiaGe/g, "Manna Music"],
  [/XiaJi/g, "Manna Series"],
];

export function rebrandText(text: string): string {
  return NAME_REPLACEMENTS.reduce((out, [pattern, name]) => out.replace(pattern, name), text);
}

// Per-language overrides for upstream translation values that are still not fully English.
// Keys are dot paths into the translation resource.
const LOCALE_OVERRIDES: Record<string, Record<string, string>> = {
  en: {
    "settings.storyboardGenKeepStyleConsistentDesc":
      'When enabled, multi-variant grid prompt appends "keep the image style consistent with the reference".',
    "settings.storyboardGenDisableTextInImageDesc":
      'When enabled, multi-variant grid prompt appends "no descriptive text in the image".',
    "settings.ignoreAtTagWhenCopyingAndGeneratingDesc":
      'When enabled, copied text and embedded grid metadata remove tags like "@Image1"; generation requests only remove "@" and keep "Image1".',
    "settings.storyboardGenAutoInferEmptyFrameDesc":
      'When enabled, empty grid cells automatically append "infer from the previous content" during generation prompt construction.',
    "myBuddy.debug.accessoryFeedback.redStar": "Red star shining!",
    // Keys upstream calls with t() but ships in no locale (the UI would show the raw key).
    "nodeToolbar.nodeId": "Node ID",
    "nodeToolbar.copyNodeId": "Copy node ID",
    "common.processing": "Processing...",
    "freezone.chat.canvasCommandsCancelled": "Canvas commands cancelled",
    "settings.modelConfig.featureModels.addChannel": "Add channel",
  },
};

// Overrides replace existing strings and also ADD keys the upstream locale files lack,
// creating intermediate objects as needed. An intermediate that is already a string is left alone.
export function applyLocaleOverrides<T>(resource: T, language: string): T {
  const overrides = LOCALE_OVERRIDES[language];
  if (!overrides || !resource || typeof resource !== "object") return resource;
  const out = structuredClone(resource) as Record<string, unknown>;
  for (const [path, value] of Object.entries(overrides)) {
    const keys = path.split(".");
    let node: Record<string, unknown> | undefined = out;
    for (const key of keys.slice(0, -1)) {
      if (!node) break;
      if (node[key] === undefined) node[key] = {};
      const next: unknown = node[key];
      node = next && typeof next === "object" ? (next as Record<string, unknown>) : undefined;
    }
    const leaf = keys[keys.length - 1];
    if (node && (node[leaf] === undefined || typeof node[leaf] === "string")) node[leaf] = value;
  }
  return out as T;
}

// Walks a translation resource (nested objects/arrays of strings) and rebrands every string.
export function rebrandTranslations<T>(value: T): T {
  if (typeof value === "string") return rebrandText(value) as T;
  if (Array.isArray(value)) return value.map((item) => rebrandTranslations(item)) as T;
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>).map(([key, item]) => [
        key,
        rebrandTranslations(item),
      ]),
    ) as T;
  }
  return value;
}
