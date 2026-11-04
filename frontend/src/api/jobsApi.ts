/**
 * API client methods for Phase 3 Job Requirements, 5-Point Verification, and Approvals.
 */
import { apiClient } from "./apiClient";
import {
  PaginatedJobResponse,
  JobRequirementDetail,
  JobFormData,
  JobVerificationCheck,
  JobWorkflowMetrics,
  CheckStatus,
} from "../types/jobs";

export interface JobFilterParams {
  search?: string;
  status?: string;
  role_category?: string;
  company_id?: string;
  work_arrangement?: string;
  has_bond?: boolean;
  min_ctc?: number;
  page?: number;
  page_size?: number;
}

export const jobsApi = {
  getJobs: async (params?: JobFilterParams): Promise<PaginatedJobResponse> => {
    const res = await apiClient.get<PaginatedJobResponse>("/jobs/requirements/", { params });
    return res.data;
  },

  getJobDetail: async (id: string): Promise<JobRequirementDetail> => {
    const res = await apiClient.get<JobRequirementDetail>(`/jobs/requirements/${id}/`);
    return res.data;
  },

  createJob: async (payload: Partial<JobFormData>): Promise<JobRequirementDetail> => {
    const res = await apiClient.post<JobRequirementDetail>("/jobs/requirements/", payload);
    return res.data;
  },

  updateJob: async (id: string, payload: Partial<JobFormData>): Promise<JobRequirementDetail> => {
    const res = await apiClient.patch<JobRequirementDetail>(`/jobs/requirements/${id}/`, payload);
    return res.data;
  },

  deleteJob: async (id: string): Promise<void> => {
    await apiClient.delete(`/jobs/requirements/${id}/`);
  },

  submitForVerification: async (id: string): Promise<JobRequirementDetail> => {
    const res = await apiClient.post<JobRequirementDetail>(`/jobs/requirements/${id}/submit/`);
    return res.data;
  },

  assignVerifier: async (id: string, verifierId: string): Promise<JobRequirementDetail> => {
    const res = await apiClient.post<JobRequirementDetail>(`/jobs/requirements/${id}/assign-verifier/`, {
      verifier_id: verifierId,
    });
    return res.data;
  },

  updateCheck: async (
    jobId: string,
    checkType: string,
    payload: { status: CheckStatus; notes?: string; evidence_reference?: string }
  ): Promise<JobVerificationCheck> => {
    const res = await apiClient.post<JobVerificationCheck>(
      `/jobs/requirements/${jobId}/checks/${checkType}/`,
      payload
    );
    return res.data;
  },

  requestChanges: async (id: string, reason: string): Promise<JobRequirementDetail> => {
    const res = await apiClient.post<JobRequirementDetail>(`/jobs/requirements/${id}/request-changes/`, {
      reason,
    });
    return res.data;
  },

  approveJob: async (id: string, notes?: string): Promise<JobRequirementDetail> => {
    const res = await apiClient.post<JobRequirementDetail>(`/jobs/requirements/${id}/approve/`, {
      notes: notes || "",
    });
    return res.data;
  },

  rejectJob: async (id: string, reason: string): Promise<JobRequirementDetail> => {
    const res = await apiClient.post<JobRequirementDetail>(`/jobs/requirements/${id}/reject/`, {
      reason,
    });
    return res.data;
  },

  amendApprovedJob: async (
    id: string,
    payload: { reason: string } & Partial<JobFormData>
  ): Promise<JobRequirementDetail> => {
    const res = await apiClient.post<JobRequirementDetail>(`/jobs/requirements/${id}/amend/`, payload);
    return res.data;
  },

  getVerificationQueue: async (): Promise<PaginatedJobResponse> => {
    const res = await apiClient.get<PaginatedJobResponse>("/jobs/verification-queue/");
    return res.data;
  },

  getApprovalQueue: async (): Promise<PaginatedJobResponse> => {
    const res = await apiClient.get<PaginatedJobResponse>("/jobs/approval-queue/");
    return res.data;
  },

  getWorkflowMetrics: async (): Promise<JobWorkflowMetrics> => {
    const res = await apiClient.get<JobWorkflowMetrics>("/jobs/metrics/");
    return res.data;
  },
};

