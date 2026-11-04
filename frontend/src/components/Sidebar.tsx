"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  LayoutDashboard,
  type LucideIcon,
  Mail,
  PlayCircle,
  Sparkles,
  UserPlus,
  Users,
} from "lucide-react";
import { useNeedsReviewCount } from "@/lib/useNeedsReviewCount";

const NAV_ITEMS: { href: string; label: string; icon: LucideIcon }[] = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/prospects", label: "Prospects", icon: Users },
  { href: "/prospects/new", label: "New Prospect", icon: UserPlus },
  { href: "/executions", label: "Executions", icon: PlayCircle },
  { href: "/outreach", label: "Outreach", icon: Mail },
];

function isActive(pathname: string | null, href: string): boolean {
  if (href === "/") return pathname === "/";
  if (href === "/prospects") return pathname === "/prospects" || /^\/prospects\/[^/]+$/.test(pathname ?? "");
  return pathname?.startsWith(href) ?? false;
}

function NavLink({
  href,
  label,
  icon: Icon,
  active,
  onNavigate,
  badge,
}: {
  href: string;
  label: string;
  icon: LucideIcon;
  active: boolean;
  onNavigate?: () => void;
  badge?: number;
}) {
  return (
    <Link
      href={href}
      onClick={onNavigate}
      className={`group relative flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-all duration-150 ${
        active ? "bg-white/[0.08] font-medium text-white" : "text-slate-400 hover:bg-white/[0.04] hover:text-slate-200"
      }`}
    >
      {active && (
        <span className="absolute left-0 top-1/2 h-4 w-0.5 -translate-y-1/2 rounded-r-full bg-accent" />
      )}
      <Icon
        className={`h-[17px] w-[17px] shrink-0 transition-colors ${active ? "text-accent" : "text-slate-500 group-hover:text-slate-300"}`}
        strokeWidth={2}
      />
      <span className="flex-1">{label}</span>
      {!!badge && (
        <span className="rounded-full bg-accent px-1.5 py-0.5 text-[10px] font-semibold leading-none text-accent-foreground">
          {badge}
        </span>
      )}
    </Link>
  );
}

export function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const needsReviewCount = useNeedsReviewCount();

  return (
    <div className="flex h-full flex-col bg-[#0b0c10] text-slate-200">
      <div className="flex items-center gap-2.5 px-5 py-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-accent to-indigo-800 shadow-[var(--shadow-sm)]">
          <Sparkles className="h-4 w-4 text-white" strokeWidth={2.25} />
        </div>
        <span className="text-sm font-semibold tracking-tight text-white">GTM Outreach</span>
      </div>

      <nav className="flex-1 space-y-0.5 px-3 py-2">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.href}
            href={item.href}
            label={item.label}
            icon={item.icon}
            active={isActive(pathname, item.href)}
            onNavigate={onNavigate}
            badge={item.href === "/outreach" ? needsReviewCount ?? 0 : undefined}
          />
        ))}
      </nav>

      <div className="border-t border-white/[0.06] px-3 py-3">
        <NavLink
          href="/status"
          label="System Status"
          icon={Activity}
          active={pathname === "/status"}
          onNavigate={onNavigate}
        />
      </div>

      <div className="border-t border-white/[0.06] px-5 py-4 text-xs text-slate-500">
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
