/**
 * API client methods for Phase 4 Creative Studio & Design Asset Approval.
 */
import { apiClient, API_BASE_URL } from "./apiClient";
import {
  PaginatedCreativeResponse,
  CreativeRequestDetail,
  CreativeAssetVersion,
  DesignComplianceCheck,
  CreativeStudioMetrics,
  ComplianceCheckStatus,
} from "../types/creatives";

export interface CreativeFilterParams {
  search?: string;
  status?: string;
  priority?: string;
  creative_type?: string;
  assigned_to?: string;
  page?: number;
  page_size?: number;
}

export interface CreateCreativeRequestPayload {
  title: string;
  brief: string;
  creative_type?: string;
  aspect_ratio?: string;
  deliverable_format?: string;
  priority?: string;
  target_completion_date?: string | null;
  job_requirement_id?: string | null;
  company_id?: string | null;
}

export const creativesApi = {
  getRequests: async (params?: CreativeFilterParams): Promise<PaginatedCreativeResponse> => {
    const res = await apiClient.get<PaginatedCreativeResponse>("/creatives/requests/", { params });
    return res.data;
  },

  getRequestDetail: async (id: string): Promise<CreativeRequestDetail> => {
    const res = await apiClient.get<CreativeRequestDetail>(`/creatives/requests/${id}/`);
    return res.data;
  },

  createRequest: async (payload: CreateCreativeRequestPayload): Promise<CreativeRequestDetail> => {
    const res = await apiClient.post<CreativeRequestDetail>("/creatives/requests/", payload);
    return res.data;
  },

  updateRequest: async (id: string, payload: Partial<CreateCreativeRequestPayload>): Promise<CreativeRequestDetail> => {
    const res = await apiClient.patch<CreativeRequestDetail>(`/creatives/requests/${id}/`, payload);
    return res.data;
  },

  submitRequest: async (id: string): Promise<CreativeRequestDetail> => {
    const res = await apiClient.post<CreativeRequestDetail>(`/creatives/requests/${id}/submit/`);
    return res.data;
  },

  assignDesigner: async (
    id: string,
    payload: { assigned_designer_id: string; priority?: string; notes?: string }
  ): Promise<CreativeRequestDetail> => {
    const res = await apiClient.post<CreativeRequestDetail>(`/creatives/requests/${id}/assign/`, payload);
    return res.data;
  },

  uploadVersion: async (
    requestId: string,
    formData: FormData
  ): Promise<CreativeAssetVersion> => {
    const res = await apiClient.post<CreativeAssetVersion>(
      `/creatives/requests/${requestId}/upload_version/`,
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
      }
    );
    return res.data;
  },

  evaluateCheck: async (
    versionId: string,
    checkType: string,
    payload: { status: ComplianceCheckStatus; notes?: string }
  ): Promise<DesignComplianceCheck> => {
    const res = await apiClient.post<DesignComplianceCheck>(
      `/creatives/versions/${versionId}/checks/${checkType}/`,
      payload
    );
    return res.data;
  },

  approveVersion: async (
    versionId: string,
    payload?: { review_feedback?: string }
  ): Promise<CreativeAssetVersion> => {
    const res = await apiClient.post<CreativeAssetVersion>(
      `/creatives/versions/${versionId}/approve/`,
      payload || {}
    );
    return res.data;
  },

  requestChanges: async (
    versionId: string,
    payload: { review_feedback: string }
  ): Promise<CreativeAssetVersion> => {
    const res = await apiClient.post<CreativeAssetVersion>(
      `/creatives/versions/${versionId}/request_changes/`,
      payload
    );
    return res.data;
  },

  markReadyForHandoff: async (
    id: string,
    payload?: { notes?: string }
  ): Promise<CreativeRequestDetail> => {
    const res = await apiClient.post<CreativeRequestDetail>(
      `/creatives/requests/${id}/handoff/`,
      payload || {}
    );
    return res.data;
  },

  cancelRequest: async (
    id: string,
    payload: { cancellation_reason: string }
  ): Promise<CreativeRequestDetail> => {
    const res = await apiClient.post<CreativeRequestDetail>(
      `/creatives/requests/${id}/cancel/`,
      payload
    );
    return res.data;
  },

  getTriageQueue: async (): Promise<CreativeRequestDetail[]> => {
    const res = await apiClient.get<CreativeRequestDetail[]>("/creatives/queues/triage/");
    return res.data;
  },

  getDesignerQueue: async (): Promise<CreativeRequestDetail[]> => {
    const res = await apiClient.get<CreativeRequestDetail[]>("/creatives/queues/designer/");
    return res.data;
  },

  getReviewQueue: async (): Promise<CreativeAssetVersion[]> => {
    const res = await apiClient.get<CreativeAssetVersion[]>("/creatives/queues/review/");
    return res.data;
  },

  getHandoffQueue: async (): Promise<CreativeRequestDetail[]> => {
    const res = await apiClient.get<CreativeRequestDetail[]>("/creatives/queues/handoff/");
    return res.data;
  },

  getStudioMetrics: async (): Promise<CreativeStudioMetrics> => {
    const res = await apiClient.get<CreativeStudioMetrics>("/creatives/metrics/");
    return res.data;
  },

  getAssetDownloadUrl: (versionId: string, download: boolean = false): string => {
    const param = download ? "?download=true" : "";
    return `${API_BASE_URL}/creatives/versions/${versionId}/download/${param}`;
  },
};

