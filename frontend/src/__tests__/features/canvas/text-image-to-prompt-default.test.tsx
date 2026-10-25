// SPDX-License-Identifier: Elastic-2.0
// Copyright (c) 2026 ClaymoreLab
import { render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { IMAGE_TO_PROMPT_DEFAULT_CONTENT } from "@/features/canvas/application/textNodeModes";
import { CANVAS_NODE_TYPES } from "@/features/canvas/domain/canvasNodes";
import { TextAnnotationNode } from "@/features/canvas/nodes/TextAnnotationNode";
import { useCanvasStore } from "@/stores/canvasStore";

vi.mock("@xyflow/react", async () => {
  const actual = await vi.importActual<typeof import("@xyflow/react")>(
    "@xyflow/react",
  );
  return {
    ...actual,
    Handle: () => <div />,
    useReactFlow: () => ({
      getNode: () => null,
      getInternalNode: () => null,
      setCenter: vi.fn(),
    }),
  };
});

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

vi.mock("@/features/canvas/ui/NodeHeader", () => ({
  NODE_HEADER_FLOATING_POSITION_CLASS: "",
  NodeHeader: () => <div />,
}));

vi.mock("@/features/canvas/ui/NodeResizeHandle", () => ({
  NodeResizeHandle: () => <div />,
}));

vi.mock(
  "@/features/canvas/ui/ProviderModelPicker",
  async (importOriginal) => {
    const actual = await importOriginal<
      typeof import("@/features/canvas/ui/ProviderModelPicker")
    >();
    return {
      ...actual,
      ProviderModelPicker: () => <div />,
    };
  },
);

vi.mock("@/lib/queries/generation-credit-cost", () => ({
  useGenerationCreditCost: () => ({ data: null, error: null }),
}));

vi.mock("@/lib/model-task-access", () => ({
  useModelTaskAccess: () => ({ blocked: false, denialReason: null, message: null }),
}));

vi.mock("@/features/canvas/application/useNodeGenerationTaskState", () => ({
  useNodeGenerationTaskState: () => ({ isGenerating: false }),
}));

// Persisted by earlier versions (Chinese default instruction).
const LEGACY_ZH_DEFAULT =
  "根据图片生成结构化中文提示词，包括主体描述、环境、光影、镜头语言、风格关键词。"; // i18n-exempt: fixture persisted by earlier versions

function renderImageToPrompt(instruction: string) {
  useCanvasStore.getState().setCanvasData(
    [
      {
        id: "text-1",
        type: CANVAS_NODE_TYPES.textAnnotation,
        position: { x: 0, y: 0 },
        data: { content: "", mode: "imageToPrompt", instruction, model: "test-model", isGenerating: false },
      },
    ],
    [],
  );
  return render(
    <TextAnnotationNode
      id="text-1"
      type={CANVAS_NODE_TYPES.textAnnotation}
      data={{ content: "", mode: "imageToPrompt", instruction, model: "test-model", isGenerating: false }}
      selected
      dragging={false}
      draggable
      selectable
      deletable
      zIndex={0}
      isConnectable
      positionAbsoluteX={0}
      positionAbsoluteY={0}
    />,
  );
}

describe("image-to-prompt default instruction", () => {
  it("shows an empty box (placeholder) for the current English default", () => {
    const { container } = renderImageToPrompt(IMAGE_TO_PROMPT_DEFAULT_CONTENT);
    const textarea = container.querySelector("textarea");
    expect(textarea).not.toBeNull();
    expect((textarea as HTMLTextAreaElement).value).toBe("");
  });

  it("also treats the legacy Chinese default persisted by earlier versions as the placeholder", () => {
    const { container } = renderImageToPrompt(LEGACY_ZH_DEFAULT);
    const textarea = container.querySelector("textarea");
    expect(textarea).not.toBeNull();
    expect((textarea as HTMLTextAreaElement).value).toBe("");
  });

  it("keeps a user-written instruction", () => {
    const { container } = renderImageToPrompt("Focus on the costume.");
    expect((container.querySelector("textarea") as HTMLTextAreaElement).value).toBe("Focus on the costume.");
  });
});
