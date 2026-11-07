import { UserPlus, Users } from "lucide-react";
import { api } from "@/lib/api";
import { LinkButton, PageHeader } from "@/components/ui";
import { ProspectsList, type ProspectRow } from "@/components/prospects/ProspectsList";

export default async function ProspectsPage() {
  const [prospects, executions] = await Promise.all([
    api.listProspects(500).catch(() => []),
    api.listExecutions(500).catch(() => []),
  ]);

  const executionCountByProspect = new Map<string, number>();
  for (const e of executions) {
    executionCountByProspect.set(e.prospect_id, (executionCountByProspect.get(e.prospect_id) ?? 0) + 1);
  }

  const rows: ProspectRow[] = [...prospects]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .map((prospect) => ({
      prospect,
      executionCount: executionCountByProspect.get(prospect.id) ?? 0,
    }));

  return (
    <div>
      <PageHeader
        title="Prospects"
        description="Every prospect you've researched: search, revisit, or kick off a fresh run."
        icon={Users}
        action={
          <LinkButton href="/prospects/new">
            <UserPlus className="h-4 w-4" /> New prospect
          </LinkButton>
        }
      />
      <ProspectsList rows={rows} />
    </div>
  );
}
