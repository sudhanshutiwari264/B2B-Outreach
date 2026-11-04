"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useNeedsReviewCount } from "@/lib/useNeedsReviewCount";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: "▣" },
  { href: "/prospects", label: "Prospects", icon: "👤" },
  { href: "/prospects/new", label: "New Prospect", icon: "➕" },
  { href: "/executions", label: "Executions", icon: "▶" },
  { href: "/outreach", label: "Outreach", icon: "✉" },
] as const;

function isActive(pathname: string | null, href: string): boolean {
  if (href === "/") return pathname === "/";
  if (href === "/prospects") return pathname === "/prospects" || /^\/prospects\/[^/]+$/.test(pathname ?? "");
  return pathname?.startsWith(href) ?? false;
}

export function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const needsReviewCount = useNeedsReviewCount();

  return (
    <div className="flex h-full flex-col bg-[#0f1115] text-slate-200">
      <div className="flex items-center gap-2 px-5 py-5">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-accent text-sm font-semibold text-accent-foreground">
          G
        </div>
        <span className="text-sm font-semibold tracking-tight text-white">GTM Outreach</span>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-2">
        {NAV_ITEMS.map((item) => {
          const active = isActive(pathname, item.href);
          const showBadge = item.href === "/outreach" && !!needsReviewCount;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={`flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-colors ${
                active
                  ? "bg-white/10 font-medium text-white"
                  : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
              }`}
            >
              <span className="text-xs opacity-80">{item.icon}</span>
              <span className="flex-1">{item.label}</span>
              {showBadge && (
                <span className="rounded-full bg-accent px-1.5 py-0.5 text-[10px] font-semibold leading-none text-accent-foreground">
                  {needsReviewCount}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-white/10 px-3 py-3">
        <Link
          href="/status"
          onClick={onNavigate}
          className={`flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-colors ${
            pathname === "/status"
              ? "bg-white/10 font-medium text-white"
              : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
          }`}
        >
          <span className="text-xs opacity-80">●</span>
          System Status
        </Link>
      </div>

      <div className="border-t border-white/10 px-5 py-4 text-xs text-slate-500">
        Personalized Outreach
        <br />
        Intelligence Engine
      </div>
    </div>
  );
}

export function Sidebar() {
  return (
    <aside className="hidden h-full w-60 shrink-0 md:flex">
      <SidebarContent />
    </aside>
  );
}
