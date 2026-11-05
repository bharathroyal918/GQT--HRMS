export interface AuditUser {
  id: string;
  email: string;
  full_name: string;
}

export interface AuditLogItem {
  id: string;
  user: AuditUser | null;
  action: string;
  resource_type: string;
  resource_id: string;
  ip_address: string | null;
  user_agent: string;
  changes: Record<string, any>;
  correlation_id: string;
  created_at: string;
}

export interface PaginatedAuditLogResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: AuditLogItem[];
}

export interface AuditSummaryMetrics {
  total_count: number;
  today_count: number;
  unique_actors: number;
  unique_resource_types: number;
  top_actions: Array<{ action: string; count: number }>;
  recent_critical_actions: Array<{ action: string; count: number }>;
}

export interface AuditFilterParams {
  search?: string;
  action?: string;
  resource_type?: string;
  user_id?: string;
  correlation_id?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

