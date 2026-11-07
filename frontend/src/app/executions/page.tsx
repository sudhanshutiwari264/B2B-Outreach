import Link from "next/link";
import { ChevronRight, PlayCircle, UserPlus } from "lucide-react";
import { api } from "@/lib/api";
import { Card, EmptyState, LinkButton, PageHeader, TableScroll } from "@/components/ui";
import { StatusBadge } from "@/components/StatusBadge";
import { Avatar } from "@/components/Avatar";

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
        title="Execution history"
        description="Track all past research executions, statuses, and outcomes."
        icon={PlayCircle}
        action={
          <LinkButton href="/prospects/new">
            <UserPlus className="h-4 w-4" /> New prospect
          </LinkButton>
        }
      />

      {sorted.length === 0 ? (
        <EmptyState
          title="No executions yet"
          description="Add a prospect and start a research run to see it here."
          icon={PlayCircle}
        />
      ) : (
        <Card>
          <TableScroll minWidth={640}>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-rule text-left text-sm text-muted">
                  <th className="px-4 py-3 font-medium sm:px-5">Prospect</th>
                  <th className="px-4 py-3 font-medium sm:px-5">Company</th>
                  <th className="px-4 py-3 font-medium sm:px-5">Started</th>
                  <th className="px-4 py-3 font-medium sm:px-5">Status</th>
                  <th className="px-4 py-3 font-medium sm:px-5"></th>
                </tr>
              </thead>
              <tbody>
                {sorted.map((execution) => {
                  const prospect = prospectById.get(execution.prospect_id);
                  return (
                    <tr
                      key={execution.id}
                      className="border-b border-rule transition-colors last:border-0 hover:bg-paper-3"
                    >
                      <td className="px-4 py-3 sm:px-5">
                        <div className="flex items-center gap-2.5 font-medium text-ink">
                          <Avatar name={prospect?.name ?? "?"} size="sm" />
                          {prospect?.name ?? "Unknown prospect"}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-muted sm:px-5">{prospect?.company ?? "Unknown"}</td>
                      <td className="px-4 py-3 font-outlier text-muted tabular-nums sm:px-5">
                        {new Date(execution.created_at).toLocaleString()}
                      </td>
                      <td className="px-4 py-3 sm:px-5">
                        <StatusBadge status={execution.status} />
                      </td>
                      <td className="px-4 py-3 text-right sm:px-5">
                        <Link
                          href={`/executions/${execution.id}`}
                          className="inline-flex items-center gap-0.5 whitespace-nowrap text-sm font-medium text-accent hover:underline"
                        >
                          Details <ChevronRight className="h-3.5 w-3.5" />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </TableScroll>
        </Card>
      )}
    </div>
  );
}
