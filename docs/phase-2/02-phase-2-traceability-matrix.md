# GQT HRMS & Recruitment CRM Platform — Phase 2: Requirements Traceability Matrix

## 1. Traceability Overview

This matrix links the approved Phase 0 recruitment CRM requirements (`MOD-002`) to the Phase 2 backend models, services, API endpoints, frontend pages, and automated tests.

---

## 2. Requirements Traceability

| Req ID | Requirement Description | Backend Implementation | Frontend UI Component | Automated Verification Test | Status |
|---|---|---|---|---|---|
| **REQ-CRM-01** | Company Model with UUID PK, name, domain, industry, source, status, tier | `apps.crm.models.Company` | `CompanyDirectoryPage.tsx`, `CompanyDetailPage.tsx` | `test_crm.py::test_company_model_save_normalization` | **VERIFIED** |
| **REQ-CRM-02** | Name and domain normalization | `normalize_company_name`, `extract_canonical_domain` | `CreateCompanyModal.tsx` | `test_crm.py::test_company_normalization_and_domain_extraction` | **VERIFIED** |
| **REQ-CRM-03** | Duplicate company detection | `detect_company_duplicates`, `CompanyCheckDuplicateAPIView` | `CreateCompanyModal.tsx` duplicate alert banner | `test_crm.py::test_duplicate_detection_exact_domain`, `crm.test.tsx` | **VERIFIED** |
| **REQ-CRM-04** | HR Contact hierarchy & primary contact toggle | `apps.crm.models.HRContact`, `create_hr_contact` | `AddContactModal.tsx`, `CompanyDetailPage.tsx` | `test_crm.py::test_hr_contact_creation_and_primary_toggle` | **VERIFIED** |
| **REQ-CRM-05** | Multi-channel outreach activity logging | `apps.crm.models.OutreachActivity`, `log_outreach_activity` | `LogOutreachModal.tsx`, `CompanyDetailPage.tsx` | `test_crm.py::test_outreach_logging_advances_company_status` | **VERIFIED** |
| **REQ-CRM-06** | Dynamic company status progression | `log_outreach_activity` status advancement logic | `CompanyDetailPage.tsx` status badge | `test_crm.py::test_outreach_logging_advances_company_status` | **VERIFIED** |
| **REQ-CRM-07** | Follow-Up task scheduling, overdue logic, completion/cancellation | `apps.crm.models.FollowUp`, `complete_follow_up`, `cancel_follow_up` | `FollowUpDashboardPage.tsx`, `CompleteFollowUpModal.tsx`, `CancelFollowUpModal.tsx` | `test_crm.py::test_follow_up_lifecycle`, `crm.test.tsx` | **VERIFIED** |
| **REQ-CRM-08** | Role-based and object-level permission enforcement | `apps.crm.permissions.IsCrmStaffOrReadOnly`, `CanManageCompany` | `Sidebar.tsx`, `ProtectedRoute.tsx` | `test_crm.py::test_auditor_read_only_enforcement`, `test_unauthorized_role_denied` | **VERIFIED** |
| **REQ-CRM-09** | Paginated lists, search, filtering without N+1 queries | `apps.crm.selectors.list_companies` (select_related & annotate) | `CompanyDirectoryPage.tsx`, `FollowUpDashboardPage.tsx` | `test_crm.py::test_calling_executive_crud_flow` | **VERIFIED** |
| **REQ-CRM-10** | Immutable audit trail for all CRM mutations | `apps.crm.services` calls to `AuditLog.objects.create` | N/A (Server-side security) | `test_crm.py::test_audit_logs_created_for_crm_actions` | **VERIFIED** |
| **REQ-CRM-11** | TypeScript strict mode & Vite production build | `frontend/src/pages/crm/*`, `frontend/src/api/crmApi.ts` | Complete production build | `npm run lint`, `npm run build` | **VERIFIED** |

