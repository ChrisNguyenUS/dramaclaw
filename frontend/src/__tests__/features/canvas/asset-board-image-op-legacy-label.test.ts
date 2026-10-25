import { beforeEach, describe, expect, it } from 'vitest';

import { switchAssetBoardImageOp } from '@/features/canvas/application/assetBoardImageOps';
import { CANVAS_NODE_TYPES } from '@/features/canvas/domain/canvasNodes';
import { useCanvasStore } from '@/stores/canvasStore';

function seed(data: Record<string, unknown>) {
  useCanvasStore.getState().setCanvasData(
    [
      {
        id: 'op-1',
        type: CANVAS_NODE_TYPES.imageGen,
        position: { x: 0, y: 0 },
        data: { imageOpKey: 'plotFourGrid', ...data },
      },
    ] as never,
    [],
  );
}

const displayName = () =>
  (useCanvasStore.getState().nodes.find((n) => n.id === 'op-1')?.data as Record<string, unknown>).displayName;

describe('switchAssetBoardImageOp display-name following', () => {
  beforeEach(() => seed({}));

  it('renames a node whose title is still the current English op label', () => {
    seed({ displayName: 'Plot Progression 2x2' });
    switchAssetBoardImageOp('op-1', 'multiCameraGrid');
    expect(displayName()).toBe('Multi-Camera 3x3');
  });

  it('renames a legacy node whose title is the Chinese op label persisted by earlier versions', () => {
    seed({ displayName: '剧情推演四宫格' }); // i18n-exempt: fixture persisted by earlier versions
    switchAssetBoardImageOp('op-1', 'multiCameraGrid');
    expect(displayName()).toBe('Multi-Camera 3x3');
  });

  it('keeps a title the user renamed', () => {
    seed({ displayName: 'My hero shot' });
    switchAssetBoardImageOp('op-1', 'multiCameraGrid');
    expect(displayName()).toBe('My hero shot');
  });
});
