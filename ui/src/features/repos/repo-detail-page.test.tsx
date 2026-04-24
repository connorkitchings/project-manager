import { screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { RepoDetailPage } from "@/features/repos/repo-detail-page";
import { renderWithAppProviders } from "@/test/utils";

describe("RepoDetailPage", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL) => {
      const url = String(input);

      if (url.endsWith("/api/repos/project-manager")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              id: "project-manager",
              name: "Project Manager",
              full_name: "connorkitchings/project-manager",
              current_goal: "Ship the frontend",
              status_summary: "Building the browser UI.",
              milestone: "Frontend MVP",
              last_activity_at: "2026-04-21T11:30:00+00:00",
              attention_flag: true,
              attention_reasons: ["Missing docs: session_logs/latest"],
              missing_sources: ["session_logs/latest"],
              last_synced_at: "2026-04-21T12:01:00+00:00",
              sync_error: null,
              notes: "Primary tracked repo",
              recent_updates: ["Added the React dashboard shell"],
              blockers: ["Need final visual polish"],
              documentation_sources: ["README.md", "docs/project_charter.md"],
              github_activity: [
                {
                  type: "pull_request",
                  title: "Add dashboard route",
                  url: "https://example.com/pull/1",
                  occurred_at: "2026-04-21T11:40:00+00:00",
                },
              ],
            }),
          ),
        );
      }

      if (url.endsWith("/api/sync")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              synced_count: 1,
              results: [
                { repo_id: "project-manager", synced: true, sync_error: null },
              ],
            }),
          ),
        );
      }

      return Promise.reject(new Error(`Unhandled fetch for ${url}`));
    }) as typeof fetch);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders the repository detail view", async () => {
    renderWithAppProviders(<RepoDetailPage />, {
      route: "/repos/project-manager",
      path: "/repos/:repoId",
    });

    expect(await screen.findByText("Ship the frontend")).toBeInTheDocument();
    expect(screen.getByText("Added the React dashboard shell")).toBeInTheDocument();
    expect(screen.getByText("Need final visual polish")).toBeInTheDocument();
    expect(screen.getByText("Add dashboard route")).toBeInTheDocument();
    expect(screen.getByText("README.md")).toBeInTheDocument();
    expect(screen.getByText("Why this needs attention")).toBeInTheDocument();
  });
});
