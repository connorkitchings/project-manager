import clsx from "clsx";
import { NavLink, Outlet } from "react-router-dom";

const navigationItems = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/settings/repos", label: "Tracked repos" },
];

export function AppShell() {
  return (
    <div className="min-h-screen bg-transparent text-ink">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col px-4 py-6 sm:px-6 lg:px-8">
        <header className="mb-8 flex flex-col gap-4 rounded-[2rem] border border-white/70 bg-white/55 px-6 py-5 shadow-panel backdrop-blur md:flex-row md:items-end md:justify-between">
          <div className="max-w-2xl">
            <div className="mb-2 inline-flex items-center rounded-full border border-pine/15 bg-pine/10 px-3 py-1 font-mono text-xs uppercase tracking-[0.24em] text-pine">
              Repo status radar
            </div>
            <h1 className="text-3xl font-semibold sm:text-4xl">Project Manager</h1>
            <p className="mt-2 max-w-xl text-sm text-ink/75 sm:text-base">
              Documentation-first repo oversight with GitHub activity as
              evidence, not noise.
            </p>
          </div>
          <div className="rounded-[1.5rem] border border-ink/10 bg-base/70 px-4 py-3 text-sm text-ink/75">
            Single-user internal dashboard for curated repositories.
          </div>
        </header>
        <nav className="mb-6 flex flex-wrap gap-2">
          {navigationItems.map((item) => (
            <NavLink
              className={({ isActive }) =>
                clsx(
                  "rounded-full border px-4 py-2 text-sm transition",
                  isActive
                    ? "border-pine bg-pine text-white"
                    : "border-white/80 bg-white/65 text-ink/70 hover:border-pine/25 hover:text-pine",
                )
              }
              end={item.end}
              key={item.to}
              to={item.to}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <main className="flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
