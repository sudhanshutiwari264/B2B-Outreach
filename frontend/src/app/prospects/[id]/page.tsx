"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { Execution, Prospect } from "@/lib/types";
import { Button, Card, EmptyState, ErrorBanner, PageHeader, Spinner, TableScroll } from "@/components/ui";
import { StatusBadge } from "@/components/StatusBadge";

function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  if (!value) return null;
  return (
    <div className="flex flex-col gap-0.5 sm:flex-row sm:gap-2">
      <span className="w-36 shrink-0 text-xs font-medium uppercase tracking-wide text-muted">{label}</span>
      <span className="text-sm text-foreground">{value}</span>
    </div>
  );
}

export default function ProspectDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const [prospect, setProspect] = useState<Prospect | null>(null);
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [p, execs] = await Promise.all([api.getProspect(id), api.listExecutions(100, id)]);
        if (!cancelled) {
          setProspect(p);
          setExecutions(execs);
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Failed to load prospect");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [id]);

  async function handleRunResearch() {
    setRunning(true);
    setError(null);
    try {
      const run = await api.runResearch(id);
      router.push(`/executions/${run.execution_id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to start research");
      setRunning(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted">
        <Spinner /> Loading prospect…
      </div>
    );
  }

  if (!prospect) {
    return <ErrorBanner message={error ?? "Prospect not found."} />;
  }

  const sortedExecutions = [...executions].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  return (
    <div>
      <div className="mb-1 text-xs text-muted">
        <Link href="/prospects" className="hover:text-accent">
          Prospects
        </Link>{" "}
        / {prospect.name}
      </div>

      <PageHeader
        title={prospect.name}
        description={`${prospect.designation} at ${prospect.company}`}
        action={
          <Button onClick={handleRunResearch} disabled={running}>
            {running ? "Starting…" : "▶ Run Research"}
          </Button>
        }
      />

      {error && (
        <div className="mb-4">
          <ErrorBanner message={error} />
        </div>
      )}

      <Card className="mb-6 space-y-2.5 p-4 sm:p-5">
        <InfoRow label="Company" value={prospect.company} />
        <InfoRow label="Designation" value={prospect.designation} />
        <InfoRow label="Industry" value={prospect.industry} />
        <InfoRow
          label="LinkedIn"
          value={
            prospect.linkedin_url && (
              <a href={prospect.linkedin_url} target="_blank" rel="noreferrer" className="text-accent hover:underline">
                {prospect.linkedin_url}
              </a>
            )
          }
        />
        <InfoRow
          label="Website"
          value={
            prospect.company_website && (
              <a href={prospect.company_website} target="_blank" rel="noreferrer" className="text-accent hover:underline">
                {prospect.company_website}
              </a>
            )
          }
        />
        <InfoRow label="Outreach channel" value={prospect.outreach_channel} />
        <InfoRow label="Product context" value={prospect.product_context} />
      </Card>

      <h2 className="mb-3 text-sm font-semibold text-foreground">Execution History</h2>
      {sortedExecutions.length === 0 ? (
        <EmptyState
          title="No research runs yet"
          description="Click Run Research above to kick off the first one."
        />
      ) : (
        <Card>
          <TableScroll minWidth={480}>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted">
                  <th className="px-4 py-3 font-medium sm:px-5">Started</th>
                  <th className="px-4 py-3 font-medium sm:px-5">Status</th>
                  <th className="px-4 py-3 font-medium sm:px-5"></th>
                </tr>
              </thead>
              <tbody>
                {sortedExecutions.map((execution) => (
                  <tr key={execution.id} className="border-b border-border last:border-0">
                    <td className="px-4 py-3 text-muted sm:px-5">
                      {new Date(execution.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 sm:px-5">
                      <StatusBadge status={execution.status} />
                    </td>
                    <td className="px-4 py-3 text-right sm:px-5">
                      <Link
                        href={`/executions/${execution.id}`}
                        className="text-sm font-medium text-accent hover:underline"
                      >
                        View Details
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </TableScroll>
        </Card>
      )}
    </div>
  );
}
