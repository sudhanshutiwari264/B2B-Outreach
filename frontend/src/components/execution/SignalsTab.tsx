import { Building2, Star, User, Zap } from "lucide-react";
import type { Signal } from "@/lib/types";
import { Card, EmptyState } from "@/components/ui";
import { StatusBadge } from "@/components/StatusBadge";

function ScoreBar({ label, value }: { label: string; value: number | null }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-28 shrink-0 text-muted">{label}</span>
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-surface-muted">
        <div
          className="h-full rounded-full bg-gradient-to-r from-accent to-indigo-400 transition-all duration-500"
          style={{ width: `${value ?? 0}%` }}
        />
      </div>
      <span className="w-8 shrink-0 text-right font-medium text-foreground">
        {value != null ? Math.round(value) : "—"}
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
          <Card
            key={s.id}
            className={`p-5 ${isTop ? "ring-1 ring-accent/60 shadow-[var(--shadow-md)]" : ""}`}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                {isTop && (
                  <span className="mb-1.5 inline-flex items-center gap-1 text-xs font-medium text-accent">
                    <Star className="h-3 w-3 fill-accent" /> Selected Signal
                  </span>
                )}
                <p className="text-sm font-medium text-foreground">{s.description}</p>
                <p className="mt-1 text-xs text-muted">{s.relevance_reason}</p>
              </div>
              <div className="flex shrink-0 flex-col items-end gap-1.5">
                <span className="text-lg font-semibold tracking-tight text-foreground">
                  {s.final_score != null ? s.final_score.toFixed(2) : "—"}
                </span>
                <div className="flex gap-1.5">
                  {s.relevance_tier && <StatusBadge status={s.relevance_tier} />}
                  {s.is_disputed && <StatusBadge status="disputed" />}
                </div>
              </div>
            </div>

            <blockquote className="mt-3 border-l-2 border-accent/30 pl-3 text-xs italic text-muted">
              &ldquo;{s.evidence_excerpt}&rdquo;
            </blockquote>

            <div className="mt-4 grid grid-cols-1 gap-1.5 sm:grid-cols-2">
              <ScoreBar label="Relevance" value={s.relevance_score} />
              <ScoreBar label="Business Impact" value={s.business_impact_score} />
              <ScoreBar label="Recency" value={s.recency_score} />
              <ScoreBar label="Evidence Quality" value={s.evidence_quality_score} />
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
              <span className="rounded-full bg-surface-muted px-2 py-0.5 font-medium">
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
