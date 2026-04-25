import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DashboardPage } from "@/features/repos/dashboard-page";
import { renderWithAppProviders } from "@/test/utils";

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);

      if (url.endsWith("/api/meta")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              name: "Project Manager",
              status: "ok",
              persistence: "sqlite",
              database_file: "data/project_manager.db",
              tracked_repos_file: "config/tracked_repos.yaml",
              latest_sync_run: {
                started_at: "2026-04-21T12:00:00+00:00",
                finished_at: "2026-04-21T12:01:00+00:00",
                synced_count: 2,
                failed_count: 0,
              },
              scheduler: {
                running: false,
                sync_interval_minutes: 360,
                next_sync_at: null,
              },
            }),
          ),
        );
      }

      if (url.endsWith("/api/repos")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              repos: [
                {
                  id: "project-manager",
                  name: "Project Manager",
                  full_name: "connorkitchings/project-manager",
                  current_goal: "Build the repo dashboard",
                  status_summary: "Healthy and active",
                  milestone: "Frontend MVP",
                  last_activity_at: "2026-04-21T11:30:00+00:00",
                  attention_flag: false,
                  attention_reasons: [],
                  missing_sources: [],
                  last_synced_at: "2026-04-21T12:01:00+00:00",
                  sync_error: null,
                  status: "healthy",
                  is_data_stale: false,
                },
                {
                  id: "legacy-repo",
                  name: "Legacy Repo",
                  full_name: "connorkitchings/legacy-repo",
                  current_goal: "Untangle old docs",
                  status_summary: "Needs cleanup",
                  milestone: null,
                  last_activity_at: null,
                  attention_flag: true,
                  attention_reasons: ["Missing docs: docs/project_charter.md"],
                  missing_sources: ["docs/project_charter.md"],
                  last_synced_at: null,
                  sync_error: "GitHub token missing",
                  status: "error",
                  is_data_stale: false,
                },
              ],
            }),
          ),
        );
      }

      if (url.endsWith("/api/sync") && init?.method === "POST") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              synced_count: 2,
              results: [
                { repo_id: "project-manager", synced: true, sync_error: null },
                { repo_id: "legacy-repo", synced: true, sync_error: null },
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

  it("renders repo summaries and filters attention states", async () => {
    const user = userEvent.setup();
    renderWithAppProviders(<DashboardPage />);

    expect(await screen.findByText("Project Manager")).toBeInTheDocument();
    expect(screen.getByText("Legacy Repo")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Needs attention" }));

    expect(screen.getByText("Legacy Repo")).toBeInTheDocument();
    expect(screen.queryByText("Healthy and active")).not.toBeInTheDocument();
  });

  it("triggers a sync mutation", async () => {
    const user = userEvent.setup();
    const fetchMock = global.fetch as ReturnType<typeof vi.fn>;

    renderWithAppProviders(<DashboardPage />);
    await screen.findByText("Project Manager");

    const [syncButton] = screen.getAllByRole("button", { name: "Sync now" });
    await user.click(syncButton);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/sync",
        expect.objectContaining({ method: "POST" }),
      );
    });
  });
});
