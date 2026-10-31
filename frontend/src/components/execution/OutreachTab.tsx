"use client";

import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { OutreachDraft } from "@/lib/types";
import { Button, Card, EmptyState, ErrorBanner } from "@/components/ui";
import { StatusBadge } from "@/components/StatusBadge";

const TERMINAL = new Set(["approved", "rejected"]);

function ValidationChecklist({ report }: { report: OutreachDraft["validation_report"] }) {
  if (!report) return null;
  return (
    <div className="mt-4 rounded-md border border-border bg-surface-muted px-3 py-2.5">
      <div className="mb-1.5 flex items-center gap-1.5 text-xs font-medium">
        <span className={report.passed ? "text-success" : "text-warning"}>
          {report.passed ? "✓ Quality checks passed" : "⚠ Quality checks flagged issues"}
        </span>
      </div>
      <ul className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-xs text-muted">
        {Object.entries(report.checks).map(([check, passed]) => (
          <li key={check} className="flex items-center gap-1.5">
            <span className={passed ? "text-success" : "text-danger"}>{passed ? "✓" : "✕"}</span>
            {check.replaceAll("_", " ")}
          </li>
        ))}
      </ul>
    </div>
  );
}

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
              className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="Subject"
            />
          )}
          <textarea
            className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm"
            rows={8}
            value={body}
            onChange={(e) => setBody(e.target.value)}
          />
          <input
            className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Reviewer notes (optional)"
          />
          <div className="flex gap-2">
            <Button
              variant="primary"
              disabled={busy}
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
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground">{displayBody}</p>
          <ValidationChecklist report={draft.validation_report} />

          {!isTerminal && (
            <div className="mt-4 flex flex-wrap gap-2">
              <Button variant="secondary" disabled={busy} onClick={() => setEditing(true)}>
                Edit
              </Button>
              <Button
                variant="primary"
                className="!bg-success"
                disabled={busy}
                onClick={() => run(() => api.approveDraft(draft.id))}
              >
                ✓ Approve
              </Button>
              <Button
                variant="danger"
                disabled={busy}
                onClick={() => run(() => api.rejectDraft(draft.id))}
              >
                ✕ Reject
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

export function OutreachTab({ drafts: initialDrafts }: { drafts: OutreachDraft[] }) {
  const [drafts, setDrafts] = useState(initialDrafts);
  const [activeChannel, setActiveChannel] = useState<"email" | "linkedin">("email");

  if (drafts.length === 0) {
    return (
      <EmptyState
        title="No draft yet"
        description="A draft is generated once a sufficiently strong, evidence-backed signal is selected. If research completed without one, no draft is created."
      />
    );
  }

  function handleChange(updated: OutreachDraft) {
    setDrafts((prev) => prev.map((d) => (d.id === updated.id ? updated : d)));
  }

  const available = drafts.map((d) => d.channel);
  const current = drafts.find((d) => d.channel === activeChannel) ?? drafts[0];

  return (
    <div>
      <div className="mb-4 flex gap-1 rounded-lg bg-surface-muted p-1 w-fit">
        {(["email", "linkedin"] as const)
          .filter((c) => available.includes(c))
          .map((channel) => (
            <button
              key={channel}
              onClick={() => setActiveChannel(channel)}
              className={`rounded-md px-3.5 py-1.5 text-sm font-medium capitalize transition-colors ${
                current.channel === channel
                  ? "bg-surface text-foreground shadow-sm"
                  : "text-muted hover:text-foreground"
              }`}
            >
              {channel}
            </button>
          ))}
      </div>
      <DraftCard key={current.id} draft={current} onChange={handleChange} />
    </div>
  );
}
