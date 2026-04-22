import { Link, useParams } from "react-router-dom";

import { useRepoDetail, useSyncRepos } from "@/features/repos/hooks";
import {
  EmptyState,
  PageBanner,
  SectionCard,
  Stat,
  StatusBadge,
  TimelineItem,
} from "@/features/repos/ui";
import { formatTimestamp } from "@/lib/format";

export function RepoDetailPage() {
  const { repoId } = useParams<{ repoId: string }>();
  const syncMutation = useSyncRepos();
  const repoQuery = useRepoDetail(repoId ?? "", Boolean(repoId));

  if (!repoId) {
    return (
      <EmptyState
        body="The repository id is missing from the route."
        title="Repository not found"
      />
    );
  }

  if (repoQuery.isLoading) {
    return (
      <EmptyState
        body="Loading the latest normalized snapshot for this repository."
        title="Loading repository"
      />
    );
  }

  if (repoQuery.isError) {
    return (
      <EmptyState
        body={repoQuery.error.message}
        title="Unable to load repository detail"
      />
    );
  }

  const repo = repoQuery.data;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Link
          className="inline-flex items-center gap-2 rounded-full border border-ink/10 bg-white/60 px-4 py-2 text-sm text-ink/70 transition hover:border-pine/30 hover:text-pine"
          to="/"
        >
          Back to dashboard
        </Link>
      </div>

      <PageBanner
        description={repo.status_summary ?? "No high-level summary is available for this repository yet."}
        onSync={() => syncMutation.mutate()}
        syncDisabled={syncMutation.isPending}
        syncLabel={syncMutation.isPending ? "Syncing..." : "Sync this portfolio"}
        title={repo.name}
      />

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="space-y-6">
          <section className="rounded-[1.75rem] border border-white/80 bg-white/75 p-6 shadow-panel">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="font-mono text-xs uppercase tracking-[0.24em] text-ink/45">
                  {repo.full_name}
                </div>
                <h2 className="mt-2 text-3xl font-semibold">{repo.current_goal ?? "No documented current goal"}</h2>
              </div>
              <StatusBadge
                attention={repo.attention_flag}
                hasError={Boolean(repo.sync_error)}
              />
            </div>

            <div className="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <Stat label="Milestone" value={repo.milestone ?? "Not specified"} />
              <Stat
                label="Last activity"
                value={formatTimestamp(repo.last_activity_at)}
              />
              <Stat
                label="Last synced"
                value={formatTimestamp(repo.last_synced_at)}
              />
              <Stat
                label="Documentation sources"
                value={String(repo.documentation_sources.length)}
              />
            </div>

            {repo.notes ? (
              <div className="mt-6 rounded-2xl bg-base/75 px-4 py-3 text-sm text-ink/75">
                {repo.notes}
              </div>
            ) : null}

            {repo.sync_error ? (
              <div className="mt-6 rounded-2xl border border-danger/20 bg-danger/10 px-4 py-3 text-sm text-danger">
                {repo.sync_error}
              </div>
            ) : null}

            {repo.attention_reasons.length ? (
              <div className="mt-4 rounded-2xl border border-attention/20 bg-attention/10 px-4 py-3">
                <div className="text-xs uppercase tracking-[0.22em] text-ink/45">
                  Why this needs attention
                </div>
                <ul className="mt-3 space-y-2 text-sm text-ink/80">
                  {repo.attention_reasons.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            {repo.missing_sources.length ? (
              <div className="mt-4 rounded-2xl border border-attention/20 bg-attention/10 px-4 py-3 text-sm text-ink/80">
                Missing sources: {repo.missing_sources.join(", ")}
              </div>
            ) : null}
          </section>

          <SectionCard
            subtitle="Items extracted from project documentation or session logs."
            title="Recent updates"
          >
            {repo.recent_updates.length ? (
              <ul className="space-y-3">
                {repo.recent_updates.map((update) => (
                  <li
                    className="rounded-2xl border border-ink/10 bg-base/65 px-4 py-3 text-sm text-ink/80"
                    key={update}
                  >
                    {update}
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState
                body="No recent updates were extracted for this repository."
                title="No documented updates"
              />
            )}
          </SectionCard>

          <SectionCard
            subtitle="Known blockers surfaced from docs or sync state."
            title="Blockers"
          >
            {repo.blockers.length ? (
              <ul className="space-y-3">
                {repo.blockers.map((blocker) => (
                  <li
                    className="rounded-2xl border border-danger/15 bg-danger/10 px-4 py-3 text-sm text-ink/80"
                    key={blocker}
                  >
                    {blocker}
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState
                body="No blockers are currently recorded for this repository."
                title="No blockers captured"
              />
            )}
          </SectionCard>
        </div>

        <div className="space-y-6">
          <SectionCard
            subtitle="Tracked files that contributed to this snapshot."
            title="Documentation sources"
          >
            {repo.documentation_sources.length ? (
              <ul className="space-y-3">
                {repo.documentation_sources.map((source) => (
                  <li
                    className="rounded-2xl border border-ink/10 bg-base/65 px-4 py-3 font-mono text-sm text-ink/75"
                    key={source}
                  >
                    {source}
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState
                body="No documentation inputs were recorded for the latest snapshot."
                title="No documentation sources"
              />
            )}
          </SectionCard>

          <SectionCard
            subtitle="Recent GitHub events used as freshness signals."
            title="GitHub activity"
          >
            {repo.github_activity.length ? (
              <div className="space-y-3">
                {repo.github_activity.map((event) => (
                  <TimelineItem
                    event={event}
                    key={`${event.type}-${event.title}-${event.occurred_at ?? "unknown"}`}
                  />
                ))}
              </div>
            ) : (
              <EmptyState
                body="No recent GitHub activity was available during the latest sync."
                title="No activity available"
              />
            )}
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
