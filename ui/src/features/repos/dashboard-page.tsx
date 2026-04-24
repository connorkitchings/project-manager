import { useDeferredValue, useMemo, useState } from "react";

import { useMeta, useRepos, useSyncRepos } from "@/features/repos/hooks";
import {
  dashboardFilters,
  EmptyState,
  FilterButton,
  PageBanner,
  RepoCard,
  type DashboardFilter,
} from "@/features/repos/ui";

export function DashboardPage() {
  const [filter, setFilter] = useState<DashboardFilter>("all");
  const [search, setSearch] = useState("");
  const deferredSearch = useDeferredValue(search);

  const metaQuery = useMeta();
  const reposQuery = useRepos();
  const syncMutation = useSyncRepos();

  const filteredRepos = useMemo(() => {
    const query = deferredSearch.trim().toLowerCase();
    const repos = reposQuery.data ?? [];

    return repos.filter((repo) => {
      const matchesQuery =
        !query ||
        repo.name.toLowerCase().includes(query) ||
        repo.full_name.toLowerCase().includes(query) ||
        (repo.current_goal ?? "").toLowerCase().includes(query) ||
        (repo.status_summary ?? "").toLowerCase().includes(query);

      if (!matchesQuery) {
        return false;
      }

      if (filter === "attention") {
        return repo.attention_flag;
      }
      if (filter === "errors") {
        return Boolean(repo.sync_error);
      }
      if (filter === "missing") {
        return repo.missing_sources.length > 0;
      }
      return true;
    });
  }, [deferredSearch, filter, reposQuery.data]);

  return (
    <div>
      <PageBanner
        description="Review documented intent, missing sources, and recent GitHub evidence without opening each repo one by one."
        meta={metaQuery.data}
        onSync={() => syncMutation.mutate()}
        syncDisabled={syncMutation.isPending}
        syncLabel={syncMutation.isPending ? "Syncing..." : "Sync now"}
        title="Portfolio dashboard"
      />

      <div className="mb-6 flex flex-col gap-4 rounded-[1.75rem] border border-white/80 bg-white/60 p-5 shadow-panel backdrop-blur lg:flex-row lg:items-center lg:justify-between">
        <label className="flex-1">
          <span className="mb-2 block text-xs uppercase tracking-[0.22em] text-ink/45">
            Search repos or goals
          </span>
          <input
            className="w-full rounded-full border border-ink/10 bg-base/80 px-4 py-3 text-sm text-ink outline-none transition focus:border-pine/35"
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search by repo, goal, or summary"
            type="search"
            value={search}
          />
        </label>
        <div className="flex flex-wrap gap-2">
          {dashboardFilters.map((option) => (
            <FilterButton
              active={filter === option.value}
              key={option.value}
              label={option.label}
              onClick={() => setFilter(option.value)}
            />
          ))}
        </div>
      </div>

      {reposQuery.isLoading ? (
        <EmptyState
          body="The dashboard is loading tracked repository summaries."
          title="Loading repositories"
        />
      ) : reposQuery.isError ? (
        <EmptyState
          body={reposQuery.error.message}
          title="Unable to load repository summaries"
        />
      ) : filteredRepos.length === 0 ? (
        <EmptyState
          body="Adjust the search or filter, or run a sync if the backend has not been refreshed yet."
          title="No repositories match this view"
        />
      ) : (
        <div className="grid gap-5 lg:grid-cols-2">
          {filteredRepos.map((repo) => (
            <RepoCard key={repo.id} repo={repo} />
          ))}
        </div>
      )}
    </div>
  );
}
