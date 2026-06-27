// ─── Policy Extraction Types ─────────────────────────────────────────────────

export type PolicyType =
  | "whole_life" | "term" | "critical_illness" | "early_critical_illness"
  | "hospital" | "disability" | "careshield_supplement"
  | "personal_accident" | "unknown";

export interface Rider {
  rider_type: string;
  sum_assured?: number;
  conditions_covered?: number;
}

export interface FinePrintClause {
  text: string;
  page?: number;
  category: "exclusion" | "waiting_period" | "non_disclosure" | "hazard";
}

export interface ExtractedPolicy {
  source_filename: string;
  policy_number?: string;
  policy_type: PolicyType;
  insurer?: string;
  sum_assured?: number;
  tpd_sum_assured?: number;
  coverage_start?: string;
  coverage_end?: string;
  maturity_age?: number;
  monthly_premium?: number;
  annual_premium?: number;
  waiting_period_days?: number;
  riders: Rider[];
  exclusions: string[];
  fine_print_clauses: FinePrintClause[];
  cash_value?: boolean;
  medishield_integrated?: boolean;
  ip_ward_tier?: string;
  missing_fields: string[];
  low_confidence_fields: string[];
  unreadable_pages: number[];
}

export interface ExtractionResult {
  session_id: string;
  policies: ExtractedPolicy[];
  has_flags: boolean;
  extraction_flags: string[];
}

// ─── Profile Types ────────────────────────────────────────────────────────────

export type Gender = "male" | "female" | "other";
export type OccupationRisk = "low" | "medium" | "high";
export type CitizenshipStatus = "sc" | "pr" | "ep_holder" | "other_foreigner";
export type EmploymentStatus = "employed" | "self_employed" | "unemployed" | "retired" | "student";

export interface EmployerGroupCoverage {
  has_group_coverage: boolean;
  estimated_group_life_sa?: number;
  estimated_group_hospital_tier?: string;
  estimated_group_ci_sa?: number;
}

export interface MedicalProfile {
  pre_existing_conditions: string[];
  medications: string[];
  family_history: string[];
  height_cm?: number;
  weight_kg?: number;
  occupation_risk: OccupationRisk;
  high_risk_activities: string[];
}

export interface UserProfile {
  age: number;
  gender: Gender;
  citizenship_status: CitizenshipStatus;
  employment_status: EmploymentStatus;
  annual_income?: number;
  dependents: number;
  smoker: boolean;
  employer_group_coverage: EmployerGroupCoverage;
  medical: MedicalProfile;
}

// ─── Report Types ─────────────────────────────────────────────────────────────

export type GapStatus = "adequate" | "underinsured" | "oversold" | "redundant" | "not_assessable";
export type Priority = "urgent" | "high" | "medium" | "low";
export type RiskLevel = "high" | "medium" | "low";
export type ActionType = "add_base" | "add_rider" | "increase" | "reduce";

export interface Citation {
  source_document: string;
  source_page?: string;
  chunk_id: string;
  chunk_text: string;
}

export interface ReportGap {
  category: string;
  status: GapStatus;
  priority: Priority;
  you_have?: number;
  recommended_low?: number;
  recommended_high?: number;
  gap_low?: number;
  gap_high?: number;
  explanation: string;
  citation?: Citation;
}

export interface ClaimRisk {
  source_filename: string;
  insurer?: string;
  clause_text: string;
  clause_page?: number;
  matched_data_point: string;
  risk_level: RiskLevel;
  plain_english_meaning: string;
  reason: string;
  recommendation: string;
}

export interface RecommendationItem {
  generic_type: string;
  action: ActionType;
  reason: string;
  source: string;
  confidence: number;
}

export interface RecommendationResult {
  items: RecommendationItem[];
  premium_burden_warning?: string;
  notes: string[];
}

export interface GapReport {
  session_id: string;
  summary: string;
  gaps: ReportGap[];
  claim_risks: ClaimRisk[];
  recommendation: RecommendationResult;
  next_steps: string[];
  disclaimers: string[];
  extraction_flags: string[];
}

// ─── Guidance Types ───────────────────────────────────────────────────────────

export interface GuidanceAnswers {
  q1_income_earner?: string;
  q2_family_history?: string;
  q3_coverage_goal?: string;
}

export interface GuidanceBrief {
  mode: "coverage_structure" | "rider";
  user_goal?: string;
  priority_categories: string[];
  source_document_text?: string;
}

// ─── UI State Types ───────────────────────────────────────────────────────────

export type FileStatus = "queued" | "uploading" | "extracting" | "done" | "failed";

export interface PolicyFileState {
  file: File;
  status: FileStatus;
  error?: string;
  policy?: ExtractedPolicy;
}
