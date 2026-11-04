/** Recruitment CRM Axios API Client. */
import { apiClient } from "./apiClient";
import {
  Company,
  CompanyDetail,
  HRContact,
  OutreachActivity,
  FollowUp,
  DuplicateCheckResult,
  PaginatedResponse,
} from "../types/crm";

export const crmApi = {
  // Companies
  getCompanies: async (params?: Record<string, any>): Promise<PaginatedResponse<Company>> => {
    const res = await apiClient.get<PaginatedResponse<Company>>("/crm/companies/", { params });
    return res.data;
  },

  getCompanyDetail: async (companyId: string): Promise<CompanyDetail> => {
    const res = await apiClient.get<CompanyDetail>(`/crm/companies/${companyId}/`);
    return res.data;
  },

  createCompany: async (payload: Record<string, any>): Promise<CompanyDetail> => {
    const res = await apiClient.post<CompanyDetail>("/crm/companies/", payload);
    return res.data;
  },

  updateCompany: async (companyId: string, payload: Record<string, any>): Promise<CompanyDetail> => {
    const res = await apiClient.patch<CompanyDetail>(`/crm/companies/${companyId}/`, payload);
    return res.data;
  },

  deleteCompany: async (companyId: string): Promise<void> => {
    await apiClient.delete(`/crm/companies/${companyId}/`);
  },

  checkDuplicateCompany: async (name: string, website?: string, excludeCompanyId?: string): Promise<DuplicateCheckResult> => {
    const res = await apiClient.post<DuplicateCheckResult>("/crm/companies/check-duplicate/", {
      name,
      website: website || "",
      exclude_company_id: excludeCompanyId || null,
    });
    return res.data;
  },

  // HR Contacts
  getCompanyContacts: async (companyId: string): Promise<HRContact[]> => {
    const res = await apiClient.get<HRContact[]>(`/crm/companies/${companyId}/contacts/`);
    return res.data;
  },

  createHRContact: async (companyId: string, payload: Record<string, any>): Promise<HRContact> => {
    const res = await apiClient.post<HRContact>(`/crm/companies/${companyId}/contacts/`, payload);
    return res.data;
  },

  updateHRContact: async (contactId: string, payload: Record<string, any>): Promise<HRContact> => {
    const res = await apiClient.patch<HRContact>(`/crm/contacts/${contactId}/`, payload);
    return res.data;
  },

  deleteHRContact: async (contactId: string): Promise<void> => {
    await apiClient.delete(`/crm/contacts/${contactId}/`);
  },

  // Outreach Touchpoints
  getCompanyOutreach: async (companyId: string): Promise<OutreachActivity[]> => {
    const res = await apiClient.get<OutreachActivity[]>(`/crm/companies/${companyId}/outreach/`);
    return res.data;
  },

  logOutreach: async (companyId: string, payload: Record<string, any>): Promise<OutreachActivity> => {
    const res = await apiClient.post<OutreachActivity>(`/crm/companies/${companyId}/outreach/`, payload);
    return res.data;
  },

  // Follow-Up Tasks
  getFollowUps: async (params?: Record<string, any>): Promise<PaginatedResponse<FollowUp>> => {
    const res = await apiClient.get<PaginatedResponse<FollowUp>>("/crm/follow-ups/", { params });
    return res.data;
  },

  createFollowUp: async (payload: Record<string, any>): Promise<FollowUp> => {
    const res = await apiClient.post<FollowUp>("/crm/follow-ups/", payload);
    return res.data;
  },

  completeFollowUp: async (followUpId: string, notes?: string): Promise<FollowUp> => {
    const res = await apiClient.post<FollowUp>(`/crm/follow-ups/${followUpId}/complete/`, {
      notes: notes || "",
    });
    return res.data;
  },

  cancelFollowUp: async (followUpId: string, reason: string): Promise<FollowUp> => {
    const res = await apiClient.post<FollowUp>(`/crm/follow-ups/${followUpId}/cancel/`, {
      reason,
    });
    return res.data;
  },
};
