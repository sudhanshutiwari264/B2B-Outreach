import { Suspense } from "react";
import { api } from "@/lib/api";
import { PageHeader, Spinner } from "@/components/ui";
import { OutreachQueue, type QueueItem } from "@/components/outreach/OutreachQueue";

export default async function OutreachQueuePage() {
  const [drafts, executions, prospects] = await Promise.all([
    api.listAllDrafts(500).catch(() => []),
    api.listExecutions(500).catch(() => []),
    api.listProspects(500).catch(() => []),
  ]);

  const executionById = new Map(executions.map((e) => [e.id, e]));
  const prospectById = new Map(prospects.map((p) => [p.id, p]));

  const items: QueueItem[] = drafts.map((draft) => {
    const execution = executionById.get(draft.execution_id);
    const prospect = execution ? prospectById.get(execution.prospect_id) : undefined;
    return {
      draft,
      prospectName: prospect?.name ?? "Unknown prospect",
      prospectCompany: prospect?.company ?? "",
    };
  });

  return (
    <div>
      <PageHeader
        title="Outreach"
        description="Every generated message in one place — review, approve, or reject without digging through executions."
      />
      <Suspense fallback={<Spinner />}>
        <OutreachQueue items={items} />
      </Suspense>
    </div>
  );
}
