# GQT HRMS & Recruitment CRM Platform — Phase 3 Traceability Matrix
## Document: `docs/phase-3/02-phase-3-traceability-matrix.md`
**Author:** QA Lead, Requirements Engineer  
**Status:** 100% Verified & Traceable  

---

## 1. Requirements Traceability Baseline

| Req ID | Requirement Description | Implementation Artifact | Test Case Verification | Status |
|:---|:---|:---|:---|:---:|
| **REQ-J01** | Structured Job Requirement model with UUID PK and PROTECT foreign key to Company | `backend/apps/jobs/models.py` (`JobRequirement`) | `test_job_model_creation_and_checks_initialization`, `test_job_company_protect_deletion_policy` | ✅ PASS |
| **REQ-J02** | Boundary validations for CTC, CGPA, percentages, deadlines, and bond | `backend/apps/jobs/models.py` (`clean()`), `serializers.py` | `test_job_field_validation` | ✅ PASS |
| **REQ-J03** | Automatic initialization of all five mandatory checklist items in PENDING | `backend/apps/jobs/services.py` (`create_job_requirement`) | `test_job_model_creation_and_checks_initialization` | ✅ PASS |
| **REQ-J04** | Independent evaluation of all five checks (Eligibility, Salary, Company, Process, Deadline) | `backend/apps/jobs/models.py` (`JobVerificationCheck`), `services.py` (`update_verification_check`) | `test_five_point_verification_advances_to_pending_approval` | ✅ PASS |
| **REQ-J05** | Denial of approval if any check is unverified, flagged, or rejected | `backend/apps/jobs/services.py` (`approve_job`) | `test_approval_denied_if_checks_not_verified` | ✅ PASS |
| **REQ-J06** | Strict Segregation of Duties: Submitting Placement Officer cannot approve own job | `backend/apps/jobs/services.py` (`approve_job`), `permissions.py` (`CanApproveOrRejectJob`) | `test_segregation_of_duties_self_approval_denied`, `ApprovalModal.test` | ✅ PASS |
| **REQ-J07** | Independent approval by Placement Head / Admin locking job against edits | `backend/apps/jobs/services.py` (`approve_job`) | `test_successful_independent_approval`, `test_approved_job_locked_against_direct_updates` | ✅ PASS |
| **REQ-J08** | Invalidation of affected checks upon material field modification | `backend/apps/jobs/services.py` (`update_job_requirement`, `MATERIAL_FIELDS_MAPPING`) | `test_material_field_edit_invalidates_affected_checks` | ✅ PASS |
| **REQ-J09** | Mandatory justification required for rejection and revision feedback | `backend/apps/jobs/services.py` (`reject_job`, `request_changes`) | `test_rejection_requires_meaningful_reason`, `test_request_changes_requires_reason` | ✅ PASS |
| **REQ-J10** | Authorized amendment workflow creating new revision and requiring re-verification | `backend/apps/jobs/services.py` (`amend_approved_job`) | `test_authorized_amendment_increments_revision_and_invalidates_checks` | ✅ PASS |
| **REQ-J11** | Auditor read-only enforcement across all job requirement and verification APIs | `backend/apps/jobs/permissions.py` (`IsJobStaffOrReadOnly`) | `test_auditor_read_only_via_api` | ✅ PASS |
| **REQ-J12** | Deny-by-default student access to staff job requirement operations | `backend/apps/jobs/permissions.py` (`IsJobStaffOrReadOnly`) | `test_student_denied_access_to_jobs_api` | ✅ PASS |
| **REQ-J13** | Dedicated verification review and approval queues | `backend/apps/jobs/selectors.py`, `views.py` (`JobVerificationQueueView`, `JobApprovalQueueView`) | `test_verification_and_approval_queues` | ✅ PASS |
| **REQ-J14** | Persisted real-time workflow metrics and verification statistics | `backend/apps/jobs/selectors.py`, `views.py` (`JobWorkflowMetricsView`) | `test_workflow_metrics_endpoint` | ✅ PASS |
| **REQ-J15** | Append-only workflow transition history and telemetry audit logging | `backend/apps/jobs/models.py` (`JobWorkflowHistory`), `services.py` | `test_submit_for_verification_workflow`, `test_successful_independent_approval` | ✅ PASS |
| **REQ-J16** | Responsive GQT-branded frontend UI: Directory, Form, Detail, Verification Checklist, Queues, Modals | `frontend/src/pages/jobs/`, `components/jobs/` | Vitest test suite (`test/jobs.test.tsx`), Vite production build | ✅ PASS |

