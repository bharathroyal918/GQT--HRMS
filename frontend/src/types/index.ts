export type RoleCode =
  | "ADMIN"
  | "PLACEMENT_HEAD"
  | "PLACEMENT_OFFICER"
  | "CALLING_EXECUTIVE"
  | "CRM_EXECUTIVE"
  | "CREATIVE_DESIGNER"
  | "CREATIVE_REVIEWER"
  | "TRAINER"
  | "INTERVIEW_COORDINATOR"
  | "AUDITOR";

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  fullName: string;
  phone: string;
  isActive: boolean;
  isStaff: boolean;
  isSuperuser: boolean;
  roles: RoleCode[];
  createdAt?: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface ApiErrorResponse {
  detail?: string;
  message?: string;
  errors?: Record<string, string[]>;
}
