"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { HealthIntegrations } from "@/lib/types";
import { Button, Card, PageHeader, Spinner } from "@/components/ui";

type CheckState = "checking" | "ok" | "degraded" | "down";

function StatusDot({ state }: { state: CheckState }) {
  const color =
    state === "ok"
      ? "bg-success"
      : state === "degraded"
        ? "bg-warning"
        : state === "down"
          ? "bg-danger"
          : "bg-muted";
  return <span className={`inline-block h-2.5 w-2.5 shrink-0 rounded-full ${color}`} />;
}

function StatusCard({
  title,
  state,
  details,
}: {
  title: string;
  state: CheckState;
  details: { label: string; value: string }[];
}) {
  return (
    <Card className="p-5">
      <div className="mb-3 flex items-center gap-2.5">
        <StatusDot state={state} />
        <h3 className="text-sm font-semibold text-foreground">{title}</h3>
        <span className="ml-auto text-xs font-medium uppercase tracking-wide text-muted">
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
        action={
          <Button variant="secondary" onClick={refresh} disabled={loading}>
            {loading ? <Spinner /> : "↻"} Refresh
          </Button>
        }
      />

      {apiError && (
        <Card className="mb-6 border-danger/30 bg-danger-soft p-4">
          <p className="text-sm text-danger">{apiError}</p>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatusCard
          title="Backend / Database"
          state={backendState}
          details={[{ label: "Postgres", value: dbOk == null ? "unknown" : dbOk ? "connected" : "unreachable" }]}
        />
        <StatusCard
          title="Tavily"
          state={tavilyState}
          details={[
            { label: "Configured", value: integrations ? String(integrations.tavily.configured) : "…" },
            { label: "Reachable", value: integrations?.tavily.reachable != null ? String(integrations.tavily.reachable) : "…" },
            ...(integrations?.tavily.error ? [{ label: "Error", value: integrations.tavily.error }] : []),
          ]}
        />
        <StatusCard
          title="Tarqa AI"
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
