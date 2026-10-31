"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: "▣" },
  { href: "/prospects/new", label: "New Prospect", icon: "➕" },
  { href: "/executions", label: "Executions", icon: "▶" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-full w-60 shrink-0 flex-col bg-[#0f1115] text-slate-200">
      <div className="flex items-center gap-2 px-5 py-5">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-accent text-sm font-semibold text-accent-foreground">
          G
        </div>
        <span className="text-sm font-semibold tracking-tight text-white">GTM Outreach</span>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-2">
        {NAV_ITEMS.map((item) => {
          const active = item.href === "/" ? pathname === "/" : pathname?.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-colors ${
                active
                  ? "bg-white/10 font-medium text-white"
                  : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
              }`}
            >
              <span className="text-xs opacity-80">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-white/10 px-5 py-4 text-xs text-slate-500">
        Personalized Outreach
        <br />
        Intelligence Engine
      </div>
    </aside>
  );
}
