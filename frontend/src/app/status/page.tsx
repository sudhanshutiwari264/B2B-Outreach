"use client";

import { useCallback, useEffect, useState } from "react";
import { Activity, Bot, Database, type LucideIcon, RefreshCw, Search } from "lucide-react";
import { api } from "@/lib/api";
import type { HealthIntegrations } from "@/lib/types";
import { Button, Card, ErrorBanner, PageHeader } from "@/components/ui";

type CheckState = "checking" | "ok" | "degraded" | "down";

const STATE_STYLES: Record<CheckState, { dot: string; text: string }> = {
  checking: { dot: "bg-muted", text: "text-muted" },
  ok: { dot: "bg-success", text: "text-success" },
  degraded: { dot: "bg-warning", text: "text-warning" },
  down: { dot: "bg-danger", text: "text-danger" },
};

function StatusCard({
  title,
  icon: Icon,
  state,
  details,
}: {
  title: string;
  icon: LucideIcon;
  state: CheckState;
  details: { label: string; value: string }[];
}) {
  const style = STATE_STYLES[state];
  return (
    <Card className="p-5">
      <div className="mb-3 flex items-center gap-2.5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-surface-muted text-muted">
          <Icon className="h-4 w-4" strokeWidth={2} />
        </div>
        <h3 className="text-sm font-semibold text-foreground">{title}</h3>
        <span className={`ml-auto flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide ${style.text}`}>
          <span className={`h-1.5 w-1.5 rounded-full ${style.dot} ${state === "checking" ? "animate-pulse" : ""}`} />
          {state === "checking" ? "Checking…" : state}
        </span>
      </div>
      <dl className="space-y-1.5">
        {details.map((d) => (
          <div key={d.label} className="flex justify-between gap-4 text-sm">
            <dt className="text-muted">{d.label}</dt>
            <dd className="truncate text-right text-foreground">{d.value}</dd>
          </div>
        ))}
      </dl>
    </Card>
  );
}

export default function StatusPage() {
  const [loading, setLoading] = useState(true);
  const [checkedAt, setCheckedAt] = useState<Date | null>(null);
  const [dbOk, setDbOk] = useState<boolean | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const [integrations, setIntegrations] = useState<HealthIntegrations | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setApiError(null);
    try {
      const [health, integ] = await Promise.all([api.health(), api.healthIntegrations()]);
      setDbOk(health.database);
      setIntegrations(integ);
    } catch {
      setApiError(
        "Could not reach the backend at all. If this is the first request in a while, the server may be waking up from a cold start — try again in 15-30 seconds."
      );
      setDbOk(null);
      setIntegrations(null);
    } finally {
      setLoading(false);
      setCheckedAt(new Date());
    }
  }, []);

  useEffect(() => {
    // Intentional fetch-on-mount; no external subscription API to sync to instead.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh();
  }, [refresh]);

  const backendState: CheckState = apiError ? "down" : loading ? "checking" : dbOk ? "ok" : "degraded";
  const tavilyState: CheckState = !integrations
    ? "checking"
    : !integrations.tavily.configured
      ? "down"
      : integrations.tavily.reachable
        ? "ok"
        : "degraded";
  const tarqaState: CheckState = !integrations
    ? "checking"
    : !integrations.tarqa.configured
      ? "down"
      : integrations.tarqa.reachable
        ? "ok"
        : "degraded";

  return (
    <div>
      <PageHeader
        title="System Status"
        description="Live connectivity to the database, Tavily, and Tarqa AI."
        icon={Activity}
        action={
          <Button variant="secondary" onClick={refresh} loading={loading}>
            {!loading && <RefreshCw className="h-3.5 w-3.5" />} Refresh
          </Button>
        }
      />

      {apiError && (
        <div className="mb-6">
          <ErrorBanner message={apiError} />
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatusCard
          title="Backend / Database"
          icon={Database}
          state={backendState}
          details={[{ label: "Postgres", value: dbOk == null ? "unknown" : dbOk ? "connected" : "unreachable" }]}
        />
        <StatusCard
          title="Tavily"
          icon={Search}
          state={tavilyState}
          details={[
            { label: "Configured", value: integrations ? String(integrations.tavily.configured) : "…" },
            { label: "Reachable", value: integrations?.tavily.reachable != null ? String(integrations.tavily.reachable) : "…" },
            ...(integrations?.tavily.error ? [{ label: "Error", value: integrations.tavily.error }] : []),
          ]}
        />
        <StatusCard
          title="Tarqa AI"
          icon={Bot}
          state={tarqaState}
          details={[
            { label: "Configured", value: integrations ? String(integrations.tarqa.configured) : "…" },
            { label: "Reachable", value: integrations?.tarqa.reachable != null ? String(integrations.tarqa.reachable) : "…" },
            { label: "Model", value: integrations?.tarqa.model ?? "…" },
            ...(integrations?.tarqa.error ? [{ label: "Error", value: integrations.tarqa.error }] : []),
          ]}
        />
      </div>

      {checkedAt && (
        <p className="mt-6 text-xs text-muted">Last checked {checkedAt.toLocaleTimeString()}</p>
      )}
    </div>
  );
}
