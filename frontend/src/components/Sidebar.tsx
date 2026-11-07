"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  LayoutDashboard,
  type LucideIcon,
  Mail,
  PlayCircle,
  UserPlus,
  Users,
} from "lucide-react";
import { useNeedsReviewCount } from "@/lib/useNeedsReviewCount";

const NAV_ITEMS: { href: string; label: string; icon: LucideIcon }[] = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/prospects", label: "Prospects", icon: Users },
  { href: "/prospects/new", label: "New prospect", icon: UserPlus },
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
      className={`group relative flex items-center gap-2.5 rounded-pill px-3 py-2 text-sm transition-colors duration-150 ${
        active ? "bg-paper-3 text-ink" : "text-muted hover:bg-paper-3 hover:text-ink"
      }`}
    >
      {active && <span className="absolute left-0 top-1/2 h-4 w-0.5 -translate-y-1/2 rounded-r-full bg-accent" />}
      <Icon className={`h-[17px] w-[17px] shrink-0 ${active ? "text-accent" : "text-muted"}`} strokeWidth={1.75} />
      <span className="flex-1">{label}</span>
      {!!badge && (
        <span className="rounded-[4px] border border-accent-soft bg-accent-soft px-1.5 py-0.5 text-[10px] font-medium leading-none text-accent">
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
    <div className="flex h-full flex-col bg-paper border-r border-rule">
      <div className="flex items-center gap-2.5 px-5 py-5">
        <span className="font-outlier text-sm text-accent">&gt;_</span>
        <span className="text-sm text-ink">GTM Outreach</span>
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

      <div className="border-t border-rule px-3 py-3">
        <NavLink
          href="/status"
          label="System status"
          icon={Activity}
          active={pathname === "/status"}
          onNavigate={onNavigate}
        />
      </div>

      <div className="border-t border-rule px-5 py-4 text-xs text-muted">
        Personalized outreach
        <br />
        intelligence engine
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
