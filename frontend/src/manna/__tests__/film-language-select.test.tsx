import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { FILM_LANGUAGE_OPTIONS, FilmLanguageSelect } from "@/manna/film-language-select";

describe("FilmLanguageSelect", () => {
  it("shows the label and options, and reports the picked language", async () => {
    const onChange = vi.fn();
    render(<FilmLanguageSelect value="en" onChange={onChange} />);
    expect(screen.getByText("Film language")).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "English" })).toBeChecked();
    await userEvent.click(screen.getByRole("radio", { name: "Vietnamese" }));
    expect(onChange).toHaveBeenCalledWith("vi");
  });

  it("treats a missing value as English (projects created before P2b)", () => {
    render(<FilmLanguageSelect value={undefined} onChange={() => {}} />);
    expect(screen.getByRole("radio", { name: "English" })).toBeChecked();
    expect(screen.getByRole("radio", { name: "Vietnamese" })).not.toBeChecked();
  });

  it("can be disabled", () => {
    render(<FilmLanguageSelect value="vi" onChange={() => {}} disabled />);
    expect(screen.getByRole("radio", { name: "Vietnamese" })).toBeDisabled();
  });

  it("exposes exactly English and Vietnamese", () => {
    expect(FILM_LANGUAGE_OPTIONS.map((o) => o.value)).toEqual(["en", "vi"]);
  });
});
