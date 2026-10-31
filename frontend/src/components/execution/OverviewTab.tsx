import { WORKFLOW_STAGES, TERMINAL_EXECUTION_STATUSES } from "@/lib/stages";
import type { Execution, ExecutionLog, ResearchSource, Signal } from "@/lib/types";
import { Card } from "@/components/ui";

type StageState = "done" | "failed" | "running" | "pending";

function computeStageStates(
  logsByStage: Map<string, ExecutionLog>,
  isRunning: boolean
): { stage: (typeof WORKFLOW_STAGES)[number]; state: StageState }[] {
  let reachedRunningStage = false;
  return WORKFLOW_STAGES.map((stage) => {
    const log = logsByStage.get(stage.key);
    let state: StageState = "pending";
    if (log?.status === "success") state = "done";
    else if (log?.status === "failed") state = "failed";
    else if (log?.status === "started" || (!log && isRunning && !reachedRunningStage)) {
      state = "running";
      reachedRunningStage = true;
    }
    if (log) reachedRunningStage = true;
    return { stage, state };
  });
}

function StageIcon({ state }: { state: StageState }) {
  if (state === "done") return <span className="text-success">✓</span>;
  if (state === "failed") return <span className="text-danger">✕</span>;
  if (state === "running")
    return (
      <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-accent border-t-transparent" />
    );
  return <span className="text-muted">○</span>;
}

export function OverviewTab({
  execution,
  logs,
  signals,
  sources,
}: {
  execution: Execution;
  logs: ExecutionLog[];
  signals: Signal[];
  sources: ResearchSource[];
}) {
  const logsByStage = new Map(logs.map((l) => [l.stage_name, l]));
  const isRunning = !TERMINAL_EXECUTION_STATUSES.has(execution.status);

  const stageStates = computeStageStates(logsByStage, isRunning);

  const topSignals = [...signals]
    .sort((a, b) => (b.final_score ?? 0) - (a.final_score ?? 0))
    .slice(0, 3);

  const topSources = [...sources]
    .filter((s) => s.extraction_status === "success")
    .slice(0, 5);

  const summary = execution.result_summary as Record<string, unknown> | null;

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <Card className="p-5">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-foreground">Research Progress</h3>
          {isRunning && (
            <span className="flex items-center gap-1.5 text-xs font-medium text-info">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-info" /> Live
            </span>
          )}
        </div>
        <ul className="space-y-2.5">
          {stageStates.map(({ stage, state }) => (
            <li key={stage.key} className="flex items-center gap-2.5 text-sm">
              <StageIcon state={state} />
              <span className={state === "pending" ? "text-muted" : "text-foreground"}>
                {stage.label}
              </span>
            </li>
          ))}
        </ul>
      </Card>

      <div className="space-y-6">
        <Card className="p-5">
          <h3 className="mb-3 text-sm font-semibold text-foreground">Key Findings</h3>
          {topSignals.length === 0 ? (
            <p className="text-sm text-muted">No signals extracted yet.</p>
          ) : (
            <ul className="space-y-2 text-sm text-foreground">
              {topSignals.map((s) => (
                <li key={s.id} className="flex gap-2">
                  <span className="mt-0.5 text-accent">•</span>
                  <span>{s.description}</span>
                </li>
              ))}
            </ul>
          )}
          {summary && typeof summary.conflicts_found === "number" && (summary.conflicts_found as number) > 0 && (
            <p className="mt-3 rounded-md bg-warning-soft px-3 py-2 text-xs text-warning">
              {summary.conflicts_found as number} conflicting claim(s) detected and excluded from outreach.
            </p>
          )}
          {execution.failure_reason && (
            <p className="mt-3 rounded-md bg-danger-soft px-3 py-2 text-xs text-danger">
              {execution.failure_reason}
            </p>
          )}
        </Card>

        <Card className="p-5">
          <h3 className="mb-3 text-sm font-semibold text-foreground">Top Sources</h3>
          {topSources.length === 0 ? (
            <p className="text-sm text-muted">No sources extracted yet.</p>
          ) : (
            <ul className="space-y-2">
              {topSources.map((s) => (
                <li key={s.id}>
                  <a
                    href={s.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-sm font-medium text-accent hover:underline"
                  >
                    {s.title || s.domain || s.url}
                  </a>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}
