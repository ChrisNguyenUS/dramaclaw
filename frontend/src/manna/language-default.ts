import { MANNA_BRAND } from "./brand";

// Upstream defaults the UI to Chinese (and its tests rely on that). Manna switches the running
// app to English once at startup, then leaves later language choices to the user.
export const MANNA_LANGUAGE_FLAG = "manna-language-initialized";

type FlagStorage = Pick<Storage, "getItem" | "setItem">;

export function applyMannaLanguageDefault(
  storage: FlagStorage,
  setLanguage: (language: string) => void,
): void {
  let alreadyApplied = false;
  try {
    alreadyApplied = storage.getItem(MANNA_LANGUAGE_FLAG) === "1";
  } catch {
    // Storage blocked (private mode, quota): fall through and still default to English.
  }
  if (alreadyApplied) return;
  setLanguage(MANNA_BRAND.defaultLanguage);
  try {
    storage.setItem(MANNA_LANGUAGE_FLAG, "1");
  } catch {
    // Without storage the switch simply repeats on the next load.
  }
}
