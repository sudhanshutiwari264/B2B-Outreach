"use client";

import { useEffect, useState } from "react";
import { Clock, Globe, Zap } from "lucide-react";
import { WORKFLOW_STAGES, TERMINAL_EXECUTION_STATUSES } from "@/lib/stages";
import { DEFAULT_MESSAGES, STAGE_MESSAGES } from "@/lib/stageMessages";
import type { Execution, ExecutionLog } from "@/lib/types";

const MESSAGE_ROTATE_MS = 3200;

function formatElapsed(ms: number): string {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const mins = Math.floor(totalSeconds / 60);
  const secs = totalSeconds % 60;
  return mins > 0 ? `${mins}m ${secs.toString().padStart(2, "0")}s` : `${secs}s`;
}

function activeStage(logs: ExecutionLog[]): { key: string; label: string } {
  const started = logs.find((l) => l.status === "started");
  if (started) {
    const def = WORKFLOW_STAGES.find((s) => s.key === started.stage_name);
    return { key: started.stage_name, label: def?.label ?? started.stage_name };
  }
  return { key: "input_validation", label: "Starting research" };
}

export function LiveStatusBanner({
  execution,
  logs,
  sourceCount,
  signalCount,
}: {
  execution: Execution;
  logs: ExecutionLog[];
  sourceCount: number;
  signalCount: number;
}) {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);

  const stage = activeStage(logs);

  if (TERMINAL_EXECUTION_STATUSES.has(execution.status)) return null;

  const startedAt = execution.started_at ? new Date(execution.started_at).getTime() : now;
  const elapsed = formatElapsed(now - startedAt);

  // Rotates purely from the already-ticking clock (no extra state/effect needed): which
  // message shows just depends on how many MESSAGE_ROTATE_MS windows have elapsed.
  const messages = STAGE_MESSAGES[stage.key] ?? DEFAULT_MESSAGES;
  const message = messages[Math.floor(now / MESSAGE_ROTATE_MS) % messages.length];

  const completedCount = logs.filter((l) => l.status === "success").length;
  const totalStages = WORKFLOW_STAGES.length;

  return (
    <div className="mb-6 rounded-card border border-rule bg-paper-2">
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-5 sm:py-4">
        <div>
          <p className="text-sm text-ink">{stage.label}</p>
          <p key={message} className="mt-0.5 text-xs text-muted">
            {message}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-4 text-xs text-muted">
          <span className="font-outlier tabular-nums text-cool">
            stage {completedCount} of {totalStages}
          </span>
          <span className="flex items-center gap-1.5">
            <Globe className="h-3.5 w-3.5" />
            <span className="font-outlier tabular-nums text-ink">{sourceCount}</span> sources
          </span>
          <span className="flex items-center gap-1.5">
            <Zap className="h-3.5 w-3.5" />
            <span className="font-outlier tabular-nums text-ink">{signalCount}</span> signals
          </span>
          <span className="flex items-center gap-1.5 font-outlier tabular-nums">
            <Clock className="h-3.5 w-3.5" />
            {elapsed}
          </span>
        </div>
      </div>
    </div>
  );
}
