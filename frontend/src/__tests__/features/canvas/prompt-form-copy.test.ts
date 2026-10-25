import { describe, expect, it } from "vitest";

import {
  TRANSLATE_PROMPT_TITLE,
  UPSTREAM_CONTENT_PLACEHOLDER,
} from "@/features/canvas/nodes/shared/promptFormCopy";
import { enT } from "../../helpers/i18n-fixtures";

describe("shared prompt form copy", () => {
  it("translate title is the en locale wording", () => {
    expect(TRANSLATE_PROMPT_TITLE).toBe(enT("node.imageGen.translatePrompt"));
  });
  it("upstream placeholder is one string for both forms", () => {
    expect(UPSTREAM_CONTENT_PLACEHOLDER).toBe("Upstream content is wired in. Add more prompt detail…");
  });
});
