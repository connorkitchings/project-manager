import { type FormEvent, useEffect, useState } from "react";

import {
  useCreateTrackedRepo,
  useTrackedRepos,
  useUpdateTrackedRepo,
} from "@/features/repos/hooks";
import { EmptyState, SectionCard } from "@/features/repos/ui";
import type { TrackedRepo } from "@/lib/api/types";

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
  const [name, setName] = useState(repo.name ?? "");
  const [notes, setNotes] = useState(repo.notes ?? "");

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
        <button
          className="rounded-full border border-ink/10 bg-white/75 px-4 py-2 text-sm font-medium text-ink transition hover:border-pine/25 hover:text-pine disabled:cursor-not-allowed disabled:opacity-60"
          disabled={updateMutation.isPending}
          onClick={() =>
            updateMutation.mutate({
              enabled: !repo.enabled,
            })
          }
          type="button"
        >
          {repo.enabled ? "Disable repo" : "Enable repo"}
        </button>
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
    </article>
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
      <SectionCard
        subtitle="Add repos to SQLite-backed runtime state, then toggle whether they appear in the portfolio dashboard and sync flow."
        title="Tracked repository management"
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
