import type { ResearchSource } from "@/lib/types";
import { Card, EmptyState, TableScroll } from "@/components/ui";
import { StatusBadge } from "@/components/StatusBadge";

export function SourcesTab({ sources }: { sources: ResearchSource[] }) {
  if (sources.length === 0) {
    return <EmptyState title="No sources yet" description="Sources will appear here once research discovery completes." />;
  }

  return (
    <Card>
      <TableScroll minWidth={620}>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted">
              <th className="px-4 py-3 font-medium sm:px-5">Source</th>
              <th className="px-4 py-3 font-medium sm:px-5">Type</th>
              <th className="px-4 py-3 font-medium sm:px-5">Evidence</th>
              <th className="px-4 py-3 font-medium sm:px-5">Extraction</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((s) => (
              <tr key={s.id} className="border-b border-border last:border-0 align-top">
                <td className="max-w-md px-4 py-3 sm:px-5">
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
                <td className="px-4 py-3 text-muted sm:px-5">{s.source_type.replaceAll("_", " ")}</td>
                <td className="px-4 py-3 text-muted sm:px-5">{s.evidence_type.replaceAll("_", " ")}</td>
                <td className="px-4 py-3 sm:px-5">
                  <StatusBadge status={s.extraction_status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableScroll>
    </Card>
  );
}
