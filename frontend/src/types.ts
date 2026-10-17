export interface CheckSpec {
  kind: string;
  types?: string[];
  comparison?: "exact" | "at_least";
  value?: number;
  distinct_bytes?: boolean;
  width_px?: number;
  height_px?: number;
  needle?: string;
  instruction?: string;
}
export interface SourceSpan {
  source_unit_id: string;
  evidence_unit_id?: string | null;
  catalog_version?: string | null;
  source_text_sha256: string;
  start_cp: number;
  end_cp: number;
  quote: string;
}
export interface AttentionRow {
  requirement_id: string;
  review_currency: "current" | "stale" | "unreviewed";
  human_disposition: string;
  applicable_attention: boolean;
  is_exception: boolean;
  reason_codes: string[];
  messages: string[];
  failed_check_count: number;
  unknown_check_count: number;
  has_manual_checks: boolean;
}
export interface AttentionSummary {
  contract_version: number;
  source_revision: number;
  input_hash: string;
  baseline_approved: boolean;
  status: string;
  requirement_count: number;
  current_review_count: number;
  stale_review_count: number;
  unreviewed_count: number;
  needs_work_count: number;
  unresolved_count: number;
  exception_count: number;
  failed_check_count: number;
  unknown_check_count: number;
  manual_requirement_count: number;
  failed_requirement_ids: string[];
  unknown_requirement_ids: string[];
  attention_requirement_ids: string[];
  exception_requirement_ids: string[];
  rows: AttentionRow[];
}
export interface Requirement {
  id: string;
  title: string;
  origin: "model_suggested" | "human_added";
  quote: string | null;
  source_id: string | null;
  evidence_unit_id?: string | null;
  source_span?: SourceSpan | null;
  checks: CheckSpec[];
  human_note: string;
}
export interface Artifact {
  id: string;
  name: string;
  type: string;
  size: number;
  sha256: string;
  inspection: string;
  metadata: Record<string, unknown>;
  text: string;
  error: string | null;
}
export interface Proposal {
  id: string;
  requirement_id: string;
  candidates: {
    file_id: string;
    reason: string;
    quote?: string;
    evidence_unit_id?: string | null;
    source_span?: SourceSpan | null;
  }[];
  coverage: string;
  model: Record<string, unknown>;
}
export interface Decision {
  requirement_id: string;
  file_ids: string[];
  review_state: string;
  human_disposition: string;
  internal_decision_note: string;
  client_usage_note: string;
  client_exception_note?: string;
  input_hash: string;
}
export interface Job {
  id: string;
  kind: string;
  state: string;
  stage: string;
  error: string | null;
}
export interface CheckResult {
  requirement_id: string;
  kind: string;
  status: string;
  reason: string;
  expected?: unknown;
  actual?: unknown;
}
export interface Project {
  id: string;
  name: string;
  revision: number;
  input_hash: string;
  brief: { id: string; text: string; label: string; sha256: string } | null;
  baseline: {
    id: string;
    state: string;
    hash: string;
    requirements: Requirement[];
  };
  files: Artifact[];
  proposals: Proposal[];
  decisions: Decision[];
  jobs: Job[];
  exports: {
    id: string;
    snapshot_hash: string;
    created_at?: string;
    status?: string;
    preview?: { input_hash: string };
  }[];
  checks?: CheckResult[];
  check_results?: CheckResult[];
  attention_summary?: AttentionSummary;
}
export interface Capabilities {
  model?: Record<string, unknown>;
  model_ready?: boolean;
  limits?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface ProjectOverview {
  id: string;
  name: string;
  created_at?: string;
  updated_at?: string | null;
  saved_review?: {
    status: string;
    baseline_approved: boolean;
    requirement_count: number;
    attention_count: number;
    stale_review_count: number;
    file_count: number;
    originals_verified: false;
  };
}
