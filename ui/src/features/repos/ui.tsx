import { type PropsWithChildren } from "react";
import { Link } from "react-router-dom";
import clsx from "clsx";

import { formatTimestamp, shortTypeLabel } from "@/lib/format";
import type { GitHubEvent, RepoStatus, RepoSummary, RootResponse } from "@/lib/api/types";

type DashboardFilter = "all" | "attention" | "errors" | "missing";

interface FilterButtonProps {
  active: boolean;
  label: string;
  onClick: () => void;
}

export function FilterButton({ active, label, onClick }: FilterButtonProps) {
  return (
    <button
      className={clsx(
        "rounded-full border px-3 py-2 text-sm transition",
        active
          ? "border-pine bg-pine text-white"
          : "border-ink/10 bg-white/70 text-ink/70 hover:border-pine/35 hover:text-ink",
      )}
      onClick={onClick}
      type="button"
    >
      {label}
    </button>
  );
}

interface StatusBadgeProps {
  attention: boolean;
  hasError?: boolean;
  label?: string;
  status?: RepoStatus;
}

const STATUS_CONFIG: Record<
  RepoStatus,
  { label: string; className: string }
> = {
  healthy: { label: "Healthy", className: "bg-pine/15 text-pine" },
  active: {
    label: "Active",
    className:
      "bg-attention/15 text-[color:color-mix(in_srgb,var(--color-attention)_80%,black)]",
  },
  stalled: {
    label: "Stalled",
    className:
      "bg-attention/15 text-[color:color-mix(in_srgb,var(--color-attention)_80%,black)]",
  },
  blocked: { label: "Blocked", className: "bg-danger/15 text-danger" },
  error: { label: "Sync issue", className: "bg-danger/15 text-danger" },
  unknown: {
    label: "Unknown",
    className:
      "bg-attention/15 text-[color:color-mix(in_srgb,var(--color-attention)_80%,black)]",
  },
};

export function StatusBadge({
  attention,
  hasError = false,
  label,
  status,
}: StatusBadgeProps) {
  let resolvedLabel: string;
  let colorClass: string;

  if (status !== undefined) {
    const config = STATUS_CONFIG[status];
    resolvedLabel = label ?? config.label;
    colorClass = config.className;
  } else {
    resolvedLabel = label ?? (hasError ? "Sync issue" : attention ? "Needs review" : "Healthy");
    colorClass = hasError
      ? "bg-danger/15 text-danger"
      : attention
        ? "bg-attention/15 text-[color:color-mix(in_srgb,var(--color-attention)_80%,black)]"
        : "bg-pine/15 text-pine";
  }

  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full px-3 py-1 font-mono text-[0.7rem] uppercase tracking-[0.22em]",
        colorClass,
      )}
    >
      {resolvedLabel}
    </span>
  );
}

interface StatProps {
  label: string;
  value: string;
}

export function Stat({ label, value }: StatProps) {
  return (
    <div className="rounded-2xl border border-ink/10 bg-white/70 px-4 py-3">
      <div className="text-xs uppercase tracking-[0.22em] text-ink/45">{label}</div>
      <div className="mt-2 text-sm font-medium text-ink">{value}</div>
    </div>
  );
}

interface SectionCardProps {
  title: string;
  subtitle?: string;
}

export function SectionCard({
  title,
  subtitle,
  children,
}: PropsWithChildren<SectionCardProps>) {
  return (
    <section className="rounded-[1.75rem] border border-white/80 bg-white/70 p-5 shadow-panel backdrop-blur">
      <div className="mb-4">
        <h2 className="text-xl font-semibold">{title}</h2>
        {subtitle ? <p className="mt-1 text-sm text-ink/65">{subtitle}</p> : null}
      </div>
      {children}
    </section>
  );
}

interface PageBannerProps {
  title: string;
  description: string;
  meta?: RootResponse;
  syncLabel?: string;
  onSync: () => void;
  syncDisabled?: boolean;
}

export function PageBanner({
  title,
  description,
  meta,
  syncLabel = "Sync now",
  onSync,
  syncDisabled = false,
}: PageBannerProps) {
  return (
    <div className="mb-6 grid gap-4 rounded-[2rem] border border-white/80 bg-white/60 p-5 shadow-panel backdrop-blur lg:grid-cols-[1.5fr_0.8fr]">
      <div>
        <h2 className="text-2xl font-semibold sm:text-3xl">{title}</h2>
        <p className="mt-2 max-w-2xl text-sm text-ink/70 sm:text-base">{description}</p>
      </div>
      <div className="flex flex-col gap-3 rounded-[1.5rem] border border-ink/10 bg-base/80 p-4">
        <div>
          <div className="text-xs uppercase tracking-[0.22em] text-ink/45">
            Latest sync
          </div>
          <div className="mt-2 text-sm font-medium text-ink">
            {formatTimestamp(meta?.latest_sync_run?.finished_at)}
          </div>
          <div className="mt-1 text-xs text-ink/55">
            {meta?.latest_sync_run
              ? `${meta.latest_sync_run.synced_count} synced / ${meta.latest_sync_run.failed_count} failed`
              : "No completed sync yet"}
          </div>
        </div>
        <button
          className="rounded-full bg-accent px-4 py-3 font-medium text-white transition hover:translate-y-[-1px] hover:bg-[color:color-mix(in_srgb,var(--color-accent)_85%,black)] disabled:cursor-not-allowed disabled:opacity-60"
          disabled={syncDisabled}
          onClick={onSync}
          type="button"
        >
          {syncLabel}
        </button>
      </div>
    </div>
  );
}

interface EmptyStateProps {
  title: string;
  body: string;
}

export function EmptyState({ title, body }: EmptyStateProps) {
  return (
    <div className="rounded-[1.75rem] border border-dashed border-ink/15 bg-white/55 p-8 text-center">
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="mx-auto mt-2 max-w-lg text-sm text-ink/65">{body}</p>
    </div>
  );
}

interface RepoCardProps {
  repo: RepoSummary;
}

export function RepoCard({ repo }: RepoCardProps) {
  const primaryAttentionReason = repo.attention_reasons[0];

  return (
    <Link
      className="group flex h-full flex-col gap-4 rounded-[1.75rem] border border-white/80 bg-white/75 p-5 shadow-panel transition hover:-translate-y-1 hover:border-pine/20"
      to={`/repos/${repo.id}`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="font-mono text-xs uppercase tracking-[0.24em] text-ink/45">
            {repo.full_name}
          </div>
          <h3 className="mt-2 text-xl font-semibold group-hover:text-pine">
            {repo.name}
          </h3>
        </div>
        <StatusBadge
          attention={repo.attention_flag}
          hasError={Boolean(repo.sync_error)}
          status={repo.status}
        />
      </div>
      <p className="text-sm text-ink/70">
        {repo.current_goal ?? "No documented goal captured yet."}
      </p>
      <p className="rounded-2xl bg-base/80 px-4 py-3 text-sm text-ink/80">
        {repo.status_summary ?? "No summary available. Sync may be incomplete."}
      </p>
      <div className="grid gap-3 md:grid-cols-2">
        <Stat label="Milestone" value={repo.milestone ?? "Not specified"} />
        <Stat
          label="Last activity"
          value={formatTimestamp(repo.last_activity_at)}
        />
      </div>
      {repo.missing_sources.length ? (
        <div className="rounded-2xl border border-attention/20 bg-attention/10 px-4 py-3 text-sm text-ink/80">
          Missing: {repo.missing_sources.join(", ")}
        </div>
      ) : null}
      {primaryAttentionReason &&
      !repo.sync_error &&
      !(repo.missing_sources.length && primaryAttentionReason.startsWith("Missing docs:")) ? (
        <div className="rounded-2xl border border-attention/20 bg-attention/10 px-4 py-3 text-sm text-ink/80">
          {primaryAttentionReason}
        </div>
      ) : null}
      {repo.sync_error ? (
        <div className="rounded-2xl border border-danger/20 bg-danger/10 px-4 py-3 text-sm text-danger">
          {repo.sync_error}
        </div>
      ) : null}
    </Link>
  );
}

interface TimelineItemProps {
  event: GitHubEvent;
}

export function TimelineItem({ event }: TimelineItemProps) {
  const body = (
    <>
      <div className="flex items-center gap-3">
        <span className="rounded-full bg-pine/10 px-2 py-1 font-mono text-[0.65rem] uppercase tracking-[0.2em] text-pine">
          {shortTypeLabel(event.type)}
        </span>
        <span className="text-xs text-ink/45">
          {formatTimestamp(event.occurred_at)}
        </span>
      </div>
      <div className="mt-2 text-sm font-medium text-ink">{event.title}</div>
    </>
  );

  return event.url ? (
    <a
      className="block rounded-2xl border border-ink/10 bg-base/65 p-4 transition hover:border-pine/30"
      href={event.url}
      rel="noreferrer"
      target="_blank"
    >
      {body}
    </a>
  ) : (
    <div className="rounded-2xl border border-ink/10 bg-base/65 p-4">{body}</div>
  );
}

export const dashboardFilters: Array<{
  value: DashboardFilter;
  label: string;
}> = [
  { value: "all", label: "All repos" },
  { value: "attention", label: "Needs attention" },
  { value: "errors", label: "Sync errors" },
  { value: "missing", label: "Missing docs" },
];

export type TimelineFilterValue = "all" | "commit" | "pull_request" | "issue";

export const timelineFilters: Array<{
  value: TimelineFilterValue;
  label: string;
}> = [
  { value: "all", label: "All" },
  { value: "commit", label: "Commits" },
  { value: "pull_request", label: "PRs" },
  { value: "issue", label: "Issues" },
];

export type { DashboardFilter };
