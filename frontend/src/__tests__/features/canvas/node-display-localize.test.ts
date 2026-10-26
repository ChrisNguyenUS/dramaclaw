// SPDX-License-Identifier: Elastic-2.0
// Copyright (c) 2026 ClaymoreLab
import type { TFunction } from 'i18next';
import { describe, expect, it } from 'vitest';

import en from '../../../../public/locales/en/translation.json';
import {
  CANVAS_NODE_TYPES,
  type CanvasNodeData,
  type CanvasNodeType,
} from '@/features/canvas/domain/canvasNodes';
import {
  getDefaultNodeDisplayName,
  localizeNodeDisplayName,
  withAutoTitleIndex,
} from '@/features/canvas/domain/nodeDisplay';

type Seed = Partial<CanvasNodeData> & { autoTitleIndex?: number };

/** New node data as the canvas store would create it (auto title index stored). */
const seeded = (
  type: CanvasNodeType,
  existing: Array<{ type?: string | null; data?: unknown }> = [],
) => withAutoTitleIndex<Seed>(type, {}, existing);

/** Minimal t() backed by the shipped English resource. */
const tEn = ((key: string) => {
  const value = key
    .split('.')
    .reduce<unknown>((node, part) => (node as Record<string, unknown> | undefined)?.[part], en);
  return typeof value === 'string' ? value : key;
}) as unknown as TFunction;

describe('localizeNodeDisplayName: indexed default names', () => {
  it('renders the indexed default in English instead of the stored Chinese name', () => {
    const data = seeded(CANVAS_NODE_TYPES.imageGen);
    // Persisted value is unchanged: Chinese base + index.
    expect(data.displayName).toBe('图片节点1');
    expect(localizeNodeDisplayName(CANVAS_NODE_TYPES.imageGen, data, tEn)).toBe('Image node 1');
  });

  it('keeps the index when it is not 1, and covers other node types', () => {
    const video = seeded(CANVAS_NODE_TYPES.video, [
      { type: CANVAS_NODE_TYPES.video, data: { autoTitleIndex: 2 } },
    ]);
    expect(video.displayName).toBe('视频3');
    expect(localizeNodeDisplayName(CANVAS_NODE_TYPES.video, video, tEn)).toBe('Video 3');
    const world = seeded(CANVAS_NODE_TYPES.threeDWorld);
    expect(localizeNodeDisplayName(CANVAS_NODE_TYPES.threeDWorld, world, tEn)).toBe('3D world 1');
  });

  it('passes a user-renamed title through unchanged', () => {
    const data = { displayName: 'My hero shot', autoTitleIndex: 1 };
    expect(localizeNodeDisplayName(CANVAS_NODE_TYPES.imageGen, data, tEn)).toBe('My hero shot');
    // A user title that merely looks like another type's default is left alone.
    const lookalike = { displayName: '视频1', autoTitleIndex: 1 };
    expect(localizeNodeDisplayName(CANVAS_NODE_TYPES.imageGen, lookalike, tEn)).toBe('视频1');
  });

  it('still localizes legacy un-indexed default names', () => {
    expect(
      localizeNodeDisplayName(CANVAS_NODE_TYPES.imageGen, { displayName: '图片节点' }, tEn),
    ).toBe('Image node');
    expect(localizeNodeDisplayName(CANVAS_NODE_TYPES.imageGen, {}, tEn)).toBe('Image node');
  });

  it('does not change what is persisted: the stored default stays the Chinese canonical name', () => {
    const data = seeded(CANVAS_NODE_TYPES.textAnnotation);
    expect(data.autoTitleIndex).toBe(1);
    expect(data.displayName).toBe(getDefaultNodeDisplayName(CANVAS_NODE_TYPES.textAnnotation, data));
    expect(data.displayName).toBe('文本1');
  });
});
