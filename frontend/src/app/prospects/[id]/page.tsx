"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Briefcase,
  Building2,
  ChevronLeft,
  ChevronRight,
  FileText,
  Globe,
  History,
  Link2,
  Play,
  Send,
} from "lucide-react";
import { api, ApiError } from "@/lib/api";
import type { Execution, Prospect } from "@/lib/types";
import { Button, Card, EmptyState, ErrorBanner, Skeleton, TableScroll } from "@/components/ui";
import { StatusBadge } from "@/components/StatusBadge";
import { Avatar } from "@/components/Avatar";

function InfoRow({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Building2;
  label: string;
  value: React.ReactNode;
}) {
  if (!value) return null;
  return (
    <div className="flex items-start gap-3 py-2">
      <Icon className="mt-0.5 h-4 w-4 shrink-0 text-muted" strokeWidth={2} />
      <div className="min-w-0">
        <div className="text-xs font-medium uppercase tracking-wide text-muted">{label}</div>
        <div className="mt-0.5 text-sm text-foreground">{value}</div>
      </div>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div>
      <Skeleton className="mb-4 h-4 w-28" />
      <div className="mb-6 flex items-center gap-3">
        <Skeleton className="h-12 w-12 rounded-full" />
        <div>
          <Skeleton className="mb-2 h-6 w-48" />
          <Skeleton className="h-4 w-32" />
        </div>
      </div>
      <Skeleton className="h-40 w-full" />
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
    return <LoadingSkeleton />;
  }

  if (!prospect) {
    return <ErrorBanner message={error ?? "Prospect not found."} />;
  }

  const sortedExecutions = [...executions].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  return (
    <div>
      <Link
        href="/prospects"
        className="mb-3 inline-flex items-center gap-1 text-xs text-muted hover:text-accent"
      >
        <ChevronLeft className="h-3.5 w-3.5" /> Prospects
      </Link>

      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-center gap-3">
          <Avatar name={prospect.name} size="lg" />
          <div>
            <h1 className="text-lg font-semibold tracking-tight text-foreground sm:text-xl">
              {prospect.name}
            </h1>
            <p className="mt-0.5 text-sm text-muted">
              {prospect.designation} at {prospect.company}
            </p>
          </div>
        </div>
        <Button onClick={handleRunResearch} loading={running} className="shrink-0">
          {!running && <Play className="h-4 w-4" />} Run Research
        </Button>
      </div>

      {error && (
        <div className="mb-4">
          <ErrorBanner message={error} />
        </div>
      )}

      <Card className="mb-6 divide-y divide-border p-4 sm:p-5">
        <InfoRow icon={Building2} label="Company" value={prospect.company} />
        <InfoRow icon={Briefcase} label="Designation" value={prospect.designation} />
        <InfoRow icon={Building2} label="Industry" value={prospect.industry} />
        <InfoRow
          icon={Link2}
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
          icon={Globe}
          label="Website"
          value={
            prospect.company_website && (
              <a href={prospect.company_website} target="_blank" rel="noreferrer" className="text-accent hover:underline">
                {prospect.company_website}
              </a>
            )
          }
        />
        <InfoRow icon={Send} label="Outreach channel" value={prospect.outreach_channel} />
        <InfoRow icon={FileText} label="Product context" value={prospect.product_context} />
      </Card>

      <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-foreground">
        <History className="h-4 w-4 text-muted" /> Execution History
      </h2>
      {sortedExecutions.length === 0 ? (
        <EmptyState
          title="No research runs yet"
          description="Click Run Research above to kick off the first one."
          icon={History}
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
                  <tr
                    key={execution.id}
                    className="border-b border-border transition-colors last:border-0 hover:bg-surface-muted/60"
                  >
                    <td className="px-4 py-3 text-muted sm:px-5">
                      {new Date(execution.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 sm:px-5">
                      <StatusBadge status={execution.status} />
                    </td>
                    <td className="px-4 py-3 text-right sm:px-5">
                      <Link
                        href={`/executions/${execution.id}`}
                        className="inline-flex items-center gap-0.5 text-sm font-medium text-accent hover:underline"
                      >
                        View Details <ChevronRight className="h-3.5 w-3.5" />
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
