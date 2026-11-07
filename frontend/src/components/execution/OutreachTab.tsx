"use client";

import { useState } from "react";
import { AlertTriangle, CheckCircle2, Mail, MessageSquare, Pencil, XCircle } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import type { Execution, OutreachDraft, Signal } from "@/lib/types";
import { Button, Card, EmptyState, ErrorBanner } from "@/components/ui";
import { StatusBadge } from "@/components/StatusBadge";
import { TERMINAL_EXECUTION_STATUSES } from "@/lib/stages";

const TERMINAL = new Set(["approved", "rejected"]);

function ValidationChecklist({ report }: { report: OutreachDraft["validation_report"] }) {
  if (!report) return null;
  return (
    <div className="mt-4 rounded-card border border-rule bg-paper-3 px-3.5 py-3">
      <div className="mb-2 flex items-center gap-1.5 text-xs font-medium">
        {report.passed ? (
          <span className="flex items-center gap-1.5 text-ok">
            <CheckCircle2 className="h-3.5 w-3.5" /> Quality checks passed
          </span>
        ) : (
          <span className="flex items-center gap-1.5 text-accent">
            <AlertTriangle className="h-3.5 w-3.5" /> Quality checks flagged issues
          </span>
        )}
      </div>
      <ul className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-muted">
        {Object.entries(report.checks).map(([check, passed]) => (
          <li key={check} className="flex items-center gap-1.5">
            {passed ? (
              <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-ok" />
            ) : (
              <XCircle className="h-3.5 w-3.5 shrink-0 text-bad" />
            )}
            {check.replaceAll("_", " ")}
          </li>
        ))}
      </ul>
    </div>
  );
}

const inputClass =
  "w-full rounded-card border border-rule-2 bg-paper-3 px-3 py-2 text-sm outline-none transition-colors focus:border-accent focus:ring-1 focus:ring-focus";

function DraftCard({ draft, onChange }: { draft: OutreachDraft; onChange: (d: OutreachDraft) => void }) {
  const [editing, setEditing] = useState(false);
  const [subject, setSubject] = useState(draft.edited_subject ?? draft.subject ?? "");
  const [body, setBody] = useState(draft.edited_body ?? draft.body);
  const [notes, setNotes] = useState(draft.reviewer_notes ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const displaySubject = draft.edited_subject ?? draft.subject;
  const displayBody = draft.edited_body ?? draft.body;
  const isTerminal = TERMINAL.has(draft.status);

  async function run(action: () => Promise<OutreachDraft>) {
    setBusy(true);
    setError(null);
    try {
      const updated = await action();
      onChange(updated);
      setEditing(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="p-5">
      <div className="mb-3 flex items-center justify-between">
        <StatusBadge status={draft.status} />
        {draft.channel === "email" && !editing && (
          <span className="text-xs text-muted">Subject: {displaySubject}</span>
        )}
      </div>

      {error && <div className="mb-3"><ErrorBanner message={error} /></div>}

      {editing ? (
        <div className="space-y-3">
          {draft.channel === "email" && (
            <input
              className={inputClass}
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="Subject"
            />
          )}
          <textarea
            className={inputClass}
            rows={8}
            value={body}
            onChange={(e) => setBody(e.target.value)}
          />
          <input
            className={inputClass}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Reviewer notes (optional)"
          />
          <div className="flex gap-2">
            <Button
              variant="primary"
              loading={busy}
              onClick={() => run(() => api.editDraft(draft.id, { subject: subject || null, body, reviewer_notes: notes || null }))}
            >
              Save changes
            </Button>
            <Button variant="ghost" disabled={busy} onClick={() => setEditing(false)}>
              Cancel
            </Button>
          </div>
        </div>
      ) : (
        <>
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink">{displayBody}</p>
          <ValidationChecklist report={draft.validation_report} />

          {!isTerminal && (
            <div className="mt-4 flex flex-wrap gap-2">
              <Button variant="secondary" disabled={busy} onClick={() => setEditing(true)}>
                <Pencil className="h-3.5 w-3.5" /> Edit
              </Button>
              <Button variant="success" loading={busy} onClick={() => run(() => api.approveDraft(draft.id))}>
                <CheckCircle2 className="h-3.5 w-3.5" /> Approve
              </Button>
              <Button variant="danger" disabled={busy} onClick={() => run(() => api.rejectDraft(draft.id))}>
                <XCircle className="h-3.5 w-3.5" /> Reject
              </Button>
            </div>
          )}
          {draft.reviewer_notes && (
            <p className="mt-3 text-xs text-muted">Reviewer notes: {draft.reviewer_notes}</p>
          )}
        </>
      )}
    </Card>
  );
}

function NoDraftNotice({ execution, signals }: { execution: Execution; signals: Signal[] }) {
  if (!TERMINAL_EXECUTION_STATUSES.has(execution.status)) {
    return (
      <EmptyState
        title="No draft yet"
        description="Research is still in progress: a draft is generated once a sufficiently strong, evidence-backed signal is found. Check the Overview tab for live status."
      />
    );
  }

  const topSignal = [...signals].sort((a, b) => (b.final_score ?? 0) - (a.final_score ?? 0))[0];

  if (!topSignal) {
    return (
      <EmptyState
        title="No draft was generated"
        description={
          execution.failure_reason ??
          "No usable signals were found for this prospect, so there wasn't enough evidence to draft a personalized message."
        }
      />
    );
  }

  return (
    <Card className="p-5">
      <p className="text-sm font-medium text-ink">No draft was generated</p>
      <p className="mt-1 text-sm text-muted">
        {execution.failure_reason ??
          "The strongest signal found didn't meet the relevance/evidence bar required for a confident, personalized outreach angle."}
      </p>

      <div className="mt-4 rounded-card border border-rule bg-paper-3 px-4 py-3.5">
        <div className="mb-1.5 flex items-center justify-between gap-2">
          <span className="text-sm text-muted">Highest-scoring signal found</span>
          <div className="flex items-center gap-1.5">
            {topSignal.relevance_tier && <StatusBadge status={topSignal.relevance_tier} />}
            <span className="font-outlier text-sm tabular-nums text-ink">
              {topSignal.final_score != null ? topSignal.final_score.toFixed(0) : "N/A"}/100
            </span>
          </div>
        </div>
        <p className="text-sm text-ink">{topSignal.description}</p>
        <blockquote className="mt-2 border-l-2 border-rule-2 pl-3 text-xs italic text-muted">
          &ldquo;{topSignal.evidence_excerpt}&rdquo;
        </blockquote>
      </div>
    </Card>
  );
}

export function OutreachTab({
  drafts: initialDrafts,
  signals,
  execution,
}: {
  drafts: OutreachDraft[];
  signals: Signal[];
  execution: Execution;
}) {
  const [drafts, setDrafts] = useState(initialDrafts);
  const [activeChannel, setActiveChannel] = useState<"email" | "linkedin">("email");

  if (drafts.length === 0) {
    return <NoDraftNotice execution={execution} signals={signals} />;
  }

  function handleChange(updated: OutreachDraft) {
    setDrafts((prev) => prev.map((d) => (d.id === updated.id ? updated : d)));
  }

  const available = drafts.map((d) => d.channel);
  const current = drafts.find((d) => d.channel === activeChannel) ?? drafts[0];

  return (
    <div>
      <div className="mb-4 flex w-fit gap-1 rounded-card border border-rule bg-paper-2 p-1">
        {(["email", "linkedin"] as const)
          .filter((c) => available.includes(c))
          .map((channel) => (
            <button
              key={channel}
              onClick={() => setActiveChannel(channel)}
              className={`flex h-8 items-center gap-1.5 rounded-pill px-3.5 text-sm font-medium capitalize transition-colors ${
                current.channel === channel ? "bg-paper-3 text-ink" : "text-muted hover:text-ink"
              }`}
            >
              {channel === "email" ? <Mail className="h-3.5 w-3.5" /> : <MessageSquare className="h-3.5 w-3.5" />}
              {channel}
            </button>
          ))}
      </div>
      <DraftCard key={current.id} draft={current} onChange={handleChange} />
    </div>
  );
}
