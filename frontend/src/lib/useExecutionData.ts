"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import { TERMINAL_EXECUTION_STATUSES } from "./stages";
import type {
  Execution,
  ExecutionLog,
  OutreachDraft,
  Prospect,
  ResearchSource,
  Signal,
} from "./types";

const POLL_INTERVAL_MS = 4000;

export interface ExecutionData {
  execution: Execution | null;
  prospect: Prospect | null;
  logs: ExecutionLog[];
  sources: ResearchSource[];
  signals: Signal[];
  drafts: OutreachDraft[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useExecutionData(executionId: string): ExecutionData {
  const [execution, setExecution] = useState<Execution | null>(null);
  const [prospect, setProspect] = useState<Prospect | null>(null);
  const [logs, setLogs] = useState<ExecutionLog[]>([]);
  const [sources, setSources] = useState<ResearchSource[]>([]);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [drafts, setDrafts] = useState<OutreachDraft[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Holds the latest `load` so the poll timeout always calls the current closure without
  // self-referencing `load` inside its own definition.
  const loadRef = useRef<() => Promise<void>>(async () => {});

  const load = useCallback(async () => {
    try {
      const exec = await api.getExecution(executionId);
      setExecution(exec);

      const [p, l, s, sig, d] = await Promise.all([
        api.getProspect(exec.prospect_id).catch(() => null),
        api.getExecutionLogs(executionId).catch(() => []),
        api.getSources(executionId).catch(() => []),
        api.getSignals(executionId).catch(() => []),
        api.getExecutionDrafts(executionId).catch(() => []),
      ]);
      setProspect(p);
      setLogs(l);
      setSources(s);
      setSignals(sig);
      setDrafts(d);
      setError(null);

      if (!TERMINAL_EXECUTION_STATUSES.has(exec.status)) {
        timerRef.current = setTimeout(() => loadRef.current(), POLL_INTERVAL_MS);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load execution");
    } finally {
      setLoading(false);
    }
  }, [executionId]);

  useEffect(() => {
    loadRef.current = load;
  }, [load]);

  useEffect(() => {
    // Intentional fetch-on-mount + self-scheduling poll; there's no external subscription
    // API to sync to instead.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [load]);

  return { execution, prospect, logs, sources, signals, drafts, loading, error, refetch: load };
}
