import type {
  CreateTrackedRepoInput,
  GitHubSearchResponse,
  RepoDetail,
  RepoListResponse,
  RootResponse,
  SyncResponse,
  TrackedRepo,
  TrackedRepoListResponse,
  UpdateTrackedRepoInput,
} from "@/lib/api/types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      Accept: "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const errorPayload = (await response.json().catch(() => null)) as
      | { detail?: string }
      | null;
    throw new Error(
      errorPayload?.detail ?? `Request failed with status ${response.status}`,
    );
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export function fetchMeta() {
  return apiFetch<RootResponse>("/api/meta");
}

export async function fetchRepos() {
  const payload = await apiFetch<RepoListResponse>("/api/repos");
  return payload.repos;
}

export async function fetchTrackedRepos() {
  const payload = await apiFetch<TrackedRepoListResponse>("/api/tracked-repos");
  return payload.tracked_repos;
}

export function fetchRepo(repoId: string) {
  return apiFetch<RepoDetail>(`/api/repos/${repoId}`);
}

export function syncRepos() {
  return apiFetch<SyncResponse>("/api/sync", { method: "POST" });
}

export function createTrackedRepo(input: CreateTrackedRepoInput) {
  return apiFetch<TrackedRepo>("/api/tracked-repos", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(input),
  });
}

export function updateTrackedRepo(
  repoId: string,
  input: UpdateTrackedRepoInput,
) {
  return apiFetch<TrackedRepo>(`/api/tracked-repos/${repoId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(input),
  });
}

export function deleteTrackedRepo(repoId: string) {
  return apiFetch<void>(`/api/tracked-repos/${repoId}`, { method: "DELETE" });
}

export async function searchGitHubRepos(query: string, limit = 10) {
  const payload = await apiFetch<GitHubSearchResponse>(
    `/api/github/search?q=${encodeURIComponent(query)}&per_page=${limit}`,
  );
  return payload.results;
}

export async function listUserRepos(username: string, limit = 30) {
  const payload = await apiFetch<GitHubSearchResponse>(
    `/api/github/user-repos?username=${encodeURIComponent(username)}&per_page=${limit}`,
  );
  return payload.results;
}
