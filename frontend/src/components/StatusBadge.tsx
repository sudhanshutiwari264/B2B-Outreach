const STATUS_STYLES: Record<string, { label: string; className: string }> = {
  queued: { label: "Queued", className: "bg-surface-muted text-muted" },
  running: { label: "Running", className: "bg-info-soft text-info" },
  completed: { label: "Completed", className: "bg-success-soft text-success" },
  partial: { label: "Partial", className: "bg-warning-soft text-warning" },
  needs_review: { label: "Needs Review", className: "bg-warning-soft text-warning" },
  insufficient_data: { label: "Insufficient Data", className: "bg-surface-muted text-muted" },
  failed: { label: "Failed", className: "bg-danger-soft text-danger" },

  draft_generated: { label: "Draft Generated", className: "bg-surface-muted text-muted" },
  pending_review: { label: "Pending Review", className: "bg-warning-soft text-warning" },
  edited: { label: "Edited", className: "bg-info-soft text-info" },
  approved: { label: "Approved", className: "bg-success-soft text-success" },
  rejected: { label: "Rejected", className: "bg-danger-soft text-danger" },

  success: { label: "Success", className: "bg-success-soft text-success" },
  started: { label: "Running", className: "bg-info-soft text-info" },
  skipped: { label: "Skipped", className: "bg-surface-muted text-muted" },

  pending: { label: "Pending", className: "bg-surface-muted text-muted" },
  verified: { label: "Verified", className: "bg-success-soft text-success" },
  disputed: { label: "Disputed", className: "bg-danger-soft text-danger" },
  restricted: { label: "Restricted", className: "bg-warning-soft text-warning" },
  needs_review_evidence: { label: "Needs Review", className: "bg-warning-soft text-warning" },

  high: { label: "High", className: "bg-success-soft text-success" },
  medium: { label: "Medium", className: "bg-warning-soft text-warning" },
  low: { label: "Low", className: "bg-surface-muted text-muted" },
};

export function StatusBadge({ status }: { status: string }) {
  const style = STATUS_STYLES[status] ?? { label: status, className: "bg-surface-muted text-muted" };
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${style.className}`}
    >
      {style.label}
    </span>
  );
}
