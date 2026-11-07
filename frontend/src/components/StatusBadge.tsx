/* Console's chip: state only, a 1px rule, tinted by meaning. Amber (accent) means a person's
 * attention is wanted; cool means the instrument is working; ok/bad are the outcome. No dot -
 * a decorative status dot is a Floor tell the chip's tint already carries. */
type Meaning = "neutral" | "person" | "instrument" | "ok" | "bad";

const MEANING_CLASSES: Record<Meaning, string> = {
  neutral: "border-rule text-muted bg-paper-3",
  person: "border-accent-soft text-accent bg-accent-soft",
  instrument: "border-cool-soft text-cool bg-cool-soft",
  ok: "border-ok-soft text-ok bg-ok-soft",
  bad: "border-bad-soft text-bad bg-bad-soft",
};

const STATUS_STYLES: Record<string, { label: string; meaning: Meaning }> = {
  queued: { label: "Queued", meaning: "neutral" },
  running: { label: "Running", meaning: "instrument" },
  completed: { label: "Completed", meaning: "ok" },
  partial: { label: "Partial", meaning: "person" },
  needs_review: { label: "Needs review", meaning: "person" },
  insufficient_data: { label: "Insufficient data", meaning: "neutral" },
  failed: { label: "Failed", meaning: "bad" },

  draft_generated: { label: "Draft generated", meaning: "neutral" },
  pending_review: { label: "Pending review", meaning: "person" },
  edited: { label: "Edited", meaning: "person" },
  approved: { label: "Approved", meaning: "ok" },
  rejected: { label: "Rejected", meaning: "bad" },

  success: { label: "Success", meaning: "ok" },
  started: { label: "Running", meaning: "instrument" },
  skipped: { label: "Skipped", meaning: "neutral" },

  pending: { label: "Pending", meaning: "neutral" },
  verified: { label: "Verified", meaning: "ok" },
  disputed: { label: "Disputed", meaning: "bad" },
  restricted: { label: "Restricted", meaning: "person" },

  high: { label: "High", meaning: "ok" },
  medium: { label: "Medium", meaning: "person" },
  low: { label: "Low", meaning: "neutral" },
};

export function StatusBadge({ status }: { status: string }) {
  const style = STATUS_STYLES[status] ?? { label: status, meaning: "neutral" as Meaning };

  return (
    <span
      className={`inline-flex items-center rounded-[4px] border px-1.5 py-0.5 text-xs font-medium ${MEANING_CLASSES[style.meaning]}`}
    >
      {style.label}
    </span>
  );
}
