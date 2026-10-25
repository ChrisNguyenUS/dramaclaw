// SPDX-License-Identifier: Elastic-2.0
// Copyright (c) 2026 ClaymoreLab
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AssetBoardReferenceThumbMenu } from "@/features/canvas/ui/asset-board/AssetBoardReferenceThumbMenu";
import { PromptMentionEditor, type MentionCandidate } from "@/features/canvas/nodes/PromptMentionEditor";

const imageCandidate: MentionCandidate = {
  key: "A",
  name: "图片1",
  imageUrl: "https://example.com/a.png",
  index: 1,
};

describe("mention chips: English display, byte-identical protocol", () => {
  it("shows 'Image' on the chip but keeps dataset.name = 图片1", () => {
    const { container } = render(
      <PromptMentionEditor value="@图片1 " onChange={() => {}} candidates={[imageCandidate]} />,
    );
    const chip = container.querySelector(".mention-chip");
    expect(chip?.querySelector(".mention-chip-label")?.textContent).toBe("Image");
    expect(chip?.getAttribute("data-name")).toBe("图片1");
  });

  it("serializes the picked candidate as @图片N, not the English display text", () => {
    const onChange = vi.fn();
    const { container } = render(
      <PromptMentionEditor
        value="@图片1 "
        onChange={onChange}
        candidates={[imageCandidate, { key: "B", name: "图片2", imageUrl: "https://example.com/b.png", index: 2 }]}
      />,
    );
    const chip = container.querySelector(".mention-chip") as HTMLElement;
    fireEvent.doubleClick(chip);
    const row = screen.getByText("@图片2").closest("button") as HTMLElement;
    fireEvent.mouseDown(row);
    fireEvent.click(row);
    expect(onChange).toHaveBeenCalledWith("@图片2 ");
  });

  it("asset-board reference thumbnail shows English alt/aria while the stored label is unchanged", () => {
    const reference = { nodeId: "n1", label: "图片1", thumbnailUrl: "/static/a.png" };
    render(<AssetBoardReferenceThumbMenu reference={reference} onEdit={() => {}} onLocate={null} />);
    expect(screen.getByRole("button", { name: "Image 1" })).toBeTruthy();
    expect(screen.getByRole("img", { name: "Image 1" })).toBeTruthy();
    expect(reference.label).toBe("图片1");
  });
});
