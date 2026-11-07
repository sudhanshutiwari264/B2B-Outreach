"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ChevronLeft, Globe, LayoutGrid, Mail, Zap } from "lucide-react";
import { useExecutionData } from "@/lib/useExecutionData";
import { StatusBadge } from "@/components/StatusBadge";
import { Avatar } from "@/components/Avatar";
import { ErrorBanner, Skeleton } from "@/components/ui";
import { OverviewTab } from "@/components/execution/OverviewTab";
import { SourcesTab } from "@/components/execution/SourcesTab";
import { SignalsTab } from "@/components/execution/SignalsTab";
import { OutreachTab } from "@/components/execution/OutreachTab";
import { LiveStatusBanner } from "@/components/execution/LiveStatusBanner";

const TABS = [
  { key: "overview", label: "Overview", icon: LayoutGrid },
  { key: "sources", label: "Sources", icon: Globe },
  { key: "signals", label: "Signals", icon: Zap },
  { key: "outreach", label: "Outreach", icon: Mail },
] as const;

type TabKey = (typeof TABS)[number]["key"];

function isTabKey(value: string | null): value is TabKey {
  return TABS.some((t) => t.key === value);
}

function LoadingSkeleton() {
  return (
    <div>
      <Skeleton className="mb-2 h-4 w-32" />
      <Skeleton className="mb-6 h-7 w-64" />
      <Skeleton className="mb-6 h-16 w-full" />
      <div className="flex gap-2">
        <Skeleton className="h-9 w-24" />
        <Skeleton className="h-9 w-24" />
        <Skeleton className="h-9 w-24" />
      </div>
    </div>
  );
}

export default function ExecutionDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { execution, prospect, logs, sources, signals, drafts, loading, error } = useExecutionData(id);
  const searchParams = useSearchParams();
  const requestedTab = searchParams.get("tab");
  const [tab, setTab] = useState<TabKey>(isTabKey(requestedTab) ? requestedTab : "overview");

  if (loading && !execution) {
    return <LoadingSkeleton />;
  }

  if (error && !execution) {
    return <ErrorBanner message={error} />;
  }

  if (!execution) {
    return <ErrorBanner message="Execution not found." />;
  }

  const duration =
    execution.started_at && execution.completed_at
      ? formatDuration(new Date(execution.completed_at).getTime() - new Date(execution.started_at).getTime())
      : null;

  return (
    <div>
      <Link
        href="/executions"
        className="mb-3 inline-flex items-center gap-1 text-xs text-muted hover:text-accent"
      >
        <ChevronLeft className="h-3.5 w-3.5" /> Executions
      </Link>

      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <Avatar name={prospect?.name ?? "?"} size="lg" />
          <div className="min-w-0">
            <h1 className="truncate text-lg text-ink sm:text-xl">
              {prospect ? `${prospect.name} (${prospect.company})` : "Execution"}
            </h1>
            <p className="mt-0.5 truncate text-xs text-muted">
              <span className="font-outlier">{execution.id}</span>
              {duration && <span>, {duration}</span>}
            </p>
          </div>
        </div>
        <StatusBadge status={execution.status} />
      </div>

      <LiveStatusBanner
        execution={execution}
        logs={logs}
        sourceCount={sources.length}
        signalCount={signals.length}
      />

      <div className="mb-6 overflow-x-auto border-b border-rule">
        <div className="flex gap-1">
          {TABS.map((t) => {
            const Icon = t.icon;
            return (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`flex shrink-0 items-center gap-1.5 whitespace-nowrap border-b-2 px-3.5 py-2.5 text-sm font-medium transition-colors ${
                  tab === t.key ? "border-accent text-accent" : "border-transparent text-muted hover:text-ink"
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                {t.label}
                {t.key === "sources" && sources.length > 0 && (
                  <span className="font-outlier text-xs text-muted">({sources.length})</span>
                )}
                {t.key === "signals" && signals.length > 0 && (
                  <span className="font-outlier text-xs text-muted">({signals.length})</span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {tab === "overview" && (
        <OverviewTab execution={execution} logs={logs} signals={signals} sources={sources} />
      )}
      {tab === "sources" && <SourcesTab sources={sources} />}
      {tab === "signals" && <SignalsTab signals={signals} />}
      {tab === "outreach" && <OutreachTab drafts={drafts} signals={signals} execution={execution} />}
    </div>
  );
}

function formatDuration(ms: number): string {
  const seconds = Math.round(ms / 1000);
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
}
