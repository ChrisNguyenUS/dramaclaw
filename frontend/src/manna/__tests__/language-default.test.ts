import { describe, expect, it, vi } from "vitest";

import { applyMannaLanguageDefault, MANNA_LANGUAGE_FLAG } from "../language-default";

function memoryStorage(initial: Record<string, string> = {}) {
  const data = new Map(Object.entries(initial));
  return {
    getItem: (key: string) => data.get(key) ?? null,
    setItem: (key: string, value: string) => void data.set(key, value),
    data,
  };
}

describe("applyMannaLanguageDefault", () => {
  it("switches a first-time (or previously Chinese) app to English exactly once", () => {
    const storage = memoryStorage();
    const setLanguage = vi.fn();
    applyMannaLanguageDefault(storage, setLanguage);
    expect(setLanguage).toHaveBeenCalledWith("en");
    expect(storage.data.get(MANNA_LANGUAGE_FLAG)).toBe("1");
  });

  it("respects the user's later choice after the one-time switch", () => {
    const storage = memoryStorage({ [MANNA_LANGUAGE_FLAG]: "1" });
    const setLanguage = vi.fn();
    applyMannaLanguageDefault(storage, setLanguage);
    expect(setLanguage).not.toHaveBeenCalled();
  });

  it("still switches to English when storage is unavailable", () => {
    const setLanguage = vi.fn();
    const broken = {
      getItem: () => {
        throw new Error("blocked");
      },
      setItem: () => {
        throw new Error("blocked");
      },
    };
    applyMannaLanguageDefault(broken, setLanguage);
    expect(setLanguage).toHaveBeenCalledWith("en");
  });
});
