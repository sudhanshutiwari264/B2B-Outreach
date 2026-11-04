"use client";

import { useState } from "react";
import { usePathname } from "next/navigation";
import { Menu, Sparkles } from "lucide-react";
import { Sidebar, SidebarContent } from "./Sidebar";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const pathname = usePathname();

  // Close the mobile drawer automatically whenever the route changes. Adjusted during
  // render (not an effect) per React's documented pattern for resetting state in
  // response to a changing value - avoids an extra render pass.
  const [lastPathname, setLastPathname] = useState(pathname);
  if (pathname !== lastPathname) {
    setLastPathname(pathname);
    setDrawerOpen(false);
  }

  return (
    <div className="flex h-full min-h-screen bg-background text-foreground">
      <Sidebar />

      {drawerOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <button
            aria-label="Close menu"
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setDrawerOpen(false)}
          />
          <div className="relative h-full w-64 max-w-[80vw] shadow-[var(--shadow-lg)] animate-[fadein_0.15s_ease-out]">
            <SidebarContent onNavigate={() => setDrawerOpen(false)} />
          </div>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-3 border-b border-border bg-surface/80 px-4 py-3 backdrop-blur-sm md:hidden">
          <button
            aria-label="Open menu"
            onClick={() => setDrawerOpen(true)}
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-border text-foreground transition-colors hover:bg-surface-muted"
          >
            <Menu className="h-4 w-4" strokeWidth={2} />
          </button>
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-gradient-to-br from-accent to-indigo-800">
              <Sparkles className="h-3.5 w-3.5 text-white" strokeWidth={2.25} />
            </div>
            <span className="text-sm font-semibold tracking-tight text-foreground">GTM Outreach</span>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-6xl px-4 py-5 sm:px-6 lg:px-8 lg:py-8">{children}</div>
        </main>
      </div>
    </div>
  );
}
