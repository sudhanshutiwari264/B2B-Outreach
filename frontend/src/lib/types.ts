export type OutreachChannel = "email" | "linkedin";

export type ExecutionStatus =
  | "queued"
  | "running"
  | "completed"
  | "partial"
  | "needs_review"
  | "insufficient_data"
  | "failed";

export type SourceType =
  | "linkedin_profile"
  | "linkedin_post"
  | "company_website"
  | "company_news"
  | "press_release"
  | "job_posting"
  | "funding_news"
  | "interview"
  | "podcast"
  | "industry_publication"
  | "other";

export type EvidenceType = "full_page" | "search_snippet" | "metadata" | "user_provided";

export type ExtractionStatus = "success" | "failed" | "restricted" | "skipped" | "pending";

export type VerificationStatus =
  | "pending"
  | "verified"
  | "disputed"
  | "restricted"
  | "needs_review"
  | "rejected";

export type SignalType =
  | "professional_activity"
  | "job_change"
  | "leadership_announcement"
  | "company_growth"
  | "funding"
  | "hiring"
  | "product_development"
  | "business_challenge"
  | "thought_leadership"
  | "partnership"
  | "public_speaking"
  | "industry_development";

export type RelevanceTier = "high" | "medium" | "low";

export type DraftStatus = "draft_generated" | "pending_review" | "edited" | "approved" | "rejected";

export type StageStatus = "started" | "success" | "failed" | "skipped";

export interface Prospect {
  id: string;
  name: string;
  company: string;
  designation: string;
  linkedin_url: string | null;
  company_website: string | null;
  industry: string | null;
  outreach_channel: OutreachChannel;
  product_context: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProspectCreateInput {
  name: string;
  company: string;
  designation: string;
  linkedin_url?: string | null;
  company_website?: string | null;
  industry?: string | null;
  outreach_channel?: OutreachChannel;
  product_context?: string | null;
}

export interface Execution {
  id: string;
  prospect_id: string;
  status: ExecutionStatus;
  current_stage: string | null;
  started_at: string | null;
  completed_at: string | null;
  result_summary: Record<string, unknown> | null;
  failure_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExecutionLog {
  id: string;
  execution_id: string;
  stage_name: string;
  status: StageStatus;
  started_at: string;
  ended_at: string | null;
  duration_ms: number | null;
  output_metadata: Record<string, unknown> | null;
  error_message: string | null;
}

export interface ResearchSource {
  id: string;
  execution_id: string;
  url: string;
  normalized_url: string;
  title: string | null;
  domain: string | null;
  source_type: SourceType;
  evidence_type: EvidenceType;
  content: string | null;
  content_hash: string | null;
  published_at: string | null;
  discovered_at: string;
  extracted_at: string | null;
  extraction_status: ExtractionStatus;
  extraction_error: string | null;
  verification_status: VerificationStatus;
}

export interface Signal {
  id: string;
  execution_id: string;
  source_id: string;
  signal_type: SignalType;
  description: string;
  entity: string;
  company: string | null;
  published_at: string | null;
  evidence_excerpt: string;
  relevance_reason: string;
  confidence_score: number;
  relevance_score: number | null;
  business_impact_score: number | null;
  recency_score: number | null;
  evidence_quality_score: number | null;
  final_score: number | null;
  relevance_tier: RelevanceTier | null;
  verification_status: VerificationStatus;
  is_disputed: boolean;
}

export interface OutreachDraft {
  id: string;
  execution_id: string;
  channel: OutreachChannel;
  subject: string | null;
  body: string;
  edited_subject: string | null;
  edited_body: string | null;
  used_signal_ids: string[];
  used_source_ids: string[];
  validation_report: {
    passed: boolean;
    issues: string[];
    checks: Record<string, boolean>;
  } | null;
  status: DraftStatus;
  reviewer_notes: string | null;
}

export interface HealthIntegrations {
  tavily: { configured: boolean; reachable?: boolean; sample_result_count?: number; error?: string };
  tarqa: { configured: boolean; reachable?: boolean; model?: string; error?: string };
}
