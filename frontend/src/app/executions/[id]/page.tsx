"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useExecutionData } from "@/lib/useExecutionData";
import { StatusBadge } from "@/components/StatusBadge";
import { ErrorBanner, Spinner } from "@/components/ui";
import { OverviewTab } from "@/components/execution/OverviewTab";
import { SourcesTab } from "@/components/execution/SourcesTab";
import { SignalsTab } from "@/components/execution/SignalsTab";
import { OutreachTab } from "@/components/execution/OutreachTab";
import { LiveStatusBanner } from "@/components/execution/LiveStatusBanner";

const TABS = [
  { key: "overview", label: "Overview" },
  { key: "sources", label: "Sources" },
  { key: "signals", label: "Signals" },
  { key: "outreach", label: "Outreach" },
] as const;

type TabKey = (typeof TABS)[number]["key"];

function isTabKey(value: string | null): value is TabKey {
  return TABS.some((t) => t.key === value);
}

export default function ExecutionDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { execution, prospect, logs, sources, signals, drafts, loading, error } = useExecutionData(id);
  const searchParams = useSearchParams();
  const requestedTab = searchParams.get("tab");
  const [tab, setTab] = useState<TabKey>(isTabKey(requestedTab) ? requestedTab : "overview");

  if (loading && !execution) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted">
        <Spinner /> Loading execution…
      </div>
    );
  }

  if (error && !execution) {
    return <ErrorBanner message={error} />;
  }

  if (!execution) {
    return <ErrorBanner message="Execution not found." />;
  }

  return (
    <div>
      <div className="mb-1 text-xs text-muted">
        <Link href="/executions" className="hover:text-accent">
          Executions
        </Link>{" "}
        / {execution.id.slice(0, 8)}
      </div>

      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="truncate text-lg font-semibold tracking-tight text-foreground sm:text-xl">
            {prospect ? `${prospect.name} — ${prospect.company}` : "Execution"}
          </h1>
          <p className="mt-1 truncate text-xs text-muted">
            Execution ID: {execution.id}
            {execution.started_at && execution.completed_at && (
              <>
                {" "}
                · Duration:{" "}
                {formatDuration(
                  new Date(execution.completed_at).getTime() - new Date(execution.started_at).getTime()
                )}
              </>
            )}
          </p>
        </div>
        <StatusBadge status={execution.status} />
      </div>

      <LiveStatusBanner
        execution={execution}
        logs={logs}
        sourceCount={sources.length}
        signalCount={signals.length}
      />

      <div className="mb-6 overflow-x-auto border-b border-border">
        <div className="flex gap-1">
          {TABS.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`shrink-0 whitespace-nowrap border-b-2 px-3.5 py-2.5 text-sm font-medium transition-colors ${
                tab === t.key
                  ? "border-accent text-accent"
                  : "border-transparent text-muted hover:text-foreground"
              }`}
            >
              {t.label}
              {t.key === "sources" && sources.length > 0 && (
                <span className="ml-1.5 text-xs text-muted">({sources.length})</span>
              )}
              {t.key === "signals" && signals.length > 0 && (
                <span className="ml-1.5 text-xs text-muted">({signals.length})</span>
              )}
            </button>
          ))}
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
