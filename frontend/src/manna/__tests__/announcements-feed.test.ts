import { readFileSync } from "node:fs";
import path from "node:path";
import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchAnnouncements } from "@/components/login/cinematic/announcements";

// The build-time wiring (compose build arg -> Dockerfile ENV -> VITE_LOGIN_ANNOUNCEMENTS_URL) is
// verified with `vite build` and a grep of dist; here we only check the Manna-owned feed file.
describe("Manna announcements feed", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("is valid for the upstream loader and empty, so the drawer shows its English empty state", async () => {
    const file = readFileSync(path.join(process.cwd(), "public/manna-announcements.json"), "utf8");
    vi.stubGlobal("fetch", vi.fn(async () => new Response(file, { status: 200 })));
    await expect(fetchAnnouncements()).resolves.toEqual([]);
  });
});
