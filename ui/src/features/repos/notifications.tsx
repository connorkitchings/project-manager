import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type PropsWithChildren,
} from "react";

import { useMeta, useRepos } from "@/features/repos/hooks";
import type { SyncRun } from "@/lib/api/types";

interface Toast {
  id: number;
  message: string;
  variant: "success" | "warning" | "error";
}

interface ToastContextValue {
  toasts: Toast[];
  addToast: (message: string, variant?: Toast["variant"]) => void;
  dismiss: (id: number) => void;
}

const ToastContext = createContext<ToastContextValue>({
  toasts: [],
  addToast: () => {},
  dismiss: () => {},
});

export function useToast() {
  return useContext(ToastContext);
}

let nextId = 0;

export function ToastProvider({ children }: PropsWithChildren) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const timers = useRef<Map<number, ReturnType<typeof setTimeout>>>(
    new Map(),
  );

  const dismiss = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
    const timer = timers.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timers.current.delete(id);
    }
  }, []);

  const addToast = useCallback(
    (message: string, variant: Toast["variant"] = "success") => {
      const id = nextId++;
      setToasts((prev) => [...prev.slice(-4), { id, message, variant }]);
      const timer = setTimeout(() => dismiss(id), 5_000);
      timers.current.set(id, timer);
    },
    [dismiss],
  );

  return (
    <ToastContext.Provider value={{ toasts, addToast, dismiss }}>
      {children}
    </ToastContext.Provider>
  );
}

export function SyncNotificationWatcher() {
  const metaQuery = useMeta();
  const reposQuery = useRepos();
  const { addToast } = useToast();
  const lastSyncFinishedAt = useRef<string | null>(null);

  const syncRun: SyncRun | null | undefined =
    metaQuery.data?.latest_sync_run;
  const schedulerRunning = metaQuery.data?.scheduler?.running ?? false;

  useEffect(() => {
    if (!schedulerRunning || !syncRun?.finished_at) return;

    if (
      lastSyncFinishedAt.current &&
      lastSyncFinishedAt.current !== syncRun.finished_at
    ) {
      const { synced_count, failed_count } = syncRun;
      if (failed_count > 0) {
        addToast(
          `Sync completed: ${synced_count} synced, ${failed_count} failed`,
          "warning",
        );
      } else {
        addToast(`Sync completed: ${synced_count} repos updated`, "success");
      }

      const prevRepos = reposQuery.data;
      if (prevRepos) {
        const attentionCount = prevRepos.filter(
          (r) => r.status === "stalled" || r.status === "blocked" || r.status === "error",
        ).length;
        if (attentionCount > 0) {
          addToast(
            `${attentionCount} repo${attentionCount > 1 ? "s" : ""} need attention`,
            "warning",
          );
        }
      }
    }

    lastSyncFinishedAt.current = syncRun.finished_at;
  }, [schedulerRunning, syncRun, addToast, reposQuery.data]);

  return null;
}

export function ToastContainer() {
  const { toasts, dismiss } = useToast();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2">
      {toasts.map((toast) => (
        <button
          className={`
            rounded-2xl border px-5 py-3 text-sm font-medium shadow-lg backdrop-blur transition
            ${toast.variant === "success" ? "border-pine/20 bg-pine/90 text-white" : ""}
            ${toast.variant === "warning" ? "border-attention/20 bg-attention/90 text-ink" : ""}
            ${toast.variant === "error" ? "border-danger/20 bg-danger/90 text-white" : ""}
          `}
          key={toast.id}
          onClick={() => dismiss(toast.id)}
          type="button"
        >
          {toast.message}
        </button>
      ))}
    </div>
  );
}
