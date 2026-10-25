import { MANNA_BRAND } from "./brand";

// Small, faint attribution required by DramaClaw's ELv2 terms. Rendered in the bottom-left of
// the task status bar; clicks open the upstream project without toggling the task panel.
export function PoweredByDramaClaw() {
  return (
    <a
      href={MANNA_BRAND.poweredByUrl}
      target="_blank"
      rel="noreferrer"
      onClick={(event) => event.stopPropagation()}
      onKeyDown={(event) => event.stopPropagation()}
      className="ml-3 hidden shrink-0 text-[9px] text-muted-foreground/30 transition-colors hover:text-muted-foreground/70 sm:inline"
    >
      {MANNA_BRAND.poweredByLabel}
    </a>
  );
}
