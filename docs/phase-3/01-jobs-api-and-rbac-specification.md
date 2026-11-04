# GQT HRMS & Recruitment CRM Platform — Phase 3 API & RBAC Specification
## Document: `docs/phase-3/01-jobs-api-and-rbac-specification.md`
**Author:** Senior Application Security Architect, API Lead  
**Status:** Approved & Implemented  
**Base Path:** `/api/v1/jobs/`  

---

## 1. Role-Based Access Control (RBAC) Matrix

Access control enforces deny-by-default. All requests require valid JWT session authentication.

| Role | Browse / Read | Create Draft | Edit Draft / Changes Req. | Evaluate Checks | Submit / Assign | Final Approval | Reject / Req. Changes | Amend Approved |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **`ADMIN`** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅* | ✅ | ✅ |
| **`PLACEMENT_HEAD`** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅* | ✅ | ✅ |
| **`PLACEMENT_OFFICER`** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **`CALLING_EXECUTIVE`** | ✅ (Read) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **`CRM_EXECUTIVE`** | ✅ (Read) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **`AUDITOR`** | ✅ (Read-Only) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **`STUDENT`** | ❌ (Denied) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

*\*Note on Segregation of Duties:* Even if a user possesses `ADMIN` or `PLACEMENT_HEAD` privileges, they cannot approve a job where `submitted_by_id == request.user.id` (unless running as superuser system override).

---

## 2. API Endpoint Catalogue

### 2.1 Job Requirement Management
- `GET /api/v1/jobs/requirements/`: Paginated listing with search on title, company name, skills, and filters by status, category, location, and CTC.
- `POST /api/v1/jobs/requirements/`: Create new job requirement draft. Automatically instantiates all 5 verification checklist gates in `PENDING` status.
- `GET /api/v1/jobs/requirements/{id}/`: Comprehensive detail view including full specifications, 5 checks, verification summary, and workflow history.
- `PATCH /api/v1/jobs/requirements/{id}/`: Update draft or changes-requested job. Triggers automatic invalidation of checks matching modified material fields.
- `DELETE /api/v1/jobs/requirements/{id}/`: Remove job requirement (restricted to `DRAFT` or `REJECTED` status).

### 2.2 Verification Review & Checkpoints
- `POST /api/v1/jobs/requirements/{id}/submit/`: Submit draft or changes-requested job for 5-point verification review (`status → PENDING_VERIFICATION`).
- `POST /api/v1/jobs/requirements/{id}/assign-verifier/`: Delegate verification review to an active staff member (`status → UNDER_VERIFICATION`).
- `GET /api/v1/jobs/requirements/{id}/checks/`: Retrieve all five verification checks for this job.
- `POST /api/v1/jobs/requirements/{id}/checks/{check_type}/`: Evaluate check (`status`: `VERIFIED`, `FLAGGED`, `REJECTED`, `PENDING`). If all 5 checks reach `VERIFIED`, automatically advances job to `PENDING_APPROVAL`.

### 2.3 Sign-Off & Lifecycle Transitions
- `POST /api/v1/jobs/requirements/{id}/approve/`: Formally authorize and approve job. Enforces SoD and requires all 5 checks to be `VERIFIED`.
- `POST /api/v1/jobs/requirements/{id}/reject/`: Reject requirement. Mandatory `reason` field required.
- `POST /api/v1/jobs/requirements/{id}/request-changes/`: Request modifications with mandatory `reason` feedback.
- `POST /api/v1/jobs/requirements/{id}/amend/`: Authorize amendment to already approved job. Increments revision counter, invalidates affected checks, and returns job to review pipeline.

### 2.4 Dedicated Queues & Real-Time Telemetry
- `GET /api/v1/jobs/verification-queue/`: Real-time queue of jobs awaiting or undergoing verification.
- `GET /api/v1/jobs/approval-queue/`: Real-time queue of jobs awaiting Placement Head approval.
- `GET /api/v1/jobs/metrics/`: Pipeline metrics: total jobs, counts by status, and verification checklist breakdown.

