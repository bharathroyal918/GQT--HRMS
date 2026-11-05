import { apiClient, API_BASE_URL } from "./apiClient";
import {
  PaginatedAuditLogResponse,
  AuditLogItem,
  AuditSummaryMetrics,
  AuditFilterParams,
} from "../types/audit";

export const auditApi = {
  getAuditLogs: async (params?: AuditFilterParams): Promise<PaginatedAuditLogResponse> => {
    const res = await apiClient.get<PaginatedAuditLogResponse>("/audit-logs/", { params });
    return res.data;
  },

  getAuditLogDetail: async (id: string): Promise<AuditLogItem> => {
    const res = await apiClient.get<AuditLogItem>(`/audit-logs/${id}/`);
    return res.data;
  },

  getAuditSummary: async (): Promise<AuditSummaryMetrics> => {
    const res = await apiClient.get<AuditSummaryMetrics>("/audit-logs/summary/");
    return res.data;
  },

  exportAuditCsvUrl: (params?: AuditFilterParams): string => {
    const query = new URLSearchParams();
    if (params?.search) query.set("search", params.search);
    if (params?.action) query.set("action", params.action);
    if (params?.resource_type) query.set("resource_type", params.resource_type);
    if (params?.date_from) query.set("date_from", params.date_from);
    if (params?.date_to) query.set("date_to", params.date_to);
    return `${API_BASE_URL}/audit-logs/export/?${query.toString()}`;
  },
};

