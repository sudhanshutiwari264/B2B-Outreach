"use client";

import { useEffect, useState } from "react";
import { api } from "./api";

const NEEDS_REVIEW_STATUSES = new Set(["draft_generated", "pending_review", "edited"]);
const REFRESH_MS = 30_000;

/** Lightweight polling count used for the sidebar's "Outreach" badge - independent of
 * whatever page is currently mounted, so the badge stays current app-wide. */
export function useNeedsReviewCount(): number | null {
  const [count, setCount] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const drafts = await api.listAllDrafts(500);
        if (!cancelled) {
          setCount(drafts.filter((d) => NEEDS_REVIEW_STATUSES.has(d.status)).length);
        }
      } catch {
        // Keep the previous count on transient failures rather than flashing to 0/empty.
      }
    }

    load();
    const t = setInterval(load, REFRESH_MS);
    return () => {
      cancelled = true;
      clearInterval(t);
    };
  }, []);

  return count;
}
