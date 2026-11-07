import { Building2, Star, User, Zap } from "lucide-react";
import type { Signal } from "@/lib/types";
import { Card, EmptyState } from "@/components/ui";
import { StatusBadge } from "@/components/StatusBadge";

/** A reading: the label in the body face, a solid cool fill (never a gradient - the
 * instrument measured this), the value tabular in the measured face. */
function ScoreBar({ label, value }: { label: string; value: number | null }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-28 shrink-0 text-muted">{label}</span>
      <div className="h-1.5 flex-1 overflow-hidden rounded-pill bg-paper-3">
        <div
          className="h-full w-full origin-left rounded-pill bg-cool transition-transform duration-500"
          style={{ transform: `scaleX(${(value ?? 0) / 100})` }}
        />
      </div>
      <span className="w-8 shrink-0 text-right font-outlier tabular-nums text-ink">
        {value != null ? Math.round(value) : "N/A"}
      </span>
    </div>
  );
}

export function SignalsTab({ signals }: { signals: Signal[] }) {
  if (signals.length === 0) {
    return (
      <EmptyState
        title="No signals yet"
        description="Signals appear here once the LLM extracts them from researched sources."
        icon={Zap}
      />
    );
  }

  const sorted = [...signals].sort((a, b) => (b.final_score ?? 0) - (a.final_score ?? 0));
  const topScore = sorted[0]?.final_score ?? 0;

  return (
    <div className="space-y-3">
      {sorted.map((s) => {
        const isTop = s.final_score === topScore && !s.is_disputed;
        return (
          <Card key={s.id} className={`p-5 ${isTop ? "border-accent-soft bg-paper-2" : ""}`}>
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                {isTop && (
                  <span className="mb-1.5 inline-flex items-center gap-1 text-xs font-medium text-accent">
                    <Star className="h-3 w-3 fill-accent" /> Selected signal
                  </span>
                )}
                <p className="text-sm font-medium text-ink">{s.description}</p>
                <p className="mt-1 text-xs text-muted">{s.relevance_reason}</p>
              </div>
              <div className="flex shrink-0 flex-col items-end gap-1.5">
                <span className="font-outlier text-2xl tabular-nums text-ink">
                  {s.final_score != null ? s.final_score.toFixed(0) : "N/A"}
                </span>
                <div className="flex gap-1.5">
                  {s.relevance_tier && <StatusBadge status={s.relevance_tier} />}
                  {s.is_disputed && <StatusBadge status="disputed" />}
                </div>
              </div>
            </div>

            <blockquote className="mt-3 border-l-2 border-rule-2 pl-3 text-xs italic text-muted">
              &ldquo;{s.evidence_excerpt}&rdquo;
            </blockquote>

            <div className="mt-4 grid grid-cols-1 gap-1.5 sm:grid-cols-2">
              <ScoreBar label="Relevance" value={s.relevance_score} />
              <ScoreBar label="Business impact" value={s.business_impact_score} />
              <ScoreBar label="Recency" value={s.recency_score} />
              <ScoreBar label="Evidence quality" value={s.evidence_quality_score} />
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
              <span className="rounded-[4px] border border-rule bg-paper-3 px-1.5 py-0.5 font-medium">
                {s.signal_type.replaceAll("_", " ")}
              </span>
              <span className="flex items-center gap-1">
                <User className="h-3 w-3" /> {s.entity}
              </span>
              {s.company && (
                <span className="flex items-center gap-1">
                  <Building2 className="h-3 w-3" /> {s.company}
                </span>
              )}
            </div>
          </Card>
        );
      })}
    </div>
  );
}
