export type DriveMode = "VIRTUAL" | "IN_PERSON" | "HYBRID";
export type DriveStatus = "SCHEDULED" | "IN_PROGRESS" | "COMPLETED" | "CANCELLED";
export type RoundType = "APTITUDE" | "CODING" | "TECHNICAL" | "HR" | "GROUP_DISCUSSION";
export type AttendanceStatus = "PENDING" | "CONFIRMED" | "PRESENT" | "ABSENT" | "RESCHEDULED";
export type RoundOutcome = "PENDING" | "SELECTED" | "NEXT_ROUND" | "ON_HOLD" | "NOT_SELECTED";

export interface InterviewSlotItem {
  id: string;
  round: string;
  student: string;
  student_roll: string;
  student_name: string;
  branch: string;
  scheduled_time: string;
  meeting_url: string;
  attendance_status: AttendanceStatus;
  outcome: RoundOutcome;
  evaluator_notes: string;
  evaluated_by_name: string | null;
  evaluated_at: string | null;
}

export interface InterviewRoundItem {
  id: string;
  drive: string;
  round_number: number;
  round_type: RoundType;
  round_name: string;
  instructions: string;
  slots_count: number;
  slots: InterviewSlotItem[];
}

export interface PlacementDriveItem {
  id: string;
  drive_code: string;
  title: string;
  job: string;
  job_title: string;
  company_name: string;
  drive_date: string;
  venue_or_link: string;
  drive_mode: DriveMode;
  status: DriveStatus;
  coordinator_name: string | null;
  rounds_count: number;
  created_at: string;
}

export interface PlacementDriveDetail extends PlacementDriveItem {
  instructions: string;
  rounds: InterviewRoundItem[];
}

export interface PaginatedDriveResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: PlacementDriveItem[];
}

export interface SubmissionPackageItem {
  id: string;
  package_code: string;
  title: string;
  job: string;
  job_title: string;
  company_name: string;
  status: string;
  candidates_count: number;
  roster_hash: string;
  dispatched_at: string | null;
  acknowledged_at: string | null;
  created_at: string;
}

export interface PlacementOfferItem {
  id: string;
  job: string;
  job_title: string;
  company_name: string;
  student: string;
  student_roll: string;
  student_name: string;
  branch: string;
  designation: string;
  ctc_lpa: string;
  offer_date: string;
  response_deadline: string;
  status: string;
  joining_status: string;
  actual_joining_date: string | null;
  created_at: string;
}

