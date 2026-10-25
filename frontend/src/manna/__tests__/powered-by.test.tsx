import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { PoweredByDramaClaw } from "../powered-by";

describe("PoweredByDramaClaw", () => {
  it("shows the small DramaClaw attribution linking to the upstream project", () => {
    render(<PoweredByDramaClaw />);
    const link = screen.getByRole("link", { name: "Powered by DramaClaw" });
    expect(link.getAttribute("href")).toBe("https://github.com/dramaclaw/dramaclaw");
    expect(link.getAttribute("target")).toBe("_blank");
  });

  it("does not toggle the task panel it sits in when clicked", () => {
    const onParentClick = vi.fn();
    render(
      <div onClick={onParentClick}>
        <PoweredByDramaClaw />
      </div>,
    );
    fireEvent.click(screen.getByRole("link", { name: "Powered by DramaClaw" }));
    expect(onParentClick).not.toHaveBeenCalled();
  });
});
