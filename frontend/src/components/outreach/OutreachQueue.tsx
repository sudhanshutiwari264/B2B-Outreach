"use client";

import { useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { OutreachDraft } from "@/lib/types";
import { Button, Card, EmptyState, ErrorBanner } from "@/components/ui";
import { StatusBadge } from "@/components/StatusBadge";

export interface QueueItem {
  draft: OutreachDraft;
  prospectName: string;
  prospectCompany: string;
}

const NEEDS_REVIEW_STATUSES = new Set(["draft_generated", "pending_review", "edited"]);

const FILTERS = [
  { key: "needs_review", label: "Needs Review" },
  { key: "approved", label: "Approved" },
  { key: "rejected", label: "Rejected" },
  { key: "all", label: "All" },
] as const;

type FilterKey = (typeof FILTERS)[number]["key"];

function isFilterKey(value: string | null): value is FilterKey {
  return FILTERS.some((f) => f.key === value);
}

function matchesFilter(status: string, filter: FilterKey): boolean {
  if (filter === "all") return true;
  if (filter === "needs_review") return NEEDS_REVIEW_STATUSES.has(status);
  return status === filter;
}

function channelLabel(channel: string): string {
  return channel === "email" ? "✉ Email" : "in LinkedIn";
}

function QueueRow({
  item,
  onChange,
}: {
  item: QueueItem;
  onChange: (updated: OutreachDraft) => void;
}) {
  const { draft, prospectName, prospectCompany } = item;
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const isTerminal = draft.status === "approved" || draft.status === "rejected";
  const body = draft.edited_body ?? draft.body;
  const preview = body.length > 180 ? `${body.slice(0, 180)}…` : body;

  async function run(action: () => Promise<OutreachDraft>) {
    setBusy(true);
    setError(null);
    try {
      onChange(await action());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="p-4 sm:p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <Link
              href={`/executions/${draft.execution_id}?tab=outreach`}
              className="font-medium text-foreground hover:text-accent"
            >
              {prospectName}
            </Link>
            {prospectCompany && <span className="text-sm text-muted">— {prospectCompany}</span>}
            <StatusBadge status={draft.status} />
            <span className="text-xs text-muted">{channelLabel(draft.channel)}</span>
          </div>
          {draft.channel === "email" && draft.subject && (
            <p className="mt-1.5 text-sm font-medium text-foreground">{draft.subject}</p>
          )}
          <p className="mt-1 text-sm text-muted">{preview}</p>
          {error && (
            <div className="mt-2">
              <ErrorBanner message={error} />
            </div>
          )}
        </div>

        <div className="flex shrink-0 flex-wrap gap-2">
          <Link
            href={`/executions/${draft.execution_id}?tab=outreach`}
            className="inline-flex items-center justify-center rounded-md border border-border bg-surface px-3.5 py-2 text-sm font-medium text-foreground transition-colors hover:bg-surface-muted"
          >
            Open
          </Link>
          {!isTerminal && (
            <>
              <Button
                variant="primary"
                className="!bg-success"
                disabled={busy}
                onClick={() => run(() => api.approveDraft(draft.id))}
              >
                ✓ Approve
              </Button>
              <Button variant="danger" disabled={busy} onClick={() => run(() => api.rejectDraft(draft.id))}>
                ✕ Reject
              </Button>
            </>
          )}
        </div>
      </div>
    </Card>
  );
}

export function OutreachQueue({ items: initialItems }: { items: QueueItem[] }) {
  const [items, setItems] = useState(initialItems);
  const searchParams = useSearchParams();
  const requestedFilter = searchParams.get("filter");
  const [filter, setFilter] = useState<FilterKey>(
    isFilterKey(requestedFilter) ? requestedFilter : "needs_review"
  );

  function handleChange(updated: OutreachDraft) {
    setItems((prev) => prev.map((it) => (it.draft.id === updated.id ? { ...it, draft: updated } : it)));
  }

  const filtered = items.filter((it) => matchesFilter(it.draft.status, filter));
  const needsReviewCount = items.filter((it) => NEEDS_REVIEW_STATUSES.has(it.draft.status)).length;

  return (
    <div>
      <div className="mb-5 flex gap-1 overflow-x-auto rounded-lg bg-surface-muted p-1 w-fit">
        {FILTERS.map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={`shrink-0 whitespace-nowrap rounded-md px-3.5 py-1.5 text-sm font-medium transition-colors ${
              filter === f.key ? "bg-surface text-foreground shadow-sm" : "text-muted hover:text-foreground"
            }`}
          >
            {f.label}
            {f.key === "needs_review" && needsReviewCount > 0 && (
              <span className="ml-1.5 text-xs text-accent">({needsReviewCount})</span>
            )}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          title={filter === "needs_review" ? "Nothing waiting on you" : "No drafts here"}
          description={
            filter === "needs_review"
              ? "Every generated draft has been reviewed. New ones will show up here as research completes."
              : "Switch filters to see drafts in other states."
          }
        />
      ) : (
        <div className="space-y-3">
          {filtered.map((item) => (
            <QueueRow key={item.draft.id} item={item} onChange={handleChange} />
          ))}
        </div>
      )}
    </div>
  );
}
