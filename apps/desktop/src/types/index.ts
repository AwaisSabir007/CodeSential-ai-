export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'informational';
export type FindingStatus = 'open' | 'investigating' | 'resolved' | 'accepted_risk' | 'false_positive';

export interface Project {
  id: string;
  name: string;
  root_path: string;
  created_at: string;
  updated_at: string;
  is_monitored: boolean;
  scan_level: number;
  ignored_patterns: string[];
}

export interface Finding {
  id: string;
  project_id: string;
  scan_id?: string;
  scan_run_id?: string;
  scanner_name: string;
  rule_id: string;
  category: string;
  severity: Severity;
  confidence: number | string;
  file_path: string;
  start_line?: number;
  line_start?: number;
  end_line?: number;
  line_end?: number;
  title: string;
  description: string;
  code_snippet?: string;
  snippet?: string;
  recommendation?: string;
  cwe_id?: string;
  status: FindingStatus;
  created_at?: string;
  updated_at?: string;
}

export interface ScanRun {
  id: string;
  project_id: string;
  status: string;
  trigger_type: string;
  scan_level: number;
  started_at: string;
  completed_at?: string;
  duration_ms?: number;
  findings_count: number;
}

export interface AgentStepTrace {
  step_id: string;
  agent_name: string;
  action: string;
  status: string;
  duration_ms: number;
}

export interface Investigation {
  investigation_id: string;
  project_id: string;
  finding: {
    finding_id: string;
    title: string;
    rule_id: string;
    category: string;
    severity: string;
    file_path: string;
    line_number: number;
    snippet: string;
  };
  current_agent: string;
  status: 'in_progress' | 'completed' | 'failed' | 'cancelled';
  plan_steps: string[];
  completed_steps: string[];
  evidence: Array<{
    agent: string;
    analysis?: string;
    risk_score?: number;
    passed?: boolean;
    confidence?: number;
    summary?: string;
  }>;
  neural_risk_score?: number;
  neural_risk_explanation?: string;
  data_flow_analysis?: string;
  dependency_analysis?: string;
  performance_analysis?: string;
  candidate_patch?: string;
  patch_explanation?: string;
  verification_passed?: boolean;
  verification_details?: string[];
  evaluation_confidence?: number;
  evaluation_summary?: string;
}

export interface ProposedPatch {
  patch_id: string;
  finding_id: string;
  file_path: string;
  original_code: string;
  modified_code: string;
  diff: {
    unified_diff: string;
    additions: number;
    deletions: number;
  };
  explanation: string;
  status: 'pending' | 'verified' | 'approved' | 'rejected' | 'applied';
  validation: {
    is_valid: boolean;
    errors: string[];
  };
}

export interface SystemHealth {
  status: string;
  version: string;
  scanners_available: number;
  active_scans: number;
  monitored_projects: number;
}

export interface ModelMetrics {
  dataset_size: number;
  baseline_a_static_only: {
    accuracy: number;
    precision: number;
    recall: number;
    f1_score: number;
    false_positive_rate: number;
    roc_auc: number;
    average_latency_ms: number;
  };
  baseline_b_static_plus_neural: {
    accuracy: number;
    precision: number;
    recall: number;
    f1_score: number;
    false_positive_rate: number;
    roc_auc: number;
    average_latency_ms: number;
  };
  baseline_c_full_agentic: {
    accuracy: number;
    precision: number;
    recall: number;
    f1_score: number;
    false_positive_rate: number;
    roc_auc: number;
    average_latency_ms: number;
  };
  academic_conclusion: string;
}
