export const WORKFLOW_STAGES: { key: string; label: string }[] = [
  { key: "input_validation", label: "Prospect validation" },
  { key: "research_discovery", label: "Research discovery (Tavily)" },
  { key: "url_deduplication", label: "URL deduplication" },
  { key: "content_extraction", label: "Content extraction" },
  { key: "content_cleaning", label: "Content cleaning" },
  { key: "source_validation", label: "Source validation" },
  { key: "signal_extraction", label: "Signal extraction (Tarqa AI)" },
  { key: "signal_scoring", label: "Signal scoring" },
  { key: "conflict_detection", label: "Conflict detection" },
  { key: "signal_selection", label: "Signal selection" },
  { key: "outreach_strategy", label: "Outreach strategy" },
  { key: "draft_generation", label: "Draft generation" },
];

export const TERMINAL_EXECUTION_STATUSES = new Set([
  "completed",
  "partial",
  "needs_review",
  "insufficient_data",
  "failed",
]);
