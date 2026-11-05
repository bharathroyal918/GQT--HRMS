import { apiClient } from "./apiClient";
import {
  PaginatedDriveResponse,
  PlacementDriveDetail,
  SubmissionPackageItem,
  PlacementOfferItem,
} from "../types/interviews";

export const interviewsApi = {
  getDrives: async (params?: { status?: string; page?: number }): Promise<PaginatedDriveResponse> => {
    const res = await apiClient.get<PaginatedDriveResponse>("/interviews/", { params });
    return res.data;
  },

  getDriveDetail: async (id: string): Promise<PlacementDriveDetail> => {
    const res = await apiClient.get<PlacementDriveDetail>(`/interviews/${id}/`);
    return res.data;
  },

  createDrive: async (payload: {
    job_id: string;
    title: string;
    drive_date: string;
    venue_or_link: string;
    drive_mode?: string;
    instructions?: string;
  }): Promise<PlacementDriveDetail> => {
    const res = await apiClient.post<PlacementDriveDetail>("/interviews/", payload);
    return res.data;
  },

  addRound: async (driveId: string, payload: {
    round_number: number;
    round_type: string;
    round_name: string;
    instructions?: string;
  }): Promise<any> => {
    const res = await apiClient.post(`/interviews/${driveId}/rounds/`, payload);
    return res.data;
  },

  scheduleSlot: async (roundId: string, payload: {
    student_id: string;
    scheduled_time: string;
    meeting_url?: string;
  }): Promise<any> => {
    const res = await apiClient.post(`/interviews/rounds/${roundId}/schedule/`, payload);
    return res.data;
  },

  updateSlotOutcome: async (slotId: string, payload: {
    attendance_status?: string;
    outcome?: string;
    evaluator_notes?: string;
  }): Promise<any> => {
    const res = await apiClient.patch(`/interviews/slots/${slotId}/outcome/`, payload);
    return res.data;
  },

  getSubmissions: async (params?: { job_id?: string }): Promise<{ count: number; results: SubmissionPackageItem[] }> => {
    const res = await apiClient.get("/submissions/", { params });
    return res.data;
  },

  getOffers: async (params?: { status?: string }): Promise<{ count: number; results: PlacementOfferItem[] }> => {
    const res = await apiClient.get("/placements/offers/", { params });
    return res.data;
  },
};

