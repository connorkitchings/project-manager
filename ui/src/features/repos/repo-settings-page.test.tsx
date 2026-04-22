import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { RepoSettingsPage } from "@/features/repos/repo-settings-page";
import { renderWithAppProviders } from "@/test/utils";

describe("RepoSettingsPage", () => {
  beforeEach(() => {
    const trackedRepos = [
      {
        id: "project-manager",
        owner: "connorkitchings",
        repo: "project-manager",
        full_name: "connorkitchings/project-manager",
        name: "Project Manager",
        display_name: "Project Manager",
        enabled: true,
        notes: "Primary tracked repo",
      },
      {
        id: "legacy-repo",
        owner: "connorkitchings",
        repo: "legacy-repo",
        full_name: "connorkitchings/legacy-repo",
        name: "Legacy Repo",
        display_name: "Legacy Repo",
        enabled: false,
        notes: null,
      },
    ];

    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);

        if (url.endsWith("/api/tracked-repos") && !init?.method) {
          return new Response(JSON.stringify({ tracked_repos: trackedRepos }));
        }

        if (url.endsWith("/api/tracked-repos") && init?.method === "POST") {
          const payload = JSON.parse(String(init.body)) as {
            id: string;
            owner: string;
            repo: string;
            name?: string | null;
            notes?: string | null;
            enabled?: boolean;
          };
          const created = {
            id: payload.id,
            owner: payload.owner,
            repo: payload.repo,
            full_name: `${payload.owner}/${payload.repo}`,
            name: payload.name ?? null,
            display_name: payload.name ?? payload.repo,
            enabled: payload.enabled ?? true,
            notes: payload.notes ?? null,
          };
          trackedRepos.push(created);
          return new Response(JSON.stringify(created), { status: 201 });
        }

        if (url.includes("/api/tracked-repos/") && init?.method === "PATCH") {
          const repoId = url.split("/").pop() ?? "";
          const payload = JSON.parse(String(init.body)) as {
            enabled?: boolean;
            name?: string | null;
            notes?: string | null;
          };
          const index = trackedRepos.findIndex((repo) => repo.id === repoId);
          trackedRepos[index] = {
            ...trackedRepos[index],
            enabled: payload.enabled ?? trackedRepos[index].enabled,
            name:
              payload.name === undefined ? trackedRepos[index].name : payload.name,
            display_name:
              payload.name === undefined
                ? trackedRepos[index].display_name
                : (payload.name ?? trackedRepos[index].repo),
            notes:
              payload.notes === undefined ? trackedRepos[index].notes : payload.notes,
          };
          return new Response(JSON.stringify(trackedRepos[index]));
        }

        return Promise.reject(new Error(`Unhandled fetch for ${url}`));
      }) as typeof fetch,
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders tracked repos and toggles enabled state", async () => {
    const user = userEvent.setup();

    renderWithAppProviders(<RepoSettingsPage />, {
      route: "/settings/repos",
      path: "/settings/repos",
    });

    expect(await screen.findByText("Project Manager")).toBeInTheDocument();
    expect(screen.getByText("Legacy Repo")).toBeInTheDocument();

    await user.click(screen.getAllByRole("button", { name: "Disable repo" })[0]);

    await waitFor(() => {
      expect(screen.getAllByRole("button", { name: "Enable repo" })).toHaveLength(2);
    });
  });

  it("adds a new tracked repo", async () => {
    const user = userEvent.setup();

    renderWithAppProviders(<RepoSettingsPage />, {
      route: "/settings/repos",
      path: "/settings/repos",
    });

    await screen.findByText("Project Manager");
    const formSection = screen
      .getAllByRole("heading", { name: "Tracked repository management" })[0]
      .closest("section");
    if (!formSection) {
      throw new Error("Tracked repository management section not found");
    }
    const form = within(formSection);

    await user.type(form.getByLabelText("GitHub owner"), "connorkitchings");
    await user.type(form.getByLabelText("GitHub repo"), "panicstats");
    await user.clear(form.getByLabelText("Runtime id"));
    await user.type(form.getByLabelText("Runtime id"), "panicstats");
    await user.type(form.getByLabelText("Display name"), "Panic Stats");
    await user.click(form.getByRole("button", { name: "Add tracked repo" }));

    expect(await screen.findByText("Panic Stats")).toBeInTheDocument();
  });
});
