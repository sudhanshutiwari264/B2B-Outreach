interface StatusStyle {
  label: string;
  bg: string;
  text: string;
  dot: string;
  pulse?: boolean;
}

const STATUS_STYLES: Record<string, StatusStyle> = {
  queued: { label: "Queued", bg: "bg-surface-muted", text: "text-muted", dot: "bg-muted" },
  running: { label: "Running", bg: "bg-info-soft", text: "text-info", dot: "bg-info", pulse: true },
  completed: { label: "Completed", bg: "bg-success-soft", text: "text-success", dot: "bg-success" },
  partial: { label: "Partial", bg: "bg-warning-soft", text: "text-warning", dot: "bg-warning" },
  needs_review: { label: "Needs Review", bg: "bg-warning-soft", text: "text-warning", dot: "bg-warning" },
  insufficient_data: { label: "Insufficient Data", bg: "bg-surface-muted", text: "text-muted", dot: "bg-muted" },
  failed: { label: "Failed", bg: "bg-danger-soft", text: "text-danger", dot: "bg-danger" },

  draft_generated: { label: "Draft Generated", bg: "bg-surface-muted", text: "text-muted", dot: "bg-muted" },
  pending_review: { label: "Pending Review", bg: "bg-warning-soft", text: "text-warning", dot: "bg-warning" },
  edited: { label: "Edited", bg: "bg-info-soft", text: "text-info", dot: "bg-info" },
  approved: { label: "Approved", bg: "bg-success-soft", text: "text-success", dot: "bg-success" },
  rejected: { label: "Rejected", bg: "bg-danger-soft", text: "text-danger", dot: "bg-danger" },

  success: { label: "Success", bg: "bg-success-soft", text: "text-success", dot: "bg-success" },
  started: { label: "Running", bg: "bg-info-soft", text: "text-info", dot: "bg-info", pulse: true },
  skipped: { label: "Skipped", bg: "bg-surface-muted", text: "text-muted", dot: "bg-muted" },

  pending: { label: "Pending", bg: "bg-surface-muted", text: "text-muted", dot: "bg-muted" },
  verified: { label: "Verified", bg: "bg-success-soft", text: "text-success", dot: "bg-success" },
  disputed: { label: "Disputed", bg: "bg-danger-soft", text: "text-danger", dot: "bg-danger" },
  restricted: { label: "Restricted", bg: "bg-warning-soft", text: "text-warning", dot: "bg-warning" },

  high: { label: "High", bg: "bg-success-soft", text: "text-success", dot: "bg-success" },
  medium: { label: "Medium", bg: "bg-warning-soft", text: "text-warning", dot: "bg-warning" },
  low: { label: "Low", bg: "bg-surface-muted", text: "text-muted", dot: "bg-muted" },
};

export function StatusBadge({ status }: { status: string }) {
  const style =
    STATUS_STYLES[status] ?? { label: status, bg: "bg-surface-muted", text: "text-muted", dot: "bg-muted" };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${style.bg} ${style.text}`}
    >
      <span className="relative flex h-1.5 w-1.5 shrink-0">
        {style.pulse && (
          <span className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-60 ${style.dot}`} />
        )}
        <span className={`relative inline-flex h-1.5 w-1.5 rounded-full ${style.dot}`} />
      </span>
      {style.label}
    </span>
  );
}
