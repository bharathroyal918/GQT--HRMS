export type PlacementStatus = "SEEKING" | "PLACED" | "OPTED_OUT" | "INELIGIBLE";
export type RegistrationStatus = "REGISTERED" | "SHORTLISTED" | "REJECTED" | "WITHDRAWN";
export type ResumeReviewStatus = "APPROVED" | "NEEDS_IMPROVEMENT";

export interface StudentResume {
  id: string;
  version: number;
  file_name: string;
  file_hash: string;
  file_size_bytes: number;
  is_verified: boolean;
  verified_at: string | null;
  created_at: string;
}

export interface StudentListItem {
  id: string;
  roll_number: string;
  full_name: string;
  email: string;
  phone: string;
  degree: string;
  branch: string;
  graduation_year: number;
  cgpa: string;
  backlogs_count: number;
  placement_status: PlacementStatus;
  is_active: boolean;
  latest_resume_version: number | null;
  is_resume_verified: boolean;
  created_at: string;
}

export interface StudentDetail extends StudentListItem {
  tenth_percentage: string | null;
  twelfth_percentage: string | null;
  skills: string[];
  notes: string;
  resumes: StudentResume[];
  updated_at: string;
}

export interface PaginatedStudentResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: StudentListItem[];
}

export interface StudentMetrics {
  total_students: number;
  placed_students: number;
  seeking_students: number;
  opted_out_students: number;
  placement_rate_pct: number;
  branch_breakdown: Array<{ branch: string; total: number; placed: number }>;
}

export interface StudentFilterParams {
  search?: string;
  branch?: string;
  graduation_year?: number;
  placement_status?: string;
  is_active?: boolean;
  page?: number;
  page_size?: number;
}

export interface EligibilityEvaluationResult {
  id: string;
  student: string;
  job: string;
  job_title: string;
  company_name: string;
  is_eligible: boolean;
  failed_criteria: string[];
  evaluated_at: string;
  manually_overridden: boolean;
  overridden_by_name: string | null;
  override_reason: string;
}

export interface ReadinessStatusResponse {
  student_id: string;
  job_id: string;
  can_certify: boolean;
  missing_criteria: string[];
  is_certified: boolean;
}

