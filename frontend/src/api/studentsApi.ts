import { apiClient } from "./apiClient";
import {
  PaginatedStudentResponse,
  StudentDetail,
  StudentMetrics,
  StudentFilterParams,
  EligibilityEvaluationResult,
  ReadinessStatusResponse,
} from "../types/students";

export const studentsApi = {
  getStudents: async (params?: StudentFilterParams): Promise<PaginatedStudentResponse> => {
    const res = await apiClient.get<PaginatedStudentResponse>("/students/", { params });
    return res.data;
  },

  getStudentDetail: async (id: string): Promise<StudentDetail> => {
    const res = await apiClient.get<StudentDetail>(`/students/${id}/`);
    return res.data;
  },

  getStudentMetrics: async (): Promise<StudentMetrics> => {
    const res = await apiClient.get<StudentMetrics>("/students/metrics/");
    return res.data;
  },

  evaluateEligibility: async (studentId: string, jobId: string): Promise<EligibilityEvaluationResult> => {
    const res = await apiClient.post<EligibilityEvaluationResult>("/students/eligibility/check/", {
      student_id: studentId,
      job_id: jobId,
    });
    return res.data;
  },

  overrideEligibility: async (evaluationId: string, reason: string): Promise<EligibilityEvaluationResult> => {
    const res = await apiClient.post<EligibilityEvaluationResult>("/students/eligibility/override/", {
      evaluation_id: evaluationId,
      reason,
    });
    return res.data;
  },

  registerForDrive: async (studentId: string, jobId: string): Promise<any> => {
    const res = await apiClient.post("/students/registrations/", {
      student: studentId,
      job: jobId,
    });
    return res.data;
  },

  checkReadinessStatus: async (studentId: string, jobId: string): Promise<ReadinessStatusResponse> => {
    const res = await apiClient.get<ReadinessStatusResponse>("/preparation/readiness/status/", {
      params: { student_id: studentId, job_id: jobId },
    });
    return res.data;
  },

  certifyReadiness: async (studentId: string, jobId: string, notes?: string): Promise<any> => {
    const res = await apiClient.post("/preparation/readiness/certify/", {
      student_id: studentId,
      job_id: jobId,
      notes: notes || "",
    });
    return res.data;
  },
};

