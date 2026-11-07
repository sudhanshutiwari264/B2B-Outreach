"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Play, Search, Users } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import type { Prospect } from "@/lib/types";
import { Button, Card, EmptyState, ErrorBanner, TableScroll } from "@/components/ui";
import { Avatar } from "@/components/Avatar";

export interface ProspectRow {
  prospect: Prospect;
  executionCount: number;
}

export function ProspectsList({ rows }: { rows: ProspectRow[] }) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [runningId, setRunningId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const filtered = rows.filter(({ prospect }) => {
    const haystack = `${prospect.name} ${prospect.company} ${prospect.designation}`.toLowerCase();
    return haystack.includes(query.trim().toLowerCase());
  });

  async function handleRunResearch(prospectId: string) {
    setRunningId(prospectId);
    setError(null);
    try {
      const run = await api.runResearch(prospectId);
      router.push(`/executions/${run.execution_id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to start research");
      setRunningId(null);
    }
  }

  return (
    <div>
      <div className="relative mb-4 max-w-sm">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by name, company, or title…"
          className="h-9 w-full rounded-pill border border-rule-2 bg-paper-2 py-2 pl-9 pr-3 text-sm outline-none transition-colors focus:border-accent focus:ring-1 focus:ring-focus"
        />
      </div>

      {error && (
        <div className="mb-4">
          <ErrorBanner message={error} />
        </div>
      )}

      {filtered.length === 0 ? (
        <EmptyState
          title={rows.length === 0 ? "No prospects yet" : "No matches"}
          description={
            rows.length === 0
              ? "Add your first prospect to start researching."
              : "Try a different search term."
          }
          icon={Users}
        />
      ) : (
        <Card>
          <TableScroll minWidth={680}>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-rule text-left text-sm text-muted">
                  <th className="px-4 py-3 font-medium sm:px-5">Name</th>
                  <th className="px-4 py-3 font-medium sm:px-5">Company</th>
                  <th className="px-4 py-3 font-medium sm:px-5">Title</th>
                  <th className="px-4 py-3 font-medium sm:px-5">Executions</th>
                  <th className="px-4 py-3 font-medium sm:px-5"></th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(({ prospect, executionCount }) => (
                  <tr
                    key={prospect.id}
                    className="border-b border-rule transition-colors last:border-0 hover:bg-paper-3"
                  >
                    <td className="px-4 py-3 sm:px-5">
                      <Link
                        href={`/prospects/${prospect.id}`}
                        className="flex items-center gap-2.5 font-medium text-ink hover:text-accent"
                      >
                        <Avatar name={prospect.name} size="sm" />
                        {prospect.name}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-muted sm:px-5">{prospect.company}</td>
                    <td className="px-4 py-3 text-muted sm:px-5">{prospect.designation}</td>
                    <td className="px-4 py-3 font-outlier text-muted tabular-nums sm:px-5">
                      {executionCount}
                    </td>
                    <td className="px-4 py-3 text-right sm:px-5">
                      <Button
                        variant="secondary"
                        loading={runningId === prospect.id}
                        onClick={() => handleRunResearch(prospect.id)}
                      >
                        {runningId !== prospect.id && <Play className="h-3.5 w-3.5" />}
                        {runningId === prospect.id ? "Starting" : "Research"}
                      </Button>
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
