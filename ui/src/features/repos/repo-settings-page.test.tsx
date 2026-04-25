import { cleanup, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { RepoSettingsPage } from "@/features/repos/repo-settings-page";
import { renderWithAppProviders } from "@/test/utils";

describe("RepoSettingsPage", () => {
  beforeEach(() => {
    const trackedRepos: Array<{
      id: string;
      owner: string;
      repo: string;
      full_name: string;
      name: string | null;
      display_name: string;
      enabled: boolean;
      notes: string | null;
    }> = [
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

        if (url.includes("/api/tracked-repos/") && init?.method === "DELETE") {
          const repoId = url.split("/").pop() ?? "";
          const index = trackedRepos.findIndex((repo) => repo.id === repoId);
          if (index !== -1) trackedRepos.splice(index, 1);
          return new Response(null, { status: 204 });
        }

        if (url.includes("/api/github/search")) {
          return new Response(JSON.stringify({ results: [] }));
        }

        if (url.includes("/api/github/user-repos")) {
          return new Response(JSON.stringify({ results: [] }));
        }

        return Promise.reject(new Error(`Unhandled fetch for ${url}`));
      }) as typeof fetch,
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    cleanup();
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

  it("removes a tracked repo after confirmation", async () => {
    const user = userEvent.setup();

    renderWithAppProviders(<RepoSettingsPage />, {
      route: "/settings/repos",
      path: "/settings/repos",
    });

    expect(await screen.findByText("Project Manager")).toBeInTheDocument();

    const removeButtons = screen.getAllByRole("button", { name: "Remove repo" });
    await user.click(removeButtons[0]);

    expect(
      await screen.findByRole("button", { name: "Confirm remove" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Confirm remove" }));

    await waitFor(
      () => {
        expect(screen.queryAllByRole("article")).toHaveLength(1);
      },
      { timeout: 3000 },
    );
  });

  it("cancels removal when Cancel is clicked", async () => {
    const user = userEvent.setup();

    renderWithAppProviders(<RepoSettingsPage />, {
      route: "/settings/repos",
      path: "/settings/repos",
    });

    expect(await screen.findAllByRole("article")).toHaveLength(2);

    await user.click(screen.getAllByRole("button", { name: "Remove repo" })[0]);
    expect(
      screen.getByRole("button", { name: "Confirm remove" }),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(
      screen.queryByRole("button", { name: "Confirm remove" }),
    ).not.toBeInTheDocument();
    expect(screen.getAllByRole("article")).toHaveLength(2);
  });

  it("adds a new tracked repo", async () => {
    const user = userEvent.setup();

    renderWithAppProviders(<RepoSettingsPage />, {
      route: "/settings/repos",
      path: "/settings/repos",
    });

    expect(await screen.findAllByRole("article")).toHaveLength(2);
    const formSection = screen
      .getAllByRole("heading", { name: "Manual add" })[0]
      .closest("section");
    if (!formSection) {
      throw new Error("Manual add section not found");
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
