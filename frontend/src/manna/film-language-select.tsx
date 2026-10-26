// Manna Studio: per-project film language picker (P2b). Manna-owned; upstream screens only
// render it at ledgered hook points (create-project dialog, project settings).

export type FilmLanguage = "en" | "vi";

export const FILM_LANGUAGE_OPTIONS: { value: FilmLanguage; label: string }[] = [
  { value: "en", label: "English" },
  { value: "vi", label: "Vietnamese" },
];

type Props = {
  value: FilmLanguage | undefined;
  onChange: (value: FilmLanguage) => void;
  disabled?: boolean;
};

export function FilmLanguageSelect({ value, onChange, disabled = false }: Props) {
  const current = value ?? "en";
  return (
    <fieldset className="flex flex-col gap-1.5" disabled={disabled}>
      <legend className="text-sm font-medium text-foreground">Film language</legend>
      <div role="radiogroup" aria-label="Film language" className="inline-flex w-fit rounded-md border border-border p-0.5">
        {FILM_LANGUAGE_OPTIONS.map((option) => {
          const checked = option.value === current;
          return (
            <label
              key={option.value}
              className={`cursor-pointer rounded px-3 py-1 text-sm transition-colors ${
                checked ? "bg-muted text-foreground" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <input
                type="radio"
                name="manna-film-language"
                className="sr-only"
                value={option.value}
                checked={checked}
                disabled={disabled}
                onChange={() => onChange(option.value)}
              />
              {option.label}
            </label>
          );
        })}
      </div>
      <p className="text-xs text-muted-foreground">
        Changes dialogue, captions, on-screen text and character names. Everything else stays English.
      </p>
    </fieldset>
  );
}
