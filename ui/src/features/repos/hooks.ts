import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  createTrackedRepo,
  deleteTrackedRepo,
  fetchMeta,
  fetchRepo,
  fetchRepos,
  fetchTrackedRepos,
  syncRepos,
  updateTrackedRepo,
} from "@/lib/api/client";
import type {
  CreateTrackedRepoInput,
  UpdateTrackedRepoInput,
} from "@/lib/api/types";

export const queryKeys = {
  meta: ["meta"] as const,
  repos: ["repos"] as const,
  trackedRepos: ["tracked-repos"] as const,
  repo: (repoId: string) => ["repo", repoId] as const,
};

const SCHEDULER_POLL_INTERVAL_MS = 60_000;

export function useMeta() {
  return useQuery({
    queryKey: queryKeys.meta,
    queryFn: fetchMeta,
    refetchInterval: SCHEDULER_POLL_INTERVAL_MS,
  });
}

export function useRepos() {
  return useQuery({
    queryKey: queryKeys.repos,
    queryFn: fetchRepos,
    refetchInterval: SCHEDULER_POLL_INTERVAL_MS,
  });
}

export function useRepoDetail(repoId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.repo(repoId),
    queryFn: () => fetchRepo(repoId),
    enabled,
  });
}

export function useTrackedRepos() {
  return useQuery({
    queryKey: queryKeys.trackedRepos,
    queryFn: fetchTrackedRepos,
  });
}

export function useSyncRepos() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: syncRepos,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.meta }),
        queryClient.invalidateQueries({ queryKey: queryKeys.repos }),
        queryClient.invalidateQueries({ queryKey: ["repo"] }),
      ]);
    },
  });
}

export function useCreateTrackedRepo() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: CreateTrackedRepoInput) => createTrackedRepo(input),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.trackedRepos }),
        queryClient.invalidateQueries({ queryKey: queryKeys.repos }),
      ]);
    },
  });
}

export function useUpdateTrackedRepo(repoId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: UpdateTrackedRepoInput) => updateTrackedRepo(repoId, input),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.trackedRepos }),
        queryClient.invalidateQueries({ queryKey: queryKeys.repos }),
        queryClient.invalidateQueries({ queryKey: queryKeys.repo(repoId) }),
      ]);
    },
  });
}

export function useDeleteTrackedRepo() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (repoId: string) => deleteTrackedRepo(repoId),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.trackedRepos }),
        queryClient.invalidateQueries({ queryKey: queryKeys.repos }),
      ]);
    },
  });
}
