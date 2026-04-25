export type RepoStatus =
  | "healthy"
  | "active"
  | "stalled"
  | "blocked"
  | "error"
  | "unknown";

export interface SyncRun {
  started_at: string;
  finished_at: string;
  synced_count: number;
  failed_count: number;
}

export interface SchedulerStatus {
  running: boolean;
  sync_interval_minutes: number;
  next_sync_at: string | null;
}

export interface RootResponse {
  name: string;
  status: string;
  persistence: string;
  database_file: string;
  tracked_repos_file: string;
  latest_sync_run: SyncRun | null;
  scheduler: SchedulerStatus;
}

export interface RepoSummary {
  id: string;
  name: string;
  full_name: string;
  current_goal: string | null;
  status_summary: string | null;
  milestone: string | null;
  last_activity_at: string | null;
  attention_flag: boolean;
  attention_reasons: string[];
  missing_sources: string[];
  last_synced_at: string | null;
  sync_error: string | null;
  status: RepoStatus;
  is_data_stale: boolean;
}

export interface GitHubEvent {
  type: "commit" | "pull_request" | "issue";
  title: string;
  url: string | null;
  occurred_at: string | null;
}

export interface RepoDetail extends RepoSummary {
  notes: string | null;
  recent_updates: string[];
  blockers: string[];
  github_activity: GitHubEvent[];
  documentation_sources: string[];
}

export interface RepoListResponse {
  repos: RepoSummary[];
}

export interface TrackedRepo {
  id: string;
  owner: string;
  repo: string;
  full_name: string;
  name: string | null;
  display_name: string;
  enabled: boolean;
  notes: string | null;
}

export interface TrackedRepoListResponse {
  tracked_repos: TrackedRepo[];
}

export interface CreateTrackedRepoInput {
  id: string;
  owner: string;
  repo: string;
  name?: string | null;
  notes?: string | null;
  enabled?: boolean;
}

export interface UpdateTrackedRepoInput {
  enabled?: boolean;
  name?: string | null;
  notes?: string | null;
}

export interface SyncResult {
  repo_id: string;
  synced: boolean;
  sync_error: string | null;
}

export interface SyncResponse {
  results: SyncResult[];
  synced_count: number;
}
