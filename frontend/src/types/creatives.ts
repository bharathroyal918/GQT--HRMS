/**
 * Domain Type Definitions for Recruitment Creative Studio.
 */

export type CreativeStatus =
  | "DRAFT"
  | "SUBMITTED"
  | "ASSIGNED"
  | "IN_DESIGN"
  | "IN_REVIEW"
  | "CHANGES_REQUESTED"
  | "APPROVED"
  | "READY_FOR_HANDOFF"
  | "CANCELLED";

export type CreativeType =
  | "JOB_FLYER"
  | "WHATSAPP_BANNER"
  | "INSTAGRAM_POST"
  | "LINKEDIN_BANNER"
  | "EMAIL_HEADER"
  | "CAMPUS_POSTER"
  | "CUSTOM";

export type AspectRatio =
  | "1:1"
  | "16:9"
  | "9:16"
  | "4:5"
  | "A4_PORTRAIT"
  | "CUSTOM";

export type DeliverableFormat = "PNG" | "JPEG" | "WEBP" | "PDF" | "MULTI_FORMAT";

export type CreativePriority = "LOW" | "MEDIUM" | "HIGH" | "URGENT";

export type VersionStatus =
  | "DRAFT"
  | "SUBMITTED_FOR_REVIEW"
  | "CHANGES_REQUESTED"
  | "APPROVED"
  | "SUPERSEDED";

export type ComplianceCheckType =
  | "FLYER_TEXT_ACCURACY"
  | "BRAND_ASSETS_COMPLIANCE"
  | "QR_CODE_INTEGRITY"
  | "CONTACT_DISCLOSURE";

export type ComplianceCheckStatus = "PENDING" | "PASSED" | "FLAGGED";

export interface DesignComplianceCheck {
  id: string;
  check_type: ComplianceCheckType;
  check_type_display: string;
  status: ComplianceCheckStatus;
  notes: string;
  verified_by: string | null;
  verified_by_name: string;
  verified_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreativeAssetVersion {
  id: string;
  version_number: number;
  original_filename: string;
  file_size_bytes: number;
  mime_type: string;
  sha256_hash: string;
  width: number | null;
  height: number | null;
  designer_notes: string;
  status: VersionStatus;
  uploader: string;
  uploader_name: string;
  reviewed_by: string | null;
  reviewed_by_name: string;
  reviewed_at: string | null;
  review_feedback: string;
  compliance_checks: DesignComplianceCheck[];
  all_checks_passed: boolean;
  created_at: string;
}

export interface CreativeWorkflowHistory {
  id: string;
  from_status: string;
  to_status: string;
  actor: string | null;
  actor_name: string;
  action: string;
  notes: string;
  created_at: string;
}

export interface CreativeRequestListItem {
  id: string;
  request_code: string;
  title: string;
  creative_type: CreativeType;
  aspect_ratio: AspectRatio;
  deliverable_format: DeliverableFormat;
  priority: CreativePriority;
  status: CreativeStatus;
  target_completion_date: string | null;
  job_requirement: string | null;
  job_title: string;
  company: string | null;
  company_name: string;
  created_by: string;
  created_by_name: string;
  assigned_designer: string | null;
  assigned_designer_name: string;
  active_version_number: number | null;
  versions_count: number;
  created_at: string;
  updated_at: string;
}

export interface CreativeRequestDetail extends CreativeRequestListItem {
  brief: string;
  cancellation_reason: string;
  active_version: CreativeAssetVersion | null;
  versions: CreativeAssetVersion[];
  history: CreativeWorkflowHistory[];
}

export interface PaginatedCreativeResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: CreativeRequestListItem[];
}

export interface CreativeStudioMetrics {
  total_requests: number;
  triage_queue_count: number;
  in_design_count: number;
  in_review_count: number;
  approved_count: number;
  ready_for_handoff_count: number;
  total_asset_versions: number;
  pending_versions_review: number;
}

