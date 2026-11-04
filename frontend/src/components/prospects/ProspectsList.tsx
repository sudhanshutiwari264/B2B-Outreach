"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import type { Prospect } from "@/lib/types";
import { Card, EmptyState, ErrorBanner, TableScroll } from "@/components/ui";

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
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search by name, company, or title…"
        className="mb-4 w-full max-w-sm rounded-md border border-border bg-surface px-3 py-2 text-sm outline-none focus:border-accent focus:ring-1 focus:ring-accent"
      />

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
        />
      ) : (
        <Card>
          <TableScroll minWidth={680}>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted">
                  <th className="px-4 py-3 font-medium sm:px-5">Name</th>
                  <th className="px-4 py-3 font-medium sm:px-5">Company</th>
                  <th className="px-4 py-3 font-medium sm:px-5">Title</th>
                  <th className="px-4 py-3 font-medium sm:px-5">Executions</th>
                  <th className="px-4 py-3 font-medium sm:px-5"></th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(({ prospect, executionCount }) => (
                  <tr key={prospect.id} className="border-b border-border last:border-0">
                    <td className="px-4 py-3 sm:px-5">
                      <Link
                        href={`/prospects/${prospect.id}`}
                        className="font-medium text-foreground hover:text-accent"
                      >
                        {prospect.name}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-muted sm:px-5">{prospect.company}</td>
                    <td className="px-4 py-3 text-muted sm:px-5">{prospect.designation}</td>
                    <td className="px-4 py-3 text-muted sm:px-5">{executionCount}</td>
                    <td className="px-4 py-3 text-right sm:px-5">
                      <button
                        onClick={() => handleRunResearch(prospect.id)}
                        disabled={runningId === prospect.id}
                        className="text-sm font-medium text-accent hover:underline disabled:opacity-50"
                      >
                        {runningId === prospect.id ? "Starting…" : "Run Research"}
                      </button>
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
