import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import { AppShell } from "@/app/shell";
import { DashboardPage } from "@/features/repos/dashboard-page";
import { RepoDetailPage } from "@/features/repos/repo-detail-page";
import { RepoSettingsPage } from "@/features/repos/repo-settings-page";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30_000,
    },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/repos/:repoId" element={<RepoDetailPage />} />
            <Route path="/settings/repos" element={<RepoSettingsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
