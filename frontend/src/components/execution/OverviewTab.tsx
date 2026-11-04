import {
  AlertTriangle,
  CheckCircle2,
  Circle,
  ExternalLink,
  Globe,
  Loader2,
  type LucideIcon,
  Sparkles,
  XCircle,
} from "lucide-react";
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
  if (state === "done") return <CheckCircle2 className="h-4 w-4 text-success" strokeWidth={2} />;
  if (state === "failed") return <XCircle className="h-4 w-4 text-danger" strokeWidth={2} />;
  if (state === "running") return <Loader2 className="h-4 w-4 animate-spin text-accent" strokeWidth={2} />;
  return <Circle className="h-4 w-4 text-muted" strokeWidth={1.75} />;
}

function SectionTitle({ icon: Icon, children }: { icon: LucideIcon; children: React.ReactNode }) {
  return (
    <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-foreground">
      <Icon className="h-4 w-4 text-muted" strokeWidth={2} />
      {children}
    </h3>
  );
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
          <SectionTitle icon={CheckCircle2}>Research Progress</SectionTitle>
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
          <SectionTitle icon={Sparkles}>Key Findings</SectionTitle>
          {topSignals.length === 0 ? (
            <p className="text-sm text-muted">No signals extracted yet.</p>
          ) : (
            <ul className="space-y-2.5 text-sm text-foreground">
              {topSignals.map((s) => (
                <li key={s.id} className="flex gap-2">
                  <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-accent" />
                  <span>{s.description}</span>
                </li>
              ))}
            </ul>
          )}
          {summary && typeof summary.conflicts_found === "number" && (summary.conflicts_found as number) > 0 && (
            <p className="mt-3 flex items-start gap-2 rounded-lg bg-warning-soft px-3 py-2.5 text-xs text-warning">
              <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              {summary.conflicts_found as number} conflicting claim(s) detected and excluded from outreach.
            </p>
          )}
          {execution.failure_reason && (
            <p className="mt-3 flex items-start gap-2 rounded-lg bg-danger-soft px-3 py-2.5 text-xs text-danger">
              <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              {execution.failure_reason}
            </p>
          )}
        </Card>

        <Card className="p-5">
          <SectionTitle icon={Globe}>Top Sources</SectionTitle>
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
                    className="group flex items-center gap-1.5 text-sm font-medium text-accent hover:underline"
                  >
                    <span className="truncate">{s.title || s.domain || s.url}</span>
                    <ExternalLink className="h-3 w-3 shrink-0 opacity-0 transition-opacity group-hover:opacity-100" />
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
