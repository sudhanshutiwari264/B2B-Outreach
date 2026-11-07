import Link from "next/link";
import { ArrowRight, LayoutDashboard, Mail, MessageSquare, UserPlus } from "lucide-react";
import { api } from "@/lib/api";
import { Card, EmptyState, LinkButton, PageHeader, StatTile, TableScroll } from "@/components/ui";
import { StatusBadge } from "@/components/StatusBadge";
import { Avatar } from "@/components/Avatar";

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
        icon={LayoutDashboard}
        action={
          <LinkButton href="/prospects/new">
            <UserPlus className="h-4 w-4" /> New prospect
          </LinkButton>
        }
      />

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatTile label="Total prospects" value={prospects.length} />
        <StatTile label="Completed" value={completed} href="/executions" />
        <StatTile label="Pending review" value={needsReview.length} href="/outreach?filter=needs_review" />
        <StatTile label="Approved" value={approved} href="/outreach?filter=approved" />
      </div>

      {needsReviewPreview.length > 0 && (
        <div className="mt-8">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm text-ink">Needs your review</h2>
            <Link
              href="/outreach"
              className="flex items-center gap-1 text-xs font-medium text-accent hover:underline"
            >
              View all ({needsReview.length}) <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
          <div className="space-y-2.5">
            {needsReviewPreview.map((draft) => {
              const execution = executionById.get(draft.execution_id);
              const prospect = execution ? prospectById.get(execution.prospect_id) : undefined;
              const body = draft.edited_body ?? draft.body;
              return (
                <Link key={draft.id} href={`/executions/${draft.execution_id}?tab=outreach`}>
                  <Card className="px-4 py-3.5 transition-colors hover:bg-paper-3 sm:px-5">
                    <div className="flex items-start gap-3">
                      <Avatar name={prospect?.name ?? "?"} />
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-medium text-ink">
                            {prospect?.name ?? "Unknown prospect"}
                          </span>
                          {prospect?.company && (
                            <span className="text-sm text-muted">({prospect.company})</span>
                          )}
                          <span className="flex items-center gap-1 text-xs text-muted">
                            {draft.channel === "email" ? (
                              <Mail className="h-3 w-3" />
                            ) : (
                              <MessageSquare className="h-3 w-3" />
                            )}
                            {draft.channel}
                          </span>
                        </div>
                        <p className="mt-1 truncate text-sm text-muted">
                          {draft.subject ?? body.slice(0, 120)}
                        </p>
                      </div>
                    </div>
                  </Card>
                </Link>
              );
            })}
          </div>
        </div>
      )}

      <div className="mt-8">
        <h2 className="mb-3 text-sm text-ink">Recent executions</h2>
        {recentExecutions.length === 0 ? (
          <EmptyState
            title="No executions yet"
            description="Start by adding a prospect and running research."
            icon={LayoutDashboard}
          />
        ) : (
          <Card>
            <TableScroll>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-rule text-left text-sm text-muted">
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
                      <tr
                        key={execution.id}
                        className="border-b border-rule transition-colors last:border-0 hover:bg-paper-3"
                      >
                        <td className="px-4 py-3 sm:px-5">
                          <Link
                            href={`/executions/${execution.id}`}
                            className="flex items-center gap-2.5 font-medium text-ink hover:text-accent"
                          >
                            <Avatar name={prospect?.name ?? "?"} size="sm" />
                            {prospect?.name ?? "Unknown prospect"}
                          </Link>
                        </td>
                        <td className="px-4 py-3 text-muted sm:px-5">{prospect?.company ?? "Unknown"}</td>
                        <td className="px-4 py-3 font-outlier text-muted tabular-nums sm:px-5">
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
          </Card>
        )}
      </div>
    </div>
  );
}
