import type { ResearchSource } from "@/lib/types";
import { Card, EmptyState } from "@/components/ui";
import { StatusBadge } from "@/components/StatusBadge";

export function SourcesTab({ sources }: { sources: ResearchSource[] }) {
  if (sources.length === 0) {
    return <EmptyState title="No sources yet" description="Sources will appear here once research discovery completes." />;
  }

  return (
    <Card>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted">
            <th className="px-5 py-3 font-medium">Source</th>
            <th className="px-5 py-3 font-medium">Type</th>
            <th className="px-5 py-3 font-medium">Evidence</th>
            <th className="px-5 py-3 font-medium">Extraction</th>
          </tr>
        </thead>
        <tbody>
          {sources.map((s) => (
            <tr key={s.id} className="border-b border-border last:border-0 align-top">
              <td className="max-w-md px-5 py-3">
                <a
                  href={s.url}
                  target="_blank"
                  rel="noreferrer"
                  className="font-medium text-accent hover:underline"
                >
                  {s.title || s.domain || s.url}
                </a>
                <div className="mt-0.5 truncate text-xs text-muted">{s.domain ?? s.url}</div>
              </td>
              <td className="px-5 py-3 text-muted">{s.source_type.replaceAll("_", " ")}</td>
              <td className="px-5 py-3 text-muted">{s.evidence_type.replaceAll("_", " ")}</td>
              <td className="px-5 py-3">
                <StatusBadge status={s.extraction_status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}
