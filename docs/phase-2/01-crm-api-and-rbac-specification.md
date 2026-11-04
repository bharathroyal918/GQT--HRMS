# GQT HRMS & Recruitment CRM Platform — Phase 2: CRM API & RBAC Specification

## 1. API Endpoints Overview

All endpoints reside under the `/api/v1/crm/` namespace:

| Method | Endpoint | Description | Permitted Roles |
|---|---|---|---|
| `GET` | `/api/v1/crm/companies/` | Paginated company list with search, status, industry, source, tier, and assigned_to filters | All CRM Staff + Auditor |
| `POST` | `/api/v1/crm/companies/` | Create target company (with duplicate validation) | Admin, Placement Head, Calling Exec, CRM Exec |
| `POST` | `/api/v1/crm/companies/check-duplicate/` | Pre-flight duplicate diagnostic check | All CRM Staff |
| `GET` | `/api/v1/crm/companies/<id>/` | Full company detail with contacts, recent outreach, and active follow-ups | All CRM Staff + Auditor |
| `PATCH` | `/api/v1/crm/companies/<id>/` | Update company attributes | Admin, Placement Head, Assigned Calling Exec |
| `DELETE` | `/api/v1/crm/companies/<id>/` | Soft-delete company (`is_deleted=True`) | Admin, Placement Head |
| `GET` | `/api/v1/crm/companies/<id>/contacts/` | List HR recruiter contacts for company | All CRM Staff + Auditor |
| `POST` | `/api/v1/crm/companies/<id>/contacts/` | Add HR recruiter contact to company | Admin, Placement Head, Calling Exec, CRM Exec |
| `GET` | `/api/v1/crm/contacts/<id>/` | Retrieve specific HR contact profile | All CRM Staff + Auditor |
| `PATCH` | `/api/v1/crm/contacts/<id>/` | Update HR contact profile | Admin, Placement Head, Calling Exec, CRM Exec |
| `DELETE` | `/api/v1/crm/contacts/<id>/` | Soft-delete HR contact | Admin, Placement Head |
| `GET` | `/api/v1/crm/companies/<id>/outreach/` | List outreach activity logs for company | All CRM Staff + Auditor |
| `POST` | `/api/v1/crm/companies/<id>/outreach/` | Log new touchpoint (call, email, WhatsApp, meeting) | Admin, Placement Head, Calling Exec, CRM Exec |
| `GET` | `/api/v1/crm/follow-ups/` | Actionable task queue (`filter_type="due_today"|"overdue"|"upcoming"`) | All CRM Staff + Auditor |
| `POST` | `/api/v1/crm/follow-ups/` | Schedule new follow-up task | Admin, Placement Head, Calling Exec, CRM Exec |
| `GET` | `/api/v1/crm/follow-ups/<id>/` | Retrieve specific follow-up task | All CRM Staff + Auditor |
| `POST` | `/api/v1/crm/follow-ups/<id>/complete/` | Mark follow-up as completed with notes | Admin, Placement Head, Assigned Executive |
| `POST` | `/api/v1/crm/follow-ups/<id>/cancel/` | Cancel follow-up with mandatory reason | Admin, Placement Head, Assigned Executive |

---

## 2. Role-Based & Object-Level Access Control (RBAC)

Enforced via `apps.crm.permissions`:

### 2.1 Institutional Role Mapping
- **`ADMIN` / `SUPERUSER`**: Full administrative CRUD across all companies, contacts, outreach logs, and follow-ups.
- **`PLACEMENT_HEAD`**: Full managerial oversight and write access across all accounts and follow-up queues.
- **`CALLING_EXECUTIVE`**:
  - Full read access to company directory.
  - Can create new prospect companies and log outreach.
  - Can edit companies assigned to them or unassigned leads.
  - Can create and complete follow-up tasks assigned to them.
- **`CRM_EXECUTIVE`**:
  - Can create and manage recruiter contacts.
  - Can log touchpoints and manage accounts.
- **`AUDITOR`**:
  - Strictly read-only (`GET` endpoints only). Mutation methods (`POST`, `PATCH`, `DELETE`) return `HTTP 403 Forbidden`.
- **Other Institutional Roles** (`TRAINER`, `STUDENT`, `DESIGNER`):
  - Completely denied (`HTTP 403 Forbidden`).

---

## 3. Audit Logging Specification

Every CRM state mutation automatically records an immutable record in `core_audit_log`:

| Action Trigger | Action Code | Resource Type | Logged Changes |
|---|---|---|---|
| Company Creation | `COMPANY_CREATED` | `crm.Company` | `name`, `status`, `assigned_to`, `canonical_domain` |
| Company Update | `COMPANY_UPDATED` | `crm.Company` | Delta mapping (`old` vs `new`) for modified fields |
| Recruiter Added | `HR_CONTACT_CREATED` | `crm.HRContact` | `company_id`, `name`, `email`, `is_primary` |
| Recruiter Updated | `HR_CONTACT_UPDATED` | `crm.HRContact` | Delta mapping for updated attributes |
| Touchpoint Logged | `OUTREACH_ACTIVITY_LOGGED` | `crm.OutreachActivity` | `company_id`, `channel`, `outcome`, `status_advanced` |
| Follow-Up Scheduled | `FOLLOWUP_SCHEDULED` | `crm.FollowUp` | `company_id`, `assigned_to`, `due_date`, `priority` |
| Follow-Up Completed | `FOLLOWUP_COMPLETED` | `crm.FollowUp` | `status: COMPLETED` |
| Follow-Up Cancelled | `FOLLOWUP_CANCELLED` | `crm.FollowUp` | `status: CANCELLED`, `reason` |

