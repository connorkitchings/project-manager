import { type FormEvent, useEffect, useMemo, useState } from "react";

import {
  useCreateTrackedRepo,
  useDeleteTrackedRepo,
  useGitHubSearch,
  useTrackedRepos,
  useUpdateTrackedRepo,
  useUserRepos,
} from "@/features/repos/hooks";
import { EmptyState, SectionCard } from "@/features/repos/ui";
import type { GitHubSearchResult, TrackedRepo } from "@/lib/api/types";

function buildRecommendedId(owner: string, repo: string) {
  return `${owner}-${repo}`
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .replace(/-{2,}/g, "-");
}

interface TrackedRepoRowProps {
  repo: TrackedRepo;
}

function TrackedRepoRow({ repo }: TrackedRepoRowProps) {
  const updateMutation = useUpdateTrackedRepo(repo.id);
  const deleteMutation = useDeleteTrackedRepo();
  const [name, setName] = useState(repo.name ?? "");
  const [notes, setNotes] = useState(repo.notes ?? "");
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    setName(repo.name ?? "");
    setNotes(repo.notes ?? "");
  }, [repo.name, repo.notes]);

  const detailsChanged = name !== (repo.name ?? "") || notes !== (repo.notes ?? "");

  return (
    <article className="rounded-[1.5rem] border border-ink/10 bg-base/70 p-4">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-lg font-semibold text-ink">{repo.display_name}</h3>
            <span
              className={
                repo.enabled
                  ? "rounded-full bg-pine/15 px-3 py-1 font-mono text-[0.7rem] uppercase tracking-[0.22em] text-pine"
                  : "rounded-full bg-ink/10 px-3 py-1 font-mono text-[0.7rem] uppercase tracking-[0.22em] text-ink/60"
              }
            >
              {repo.enabled ? "Enabled" : "Disabled"}
            </span>
          </div>
          <div className="font-mono text-xs uppercase tracking-[0.22em] text-ink/45">
            {repo.full_name} · {repo.id}
          </div>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <button
            className="rounded-full border border-ink/10 bg-white/75 px-4 py-2 text-sm font-medium text-ink transition hover:border-pine/25 hover:text-pine disabled:cursor-not-allowed disabled:opacity-60"
            disabled={updateMutation.isPending}
            onClick={() => updateMutation.mutate({ enabled: !repo.enabled })}
            type="button"
          >
            {repo.enabled ? "Disable repo" : "Enable repo"}
          </button>
          {confirming ? (
            <>
              <button
                className="rounded-full border border-danger/30 bg-danger/10 px-4 py-2 text-sm font-medium text-danger transition hover:bg-danger/20 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={deleteMutation.isPending}
                onClick={() => deleteMutation.mutate(repo.id)}
                type="button"
              >
                {deleteMutation.isPending ? "Removing…" : "Confirm remove"}
              </button>
              <button
                className="rounded-full border border-ink/10 bg-white/75 px-4 py-2 text-sm font-medium text-ink transition hover:border-ink/25 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={deleteMutation.isPending}
                onClick={() => setConfirming(false)}
                type="button"
              >
                Cancel
              </button>
            </>
          ) : (
            <button
              className="rounded-full border border-ink/10 bg-white/75 px-4 py-2 text-sm font-medium text-ink/60 transition hover:border-danger/30 hover:text-danger disabled:cursor-not-allowed disabled:opacity-60"
              onClick={() => setConfirming(true)}
              type="button"
            >
              Remove repo
            </button>
          )}
        </div>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_1.25fr_auto]">
        <label className="space-y-2">
          <span className="text-xs uppercase tracking-[0.22em] text-ink/45">
            Display name
          </span>
          <input
            className="w-full rounded-2xl border border-ink/10 bg-white/75 px-4 py-3 text-sm text-ink outline-none transition focus:border-pine/35"
            onChange={(event) => setName(event.target.value)}
            type="text"
            value={name}
          />
        </label>
        <label className="space-y-2">
          <span className="text-xs uppercase tracking-[0.22em] text-ink/45">
            Notes
          </span>
          <input
            className="w-full rounded-2xl border border-ink/10 bg-white/75 px-4 py-3 text-sm text-ink outline-none transition focus:border-pine/35"
            onChange={(event) => setNotes(event.target.value)}
            placeholder="Optional context for why this repo is tracked"
            type="text"
            value={notes}
          />
        </label>
        <div className="flex items-end">
          <button
            className="w-full rounded-full bg-accent px-4 py-3 text-sm font-medium text-white transition hover:translate-y-[-1px] hover:bg-[color:color-mix(in_srgb,var(--color-accent)_85%,black)] disabled:cursor-not-allowed disabled:opacity-60"
            disabled={!detailsChanged || updateMutation.isPending}
            onClick={() =>
              updateMutation.mutate({
                name: name || null,
                notes: notes || null,
              })
            }
            type="button"
          >
            Save details
          </button>
        </div>
      </div>

      {updateMutation.error ? (
        <p className="mt-3 text-sm text-danger">{updateMutation.error.message}</p>
      ) : null}
      {deleteMutation.error ? (
        <p className="mt-3 text-sm text-danger">{deleteMutation.error.message}</p>
      ) : null}
    </article>
  );
}

type DiscoveryTab = "search" | "username";

function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);
  return debounced;
}

interface RepoDiscoverySectionProps {
  trackedRepos: TrackedRepo[];
}

function RepoDiscoverySection({ trackedRepos }: RepoDiscoverySectionProps) {
  const createMutation = useCreateTrackedRepo();
  const [tab, setTab] = useState<DiscoveryTab>("search");
  const [searchQuery, setSearchQuery] = useState("");
  const [usernameInput, setUsernameInput] = useState("");
  const debouncedQuery = useDebouncedValue(searchQuery, 400);
  const debouncedUsername = useDebouncedValue(usernameInput, 400);

  const searchResults = useGitHubSearch(debouncedQuery);
  const userRepos = useUserRepos(tab === "username" ? debouncedUsername : "");

  const trackedFullNames = useMemo(
    () => new Set(trackedRepos.map((r) => r.full_name.toLowerCase())),
    [trackedRepos],
  );

  const activeResults = tab === "search" ? searchResults.data : userRepos.data;
  const isLoading = tab === "search" ? searchResults.isLoading : userRepos.isLoading;
  const error = tab === "search" ? searchResults.error : userRepos.error;

  function handleAdd(result: GitHubSearchResult) {
    createMutation.mutate({
      id: buildRecommendedId(result.owner, result.repo),
      owner: result.owner,
      repo: result.repo,
      enabled: true,
    });
  }

  return (
    <SectionCard
      subtitle="Search GitHub or list your public repos, then add them to the dashboard with one click."
      title="Discover repositories"
    >
      <div className="flex gap-2">
        <button
          className={`rounded-full px-4 py-2 text-sm font-medium transition ${
            tab === "search"
              ? "bg-pine/15 text-pine"
              : "border border-ink/10 text-ink/60 hover:border-pine/25 hover:text-pine"
          }`}
          onClick={() => setTab("search")}
          type="button"
        >
          Search
        </button>
        <button
          className={`rounded-full px-4 py-2 text-sm font-medium transition ${
            tab === "username"
              ? "bg-pine/15 text-pine"
              : "border border-ink/10 text-ink/60 hover:border-pine/25 hover:text-pine"
          }`}
          onClick={() => setTab("username")}
          type="button"
        >
          My repos
        </button>
      </div>

      <div className="mt-4">
        {tab === "search" ? (
          <input
            className="w-full rounded-2xl border border-ink/10 bg-base/80 px-4 py-3 text-sm text-ink outline-none transition focus:border-pine/35"
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search repositories (e.g. flask dashboard)…"
            type="text"
            value={searchQuery}
          />
        ) : (
          <input
            className="w-full rounded-2xl border border-ink/10 bg-base/80 px-4 py-3 text-sm text-ink outline-none transition focus:border-pine/35"
            onChange={(e) => setUsernameInput(e.target.value)}
            placeholder="GitHub username (e.g. connorkitchings)…"
            type="text"
            value={usernameInput}
          />
        )}
      </div>

      {isLoading ? (
        <EmptyState body="Searching GitHub…" title="Loading" />
      ) : error ? (
        <EmptyState body={error.message} title="Search failed" />
      ) : !activeResults ? (
        <EmptyState
          body={tab === "search" ? "Type at least 2 characters to search." : "Enter a GitHub username to list repos."}
          title={tab === "search" ? "Search GitHub" : "List your repos"}
        />
      ) : activeResults.length === 0 ? (
        <EmptyState body="No repositories found." title="No results" />
      ) : (
        <ul className="mt-4 space-y-3">
          {activeResults.map((result) => {
            const isTracked = trackedFullNames.has(result.full_name.toLowerCase());
            return (
              <li
                key={result.full_name}
                className="flex flex-col gap-2 rounded-2xl border border-ink/10 bg-base/70 p-4 sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="min-w-0 space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <a
                      className="text-sm font-semibold text-ink transition hover:text-pine"
                      href={result.html_url}
                      rel="noopener noreferrer"
                      target="_blank"
                    >
                      {result.full_name}
                    </a>
                    {result.language ? (
                      <span className="rounded-full bg-ink/8 px-2 py-0.5 font-mono text-[0.65rem] uppercase tracking-[0.18em] text-ink/50">
                        {result.language}
                      </span>
                    ) : null}
                    {result.stargazers_count > 0 ? (
                      <span className="text-xs text-ink/40">
                        ★ {result.stargazers_count}
                      </span>
                    ) : null}
                  </div>
                  {result.description ? (
                    <p className="truncate text-sm text-ink/60">{result.description}</p>
                  ) : null}
                </div>
                <div className="shrink-0">
                  <button
                    className="rounded-full bg-accent px-4 py-2 text-sm font-medium text-white transition hover:translate-y-[-1px] hover:bg-[color:color-mix(in_srgb,var(--color-accent)_85%,black)] disabled:cursor-not-allowed disabled:opacity-60"
                    disabled={isTracked || createMutation.isPending}
                    onClick={() => handleAdd(result)}
                    type="button"
                  >
                    {isTracked ? "Already tracked" : "Add to dashboard"}
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      )}

      {createMutation.error ? (
        <p className="mt-3 text-sm text-danger">{createMutation.error.message}</p>
      ) : null}
    </SectionCard>
  );
}

export function RepoSettingsPage() {
  const trackedReposQuery = useTrackedRepos();
  const createMutation = useCreateTrackedRepo();
  const [owner, setOwner] = useState("");
  const [repo, setRepo] = useState("");
  const [repoId, setRepoId] = useState("");
  const [name, setName] = useState("");
  const [notes, setNotes] = useState("");
  const [enabled, setEnabled] = useState(true);
  const [idTouched, setIdTouched] = useState(false);

  useEffect(() => {
    if (idTouched) {
      return;
    }
    setRepoId(buildRecommendedId(owner, repo));
  }, [idTouched, owner, repo]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await createMutation.mutateAsync({
      id: repoId,
      owner,
      repo,
      name: name || null,
      notes: notes || null,
      enabled,
    });
    setOwner("");
    setRepo("");
    setRepoId("");
    setName("");
    setNotes("");
    setEnabled(true);
    setIdTouched(false);
  }

  return (
    <div className="space-y-6">
      <RepoDiscoverySection trackedRepos={trackedReposQuery.data ?? []} />

      <SectionCard
        subtitle="Add repos to SQLite-backed runtime state, then toggle whether they appear in the portfolio dashboard and sync flow."
        title="Manual add"
      >
        <form className="grid gap-4 lg:grid-cols-2" onSubmit={handleSubmit}>
          <label className="space-y-2">
            <span className="text-xs uppercase tracking-[0.22em] text-ink/45">
              GitHub owner
            </span>
            <input
              className="w-full rounded-2xl border border-ink/10 bg-base/80 px-4 py-3 text-sm text-ink outline-none transition focus:border-pine/35"
              onChange={(event) => setOwner(event.target.value)}
              placeholder="connorkitchings"
              required
              type="text"
              value={owner}
            />
          </label>
          <label className="space-y-2">
            <span className="text-xs uppercase tracking-[0.22em] text-ink/45">
              GitHub repo
            </span>
            <input
              className="w-full rounded-2xl border border-ink/10 bg-base/80 px-4 py-3 text-sm text-ink outline-none transition focus:border-pine/35"
              onChange={(event) => setRepo(event.target.value)}
              placeholder="project-manager"
              required
              type="text"
              value={repo}
            />
          </label>
          <label className="space-y-2">
            <span className="text-xs uppercase tracking-[0.22em] text-ink/45">
              Runtime id
            </span>
            <input
              className="w-full rounded-2xl border border-ink/10 bg-base/80 px-4 py-3 text-sm text-ink outline-none transition focus:border-pine/35"
              onChange={(event) => {
                setIdTouched(true);
                setRepoId(event.target.value);
              }}
              placeholder="connorkitchings-project-manager"
              required
              type="text"
              value={repoId}
            />
          </label>
          <label className="space-y-2">
            <span className="text-xs uppercase tracking-[0.22em] text-ink/45">
              Display name
            </span>
            <input
              className="w-full rounded-2xl border border-ink/10 bg-base/80 px-4 py-3 text-sm text-ink outline-none transition focus:border-pine/35"
              onChange={(event) => setName(event.target.value)}
              placeholder="Project Manager"
              type="text"
              value={name}
            />
          </label>
          <label className="space-y-2 lg:col-span-2">
            <span className="text-xs uppercase tracking-[0.22em] text-ink/45">
              Notes
            </span>
            <textarea
              className="min-h-28 w-full rounded-[1.5rem] border border-ink/10 bg-base/80 px-4 py-3 text-sm text-ink outline-none transition focus:border-pine/35"
              onChange={(event) => setNotes(event.target.value)}
              placeholder="Why track this repo? Any portfolio context?"
              value={notes}
            />
          </label>
          <label className="inline-flex items-center gap-3 rounded-2xl border border-ink/10 bg-base/80 px-4 py-3 text-sm text-ink">
            <input
              checked={enabled}
              className="h-4 w-4 accent-pine"
              onChange={(event) => setEnabled(event.target.checked)}
              type="checkbox"
            />
            Enable immediately after adding
          </label>
          <div className="flex items-end justify-end lg:col-span-1">
            <button
              className="w-full rounded-full bg-accent px-4 py-3 font-medium text-white transition hover:translate-y-[-1px] hover:bg-[color:color-mix(in_srgb,var(--color-accent)_85%,black)] disabled:cursor-not-allowed disabled:opacity-60 lg:w-auto"
              disabled={createMutation.isPending}
              type="submit"
            >
              {createMutation.isPending ? "Adding repo..." : "Add tracked repo"}
            </button>
          </div>
        </form>
        {createMutation.error ? (
          <p className="mt-4 text-sm text-danger">{createMutation.error.message}</p>
        ) : null}
      </SectionCard>

      <SectionCard
        subtitle="Enabled repos appear on the dashboard and participate in sync. Disabled repos stay in SQLite runtime state but are hidden from the main portfolio view."
        title="Runtime tracked repos"
      >
        {trackedReposQuery.isLoading ? (
          <EmptyState
            body="Loading tracked repository settings from SQLite."
            title="Loading tracked repos"
          />
        ) : trackedReposQuery.isError ? (
          <EmptyState
            body={trackedReposQuery.error.message}
            title="Unable to load tracked repos"
          />
        ) : trackedReposQuery.data.length === 0 ? (
          <EmptyState
            body="Add the first tracked repo to start managing dashboard coverage."
            title="No tracked repos configured"
          />
        ) : (
          <div className="space-y-4">
            {trackedReposQuery.data.map((trackedRepo) => (
              <TrackedRepoRow key={trackedRepo.id} repo={trackedRepo} />
            ))}
          </div>
        )}
      </SectionCard>
    </div>
  );
}
