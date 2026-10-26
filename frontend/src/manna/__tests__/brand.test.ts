import { describe, expect, it } from "vitest";

import { MANNA_BRAND, applyLocaleOverrides, rebrandText, rebrandTranslations } from "../brand";

describe("Manna brand", () => {
  it("replaces the upstream product name, including the combined Chinese form", () => {
    expect(rebrandText("Welcome to DramaClaw")).toBe("Welcome to Manna Studio");
    expect(rebrandText("DramaClaw 虾导 helps you")).toBe("Manna Studio helps you");
    expect(rebrandText("虾导 Agent")).toBe("Manna Studio Agent");
  });

  it("renames the upstream Xia-branded feature names to Manna names", () => {
    expect(rebrandText("Ask Xia Director")).toBe("Ask Manna Director");
    expect(rebrandText("Waiting for Xia Draw")).toBe("Waiting for Manna Draw");
    expect(rebrandText("Open XiaHua")).toBe("Open Manna Canvas");
    expect(rebrandText("XiaTang")).toBe("Manna Library");
    expect(rebrandText("XiaJi pipeline")).toBe("Manna Series pipeline");
    expect(rebrandText("Connect RelayClaw")).toBe("Connect RelayClaw");
  });

  it("rebrands nested translation resources without touching keys or non-strings", () => {
    const resource = {
      "app.title": "DramaClaw",
      nested: { tip: "Open DramaClaw settings", list: ["DramaClaw", 3] },
      count: 2,
    };
    expect(rebrandTranslations(resource)).toEqual({
      "app.title": "Manna Studio",
      nested: { tip: "Open Manna Studio settings", list: ["Manna Studio", 3] },
      count: 2,
    });
  });

  it("applies English overrides for upstream strings that still contain Chinese", () => {
    const resource = {
      settings: { storyboardGenDisableTextInImageDesc: 'appends "禁止添加描述文本".', other: "keep" },
      myBuddy: { debug: { accessoryFeedback: { redStar: "红星闪闪！" } } },
    };
    const out = applyLocaleOverrides(resource, "en");
    expect(out.settings.storyboardGenDisableTextInImageDesc).toBe(
      'When enabled, multi-variant grid prompt appends "no descriptive text in the image".',
    );
    expect(out.myBuddy.debug.accessoryFeedback.redStar).toBe("Red star shining!");
    expect(out.settings.other).toBe("keep");
    expect(applyLocaleOverrides(resource, "zh")).toEqual(resource);
  });

  it("adds missing English keys, creating intermediate objects, without touching other languages", () => {
    const resource = { common: { cancel: "Cancel" } };
    const out = applyLocaleOverrides(resource, "en") as Record<string, any>;
    expect(out.common.processing).toBe("Processing...");
    expect(out.common.cancel).toBe("Cancel");
    expect(out.nodeToolbar.nodeId).toBe("Node ID");
    expect(out.settings.modelConfig.featureModels.addChannel).toBe("Add channel");
    expect(resource).toEqual({ common: { cancel: "Cancel" } });
    expect(applyLocaleOverrides(resource, "vi")).toEqual(resource);
  });

  it("keeps the DramaClaw attribution and defaults the UI to English", () => {
    expect(MANNA_BRAND.poweredByLabel).toBe("Powered by DramaClaw");
    expect(MANNA_BRAND.defaultLanguage).toBe("en");
  });
});
