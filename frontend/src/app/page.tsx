import Link from "next/link";
import { api } from "@/lib/api";
import { Card, LinkButton, PageHeader, StatTile, TableScroll } from "@/components/ui";
import { StatusBadge } from "@/components/StatusBadge";

const NEEDS_REVIEW_STATUSES = new Set(["draft_generated", "pending_review", "edited"]);

export default async function DashboardPage() {
  const [prospects, executions, drafts] = await Promise.all([
    api.listProspects(500).catch(() => []),
    api.listExecutions(500).catch(() => []),
    api.listAllDrafts(500).catch(() => []),
  ]);

  const prospectById = new Map(prospects.map((p) => [p.id, p]));
  const executionById = new Map(executions.map((e) => [e.id, e]));

  const completed = executions.filter((e) => e.status === "completed").length;
  const needsReview = drafts.filter((d) => NEEDS_REVIEW_STATUSES.has(d.status));
  const approved = drafts.filter((d) => d.status === "approved").length;

  const recentExecutions = [...executions]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 8);

  const needsReviewPreview = [...needsReview]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 3);

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Overview of activity, key metrics, and recent executions."
        action={<LinkButton href="/prospects/new">+ New Prospect</LinkButton>}
      />

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatTile label="Total Prospects" value={prospects.length} />
        <StatTile label="Completed" value={completed} href="/executions" />
        <StatTile label="Pending Review" value={needsReview.length} href="/outreach?filter=needs_review" />
        <StatTile label="Approved" value={approved} href="/outreach?filter=approved" />
      </div>

      {needsReviewPreview.length > 0 && (
        <div className="mt-8">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-foreground">Needs Your Review</h2>
            <Link href="/outreach" className="text-xs font-medium text-accent hover:underline">
              View all ({needsReview.length})
            </Link>
          </div>
          <div className="space-y-2.5">
            {needsReviewPreview.map((draft) => {
              const execution = executionById.get(draft.execution_id);
              const prospect = execution ? prospectById.get(execution.prospect_id) : undefined;
              const body = draft.edited_body ?? draft.body;
              return (
                <Link key={draft.id} href={`/executions/${draft.execution_id}?tab=outreach`}>
                  <Card className="px-4 py-3.5 transition-colors hover:border-accent/50 hover:bg-surface-muted sm:px-5">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-medium text-foreground">
                        {prospect?.name ?? "Unknown prospect"}
                      </span>
                      {prospect?.company && <span className="text-sm text-muted">— {prospect.company}</span>}
                      <span className="text-xs text-muted">
                        {draft.channel === "email" ? "✉ Email" : "in LinkedIn"}
                      </span>
                    </div>
                    <p className="mt-1 truncate text-sm text-muted">
                      {draft.subject ?? body.slice(0, 120)}
                    </p>
                  </Card>
                </Link>
              );
            })}
          </div>
        </div>
      )}

      <div className="mt-8">
        <h2 className="mb-3 text-sm font-semibold text-foreground">Recent Executions</h2>
        <Card>
          {recentExecutions.length === 0 ? (
            <div className="px-5 py-8 text-center text-sm text-muted">
              No executions yet. Start by adding a prospect and running research.
            </div>
          ) : (
            <TableScroll>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted">
                    <th className="px-4 py-3 font-medium sm:px-5">Prospect</th>
                    <th className="px-4 py-3 font-medium sm:px-5">Company</th>
                    <th className="px-4 py-3 font-medium sm:px-5">Date</th>
                    <th className="px-4 py-3 font-medium sm:px-5">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {recentExecutions.map((execution) => {
                    const prospect = prospectById.get(execution.prospect_id);
                    return (
                      <tr key={execution.id} className="border-b border-border last:border-0">
                        <td className="px-4 py-3 sm:px-5">
                          <Link
                            href={`/executions/${execution.id}`}
                            className="font-medium text-foreground hover:text-accent"
                          >
                            {prospect?.name ?? "Unknown prospect"}
                          </Link>
                        </td>
                        <td className="px-4 py-3 text-muted sm:px-5">{prospect?.company ?? "—"}</td>
                        <td className="px-4 py-3 text-muted sm:px-5">
                          {new Date(execution.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-4 py-3 sm:px-5">
                          <StatusBadge status={execution.status} />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </TableScroll>
          )}
        </Card>
      </div>
    </div>
  );
}
