export type CompanyStatus =
  | "LEAD"
  | "CONTACTED"
  | "ENGAGED"
  | "ACTIVE_HIRING_PARTNER"
  | "DORMANT"
  | "BLACKLISTED";

export type CompanyTier = "TIER_1" | "TIER_2" | "TIER_3" | "UNRATED";

export type IndustryType =
  | "IT_SERVICES"
  | "PRODUCT_TECH"
  | "FINTECH"
  | "EDTECH"
  | "HEALTHCARE"
  | "MANUFACTURING"
  | "ECOMMERCE"
  | "CONSULTING"
  | "TELECOM"
  | "OTHER";

export type AcquisitionSource =
  | "OUTBOUND_CALLING"
  | "INBOUND_INQUIRY"
  | "JOB_PORTAL"
  | "CAMPUS_ALUMNI"
  | "LINKEDIN"
  | "EXECUTIVE_REFERRAL"
  | "OTHER";

export type ContactStatus = "ACTIVE" | "INACTIVE" | "FORMER_EMPLOYEE";

export type PreferredChannel = "EMAIL" | "PHONE" | "WHATSAPP" | "LINKEDIN";

export type OutreachChannel = "PHONE" | "EMAIL" | "WHATSAPP" | "LINKEDIN" | "IN_PERSON" | "OTHER";

export type OutreachOutcome =
  | "INTERESTED"
  | "FOLLOW_UP_REQUESTED"
  | "NOT_INTERESTED"
  | "CALL_NOT_ANSWERED"
  | "WRONG_NUMBER"
  | "GATEKEEPER_BLOCKED"
  | "MEETING_SCHEDULED"
  | "REQUIREMENT_SHARED";

export type FollowUpPriority = "LOW" | "MEDIUM" | "HIGH" | "URGENT";

export type FollowUpStatus = "PENDING" | "COMPLETED" | "RESCHEDULED" | "CANCELLED";

export interface Company {
  id: string;
  name: string;
  normalized_name: string;
  website: string;
  canonical_domain: string;
  industry: IndustryType;
  source: AcquisitionSource;
  status: CompanyStatus;
  tier: CompanyTier;
  assigned_to: string | null;
  assigned_to_name: string | null;
  contacts_count: number;
  outreach_count: number;
  pending_followups_count: number;
  created_at: string;
  updated_at: string;
}

export interface HRContact {
  id: string;
  company: string;
  company_name?: string;
  name: string;
  designation: string;
  department: string;
  email: string;
  phone: string;
  alternate_phone: string;
  linkedin_url: string;
  preferred_channel: PreferredChannel;
  status: ContactStatus;
  is_primary: boolean;
  notes: string;
  assigned_to: string | null;
  created_at: string;
  updated_at: string;
}

export interface OutreachActivity {
  id: string;
  company: string;
  company_name: string;
  contact: string | null;
  contact_name: string | null;
  executive: string;
  executive_name: string;
  attempted_at: string;
  channel: OutreachChannel;
  outcome: OutreachOutcome;
  notes: string;
  next_action: string;
  follow_up_date: string | null;
  created_at: string;
}

export interface FollowUp {
  id: string;
  company: string;
  company_name: string;
  contact: string | null;
  contact_name: string | null;
  outreach_activity: string | null;
  assigned_to: string;
  assigned_to_name: string;
  title: string;
  description: string;
  due_date: string;
  priority: FollowUpPriority;
  status: FollowUpStatus;
  is_overdue: boolean;
  is_due_today: boolean;
  completed_at: string | null;
  completed_by: string | null;
  cancellation_reason: string;
  created_at: string;
}

export interface CompanyDetail extends Company {
  notes: string;
  contacts: HRContact[];
  recent_outreach: OutreachActivity[];
  active_follow_ups: FollowUp[];
}

export interface DuplicateCheckResult {
  is_duplicate: boolean;
  match_count: number;
  matches: Array<{
    id: string;
    name: string;
    canonical_domain: string;
    status: string;
    match_reason: string;
  }>;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

