import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const post = vi.fn();
vi.mock("@/lib/api", () => ({
  api: {
    post: (...args: unknown[]) => {
      post(...args);
      return { json: async () => ({ ok: true, data: { name: "demo" } }) };
    },
  },
}));

import { useCreateProject } from "@/lib/queries/projects";

function wrapper({ children }: { children: ReactNode }) {
  return <QueryClientProvider client={new QueryClient()}>{children}</QueryClientProvider>;
}

describe("useCreateProject film language", () => {
  beforeEach(() => post.mockReset());

  it("sends film_language with the name", async () => {
    const { result } = renderHook(() => useCreateProject(), { wrapper });
    await act(() => result.current.mutateAsync({ name: "demo", film_language: "vi" }));
    expect(post).toHaveBeenCalledWith("api/v1/projects", { json: { name: "demo", film_language: "vi" } });
  });

  it("still accepts a plain name (existing callers)", async () => {
    const { result } = renderHook(() => useCreateProject(), { wrapper });
    await act(() => result.current.mutateAsync("demo"));
    expect(post).toHaveBeenCalledWith("api/v1/projects", { json: { name: "demo" } });
  });
});
