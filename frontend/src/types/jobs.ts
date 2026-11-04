/**
 * Phase 3: Job Requirements, 5-Point Verification, and Approval Domain Typings
 */

export type JobStatus =
  | "DRAFT"
  | "PENDING_VERIFICATION"
  | "UNDER_VERIFICATION"
  | "CHANGES_REQUESTED"
  | "PENDING_APPROVAL"
  | "APPROVED"
  | "REJECTED";

export type RoleCategory =
  | "SOFTWARE_ENGINEERING"
  | "DATA_ANALYTICS"
  | "CLOUD_DEVOPS"
  | "QA_TESTING"
  | "PRODUCT_SUPPORT"
  | "CYBERSECURITY"
  | "BUSINESS_ANALYST"
  | "OTHER";

export type WorkArrangement = "ONSITE" | "HYBRID" | "REMOTE";

export type VerificationCheckType =
  | "ELIGIBILITY"
  | "SALARY_AUTHENTICITY"
  | "COMPANY_AUTHENTICITY"
  | "INTERVIEW_PROCESS"
  | "REGISTRATION_DEADLINE";

export type CheckStatus = "PENDING" | "VERIFIED" | "FLAGGED" | "REJECTED";

export interface VerificationSummary {
  total_mandatory_checks: number;
  verified_count: number;
  flagged_count: number;
  rejected_count: number;
  pending_count: number;
  is_all_verified: boolean;
}

export interface JobVerificationCheck {
  id: string;
  check_type: VerificationCheckType;
  status: CheckStatus;
  verified_by: string | null;
  verified_by_name: string;
  verified_by_email: string;
  verified_at: string | null;
  notes: string;
  evidence_reference: string;
  requires_reverification: boolean;
  invalidation_reason: string;
  created_at: string;
  updated_at: string;
}

export interface JobWorkflowHistory {
  id: string;
  from_status: string;
  to_status: string;
  actor: string | null;
  actor_name: string;
  actor_email: string;
  action: string;
  notes: string;
  created_at: string;
}

export interface InterviewRoundItem {
  round_number: number;
  round_type: "APTITUDE" | "CODING" | "TECHNICAL" | "HR" | "MANAGERIAL" | "OTHER";
  description: string;
}

export interface JobRequirementListItem {
  id: string;
  company: string;
  company_name: string;
  company_canonical_domain: string;
  title: string;
  role_category: RoleCategory;
  job_location: string;
  work_arrangement: WorkArrangement;
  min_ctc_lpa: string;
  max_ctc_lpa: string;
  vacancies_count: number | null;
  registration_deadline: string;
  interview_date: string | null;
  status: JobStatus;
  revision_number: number;
  submitted_by: string | null;
  submitted_by_name: string;
  assigned_verifier: string | null;
  assigned_verifier_name: string;
  verification_summary: VerificationSummary;
  created_at: string;
  updated_at: string;
}

export interface JobRequirementDetail extends JobRequirementListItem {
  company_industry: string;
  description: string;
  required_skills: string[];
  min_cgpa: string | null;
  min_percentage: string | null;
  eligible_batches: string[];
  eligible_branches: string[];
  max_backlogs_allowed: number;
  stipend_amount: string | null;
  salary_details: string;
  has_bond: boolean;
  bond_duration_months: number | null;
  bond_details: string;
  interview_rounds: InterviewRoundItem[];
  interview_process_notes: string;
  submitted_by_email: string;
  assigned_verifier_email: string;
  approved_by: string | null;
  approved_by_name: string;
  approved_at: string | null;
  rejected_by: string | null;
  rejected_by_name: string;
  rejected_at: string | null;
  rejection_reason: string;
  changes_requested_reason: string;
  verification_checks: JobVerificationCheck[];
  workflow_history: JobWorkflowHistory[];
  is_all_checks_verified: boolean;
}

export interface JobFormData {
  company: string;
  title: string;
  description: string;
  role_category: RoleCategory;
  required_skills: string[];
  min_cgpa?: number | null;
  min_percentage?: number | null;
  eligible_batches: string[];
  eligible_branches: string[];
  max_backlogs_allowed: number;
  min_ctc_lpa: number;
  max_ctc_lpa: number;
  stipend_amount?: number | null;
  salary_details?: string;
  job_location?: string;
  work_arrangement: WorkArrangement;
  has_bond: boolean;
  bond_duration_months?: number | null;
  bond_details?: string;
  interview_rounds?: InterviewRoundItem[];
  interview_process_notes?: string;
  interview_date?: string | null;
  registration_deadline: string;
  vacancies_count?: number | null;
}

export interface JobWorkflowMetrics {
  total_jobs: number;
  draft_jobs: number;
  pending_verification_jobs: number;
  under_verification_jobs: number;
  changes_requested_jobs: number;
  pending_approval_jobs: number;
  approved_jobs: number;
  rejected_jobs: number;
  verification_stats: {
    total_checks: number;
    verified_checks: number;
    pending_checks: number;
    flagged_checks: number;
    rejected_checks: number;
  };
}

export interface PaginatedJobResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: JobRequirementListItem[];
}

