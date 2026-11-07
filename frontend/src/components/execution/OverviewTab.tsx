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
  if (state === "done") return <CheckCircle2 className="h-4 w-4 text-ok" strokeWidth={1.75} />;
  if (state === "failed") return <XCircle className="h-4 w-4 text-bad" strokeWidth={1.75} />;
  if (state === "running") return <Loader2 className="h-4 w-4 animate-spin text-cool" strokeWidth={1.75} />;
  return <Circle className="h-4 w-4 text-muted" strokeWidth={1.5} />;
}

function SectionTitle({ icon: Icon, children }: { icon: LucideIcon; children: React.ReactNode }) {
  return (
    <h3 className="mb-3 flex items-center gap-2 text-sm text-ink">
      <Icon className="h-4 w-4 text-muted" strokeWidth={1.75} />
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
        <SectionTitle icon={CheckCircle2}>Research progress</SectionTitle>
        <ul className="space-y-2.5">
          {stageStates.map(({ stage, state }) => (
            <li key={stage.key} className="flex items-center gap-2.5 text-sm">
              <StageIcon state={state} />
              <span className={state === "pending" ? "text-muted" : "text-ink"}>{stage.label}</span>
            </li>
          ))}
        </ul>
      </Card>

      <div className="space-y-6">
        <Card className="p-5">
          <SectionTitle icon={Sparkles}>Key findings</SectionTitle>
          {topSignals.length === 0 ? (
            <p className="text-sm text-muted">No signals extracted yet.</p>
          ) : (
            <ul className="space-y-2.5 text-sm text-ink">
              {topSignals.map((s) => (
                <li key={s.id} className="flex gap-2">
                  <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-muted" />
                  <span>{s.description}</span>
                </li>
              ))}
            </ul>
          )}
          {summary && typeof summary.conflicts_found === "number" && (summary.conflicts_found as number) > 0 && (
            <p className="mt-3 flex items-start gap-2 rounded-card border border-accent-soft bg-accent-soft px-3 py-2.5 text-xs text-accent">
              <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              {summary.conflicts_found as number} conflicting claim(s) detected and excluded from outreach.
            </p>
          )}
          {execution.failure_reason && (
            <p className="mt-3 flex items-start gap-2 rounded-card border border-bad-soft bg-bad-soft px-3 py-2.5 text-xs text-bad">
              <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              {execution.failure_reason}
            </p>
          )}
        </Card>

        <Card className="p-5">
          <SectionTitle icon={Globe}>Top sources</SectionTitle>
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
