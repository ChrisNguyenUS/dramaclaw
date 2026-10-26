import { render, screen } from "@testing-library/react";
import i18next from "i18next";
import { afterAll, beforeAll, describe, expect, it } from "vitest";

import { SkillStudioStatusCard } from "@/features/superchat/superchat-panel";

// The test setup boots i18next in zh, where server-text translation is switched off.
beforeAll(() => i18next.changeLanguage("en"));
afterAll(() => i18next.changeLanguage("zh"));

describe("Skill Studio status frame", () => {
  it("shows the backend's untagged Chinese status in English", () => {
    render(
      <SkillStudioStatusCard
        event={{ type: "skill_studio.status", message: "正在整理 Skill 方向..." }} // i18n-exempt: backend status text fed as input
      />,
    );
    expect(screen.getByText("Working out the Skill direction...")).toBeInTheDocument();
  });

  it("falls back to the English default when the message is empty", () => {
    render(<SkillStudioStatusCard event={{ type: "skill_studio.status", message: "" }} />);
    expect(screen.getByText("Entering Skill Studio...")).toBeInTheDocument();
  });
});
