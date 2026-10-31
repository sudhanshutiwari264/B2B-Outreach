import Link from "next/link";
import { api } from "@/lib/api";
import { Card, EmptyState, LinkButton, PageHeader } from "@/components/ui";
import { StatusBadge } from "@/components/StatusBadge";

export default async function ExecutionsPage() {
  const [prospects, executions] = await Promise.all([
    api.listProspects(500).catch(() => []),
    api.listExecutions(500).catch(() => []),
  ]);
  const prospectById = new Map(prospects.map((p) => [p.id, p]));

  const sorted = [...executions].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  return (
    <div>
      <PageHeader
        title="Execution History"
        description="Track all past research executions, statuses, and outcomes."
        action={<LinkButton href="/prospects/new">+ New Prospect</LinkButton>}
      />

      {sorted.length === 0 ? (
        <EmptyState
          title="No executions yet"
          description="Add a prospect and start a research run to see it here."
        />
      ) : (
        <Card>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted">
                <th className="px-5 py-3 font-medium">Prospect</th>
                <th className="px-5 py-3 font-medium">Company</th>
                <th className="px-5 py-3 font-medium">Started</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((execution) => {
                const prospect = prospectById.get(execution.prospect_id);
                return (
                  <tr key={execution.id} className="border-b border-border last:border-0">
                    <td className="px-5 py-3 font-medium text-foreground">
                      {prospect?.name ?? "Unknown prospect"}
                    </td>
                    <td className="px-5 py-3 text-muted">{prospect?.company ?? "—"}</td>
                    <td className="px-5 py-3 text-muted">
                      {new Date(execution.created_at).toLocaleString()}
                    </td>
                    <td className="px-5 py-3">
                      <StatusBadge status={execution.status} />
                    </td>
                    <td className="px-5 py-3 text-right">
                      <Link href={`/executions/${execution.id}`} className="text-sm font-medium text-accent hover:underline">
                        View Details
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
