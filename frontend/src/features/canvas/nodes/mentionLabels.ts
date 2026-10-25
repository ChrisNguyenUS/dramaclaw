// SPDX-License-Identifier: Elastic-2.0
// Display-only localization of @mention protocol names. The protocol names
// (图片N / 图N / 视频N / 音频N, serialized as @图片N) stay untouched everywhere
// they are stored, parsed or sent to the backend; only what the user *sees* is mapped.

// i18n-exempt-start
const MENTION_KIND_DISPLAY: Record<string, string> = {
  图片: 'Image',
  图: 'Image',
  视频: 'Video',
  音频: 'Audio',
  文本: 'Text',
};
const MENTION_NAME_PATTERN = /^(图片|图|视频|音频|文本)(\d*)$/;
// i18n-exempt-end

/** `图片1` -> `Image 1`, `音频` -> `Audio`. Anything that is not a protocol name is returned as is. */
export function localizeMentionLabel(name: string): string {
  const match = MENTION_NAME_PATTERN.exec(name);
  if (!match) return name;
  const kind = MENTION_KIND_DISPLAY[match[1]];
  return match[2] ? `${kind} ${match[2]}` : kind;
}
