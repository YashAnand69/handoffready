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
export interface Requirement {
  id: string;
  title: string;
  origin: "model_suggested" | "human_added";
  quote: string | null;
  source_id: string | null;
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
  candidates: { file_id: string; reason: string; quote?: string }[];
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
}
export interface Capabilities {
  model?: Record<string, unknown>;
  model_ready?: boolean;
  limits?: Record<string, unknown>;
  [key: string]: unknown;
}
